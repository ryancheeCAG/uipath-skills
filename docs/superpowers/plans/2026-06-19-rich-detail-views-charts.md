# Rich Detail Views (charts in drill-downs) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a dashboard detail view optionally render one or more **charts** (plus tables) about the drilled-into entity — e.g. click an agent in the runtime-compliance report and see that agent's violations-by-hook donut, top-rules ranked table, and full evaluation table — instead of only a flat records table.

**Architecture:** A new optional `detailView.widgets[]` spec on a metric declares the sub-widgets a detail page renders. The metric's keyed/record-grain detail fetch returns a **named-source map** (`{ rows, byHook, byStandard, … }`); each sub-widget reads `data[source]`. The build renders the sub-widgets with **new presentational chart primitives** (`Donut`/`Bars`/`TrendArea`/`MultiLine`) that take `data` as props — the existing dashboard widget templates are untouched. Backward-compatible: a metric with no `detailView` (or whose detail fetch returns a bare array) renders exactly as today (single `RecordsTable`). Applies to BOTH keyed row-click views and chart record-grain views.

**Tech Stack:** React + TypeScript + Recharts + Tailwind (scaffold in `apps-dev-tools/uipath-dashboard-starter-kit/`); the Node build engine `build-dashboard.mjs` (skill repo); `node --test` for unit tests.

**Decisions locked (2026-06-19):** (1) new presentational detail chart primitives — dashboard widget templates untouched; (2) one keyed fetch → named-source map; (3) support both keyed row-click and chart record-grain detail views.

---

## Repos & key files

- **Scaffold (source of truth):** `C:\Work\apps-dev-tools\uipath-dashboard-starter-kit\` on `feat/dashboard-starter-kit`. Edit here, then `node publish.mjs` to re-pack the `.zip` + `.version` into the skill.
- **Engine + docs (consumer):** `C:\Work\skills\skills\uipath-coded-apps\` on `feat/dashboard-compiler-arch`.
- **Engine:** `skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs` — anchors: `VALID_DISPLAY_TYPES` (:165), `writeKeyedViewIfRowLink` (:246), `generateViewFile` (:592), `generateKeyedDetailViewFile` (:665), `compileColumns` (:950), `buildViewSpec` (:1010), `buildWidgetFile` (:1031), `validateIntent` (grep — exported). Locate `validateIntent` with `grep -n "export function validateIntent" build-dashboard.mjs`.
- **Tests:** `skills/uipath-coded-apps/assets/scripts/tests/resolution.test.mjs`.
- **Detail-view doc:** `skills/uipath-coded-apps/references/dashboards/primitives/detail-views.md`.
- **Governance recipe:** `skills/uipath-coded-apps/references/sdk/governance-traces.md`.

> **Verify before editing:** this skill changes fast — re-grep each anchor's current line before editing.

---

## Data contract (the spine of the feature)

A metric's detail fetch returns EITHER:
- a **bare array** → legacy single-table behaviour (today), OR
- a **named-source map** `Record<string, unknown[]>` when `detailView` is declared, e.g.
  ```ts
  { rows: GovernanceRuleRow[], byHook: {name,value}[], byStandard: {name,value}[] }
  ```
`fetchDetailByKey(sdk, key, getToken)` (keyed) and `fetchDetail(sdk, getToken)` (record-grain) may return either shape. The generated view normalizes:
```ts
const d: Record<string, unknown[]> = (data && !Array.isArray(data))
  ? (data as Record<string, unknown[]>)
  : { rows: toRows(data) }
```
Each `detailView.widgets[i].source` indexes `d`; a missing/empty source renders that sub-widget's EmptyState. **Robustness rule:** the detail fetch must never throw (use `@/lib/governance` parsing) and the view must render EmptyState per sub-widget when its source is empty.

### Intent schema — `detailView`

```jsonc
"detailView": {
  "widgets": [
    { "displayAs": "donut-chart",  "title": "Violations by Hook",  "source": "byHook",    "xKey": "name", "yKey": "value" },
    { "displayAs": "ranked-table", "title": "Top Rules Fired",      "source": "byRule",
      "columns": [ {"key":"name","label":"Rule"}, {"key":"value","label":"Fired","align":"right","format":"number"} ] },
    { "displayAs": "data-table",   "title": "All Rule Evaluations", "source": "rows",
      "columns": [ {"key":"hook","label":"Hook"}, {"key":"rule","label":"Rule"}, {"key":"status","label":"Status"}, {"key":"action","label":"Action"} ] }
  ]
}
```
- `displayAs`: `donut-chart` | `bar-chart` | `area-chart` | `line-chart` | `multi-line-chart` | `data-table` | `ranked-table`.
- chart sub-widgets need `xKey`+`yKey` (or `series` for multi-line); table sub-widgets take `columns` (optional → auto-detect).
- `detailView` is valid on a metric that ALSO has `rowLink` (keyed) OR `detail: true` (record-grain). On any other metric it's an error.

---

## Task 1: Presentational detail-chart primitives (scaffold)

**Files:**
- Create: `apps-dev-tools/uipath-dashboard-starter-kit/scaffold/src/dashboard/charts/Donut.tsx`
- Create: `…/charts/Bars.tsx`
- Create: `…/charts/TrendArea.tsx`
- Create: `…/charts/MultiLine.tsx`
- Create: `…/charts/index.ts`

These are **presentational only** — they take `data` + keys as props, fetch nothing, navigate nowhere, and render an `EmptyState` when `data` is empty. Each wraps in a titled `Card` so it sits naturally in the detail grid.

- [ ] **Step 1: Create `Donut.tsx`**

```tsx
import React from 'react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { EmptyState } from '@/dashboard/chrome'

const CHART_COLORS = ['hsl(var(--chart-1))', 'hsl(var(--chart-2))', 'hsl(var(--chart-3))', 'hsl(var(--chart-4))', 'hsl(var(--chart-5))']

interface DonutProps {
  data: Record<string, unknown>[]
  nameKey: string
  valueKey: string
  title?: string
  height?: number
}

/** Presentational donut — data passed in, no fetch, no navigation. */
export function Donut({ data, nameKey, valueKey, title, height = 220 }: DonutProps) {
  return (
    <Card>
      {title && <CardHeader className="pb-2"><CardTitle className="text-base">{title}</CardTitle></CardHeader>}
      <CardContent className="pt-2">
        {data && data.length > 0 ? (
          <ResponsiveContainer width="100%" height={height}>
            <PieChart>
              <Pie data={data} dataKey={valueKey} nameKey={nameKey} innerRadius={50} outerRadius={80}>
                {data.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState message="No data" />
        )}
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 2: Create `Bars.tsx`** (ranked/bar) — same Card+EmptyState wrapper:

```tsx
import React from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { EmptyState } from '@/dashboard/chrome'

interface BarsProps { data: Record<string, unknown>[]; nameKey: string; valueKey: string; title?: string; height?: number }

export function Bars({ data, nameKey, valueKey, title, height = 220 }: BarsProps) {
  return (
    <Card>
      {title && <CardHeader className="pb-2"><CardTitle className="text-base">{title}</CardTitle></CardHeader>}
      <CardContent className="pt-2">
        {data && data.length > 0 ? (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={data} layout="vertical" margin={{ left: 24 }}>
              <XAxis type="number" hide />
              <YAxis type="category" dataKey={nameKey} width={140} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey={valueKey} fill="hsl(var(--chart-1))" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : <EmptyState message="No data" />}
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 3: Create `TrendArea.tsx`** (area + line share this; `area` prop toggles fill):

```tsx
import React from 'react'
import { AreaChart, Area, Line, LineChart, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { EmptyState } from '@/dashboard/chrome'

interface TrendProps { data: Record<string, unknown>[]; xKey: string; yKey: string; title?: string; area?: boolean; height?: number }

export function TrendArea({ data, xKey, yKey, title, area = true, height = 220 }: TrendProps) {
  const hasData = data && data.length > 0
  return (
    <Card>
      {title && <CardHeader className="pb-2"><CardTitle className="text-base">{title}</CardTitle></CardHeader>}
      <CardContent className="pt-2">
        {hasData ? (
          <ResponsiveContainer width="100%" height={height}>
            {area ? (
              <AreaChart data={data}>
                <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Area type="monotone" dataKey={yKey} stroke="hsl(var(--chart-1))" fill="hsl(var(--chart-1))" fillOpacity={0.2} />
              </AreaChart>
            ) : (
              <LineChart data={data}>
                <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line type="monotone" dataKey={yKey} stroke="hsl(var(--chart-1))" dot={false} />
              </LineChart>
            )}
          </ResponsiveContainer>
        ) : <EmptyState message="No data" />}
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 4: Create `MultiLine.tsx`** (`series` = `{key,color}[]`):

```tsx
import React from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { EmptyState } from '@/dashboard/chrome'

interface SeriesDef { key: string; color: string }
interface MultiLineProps { data: Record<string, unknown>[]; xKey: string; series: SeriesDef[]; title?: string; height?: number }

export function MultiLine({ data, xKey, series, title, height = 220 }: MultiLineProps) {
  return (
    <Card>
      {title && <CardHeader className="pb-2"><CardTitle className="text-base">{title}</CardTitle></CardHeader>}
      <CardContent className="pt-2">
        {data && data.length > 0 ? (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={data}>
              <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip /><Legend />
              {series.map(s => <Line key={s.key} type="monotone" dataKey={s.key} stroke={s.color} dot={false} />)}
            </LineChart>
          </ResponsiveContainer>
        ) : <EmptyState message="No data" />}
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 5: Create `charts/index.ts`**

```ts
export { Donut } from './Donut'
export { Bars } from './Bars'
export { TrendArea } from './TrendArea'
export { MultiLine } from './MultiLine'
```

- [ ] **Step 6: Verify imports resolve** — confirm `EmptyState` is exported from `@/dashboard/chrome` (it is — `chrome/index.ts`) and `Card*` from `@/components/ui/card`. No build yet; these compile in the Task 8 self-test.

---

## Task 2: Intent schema + validation (`detailView`)

**Files:**
- Modify: `build-dashboard.mjs` — `validateIntent` (grep for it) + a new exported `validateDetailView(metric)` helper.
- Test: `resolution.test.mjs`.

- [ ] **Step 1: Write failing tests** (append to `resolution.test.mjs`):

```js
import { validateIntent } from '../build-dashboard.mjs' // already imported — reuse

test('detailView: valid spec on a rowLink table passes validation', () => {
  const intent = baseIntent({ metrics: [{
    name: 'agent-compliance-report', tier: 'T1', title: 'Agent Compliance', displayAs: 'data-table',
    rowLink: { key: 'agentName' },
    detailView: { widgets: [
      { displayAs: 'donut-chart', title: 'By Hook', source: 'byHook', xKey: 'name', yKey: 'value' },
      { displayAs: 'data-table', title: 'Rules', source: 'rows' },
    ] },
  }] })
  assert.doesNotThrow(() => validateIntent(intent))
})

test('detailView: chart sub-widget missing xKey/yKey is rejected', () => {
  const intent = baseIntent({ metrics: [{
    name: 'x', tier: 'T3', title: 'X', displayAs: 'data-table', rowLink: { key: 'k' },
    detailView: { widgets: [{ displayAs: 'donut-chart', title: 'Bad', source: 'byHook' }] },
  }] })
  assert.throws(() => validateIntent(intent), /detailView.*xKey|yKey/i)
})

test('detailView: bad displayAs is rejected', () => {
  const intent = baseIntent({ metrics: [{
    name: 'x', tier: 'T3', title: 'X', displayAs: 'data-table', rowLink: { key: 'k' },
    detailView: { widgets: [{ displayAs: 'pie', title: 'Bad', source: 'rows' }] },
  }] })
  assert.throws(() => validateIntent(intent), /detailView.*displayAs/i)
})

test('detailView: requires rowLink or detail:true on the host metric', () => {
  const intent = baseIntent({ metrics: [{
    name: 'x', tier: 'T3', title: 'X', displayAs: 'kpi-card',
    detailView: { widgets: [{ displayAs: 'data-table', title: 'R', source: 'rows' }] },
  }] })
  assert.throws(() => validateIntent(intent), /detailView requires/i)
})
```

> `baseIntent(overrides)` helper: if the test file lacks one, add a small factory returning a minimal valid schemaVersion-2 intent (`{schemaVersion:2,dashboardName:'T',routingName:'t-x',projectDir:'.',orgName:'o',tenantName:'t',cloudUrl:'c',apiUrl:'a',timeRange:'30d',clientId:'',metrics:[...]}`) merged with overrides. Grep existing tests for a similar factory first and reuse it.

- [ ] **Step 2: Run tests, confirm they fail** — `node --test resolution.test.mjs` → the 4 new tests fail (no validation yet).

- [ ] **Step 3: Implement `validateDetailView` + call it from `validateIntent`.** Add near `VALID_DISPLAY_TYPES` (:165):

```js
const DETAIL_CHART_TYPES = new Set(['donut-chart', 'bar-chart', 'area-chart', 'line-chart', 'multi-line-chart'])
const DETAIL_TABLE_TYPES = new Set(['data-table', 'ranked-table'])

/** Validate a metric's optional detailView spec. Throws with a precise message. */
export function validateDetailView(metric) {
  const dv = metric.detailView
  if (dv == null) return
  if (!metric.rowLink?.key && metric.detail !== true) {
    throw new Error(`metric "${metric.name}": detailView requires the metric to have rowLink.key (table) or detail:true (chart)`)
  }
  if (!Array.isArray(dv.widgets) || dv.widgets.length === 0) {
    throw new Error(`metric "${metric.name}": detailView.widgets must be a non-empty array`)
  }
  for (const w of dv.widgets) {
    if (!w.source || typeof w.source !== 'string') throw new Error(`metric "${metric.name}": each detailView widget needs a "source" string`)
    if (!w.title) throw new Error(`metric "${metric.name}": detailView widget (source "${w.source}") needs a title`)
    const isChart = DETAIL_CHART_TYPES.has(w.displayAs)
    const isTable = DETAIL_TABLE_TYPES.has(w.displayAs)
    if (!isChart && !isTable) throw new Error(`metric "${metric.name}": detailView widget displayAs "${w.displayAs}" invalid`)
    if (w.displayAs === 'multi-line-chart') {
      if (!w.xKey || !Array.isArray(w.series) || w.series.length === 0) throw new Error(`metric "${metric.name}": detailView multi-line-chart needs xKey + series[]`)
    } else if (isChart) {
      if (!w.xKey || !w.yKey) throw new Error(`metric "${metric.name}": detailView ${w.displayAs} needs xKey and yKey`)
    }
  }
}
```

Then inside `validateIntent`, in the per-metric loop, add: `validateDetailView(m)`.

- [ ] **Step 4: Run tests, confirm pass.**

- [ ] **Step 5: Commit (deferred — single commit at Task 8).**

---

## Task 3: `compileDetailWidgets` generator + wire into keyed view

**Files:**
- Modify: `build-dashboard.mjs` — new exported `compileDetailWidgets(detailView)`; modify `generateKeyedDetailViewFile` (:665) + `writeKeyedViewIfRowLink` (:246).
- Test: `resolution.test.mjs`.

- [ ] **Step 1: Failing test** for the generator:

```js
import { compileDetailWidgets } from '../build-dashboard.mjs'

test('compileDetailWidgets: emits primitive imports + JSX per sub-widget', () => {
  const { imports, jsx } = compileDetailWidgets({ widgets: [
    { displayAs: 'donut-chart', title: 'By Hook', source: 'byHook', xKey: 'name', yKey: 'value' },
    { displayAs: 'ranked-table', title: 'Rules', source: 'byRule', columns: [{ key: 'name', label: 'Rule' }] },
    { displayAs: 'data-table', title: 'All', source: 'rows' },
  ]}, 'd')
  assert.ok([...imports].some(i => i.includes('Donut')), 'Donut import missing')
  assert.ok(jsx.includes('d.byHook'), 'byHook source not referenced')
  assert.ok(jsx.includes('RecordsTable'), 'table sub-widget not rendered via RecordsTable')
  assert.equal(jsx.match(/<[A-Z][a-zA-Z]*<<[A-Z_]+>>/g), null) // no leftover placeholders
})
```

- [ ] **Step 2: Run, confirm fail** (no `compileDetailWidgets` export).

- [ ] **Step 3: Implement `compileDetailWidgets`** (place after `compileColumns`, :950). Returns `{ imports:Set<string>, jsx:string }`. Charts → primitive; tables → `RecordsTable` in a titled Card. `dataVar` is the normalized map variable name (`d`).

```js
/**
 * Compile a detailView spec into JSX + the set of imports it needs.
 * @param {{widgets:Array<object>}} detailView
 * @param {string} dataVar  the in-component variable holding the named-source map (e.g. 'd')
 * @returns {{imports:Set<string>, jsx:string}}
 */
export function compileDetailWidgets(detailView, dataVar = 'd') {
  const imports = new Set()
  const PRIMITIVE = { 'donut-chart': 'Donut', 'bar-chart': 'Bars', 'area-chart': 'TrendArea', 'line-chart': 'TrendArea', 'multi-line-chart': 'MultiLine' }
  const blocks = detailView.widgets.map(w => {
    const src = `(${dataVar}[${JSON.stringify(w.source)}] ?? []) as Record<string, unknown>[]`
    if (w.displayAs === 'data-table' || w.displayAs === 'ranked-table') {
      imports.add(`import { RecordsTable, type ColumnDef } from '@/dashboard/chrome/RecordsTable'`)
      imports.add(`import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'`)
      const cols = w.columns ? compileColumns(w.columns) : `autoColumns(${src})`
      return `        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">${escapeJsx(w.title)}</CardTitle></CardHeader>
          <CardContent className="pt-2"><RecordsTable rows={${src}} columns={${cols}} /></CardContent>
        </Card>`
    }
    const comp = PRIMITIVE[w.displayAs]
    imports.add(`import { ${comp} } from '@/dashboard/charts'`)
    if (w.displayAs === 'multi-line-chart') {
      return `        <${comp} data={${src}} xKey=${JSON.stringify(w.xKey)} series={${JSON.stringify(w.series)}} title=${JSON.stringify(w.title)} />`
    }
    const areaProp = w.displayAs === 'line-chart' ? ' area={false}' : ''
    if (comp === 'TrendArea') {
      return `        <${comp} data={${src}} xKey=${JSON.stringify(w.xKey)} yKey=${JSON.stringify(w.yKey)} title=${JSON.stringify(w.title)}${areaProp} />`
    }
    return `        <${comp} data={${src}} nameKey=${JSON.stringify(w.xKey)} valueKey=${JSON.stringify(w.yKey)} title=${JSON.stringify(w.title)} />`
  })
  return { imports, jsx: blocks.join('\n') }
}
```

> `escapeJsx` — reuse the existing string-escape helper if present (grep); else `JSON.stringify(title).slice(1,-1)` inline. Simpler: render titles via the primitive's `title=` prop using `JSON.stringify` (already done for charts). For the table Card title use `{${JSON.stringify(w.title)}}` instead of raw text to avoid escaping issues — adjust the table block to `<CardTitle ...>{${JSON.stringify(w.title)}}</CardTitle>`.

- [ ] **Step 4: Modify `generateKeyedDetailViewFile` (:665)** to branch on `widget.detailView`:
  - Add `detailView` to the destructured `widget` fields.
  - When `detailView` present: inject `compileDetailWidgets(detailView,'d').imports` into the import block, change the fetched state to `useState<unknown>(null)`, normalize `const d = (data && !Array.isArray(data)) ? (data as Record<string, unknown[]>) : { rows: toRows(data) }`, and render `<div className="space-y-6">{compiled jsx}</div>` inside `DetailViewShell` instead of the single `RecordsTable`. Keep `toRows` + `autoColumns` helpers (still used by table sub-widgets / legacy path).
  - When absent: emit exactly today's single-`RecordsTable` body (unchanged).

  Concretely, compute once at the top of the function:
  ```js
  const dv = widget.detailView
  const compiled = dv ? compileDetailWidgets(dv, 'd') : null
  const extraImports = compiled ? [...compiled.imports].join('\n') : ''
  const body = compiled
    ? `      <div className="space-y-6">\n${compiled.jsx}\n      </div>`
    : `      <RecordsTable rows={rows} columns={columns} />`
  ```
  Inject `extraImports` after the existing imports, add the normalize line `const d = (data && !Array.isArray(data)) ? (data as Record<string, unknown[]>) : { rows: toRows(data as unknown) }` before the return, and substitute `${body}` into the success `DetailViewShell`. Guard the legacy `rows`/`columns` consts so they don't dangle when `dv` is set (only declare them in the non-dv branch, or keep them — they're harmless if `RecordsTable` import remains; simplest: always keep `toRows`/`autoColumns`, declare `rows`/`columns` only in the no-dv body string).

- [ ] **Step 5: Pass `detailView` through `writeKeyedViewIfRowLink` (:246)** — add `detailView: metric.detailView ?? null` to the object passed to `generateKeyedDetailViewFile`.

- [ ] **Step 6: Run the generator test + confirm pass.**

---

## Task 4: Wire `detailView` into the chart record-grain view (`generateViewFile`)

**Files:** Modify `build-dashboard.mjs` `generateViewFile` (:592) + `buildViewSpec` (:1010).

- [ ] **Step 1: Failing test** — `generateViewFile` with a `detailView` emits a chart primitive import + sub-widget JSX, and without one still emits a single `RecordsTable` (backward-compat assertion).

- [ ] **Step 2: `buildViewSpec` (:1010)** — add `detailView: metric.detailView ?? null` to the returned spec.

- [ ] **Step 3: `generateViewFile` (:592)** — mirror Task 3 Step 4: branch on `widget.detailView`. The record-grain view uses `useWidgetData(${detailExport}, [])`; normalize its `data` the same way (`const d = (data && !Array.isArray(data)) ? … : { rows: toRows(data ?? []) }`) and render the compiled sub-widgets when `detailView` is set, else the current single table.

- [ ] **Step 4: Run tests, confirm pass + backward-compat test green.**

---

## Task 5: Registry + governance recipe (the agent-compliance example)

**Files:**
- Modify: `skills/uipath-coded-apps/assets/scripts/capability-registry.json` — `agent-compliance-report` entry.
- Modify: `skills/uipath-coded-apps/references/sdk/governance-traces.md` — the Layer-1 recipe.

- [ ] **Step 1: Add a default `detailView` to `agent-compliance-report`** (under its `defaults`):

```jsonc
"detailView": { "widgets": [
  { "displayAs": "donut-chart",  "title": "Violations by Hook",  "source": "byHook",     "xKey": "name", "yKey": "value" },
  { "displayAs": "ranked-table", "title": "Top Rules Fired",     "source": "byRule",
    "columns": [ {"key":"name","label":"Rule"}, {"key":"value","label":"Fired","align":"right","format":"number"} ] },
  { "displayAs": "data-table",   "title": "All Rule Evaluations","source": "rows",
    "columns": [ {"key":"hook","label":"Hook"}, {"key":"rule","label":"Rule"}, {"key":"standard","label":"Standard"}, {"key":"status","label":"Status"}, {"key":"action","label":"Action"} ] }
] }
```
Update the entry description: append "rowLink → a per-agent **rich** detail view (donut by hook + ranked rules + full table) via `detailView` + a named-source `fetchDetailByKey`."

- [ ] **Step 2: Rewrite the `fetchDetailByKey` recipe in `governance-traces.md`** to return the named-source map:

```ts
export const fetchDetailByKey: MetricDetailByKeyFn = async (sdk, agentName) => {
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  const { Traces } = await import('@uipath/uipath-typescript/traces')
  const { parseGovernanceSpans, countBy } = await import('@/lib/governance')
  const jobs = (await new Jobs(sdk as never).getAll({ filter: "ProcessType eq 'Agent'", orderby: 'CreationTime desc' }))?.items ?? []
  const job = jobs.find((j: { processName?: string | null; traceId?: string | null }) => j.processName === agentName)
  if (!job?.traceId) return { rows: [], byHook: [], byRule: [] }
  const spans = await new Traces(sdk as never).getById(job.traceId)
  const { violations } = parseGovernanceSpans(spans)
  const rows = (spans ?? []).filter((s: any) => String(s.name).startsWith('governance.rule.')).map((s: any) => {
    const a: any = (s.attributes && typeof s.attributes === 'object') ? s.attributes
      : (() => { try { return JSON.parse(s.attributes ?? '{}') } catch { return {} } })()
    return { hook: a['governance.hook'] ?? '', rule: a['governance.rule_name'] ?? a['governance.rule_id'] ?? s.name,
             standard: a['governance.pack_name'] ?? '', status: a['governance.status'] ?? '', action: a['governance.action'] ?? '' }
  })
  return { rows, byHook: countBy(violations, v => v.hook), byRule: countBy(violations, v => v.ruleName) }
}
```
Add a note: "When the metric declares `detailView`, return a **named-source map** (`{ rows, byHook, byRule, … }`) whose keys match each sub-widget's `source`; otherwise return a bare array (single table). The map is derived from ONE `Traces.getById` call — no extra round-trips."

---

## Task 6: Docs — the `detailView` contract + planner gating

**Files:** `references/dashboards/primitives/detail-views.md`, `references/dashboards/plugins/build/impl.md`, `references/dashboards/primitives/tier-resolution.md`.

- [ ] **Step 1: `detail-views.md`** — add a "## Rich detail views (charts)" section: the `detailView.widgets[]` schema, the named-source-map contract + the array-fallback, the chart primitives (`Donut`/`Bars`/`TrendArea`/`MultiLine` from `@/dashboard/charts`, tables via `RecordsTable`), and the rule "each sub-widget renders its own EmptyState when its `source` is empty."

- [ ] **Step 2: `build/impl.md`** — in "Presentation fields", document `detailView`; add a planner callout: **"Rich drill-downs are opt-in.** Add a `detailView` only when the user asks to click an entity and *see charts/insights* about it (e.g. 'let me click an agent and see its violation breakdown'). Default detail views stay a single records table. When you add one, the module's detail fetch must return a named-source map whose keys match each sub-widget's `source`."

- [ ] **Step 3: `tier-resolution.md`** — in the governance gated section, note the `agent-compliance-report` row-click now opens a rich detail view (donut + ranked rules + table) by default.

---

## Task 7: Validate end-to-end (self-test build)

**Files:** none committed — a throwaway project under `C:\Work\_dv-test\` (delete after).

- [ ] **Step 1: Republish the kit** so the new primitives ship: `cd apps-dev-tools/uipath-dashboard-starter-kit && node publish.mjs`. Bump `starter-kit.json` version first (e.g. `2.3.0 → 2.4.0`).

- [ ] **Step 2: Author a self-test intent + module** at `C:\Work\_dv-test\intent\` — one `agent-compliance-report` metric with the default `detailView`, and `metrics/agent-compliance-report.ts` exporting `fetchData` (agents list) + the named-map `fetchDetailByKey` from Task 5.

- [ ] **Step 3: Extract the kit + build:**
```bash
mkdir -p C:/Work/_dv-test/proj && powershell -NoProfile -Command "Expand-Archive -LiteralPath '<SKILL>/assets/fixtures/governance-dashboard-starter-kit.zip' -DestinationPath 'C:/Work/_dv-test/proj' -Force"
cd C:/Work/_dv-test/proj && npm ci --silent && node "<SKILL>/assets/scripts/build-dashboard.mjs" C:/Work/_dv-test/intent/intent.json
```
Expected: `METRICS_PASS` + `WIDGET_READY` + `TSC_PASS` + `BUILD_RESULT success`.

- [ ] **Step 4: Confirm the generated `AgentComplianceReportDetailView.tsx`** imports `Donut`/`Bars` from `@/dashboard/charts`, references `d.byHook`/`d.byRule`/`d.rows`, and has no leftover `<<…>>` placeholders. `grep` it.

- [ ] **Step 5: Clean up** `rm -rf C:/Work/_dv-test`.

---

## Task 8: Full test pass + single commit per repo

- [ ] **Step 1:** `node --test resolution.test.mjs` → all green (existing 118 + the new detailView/compileDetailWidgets tests).
- [ ] **Step 2:** `node --test apps-dev-tools/uipath-dashboard-starter-kit/tests/governance.test.mjs` → 6/6 (unchanged).
- [ ] **Step 3: Commit apps-dev-tools** (`feat/dashboard-starter-kit`), ONE commit: charts primitives + index + `starter-kit.json` bump.
```bash
git add scaffold/src/dashboard/charts starter-kit.json
git commit -m "feat(starter-kit): presentational detail-view chart primitives (vX.Y.0)"
```
- [ ] **Step 4: Commit skills** (`feat/dashboard-compiler-arch`), ONE commit: `build-dashboard.mjs` (validateDetailView, compileDetailWidgets, view generators), registry, governance-traces.md, detail-views.md, build/impl.md, tier-resolution.md, resolution.test.mjs, republished `.zip` + `.version`, this plan.
```bash
git commit -m "feat(dashboards): rich detail views — charts in drill-downs via detailView spec"
```
End commit messages with the standard Claude Code trailer.

---

## Self-review checklist (run before executing)
- **Backward compatibility:** a metric with no `detailView` whose detail fetch returns an array renders the single `RecordsTable` exactly as today — assert with a regression test (Task 4 Step 1).
- **No new SDK round-trips:** the named-source map is derived client-side from ONE `Traces.getById` (Task 5) — no per-chart fetch.
- **Type names consistent:** `compileDetailWidgets`, `validateDetailView`, primitive names (`Donut`/`Bars`/`TrendArea`/`MultiLine`) used identically across build code, scaffold, and docs.
- **Robustness:** every sub-widget renders an EmptyState when its `source` is empty; the detail fetch never throws (uses `@/lib/governance`).
- **Gating:** `detailView` is opt-in (planner adds it only when the user asks for chart drill-downs) and only valid on `rowLink`/`detail:true` metrics (Task 2 validation).
- **Placeholders:** the generated view has no leftover `<<…>>` (Task 7 Step 4 + the generator test assertion).
