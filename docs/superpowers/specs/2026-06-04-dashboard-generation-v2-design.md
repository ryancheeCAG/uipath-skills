# Dashboard Generation v2 — Design Spec

**Date:** 2026-06-04
**Branch:** feat/uipath-dashboards-skill
**Status:** Approved for implementation planning

---

## 1. Problem Statement

The current dashboard generation capability (v1) asks the AI agent to orchestrate 7 sequential phases and write TypeScript widget configurations. This creates three compounding problems:

1. **Brittleness** — agent-generated TypeScript config is a hallucination surface. Any error cascades to a broken build.
2. **Slowness** — 7 sequential phases with timing-dependent pre-warm. Typical time: 90–150s. Hard floor at ~60s.
3. **Opacity** — no progress feedback during build. User sees nothing until success or failure.

This spec defines v2, which eliminates all three problems by shifting intelligence from the agent to deterministic code.

---

## 2. Target User & Goals

**Primary user:** UiPath Admin / CoE Lead. Manages the automation platform. Understands Orchestrator and tenants. Wants operational visibility without writing code.

**Success criteria:**
- First dashboard live in browser: <60s for ≤4 T1/T2 widgets, <3 min for complex dashboards with T3 metrics
- Zero broken builds caused by agent-generated TypeScript
- Every unknown metric gets a generation path, not a refusal
- Follow-up customizations (add/remove/change widget) complete in <10s with hot-reload
- Resuming an existing dashboard in a new session requires zero re-prompting

---

## 3. Architecture Overview

Four layers with clean separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1 — AGENT (NLP)                                      │
│  Intent Extractor → Plan Renderer → Tier 3 Hook Author     │
│  Writes: intent.json (3 fields) + T3 fn bodies only        │
└────────────────────────┬────────────────────────────────────┘
                         │ intent.json
┌────────────────────────▼────────────────────────────────────┐
│  LAYER 2 — RESOLUTION ENGINE (deterministic code)           │
│  Metric Classifier → Tier Router → Widget Config Builder   │
│  Output: validated widget specs[]                           │
└────────────────────────┬────────────────────────────────────┘
                         │ widget specs[]
┌────────────────────────▼────────────────────────────────────┐
│  LAYER 3 — BUILD ENGINE (build-dashboard.mjs)               │
│  Scaffold Copier → Code Generator → tsc Validator          │
│  → Progressive Emitter (WIDGET_READY events to stdout)     │
└────────────────────────┬────────────────────────────────────┘
                         │ events stream
┌────────────────────────▼────────────────────────────────────┐
│  LAYER 4 — UX SHELL                                         │
│  Pre-warm Manager → Progress Reporter → State Manager      │
│  → Dev Server (hot-reload on incremental edits)            │
└─────────────────────────────────────────────────────────────┘
```

**Key architectural shift from v1:** Everything except NLP → intent extraction moves out of the agent into deterministic, testable code. The agent's only jobs are: (1) extract intent, (2) render the plan, (3) author Tier 3 function bodies when needed.

---

## 4. User Journey

### 4.1 Happy Path — First Dashboard

| Time | What happens |
|------|-------------|
| T+0s | User sends NLP request: "show me agent error rates, invocation volume, and queues where failure > 20% for 30 days" |
| T+1s | Agent writes intent.json (3 fields). Pre-warm fires silently (`npm ci` in background). Resolution Engine classifies all 3 metrics in parallel. |
| T+3s | Agent renders plain-English plan. No API names, no technical jargon. Shows what each widget does and invites changes. |
| T+3–25s | User reads plan. npm ci completes in background. |
| T+25s | User confirms. Build Engine starts. Progress ticks stream to terminal as each widget validates. |
| T+45s | Dashboard opens in browser. Agent: "Your dashboard is live at http://localhost:5173. Tell me what to change." |

### 4.2 Plan Format

```
Here's your **Operations Health Dashboard** — 3 widgets. Confirm to build, or tell me what to change.

• **Agent Error Rate (30 days)** — daily error counts as a trend line, so you can spot spikes early
• **Invocation Volume (30 days)** — total runs per day as an area chart
• **High-Failure Queues** — queues where failure rate > 20%, ranked by failure rate

What you can do: "make it 7 days", "add a KPI for total errors today", "remove the queue widget", "add job failures"
```

Rules:
- No API endpoint names visible to user
- No tier labels (T1/T2/T3) visible to user
- Every widget gets a one-line plain-English description of *why* it's useful
- "What you can do" block always present with 3–4 concrete edit examples
- If any metric was hard-refused: shown as strikethrough with plain-English reason + alternative

### 4.3 Follow-up Enhancements

| Request | Agent writes | Build script does | Time |
|---------|-------------|-------------------|------|
| "add a KPI showing total errors today" | ADD edit-intent.json | Generate 1 widget file, inject into Dashboard.tsx, tsc validate, hot-reload | ~5s |
| "change the error chart to 7 days" | CHANGE edit-intent.json | Re-run resolution with new params, regenerate 1 widget file, tsc validate, hot-reload | ~5s |
| "remove the queue widget" | REMOVE edit-intent.json | Delete widget file, remove from Dashboard.tsx + index.ts, update state.json, hot-reload | ~2s |

### 4.4 New Session Resume

Agent detects `.dashboard/state.json` → reads widget list, org, tenant, routing name → starts dev server (no rebuild) → reports: "Found existing dashboard with N widgets. Server running at http://localhost:5173. What would you like to change?" Zero re-prompting.

---

## 5. Intent JSON Schema

The only artifact the agent produces for a fresh build:

```json
{
  "dashboardName": "Operations Health",
  "timeRange": "30d",
  "metrics": [
    { "name": "agent-errors", "tier": "T1" },
    { "name": "invocation-volume", "tier": "T1" },
    {
      "name": "queue-failure-threshold",
      "tier": "T2",
      "params": { "threshold": 0.2, "direction": "gt" }
    },
    {
      "name": "faulted-queue-items",
      "tier": "T3",
      "title": "Faulted Queue Items by Queue",
      "displayAs": "ranked-table",
      "columns": ["name", "pending"],
      "fnBody": "const r = await sdk.queues.getAll({ state: 'Faulted' })\nreturn r.items?.map(q => ({ name: q.name, pending: q.pendingCount })) ?? []"
    }
  ]
}
```

Valid `timeRange` values: `"1d"`, `"7d"`, `"30d"`, `"90d"`.

**Agent determines tier during in-context classification (no tool call).** The Resolution Engine validates the tier claim and re-classifies if a T1 entry exists that the agent missed.

**T2 params are compact.** The agent provides filter values only (`threshold`, `direction`). The Resolution Engine expands these to a full descriptor using the capability registry entry for that metric name (which specifies service, method, sort defaults, and display template). The agent never writes the full descriptor.

**T3 fn body is inline in intent.json.** The `fnBody` field contains the async function body as a string. The build script injects it into the typed template shell at build time. If the fn body fails `tsc`, the build script emits `T3_RETRY` and overwrites `metrics[n].fnBody` in intent.json with the corrected version — the file is the shared state for the retry loop.

---

## 6. Tiered Resolution Engine

All classification and widget config generation happens in the build script. The agent never writes TypeScript widget code.

### 6.1 Tier 1 — Catalog (pure template substitution)

**Trigger:** metric name has an exact alias match in the capability registry.

**What build script does:**
1. Look up capability entry by alias
2. Read template file from `assets/templates/dashboard/widgets/<template>.tsx`
3. Replace all `<PLACEHOLDER>` markers using registry defaults
4. Inject time constants after last import line
5. Write widget file atomically (`.tmp` → rename)

**What agent provides:** metric name + time range. Nothing else.

**Speed:** <1s per widget.

### 6.2 Tier 2 — Parametric (typed descriptor → compiled TypeScript)

**Trigger:** metric maps to a known SDK service but with custom filter/threshold/transform. No exact catalog match.

**Typed descriptor schema (agent fills values, not code):**

```json
{
  "service": "queues",
  "method": "getAll",
  "filter": {
    "field": "failureRate",
    "op": "gt",
    "value": 0.2
  },
  "sort": { "field": "failureRate", "dir": "desc" },
  "displayAs": "ranked-table",
  "title": "High-Failure Queues",
  "columns": ["name", "failureRate", "total"]
}
```

Valid `op` values: `"gt"`, `"lt"`, `"eq"`, `"gte"`, `"lte"`, `"neq"`.
Valid `displayAs` values: all T1 template names.

**What build script does:** validates descriptor against JSON schema, compiles to TypeScript SDK hook + filter expression + column definitions. No arbitrary code paths — only the descriptor values are variable.

**Hallucination risk:** field names and threshold numbers only. No code.

**Speed:** <2s per widget.

### 6.3 Tier 3 — Sandboxed Custom (typed fn body, component shell is deterministic)

**Trigger:** genuinely novel query with no catalog or parametric match.

**Constrained interface (never changes):**

```typescript
type Row = Record<string, unknown>
type DataFn = (
  sdk: UiPathClient,
  getToken: () => Promise<string>
) => Promise<Row[]>
```

**Agent writes only the function body:**

```typescript
const r = await sdk.queues.getAll({ state: 'Faulted' })
return r.items?.map(q => ({
  name: q.name,
  pending: q.pendingCount
})) ?? []
```

**Build script:**
1. Injects fn body into typed template shell (error boundary, loading state, card wrapper are always deterministic)
2. Runs `tsc --noEmit` on that file only
3. On error: emits `T3_RETRY:{"widget":"<name>","errors":[...],"intentPath":"<abs-path>"}` to stdout
4. Agent reads the event, rewrites the `fnBody` field in intent.json at `intentPath`, emits `T3_FIX_READY` to the build script's stdin
5. Build script re-injects the updated fn body and re-runs tsc
6. Max 3 retries. On 3rd failure: emits `T3_FAILED`, agent reports to user with plain-English explanation

**Key property:** T1/T2 widgets continue generating while T3 retry is in flight. Other widgets are not blocked.

**Speed:** 5–10s + up to 3 tsc round-trips for retries.

### 6.4 Hard Refuse Table

Checked before any tier routing. Agent refuses only the specific metric (not the whole dashboard) with a plain-English reason and alternative:

| Refused request | Reason | Alternative offered |
|----------------|--------|---------------------|
| Agent cost in dollars | Platform tracks AGU units, not currency | AGU consumption chart |
| Real-time CPU/memory per agent | Not exposed by any API | Fleet-level latency via Traceview |
| Per-user job attribution | Job records carry no end-user identity | Job counts by process name |
| Cross-tenant comparison | Dashboard scoped to one tenant | Multi-widget single-tenant view |
| SLA breach % | Raw counts only, no SLA metadata | Success rate % (computable) |
| Per-agent memory profiling | Traceview is fleet-level only | Fleet memory timeline |
| Historical queue throughput | No endpoint | Queue item counts over time |
| Error message text / stack traces | No aggregation endpoint | Error count by type |

---

## 7. Progressive Build Protocol

### 7.1 Pre-warm Guarantee

**Current problem:** pre-warm timing-dependent. If user confirms before npm finishes, build fails mid-flight.

**v2 solution:** build script writes `.prewarm.lock` when npm ci starts. Code generation phase polls for `node_modules/.package-lock.json` before writing any widget file. If not ready when user confirms, build script shows "Installing dependencies..." inside the build phase — never a failure. Pre-warm is decoupled from plan review timing entirely.

**Early validation:** build script validates `GH_NPM_REGISTRY_TOKEN` is set before starting pre-warm. Emits `AUTH_MISSING:{"var":"GH_NPM_REGISTRY_TOKEN"}` immediately if not.

### 7.2 Event Streaming Protocol

Build script emits structured events to stdout, one per line. Agent parses in real time:

```
PREWARM_DONE
SCAFFOLD_READY
ENV_WRITTEN
WIDGET_READY:{"name":"ErrorRateTrend","index":1,"total":4}
WIDGET_READY:{"name":"InvocationVolume","index":2,"total":4}
T3_RETRY:{"widget":"CustomQuery","errors":["TS2339: Property 'x' does not exist on type 'y'"]}
WIDGET_READY:{"name":"CustomQuery","index":3,"total":4}
WIDGET_READY:{"name":"HighFailureQueues","index":4,"total":4}
TSC_PASS
SERVER_READY:{"port":5173,"url":"http://localhost:5173"}
BUILD_RESULT:{"success":true,"widgets":[...]}
```

Agent displays progress ticks as WIDGET_READY events arrive. T3_RETRY triggers agent to rewrite fn body and pipe it back via stdin.

### 7.3 Widget Generation Parallelism

T1 and T2 widgets generate in parallel (`Promise.all` inside build script). T3 widgets run sequentially because they require agent interaction round-trips. A dashboard with 4 widgets where 3 are T1/T2 takes the time of the slowest T1/T2 widget (~1s) plus T3 resolution time, not 4× sequential.

---

## 8. Incremental Editing

### 8.1 Edit Intent Schema

```typescript
type EditIntent =
  | { op: "ADD"; metric: MetricRef }
  | { op: "REMOVE"; target: string }          // widget component name
  | { op: "CHANGE"; target: string; delta: Partial<MetricRef> }
  | { op: "REBUILD" }                          // full regeneration
```

Agent writes a single `edit-intent.json` to the dashboard project root (same directory as `.dashboard/state.json`). Build script reads `state.json`, applies the diff, regenerates only affected files, hot-reload fires automatically.

### 8.2 Hand-Edit Protection

Build script hashes each generated widget file at write time, stores hash in `state.json`:

```json
"widgets": {
  "ErrorRateTrend": { "hash": "a3f7b2...", "tier": "T1" }
}
```

On CHANGE or REMOVE: if current file hash ≠ stored hash, file was hand-edited. Build script emits `HAND_EDIT_DETECTED:{"widget":"ErrorRateTrend"}`. Agent warns user before overwriting. REBUILD always asks for confirmation before overwriting any hand-edited file.

### 8.3 Routing Name Permanence

Routing name derived at first build: `<kebab-dashboard-name>-<4-char-suffix>`. Stored in `state.json`. Never changes on edits, never changes on deploy upgrades. Ensures app URL slug and Orchestrator package identity remain stable across the dashboard's lifetime.

---

## 9. Error Handling

| Failure | Detection | Recovery |
|---------|-----------|----------|
| T3 TypeScript error | `T3_RETRY` event with error array | Agent rewrites fn body, max 3 retries. On 3rd: `T3_FAILED`, agent explains to user and offers widget removal or request reformulation |
| npm install failure | `PREWARM_FAILED` event with exit code + stderr excerpt | Agent surfaces error to user, suggests running `npm ci` manually for full output |
| Missing npm token | `AUTH_MISSING:{"var":"GH_NPM_REGISTRY_TOKEN"}` before pre-warm starts | Agent tells user to set the variable and retry |
| UiPath auth expiry | `uip login status` returns not-logged-in | Agent runs `uip login`, waits for browser auth, then retries |
| Partial build crash | `.build-in-progress` sentinel present at next build start | `PARTIAL_BUILD_DETECTED` event — agent asks user: resume (skip scaffold+npm, regenerate missing widgets) or clean rebuild |
| Port conflict | Vite auto-increments port | Build script captures actual port from Vite stdout, emits `SERVER_READY` with actual port. Agent always reports actual URL. |
| Hard-refuse metric in mixed request | Classified during resolution | Agent refuses only that metric, builds dashboard with remaining metrics. Refused metric shown with strikethrough + reason + alternative in plan. |
| T2 descriptor schema violation | JSON schema validation before compile | `T2_SCHEMA_ERROR` event with violation detail. Agent reformulates the parametric descriptor. |
| Hand-edited widget on CHANGE/REMOVE | Hash mismatch vs state.json | `HAND_EDIT_DETECTED` event. Agent warns user and asks for confirmation before overwriting. |

---

## 10. State File Schema (v2)

`.dashboard/state.json`:

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
    "ErrorRateTrend": { "hash": "a3f7b2...", "tier": "T1", "metric": "agent-errors" },
    "InvocationVolume": { "hash": "c9e1d4...", "tier": "T1", "metric": "invocation-volume" },
    "HighFailureQueues": { "hash": "f2a8c6...", "tier": "T2", "metric": "queue-failure-threshold" }
  },
  "deployment": {
    "systemName": null,
    "folderKey": null,
    "appUrl": null,
    "lastDeployedAt": null
  }
}
```

`schemaVersion: 2` enables migration detection if schema changes in future.

---

## 11. What Changes vs v1

### Removed from agent responsibility

- Deriving TypeScript widget configs (moved to Tier Router + Code Generator)
- Writing widget files (moved to Build Engine)
- Orchestrating 7 sequential phases (moved to build-dashboard.mjs pipeline)
- Timing-based pre-warm (replaced by polling-based guarantee)
- Streaming no progress during build (replaced by WIDGET_READY event stream)

### Added to build-dashboard.mjs

- Tier classification + routing logic
- T1: alias lookup + placeholder substitution
- T2: JSON schema validation + descriptor compilation
- T3: fn body injection + typed interface enforcement + tsc retry loop
- Pre-warm polling guarantee (`.prewarm.lock` + `node_modules/.package-lock.json` check)
- Event streaming protocol (all events listed in §7.2)
- Widget hash tracking for hand-edit detection
- `.build-in-progress` sentinel for partial build recovery
- Parallel T1/T2 generation with sequential T3 retry

### Agent keeps

- NLP → intent.json (metric names + time range)
- In-context metric classification (T1/T2/T3/refuse) — no tool call
- Plan rendering (plain English, no API names)
- T3 fn body authoring (only when needed)
- Edit intent classification (ADD/REMOVE/CHANGE/REBUILD)
- Hard-refuse enforcement with partial dashboard offer

---

## 12. Files Affected

| File | Change |
|------|--------|
| `references/dashboards/CAPABILITY.md` | Update phase descriptions to v2 model |
| `references/dashboards/plugins/build/impl.md` | Rewrite to 5 phases (boot → preflight → plan → approve → build) |
| `references/dashboards/primitives/build-plan.md` | Update intent.json schema, add tier classification rules |
| `references/dashboards/primitives/state-file.md` | Update schema to v2 (add widget hashes, schemaVersion) |
| `assets/scripts/build-dashboard.mjs` | Major rewrite: add Resolution Engine, event streaming, pre-warm polling, T2 descriptor compilation, T3 retry loop, hash tracking, partial build recovery |
| `assets/templates/dashboard/widgets/` | Add T2 descriptor templates; T3 shell template (fn body injection point) |
| `references/dashboards/primitives/incremental-editor.md` | Update to edit-intent.json schema, add HAND_EDIT_DETECTED flow |
| `references/dashboards/primitives/insights-client.md` | No change (temporary HTTP client unchanged) |
| `references/dashboards/sdk-capabilities.md` | Add T2 parametric entries alongside existing T1 entries |

---

## 13. Out of Scope

- **Catalog pre-compilation (Approach C):** Pre-built dashboard bundles. Deferred — can be added as a performance optimisation once v2 is proven. Common dashboards (Agent Health, RPA Operations, Governance, Job Performance) are the candidates.
- **Insights SDK migration:** When UiPath ships Insights in the TypeScript SDK, the HTTP client in `insights-client.ts` is replaced. The hook interface (`useInsights`) stays the same — zero dashboard code change needed.
- **Deploy plugin changes:** v2 does not change the deploy flow. Deploy still requires explicit user confirmation and follows the existing pre-flight + pack + publish + deploy sequence.
- **Multi-tenant dashboards:** Single-tenant scoping is a hard platform constraint, not a design choice.
