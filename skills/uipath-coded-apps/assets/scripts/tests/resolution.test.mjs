import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { validateIntent, resolveMetric, buildWidgetFile, emit, parseEvent, classifyEditIntent, VALID_DISPLAY_TYPES } from '../build-dashboard.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const REGISTRY_PATH = resolve(__dirname, '../capability-registry.json')

const registry = JSON.parse(readFileSync(REGISTRY_PATH, 'utf8'))

function resolveT1(metricName) {
  const entry = registry.t1[metricName]
  if (!entry) return null
  return { tier: 'T1', entry }
}

function resolveAlias(userText) {
  const lower = userText.toLowerCase()
  for (const [key, entry] of Object.entries(registry.t1)) {
    if (entry.aliases.some(a => lower.includes(a))) return { tier: 'T1', key, entry }
  }
  for (const [key, entry] of Object.entries(registry.t2)) {
    if (entry.aliases.some(a => lower.includes(a))) return { tier: 'T2', key, entry }
  }
  return null
}

test('T1 exact name lookup returns entry', () => {
  const result = resolveT1('agent-errors')
  assert.ok(result)
  assert.equal(result.tier, 'T1')
  assert.equal(result.entry.template, 'line-chart')
})

test('T1 exact name lookup returns null for unknown metric', () => {
  const result = resolveT1('completely-unknown-metric')
  assert.equal(result, null)
})

test('alias lookup finds agent-errors by natural language', () => {
  const result = resolveAlias('show me agent failures over time')
  assert.ok(result)
  assert.equal(result.tier, 'T1')
  assert.equal(result.key, 'agent-errors')
})

test('alias lookup finds T2 jobs-duration-threshold', () => {
  const result = resolveAlias('long running jobs over threshold')
  assert.ok(result)
  assert.equal(result.tier, 'T2')
  assert.equal(result.key, 'jobs-duration-threshold')
})

test('alias lookup returns null for unknown text', () => {
  const result = resolveAlias('completely unrelated nonsense xyz')
  assert.equal(result, null)
})

test('all T1 entries have required fields', () => {
  for (const [key, entry] of Object.entries(registry.t1)) {
    assert.ok(entry.template, `${key} missing template`)
    assert.ok(entry.description, `${key} missing description`)
    assert.ok(Array.isArray(entry.aliases) && entry.aliases.length > 0, `${key} missing aliases`)
    assert.ok(entry.defaults?.title, `${key} missing defaults.title`)
    // SDK fields must NOT be present — registry is hints-only
    assert.equal(entry.sdkImport, undefined, `${key} should not have sdkImport (removed)`)
    assert.equal(entry.sdkService, undefined, `${key} should not have sdkService (removed)`)
    assert.equal(entry.sdkMethod, undefined, `${key} should not have sdkMethod (removed)`)
    assert.equal(entry.responseType, undefined, `${key} should not have responseType (removed)`)
  }
})

test('all T2 entries have required fields', () => {
  for (const [key, entry] of Object.entries(registry.t2)) {
    assert.ok(entry.description, `${key} missing description`)
    assert.ok(Array.isArray(entry.aliases) && entry.aliases.length > 0, `${key} missing aliases`)
    // SDK fields must NOT be present — registry is hints-only
    assert.equal(entry.sdkImport, undefined, `${key} should not have sdkImport (removed)`)
    assert.equal(entry.sdkService, undefined, `${key} should not have sdkService (removed)`)
    assert.equal(entry.method, undefined, `${key} should not have method (removed)`)
    assert.equal(entry.filterField, undefined, `${key} should not have filterField (removed)`)
    assert.equal(entry.filterType, undefined, `${key} should not have filterType (removed)`)
    assert.equal(entry.sortField, undefined, `${key} should not have sortField (removed)`)
    assert.equal(entry.sortDir, undefined, `${key} should not have sortDir (removed)`)
    assert.equal(entry.defaultDisplayAs, undefined, `${key} should not have defaultDisplayAs (removed)`)
  }
})

test('all hardRefuse entries have pattern, reason, alternative', () => {
  for (const entry of registry.hardRefuse) {
    assert.ok(entry.pattern, 'hardRefuse entry missing pattern')
    assert.ok(entry.reason, 'hardRefuse entry missing reason')
    assert.ok(entry.alternative, 'hardRefuse entry missing alternative')
    // Verify pattern is a valid regex
    assert.doesNotThrow(() => new RegExp(entry.pattern), `invalid regex: ${entry.pattern}`)
  }
})

test('hardRefuse matches cost/dollar phrases', () => {
  const dollarEntry = registry.hardRefuse.find(e => e.pattern.includes('dollar'))
  assert.ok(dollarEntry)
  assert.ok(new RegExp(dollarEntry.pattern).test('cost in dollars'))
})

test('hardRefuse does not collide with valid T1 aliases', () => {
  for (const refuseEntry of registry.hardRefuse) {
    const re = new RegExp(refuseEntry.pattern)
    for (const [key, t1Entry] of Object.entries(registry.t1)) {
      for (const alias of t1Entry.aliases) {
        assert.ok(!re.test(alias), `hardRefuse pattern "${refuseEntry.pattern}" collides with T1 alias "${alias}" (${key})`)
      }
    }
  }
})

// ── validateIntent tests ──────────────────────────────────────────────────────

test('validateIntent: valid T1 intent passes', () => {
  const errors = validateIntent({
    dashboardName: 'My Dashboard',
    timeRange: '30d',
    metrics: [{ name: 'agent-errors', tier: 'T1', title: 'Agent Errors', fnBody: 'return []' }]
  })
  assert.deepEqual(errors, [])
})

test('validateIntent: rejects T1 metric without fnBody', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '30d',
    metrics: [{ name: 'agent-errors', tier: 'T1', title: 'Agent Errors' }]
  })
  assert.ok(errors.some(e => e.includes('T1') && e.includes('fnBody')))
})

test('validateIntent: rejects T1 metric without title', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '30d',
    metrics: [{ name: 'agent-errors', tier: 'T1', fnBody: 'return []' }]
  })
  assert.ok(errors.some(e => e.includes('T1') && e.includes('title')))
})

test('validateIntent: rejects T2 metric without fnBody', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'jobs-by-state', tier: 'T2', title: 'Jobs', params: { value: 'Faulted' } }]
  })
  assert.ok(errors.some(e => e.includes('T2') && e.includes('fnBody')))
})

test('validateIntent: rejects missing dashboardName', () => {
  const errors = validateIntent({ timeRange: '30d', metrics: [{ name: 'x', tier: 'T1' }] })
  assert.ok(errors.some(e => e.includes('dashboardName')))
})

test('validateIntent: rejects invalid timeRange', () => {
  const errors = validateIntent({ dashboardName: 'x', timeRange: '2w', metrics: [{ name: 'x', tier: 'T1' }] })
  assert.ok(errors.some(e => e.includes('timeRange')))
})

test('validateIntent: rejects T2 metric without params', () => {
  const errors = validateIntent({ dashboardName: 'x', timeRange: '7d', metrics: [{ name: 'queue-failure-threshold', tier: 'T2' }] })
  assert.ok(errors.some(e => e.includes('T2') && e.includes('params')))
})

test('validateIntent: rejects T3 metric without fnBody', () => {
  const errors = validateIntent({ dashboardName: 'x', timeRange: '7d', metrics: [{ name: 'custom', tier: 'T3', displayAs: 'ranked-table', title: 'Custom' }] })
  assert.ok(errors.some(e => e.includes('T3') && e.includes('fnBody')))
})

// ── resolveMetric tests ───────────────────────────────────────────────────────

test('resolveMetric: T1 known name returns entry with template', () => {
  const result = resolveMetric({ name: 'agent-errors', tier: 'T1' })
  assert.equal(result.tier, 'T1')
  assert.equal(result.entry.template, 'line-chart')
})

test('resolveMetric: T2 known name returns entry with description', () => {
  const result = resolveMetric({ name: 'jobs-duration-threshold', tier: 'T2', params: { threshold: 300, direction: 'gt' } })
  assert.equal(result.tier, 'T2')
  assert.ok(result.entry.description)
})

test('resolveMetric: T3 always resolves with null entry', () => {
  const result = resolveMetric({ name: 'custom-thing', tier: 'T3', fnBody: 'return []', displayAs: 'kpi-card', title: 'X' })
  assert.equal(result.tier, 'T3')
  assert.equal(result.entry, null)
})

test('resolveMetric: unknown T1 name throws with "not found in registry"', () => {
  assert.throws(() => resolveMetric({ name: 'nonexistent-metric', tier: 'T1' }), /not found in registry/)
})

// ── buildWidgetFile tests (unified path for all tiers) ────────────────────────

test('buildWidgetFile: T1 metric uses fnBody from agent (not hardcoded SDK)', () => {
  const entry = registry.t1['agent-errors']
  const content = buildWidgetFile(
    {
      name: 'agent-errors',
      tier: 'T1',
      title: 'Agent Error Rate',
      displayAs: 'line-chart',
      xKey: 'date',
      yKey: 'value',
      fnBody: "const { Agents } = await import('@uipath/uipath-typescript/agents')\nconst svc = new Agents(sdk as never)\nreturn (await svc.getErrorsTimeline(THIRTY_DAYS_AGO, NOW))?.data ?? []"
    },
    entry,
    '30d'
  )
  assert.ok(content.includes('customDataFn'))
  assert.ok(content.includes('getErrorsTimeline'))
  // No hardcoded type params from registry
  assert.ok(!content.includes('useInsightsSDK<'))
})

test('buildWidgetFile: uses registry defaults for xKey/yKey when not in metric', () => {
  const entry = registry.t1['agent-errors']
  const content = buildWidgetFile(
    { name: 'agent-errors', tier: 'T1', title: 'Agent Errors', displayAs: 'line-chart', fnBody: 'return []' },
    entry,
    '30d'
  )
  // xKey from registry defaults
  assert.ok(content.includes('date'))
})

test('buildWidgetFile: T2 metric with fnBody uses chart path', () => {
  const entry = registry.t2['jobs-duration-threshold']
  const content = buildWidgetFile(
    {
      name: 'jobs-duration-threshold',
      tier: 'T2',
      title: 'Long Running Jobs',
      displayAs: 'bar-chart',
      xKey: 'name',
      yKey: 'duration',
      fnBody: "const { Jobs } = await import('@uipath/uipath-typescript/jobs')\nconst svc = new Jobs(sdk as never)\nconst result = await svc.getAll({ filter: \"State eq 'Running'\" })\nreturn result?.items ?? []"
    },
    entry,
    '30d'
  )
  assert.ok(content.includes('customDataFn'))
  assert.ok(content.includes('Jobs'))
  assert.ok(!content.includes('useInsightsSDK<'))
})

test('buildWidgetFile: T3 metric (null registry entry) uses shell path for kpi-card', () => {
  const content = buildWidgetFile(
    {
      name: 'running-jobs-kpi',
      tier: 'T3',
      title: 'Running Jobs',
      displayAs: 'kpi-card',
      fnBody: 'return [{ count: 42 }]',
      valueField: 'count',
      valueLabel: 'running jobs'
    },
    null,
    '30d'
  )
  assert.ok(content.includes('RunningJobsKpi'))
  assert.ok(content.includes('Running Jobs'))
  assert.ok(content.includes("const VALUE_FIELD = 'count'"))
  assert.ok(content.includes("const VALUE_LABEL = 'running jobs'"))
  assert.ok(!content.includes('<<FN_BODY>>'))
})

test('buildWidgetFile: throws if title is missing', () => {
  assert.throws(
    () => buildWidgetFile({ name: 'x', tier: 'T3', displayAs: 'kpi-card', fnBody: 'return []' }, null),
    /missing title/
  )
})

test('buildWidgetFile: throws if fnBody is missing', () => {
  assert.throws(
    () => buildWidgetFile({ name: 'x', tier: 'T3', title: 'X', displayAs: 'kpi-card' }, null),
    /missing fnBody/
  )
})

test('buildWidgetFile: throws if displayAs cannot be determined', () => {
  assert.throws(
    () => buildWidgetFile({ name: 'x', tier: 'T3', title: 'X', fnBody: 'return []' }, null),
    /needs displayAs/
  )
})

test('buildWidgetFile: injects fnBody into shell template for ranked-table', () => {
  const content = buildWidgetFile({
    name: 'faulted-queues', tier: 'T3', title: 'Faulted Queues', description: 'Queues with faults',
    displayAs: 'ranked-table', fnBody: "const r = await sdk.queues.getAll({})\nreturn r.items ?? []"
  }, null, '30d')
  assert.ok(content.includes('FaultedQueues'), 'component name not injected')
  assert.ok(content.includes('Faulted Queues'), 'title not injected')
  assert.ok(content.includes('sdk.queues.getAll'), 'fnBody not injected')
  assert.ok(!content.includes('<<FN_BODY>>'), 'FN_BODY placeholder not replaced')
  assert.ok(!content.includes('<<COMPONENT_NAME>>'), 'COMPONENT_NAME placeholder not replaced')
})

test('buildWidgetFile: no unresolved << >> placeholders remain', () => {
  const content = buildWidgetFile({
    name: 'test', tier: 'T3', title: 'Test Widget',
    displayAs: 'ranked-table',
    fnBody: 'return []',
    valueField: '', valueLabel: '',
  }, null, '30d')
  const unresolved = content.match(/<<[A-Z_]+>>/g)
  assert.equal(unresolved, null, `Unresolved placeholders: ${(unresolved ?? []).join(', ')}`)
})

test('buildWidgetFile: uses registry defaults for icon when metric has none', () => {
  const entry = registry.t1['agent-errors']
  const content = buildWidgetFile(
    { name: 'agent-errors', tier: 'T1', title: 'Errors', displayAs: 'line-chart', fnBody: 'return []' },
    entry,
    '30d'
  )
  assert.ok(content.includes('AlertTriangle'))
})

// ── emit + parseEvent tests ───────────────────────────────────────────────────

test('emit: writes structured event with payload', () => {
  const lines = []
  emit('WIDGET_READY', { name: 'ErrorRateTrend', index: 1, total: 4 }, { write: s => lines.push(s) })
  assert.equal(lines.length, 1)
  const parsed = JSON.parse(lines[0].replace('WIDGET_READY:', ''))
  assert.equal(parsed.name, 'ErrorRateTrend')
})

test('emit: writes simple event with no payload', () => {
  const lines = []
  emit('PREWARM_DONE', null, { write: s => lines.push(s) })
  assert.equal(lines[0].trim(), 'PREWARM_DONE')
})

test('parseEvent: parses WIDGET_READY with payload', () => {
  const result = parseEvent('WIDGET_READY:{"name":"Foo","index":2,"total":5}')
  assert.equal(result.type, 'WIDGET_READY')
  assert.equal(result.payload.name, 'Foo')
})

test('parseEvent: parses simple event with no payload', () => {
  const result = parseEvent('PREWARM_DONE')
  assert.equal(result.type, 'PREWARM_DONE')
  assert.equal(result.payload, null)
})

test('parseEvent: returns null for non-event lines', () => {
  const result = parseEvent('regular log line')
  assert.equal(result, null)
})

// ── classifyEditIntent tests ──────────────────────────────────────────────────

test('classifyEditIntent: identifies ADD', () => {
  const result = classifyEditIntent({ op: 'ADD', projectDir: '/tmp/x', metric: { name: 'agent-errors', tier: 'T1' } })
  assert.equal(result.op, 'ADD')
})

test('classifyEditIntent: identifies REMOVE', () => {
  const result = classifyEditIntent({ op: 'REMOVE', projectDir: '/tmp/x', target: 'ErrorRateTrend' })
  assert.equal(result.op, 'REMOVE')
  assert.equal(result.target, 'ErrorRateTrend')
})

test('classifyEditIntent: throws on invalid op', () => {
  assert.throws(() => classifyEditIntent({ op: 'DELETE', projectDir: '/tmp/x' }), /invalid op/)
})

test('parseEvent: recognizes AUTH_MISSING event', () => {
  const result = parseEvent('AUTH_MISSING:{"var":"clientId","message":"No client ID"}')
  assert.equal(result.type, 'AUTH_MISSING')
  assert.equal(result.payload.var, 'clientId')
})

// ── VALID_DISPLAY_TYPES + displayAs validation tests ─────────────────────────

test('VALID_DISPLAY_TYPES includes all chart and table types', () => {
  assert.ok(VALID_DISPLAY_TYPES.includes('kpi-card'))
  assert.ok(VALID_DISPLAY_TYPES.includes('ranked-table'))
  assert.ok(VALID_DISPLAY_TYPES.includes('data-table'))
  assert.ok(VALID_DISPLAY_TYPES.includes('area-chart'))
  assert.ok(VALID_DISPLAY_TYPES.includes('line-chart'))
  assert.ok(VALID_DISPLAY_TYPES.includes('bar-chart'))
  assert.ok(VALID_DISPLAY_TYPES.includes('donut-chart'))
  assert.ok(VALID_DISPLAY_TYPES.includes('multi-line-chart'))
})

test('validateIntent: accepts T3-SDK with chart displayAs (area-chart, line-chart, bar-chart, donut-chart)', () => {
  for (const chartType of ['area-chart', 'line-chart', 'bar-chart', 'donut-chart']) {
    const errors = validateIntent({
      dashboardName: 'x', timeRange: '7d',
      metrics: [{ name: 'custom', tier: 'T3', title: 'X', fnBody: 'return []', displayAs: chartType }]
    })
    assert.deepEqual(errors, [], `${chartType} should be valid for T3-SDK`)
  }
})

test('validateIntent: rejects T3-SDK with truly unsupported displayAs', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'custom', tier: 'T3', title: 'X', fnBody: 'return []', displayAs: 'unknown-widget' }]
  })
  assert.ok(errors.some(e => e.includes('unsupported displayAs')))
})

test('validateIntent: accepts T3-SDK with ranked-table displayAs', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'custom', tier: 'T3', title: 'X', fnBody: 'return []', displayAs: 'ranked-table' }]
  })
  assert.deepEqual(errors, [])
})

test('buildWidgetFile: injects valueField and valueLabel placeholders', () => {
  const content = buildWidgetFile({
    name: 'running-jobs', tier: 'T3', title: 'Running Jobs', displayAs: 'kpi-card',
    fnBody: 'return []', valueField: 'count', valueLabel: 'running jobs'
  }, null)
  assert.ok(content.includes("const VALUE_FIELD = 'count'"))
  assert.ok(content.includes("const VALUE_LABEL = 'running jobs'"))
  assert.ok(!content.includes('<<VALUE_FIELD>>'))
  assert.ok(!content.includes('<<VALUE_LABEL>>'))
})
