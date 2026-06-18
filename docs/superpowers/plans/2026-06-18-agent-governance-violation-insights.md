# Agent Governance & Compliance Insights (trace-derived, interim) — Plan

> Brainstorm → plan. Interim capability: there is **no OOB SDK/Insights aggregate** for runtime
> governance results, so we derive them by parsing the `governance.*` spans the runtime-governance
> feature emits into agent traces. Designed to swap to a real Insights API later by changing only the
> metric modules — widgets, registry entries, and the per-agent drill-down stay.

**Goal:** Let a user ask "show governance violations in my agents for <standard>" (or for one agent) and
get a real dashboard — a tenant-wide violations overview plus a per-agent compliance report — built on
agent trace spans until an Insights API exists.

**Fits the skill via:** T3 custom metrics + the existing agent→job→trace→spans recipe + the existing
`rowLink` keyed drill-down + a new SDK reference that documents the governance-span contract.

---

## Routing gate — these views are built ONLY on explicit governance intent

This capability is **not** part of a generic agent-ops dashboard. The planner proposes the governance
widgets / per-agent compliance report **only** when the prompt carries a governance-compliance signal:

- "governance violation(s)" / "policy violation(s)" / "compliance" / "audit findings"
- a standard / pack reference: "standard(s)", "pack", **`ISO`** + clause (e.g. `ISO 42001`, `ISO/IEC 42001`,
  `A.8.4`), or a named pack (`pack_name`)
- governance-runtime terms: hook names (`BEFORE_AGENT`/`AFTER_MODEL`/…), `enforce`/`audit` mode, "rule fired"

If none of these appear, **do not** add governance widgets (a plain "agent health/ops" prompt must not pull
them in). Encoded as: a gated entry in `tier-resolution.md` (its own trigger block, distinct from the
agent-ops catalog) + registry aliases limited to the phrases above + a planner rule in `impl.md`.

**Robustness / graceful degradation (hard requirement):** the parser never throws (typed lib below); every
widget renders an EmptyState ("No governance data in the last N days") when the scan yields no governance
spans or zero violations — it must never crash a dashboard, even on agents with no governance instrumentation
or on malformed/minimal spans. The by-agent cap is `log()`-surfaced.

## Data model (verified from the shared payload)

Each trace = one agent run (one `traceId` / `jobKey`). Spans (SDK `AgentSpanGetResponse`, camelCase:
`name`, `attributes` (JSON **string**), `startTime`, `jobKey`, `referenceId` (= agentId), `spanType`).

- **Per-rule spans** — `name` starts with `governance.rule.`. Parsed `attributes`:
  `governance.rule_id`, `governance.rule_name`, `governance.pack_name` (the standard), `governance.hook`,
  `governance.matched` (bool), `governance.action` (`allow`/`audit`/`block`), `governance.status`
  (`PASS`/`MATCHED`), `governance.detail`, `governance.agent_name`, + `agentId`/`agentName`/`agentVersion`.
  **A violation = `governance.matched === true`.**
- **Per-hook summary spans** — `governance.before_agent|before_model|after_model|after_agent`:
  `governance.hook`, `governance.total_rules`, `governance.matched_rules`, `governance.final_action`,
  `governance.enforcement_mode` (`audit`/`enforce`).
- **Context spans** — `LangGraph`/`chat`/`UiPathChat`/`output`: `input.value`/`output.value` (the prompt
  + reply), model, token counts. Useful to show *what triggered* a violation in the drill-down.
- **Robustness:** some `governance.rule.*` spans carry only `{agentId, agentName, agentVersion}` (minimal
  attrs) — skip those (no rule signal). The integer span `Status` is NOT the governance signal — use
  `governance.matched`/`governance.status`.

## SDK building blocks (source-confirmed)

- `AgentTraces.getSpansByTraceId(traceId)` → spans of one trace (the per-run report).
- `AgentTraces.getSpansByReference(agentId, { pageSize, cursor })` → paginated spans across **all** of one
  agent's runs (the agent-history path — `referenceId` in the payload IS the agentId).
- `Jobs.getAll({ filter: "ProcessType eq 'Agent'", orderby: 'CreationTime desc' })` → agent runs +
  `traceId`/`processName` (to enumerate / map agentName → traceId).
- `Traces.getById` / `getSpansByIds` — the methods you named; the executor confirms the exact signature
  at build and picks whichever returns the full span set most directly.
- Scope: `Insights Insights.RealTimeData OR.Folders.Read` (spans) + `OR.Jobs.Read` (job enumeration).

---

## Typed, hardened governance lib (shipped in the starter kit)

A proper typed interface + ONE defensive parser, shipped as `scaffold/src/lib/governance.ts` (in
apps-dev-tools, bundled into the kit, type-checked by Stage A, imported by every governance metric
module — DRY + robust, never loose `any` dictionary access at call sites). **The parser never throws**:
it skips non-governance spans, malformed JSON, and minimal-attribute spans, and defaults every field.

```ts
// scaffold/src/lib/governance.ts  — the contract with the runtime-governance feature

export type GovernanceHook = 'BEFORE_AGENT' | 'BEFORE_MODEL' | 'AFTER_MODEL' | 'AFTER_AGENT' | (string & {})

/** Raw attributes on a `governance.rule.*` span (all optional — spans vary in richness). */
export interface GovernanceRuleAttributes {
  'governance.rule_id'?: string
  'governance.rule_name'?: string
  'governance.pack_name'?: string        // the standard, e.g. "ISO/IEC 42001:2023 Runtime"
  'governance.hook'?: GovernanceHook
  'governance.matched'?: boolean
  'governance.action'?: string           // allow | audit | block
  'governance.status'?: string           // PASS | MATCHED
  'governance.detail'?: string
  agentName?: string; agentVersion?: string; 'governance.agent_name'?: string
}

/** Raw attributes on a `governance.<hook>` summary span. */
export interface GovernanceHookAttributes {
  'governance.hook'?: GovernanceHook
  'governance.total_rules'?: number
  'governance.matched_rules'?: number
  'governance.final_action'?: string
  'governance.enforcement_mode'?: string // audit | enforce
  agentName?: string; agentVersion?: string
}

/** Normalized, UI-ready violation row (one per FIRED rule). */
export interface GovernanceViolation {
  agentName: string; agentVersion: string
  ruleId: string; ruleName: string
  standard: string                       // <- pack_name
  hook: GovernanceHook; action: string; status: string; detail: string
  time: string; jobKey: string; traceId: string
}

/** Per-hook rollup row (from the summary spans). */
export interface GovernanceHookSummary {
  agentName: string; hook: GovernanceHook
  totalRules: number; matchedRules: number; finalAction: string; enforcementMode: string
  time: string; jobKey: string
}

/** Minimal structural span shape the parser needs (subset of AgentSpanGetResponse). */
interface SpanLike { name?: string | null; attributes?: string | null; startTime?: string | null; jobKey?: string | null; traceId?: string | null }

const str = (v: unknown, d = '') => (v == null ? d : String(v))
const num = (v: unknown) => (Number.isFinite(Number(v)) ? Number(v) : 0)

/** Parse a trace's spans into typed violations + hook summaries. Never throws. */
export function parseGovernanceSpans(spans: SpanLike[] | null | undefined): {
  violations: GovernanceViolation[]; hookSummaries: GovernanceHookSummary[]
} {
  const violations: GovernanceViolation[] = []
  const hookSummaries: GovernanceHookSummary[] = []
  for (const s of spans ?? []) {
    const name = str(s?.name)
    if (!name.startsWith('governance.')) continue
    let a: GovernanceRuleAttributes & GovernanceHookAttributes
    try { a = JSON.parse(str(s?.attributes, '{}')) } catch { continue }   // malformed → skip
    const agentName = str(a.agentName ?? a['governance.agent_name'], 'unknown')
    if (name.startsWith('governance.rule.')) {
      if (a['governance.matched'] !== true) continue                       // only fired rules = violations
      if (!a['governance.rule_id'] && !a['governance.rule_name']) continue // minimal-attr span → skip
      violations.push({
        agentName, agentVersion: str(a.agentVersion),
        ruleId: str(a['governance.rule_id']),
        ruleName: str(a['governance.rule_name'], str(a['governance.rule_id'], 'rule')),
        standard: str(a['governance.pack_name'], 'Unknown standard'),
        hook: str(a['governance.hook']) as GovernanceHook,
        action: str(a['governance.action']), status: str(a['governance.status'], 'MATCHED'),
        detail: str(a['governance.detail']),
        time: str(s?.startTime), jobKey: str(s?.jobKey), traceId: str(s?.traceId),
      })
    } else if (/^governance\.(before|after)_(agent|model)$/.test(name)) {
      hookSummaries.push({
        agentName, hook: str(a['governance.hook']) as GovernanceHook,
        totalRules: num(a['governance.total_rules']), matchedRules: num(a['governance.matched_rules']),
        finalAction: str(a['governance.final_action']), enforcementMode: str(a['governance.enforcement_mode']),
        time: str(s?.startTime), jobKey: str(s?.jobKey),
      })
    }
  }
  return { violations, hookSummaries }
}

/** Count rows by a key → ready-to-chart [{name,value}] (for donut / ranked-table). */
export function countBy<T>(rows: T[], key: (r: T) => string): { name: string; value: number }[] {
  const m = new Map<string, number>()
  for (const r of rows) { const k = key(r) || 'Unknown'; m.set(k, (m.get(k) ?? 0) + 1) }
  return [...m.entries()].map(([name, value]) => ({ name, value })).sort((x, y) => y.value - x.value)
}
```

Metric modules then stay tiny + typed, e.g. by-standard donut:
```ts
import type { MetricFn } from '@/lib/metric-contract'
import { parseGovernanceSpans, countBy } from '@/lib/governance'
// …scan spans (Layer 2)… then:
return countBy(violations, v => v.standard)
```

## Two layers

### Layer 1 — Per-agent compliance report (cheap, 1 trace) — reuses the rowLink drill-down
A `data-table` of agents with `rowLink: { key: "agentName" }`; clicking an agent opens
`/<widget>/:key` whose `fetchDetailByKey(sdk, agentName)` does: Jobs(Agent, latest) → find by
`processName` → `traceId` → `getSpansByTraceId` → render the **full rule list** (PASS/MATCHED) grouped by
hook, plus the triggering prompt/reply — mirroring the product's Trace view in the screenshot.
**This is ~the recipe we already built; only the parsing + columns are new.**

### Layer 2 — Tenant-wide violation insights (bounded by-agent scan, interim)
A set of T3 metrics over a **shared, rate-limit-safe scan**, enumerated **by agent** (decision):

```ts
const MAX_AGENTS = 10  // hard cap so we never make an insane number of calls
const agents = (await new Agents(sdk).getAll(THIRTY_DAYS_AGO, NOW,
  { orderBy: { column: AgentListSortColumn.LastRun, desc: true } }))?.items ?? []
const scan = agents.slice(0, MAX_AGENTS)               // top-N most-recently-active
const violations = []
for (const ag of scan) {
  // time-window bounds the spans per agent (getSpansByReference accepts startTime/endTime);
  // fetch-cache dedupes; pageSize bounds pages → call count stays ~ MAX_AGENTS × few pages
  const spans = await fetchAll(cursor =>
    new AgentTraces(sdk).getSpansByReference(ag.agentId,
      { startTime: THIRTY_DAYS_AGO, endTime: NOW, pageSize: 200, cursor }))
  violations.push(...parseGovernanceSpans(spans).violations)
}
log(`scanned ${scan.length} of ${agents.length} agents (cap ${MAX_AGENTS})`)  // cap is surfaced, not silent
```

Widgets (each a small T3 module over this scan; all-standards, groupable):
- **KPI** — total violations · agents-with-violations · most-violated standard.
- **donut** — violations **by standard** (`pack_name` / clause) — the primary "for <standard>" view.
- **ranked-table** — top rules by match count (`ruleName` + count + standard).
- **donut** — violations by `hook` (BEFORE_AGENT/BEFORE_MODEL/AFTER_MODEL/AFTER_AGENT) or by `action`.
- **ranked-table** — agents by violation count.
- **data-table** — recent violations (agent · rule · standard · hook · action · detail · time),
  `rowLink` → the Layer-1 per-agent report.

---

## Tasks

- [ ] **1. Typed governance lib (apps-dev-tools → kit)** — add `scaffold/src/lib/governance.ts` with the
  interfaces + `parseGovernanceSpans` + `countBy` above; add it to `tsconfig.metrics.json`'s include so
  Stage A type-checks modules that import it. Re-pack + `publish.mjs` into the skill.
- [ ] **2. Parser unit test (apps-dev-tools)** — `tests/governance.test.mjs` against the shared payload:
  matched rules → violations; PASS rules excluded; minimal-attr spans skipped; malformed JSON skipped
  (no throw); hook summaries parsed; `countBy` groups by standard/hook/rule. Wire into `npm test`.
- [ ] **3. SDK reference** — `references/sdk/governance-traces.md`: the `governance.*` span contract,
  the `@/lib/governance` API (types + `parseGovernanceSpans`/`countBy`), the two fetch paths
  (`getSpansByTraceId` for a run; `getSpansByReference(agentId)` capped at `MAX_AGENTS`, time-bounded, for
  the aggregate), scope, and a loud **INTERIM** note (trace-derived; cap; rate-limit-safe; migrate to an
  Insights API when available — only the modules change).
- [ ] **4. Routing gate** — `tier-resolution.md`: a distinct gated trigger block (governance/compliance/
  standard/pack/ISO signals) separate from the agent-ops catalog; registry aliases limited to those
  phrases; `impl.md` planner rule: propose governance widgets ONLY on those signals, never for a plain
  agent-ops prompt. State it's trace-derived/interim with the bounded-scan caveat.
- [ ] **5. Registry entries (T3-documented)** — `agent-governance-violations` (KPI),
  `violations-by-standard` (donut, primary), `violations-by-rule` (ranked-table),
  `violations-by-hook` (donut), `agents-by-violations` (ranked-table),
  `recent-violations` (data-table, `rowLink` → report), `agent-compliance-report` (Layer-1 detail). Each
  `description` carries the exact SDK scan + `@/lib/governance` usage + template + scope.
- [ ] **6. Drill-down wiring** — Layer-1 `rowLink` table + keyed `fetchDetailByKey` report (reuses the
  existing keyed-view path; governance columns + hook grouping; EmptyState when no governance spans).
- [ ] **7. Skill tests** — resolution: governance aliases resolve T3 **and** are NOT proposed without a
  governance signal (gate test); widget-gen smoke for the new entries (incl. empty-data → EmptyState, no
  crash).
- [ ] **8. Self-test build** — extract kit → build an "Agent Governance" dashboard (KPI, by-standard
  donut, by-rule table, by-hook donut, recent-violations table + per-agent drill-down) → METRICS_PASS +
  TSC_PASS; also build a plain agent-ops dashboard and confirm NO governance widgets are pulled in.

## Honest caveats (the "until SDK support" part)
- **Cost:** Layer 2 is an N+1 fan-out with no aggregate endpoint — capped + cached. Fine for demo /
  small tenants; not for scale. The cap is surfaced, not silent.
- **Schema coupling:** the `governance.*` keys are a contract with the runtime-governance feature; if
  they rename keys, parsing breaks. Document the keys; skip unknown spans gracefully.
- **Verbosity:** matched rules can carry `verbosityLevel: 3`; which spans are captured depends on the
  run's verbosity. Note as a data-availability caveat.
- **Migration path:** when an Insights API lands, only the metric modules' fetch changes — registry,
  widgets, drill-down, and the dashboard layout are untouched.

## Decisions (locked)
1. **Build both layers** — per-agent report + tenant-wide aggregate.
2. **Enumerate by agent** via `getSpansByReference(agentId)`, **capped at `MAX_AGENTS = 10`** most-recently-active
   agents, **time-window bounded** per agent, fetch-cache on — keeps the call count small to avoid rate
   limiting. The cap is `log()`-surfaced ("scanned N of M agents").
3. **All standards, groupable** — default view shows all `pack_name`s with a **by-standard** breakdown
   widget (the primary lens for "violations for <standard>"); standard becomes a T2 filter param later.
