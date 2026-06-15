# Dashboard Phase 1 — Metric Modules + Two-Stage Compile — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move each metric's data-fetch code out of the `fnBody` string in `intent.json` into a real `src/metrics/<name>.ts` module, type-checked in isolation *before* the React app is generated, so errors are metric-local and `intent.json` becomes pure metadata.

**Architecture:** The agent authors `intent.json` (metadata only) plus one `metrics/<name>.ts` per metric exporting `fetchData: MetricFn`. The build copies those modules into the scaffolded project, runs an isolated `tsc -p tsconfig.metrics.json` over just the metric files + pure libs (Stage A) — a failure maps directly to a `.ts` file and emits `METRICS_RETRY`. Only once Stage A is green does the build generate widgets that **import** the metric module (Stage B) and run the full-app `tsc` as a backstop.

**Tech Stack:** Node ESM build script (`build-dashboard.mjs`), `node:test` unit tests, TypeScript 5.x (`tsc --noEmit`), Vite/React scaffold, `@uipath/uipath-typescript` SDK.

**Spec:** `docs/superpowers/specs/2026-06-15-dashboard-compiler-architecture-design.md` (§3 is Phase 1). Phases 2 (versioning/upgrade) and 3 (zip fixture) are separate plans.

**Branch:** `feat/dashboard-compiler-arch` (already created from `feat/insights-sdk-production`).

---

## File Structure

**New scaffold files** (`skills/uipath-coded-apps/assets/templates/dashboard/scaffold/`):
- `src/lib/metric-contract.ts` — the `MetricFn` type every metric module exports.
- `src/lib/time.ts` — relative time-window `Date` constants (moved out of the build script's inline `TIME_CONSTANTS` splice).
- `tsconfig.metrics.json` — isolated compile config: metric files + pure libs only, no React.

**Modified scaffold template:**
- `assets/templates/dashboard/widgets/t3-shell.tsx.template` — replace the embedded `customDataFn` block with a metric-module import.
  *(The 6 chart templates need NO edit — they already use `<HOOK_IMPORT>`/`<DATA_HOOK>` placeholders; only the build script's substitution changes.)*

**Modified build script** (`assets/scripts/build-dashboard.mjs`):
- `applyTemplate` — stop injecting `TIME_CONSTANTS`.
- `buildWidgetFile` — chart path and shell path emit an `import { fetchData }` instead of splicing code.
- `buildViewSpec` / `generateViewFile` — detail views import `fetchData`/`fetchDetail`.
- `validateIntent` — drop the `fnBody` requirement; accept metadata-only metrics; require `schemaVersion`.
- `runDashboardBuild` — copy metric modules in, run Stage A, reorder, store module ref (not `fnBody`) in state.
- New helper `metricModuleSpecifier(metric)` and `runMetricsTypecheck(projectPath)`.
- `classifyEditIntent` / `runIncrementalEdit` — ADD/CHANGE/REMOVE act on metric files.

**Modified references** (`assets/.../references/dashboards/`):
- `primitives/tier-resolution.md`, `plugins/build/impl.md`, `primitives/incremental-editor.md`, `primitives/state-file.md` — "write fnBody" → "write a metric module".

**Modified tests:**
- `assets/scripts/tests/resolution.test.mjs` — update `buildWidgetFile` expectations; add module-specifier + import-wiring tests.

**New test task:**
- `tests/tasks/uipath-coded-apps/dashboard/smoke/dashboard_metric_modules.yaml`.

---

## Task 1: Scaffold lib — `metric-contract.ts` and `time.ts`; stop splicing time constants

**Files:**
- Create: `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/lib/metric-contract.ts`
- Create: `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/lib/time.ts`
- Modify: `skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs` (`applyTemplate`, remove `TIME_CONSTANTS` injection at lines 366-375; the `TIME_CONSTANTS` const at 142-147 stays only if still referenced — after this task it is not, so remove it too)

- [ ] **Step 1: Create `metric-contract.ts`**

```ts
// The data-fetch signature every metric module exports.
//
// sdk is `any` because the SDK service constructors take `sdk as never`; the
// array return preserves the settled Promise<any[]> harness — SDK response
// interfaces lack implicit index signatures and are not assignable to
// Record<string, unknown>[], so any[] accepts SDK-typed arrays directly while
// still requiring an array return.
export type MetricFn = (sdk: any, getToken: () => Promise<string>) => Promise<any[]>
```

- [ ] **Step 2: Create `time.ts`**

```ts
// Relative time windows for dashboard queries, computed once at module load.
// Metric modules import the windows they need. Moved out of the build script's
// inline TIME_CONSTANTS splice so metric modules type-check in isolation.
export const NOW = new Date()
export const ONE_DAY_AGO = new Date(Date.now() - 86_400_000)
export const SEVEN_DAYS_AGO = new Date(Date.now() - 604_800_000)
export const THIRTY_DAYS_AGO = new Date(Date.now() - 2_592_000_000)
export const NINETY_DAYS_AGO = new Date(Date.now() - 7_776_000_000)
```

- [ ] **Step 3: Remove the time-constant injection from `applyTemplate`**

In `build-dashboard.mjs`, delete the injection block currently at lines 366-375:
```js
  // Inject time constants after the last import line
  const lines = content.split('\n')
  let lastImportIdx = -1
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].startsWith('import ')) lastImportIdx = i
  }
  if (lastImportIdx >= 0) {
    lines.splice(lastImportIdx + 1, 0, '', TIME_CONSTANTS.trimEnd())
    content = lines.join('\n')
  }
```
Leave the placeholder-substitution loop and the unresolved-placeholder check intact. Then delete the now-unused `TIME_CONSTANTS` constant (lines 142-147) and the `TIME_CONSTANT_BY_RANGE` map only if nothing else references it (grep first — `autoSubtitle`/time-range label logic may still use the `'30d' → 'THIRTY_DAYS_AGO'` map; if so, keep the map and delete only the multi-line `TIME_CONSTANTS` string).

- [ ] **Step 4: Verify the build script still parses**

Run: `node --check skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs`
Expected: no output, exit 0.

- [ ] **Step 5: Commit**

```bash
git add skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/lib/metric-contract.ts \
        skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/lib/time.ts \
        skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs
git commit -m "feat(dashboards): add metric-contract + time lib, stop splicing time constants"
```

---

## Task 2: Scaffold — isolated `tsconfig.metrics.json`

**Files:**
- Create: `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/tsconfig.metrics.json`

- [ ] **Step 1: Create the config**

```json
{
  "extends": "./tsconfig.json",
  "include": [
    "src/metrics/**/*.ts",
    "src/lib/metric-contract.ts",
    "src/lib/paginate.ts",
    "src/lib/time.ts"
  ]
}
```

Notes: `extends` inherits `compilerOptions` (strict, `paths: {"@/*": ["./src/*"]}`, `noEmit`, `moduleResolution: bundler`) but NOT `include`/`references`, so this config checks only the listed roots and what they import. The three libs are pure (no React), so the metrics compile pulls no DOM/React graph and stays fast.

- [ ] **Step 2: Sanity — the config is valid JSON**

Run: `node -e "JSON.parse(require('fs').readFileSync('skills/uipath-coded-apps/assets/templates/dashboard/scaffold/tsconfig.metrics.json','utf8'))"`
Expected: no output, exit 0.

- [ ] **Step 3: Commit**

```bash
git add skills/uipath-coded-apps/assets/templates/dashboard/scaffold/tsconfig.metrics.json
git commit -m "feat(dashboards): isolated tsconfig.metrics for two-stage compile"
```

---

## Task 3: Build — module-specifier helper + intent v2 validation

**Files:**
- Modify: `skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs` (add `metricModuleSpecifier`; change `validateIntent` at 595-647)
- Test: `skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs`

- [ ] **Step 1: Write failing tests**

Append to `resolution.test.mjs` (and add `metricModuleSpecifier` to the import on line 6):

```js
test('metricModuleSpecifier derives @/metrics/<name> by default', () => {
  assert.equal(metricModuleSpecifier({ name: 'agent-health' }), '@/metrics/agent-health')
})

test('metricModuleSpecifier honors explicit module field and strips .ts', () => {
  assert.equal(metricModuleSpecifier({ name: 'x', module: 'metrics/custom-thing.ts' }), '@/metrics/custom-thing')
})

test('validateIntent accepts a metadata-only metric (no fnBody)', () => {
  const errors = validateIntent({
    schemaVersion: 2, dashboardName: 'D', timeRange: '30d',
    metrics: [{ name: 'agent-health', tier: 'T1', title: 'Agent Health', displayAs: 'ranked-table' }],
  })
  assert.deepEqual(errors, [])
})

test('validateIntent rejects intent missing schemaVersion 2', () => {
  const errors = validateIntent({
    dashboardName: 'D', timeRange: '30d',
    metrics: [{ name: 'm', tier: 'T3', title: 'M', displayAs: 'kpi-card' }],
  })
  assert.ok(errors.some(e => /schemaVersion/.test(e)))
})
```

- [ ] **Step 2: Run to verify failure**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/`
Expected: FAIL — `metricModuleSpecifier is not a function` / `validateIntent` still requires `fnBody`.

- [ ] **Step 3: Add the helper**

In `build-dashboard.mjs`, near `resolveMetric` (≈ line 649), add and export:
```js
/**
 * The module specifier a generated widget imports its data function from.
 * Default convention: metrics/<metric-name>.ts → '@/metrics/<metric-name>'.
 * An explicit `module` field (e.g. "metrics/custom.ts") overrides; the .ts is stripped.
 * @param {{ name: string, module?: string }} metric
 * @returns {string}
 */
export function metricModuleSpecifier(metric) {
  const rel = metric.module ?? `metrics/${metric.name}.ts`
  return '@/' + rel.replace(/\.ts$/, '')
}
```

- [ ] **Step 4: Update `validateIntent`**

In `validateIntent` (595-647): (a) at the top, push an error if `intent.schemaVersion !== 2`; (b) remove the per-metric `fnBody` requirement (the lines pushing `... missing fnBody ...` at ≈604 and ≈614). Keep all other checks (title, displayAs/template, rate-chart rateNum/rateDen). Replace the fnBody checks with a name check:
```js
      if (!m.name) errors.push(`metric ${JSON.stringify(m.title ?? m)} missing name (needed to resolve its metrics/<name>.ts module)`)
```

- [ ] **Step 5: Run tests to verify pass**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/`
Expected: PASS (new tests green; pre-existing tests still green except any that assert the old fnBody requirement — fix those in Task 4/5).

- [ ] **Step 6: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
git commit -m "feat(dashboards): intent schemaVersion 2 + metric module specifier; drop fnBody requirement"
```

---

## Task 4: Build — chart widgets import the metric module (no splice)

**Files:**
- Modify: `build-dashboard.mjs` `buildWidgetFile` chart path (754-796)
- Test: `resolution.test.mjs`

- [ ] **Step 1: Write failing test**

```js
test('buildWidgetFile (chart) imports fetchData and does not splice customDataFn', () => {
  const out = buildWidgetFile(
    { name: 'memory-calls-trend', tier: 'T1', title: 'Memory Calls', displayAs: 'area-chart', xKey: 'timeSlice', yKey: 'memoryCallsCount' },
    null, '30d'
  )
  assert.match(out, /import \{ fetchData \} from '@\/metrics\/memory-calls-trend'/)
  assert.match(out, /useWidgetData\(fetchData, \[\]\)/)
  assert.doesNotMatch(out, /const customDataFn = async/)
})
```

- [ ] **Step 2: Run to verify failure**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/`
Expected: FAIL — output still contains `const customDataFn = async` / no `import { fetchData }`.

- [ ] **Step 3: Rewrite the chart path**

Replace the chart branch (754-796) with:
```js
  // ── Chart path ─────────────────────────────────────────────────────────────
  if (CHART_TYPES.has(displayAs)) {
    const moduleSpecifier = metricModuleSpecifier(metric)
    const spec = {
      componentName,
      template:          displayAs,
      detailRoute:       metric.detailRoute ?? `/${componentName.toLowerCase()}`,
      icon:              iconName,
      title:             metric.title,
      subtitle:          autoSubtitle(metric, defaults, timeRange),
      dataHook:          'useWidgetData(fetchData, [])',
      hookImport:        [
                           "import { useWidgetData } from '@/hooks/useWidgetData'",
                           `import { fetchData } from '${moduleSpecifier}'`,
                         ].join('\n'),
      sdkImportLine:     '',
      responseTypeImport: '',
      dataSelector:      'data ?? []',
      xKey:              metric.xKey  ?? defaults.xKey  ?? 'date',
      yKey:              metric.yKey  ?? defaults.yKey  ?? 'value',
      headlineMode:      metric.headlineMode  ?? defaults.headlineMode  ?? 'sum',
      deltaPolarity:     metric.deltaPolarity ?? defaults.deltaPolarity ?? 'neutral',
      rateNum:           metric.rateNum ?? defaults.rateNum ?? 'num',
      rateDen:           metric.rateDen ?? defaults.rateDen ?? 'den',
      series:            metric.series ?? defaults.series ?? '[{key:"value",color:"hsl(var(--chart-1))"}]',
      pivotExpression:   metric.pivotExpression ?? defaults.pivotExpression ?? 'rawData',
    }
    return applyTemplate(spec.template, specToSubs(spec))
  }
```
(Removes the `indented`/`customFnBlock`/`content.replace(...)` splice. The `metric.fnBody` guard at line 743 is removed in Task 5 Step 3.)

- [ ] **Step 4: Run tests to verify pass**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/`
Expected: PASS for the new test.

- [ ] **Step 5: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
git commit -m "feat(dashboards): chart widgets import metric module instead of spliced fnBody"
```

---

## Task 5: Template + build — `t3-shell` (KPI/table) imports the metric module

**Files:**
- Modify: `assets/templates/dashboard/widgets/t3-shell.tsx.template`
- Modify: `build-dashboard.mjs` `buildWidgetFile` shell path (798-end of function, ≈808-830) and remove the top-of-function `fnBody` guard (743)
- Test: `resolution.test.mjs`

- [ ] **Step 1: Edit the template**

Replace the `customDataFn` block (lines 14-21) with a metric-import placeholder, and change the call site. Specifically:

Delete lines 14-21:
```ts
// ── Custom data function (injected at build time) ─────────────────────────────
// Promise<any[]>: SDK response interfaces lack index signatures and are not
// assignable to Record<string, unknown> — any[] accepts them while still
// requiring an array return.
const customDataFn = async (sdk: any, getToken: () => Promise<string>): Promise<any[]> => {
<<FN_BODY>>
}
// ─────────────────────────────────────────────────────────────────────────────
```
Add `<<METRIC_IMPORT>>` to the import group (after line 10, the `lucide-react` import):
```ts
import { <<ICON_NAME>> } from 'lucide-react'
<<METRIC_IMPORT>>
```
Change the fetch call (was line 37) from `customDataFn(sdk, getToken)` to:
```ts
    fetchData(sdk, getToken)
```

- [ ] **Step 2: Write failing test**

```js
test('buildWidgetFile (kpi/table) imports fetchData and has no embedded customDataFn', () => {
  const out = buildWidgetFile(
    { name: 'job-failures', tier: 'T1', title: 'Faulted Jobs', displayAs: 'data-table',
      columns: '[{key:"processName",label:"Process"}]' },
    null, '30d'
  )
  assert.match(out, /import \{ fetchData \} from '@\/metrics\/job-failures'/)
  assert.match(out, /fetchData\(sdk, getToken\)/)
  assert.doesNotMatch(out, /const customDataFn = async/)
})
```

- [ ] **Step 3: Run to verify failure**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/`
Expected: FAIL — shell path still injects `<<FN_BODY>>` / unresolved `<<METRIC_IMPORT>>` placeholder error.

- [ ] **Step 4: Rewrite the shell path**

In `buildWidgetFile`: remove the `if (!metric.fnBody) throw ...` guard (≈743). In the shell branch (≈798-830), delete the `indentedFnBody` computation and the `<<FN_BODY>>` substitution; add a `<<METRIC_IMPORT>>` substitution. The substitution map gains:
```js
  const subs = {
    METRIC_IMPORT: `import { fetchData } from '${metricModuleSpecifier(metric)}'`,
    ICON_NAME: iconName,
    DISPLAY_AS: displayAs,
    VALUE_FIELD: valueField,
    VALUE_LABEL: valueLabel,
    COLUMNS: columns,
    COMPONENT_NAME: componentName,
    TITLE: metric.title,
    DESCRIPTION: subtitle,
  }
  for (const [key, value] of Object.entries(subs)) {
    content = content.split(`<<${key}>>`).join(value)
  }
```
(Keep the existing unresolved-`<<...>>` check if present; otherwise the chart-path `applyTemplate` check covers charts and this loop covers the shell.)

- [ ] **Step 5: Run tests to verify pass**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/uipath-coded-apps/assets/templates/dashboard/widgets/t3-shell.tsx.template skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
git commit -m "feat(dashboards): t3-shell imports metric module instead of embedded customDataFn"
```

---

## Task 6: Build — detail views import `fetchData`/`fetchDetail`

**Files:**
- Modify: `build-dashboard.mjs` `buildViewSpec` (721-732) and `generateViewFile` (404-484)
- Test: `resolution.test.mjs`

- [ ] **Step 1: Write failing test**

```js
test('generateViewFile imports the metric module detail/data export', () => {
  const spec = buildViewSpec('MemoryCallsTrend',
    { name: 'memory-calls-trend', tier: 'T1', title: 'Memory Calls', displayAs: 'area-chart' },
    null, '30d')
  const out = generateViewFile(spec)
  assert.match(out, /import \{ (fetchData|fetchDetail) \} from '@\/metrics\/memory-calls-trend'/)
  assert.doesNotMatch(out, /const customDataFn = async/)
})
```

- [ ] **Step 2: Run to verify failure**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/`
Expected: FAIL — view still splices `detailFnBody`.

- [ ] **Step 3: Update `buildViewSpec` and `generateViewFile`**

`buildViewSpec`: replace `detailFnBody: metric.detailFnBody ?? metric.fnBody` with:
```js
    moduleSpecifier: metricModuleSpecifier(metric),
    detailExport: metric.detail === true ? 'fetchDetail' : 'fetchData',
```
`generateViewFile`: where it currently emits the spliced `customDataFn`/`detailFnBody`, emit an import and use the imported function:
```js
  const dataImport = `import { ${widget.detailExport} } from '${widget.moduleSpecifier}'`
  // ...in the generated file: use `${widget.detailExport}(sdk, getToken)` as the fetcher,
  // and place `${dataImport}` with the other imports.
```
Show the import among the view file's imports and call `${widget.detailExport}(sdk, getToken)` inside the view's `useWidgetData(...)` (mirror the chart widget wiring).

- [ ] **Step 4: Run tests to verify pass**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
git commit -m "feat(dashboards): detail views import metric module (fetchData/fetchDetail)"
```

---

## Task 7: Build pipeline — copy metric modules, Stage A typecheck, reorder, state stores module ref

**Files:**
- Modify: `build-dashboard.mjs` — add `runMetricsTypecheck`; in `runDashboardBuild` add a copy step + Stage A before the widget loop (≈1033); add `METRICS_RETRY` to `KNOWN_EVENTS` (149-154); change `widgetHashes[...]` to drop `fnBody` from `intentMetric` (1052)
- Test: covered by Task 10's integration smoke (Stage A runs `tsc`/`npm`, too heavy for the fast unit suite)

- [ ] **Step 1: Add `METRICS_RETRY` to `KNOWN_EVENTS`**

In the `KNOWN_EVENTS` set (149-154), add `'METRICS_RETRY'` and `'METRICS_PASS'`.

- [ ] **Step 2: Add the Stage-A helper**

Add near `runPrewarm`:
```js
/**
 * Stage A — isolated type-check of the agent-written metric modules, before any
 * widget is generated. Fast (no React graph) and maps errors directly to the
 * offending src/metrics/<name>.ts file.
 * @param {string} projectPath
 * @returns {{ ok: true } | { ok: false, errors: string[], files: string[] }}
 */
export function runMetricsTypecheck(projectPath) {
  try {
    execSync('npx tsc -p tsconfig.metrics.json', { cwd: projectPath, stdio: 'pipe' })
    return { ok: true }
  } catch (e) {
    const out = (e.stdout?.toString() ?? '') + (e.stderr?.toString() ?? '')
    const errors = out.split('\n').filter(l => l.includes('error TS')).slice(0, 20)
    const files = [...new Set((out.match(/src[/\\]metrics[/\\][\w-]+\.ts/g) ?? []).map(p => p.replace(/\\/g, '/')))]
    return { ok: false, errors, files }
  }
}
```

- [ ] **Step 3: Copy metric modules + run Stage A in `runDashboardBuild`**

After the scaffold is ready and deps are pre-warmed, and BEFORE the widget-generation loop (≈1033), insert:
```js
    // Stage A — copy agent-authored metric modules into the project and
    // type-check them in isolation before generating any widget.
    const metricsSrcDir = join(dirname(intentPath), 'metrics')
    const metricsDestDir = join(P, 'src', 'metrics')
    mkdirSync(metricsDestDir, { recursive: true })
    for (const metric of metrics) {
      const rel = metric.module ?? `metrics/${metric.name}.ts`
      const fromPath = join(dirname(intentPath), rel)
      if (!existsSync(fromPath)) {
        fail(`Metric module not found: ${fromPath} — write the data function as metrics/${metric.name}.ts exporting "fetchData"`)
      }
      copyFileSync(fromPath, join(metricsDestDir, basename(rel)))
    }
    const stageA = runMetricsTypecheck(P)
    if (!stageA.ok) {
      emit('METRICS_RETRY', { files: stageA.files, errors: stageA.errors, intentPath })
      log(`⚠ Metric modules have TypeScript errors. Fix the named files in ${metricsDestDir} and re-run.`)
      process.exit(2)
    }
    emit('METRICS_PASS')
```
Ensure `mkdirSync`, `copyFileSync`, `basename`, `dirname` are imported at the top of the file (add to the existing `node:fs` / `node:path` imports if missing).

- [ ] **Step 4: Drop `fnBody` from persisted state**

At the `widgetHashes[componentName] = {...}` assignment (1052), the `intentMetric: metric` now carries metadata only (no `fnBody` after Task 3) — no change needed beyond confirming `metric` has no `fnBody`. The durable code is the `src/metrics/<name>.ts` file. Add `module: metric.module ?? \`metrics/${metric.name}.ts\`` to the persisted object so REBUILD/upgrade can find it.

- [ ] **Step 5: Verify the script parses + a real fresh build reaches Stage A**

Run: `node --check skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs`
Expected: exit 0. (End-to-end build is exercised in Task 10.)

- [ ] **Step 6: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs
git commit -m "feat(dashboards): Stage A metric typecheck + copy modules + persist module ref"
```

---

## Task 8: Incremental editor — ADD/CHANGE/REMOVE act on metric files

**Files:**
- Modify: `build-dashboard.mjs` `classifyEditIntent` (1146) and `runIncrementalEdit` (the ADD/CHANGE/REMOVE handlers ≈1200-1290)
- Test: `resolution.test.mjs`

- [ ] **Step 1: Write failing test**

```js
test('classifyEditIntent ADD requires a metric module path or name', () => {
  const plan = classifyEditIntent({
    projectDir: '/p',
    ops: [{ op: 'ADD', metric: { name: 'agent-health', tier: 'T1', title: 'Agent Health', displayAs: 'ranked-table' } }],
  })
  assert.equal(plan.ops[0].op, 'ADD')
  assert.equal(plan.ops[0].metric.name, 'agent-health')
  // fnBody is no longer part of an ADD op
  assert.equal(plan.ops[0].metric.fnBody, undefined)
})
```

- [ ] **Step 2: Run to verify failure / regression**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/`
Expected: FAIL or a stale assertion in an existing CHANGE/ADD test that still expects `fnBody`. Note which existing tests reference `fnBody` for fixup in Step 4.

- [ ] **Step 3: Update the edit handlers**

In `runIncrementalEdit`:
- **ADD**: write `<projectDir>/src/metrics/<name>.ts` from the op's metric module source (the agent writes it to `<editIntentDir>/metrics/<name>.ts`; copy it in, same as Task 7), run `runMetricsTypecheck`, then generate the widget.
- **CHANGE**: if the op carries a new module source, overwrite `src/metrics/<target-name>.ts`; re-run `runMetricsTypecheck`; regenerate the widget + view. Metadata-only CHANGE (e.g. `displayAs`) skips the module rewrite.
- **REMOVE**: delete `src/metrics/<name>.ts` alongside the widget/view.
Pre-validate the whole batch (all module files present, Stage-A clean) before applying — matching the existing "validate-all-then-apply" batch contract.

- [ ] **Step 4: Fix stale `fnBody` assertions + run tests**

Update any existing test that constructed CHANGE/ADD ops with `fnBody` to use a metric module instead. Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs
git commit -m "feat(dashboards): incremental edits operate on metric modules"
```

---

## Task 9: References — rewrite "write fnBody" → "write a metric module"

**Files:**
- Modify: `references/dashboards/primitives/tier-resolution.md`
- Modify: `references/dashboards/plugins/build/impl.md`
- Modify: `references/dashboards/primitives/incremental-editor.md`
- Modify: `references/dashboards/primitives/state-file.md`

- [ ] **Step 1: `tier-resolution.md`** — Replace the "Writing fnBody" section with "Writing a metric module": the agent writes `metrics/<name>.ts` exporting `export const fetchData: MetricFn = async (sdk) => { ... }`, importing time windows from `@/lib/time` and using `fetchAll` from `@/lib/paginate`. Update every T1/T2/T3 intent example to metadata-only (drop `fnBody`) and add the matching `.ts` module beside it. Keep the read-only-methods rule, the `Promise<any[]>` rule, the three SDK calling conventions, and the T0 refuse table.

- [ ] **Step 2: `impl.md`** — Phase 4: the agent writes `intent.json` (metadata) + `metrics/*.ts`. The build emits `METRICS_PASS` (silent) then `WIDGET_READY`; on `METRICS_RETRY:{files,errors}` the agent fixes the named `src/metrics/*.ts` files and re-runs (this replaces the old `T3_RETRY` fnBody-in-intent loop). Keep the build-subagent + server-as-background-job flow.

- [ ] **Step 3: `incremental-editor.md`** — ADD/CHANGE/REMOVE operate on metric modules (per Task 8); `edit-intent.json` ops reference metric files, not `fnBody` strings.

- [ ] **Step 4: `state-file.md`** — `widgets.<C>.intentMetric` no longer has `fnBody`; add `module` ref; note the durable code lives at `src/metrics/<name>.ts`.

- [ ] **Step 5: Commit**

```bash
git add skills/uipath-coded-apps/references/
git commit -m "docs(dashboards): metric-module authoring replaces fnBody strings"
```

---

## Task 10: Smoke test + full validation

**Files:**
- Create: `tests/tasks/uipath-coded-apps/dashboard/smoke/dashboard_metric_modules.yaml`
- Run: full unit suite + a real fresh build

- [ ] **Step 1: Add the smoke task**

```yaml
name: dashboard_metric_modules
description: Fresh dashboard build authors metric modules and passes the isolated Stage-A typecheck before app generation.
tags: [uipath-coded-apps, dashboard, smoke]
initial_prompt: |
  Build a UiPath dashboard with one widget: agent memory entries over the last 30 days.
sandbox:
  node: {}
success_criteria:
  - type: skill_triggered
    skill: uipath-coded-apps
  - type: file_exists
    path: src/metrics/agent-memory-timeline.ts
  - type: command_executed
    pattern: "build-dashboard\\.mjs"
    min_count: 1
  - type: run_command
    command: "npx tsc -p tsconfig.metrics.json --noEmit"
    expected_exit_code: 0
```
(Confirm the exact criterion keys against a neighbor task under `tests/tasks/uipath-coded-apps/dashboard/`; mirror its sandbox + path conventions. Do NOT add `@uipath/cli` to `env_packages` — the runner installs it globally.)

- [ ] **Step 2: Run the full unit suite**

Run: `node --test skills/uipath-coded-apps/assets/scripts/tests/`
Expected: all tests PASS, 0 fail.

- [ ] **Step 3: Real fresh build (happy path)**

Create a temp workdir with `intent.json` (schemaVersion 2, one area-chart metric) + `metrics/agent-memory-timeline.ts` (the example module from Task 1 docs). Run:
`node skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs <tmp>/intent.json`
Expected: `METRICS_PASS`, then `WIDGET_READY`, then `TSC_PASS`, then `BUILD_RESULT:{success:true}`. Confirm `<project>/src/metrics/agent-memory-timeline.ts` exists and the generated widget contains `import { fetchData } from '@/metrics/agent-memory-timeline'`.

- [ ] **Step 4: Broken-metric path (Stage A catches it)**

Edit the temp `metrics/agent-memory-timeline.ts` to call a non-existent SDK method (e.g. `getTimelinez`). Re-run the build.
Expected: `METRICS_RETRY:{files:["src/metrics/agent-memory-timeline.ts"], errors:[...]}` and exit code 2 — BEFORE any widget is generated.

- [ ] **Step 5: Commit**

```bash
git add tests/tasks/uipath-coded-apps/dashboard/smoke/dashboard_metric_modules.yaml
git commit -m "test(dashboards): smoke task for metric-module build + Stage-A typecheck"
```

---

## Self-Review (completed by plan author)

- **Spec coverage:** §3.1 pure-metadata intent → Tasks 3,9. §3.2 input layout → Task 7. §3.3 MetricFn contract → Task 1. §3.4 `@/lib/time` → Task 1. §3.5 two-stage compile → Tasks 2,7. §3.6 state stores module ref → Task 7. §3.7 incremental editor → Task 8. Phase 2/3 intentionally excluded (separate plans).
- **Placeholder scan:** New files (Tasks 1,2) are complete. Build-script edits show the replacement code or the exact lines + new logic. The two largest edits (Task 7 pipeline, Task 8 incremental) reference exact insertion points; their new code is shown. No "TBD"/"handle edge cases".
- **Type consistency:** `MetricFn` (Task 1) = `(sdk: any, getToken: () => Promise<string>) => Promise<any[]>` — matches `useWidgetData`'s `fetcher` (sdk widens from `UiPath`) and the export name `fetchData` used in Tasks 4,5,6,7. `metricModuleSpecifier` (Task 3) is consumed unchanged in Tasks 4,5,6.
- **Open risk to verify during execution:** the unresolved-`<<...>>` placeholder check must cover the shell path after removing `<<FN_BODY>>` (Task 5 Step 4) — confirm no stray `<<FN_BODY>>` remains in the template.

---

## Execution Handoff

Phase 1 only. Phases 2 (versioning/upgrade) and 3 (zip fixture) get their own plans after Phase 1 lands and is validated.
