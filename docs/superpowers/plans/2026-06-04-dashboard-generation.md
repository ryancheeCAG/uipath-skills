# Dashboard Generation — Code-as-Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `build-dashboard.mjs` and its skill documentation to implement the Code-as-Orchestrator architecture — shifting widget config generation, tier routing, and build orchestration from the AI agent into deterministic Node.js code.

**Architecture:** A four-layer system where the agent only translates NLP to a compact `intent.json`. A Tiered Resolution Engine (T1: catalog, T2: parametric, T3: sandboxed fn body) inside `build-dashboard.mjs` derives all widget TypeScript. A structured event stream (`WIDGET_READY`, `T3_RETRY`, `BUILD_RESULT`) gives progressive feedback. All skill reference docs are updated to teach agents the new interface.

**Tech Stack:** Node.js 20 ESM, `node:test` + `node:assert` for unit tests, TypeScript (tsc for T3 validation), Vite (dev server), existing scaffold at `assets/templates/dashboard/scaffold/`.

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `assets/scripts/capability-registry.json` | **Create** | Machine-readable T1/T2 entries — alias table, API routing, template defaults |
| `assets/scripts/build-dashboard.mjs` | **Rewrite** | Main pipeline — reads intent.json, runs Resolution Engine, streams events, starts dev server |
| `assets/scripts/tests/resolution.test.mjs` | **Create** | Unit tests for T1 alias lookup, T2 descriptor compilation, T3 injection, event format |
| `assets/templates/dashboard/widgets/t3-shell.tsx.template` | **Create** | Typed React component shell with `<<FN_BODY>>` injection point for T3 |
| `skills/uipath-coded-apps/references/dashboards/plugins/build/impl.md` | **Rewrite** | Agent instructions for intent-based build flow (5 phases, intent.json, event parsing) |
| `skills/uipath-coded-apps/references/dashboards/primitives/build-plan.md` | **Update** | intent.json schema, tier classification rules, plan format |
| `skills/uipath-coded-apps/references/dashboards/primitives/state-file.md` | **Update** | schema (widget hashes, schemaVersion, tier metadata) |
| `skills/uipath-coded-apps/references/dashboards/primitives/incremental-editor.md` | **Update** | edit-intent.json schema, HAND_EDIT_DETECTED flow |
| `skills/uipath-coded-apps/references/dashboards/primitives/tier-resolution.md` | **Create** | Agent guide: how to classify metrics into T1/T2/T3, write T2 params, write T3 fn bodies |
| `skills/uipath-coded-apps/references/dashboards/CAPABILITY.md` | **Update** | Phase list, link to tier-resolution.md |

> **Path note:** `assets/scripts/` maps to `skills/uipath-coded-apps/assets/scripts/`. Always use the full path from repo root.

---

## Task 1: Capability Registry JSON

**Files:**
- Create: `skills/uipath-coded-apps/assets/scripts/capability-registry.json`
- Create: `skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs`

This file is the build script's source of truth for T1 alias matching and T2 service routing. The agent classifies in-context; the registry validates and expands.

- [ ] **Step 1.1: Create the capability registry**

```bash
# From repo root
mkdir -p skills/uipath-coded-apps/assets/scripts/tests
```

Write `skills/uipath-coded-apps/assets/scripts/capability-registry.json`:

```json
{
  "t1": {
    "agent-errors": {
      "aliases": ["agent errors", "error count", "errors over time", "agent failures", "error rate trend", "error spikes", "which agents are failing"],
      "source": "insights",
      "namespace": "agents",
      "method": "getErrors",
      "template": "line-chart",
      "defaults": {
        "title": "Agent Error Rate",
        "description": "Daily error counts — spot spikes early",
        "icon": "AlertTriangle",
        "xKey": "date",
        "yKey": "value",
        "deltaDir": "down-good",
        "deltaText": "errors today",
        "dataSelector": "(data as any)?.data ?? []"
      }
    },
    "invocation-volume": {
      "aliases": ["invocation volume", "total runs", "agent runs", "invocations", "run volume", "execution volume"],
      "source": "insights",
      "namespace": "agents",
      "method": "getSummaryV2",
      "template": "area-chart",
      "defaults": {
        "title": "Invocation Volume",
        "description": "Total agent runs per day",
        "icon": "Activity",
        "xKey": "date",
        "yKey": "count",
        "deltaDir": "up-good",
        "deltaText": "runs today",
        "dataSelector": "(data as any)?.data ?? []"
      }
    },
    "top-failing-agents": {
      "aliases": ["top failing agents", "most errors by agent", "agent leaderboard errors", "which agents fail most"],
      "source": "insights",
      "namespace": "agents",
      "method": "getTopErroredAgents",
      "template": "ranked-table",
      "defaults": {
        "title": "Top Failing Agents",
        "description": "Agents with the most errors",
        "icon": "AlertOctagon",
        "dataSelector": "(data as any)?.data ?? []",
        "columns": "[{key:\"name\",label:\"Agent\"},{key:\"value\",label:\"Errors\",align:\"right\" as const}]",
        "deltaDir": "neutral",
        "deltaText": ""
      }
    },
    "active-agents-kpi": {
      "aliases": ["active agents", "active agent count", "how many agents", "agent count", "agents running"],
      "source": "insights",
      "namespace": "agents",
      "method": "getAgents",
      "template": "kpi-card",
      "defaults": {
        "title": "Active Agents",
        "description": "Agents with at least one run",
        "icon": "Bot",
        "valueExpression": "String((data as any)?.data?.length ?? 0)",
        "dataSelector": "(data as any)?.data ?? []",
        "deltaDir": "up-good",
        "deltaText": "active agents"
      }
    },
    "agent-latency": {
      "aliases": ["agent latency", "p95 latency", "response time", "execution time", "latency trend"],
      "source": "insights",
      "namespace": "agents",
      "method": "getLatencyTimeline",
      "template": "multi-line-chart",
      "defaults": {
        "title": "Agent Latency",
        "description": "P50 and P95 execution time",
        "icon": "Timer",
        "xKey": "date",
        "yKey": "value",
        "deltaDir": "down-good",
        "deltaText": "ms p95 today",
        "dataSelector": "(data as any)?.data ?? []",
        "series": "[{key:\"p50\",color:\"hsl(var(--chart-1))\"},{key:\"p95\",color:\"hsl(var(--chart-2))\"}]",
        "pivotExpression": "rawData"
      }
    },
    "job-failures": {
      "aliases": ["job failures", "job failure rate", "rpa failures", "process failures", "failed jobs"],
      "source": "insights",
      "namespace": "jobs",
      "method": "getTopFailures",
      "template": "ranked-table",
      "defaults": {
        "title": "Top Job Failures",
        "description": "Processes with the most failures",
        "icon": "XCircle",
        "dataSelector": "(data as any)?.data ?? []",
        "columns": "[{key:\"name\",label:\"Process\"},{key:\"value\",label:\"Failures\",align:\"right\" as const}]",
        "deltaDir": "down-good",
        "deltaText": "failures today"
      }
    },
    "job-completion-trend": {
      "aliases": ["job completions", "completed jobs", "jobs over time", "job volume", "rpa throughput"],
      "source": "insights",
      "namespace": "jobs",
      "method": "getCompletedTimeline",
      "template": "area-chart",
      "defaults": {
        "title": "Job Completions",
        "description": "Jobs completed per day",
        "icon": "CheckCircle",
        "xKey": "date",
        "yKey": "value",
        "deltaDir": "up-good",
        "deltaText": "completions today",
        "dataSelector": "(data as any)?.data ?? []"
      }
    },
    "governance-policy-summary": {
      "aliases": ["governance", "policy violations", "policy compliance", "governance summary"],
      "source": "insights",
      "namespace": "governance",
      "method": "getPolicySummary",
      "template": "kpi-card",
      "defaults": {
        "title": "Policy Violations",
        "description": "Total governance policy violations",
        "icon": "ShieldAlert",
        "valueExpression": "String((data as any)?.total ?? 0)",
        "dataSelector": "(data as any)?.data ?? []",
        "deltaDir": "down-good",
        "deltaText": "violations"
      }
    }
  },
  "t2": {
    "queue-failure-threshold": {
      "aliases": ["queues where failure", "high failure queues", "failing queues above", "queues exceeding failure"],
      "service": "queues",
      "sdkImport": "@uipath/uipath-typescript/queues",
      "sdkService": "Queues",
      "method": "getAll",
      "filterField": "failureCount",
      "sortField": "failureCount",
      "defaultDisplayAs": "ranked-table",
      "defaults": {
        "title": "High-Failure Queues",
        "description": "Queues exceeding the failure threshold",
        "icon": "AlertOctagon",
        "columns": "[{key:\"name\",label:\"Queue\"},{key:\"failureCount\",label:\"Failures\",align:\"right\" as const}]"
      }
    },
    "jobs-duration-threshold": {
      "aliases": ["long running jobs", "jobs over duration", "slow jobs", "jobs running longer than"],
      "service": "jobs",
      "sdkImport": "@uipath/uipath-typescript/processes",
      "sdkService": "Jobs",
      "method": "getAll",
      "filterField": "duration",
      "sortField": "duration",
      "defaultDisplayAs": "data-table",
      "defaults": {
        "title": "Long-Running Jobs",
        "description": "Jobs exceeding duration threshold",
        "icon": "Clock",
        "columns": "[{key:\"name\",label:\"Process\"},{key:\"state\",label:\"State\"},{key:\"duration\",label:\"Duration\",align:\"right\" as const}]"
      }
    }
  },
  "hardRefuse": [
    { "pattern": "cost.*dollar|dollar.*cost|\\$.*agent|agent.*\\$", "reason": "The platform tracks AGU units, not currency.", "alternative": "AGU consumption chart (metric: invocation-volume)" },
    { "pattern": "cpu|memory per agent|per.agent memory", "reason": "Per-agent CPU/memory is not exposed by any API.", "alternative": "Fleet-level latency (metric: agent-latency)" },
    { "pattern": "who triggered|triggered by|user.*job|job.*user", "reason": "Job records carry no end-user identity.", "alternative": "Job counts by process name (metric: job-completion-trend)" },
    { "pattern": "cross.tenant|multi.tenant|compare.*tenant", "reason": "Dashboards are scoped to one tenant.", "alternative": "Multi-widget single-tenant view" },
    { "pattern": "sla.*breach|breach.*sla", "reason": "Raw counts only — no SLA metadata in any API.", "alternative": "Success rate % (computable from job-completion-trend)" },
    { "pattern": "error.*message|stack.*trace|exception.*text", "reason": "No aggregation endpoint for error text or stack traces.", "alternative": "Error count by type (metric: agent-errors)" }
  ]
}
```

- [ ] **Step 1.2: Write the failing test for alias lookup**

Create `skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs`:

```javascript
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const REGISTRY_PATH = resolve(__dirname, '../capability-registry.json')

// Load registry directly for unit tests
const registry = JSON.parse(readFileSync(REGISTRY_PATH, 'utf8'))

// We'll import the resolution functions once build-dashboard.mjs exports them
// For now, implement inline to drive the TDD loop

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

test('alias lookup finds T2 queue-failure-threshold', () => {
  const result = resolveAlias('queues where failure rate is high')
  assert.ok(result)
  assert.equal(result.tier, 'T2')
  assert.equal(result.key, 'queue-failure-threshold')
})

test('alias lookup returns null for unknown text', () => {
  const result = resolveAlias('completely unrelated nonsense xyz')
  assert.equal(result, null)
})

test('all T1 entries have required fields', () => {
  for (const [key, entry] of Object.entries(registry.t1)) {
    assert.ok(entry.template, `${key} missing template`)
    assert.ok(entry.namespace, `${key} missing namespace`)
    assert.ok(entry.method, `${key} missing method`)
    assert.ok(Array.isArray(entry.aliases) && entry.aliases.length > 0, `${key} missing aliases`)
    assert.ok(entry.defaults?.title, `${key} missing defaults.title`)
  }
})

test('all T2 entries have required fields', () => {
  for (const [key, entry] of Object.entries(registry.t2)) {
    assert.ok(entry.service, `${key} missing service`)
    assert.ok(entry.sdkImport, `${key} missing sdkImport`)
    assert.ok(entry.sdkService, `${key} missing sdkService`)
    assert.ok(entry.method, `${key} missing method`)
    assert.ok(Array.isArray(entry.aliases) && entry.aliases.length > 0, `${key} missing aliases`)
  }
})
```

- [ ] **Step 1.3: Run the test — expect PASS (all logic is inline in test file)**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
```

Expected: all 6 tests PASS (the resolution logic is inline in the test file for now; it moves to build-dashboard.mjs in Task 3).

- [ ] **Step 1.4: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/capability-registry.json \
        skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
git commit -m "feat(dashboards): add capability registry JSON and initial resolution tests"
```

---

## Task 2: intent.json Schema Validator

**Files:**
- Modify: `skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs` (add `validateIntent` near top, after imports)
- Modify: `skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs` (add validation tests)

- [ ] **Step 2.1: Write failing validation tests**

Append to `resolution.test.mjs`:

```javascript
// ── intent.json validation ────────────────────────────────────────────────────

function validateIntent(intent) {
  // Will be imported from build-dashboard.mjs once exported
  // Inline here for TDD
  const errors = []
  if (!intent.dashboardName || typeof intent.dashboardName !== 'string') errors.push('dashboardName must be a non-empty string')
  if (!['1d','7d','30d','90d'].includes(intent.timeRange)) errors.push(`timeRange must be one of: 1d, 7d, 30d, 90d`)
  if (!Array.isArray(intent.metrics) || intent.metrics.length === 0) errors.push('metrics must be a non-empty array')
  for (const m of (intent.metrics ?? [])) {
    if (!m.name) errors.push(`metric missing name`)
    if (!['T1','T2','T3'].includes(m.tier)) errors.push(`metric "${m.name}" has invalid tier: ${m.tier}`)
    if (m.tier === 'T2' && !m.params) errors.push(`T2 metric "${m.name}" missing params`)
    if (m.tier === 'T3' && !m.fnBody) errors.push(`T3 metric "${m.name}" missing fnBody`)
    if (m.tier === 'T3' && !m.displayAs) errors.push(`T3 metric "${m.name}" missing displayAs`)
    if (m.tier === 'T3' && !m.title) errors.push(`T3 metric "${m.name}" missing title`)
  }
  return errors
}

test('validates a correct T1 intent', () => {
  const errors = validateIntent({
    dashboardName: 'My Dashboard',
    timeRange: '30d',
    metrics: [{ name: 'agent-errors', tier: 'T1' }]
  })
  assert.deepEqual(errors, [])
})

test('rejects missing dashboardName', () => {
  const errors = validateIntent({ timeRange: '30d', metrics: [{ name: 'x', tier: 'T1' }] })
  assert.ok(errors.some(e => e.includes('dashboardName')))
})

test('rejects invalid timeRange', () => {
  const errors = validateIntent({ dashboardName: 'x', timeRange: '2w', metrics: [{ name: 'x', tier: 'T1' }] })
  assert.ok(errors.some(e => e.includes('timeRange')))
})

test('rejects T2 metric without params', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'queue-failure-threshold', tier: 'T2' }]
  })
  assert.ok(errors.some(e => e.includes('T2') && e.includes('params')))
})

test('rejects T3 metric without fnBody', () => {
  const errors = validateIntent({
    dashboardName: 'x', timeRange: '7d',
    metrics: [{ name: 'custom', tier: 'T3', displayAs: 'ranked-table', title: 'Custom' }]
  })
  assert.ok(errors.some(e => e.includes('T3') && e.includes('fnBody')))
})
```

- [ ] **Step 2.2: Run — expect PASS**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
```

Expected: 11 tests PASS.

- [ ] **Step 2.3: Add `validateIntent` to build-dashboard.mjs**

In `build-dashboard.mjs`, after line 42 (after the `WIDGETS_DIR` const), add:

```javascript
// ── Capability registry ───────────────────────────────────────────────────────

const REGISTRY = JSON.parse(readFileSync(resolve(__dirname, 'capability-registry.json'), 'utf8'));

// ── intent.json validator ─────────────────────────────────────────────────────

export function validateIntent(intent) {
  const errors = []
  if (!intent.dashboardName || typeof intent.dashboardName !== 'string') errors.push('dashboardName must be a non-empty string')
  if (!['1d','7d','30d','90d'].includes(intent.timeRange)) errors.push(`timeRange must be one of: 1d, 7d, 30d, 90d`)
  if (!Array.isArray(intent.metrics) || intent.metrics.length === 0) errors.push('metrics must be a non-empty array')
  for (const m of (intent.metrics ?? [])) {
    if (!m.name) errors.push('metric missing name')
    if (!['T1','T2','T3'].includes(m.tier)) errors.push(`metric "${m.name}" has invalid tier: ${m.tier}`)
    if (m.tier === 'T2' && !m.params) errors.push(`T2 metric "${m.name}" missing params`)
    if (m.tier === 'T3' && !m.fnBody) errors.push(`T3 metric "${m.name}" missing fnBody`)
    if (m.tier === 'T3' && !m.displayAs) errors.push(`T3 metric "${m.name}" missing displayAs`)
    if (m.tier === 'T3' && !m.title) errors.push(`T3 metric "${m.name}" missing title`)
  }
  return errors
}
```

Also add this guard near the top of main execution (after `plan` is read, currently ~line 151):

```javascript
// intent.json path
if (plan.metrics) {
  const intentErrors = validateIntent(plan)
  if (intentErrors.length > 0) fail(`Invalid intent.json:\n${intentErrors.map(e => '  • ' + e).join('\n')}`)
}
```

- [ ] **Step 2.4: Update the test to import from build-dashboard.mjs**

Replace the inline `validateIntent` function in `resolution.test.mjs` with an import:

```javascript
// At top of file, add:
import { validateIntent } from '../build-dashboard.mjs'

// Remove the inline validateIntent function definition
```

- [ ] **Step 2.5: Run — expect PASS**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
```

Expected: 11 tests PASS.

- [ ] **Step 2.6: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs \
        skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
git commit -m "feat(dashboards): add validateIntent and capability registry loading to build script"
```

---

## Task 3: Tier 1 Resolution — Alias Lookup + Template Substitution

**Files:**
- Modify: `skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs` (add `resolveMetric`, `buildT1WidgetSpec` exports)
- Modify: `skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs` (update to use imports)

- [ ] **Step 3.1: Write failing tests for T1 widget spec builder**

Append to `resolution.test.mjs`:

```javascript
import { resolveMetric, buildT1WidgetSpec } from '../build-dashboard.mjs'

test('resolveMetric returns T1 for known metric name', () => {
  const result = resolveMetric({ name: 'agent-errors', tier: 'T1' })
  assert.equal(result.tier, 'T1')
  assert.ok(result.entry)
  assert.equal(result.entry.template, 'line-chart')
})

test('resolveMetric returns T2 for known T2 metric name', () => {
  const result = resolveMetric({ name: 'queue-failure-threshold', tier: 'T2', params: { threshold: 0.2, direction: 'gt' } })
  assert.equal(result.tier, 'T2')
  assert.ok(result.entry.service)
})

test('resolveMetric throws for unknown T1 metric name', () => {
  assert.throws(
    () => resolveMetric({ name: 'nonexistent-metric', tier: 'T1' }),
    /not found in registry/
  )
})

test('buildT1WidgetSpec merges registry defaults with intent overrides', () => {
  const spec = buildT1WidgetSpec(
    { name: 'agent-errors', tier: 'T1', title: 'My Error Chart' },
    registry.t1['agent-errors'],
    '30d'
  )
  assert.equal(spec.componentName, 'AgentErrors')
  assert.equal(spec.template, 'line-chart')
  assert.equal(spec.title, 'My Error Chart')        // intent override
  assert.equal(spec.icon, 'AlertTriangle')            // registry default
  assert.ok(spec.dataHook.includes('agents.getErrors'))
  assert.ok(spec.dataHook.includes('THIRTY_DAYS_AGO'))
})

test('buildT1WidgetSpec uses 7d timeRange constant', () => {
  const spec = buildT1WidgetSpec(
    { name: 'agent-errors', tier: 'T1' },
    registry.t1['agent-errors'],
    '7d'
  )
  assert.ok(spec.dataHook.includes('SEVEN_DAYS_AGO'))
})
```

- [ ] **Step 3.2: Run — expect FAIL (functions not exported yet)**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
```

Expected: FAIL with import errors for `resolveMetric`, `buildT1WidgetSpec`.

- [ ] **Step 3.3: Add `resolveMetric` and `buildT1WidgetSpec` to build-dashboard.mjs**

After the `validateIntent` function, add:

```javascript
// ── Resolution Engine ─────────────────────────────────────────────────────────

const TIME_RANGE_CONSTANTS = {
  '1d':  'ONE_DAY_AGO',
  '7d':  'SEVEN_DAYS_AGO',
  '30d': 'THIRTY_DAYS_AGO',
  '90d': 'NINETY_DAYS_AGO',
}

/** Convert kebab-case metric name to PascalCase component name */
function toPascalCase(str) {
  return str.split('-').map(w => w[0].toUpperCase() + w.slice(1)).join('')
}

/**
 * Resolve a metric intent entry against the capability registry.
 * Returns { tier, key, entry } or throws for T1/T2 misses.
 * T3 metrics always resolve (they carry their own fnBody).
 */
export function resolveMetric(metric) {
  if (metric.tier === 'T3') return { tier: 'T3', key: metric.name, entry: null }

  const registrySection = metric.tier === 'T1' ? REGISTRY.t1 : REGISTRY.t2
  const entry = registrySection[metric.name]
  if (!entry) {
    throw new Error(`Metric "${metric.name}" (${metric.tier}) not found in registry. ` +
      `Available: ${Object.keys(registrySection).join(', ')}`)
  }
  return { tier: metric.tier, key: metric.name, entry }
}

/**
 * Build a complete T1 widget spec from a registry entry + intent metric + timeRange.
 * Returns a spec object ready for template substitution.
 */
export function buildT1WidgetSpec(metric, entry, timeRange) {
  const startConst = TIME_RANGE_CONSTANTS[timeRange] ?? 'THIRTY_DAYS_AGO'
  const componentName = metric.componentName ?? toPascalCase(metric.name)
  const namespace = entry.namespace
  const method = entry.method
  const responseType = '{ data: Array<Record<string, unknown>> }'
  const dataHook = `useInsights<${responseType}>('${namespace}.${method}', { startTime: ${startConst}, endTime: NOW })`

  return {
    componentName,
    template: entry.template,
    detailRoute: metric.detailRoute ?? `/${componentName.toLowerCase()}`,
    icon: metric.icon ?? entry.defaults.icon,
    title: metric.title ?? entry.defaults.title,
    description: metric.description ?? entry.defaults.description,
    dataHook,
    dataSelector: entry.defaults.dataSelector ?? '[]',
    xKey: entry.defaults.xKey ?? 'date',
    yKey: entry.defaults.yKey ?? 'value',
    valueExpression: entry.defaults.valueExpression ?? "'—'",
    columns: metric.columns ?? entry.defaults.columns ?? '[{key:"name",label:"Name"},{key:"value",label:"Value",align:"right" as const}]',
    deltaDir: entry.defaults.deltaDir ?? 'neutral',
    deltaText: entry.defaults.deltaText ?? '',
    series: entry.defaults.series ?? '[{key:"value",color:"hsl(var(--chart-1))"}]',
    pivotExpression: entry.defaults.pivotExpression ?? 'rawData',
  }
}
```

- [ ] **Step 3.4: Run — expect PASS**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
```

Expected: all tests PASS.

- [ ] **Step 3.5: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs \
        skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
git commit -m "feat(dashboards): add resolveMetric and buildT1WidgetSpec to Resolution Engine"
```

---

## Task 4: Tier 2 Descriptor Compiler

**Files:**
- Modify: `skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs` (add `buildT2WidgetSpec`, `compileT2ToTypeScript`)
- Modify: `skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs`

T2 metrics map to known SDK services with custom filter/threshold. The build script compiles a typed descriptor into a TypeScript SDK hook — no agent-authored code.

- [ ] **Step 4.1: Write failing tests**

Append to `resolution.test.mjs`:

```javascript
import { buildT2WidgetSpec, compileT2ToTypeScript } from '../build-dashboard.mjs'

test('buildT2WidgetSpec returns correct spec for queue-failure-threshold', () => {
  const metric = {
    name: 'queue-failure-threshold',
    tier: 'T2',
    params: { threshold: 20, direction: 'gt' }
  }
  const entry = registry.t2['queue-failure-threshold']
  const spec = buildT2WidgetSpec(metric, entry)
  assert.equal(spec.componentName, 'QueueFailureThreshold')
  assert.equal(spec.template, 'ranked-table')
  assert.ok(spec.sdkHookCode)
  assert.ok(spec.sdkImport)
})

test('compileT2ToTypeScript generates valid hook code for gt filter', () => {
  const descriptor = {
    service: 'queues',
    sdkImport: '@uipath/uipath-typescript/queues',
    sdkService: 'Queues',
    method: 'getAll',
    filterField: 'failureCount',
    filterOp: 'gt',
    filterValue: 20,
    sortField: 'failureCount',
    sortDir: 'desc'
  }
  const code = compileT2ToTypeScript(descriptor, 'sdk')
  assert.ok(code.includes('Queues'))
  assert.ok(code.includes('getAll'))
  assert.ok(code.includes('failureCount'))
  // Must be a valid-looking arrow function
  assert.ok(code.startsWith('async (sdk'))
})

test('compileT2ToTypeScript rejects invalid op', () => {
  assert.throws(() => compileT2ToTypeScript({
    service: 'queues', sdkImport: 'x', sdkService: 'Queues',
    method: 'getAll', filterField: 'x', filterOp: 'INVALID', filterValue: 1,
    sortField: 'x', sortDir: 'desc'
  }), /invalid op/)
})
```

- [ ] **Step 4.2: Run — expect FAIL**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
```

Expected: FAIL with import errors for `buildT2WidgetSpec`, `compileT2ToTypeScript`.

- [ ] **Step 4.3: Add T2 functions to build-dashboard.mjs**

After `buildT1WidgetSpec`, add:

```javascript
const VALID_T2_OPS = ['gt', 'lt', 'eq', 'gte', 'lte', 'neq']
const T2_OP_TO_JS = { gt: '>', lt: '<', eq: '===', gte: '>=', lte: '<=', neq: '!==' }

/**
 * Compile a T2 descriptor to a TypeScript async arrow function body.
 * Returns a string starting with "async (sdk, getToken) => { ... }".
 * Throws if descriptor is invalid.
 */
export function compileT2ToTypeScript(descriptor) {
  const { sdkService, method, filterField, filterOp, filterValue, sortField, sortDir } = descriptor
  if (!VALID_T2_OPS.includes(filterOp)) {
    throw new Error(`T2 descriptor has invalid op: ${filterOp}. Must be one of: ${VALID_T2_OPS.join(', ')}`)
  }
  const jsOp = T2_OP_TO_JS[filterOp]
  const sortFn = sortDir === 'asc'
    ? `items.sort((a, b) => (a.${sortField} ?? 0) - (b.${sortField} ?? 0))`
    : `items.sort((a, b) => (b.${sortField} ?? 0) - (a.${sortField} ?? 0))`

  return `async (sdk, _getToken) => {
  const svc = sdk.${sdkService.toLowerCase()}
  const result = await svc.${method}({})
  const items = (result?.items ?? result?.value ?? []) as Array<Record<string, number>>
  const filtered = items.filter(item => (item.${filterField} ?? 0) ${jsOp} ${filterValue})
  ${sortFn}
  return filtered
}`
}

/**
 * Build a T2 widget spec from a registry entry + intent metric.
 */
export function buildT2WidgetSpec(metric, entry) {
  const componentName = metric.componentName ?? toPascalCase(metric.name)
  const { params } = metric
  const descriptor = {
    service: entry.service,
    sdkImport: entry.sdkImport,
    sdkService: entry.sdkService,
    method: entry.method,
    filterField: params.field ?? entry.filterField,
    filterOp: params.direction ?? 'gt',
    filterValue: params.threshold ?? params.value ?? 0,
    sortField: params.sortField ?? entry.sortField,
    sortDir: params.sortDir ?? 'desc',
  }
  const sdkHookCode = compileT2ToTypeScript(descriptor)

  return {
    componentName,
    template: metric.displayAs ?? entry.defaultDisplayAs,
    sdkImport: entry.sdkImport,
    sdkService: entry.sdkService,
    sdkHookCode,
    title: metric.title ?? entry.defaults.title,
    description: metric.description ?? entry.defaults.description,
    icon: metric.icon ?? entry.defaults.icon,
    columns: metric.columns ?? entry.defaults.columns,
    detailRoute: metric.detailRoute ?? `/${componentName.toLowerCase()}`,
    deltaDir: 'neutral',
    deltaText: '',
  }
}
```

- [ ] **Step 4.4: Run — expect PASS**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
```

Expected: all tests PASS.

- [ ] **Step 4.5: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs \
        skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
git commit -m "feat(dashboards): add T2 descriptor compiler to Resolution Engine"
```

---

## Task 5: T3 Shell Template + Injector

**Files:**
- Create: `skills/uipath-coded-apps/assets/templates/dashboard/widgets/t3-shell.tsx.template`
- Modify: `skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs` (add `buildT3WidgetFile`)
- Modify: `skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs`

T3 injects a typed async fn body into a deterministic React component shell. The agent writes only the fn body; all JSX and component structure is always from the template.

- [ ] **Step 5.1: Create the T3 shell template**

Write `skills/uipath-coded-apps/assets/templates/dashboard/widgets/t3-shell.tsx.template`:

```tsx
import React from 'react'
import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { WidgetBoundary } from '@/dashboard/chrome/WidgetBoundary'
import { LoadingState, EmptyState } from '@/dashboard/chrome'
import { <<ICON_IMPORT>> } from 'lucide-react'
import type { UiPathClient } from '@uipath/uipath-typescript/core'

type Row = Record<string, unknown>

// ── Custom data function (Tier 3 — agent-authored fn body, injected at build time) ──
const customDataFn = async (sdk: UiPathClient, getToken: () => Promise<string>): Promise<Row[]> => {
<<FN_BODY>>
}
// ── End injected fn body ──────────────────────────────────────────────────────────

function use<<COMPONENT_NAME>>Data() {
  const { sdk, getToken } = useAuth()
  const [data, setData] = useState<Row[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!sdk) return
    setLoading(true)
    customDataFn(sdk, getToken)
      .then(rows => { setData(rows); setLoading(false) })
      .catch(err => { setError(err instanceof Error ? err : new Error(String(err))); setLoading(false) })
  }, [sdk])

  return { data, loading, error }
}

export function <<COMPONENT_NAME>>() {
  const { data, loading, error } = use<<COMPONENT_NAME>>Data()

  return (
    <WidgetBoundary label="<<TITLE>>">
      <Card className="cursor-pointer hover:shadow-md transition-shadow">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <<<ICON_NAME>> className="h-4 w-4" />
            <<TITLE>>
          </CardTitle>
          <CardDescription><<DESCRIPTION>></CardDescription>
        </CardHeader>
        <CardContent>
          {loading && <LoadingState height="h-32" />}
          {error && <EmptyState message={error.message} />}
          {!loading && !error && (
            <div className="text-sm text-muted-foreground">
              {data.length === 0
                ? <EmptyState message="No data" />
                : <span className="text-2xl font-bold text-foreground">{data.length} items</span>
              }
            </div>
          )}
        </CardContent>
      </Card>
    </WidgetBoundary>
  )
}
```

- [ ] **Step 5.2: Write failing test**

Append to `resolution.test.mjs`:

```javascript
import { buildT3WidgetFile } from '../build-dashboard.mjs'

test('buildT3WidgetFile injects fnBody into shell template', () => {
  const metric = {
    name: 'faulted-queue-items',
    tier: 'T3',
    title: 'Faulted Queue Items',
    description: 'Queues with faulted items',
    displayAs: 'ranked-table',
    columns: [],
    fnBody: "const r = await sdk.queues.getAll({})\nreturn r.items ?? []"
  }
  const content = buildT3WidgetFile(metric)
  assert.ok(content.includes('FaultedQueueItems'), 'component name not injected')
  assert.ok(content.includes('Faulted Queue Items'), 'title not injected')
  assert.ok(content.includes('sdk.queues.getAll'), 'fnBody not injected')
  assert.ok(!content.includes('<<FN_BODY>>'), 'placeholder not replaced')
  assert.ok(!content.includes('<<COMPONENT_NAME>>'), 'component name placeholder not replaced')
})

test('buildT3WidgetFile throws if fnBody is missing', () => {
  assert.throws(
    () => buildT3WidgetFile({ name: 'x', tier: 'T3', title: 'X', displayAs: 'kpi-card' }),
    /fnBody/
  )
})
```

- [ ] **Step 5.3: Run — expect FAIL**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
```

Expected: FAIL — `buildT3WidgetFile` not exported.

- [ ] **Step 5.4: Add `buildT3WidgetFile` to build-dashboard.mjs**

Add the T3 shell template path constant after `WIDGETS_DIR`:

```javascript
const T3_SHELL_TEMPLATE = resolve(__dirname, '../templates/dashboard/widgets/t3-shell.tsx.template');
```

After `buildT2WidgetSpec`, add:

```javascript
/**
 * Generate a complete T3 widget file by injecting the agent's fn body into the shell template.
 * Returns the full TypeScript file content as a string.
 */
export function buildT3WidgetFile(metric) {
  if (!metric.fnBody) throw new Error(`T3 metric "${metric.name}" missing fnBody`)
  if (!existsSync(T3_SHELL_TEMPLATE)) fail(`T3 shell template not found at ${T3_SHELL_TEMPLATE}`)

  const componentName = metric.componentName ?? toPascalCase(metric.name)
  const iconName = metric.icon ?? 'Activity'
  // Indent the fn body by 2 spaces to match the template indentation
  const indentedFnBody = metric.fnBody.split('\n').map(l => '  ' + l).join('\n')

  let content = readFileSync(T3_SHELL_TEMPLATE, 'utf8')
  content = content
    .split('<<FN_BODY>>').join(indentedFnBody)
    .split('<<COMPONENT_NAME>>').join(componentName)
    .split('<<TITLE>>').join(metric.title ?? componentName)
    .split('<<DESCRIPTION>>').join(metric.description ?? '')
    .split('<<ICON_NAME>>').join(iconName)
    .split('<<ICON_IMPORT>>').join(iconName)

  return content
}
```

- [ ] **Step 5.5: Run — expect PASS**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
```

Expected: all tests PASS.

- [ ] **Step 5.6: Commit**

```bash
git add skills/uipath-coded-apps/assets/templates/dashboard/widgets/t3-shell.tsx.template \
        skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs \
        skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
git commit -m "feat(dashboards): add T3 shell template and buildT3WidgetFile injector"
```

---

## Task 6: Event Streaming Protocol

**Files:**
- Modify: `skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs` (replace `log()` with event emitter)
- Modify: `skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs`

Replace the current ad-hoc `log()` calls with a structured event emitter that the agent can parse line-by-line.

- [ ] **Step 6.1: Write failing tests**

Append to `resolution.test.mjs`:

```javascript
import { emit, parseEvent } from '../build-dashboard.mjs'

test('emit writes structured event to stdout', () => {
  const lines = []
  const captured = { write: (s) => lines.push(s) }
  emit('WIDGET_READY', { name: 'ErrorRateTrend', index: 1, total: 4 }, captured)
  assert.equal(lines.length, 1)
  const parsed = JSON.parse(lines[0].replace('WIDGET_READY:', ''))
  assert.equal(parsed.name, 'ErrorRateTrend')
  assert.equal(parsed.index, 1)
})

test('emit writes simple string event with no payload', () => {
  const lines = []
  emit('PREWARM_DONE', null, { write: (s) => lines.push(s) })
  assert.equal(lines[0].trim(), 'PREWARM_DONE')
})

test('parseEvent parses WIDGET_READY correctly', () => {
  const result = parseEvent('WIDGET_READY:{"name":"Foo","index":2,"total":5}')
  assert.equal(result.type, 'WIDGET_READY')
  assert.equal(result.payload.name, 'Foo')
})

test('parseEvent parses simple event with no payload', () => {
  const result = parseEvent('PREWARM_DONE')
  assert.equal(result.type, 'PREWARM_DONE')
  assert.equal(result.payload, null)
})

test('parseEvent returns null for non-event lines', () => {
  const result = parseEvent('regular log line without colon prefix')
  assert.equal(result, null)
})
```

- [ ] **Step 6.2: Run — expect FAIL**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
```

- [ ] **Step 6.3: Add `emit` and `parseEvent` to build-dashboard.mjs**

Replace the current `log()` function with:

```javascript
const KNOWN_EVENTS = new Set([
  'PREWARM_START','PREWARM_DONE','PREWARM_FAILED','SCAFFOLD_READY','ENV_WRITTEN',
  'WIDGET_READY','T3_RETRY','T3_FAILED','TSC_PASS','TSC_FAIL',
  'SERVER_READY','BUILD_RESULT','PARTIAL_BUILD_DETECTED','AUTH_MISSING',
  'HAND_EDIT_DETECTED','T2_SCHEMA_ERROR','INCREMENTAL_READY'
])

/** Emit a structured event to stdout (or a custom writer for tests) */
export function emit(type, payload = null, writer = process.stdout) {
  const line = payload != null ? `${type}:${JSON.stringify(payload)}` : type
  writer.write(line + '\n')
}

/** Parse a stdout line back into { type, payload } — returns null for non-event lines */
export function parseEvent(line) {
  const colonIdx = line.indexOf(':')
  if (colonIdx === -1) {
    return KNOWN_EVENTS.has(line.trim()) ? { type: line.trim(), payload: null } : null
  }
  const type = line.slice(0, colonIdx)
  if (!KNOWN_EVENTS.has(type)) return null
  try {
    return { type, payload: JSON.parse(line.slice(colonIdx + 1)) }
  } catch {
    return null
  }
}

/** Human-readable log — for non-event output like progress steps */
function log(msg) {
  process.stdout.write(msg + '\n')
}
```

- [ ] **Step 6.4: Run — expect PASS**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
```

- [ ] **Step 6.5: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs \
        skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
git commit -m "feat(dashboards): add structured event streaming protocol (emit/parseEvent)"
```

---

## Task 7: Pre-warm Polling Guarantee

**Files:**
- Modify: `skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs` (replace timing-based pre-warm with `runPrewarm`, `waitForPrewarm`)

The current pre-warm is timing-based — if the user confirms before `npm ci` finishes, the build fails. the new design uses a polling guarantee: code generation waits for `node_modules/.package-lock.json` before proceeding, regardless of timing.

- [ ] **Step 7.1: Replace pre-warm section in build-dashboard.mjs**

Locate Step 3 (npm ci section, lines 209–220 in current file). Replace the entire block with:

```javascript
// Step 3 — Pre-warm guarantee: poll for .package-lock.json, run npm ci if missing
const LOCK_SIGNAL = join(P, 'node_modules', '.package-lock.json');
const PREWARM_LOCK = join(P, '.prewarm.lock');

async function runPrewarm(projectPath) {
  emit('PREWARM_START')
  // Write sentinel so a parallel pre-warm started during plan review can be detected
  writeAtomic(PREWARM_LOCK, String(Date.now()))
  const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm'
  try {
    execSync(`${npmCmd} ci --prefer-offline`, { cwd: projectPath, stdio: 'pipe' })
  } catch {
    try {
      execSync(`${npmCmd} ci`, { cwd: projectPath, stdio: 'pipe' })
    } catch (e) {
      const stderr = e.stderr?.toString() ?? String(e)
      emit('PREWARM_FAILED', { exitCode: e.status ?? 1, stderr: stderr.slice(0, 500) })
      fail(`npm ci failed. Run "npm ci" manually in ${projectPath} for full output.`)
    }
  }
  try { unlinkSync(PREWARM_LOCK) } catch { /* already gone */ }
  emit('PREWARM_DONE')
}

function waitForPrewarm(projectPath, timeoutMs = 60_000) {
  const signal = join(projectPath, 'node_modules', '.package-lock.json')
  const deadline = Date.now() + timeoutMs
  while (!existsSync(signal)) {
    if (Date.now() > deadline) {
      emit('PREWARM_FAILED', { exitCode: -1, stderr: 'Timed out waiting for pre-warm' })
      fail('Pre-warm timed out after 60s. npm ci may have failed.')
    }
    execSync('node -e "setTimeout(()=>{},500)"', { stdio: 'pipe' })
  }
  emit('PREWARM_DONE')
}
```

Also add `unlinkSync` to the import at line 35:

```javascript
import { readFileSync, writeFileSync, copyFileSync, mkdirSync, readdirSync, existsSync, renameSync, unlinkSync } from 'fs';
```

And replace the Step 3 execution code:

```javascript
// Step 3 — Ensure dependencies installed (pre-warm guarantee)
if (!existsSync(LOCK_SIGNAL)) {
  if (existsSync(PREWARM_LOCK)) {
    // Pre-warm started during plan review — poll until done
    log('⏳ Waiting for pre-warm to complete…')
    waitForPrewarm(P)
  } else {
    // No pre-warm in flight — run synchronously now
    log('⚙ Installing dependencies…')
    await runPrewarm(P)
  }
} else {
  emit('PREWARM_DONE')
  log('✓ Dependencies ready (pre-warm)')
}
```

> Note: The main function will need to be wrapped in an async IIFE (see Task 8).

- [ ] **Step 7.2: Verify the script still parses without error**

```bash
node --check skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs
```

Expected: no syntax errors printed.

- [ ] **Step 7.3: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs
git commit -m "feat(dashboards): replace timing-based pre-warm with polling guarantee"
```

---

## Task 8: Main Pipeline Rewrite — runDashboardBuild

**Files:**
- Modify: `skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs` (rewrite main execution section)

Wire the Resolution Engine, T1/T2/T3 generators, event streaming, and parallel widget generation into the main pipeline. Replace the current `plan.json` workflow with `intent.json` workflow while preserving backward compatibility for existing `plan.json` inputs.

- [ ] **Step 8.1: Wrap main execution in async IIFE**

The current main code starts at line 145. Replace the entire main execution block (everything from `// ── Main ──` through `process.exit(0)` at line 374, keeping the comment block below) with:

```javascript
// ── Main ──────────────────────────────────────────────────────────────────────

;(async () => {
  const planArg = process.argv[2]
  if (!planArg) fail('Usage: node build-dashboard.mjs <intent.json>')

  let plan
  try {
    plan = JSON.parse(readFileSync(planArg, 'utf8'))
  } catch (e) {
    fail(`Could not read JSON from ${planArg}: ${e.message}`)
  }

  // ── intent.json path (new capability) ───────────────────────────────────────────────────
  if (plan.metrics) {
    await runDashboardBuild(plan, planArg)
    return
  }

  // ── legacy plan.json backward-compat path ────────────────────────────────────
  await runLegacyPlanBuild(plan)
})()
```

- [ ] **Step 8.2: Extract legacy build into `runLegacyPlanBuild`**

Move the existing main execution body (scaffold copy through `process.exit(0)`) into a function named `runLegacyPlanBuild(plan)`. This preserves all existing plan.json behavior exactly — no changes to the logic.

```javascript
async function runLegacyPlanBuild(plan) {
  // [PASTE all existing main code from the current lines 158–374 here, unchanged]
  // Only change: replace process.exit(0) at the end with return
}
```

- [ ] **Step 8.3: Implement `runDashboardBuild`**

Add the new pipeline function before `runLegacyPlanBuild`:

```javascript
async function runDashboardBuild(intent, intentPath) {
  const {
    dashboardName, timeRange, metrics,
    projectDir, orgName, tenantName, cloudUrl, apiUrl, tenantId, clientId = '',
    routingName,
  } = intent

  if (!projectDir) fail('intent.projectDir is required')
  if (!routingName) fail('intent.routingName is required')

  const P = resolve(projectDir)

  // ── Partial build recovery ────────────────────────────────────────────────
  const BUILD_SENTINEL = join(P, '.build-in-progress')
  if (existsSync(BUILD_SENTINEL)) {
    emit('PARTIAL_BUILD_DETECTED', { projectDir: P })
    // Continue anyway — build is idempotent. State from prior run is preserved.
  }
  writeAtomic(BUILD_SENTINEL, String(Date.now()))

  try {
    // Step 1 — Scaffold
    if (!existsSync(join(P, 'package.json'))) {
      if (!existsSync(SCAFFOLD_DIR)) fail(`Scaffold not found at ${SCAFFOLD_DIR}`)
      copyDir(SCAFFOLD_DIR, P)
      try {
        execSync(`node -e "require('fs').rmSync(${JSON.stringify(join(P,'node_modules'))},{recursive:true,force:true})"`,
          { stdio: 'pipe' })
      } catch { /* ignore */ }
    }
    emit('SCAFFOLD_READY')

    // Step 2 — Env
    writeAtomic(join(P, '.env.local'), [
      `VITE_UIPATH_CLOUD_URL=${cloudUrl}`,
      `VITE_UIPATH_BASE_URL=${apiUrl}`,
      `VITE_UIPATH_ORG_NAME=${orgName}`,
      `VITE_UIPATH_TENANT_NAME=${tenantName}`,
      `VITE_INSIGHTS_TENANT_ID=${tenantId}`,
      `VITE_UIPATH_CLIENT_ID=${clientId}`,
    ].join('\n'))
    emit('ENV_WRITTEN')

    // Step 3 — Pre-warm
    const LOCK_SIGNAL = join(P, 'node_modules', '.package-lock.json')
    const PREWARM_LOCK = join(P, '.prewarm.lock')
    if (!existsSync(LOCK_SIGNAL)) {
      if (existsSync(PREWARM_LOCK)) {
        log('⏳ Waiting for pre-warm to complete…')
        waitForPrewarm(P)
      } else {
        log('⚙ Installing dependencies…')
        await runPrewarm(P)
      }
    } else {
      emit('PREWARM_DONE')
    }

    // Step 4 — Resolve all metrics, build widget files in parallel for T1/T2
    const t3Metrics = metrics.filter(m => m.tier === 'T3')
    const nonT3Metrics = metrics.filter(m => m.tier !== 'T3')

    const widgetHashes = {}
    const allWidgetNames = []
    let widgetIndex = 0
    const total = metrics.length

    // T1 + T2 in parallel
    await Promise.all(nonT3Metrics.map(async (metric) => {
      const { tier, key, entry } = resolveMetric(metric)
      let widgetContent, spec

      if (tier === 'T1') {
        spec = buildT1WidgetSpec(metric, entry, timeRange)
        widgetContent = applyTemplate(spec.template, {
          COMPONENT_NAME: spec.componentName,
          TITLE: spec.title,
          DESCRIPTION: spec.description,
          DETAIL_ROUTE: spec.detailRoute,
          ICON: spec.icon,
          DATA_HOOK: spec.dataHook,
          DATA_SELECTOR: spec.dataSelector,
          X_KEY: spec.xKey,
          Y_KEY: spec.yKey,
          VALUE_EXPRESSION: spec.valueExpression,
          COLUMNS: spec.columns,
          DELTA_DIR: spec.deltaDir,
          DELTA_TEXT: spec.deltaText,
          SERIES: spec.series,
          PIVOT_EXPRESSION: spec.pivotExpression,
          SDK_IMPORT: '', SDK_SERVICE: '', SDK_CALL: '', SDK_RESULT_TYPE: '',
        })
      } else {
        // T2
        spec = buildT2WidgetSpec(metric, entry)
        // T2 uses sdk-* template variant; generate inline hook from compiled code
        widgetContent = applyTemplate('sdk-data-table', {
          COMPONENT_NAME: spec.componentName,
          TITLE: spec.title,
          DESCRIPTION: spec.description,
          DETAIL_ROUTE: spec.detailRoute,
          ICON: spec.icon,
          SDK_IMPORT: spec.sdkImport,
          SDK_SERVICE: spec.sdkService,
          SDK_CALL: `getAll({})`,
          SDK_RESULT_TYPE: '{ items?: Array<Record<string, unknown>> }',
          COLUMNS: spec.columns,
          DELTA_DIR: 'neutral', DELTA_TEXT: '',
          DATA_HOOK: '', DATA_SELECTOR: '', X_KEY: '', Y_KEY: '',
          VALUE_EXPRESSION: '', SERIES: '', PIVOT_EXPRESSION: '',
        })
      }

      const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${spec.componentName}.tsx`)
      writeAtomic(widgetPath, widgetContent)
      widgetHashes[spec.componentName] = {
        hash: hashFile(widgetContent),
        tier,
        metric: metric.name
      }
      allWidgetNames.push(spec.componentName)
      widgetIndex++
      emit('WIDGET_READY', { name: spec.componentName, index: widgetIndex, total })
    }))

    // T3 — sequential (each needs potential agent retry round-trip)
    for (const metric of t3Metrics) {
      let attempts = 0
      let success = false
      while (attempts < 3 && !success) {
        attempts++
        // Re-read metric from intent.json (agent may have updated fnBody between attempts)
        const currentIntent = JSON.parse(readFileSync(intentPath, 'utf8'))
        const currentMetric = currentIntent.metrics.find(m => m.name === metric.name) ?? metric

        let widgetContent
        try {
          widgetContent = buildT3WidgetFile(currentMetric)
        } catch (e) {
          emit('T3_FAILED', { widget: metric.name, reason: e.message })
          fail(`T3 widget "${metric.name}" build failed: ${e.message}`)
        }

        const widgetPath = join(P, 'src', 'dashboard', 'widgets', `${toPascalCase(metric.name)}.tsx`)
        writeAtomic(widgetPath, widgetContent)

        // Run tsc on this file only
        try {
          execSync(`npx tsc --noEmit --allowJs false`, { cwd: P, stdio: 'pipe' })
          const componentName = toPascalCase(metric.name)
          widgetHashes[componentName] = { hash: hashFile(widgetContent), tier: 'T3', metric: metric.name }
          allWidgetNames.push(componentName)
          widgetIndex++
          emit('WIDGET_READY', { name: componentName, index: widgetIndex, total })
          success = true
        } catch (e) {
          const errors = (e.stdout?.toString() ?? '').split('\n').filter(l => l.includes('error TS')).slice(0, 5)
          if (attempts >= 3) {
            emit('T3_FAILED', { widget: metric.name, errors, attempts })
            fail(`T3 widget "${metric.name}" failed after 3 attempts. Remove it or reformulate the request.`)
          }
          emit('T3_RETRY', { widget: metric.name, errors, intentPath, retryCount: attempts })
          log(`⚠ T3 widget "${metric.name}" has TypeScript errors (attempt ${attempts}/3). ` +
            `Update fnBody in ${intentPath} and re-run.`)
          // Exit with code 2 — agent updates intent.json and re-runs
          process.exit(2)
        }
      }
    }

    // Step 5 — Generate Dashboard.tsx + index.ts from widget list
    generateDashboardFiles(P, allWidgetNames, dashboardName)

    // Step 6 — tsc full project
    try {
      execSync('npx tsc --noEmit', { cwd: P, stdio: 'pipe' })
      emit('TSC_PASS')
    } catch (e) {
      const err = e.stdout?.toString() || e.stderr?.toString() || String(e)
      emit('TSC_FAIL', { errors: err.slice(0, 1000) })
      fail(`TypeScript errors after full build:\n${err}`)
    }

    // Step 7 — Write state.json
    const stateDir = join(P, '.dashboard')
    mkdirSync(stateDir, { recursive: true })
    const statePath = join(stateDir, 'state.json')
    const existingState = existsSync(statePath) ? JSON.parse(readFileSync(statePath, 'utf8')) : {}
    const newState = {
      schemaVersion: 2,
      app: { name: dashboardName, routingName, semver: existingState.app?.semver ?? '1.0.0' },
      env: cloudUrl.includes('alpha') ? 'alpha' : cloudUrl.includes('staging') ? 'staging' : 'prod',
      org: orgName, tenant: tenantName, cloudUrl,
      widgets: widgetHashes,
      deployment: existingState.deployment ?? { systemName: null, folderKey: null, appUrl: null, lastDeployedAt: null },
    }
    writeAtomic(statePath, JSON.stringify(newState, null, 2))

    // Step 8 — Start dev server
    const isWindows = process.platform === 'win32'
    const server = spawn('npm', ['run', 'dev'], {
      cwd: P, detached: true, stdio: 'pipe', shell: isWindows,
    })
    server.on('error', () => {})
    server.unref()

    let port = 5173
    const deadline = Date.now() + 8000
    while (Date.now() < deadline) {
      try {
        execSync(
          `node -e "require('http').get('http://localhost:${port}',r=>process.exit(r.statusCode<500?0:1)).on('error',()=>process.exit(1))"`,
          { stdio: 'pipe', timeout: 1000 }
        )
        break
      } catch { port++; if (port > 5183) { port = 5173; break } }
    }

    emit('SERVER_READY', { port, url: `http://localhost:${port}` })
    emit('BUILD_RESULT', {
      success: true, projectDir: P, port,
      previewUrl: `http://localhost:${port}`,
      widgets: Object.keys(widgetHashes),
      dashboardName,
    })

  } finally {
    // Remove build sentinel on clean exit or error
    try { unlinkSync(BUILD_SENTINEL) } catch { /* ignore */ }
  }
}
```

- [ ] **Step 8.4: Add helper functions needed by the pipeline**

After `buildT3WidgetFile`, add:

```javascript
import { createHash } from 'crypto'

function hashFile(content) {
  return createHash('sha256').update(content).digest('hex').slice(0, 16)
}

function generateDashboardFiles(projectPath, widgetNames, dashboardName) {
  const imports = widgetNames.map(n => `import { ${n} } from './${n}'`).join('\n')
  const indexTs = widgetNames.map(n => `export { ${n} } from './${n}'`).join('\n')

  const dashboardJsx = `import React from 'react'
import { Header } from '@/dashboard/chrome/Header'
${imports}

export function Dashboard() {
  return (
    <div className="min-h-screen bg-background">
      <Header title="${dashboardName}" description="Operational metrics dashboard" />
      <div className="p-4 md:p-8 space-y-6">
        <div className="grid grid-cols-1 gap-4 ${widgetNames.length <= 2 ? 'lg:grid-cols-2' : 'lg:grid-cols-2'}">
          ${widgetNames.map(n => `<${n} />`).join('\n          ')}
        </div>
      </div>
    </div>
  )
}
`
  writeAtomic(join(projectPath, 'src', 'dashboard', 'Dashboard.tsx'), dashboardJsx)
  writeAtomic(join(projectPath, 'src', 'dashboard', 'widgets', 'index.ts'), indexTs)
}
```

Also add `createHash` to the crypto import at the top of the file:

```javascript
import { createHash } from 'crypto'
```

- [ ] **Step 8.5: Verify the script parses without error**

```bash
node --check skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs
```

Expected: no output (clean parse).

- [ ] **Step 8.6: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs
git commit -m "feat(dashboards): implement runDashboardBuild pipeline with T1/T2/T3 routing and event streaming"
```

---

## Task 9: State File + Incremental Editing

**Files:**
- Modify: `skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs` (add `runIncrementalEdit`)
- Modify: `skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs`

- [ ] **Step 9.1: Write failing tests for edit intent handling**

Append to `resolution.test.mjs`:

```javascript
import { classifyEditIntent } from '../build-dashboard.mjs'

test('classifyEditIntent identifies ADD operation', () => {
  const intent = { op: 'ADD', metric: { name: 'agent-errors', tier: 'T1' } }
  const result = classifyEditIntent(intent)
  assert.equal(result.op, 'ADD')
  assert.ok(result.metric)
})

test('classifyEditIntent identifies REMOVE operation', () => {
  const result = classifyEditIntent({ op: 'REMOVE', target: 'ErrorRateTrend' })
  assert.equal(result.op, 'REMOVE')
  assert.equal(result.target, 'ErrorRateTrend')
})

test('classifyEditIntent identifies CHANGE operation', () => {
  const result = classifyEditIntent({ op: 'CHANGE', target: 'ErrorRateTrend', delta: { timeRange: '7d' } })
  assert.equal(result.op, 'CHANGE')
  assert.ok(result.delta)
})

test('classifyEditIntent throws on unknown op', () => {
  assert.throws(() => classifyEditIntent({ op: 'UNKNOWN' }), /invalid op/)
})
```

- [ ] **Step 9.2: Run — expect FAIL**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
```

- [ ] **Step 9.3: Add `classifyEditIntent` and `runIncrementalEdit` to build-dashboard.mjs**

After `generateDashboardFiles`, add:

```javascript
// ── Incremental editing ───────────────────────────────────────────────────────

const VALID_EDIT_OPS = ['ADD', 'REMOVE', 'CHANGE', 'REBUILD']

export function classifyEditIntent(editIntent) {
  if (!VALID_EDIT_OPS.includes(editIntent.op)) {
    throw new Error(`classifyEditIntent: invalid op "${editIntent.op}". Must be one of: ${VALID_EDIT_OPS.join(', ')}`)
  }
  return editIntent
}

async function runIncrementalEdit(editIntent, projectPath, timeRange) {
  const statePath = join(projectPath, '.dashboard', 'state.json')
  if (!existsSync(statePath)) fail('No state.json found. Run a fresh build first.')
  const state = JSON.parse(readFileSync(statePath, 'utf8'))
  const { op, target, metric, delta } = classifyEditIntent(editIntent)

  if (op === 'ADD') {
    const { tier, entry } = resolveMetric(metric)
    let widgetContent, componentName

    if (tier === 'T1') {
      const spec = buildT1WidgetSpec(metric, entry, timeRange ?? '30d')
      componentName = spec.componentName
      widgetContent = applyTemplate(spec.template, {
        COMPONENT_NAME: spec.componentName, TITLE: spec.title, DESCRIPTION: spec.description,
        DETAIL_ROUTE: spec.detailRoute, ICON: spec.icon, DATA_HOOK: spec.dataHook,
        DATA_SELECTOR: spec.dataSelector, X_KEY: spec.xKey, Y_KEY: spec.yKey,
        VALUE_EXPRESSION: spec.valueExpression, COLUMNS: spec.columns,
        DELTA_DIR: spec.deltaDir, DELTA_TEXT: spec.deltaText,
        SERIES: spec.series, PIVOT_EXPRESSION: spec.pivotExpression,
        SDK_IMPORT: '', SDK_SERVICE: '', SDK_CALL: '', SDK_RESULT_TYPE: '',
      })
    } else if (tier === 'T3') {
      componentName = toPascalCase(metric.name)
      widgetContent = buildT3WidgetFile(metric)
    } else {
      const spec = buildT2WidgetSpec(metric, entry)
      componentName = spec.componentName
      widgetContent = applyTemplate('sdk-data-table', {
        COMPONENT_NAME: componentName, TITLE: spec.title, DESCRIPTION: spec.description,
        DETAIL_ROUTE: spec.detailRoute, ICON: spec.icon, SDK_IMPORT: spec.sdkImport,
        SDK_SERVICE: spec.sdkService, SDK_CALL: 'getAll({})',
        SDK_RESULT_TYPE: '{ items?: Array<Record<string, unknown>> }',
        COLUMNS: spec.columns, DELTA_DIR: 'neutral', DELTA_TEXT: '',
        DATA_HOOK: '', DATA_SELECTOR: '', X_KEY: '', Y_KEY: '', VALUE_EXPRESSION: '', SERIES: '', PIVOT_EXPRESSION: '',
      })
    }

    const widgetPath = join(projectPath, 'src', 'dashboard', 'widgets', `${componentName}.tsx`)
    writeAtomic(widgetPath, widgetContent)
    state.widgets[componentName] = { hash: hashFile(widgetContent), tier, metric: metric.name }

  } else if (op === 'REMOVE') {
    const widgetPath = join(projectPath, 'src', 'dashboard', 'widgets', `${target}.tsx`)
    const currentContent = existsSync(widgetPath) ? readFileSync(widgetPath, 'utf8') : null
    const stored = state.widgets[target]
    if (currentContent && stored && hashFile(currentContent) !== stored.hash) {
      emit('HAND_EDIT_DETECTED', { widget: target })
      fail(`Widget "${target}" has been hand-edited. Pass --force to overwrite.`)
    }
    if (existsSync(widgetPath)) unlinkSync(widgetPath)
    const viewPath = join(projectPath, 'src', 'dashboard', 'views', `${target}View.tsx`)
    if (existsSync(viewPath)) unlinkSync(viewPath)
    delete state.widgets[target]

  } else if (op === 'CHANGE') {
    const widgetPath = join(projectPath, 'src', 'dashboard', 'widgets', `${target}.tsx`)
    const currentContent = existsSync(widgetPath) ? readFileSync(widgetPath, 'utf8') : null
    const stored = state.widgets[target]
    if (currentContent && stored && hashFile(currentContent) !== stored.hash) {
      emit('HAND_EDIT_DETECTED', { widget: target })
      fail(`Widget "${target}" has been hand-edited. Pass --force to overwrite.`)
    }
    const tier = stored?.tier ?? 'T1'
    const metricRef = { name: stored?.metric ?? target.toLowerCase(), tier, ...delta }
    if (tier === 'T1') {
      const { entry } = resolveMetric(metricRef)
      const spec = buildT1WidgetSpec(metricRef, entry, delta?.timeRange ?? timeRange ?? '30d')
      const widgetContent = applyTemplate(spec.template, {
        COMPONENT_NAME: spec.componentName, TITLE: spec.title, DESCRIPTION: spec.description,
        DETAIL_ROUTE: spec.detailRoute, ICON: spec.icon, DATA_HOOK: spec.dataHook,
        DATA_SELECTOR: spec.dataSelector, X_KEY: spec.xKey, Y_KEY: spec.yKey,
        VALUE_EXPRESSION: spec.valueExpression, COLUMNS: spec.columns,
        DELTA_DIR: spec.deltaDir, DELTA_TEXT: spec.deltaText,
        SERIES: spec.series, PIVOT_EXPRESSION: spec.pivotExpression,
        SDK_IMPORT: '', SDK_SERVICE: '', SDK_CALL: '', SDK_RESULT_TYPE: '',
      })
      writeAtomic(widgetPath, widgetContent)
      state.widgets[target] = { hash: hashFile(widgetContent), tier, metric: metricRef.name }
    }
  }

  // Regenerate Dashboard.tsx + index.ts from updated widget list
  generateDashboardFiles(projectPath, Object.keys(state.widgets), state.app.name)

  // tsc validate
  try {
    execSync('npx tsc --noEmit', { cwd: projectPath, stdio: 'pipe' })
    emit('TSC_PASS')
  } catch (e) {
    const err = e.stdout?.toString() || ''
    emit('TSC_FAIL', { errors: err.slice(0, 500) })
    fail(`TypeScript errors after edit:\n${err}`)
  }

  writeAtomic(statePath, JSON.stringify(state, null, 2))
  emit('INCREMENTAL_READY', { op, widget: target ?? toPascalCase(metric?.name ?? '') })
}
```

- [ ] **Step 9.4: Wire incremental edit into main entry point**

In the main IIFE, after `if (plan.metrics)`, add:

```javascript
  // edit-intent.json path
  if (plan.op) {
    const stateFile = join(resolve(plan.projectDir ?? process.cwd()), '.dashboard', 'state.json')
    if (!existsSync(stateFile)) fail('No .dashboard/state.json found. Run a fresh build first.')
    const state = JSON.parse(readFileSync(stateFile, 'utf8'))
    await runIncrementalEdit(plan, resolve(plan.projectDir ?? process.cwd()), state.timeRange ?? '30d')
    return
  }
```

- [ ] **Step 9.5: Run tests — expect PASS**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
```

Expected: all tests PASS.

- [ ] **Step 9.6: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs \
        skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
git commit -m "feat(dashboards): add classifyEditIntent, runIncrementalEdit, state.json hashes"
```

---

## Task 10: Skill Reference Documentation Update

**Files:**
- Rewrite: `skills/uipath-coded-apps/references/dashboards/plugins/build/impl.md`
- Update: `skills/uipath-coded-apps/references/dashboards/primitives/build-plan.md`
- Update: `skills/uipath-coded-apps/references/dashboards/primitives/state-file.md`
- Update: `skills/uipath-coded-apps/references/dashboards/primitives/incremental-editor.md`
- Create: `skills/uipath-coded-apps/references/dashboards/primitives/tier-resolution.md`
- Update: `skills/uipath-coded-apps/references/dashboards/CAPABILITY.md`

- [ ] **Step 10.1: Rewrite `impl.md` — the agent's build instruction file**

Write `skills/uipath-coded-apps/references/dashboards/plugins/build/impl.md`:

```markdown
# Dashboard Build Plugin

Implements `build` action from `CAPABILITY.md`. Reads an `intent.json`, runs `build-dashboard.mjs`, streams progress to terminal.

## Critical Rules

1. Read `primitives/tier-resolution.md` before classifying any metric.
2. Write `intent.json` with compact fields only — never full TypeScript in the intent file (except T3 `fnBody`).
3. Fire pre-warm (`npm ci`) BEFORE showing the plan — hidden from user.
4. Show plan in plain English — no API names, no tier labels.
5. HALT after plan — do not build until user explicitly confirms.
6. Parse build script stdout line by line — each `WIDGET_READY:` event → print one progress tick.
7. On `T3_RETRY`: update `fnBody` in `intent.json`, re-run build script (exit code 2 = retry needed).
8. On `BUILD_RESULT`: extract `previewUrl`, open it in browser.
9. Never commit generated dashboard files.

## 5-Phase Build Flow

### Phase 0 — Incremental check (1 Bash)

```bash
node -e "require('fs').existsSync('.dashboard/state.json') && process.exit(0) || process.exit(1)" && echo INCREMENTAL || echo FRESH
```

- `INCREMENTAL` → follow `primitives/incremental-editor.md`
- `FRESH` → continue to Phase 1

### Phase 1 — Boot (1 parallel Read block, 3 files)

ALL THREE in ONE message block:
1. `primitives/auth-context.md`
2. `primitives/tier-resolution.md`
3. `references/dashboards/aesthetic/layout-patterns.md`

### Phase 2 — Preflight (1 Bash)

```bash
uip login status --output json
```

Extract: `orgName`, `tenantName`, `cloudUrl`, `tenantId` (UUID from `~/.uipath/.auth`).
Derive `apiUrl`: insert `api.` subdomain into `cloudUrl` (e.g. `alpha.uipath.com` → `alpha.api.uipath.com`).

Fire pre-warm silently (do not tell user):

```bash
cd <PROJECT_DIR> && npm ci --prefer-offline &
```

Or write `.prewarm.lock` and confirm pre-warm started. Build script polls for completion automatically.

### Phase 3 — Plan (0 tool calls, in-context)

For each user metric:
1. Check hard-refuse list in `primitives/tier-resolution.md` — refuse metric only (not whole dashboard)
2. Classify tier using `primitives/tier-resolution.md` rules
3. Determine widget name and time range constant

Write `intent.json` (see schema in `primitives/build-plan.md`).

Render plan:

```
Here's your **[Name]** — N widgets. Confirm to build, or tell me what to change.

• **[Widget Name] ([timeRange])** — one-line plain-English description
• ...

What you can do: "make it 7 days", "add X", "remove Y", "change Z"
```

No API names. No tier labels. No technical jargon.

### Phase 4 — Approval gate

HALT. Do not run build script until user says "go ahead", "yes", "build it", or makes an edit.

If user edits: update intent.json, re-render plan, HALT again.

### Phase 5 — Build (1 Bash, stream events)

```bash
node "${SKILL_BASE_DIR}/assets/scripts/build-dashboard.mjs" "${INTENT_JSON_PATH}"
```

Parse stdout line by line:
- `WIDGET_READY:{"name":"X","index":N,"total":M}` → print `✓ X ready (N/M)`
- `T3_RETRY:{"widget":"X","errors":[...],"intentPath":"..."}` → exit code 2 → update fnBody in intent.json → re-run
- `TSC_PASS` → print `✓ TypeScript clean`
- `SERVER_READY:{"port":N,"url":"..."}` → save URL
- `BUILD_RESULT:{...}` → extract previewUrl → open in browser
- `PREWARM_FAILED:{...}` → surface error to user
- `PARTIAL_BUILD_DETECTED` → inform user, continue

On success: "Your dashboard is live at [url]. Tell me what to change."
```

- [ ] **Step 10.2: Update `build-plan.md`**

Write `skills/uipath-coded-apps/references/dashboards/primitives/build-plan.md`:

```markdown
# Build Plan — intent.json Schema

## intent.json

Agent writes this file. Build script reads it.

```json
{
  "dashboardName": "Operations Health",
  "timeRange": "30d",
  "projectDir": "/absolute/path/to/project",
  "routingName": "operations-health-x7k2",
  "orgName": "appsdev",
  "tenantName": "appsdevDefault",
  "cloudUrl": "https://alpha.uipath.com",
  "apiUrl": "https://alpha.api.uipath.com",
  "tenantId": "<UUID>",
  "clientId": "<OAuth app client ID>",
  "metrics": [
    { "name": "agent-errors", "tier": "T1" },
    {
      "name": "queue-failure-threshold",
      "tier": "T2",
      "params": { "threshold": 20, "direction": "gt" }
    },
    {
      "name": "faulted-items",
      "tier": "T3",
      "title": "Faulted Items by Queue",
      "displayAs": "ranked-table",
      "columns": ["name", "pending"],
      "fnBody": "const r = await sdk.queues.getAll({ state: 'Faulted' })\nreturn r.items?.map(q => ({ name: q.name, pending: q.pendingCount })) ?? []"
    }
  ]
}
```

## Valid values

| Field | Values |
|-------|--------|
| `timeRange` | `"1d"`, `"7d"`, `"30d"`, `"90d"` |
| `metrics[].tier` | `"T1"`, `"T2"`, `"T3"` |
| T2 `params.direction` | `"gt"`, `"lt"`, `"eq"`, `"gte"`, `"lte"`, `"neq"` |

## Routing name

Derive at plan time: `<kebab-dashboard-name>-<4-char-random>`. Example: `agent-health-x7k2`.
Store in intent.json. Never change after first build.

## Approval gate rules

Show plan in plain English. HALT. Wait for one of:
- Explicit confirmation: "go ahead", "yes", "build it", "looks good", "confirm"  
- Edit request: update intent.json, re-render plan, HALT again
- Rejection: discard intent.json, start over
```

- [ ] **Step 10.3: Update `state-file.md`**

Write `skills/uipath-coded-apps/references/dashboards/primitives/state-file.md`:

```markdown
# State File — .dashboard/state.json

Per-project metadata. Read at every build start. Written by build script on success.

## Schema

```json
{
  "schemaVersion": 2,
  "app": {
    "name": "Operations Health Dashboard",
    "routingName": "operations-health-x7k2",
    "semver": "1.0.0"
  },
  "env": "alpha",
  "org": "appsdev",
  "tenant": "appsdevDefault",
  "cloudUrl": "https://alpha.uipath.com",
  "widgets": {
    "ErrorRateTrend": { "hash": "a3f7b2c1", "tier": "T1", "metric": "agent-errors" },
    "InvocationVolume": { "hash": "c9e1d4f2", "tier": "T1", "metric": "invocation-volume" },
    "HighFailureQueues": { "hash": "f2a8c6d3", "tier": "T2", "metric": "queue-failure-threshold" }
  },
  "deployment": {
    "systemName": null,
    "folderKey": null,
    "appUrl": null,
    "lastDeployedAt": null
  }
}
```

## Key rules

1. `schemaVersion: 2 — build script writes this. If absent, treat as legacy (widget list array).
2. `widgets` is now a map of `{ hash, tier, metric }` — not a string array.
3. `routingName` never changes once set. Not even on upgrades.
4. `hash` used for hand-edit detection — compare to current file content before CHANGE/REMOVE.
5. `deployment.systemName` set by deploy plugin on first deploy; used for upgrade deploys.
```

- [ ] **Step 10.4: Update `incremental-editor.md`**

Write `skills/uipath-coded-apps/references/dashboards/primitives/incremental-editor.md`:

```markdown
# Incremental Editor

Handles ADD / REMOVE / CHANGE / REBUILD requests on existing dashboards.

## Trigger

Detects `.dashboard/state.json` at session start or when user requests a change after `BUILD_RESULT`.

## edit-intent.json schema

Write to `<PROJECT_DIR>/edit-intent.json`:

```json
// ADD
{ "op": "ADD", "projectDir": "/abs/path", "metric": { "name": "job-failures", "tier": "T1" } }

// REMOVE
{ "op": "REMOVE", "projectDir": "/abs/path", "target": "InvocationVolume" }

// CHANGE (timeRange only)
{ "op": "CHANGE", "projectDir": "/abs/path", "target": "ErrorRateTrend", "delta": { "timeRange": "7d" } }

// REBUILD (full regeneration)
{ "op": "REBUILD", "projectDir": "/abs/path" }
```

## Run command

```bash
node "${SKILL_BASE_DIR}/assets/scripts/build-dashboard.mjs" "${EDIT_INTENT_PATH}"
```

## Events to watch

- `HAND_EDIT_DETECTED:{"widget":"X"}` — file was hand-edited. Warn user, ask to confirm before overwriting.
- `TSC_PASS` — edit validated clean
- `TSC_FAIL:{"errors":"..."}` — TypeScript error after edit; surface to user
- `INCREMENTAL_READY:{"op":"ADD","widget":"X"}` — done; hot-reload fires automatically

## Rules

1. Only regenerate affected widget files — never the full scaffold.
2. Routing name never changes on edit.
3. After REMOVE or CHANGE: always regenerate `Dashboard.tsx` and `widgets/index.ts`.
4. REBUILD asks for explicit user confirmation before overwriting hand-edited files.
5. Do not touch `.env.local` unless user explicitly requests a config change.
```

- [ ] **Step 10.5: Create `tier-resolution.md`**

Write `skills/uipath-coded-apps/references/dashboards/primitives/tier-resolution.md`:

```markdown
# Tier Resolution — Classifying Metrics

Every metric in `intent.json` has a `tier` field you must set during Phase 3. The build script validates your classification and routes accordingly.

## Tier Decision Tree

```
User asks for metric
  → Check hard-refuse list below
    → If match: refuse metric (not whole dashboard), offer alternative
  → Search T1 catalog: does the request match a known metric name or alias?
    → YES: tier = "T1", use the metric name from the registry
  → Search T2 catalog: does the request map to a known SDK service + custom filter?
    → YES: tier = "T2", provide compact params object
  → Else: tier = "T3", write fnBody (async function body)
```

## Tier 1 — Known catalog metrics

These exact names are in `capability-registry.json`. Use them verbatim:

| Metric name | What it shows | Time range |
|-------------|--------------|------------|
| `agent-errors` | Daily error counts as trend line | any |
| `invocation-volume` | Agent runs per day as area chart | any |
| `top-failing-agents` | Agents ranked by error count | any |
| `active-agents-kpi` | Count of agents with at least one run | any |
| `agent-latency` | P50/P95 latency over time | any |
| `job-failures` | Processes ranked by failure count | any |
| `job-completion-trend` | Completed jobs per day | any |
| `governance-policy-summary` | Total governance violations KPI | any |

## Tier 2 — Parametric metrics

These map to known SDK services with custom filter values:

| Metric name | What it does | Required params |
|-------------|-------------|----------------|
| `queue-failure-threshold` | Queues filtered by failureCount | `{ threshold: number, direction: "gt" }` |
| `jobs-duration-threshold` | Jobs filtered by duration | `{ threshold: number, direction: "gt" }` |

**T2 params format:**

```json
{
  "name": "queue-failure-threshold",
  "tier": "T2",
  "params": { "threshold": 20, "direction": "gt" }
}
```

## Tier 3 — Custom function body

Use when the metric doesn't match T1 or T2. Write a typed async function body:

```typescript
// sdk is UiPathClient, getToken returns a Bearer token string
const r = await sdk.queues.getAll({ state: 'Faulted' })
return r.items?.map(q => ({ name: q.name, count: q.pendingCount })) ?? []
```

Rules for T3 fnBody:
- Must return `Promise<Array<Record<string, unknown>>>`
- Use `sdk.*` for SDK calls — imports are handled by the shell template
- Use `await` for all async operations
- No `import` statements — the shell provides all imports
- No JSX — just data fetching and transformation

T3 fields required in intent.json:
```json
{
  "name": "my-metric",
  "tier": "T3",
  "title": "Human-readable title",
  "displayAs": "ranked-table",
  "columns": ["name", "count"],
  "fnBody": "..."
}
```

## Hard Refuse List

Refuse ONLY the specific metric. Offer the dashboard with remaining metrics.

| User asks for | Reason | Suggest instead |
|--------------|--------|----------------|
| Agent cost in dollars | Platform tracks AGU, not currency | `invocation-volume` for AGU consumption |
| CPU/memory per agent | Not exposed by any API | `agent-latency` for fleet-level latency |
| Who triggered a job | Job records carry no end-user identity | `job-completion-trend` by process |
| Cross-tenant data | Single-tenant scope only | Multi-widget view within one tenant |
| SLA breach % | No SLA metadata in platform | Success rate from `job-completion-trend` |
| Error message text | No aggregation endpoint | `agent-errors` for counts |
```

- [ ] **Step 10.6: Update CAPABILITY.md**

Replace `skills/uipath-coded-apps/references/dashboards/CAPABILITY.md`:

```markdown
# Dashboard Capability — Entry Point

Build or edit a Coded Web App dashboard powered by Insights RTM and the UiPath TypeScript SDK.

## When to use this capability

- User asks for a dashboard, chart, report, or metric visualization
- User asks to "add/remove/change" widgets on an existing dashboard

## Critical Rules

1. Read `primitives/tier-resolution.md` BEFORE classifying any metric — do not guess tiers from memory.
2. Fire pre-warm before showing the plan — hidden from user.
3. Always use plain English in the plan — no API names, no tier labels.
4. HALT after plan — do not build until user confirms.
5. Parse EVERY build script output line — miss a T3_RETRY and the build hangs at exit code 2.
6. Never auto-deploy — deploy requires explicit user confirmation.

## Plugin Router

| User intent | Plugin |
|-------------|--------|
| Build new dashboard | `plugins/build/impl.md` |
| Edit existing dashboard | `primitives/incremental-editor.md` |
| Deploy dashboard | `plugins/deploy/impl.md` |

## Reference Navigation

| Doc | Purpose |
|-----|---------|
| `primitives/tier-resolution.md` | T1/T2/T3 classification rules + hard-refuse list |
| `primitives/build-plan.md` | intent.json schema + routing name rules |
| `primitives/auth-context.md` | How to extract org/tenant/tenantId from uip login |
| `primitives/state-file.md` | .dashboard/state.json schema |
| `primitives/incremental-editor.md` | edit-intent.json schema + ADD/REMOVE/CHANGE flow |
| `primitives/insights-client.md` | Temporary Insights HTTP client (until SDK ships) |
| `aesthetic/layout-patterns.md` | 10 immutable layout rules |
| `aesthetic/charting.md` | Chart type selection guide |
| `sdk-capabilities.md` | Full capability registry with aliases |
```

- [ ] **Step 10.7: Verify all reference files exist**

```bash
ls skills/uipath-coded-apps/references/dashboards/primitives/
ls skills/uipath-coded-apps/references/dashboards/plugins/build/
```

Expected: `tier-resolution.md`, `build-plan.md`, `state-file.md`, `incremental-editor.md`, `auth-context.md` all present.

- [ ] **Step 10.8: Commit all documentation**

```bash
git add skills/uipath-coded-apps/references/dashboards/
git commit -m "docs(dashboards): rewrite all reference docs for intent-based build — intent.json, tiered resolution, state schema v2, edit-intent"
```

---

## Task 11: Run Full Test Suite + Smoke Test

**Verifies everything integrates end to end.**

- [ ] **Step 11.1: Run all unit tests**

```bash
node --test skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
```

Expected: all tests PASS. If any fail, fix before proceeding.

- [ ] **Step 11.2: Validate capability registry JSON**

```bash
node -e "
const r = JSON.parse(require('fs').readFileSync('skills/uipath-coded-apps/assets/scripts/capability-registry.json'))
const t1 = Object.keys(r.t1).length
const t2 = Object.keys(r.t2).length
console.log('T1 entries:', t1)
console.log('T2 entries:', t2)
console.log('Hard refuse:', r.hardRefuse.length)
if (t1 === 0) throw new Error('No T1 entries')
if (t2 === 0) throw new Error('No T2 entries')
console.log('Registry OK')
"
```

Expected:
```
T1 entries: 8
T2 entries: 2
Hard refuse: 6
Registry OK
```

- [ ] **Step 11.3: Validate build-dashboard.mjs syntax**

```bash
node --check skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs
```

Expected: no output (clean).

- [ ] **Step 11.4: Validate the T3 shell template has no leftover placeholders by verifying injection**

```bash
node -e "
import { buildT3WidgetFile } from './skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs'
const content = buildT3WidgetFile({
  name: 'test-metric', tier: 'T3', title: 'Test', description: 'Desc',
  displayAs: 'ranked-table', columns: [],
  fnBody: 'return []'
})
const unresolved = content.match(/<<[A-Z_]+>>/g)
if (unresolved) { console.error('Unresolved placeholders:', unresolved); process.exit(1) }
console.log('T3 shell template OK')
" --input-type module
```

Expected: `T3 shell template OK`

- [ ] **Step 11.5: Commit if any fixes needed**

```bash
git add -A
git commit -m "test(dashboards): fix any issues found during smoke test"
```

---

## Self-Review Checklist

**Spec coverage check:**

| Spec section | Covered by task |
|-------------|----------------|
| §4 User Journey — NLP → plan → build | Tasks 8, 10 (impl.md) |
| §4.2 Plan format rules | Task 10 (build-plan.md) |
| §4.3 Follow-up enhancements | Task 9 (runIncrementalEdit) |
| §4.4 New session resume | Task 9 (state.json detection) |
| §5 intent.json schema | Tasks 2, 10 |
| §6.1 Tier 1 resolution | Tasks 1, 3 |
| §6.2 Tier 2 resolution | Tasks 1, 4 |
| §6.3 Tier 3 resolution | Tasks 5, 8 |
| §6.3 T3 retry protocol (exit code 2) | Task 8 |
| §6.4 Hard refuse table | Tasks 1, 10 |
| §7.1 Pre-warm polling guarantee | Task 7 |
| §7.2 Event streaming protocol | Task 6 |
| §7.3 Parallel T1/T2 generation | Task 8 (Promise.all) |
| §8.1 edit-intent.json schema | Tasks 9, 10 |
| §8.2 Hand-edit protection | Task 9 |
| §8.3 Routing name permanence | Tasks 8, 10 |
| §9 All error events | Tasks 7, 8, 9 |
| §10 State file schema | Tasks 8, 9, 10 |
| §11 What changes from legacy plan.json | Tasks 8 (backward compat), 10 |
| §12 Files affected list | All tasks |
