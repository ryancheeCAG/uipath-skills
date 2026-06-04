import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

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
