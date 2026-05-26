# Dashboard Skill — Capability Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the static `insights-catalog.md` + `data-router.md` pair with a single `sdk-capabilities.md` capability registry that drives a Phase 3a feasibility gate — ensuring agents hard-refuse unavailable metrics before any plan is shown, while adding 4 SDK widget templates for Orchestrator data.

**Architecture:** Single `sdk-capabilities.md` file documents every data source the skill can use (Insights RTM HTTP client + Orchestrator SDK). Phase 3 splits into 3a (feasibility gate — map NLP request to registry, classify GREEN/AMBER/RED) and 3b (unchanged derivation for GREEN/AMBER only). Four new SDK templates follow the existing `<PLACEHOLDER>` substitution pattern with SDK-specific fields.

**Tech Stack:** Markdown (skill docs), TypeScript/React (scaffold templates), Node.js (build script)

**Working directory:** `C:\Work\skills`

---

## File Map

| Action | Path |
|---|---|
| **Create** | `skills/uipath-coded-apps/references/dashboards/sdk-capabilities.md` |
| **Create** | `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-kpi-card.tsx` |
| **Create** | `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-data-table.tsx` |
| **Create** | `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-bar-chart.tsx` |
| **Create** | `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-ranked-table.tsx` |
| **Modify** | `skills/uipath-coded-apps/references/dashboards/CAPABILITY.md` |
| **Modify** | `skills/uipath-coded-apps/references/dashboards/plugins/build/impl.md` |
| **Modify** | `skills/uipath-coded-apps/references/dashboards/primitives/build-plan.md` |
| **Modify** | `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/hooks/useInsights.ts` |
| **Modify** | `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/lib/insights-client.ts` |
| **Modify** | `skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs` |
| **Delete** | `skills/uipath-coded-apps/references/dashboards/insights-catalog.md` |
| **Delete** | `skills/uipath-coded-apps/references/dashboards/primitives/data-router.md` |

---

## Task 1: Write `sdk-capabilities.md`

**Files:**
- Create: `skills/uipath-coded-apps/references/dashboards/sdk-capabilities.md`

- [ ] **Step 1: Create the file with refuse table and Insights RTM capabilities**

Write the full content below to `skills/uipath-coded-apps/references/dashboards/sdk-capabilities.md`:

```markdown
# SDK Capability Registry

Single source of truth for what data the dashboard skill can access. Consulted during Phase 3a
feasibility gate. Route each metric here before planning any widget.

**Data layers:**
- **Insights RTM** — POST-based analytics API via custom HTTP client (temporary; will migrate to SDK)
- **Orchestrator SDK** — live operational state via `@uipath/uipath-typescript` services

---

## Hard Refuse Table

Check this table FIRST in Phase 3a. If the user's request matches, refuse before planning.
Never approximate these silently. State the reason and offer the best alternative if one exists.

| Requested metric | Why unavailable | Suggest instead |
|---|---|---|
| Agent cost in dollars / currency | Platform tracks AGU/PLTU units, not currency | `agents.getConsumption` (AGU/PLTU) |
| Real-time CPU / memory per agent | Not exposed via any UiPath API | — |
| Per-user job attribution | Job records don't carry end-user identity | — |
| Cross-tenant comparison | Dashboard scoped to one tenant at build time | — |
| Agent version history | No version tracking endpoint | — |
| Who triggered a job (username) | Not in any UiPath API | — |
| Historical queue throughput trend | No Insights endpoint for queue history | SDK `QueueItems.getAll()` for current state |
| SLA breach count as % | No % endpoint; raw count only | `CaseInstances.getSlaSummary()` for counts |
| Per-agent memory usage | Traceview is fleet-level only | `traceview.getMemoryTimeline` (fleet) |
| Error message text / stack traces | `jobs.getFailureDetails` has rows but no aggregation | `jobs.getFailuresByReason` for type breakdown |

**Refuse wording pattern:**
```
⚠ "[Requested metric]" isn't available — [specific reason].
[If alternative: I can show [alternative] instead — want that?]
[If no alternative: I've excluded it from the plan.]
```

---

## Metric Classification

When Phase 3a classifies each requested metric:

- **GREEN** — capability entry exists AND matching template listed → use `widgets[]` array in plan.json
- **AMBER** — capability entry exists, no template → write custom SDK hook in `files{}` map; use the
  exact method signature and response shape from the capability entry below. TypeScript must compile.
- **RED** — no capability entry → hard refuse using the wording pattern above

---

## Insights RTM Capabilities

Base URL: `${VITE_UIPATH_CLOUD_URL}/${ORG}/${TENANT}/insightsrtm_`
Jobs base: `${VITE_UIPATH_BASE_URL}/${ORG}/${TENANT}`
All calls: POST JSON. All require `tenantId` (UUID), `startTime` (ISO 8601), `endTime` (ISO 8601).
**Omitting `endTime` causes 500 errors.** Always pass `endTime: NOW`.

> **Migration note:** These endpoints will be replaced by `sdk.insights.*` methods when the
> Insights service joins the TypeScript SDK. When that happens, update each entry's **Source** line
> and the `InsightsClient` method references. Templates and plan.json format do not change.

---

### agents.getSummaryV2 — Agent Fleet Summary

**Source:** Insights RTM HTTP client · `POST Agents/summaryV2`
**Response shape:**
```typescript
{
  data: {
    currentPeriodSummary: {
      totalJobs: number
      successfulJobs: number
      successRate: number          // 0–100
      averageDurationSeconds: number
    }
    agents: Array<{
      processKey: string
      successRate: number
      averageDurationSeconds: number
      lastJobStatus: string
    }>
  }
}
```
**Computable metrics:** Fleet success rate, avg duration, total job count, per-agent success rate
**Cannot compute:** Time-series trend (aggregate only — never use for line/area charts), cost
**Templates:** `kpi-card`, `ranked-table`
**Aliases:** "success rate", "pass rate", "how well are agents doing", "avg duration", "average execution time", "fleet summary", "overview", "key metrics", "important metrics", "agent health overview"

---

### agents.getErrors — Agent Error Counts Over Time

**Source:** Insights RTM HTTP client · `POST Agents/errors`
**Response shape:**
```typescript
{ data: Array<{ name: string; value: number; date: string }> }
// name = agentName, value = errorCount, date = ISO string
// One row per agent per time bucket
```
**Computable metrics:** Error count over time, total errors, error trend, per-agent error count
**Cannot compute:** Error rate % (need total runs — combine with agents.getSummaryV2), error text
**Templates:** `line-chart`, `area-chart`, `kpi-card`, `kpi-with-sparkline`
**Aliases:** "agent errors", "error count", "errors over time", "error trend", "agent failures", "which agents are failing", "error spikes"

---

### agents.getTopErroredAgents — Top-N Erroring Agents

**Source:** Insights RTM HTTP client · `POST Agents/topErroredAgents`
**Response shape:**
```typescript
{ totalErrors: number; data: Array<{ agentId: string; name: string; count: number }> }
```
**Computable metrics:** Error leaderboard, top N by error count
**Cannot compute:** Error rate %, error text
**Templates:** `bar-chart`, `ranked-table`
**Aliases:** "top erroring agents", "most failures", "error leaderboard", "which agents fail most", "worst agents"

---

### agents.getIncidents — Agent Incidents (Paged)

**Source:** Insights RTM HTTP client · `POST Agents/incidents`
**Response shape:**
```typescript
{
  totalErrorCount: number
  pagination: { total: number; pageNumber: number; pageSize: number }
  data: Array<{
    type: string
    description: string
    agentId: string
    agentName: string
    firstSeen: string     // ISO
    count: number
    folderPath: string
  }>
}
```
**Computable metrics:** Incident list, incident type breakdown, recurring error detection
**Cannot compute:** Root cause, fix recommendations
**Templates:** `data-table`
**Aliases:** "agent incidents", "recurring errors", "incident list", "what went wrong", "failure details"

---

### agents.getIncidentDistribution — Incident Type Split

**Source:** Insights RTM HTTP client · `POST Agents/incidentDistribution`
**Response shape:**
```typescript
{ data: { errorCount: number; escalationCount: number; policyCount: number } }
```
**Computable metrics:** Error / Escalation / Policy proportion
**Cannot compute:** Time-series (single aggregate period)
**Templates:** `donut-chart`, `progress-bar-list`, `kpi-card`
**Aliases:** "incident types", "error vs escalation", "incident breakdown", "what kind of failures", "incident distribution"

---

### agents.getConsumption — Agent AGU/PLTU Consumption

**Source:** Insights RTM HTTP client · `POST Agents/consumption`
**Response shape:**
```typescript
{
  data: {
    totalConsumed: number
    totalAGUConsumed: number
    totalPLTUConsumed: number
    agents: Array<{
      agentId: string
      agentName: string
      consumedQuantity: number
      consumedAGUQuantity: number
    }>
  }
}
```
**Computable metrics:** AGU/PLTU by agent, total consumption, top consumers
**Cannot compute:** Cost in currency, future consumption forecast
**Templates:** `bar-chart`, `ranked-table`, `kpi-card`
**Aliases:** "AGU consumption", "PLTU consumption", "token consumption", "top consumers", "most expensive agents", "highest usage", "who uses the most AGU"

---

### agents.getConsumptionTimeline — AGU Burn-Rate Over Time

**Source:** Insights RTM HTTP client · `POST Agents/consumptionTimeline`
**Response shape:**
```typescript
{ data: Array<{ timeSlice: string; aguConsumption: number }> }
// timeSlice = ISO string (hourly or daily bucket)
```
**Computable metrics:** AGU burn rate over time, invocation activity proxy
**Cannot compute:** Per-agent breakdown (fleet total only), cost
**Templates:** `area-chart`, `line-chart`
**Aliases:** "invocation volume", "how busy", "activity over time", "run count", "agent calls", "AGU burn rate", "usage over time"

---

### agents.getLatencyTimeline — P50/P95 Latency Per Agent

**Source:** Insights RTM HTTP client · `POST Agents/latencyTimeline`
**Response shape:**
```typescript
{ data: Array<{ name: 'P50' | 'P95'; value: number; date: string }> }
// value in seconds; one row per percentile per time bucket
```
**Computable metrics:** P50/P95 latency trend, slowest agents
**Cannot compute:** P99, individual run timing
**Templates:** `line-chart`, `multi-line-chart`
**Aliases:** "latency", "response time", "P95", "P50", "how fast are agents", "slowest agents", "execution time trend"

---

### agents.getAgents — Agent Fleet List

**Source:** Insights RTM HTTP client · `POST Agents/agents`
**Response shape:**
```typescript
{
  data: {
    agents: Array<{
      agentId: string
      agentName: string
      folderPath: string
      lastRun: string     // ISO
      healthScore: number // 0–100
      lastIncidentType: string
      unitsQuantity: number
      quantityAGU: number
    }>
  }
}
```
**Computable metrics:** Fleet list with health, active agent count, stale agents, unit usage per agent
**Cannot compute:** Real-time status, current run state
**Templates:** `data-table`, `kpi-card` (for count)
**Aliases:** "agent list", "fleet overview", "all agents", "agent status table", "health scores", "active agents", "fleet size", "how many agents", "agent count"

---

### agents.getUnitConsumption — AGU/PLTU by Job Completion

**Source:** Insights RTM HTTP client · `POST Agents/summary/unit-consumption`
**Response shape:**
```typescript
{
  data: {
    currentPeriodSummary: {
      totalAgentUnitConsumption: { completeJobs: number; incompleteJobs: number }
      totalPlatformUnitConsumption: { completeJobs: number; incompleteJobs: number }
    }
  }
}
```
**Computable metrics:** AGU/PLTU split by complete vs incomplete jobs
**Cannot compute:** Per-agent breakdown, trend over time
**Templates:** `kpi-card`, `bar-chart`
**Aliases:** "AGU by job type", "consumption split", "complete vs incomplete consumption", "unit consumption breakdown"

---

### traceview.getLatencyTimeline — Trace-Level P50/P95 Latency

**Source:** Insights RTM HTTP client · `POST Traceview/latencyTimeline`
**Response shape:** same shape as `agents.getLatencyTimeline`
```typescript
{ data: Array<{ name: 'P50' | 'P95'; value: number; date: string }> }
```
**Computable metrics:** Trace-level latency percentiles (NOT agent-level)
**Cannot compute:** Per-agent breakdown — use `agents.getLatencyTimeline` for that
**Templates:** `line-chart`, `multi-line-chart`
**Aliases:** "trace latency", "trace P50/P95", "trace response time"

---

### traceview.getErrorsTimeline — Trace Errors Per Agent

**Source:** Insights RTM HTTP client · `POST Traceview/errorsTimeline`
**Response shape:**
```typescript
{ data: Array<{ name: string; value: number; date: string }> }
// name = agentName
```
**Computable metrics:** Trace error count per agent over time
**Templates:** `area-chart`, `line-chart`
**Aliases:** "trace errors", "trace error trend"

---

### traceview.getMemoryTimeline — Agent Memory Usage (Fleet)

**Source:** Insights RTM HTTP client · `POST Traceview/memoryTimeline`
**Response shape:**
```typescript
{
  data: Array<{
    timeSlice: string        // ISO
    inMemoryCount: number
    notInMemoryCount: number
    totalCount: number
    enabledMemoryCount: number
    disabledMemoryCount: number
  }>
}
```
**Computable metrics:** In-memory vs not-in-memory agent count over time
**Cannot compute:** Per-agent memory usage (fleet total only)
**Templates:** `area-chart`
**Aliases:** "memory usage", "agent memory", "in-memory traces", "context retention", "memory timeline"

---

### governance.getPolicySummary — Policy Allow/Deny/NoOp Ratio

**Source:** Insights RTM HTTP client · `POST Governance/policy/summary`
**Extra required field:** `policy` (UUID of the policy to report on)
**Response shape:**
```typescript
{ data: { allowCount: number; denyCount: number; noOpCount: number } }
```
**Computable metrics:** Policy decision ratio
**Cannot compute:** Cross-policy comparison in one widget (one policy per call)
**Templates:** `donut-chart`, `kpi-card`
**Aliases:** "policy summary", "allow vs deny", "governance violations", "policy decisions"

---

### governance.getPolicyTraces — Policy Decision Trace Table

**Source:** Insights RTM HTTP client · `POST Governance/policy/traces`
**Response shape:**
```typescript
{
  data: Array<{
    traceId: string
    agentId: string
    agentName: string
    decision: 'Allow' | 'Deny' | 'NoOp'
    timestamp: string
    policyName: string
  }>
}
```
**Computable metrics:** Recent policy evaluations, denial feed
**Templates:** `data-table`
**Aliases:** "policy traces", "recent policy decisions", "denial feed", "governance trace"

---

### governance.getOperationSummary — Governed Operation Volume

**Source:** Insights RTM HTTP client · `POST Governance/operation/summary`
**Response shape:**
```typescript
{ data: Array<{ operationName: string; count: number; date: string }> }
```
**Computable metrics:** Which operations are governed, volume over time
**Templates:** `bar-chart`
**Aliases:** "governed operations", "operation volume", "governance activity"

---

### jobs.getSummary — Job KPI Summary

**Source:** Insights RTM HTTP client · `POST api/v1.0/InsightsJobs/summary`
**Response shape:**
```typescript
{
  data: {
    totalJobs: number
    successfulJobs: number
    failedJobs: number
    averageDurationSeconds: number
  }
}
```
**Computable metrics:** Total jobs, success count, failure count, avg duration (aggregate, not time-series)
**Cannot compute:** Time-series trend (use `jobs.getCompletedTimeline` for that)
**Templates:** `kpi-card`
**Aliases:** "job KPI", "job summary", "total jobs", "job success count", "job aggregate"

---

### jobs.getCompletedTimeline — Completed Jobs Over Time

**Source:** Insights RTM HTTP client · `POST api/v1.0/InsightsJobs/completed-timeline`
**Response shape:**
```typescript
{ data: Array<{ date: string; count: number; state: string }> }
// state = 'Successful' | 'Faulted' | 'Stopped'
```
**Computable metrics:** Completed job volume over time, success vs failure trend
**Templates:** `area-chart`, `line-chart`
**Aliases:** "job trend", "completed jobs over time", "automation volume", "job history", "jobs over time"

---

### jobs.getTopFailures — Top Failing Processes

**Source:** Insights RTM HTTP client · `POST api/v1.0/InsightsJobs/top-failures`
**Response shape:**
```typescript
{ data: Array<{ processName: string; failureCount: number }> }
```
**Computable metrics:** Ranked list of processes by failure count
**Templates:** `bar-chart`, `ranked-table`
**Aliases:** "top failures", "failing processes", "most failed automations", "worst processes"

---

### jobs.getFailuresByReason — Job Failures by Exception Type

**Source:** Insights RTM HTTP client · `POST api/v1.0/InsightsJobs/failures-by-reason`
**Response shape:**
```typescript
{ data: Array<{ reason: string; count: number }> }
```
**Computable metrics:** Breakdown of failure causes by exception type
**Templates:** `donut-chart`, `bar-chart`
**Aliases:** "failure reasons", "exception types", "why are jobs failing", "failure breakdown"

---

### jobs.getProcessDetails — Per-Process Job Stats

**Source:** Insights RTM HTTP client · `POST api/v1.0/InsightsJobs/process-details`
**Response shape:**
```typescript
{
  data: Array<{
    processName: string
    totalJobs: number
    successfulJobs: number
    successRate: number
    averageDurationSeconds: number
  }>
}
```
**Computable metrics:** Per-process success rate, duration, volume
**Templates:** `data-table`, `ranked-table`
**Aliases:** "process breakdown", "per-process stats", "automation details", "which process succeeds most"

---

## Orchestrator SDK Capabilities

Import pattern — always use subpath exports:
```typescript
import { Jobs } from '@uipath/uipath-typescript/jobs'
import { QueueItems } from '@uipath/uipath-typescript/queues'
import { Processes } from '@uipath/uipath-typescript/processes'
import { Tasks } from '@uipath/uipath-typescript/tasks'
```

SDK calls do NOT need `tenantId`, `startTime`, or `endTime` — those are Insights-only.
SDK calls use `const { sdk, isAuthenticated } = useAuth()` then `new ServiceClass(sdk as never)`.

---

### Jobs.getAll — Current Job State

**Source:** SDK · `@uipath/uipath-typescript/jobs`
**Call pattern:** `new Jobs(sdk as never).getAll(params?)`
**Parameters (optional):**
```typescript
{
  state?: string           // comma-separated: 'Running,Pending,Successful,Faulted,Stopped'
  startTime?: string       // ISO — filter jobs started after this time
  processName?: string     // filter by process
  top?: number             // page size (default 20, max 100)
  skip?: number            // offset for pagination
}
```
**Response shape:**
```typescript
{
  items: Array<{
    id: string
    key: string
    state: 'Running' | 'Successful' | 'Faulted' | 'Stopped' | 'Pending'
    startTime: string    // ISO
    endTime: string      // ISO (null if still running)
    processName: string
    organizationUnitId: number
  }>
  count: number          // total matching records (not just this page)
}
```
**Computable metrics:** Running job count, pending count, today's success count, today's failure count
**Cannot compute:** Historical trend (use `jobs.getCompletedTimeline`), per-agent breakdown
**Templates:** `sdk-kpi-card`
**Aliases:** "running jobs", "active jobs", "jobs in progress", "how many jobs are running", "pending jobs", "job queue", "job count today", "failed jobs today"

---

### QueueItems.getAll — Queue Depth (Current State)

**Source:** SDK · `@uipath/uipath-typescript/queues`
**Call pattern:** `new QueueItems(sdk as never).getAll(params?)`
**Parameters (optional):**
```typescript
{
  status?: string          // comma-separated: 'New,InProgress,Successful,Failed,Abandoned,Retried'
  queueDefinitionId?: number
  top?: number
  skip?: number
}
```
**Response shape:**
```typescript
{
  items: Array<{
    id: number
    status: 'New' | 'InProgress' | 'Successful' | 'Failed' | 'Abandoned' | 'Retried'
    queueDefinitionId: number
    queueDefinitionName: string
    priority: 'Low' | 'Normal' | 'High'
    dueDate: string | null    // ISO
    creationTime: string      // ISO
  }>
  count: number
}
```
**Computable metrics:** Queue depth (New + InProgress count), failed item count, queue name breakdown
**Cannot compute:** Historical throughput trend, SLA compliance %
**Templates:** `sdk-kpi-card`, `sdk-data-table`
**Aliases:** "queue depth", "active queue items", "queued transactions", "how full is my queue", "queue status", "queue items"

---

### Processes.getAll — Deployed Automation Inventory

**Source:** SDK · `@uipath/uipath-typescript/processes`
**Call pattern:** `new Processes(sdk as never).getAll(params?)`
**Parameters (optional):**
```typescript
{ top?: number; skip?: number }
```
**Response shape:**
```typescript
{
  items: Array<{
    id: string
    name: string
    description: string
    version: string
    environmentId: number
    environmentName: string
  }>
  count: number
}
```
**Computable metrics:** Total deployed automations, process inventory
**Cannot compute:** Run history, success rate (use Insights for historical)
**Templates:** `sdk-data-table`
**Aliases:** "what processes are deployed", "automation inventory", "list my processes", "what automations do I have", "deployed processes", "process list"

---

### Tasks.getAll — Action Center Pending Tasks

**Source:** SDK · `@uipath/uipath-typescript/tasks`
**Call pattern:** `new Tasks(sdk as never).getAll(params?)`
**Parameters (optional):**
```typescript
{
  status?: string          // comma-separated: 'Unassigned,Pending,Completed'
  type?: string
  top?: number
  skip?: number
}
```
**Response shape:**
```typescript
{
  items: Array<{
    id: number
    title: string
    status: 'Unassigned' | 'Pending' | 'Completed'
    type: string
    creationTime: string    // ISO
    lastModificationTime: string
  }>
  count: number
}
```
**Computable metrics:** Pending task count, unassigned task count, Action Center backlog
**Cannot compute:** SLA compliance, average resolution time
**Templates:** `sdk-kpi-card`
**Aliases:** "pending tasks", "action center backlog", "tasks waiting for review", "human tasks", "approval queue", "unassigned tasks"

---

## Standard Time Constants

Canonical definition — reference these, do not redefine them in other files.

```typescript
const NOW             = new Date().toISOString()
const ONE_DAY_AGO     = new Date(Date.now() -    86_400_000).toISOString()
const SEVEN_DAYS_AGO  = new Date(Date.now() -   604_800_000).toISOString()
const THIRTY_DAYS_AGO = new Date(Date.now() - 2_592_000_000).toISOString()
const NINETY_DAYS_AGO = new Date(Date.now() - 7_776_000_000).toISOString()
```

`build-dashboard.mjs` injects these after the last import line in every generated widget file.
Use the plain names (`SEVEN_DAYS_AGO`, `NOW`, etc.) in `dataHook` expressions — the script adds the declarations.

**Both `startTime` AND `endTime` are required for Insights calls.** Omitting `endTime` causes 500 errors.

---

## Widget Recipes

Pre-written `plan.json` widget configurations. Use these as-is for the most common requests.
For Insights RTM recipes, `dataHook` uses `useInsights<ResponseType>(key, params)`.
For SDK recipes, use AMBER path — write custom hook in `files{}` map using the capability entry above.

### ColumnDef format — never invent variations

`RecordsTable` uses `{ key, label, align? }` — NOT TanStack Table's `{ accessorKey, header }`:

```typescript
{ key: 'agentName', label: 'Agent' }
{ key: 'healthScore', label: 'Health Score', align: 'right' as const }
// align must be 'right' as const or 'left' as const — never numeric: true
```

### Insights RTM Recipes

**Recipe 1 — Agent Error Trend**
Triggers: "error rate", "errors over time", "error trend", "agent failures", "which agents are failing"
```json
{
  "template": "line-chart",
  "dataHook": "useInsights<{ data: Array<{ name: string; value: number; date: string }> }>('agents.getErrors', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data ?? []",
  "xKey": "date",
  "yKey": "value",
  "deltaDir": "down-good"
}
```

**Recipe 2 — Invocation / Activity Timeline**
Triggers: "invocation volume", "how busy", "activity over time", "run count"
```json
{
  "template": "area-chart",
  "dataHook": "useInsights<{ data: Array<{ timeSlice: string; aguConsumption: number }> }>('agents.getConsumptionTimeline', { startTime: ONE_DAY_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data ?? []",
  "xKey": "timeSlice",
  "yKey": "aguConsumption"
}
```

**Recipe 3 — Active Agents Count (KPI)**
Triggers: "active agents", "fleet size", "how many agents", "agent count"
```json
{
  "template": "kpi-card",
  "dataHook": "useInsights<{ data: { agents: Array<{ agentId: string }> } }>('agents.getAgents', { startTime: THIRTY_DAYS_AGO, endTime: NOW })",
  "valueExpression": "String((data as any)?.data?.agents?.length ?? '—')",
  "deltaDir": "neutral"
}
```

**Recipe 4 — Success Rate KPI**
Triggers: "success rate", "pass rate", "how well are agents doing"
```json
{
  "template": "kpi-card",
  "dataHook": "useInsights<{ data: { currentPeriodSummary: { successRate: number } } }>('agents.getSummaryV2', { startTime: THIRTY_DAYS_AGO, endTime: NOW })",
  "valueExpression": "(() => { const s = (data as any)?.data?.currentPeriodSummary; return s ? `${s.successRate.toFixed(1)}%` : '—' })()",
  "deltaDir": "up-good"
}
```

**Recipe 5 — Avg Duration KPI**
Triggers: "average duration", "how long do agents take", "avg execution time"
```json
{
  "template": "kpi-card",
  "dataHook": "useInsights<{ data: { currentPeriodSummary: { averageDurationSeconds: number } } }>('agents.getSummaryV2', { startTime: THIRTY_DAYS_AGO, endTime: NOW })",
  "valueExpression": "(() => { const secs = (data as any)?.data?.currentPeriodSummary?.averageDurationSeconds; return secs != null ? `${(secs / 60).toFixed(1)}m` : '—' })()",
  "deltaDir": "neutral"
}
```

**Recipe 6 — Top Erroring Agents (Bar)**
Triggers: "top erroring agents", "most failures", "error leaderboard"
```json
{
  "template": "bar-chart",
  "dataHook": "useInsights<{ totalErrors: number; data: Array<{ name: string; count: number }> }>('agents.getTopErroredAgents', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data ?? []",
  "xKey": "name",
  "yKey": "count"
}
```

**Recipe 7 — P95 Latency Trend**
Triggers: "latency", "response time", "P95", "how fast are agents"
```json
{
  "template": "line-chart",
  "dataHook": "useInsights<{ data: Array<{ name: 'P50' | 'P95'; value: number; date: string }> }>('agents.getLatencyTimeline', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data?.filter((d: { name: string }) => d.name === 'P95') ?? []",
  "xKey": "date",
  "yKey": "value"
}
```

**Recipe 8 — Incident Type Distribution (Donut)**
Triggers: "incident types", "error vs escalation", "incident breakdown"
```json
{
  "template": "donut-chart",
  "dataHook": "useInsights<{ data: { errorCount: number; escalationCount: number; policyCount: number } }>('agents.getIncidentDistribution', { startTime: THIRTY_DAYS_AGO, endTime: NOW })",
  "dataSelector": "[{ name: 'Errors', value: (data as any)?.data?.errorCount ?? 0 }, { name: 'Escalations', value: (data as any)?.data?.escalationCount ?? 0 }, { name: 'Policy', value: (data as any)?.data?.policyCount ?? 0 }].filter(d => d.value > 0)",
  "dataKey": "value",
  "nameKey": "name"
}
```

**Recipe 9 — Agent Fleet Table**
Triggers: "agent list", "fleet overview", "all agents", "health scores"
```json
{
  "template": "data-table",
  "dataHook": "useInsights<{ data: { agents: Array<{ agentName: string; healthScore: number; unitsQuantity: number; lastRun: string }> } }>('agents.getAgents', { startTime: THIRTY_DAYS_AGO, endTime: NOW })",
  "dataSelector": "[...((data as any)?.data?.agents ?? [])].sort((a, b) => b.unitsQuantity - a.unitsQuantity)",
  "columns": "[{ key: 'agentName', label: 'Agent' }, { key: 'healthScore', label: 'Health' }, { key: 'unitsQuantity', label: 'Units Used', align: 'right' as const }, { key: 'lastRun', label: 'Last Run' }]"
}
```

**Recipe 10 — Top Agents by Consumption (Bar)**
Triggers: "top consumers", "highest usage", "who uses the most AGU"
```json
{
  "template": "bar-chart",
  "dataHook": "useInsights<{ data: { agents: Array<{ agentName: string; consumedQuantity: number }> } }>('agents.getConsumption', { startTime: THIRTY_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data?.agents ?? []",
  "xKey": "agentName",
  "yKey": "consumedQuantity"
}
```

**Recipe 11 — Job Completion Timeline**
Triggers: "job trend", "completed jobs over time", "automation volume", "job history"
```json
{
  "template": "area-chart",
  "dataHook": "useInsights<{ data: Array<{ date: string; count: number; state: string }> }>('jobs.getCompletedTimeline', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data?.filter((d: { state: string }) => d.state === 'Successful') ?? []",
  "xKey": "date",
  "yKey": "count"
}
```

**Recipe 12 — Memory Usage Timeline (Traceview)**
Triggers: "memory usage", "agent memory", "in-memory traces", "context retention"
```json
{
  "template": "area-chart",
  "dataHook": "useInsights<{ data: Array<{ timeSlice: string; inMemoryCount: number; totalCount: number }> }>('traceview.getMemoryTimeline', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data ?? []",
  "xKey": "timeSlice",
  "yKey": "inMemoryCount"
}
```

**Recipe 13 — P50 + P95 Latency (Multi-Line)**
Triggers: "latency with P50 and P95", "compare P50 vs P95", "latency percentiles"
```json
{
  "template": "multi-line-chart",
  "dataHook": "useInsights<{ data: Array<{ name: 'P50' | 'P95'; value: number; date: string }> }>('agents.getLatencyTimeline', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(data as any)?.data ?? []",
  "xKey": "date",
  "pivotExpression": "rawData.reduce((acc: Record<string, unknown>[], row: { name: string; value: number; date: string }) => { const existing = acc.find(r => r.date === row.date) as Record<string, unknown> | undefined; if (existing) { existing[row.name] = row.value } else acc.push({ date: row.date, [row.name]: row.value }); return acc }, [])",
  "series": "[{ key: 'P50', color: 'hsl(var(--chart-1))' }, { key: 'P95', color: 'hsl(var(--chart-2))' }]"
}
```

**Recipe 14 — Agent Error Rate KPI with Sparkline**
Triggers: "agent error rate trend", "errors with trend", "error KPI with sparkline"
```json
{
  "template": "kpi-with-sparkline",
  "dataHook": "useInsights<{ data: Array<{ name: string; value: number; date: string }> }>('agents.getErrors', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "(() => { const byDate = ((data as any)?.data ?? []).reduce((acc: Record<string, number>, r: { date: string; value: number }) => { const day = r.date.slice(0, 10); acc[day] = (acc[day] ?? 0) + r.value; return acc }, {}); return Object.entries(byDate).sort(([a], [b]) => a.localeCompare(b)).map(([date, errors]) => ({ date, errors })) })()",
  "valueExpression": "(() => { const allRows = (data as any)?.data ?? []; const byDate = allRows.reduce((acc: Record<string, number>, r: { date: string; value: number }) => { const day = r.date.slice(0, 10); acc[day] = (acc[day] ?? 0) + r.value; return acc }, {}); const sorted = Object.entries(byDate).sort(([a], [b]) => a.localeCompare(b)); return sorted.length > 0 ? String(sorted[sorted.length - 1][1]) : '—' })()",
  "yKey": "errors",
  "deltaDir": "down-good"
}
```

**Recipe 15 — Top Agents Ranked Table**
Triggers: "top agents", "leaderboard", "agents ranked by errors"
```json
{
  "template": "ranked-table",
  "dataHook": "useInsights<{ data: Array<{ name: string; count: number }> }>('agents.getTopErroredAgents', { startTime: SEVEN_DAYS_AGO, endTime: NOW })",
  "dataSelector": "[...((data as any)?.data ?? [])].sort((a, b) => b.count - a.count)",
  "columns": "[{ key: 'name', label: 'Agent' }, { key: 'count', label: 'Errors', align: 'right' as const }]"
}
```

**Recipe 16 — Incident Type Progress Bars**
Triggers: "incident breakdown", "error vs escalation as bars", "incident proportions"
```json
{
  "template": "progress-bar-list",
  "dataHook": "useInsights<{ data: { errorCount: number; escalationCount: number; policyCount: number } }>('agents.getIncidentDistribution', { startTime: THIRTY_DAYS_AGO, endTime: NOW })",
  "dataSelector": "[{ label: 'Errors', value: (data as any)?.data?.errorCount ?? 0 }, { label: 'Escalations', value: (data as any)?.data?.escalationCount ?? 0 }, { label: 'Policy', value: (data as any)?.data?.policyCount ?? 0 }].filter(d => d.value > 0)"
}
```

### SDK Recipes (AMBER path — use `files{}` map, not `widgets[]`)

For SDK widgets, write a custom TypeScript hook in the `files{}` map using the SDK capability entry
above. Do NOT use `useInsights`. Use `const { sdk, isAuthenticated } = useAuth()` and
`new ServiceClass(sdk as never).method(params)`.

**SDK Recipe A — Running Jobs Count**
Triggers: "running jobs", "active jobs", "jobs in progress", "how many jobs are running"
```tsx
// Write to files['src/dashboard/widgets/RunningJobs.tsx']:
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Activity } from 'lucide-react'
import { Jobs } from '@uipath/uipath-typescript/jobs'
import { useAuth } from '@/hooks/useAuth'
import { DeltaBadge, ViewAllLink, LoadingState } from '@/dashboard/chrome'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

export function RunningJobs() {
  const navigate = useNavigate()
  const { sdk, isAuthenticated } = useAuth()
  const [count, setCount] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  useEffect(() => {
    if (!isAuthenticated) return
    let cancelled = false
    const svc = new Jobs(sdk as never)
    svc.getAll({ state: 'Running,Pending' })
      .then((r: { items?: Array<{ state: string }> }) => { if (!cancelled) setCount(r.items?.length ?? 0) })
      .catch((e: unknown) => { if (!cancelled) setError(e instanceof Error ? e : new Error(String(e))) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [sdk, isAuthenticated])
  if (loading) return <LoadingState height="h-32" />
  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate('/running-jobs')}>
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-muted p-2"><Activity className="w-4 h-4 text-muted-foreground" /></div>
          <div><CardTitle className="text-base">Running Jobs</CardTitle><CardDescription>Active and pending jobs right now</CardDescription></div>
        </div>
        <ViewAllLink to="/running-jobs" />
      </CardHeader>
      <div className="px-6 pb-4 flex items-baseline gap-3">
        <span className="text-3xl font-semibold tabular-nums">{error ? '—' : String(count ?? '—')}</span>
        <DeltaBadge direction="neutral" text="" />
      </div>
    </Card>
  )
}
```

**SDK Recipe B — Queue Depth**
Triggers: "queue depth", "active queue items", "queued transactions"
Use same pattern as Recipe A but with `new QueueItems(sdk as never).getAll({ status: 'New,InProgress' })`.

**SDK Recipe C — Pending Action Center Tasks**
Triggers: "pending tasks", "action center backlog", "human tasks"
Use same pattern as Recipe A but with `new Tasks(sdk as never).getAll({ status: 'Pending,Unassigned' })`.

**SDK Recipe D — Process Inventory Table**
Triggers: "what processes are deployed", "automation inventory", "process list"
Use `sdk-data-table` template with:
- `sdkImport: "@uipath/uipath-typescript/processes"`
- `sdkService: "Processes"`
- `sdkCall: "getAll()"`
- `sdkResultType: "{ items?: Array<{ name: string; description: string; version: string }> }"`
- `dataSelector: "(r as any)?.items ?? []"`
- `columns: "[{ key: 'name', label: 'Process' }, { key: 'description', label: 'Description' }, { key: 'version', label: 'Version' }]"`

---

## Tie-Breaking Rules

- "job count today" → SDK `Jobs.getAll`; "job count over 7 days" → `jobs.getCompletedTimeline`
- "queue depth" → SDK `QueueItems.getAll`; "queue throughput trend" → no endpoint, stay SDK with disclaimer
- P50/P95 latency → `agents.getLatencyTimeline` (fleet) or `traceview.getLatencyTimeline` (trace-level)
- `governance.getPolicySummary` requires `policy` (UUID) extra body field — confirm with user
- "invocation volume" → `agents.getConsumptionTimeline` (activity proxy — say so in plan)
- `getSummaryV2` is AGGREGATE ONLY — never use for line/area/bar time-series charts
- "real-time" → SDK operational state; "over time" / "trend" → Insights RTM analytics
```

- [ ] **Step 2: Verify the file was created and is non-empty**

```bash
wc -c skills/uipath-coded-apps/references/dashboards/sdk-capabilities.md
```
Expected: output shows a size > 10000 bytes.

- [ ] **Step 3: Check all section headers are present**

```bash
grep "^### " skills/uipath-coded-apps/references/dashboards/sdk-capabilities.md | wc -l
```
Expected: output shows at least 20 (one per capability entry).

- [ ] **Step 4: Commit**

```bash
git add skills/uipath-coded-apps/references/dashboards/sdk-capabilities.md
git commit -m "feat(coded-apps): add SDK capability registry replacing insights-catalog + data-router"
```

---

## Task 2: Update `CAPABILITY.md` — early incremental check and reference cleanup

**Files:**
- Modify: `skills/uipath-coded-apps/references/dashboards/CAPABILITY.md`

- [ ] **Step 1: Rewrite `CAPABILITY.md` with incremental check and updated references**

Replace the entire file content:

```markdown
---
name: uipath-coded-apps/dashboards
---

# Dashboard Capability

## When to Use This Capability
- User wants a dashboard, analytics view, KPI summary, or metric report
- NLP prompt describes data to visualize ("agent success rates", "queue SLA", "governance violations")
- Iterating on an existing dashboard (adding widgets, changing chart types)

## First: Check for Existing Dashboard

Before loading any plugin, run:

```bash
ls .dashboard/state.json 2>/dev/null && echo "INCREMENTAL" || echo "FRESH"
```

- **INCREMENTAL** → Load `plugins/build/impl.md` Phase 0 path, or read `primitives/incremental-editor.md` directly for widget edits
- **FRESH** → Continue to Plugin Router below

## Critical Rules
1. Read `primitives/auth-context.md` BEFORE any SDK or Insights API call
2. ALWAYS derive a plain-language plan before writing code — read `primitives/build-plan.md`
3. HALT at the approval gate — do not scaffold until user confirms the plan
4. Run Phase 3a feasibility gate — never plan a widget before checking `sdk-capabilities.md`
5. NEVER hardcode tenant IDs, org names, or folder paths in generated code
6. NEVER auto-deploy — deploy pipeline always requires explicit user confirmation
7. All tokens flow through `useAuth()` — never store tokens in state, localStorage, or env vars at runtime
8. Run `tsc --noEmit` before claiming success
9. Every list call paginates — ≤50 rows per page, never load all

## Plugin Router

| I want to...                                  | Read                                           |
|-----------------------------------------------|------------------------------------------------|
| Create or edit a dashboard                    | [plugins/build/impl.md](plugins/build/impl.md) |
| Deploy a built dashboard to Automation Cloud  | [plugins/deploy/impl.md](plugins/deploy/impl.md) |

## Reference Files
- [primitives/auth-context.md](primitives/auth-context.md) — auth session resolution
- [primitives/build-plan.md](primitives/build-plan.md) — plan generation + approval gate
- [primitives/state-file.md](primitives/state-file.md) — per-project state.json schema
- [primitives/incremental-editor.md](primitives/incremental-editor.md) — editing existing dashboards
- [sdk-capabilities.md](sdk-capabilities.md) — full capability registry (Insights RTM + Orchestrator SDK)
- [aesthetic/layout-patterns.md](aesthetic/layout-patterns.md) — layout rules
- [aesthetic/charting.md](aesthetic/charting.md) — chart type selection, colors, delta direction
```

- [ ] **Step 2: Verify no references to `data-router.md` or `insights-catalog.md` remain**

```bash
grep -n "data-router\|insights-catalog" skills/uipath-coded-apps/references/dashboards/CAPABILITY.md
```
Expected: no output (no matches).

- [ ] **Step 3: Commit**

```bash
git add skills/uipath-coded-apps/references/dashboards/CAPABILITY.md
git commit -m "feat(coded-apps): add early incremental check to CAPABILITY.md, update to sdk-capabilities"
```

---

## Task 3: Phase 3a feasibility gate in `build/impl.md`

**Files:**
- Modify: `skills/uipath-coded-apps/references/dashboards/plugins/build/impl.md`

- [ ] **Step 1: Replace Phase 3 with Phase 3a + 3b**

Find the current Phase 3 section in `build/impl.md`:
```
## Phase 3 — Metric Derivation (0 tool calls, in-context)

Apply four-axis decomposition from build-plan.md. Route via data-router.md.
Use Widget Recipes from insights-catalog.md (already loaded).
```

Replace it with:

```markdown
## Phase 3a — Feasibility Gate (0 tool calls, in-context)

> **MUST run before Phase 3b.** If Phase 3b derives configuration for a metric before Phase 3a
> classifies it, the feasibility gate has been bypassed. Stop and classify first.

For each metric in the user's NLP request:

**Step 1 — Check the Hard Refuse Table** (`sdk-capabilities.md` top section).
If the metric matches a row: it is RED. Note the reason and suggested alternative.

**Step 2 — Search registry aliases.**
Scan each capability entry's **Aliases** field. Match the user's phrasing against them.
- Match found + template listed → **GREEN** (template substitution via `widgets[]`)
- Match found + no template → **AMBER** (agent writes typed SDK hook in `files{}` map)
- No match → **RED** (hard refuse)

**Refuse output (inline with the plan, not a separate step):**
```
⚠ "[Requested metric]" isn't available — [reason from Hard Refuse Table or "no matching API"].
[If alternative exists: I can show [alternative] instead — want that?]
[If no alternative: I've excluded it from the plan.]
```

RED metrics are excluded from the plan. Never silently drop — always surface with reason.

AMBER metrics appear in the plan with a disclosure note:
```
• **[Widget Title]** — I'll write a custom data hook for this using the [ServiceName] SDK service.
```

---

## Phase 3b — Widget Configuration Derivation (0 tool calls, in-context)

For GREEN and AMBER metrics only (RED metrics do not reach this phase).

Use four-axis decomposition from `build-plan.md`:
- **Shape**: `line | bar | area | donut | kpi | table`
- **Time frame**: `realtime | hourly | daily | weekly | monthly`
- **Aggregation**: `count | sum | avg | p50 | p95`
- **Service**: Insights RTM or SDK (already determined in Phase 3a)

Use Widget Recipes from `sdk-capabilities.md` (already loaded in Phase 1 block).
Use response shapes from capability entries — never guess field names.

For AMBER metrics: write the custom hook in the `files{}` map using the exact method signature
and response shape from the capability entry. TypeScript must compile (`tsc --noEmit` in Phase 6).
```

- [ ] **Step 2: Update Phase 1 boot block to reference `sdk-capabilities.md` instead of `insights-catalog.md` and `data-router.md`**

Find the Phase 1 section that lists 4 reads. It currently reads:
```
☐ 1. `../../primitives/auth-context.md`  
☐ 2. `../../primitives/build-plan.md`  
☐ 3. `../../primitives/data-router.md`  
☐ 4. `../../insights-catalog.md`
```

Replace with:
```
☐ 1. `../../primitives/auth-context.md`  
☐ 2. `../../primitives/build-plan.md`  
☐ 3. `../../sdk-capabilities.md`  
☐ 4. `../../aesthetic/layout-patterns.md`
```

- [ ] **Step 3: Update Allowed template values in Phase 6**

Find this line in Phase 6:
```
`line-chart` · `area-chart` · `bar-chart` · `donut-chart` · `kpi-card` ·
`kpi-with-sparkline` · `data-table` · `ranked-table` · `progress-bar-list` · `multi-line-chart`
```

Replace with:
```
`line-chart` · `area-chart` · `bar-chart` · `donut-chart` · `kpi-card` ·
`kpi-with-sparkline` · `data-table` · `ranked-table` · `progress-bar-list` · `multi-line-chart` ·
`sdk-kpi-card` · `sdk-data-table` · `sdk-bar-chart` · `sdk-ranked-table`
```

- [ ] **Step 4: Verify no remaining references to `data-router.md` or `insights-catalog.md`**

```bash
grep -n "data-router\|insights-catalog" skills/uipath-coded-apps/references/dashboards/plugins/build/impl.md
```
Expected: no output.

- [ ] **Step 5: Commit**

```bash
git add skills/uipath-coded-apps/references/dashboards/plugins/build/impl.md
git commit -m "feat(coded-apps): add Phase 3a feasibility gate, update boot reads to sdk-capabilities"
```

---

## Task 4: Update `build-plan.md`

**Files:**
- Modify: `skills/uipath-coded-apps/references/dashboards/primitives/build-plan.md`

- [ ] **Step 1: Replace the Standard Time Constants section with a reference to sdk-capabilities.md**

Find this block in `build-plan.md`:
```markdown
## Standard Time Constants
**Both `startTime` AND `endTime` are required for all Insights API calls — omitting `endTime` causes 500 errors.**

Use these constants — do not compute date arithmetic inline:
```typescript
const NOW             = new Date().toISOString()                            // always required as endTime
const ONE_DAY_AGO     = new Date(Date.now() -    86_400_000).toISOString() // 24 hours
const SEVEN_DAYS_AGO  = new Date(Date.now() -   604_800_000).toISOString() // 7 days
const THIRTY_DAYS_AGO = new Date(Date.now() - 2_592_000_000).toISOString() // 30 days
const NINETY_DAYS_AGO = new Date(Date.now() - 7_776_000_000).toISOString() // 90 days
```

Every `useInsights` call must pass both:
```typescript
useInsights('agents.getErrors', { startTime: SEVEN_DAYS_AGO, endTime: NOW })
```

In the plan, map time frames to natural language: ONE_DAY_AGO → "today" or "24h",
SEVEN_DAYS_AGO → "last 7 days", THIRTY_DAYS_AGO → "last 30 days".
```

Replace with:
```markdown
## Standard Time Constants

See canonical definitions in `sdk-capabilities.md` (Standard Time Constants section).

`build-dashboard.mjs` injects these automatically into every generated widget file.
Use `SEVEN_DAYS_AGO`, `NOW`, etc. directly in `dataHook` expressions without re-declaring them.

**Both `startTime` AND `endTime` are required for all Insights calls.** Omitting `endTime` causes 500 errors.

In the plan, map time frames to natural language: `ONE_DAY_AGO` → "today/24h",
`SEVEN_DAYS_AGO` → "last 7 days", `THIRTY_DAYS_AGO` → "last 30 days".
```

- [ ] **Step 2: Clarify the approval gate to require both plan approval and client ID answer**

Find the Approval Gate Rules section. Add this rule after the existing rules:

```markdown
- **Client ID question must be answered before Phase 6.** If the user approves the widget list
  but doesn't answer the client ID question, re-ask specifically:
  "One more thing — do you have an existing non-confidential external app Client ID, or should I create one?"
  Do not proceed to Phase 6 until both the plan and client ID question are answered.
```

- [ ] **Step 3: Verify time constants block is replaced (not present twice)**

```bash
grep -c "ONE_DAY_AGO.*86_400_000" skills/uipath-coded-apps/references/dashboards/primitives/build-plan.md
```
Expected: `0` (the verbatim constant definition is gone).

- [ ] **Step 4: Commit**

```bash
git add skills/uipath-coded-apps/references/dashboards/primitives/build-plan.md
git commit -m "feat(coded-apps): deduplicate time constants, clarify approval gate client ID requirement"
```

---

## Task 5: Fix scaffold code — `useInsights.ts` and `insights-client.ts`

**Files:**
- Modify: `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/hooks/useInsights.ts`
- Modify: `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/lib/insights-client.ts`

- [ ] **Step 1: Fix `useInsights.ts` — default dependency array**

The current `useEffect` uses `deps` (default `[]`), so the hook never re-fetches when `key` or `params` change. Replace the `useEffect` closing line:

Find:
```typescript
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
```

Replace with:
```typescript
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps.length > 0 ? deps : [key, JSON.stringify(params), tenantId])
```

This means: if the caller passes explicit deps, use those (existing behavior for overrides); otherwise default to re-fetching when the endpoint key, params, or tenantId change.

- [ ] **Step 2: Fix `insights-client.ts` — error distinction**

Find the `post` method's error handling:
```typescript
    if (res.status === 401) throw new Error('INSIGHTS_AUTH_EXPIRED')
    if (!res.ok) throw new Error(`Insights ${res.status}: ${path}`)
    return res.json() as Promise<T>
```

Replace with:
```typescript
    if (res.status === 401) throw new Error('Insights auth expired — sign out and sign in again')
    if (res.status === 403) throw new Error('Insights access denied — check tenant permissions')
    if (!res.ok) {
      let body = ''
      try { body = await res.text() } catch { /* ignore */ }
      throw new Error(`Insights ${res.status} error${body ? `: ${body.slice(0, 120)}` : ''}`)
    }
    return res.json() as Promise<T>
```

Also wrap the fetch call itself to distinguish CORS/network failures:
Find:
```typescript
  private async post<T>(base: string, path: string, body: InsightsParams): Promise<T> {
    const token = await this.getToken()
    const res = await fetch(`${base}/${path}`, {
```

Replace with:
```typescript
  private async post<T>(base: string, path: string, body: InsightsParams): Promise<T> {
    const token = await this.getToken()
    let res: Response
    try {
      res = await fetch(`${base}/${path}`, {
```

And after the closing brace of the fetch options add:
```typescript
      })
    } catch {
      throw new Error('Cannot reach Insights API — check network connection or CORS configuration')
    }
```

- [ ] **Step 3: Verify TypeScript compiles in scaffold**

```bash
cd skills/uipath-coded-apps/assets/templates/dashboard/scaffold && npx tsc --noEmit 2>&1 | head -20
```
Expected: no output (clean compile) or only pre-existing errors unrelated to these files.

- [ ] **Step 4: Commit**

```bash
cd C:\Work\skills
git add skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/hooks/useInsights.ts
git add skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/lib/insights-client.ts
git commit -m "fix(coded-apps): useInsights default deps, insights-client error distinction"
```

---

## Task 6: Create SDK widget templates

**Files:**
- Create: `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-kpi-card.tsx`
- Create: `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-data-table.tsx`
- Create: `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-bar-chart.tsx`
- Create: `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-ranked-table.tsx`

**Placeholder conventions for SDK templates (new fields not in Insights templates):**
- `<SDK_IMPORT>` — npm subpath, e.g. `@uipath/uipath-typescript/jobs`
- `<SDK_SERVICE>` — class name, e.g. `Jobs`
- `<SDK_CALL>` — method call expression returning a Promise, e.g. `getAll({ state: 'Running,Pending' })`
- `<SDK_RESULT_TYPE>` — TypeScript type literal for the response, e.g. `{ items?: Array<{ state: string }> }`

The existing placeholders (`<COMPONENT_NAME>`, `<ICON>`, `<TITLE>`, `<DESCRIPTION>`, `<DETAIL_ROUTE>`, `<DELTA_DIR>`, `<DELTA_TEXT>`, `<COLUMNS>`, `<DATA_SELECTOR>`, `<X_KEY>`, `<Y_KEY>`) work the same as in Insights templates.

- [ ] **Step 1: Create `sdk-kpi-card.tsx`**

Write this file to `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-kpi-card.tsx`:

```tsx
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { <ICON> } from 'lucide-react'
import { <SDK_SERVICE> } from '<SDK_IMPORT>'
import { useAuth } from '@/hooks/useAuth'
import { DeltaBadge, ViewAllLink, LoadingState } from '@/dashboard/chrome'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

export function <COMPONENT_NAME>() {
  const navigate = useNavigate()
  const { sdk, isAuthenticated } = useAuth()
  const [value, setValue] = useState<string>('—')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!isAuthenticated) return
    let cancelled = false
    setLoading(true)
    const svc = new <SDK_SERVICE>(sdk as never)
    svc.<SDK_CALL>
      .then((r: <SDK_RESULT_TYPE>) => { if (!cancelled) setValue(<VALUE_EXPRESSION>) })
      .catch((e: unknown) => { if (!cancelled) setError(e instanceof Error ? e : new Error(String(e))) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [sdk, isAuthenticated])

  if (loading) return <LoadingState height="h-32" />

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={() => navigate('<DETAIL_ROUTE>')}
    >
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-muted p-2">
            <<ICON> className="w-4 h-4 text-muted-foreground" />
          </div>
          <div>
            <CardTitle className="text-base"><TITLE></CardTitle>
            <CardDescription><DESCRIPTION></CardDescription>
          </div>
        </div>
        <ViewAllLink to="<DETAIL_ROUTE>" />
      </CardHeader>
      <div className="px-6 pb-4 flex items-baseline gap-3">
        <span className="text-3xl font-semibold tabular-nums">{error ? '—' : value}</span>
        <DeltaBadge direction="<DELTA_DIR>" text="<DELTA_TEXT>" />
      </div>
    </Card>
  )
}
```

- [ ] **Step 2: Create `sdk-data-table.tsx`**

Write this file to `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-data-table.tsx`:

```tsx
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { <ICON> } from 'lucide-react'
import { <SDK_SERVICE> } from '<SDK_IMPORT>'
import { useAuth } from '@/hooks/useAuth'
import { ViewAllLink, LoadingState, EmptyState } from '@/dashboard/chrome'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

const COLUMNS: { key: string; label: string; align?: 'left' | 'right' }[] = <COLUMNS>
const PAGE_SIZE = 10

export function <COMPONENT_NAME>() {
  const [page, setPage] = useState(0)
  const navigate = useNavigate()
  const { sdk, isAuthenticated } = useAuth()
  const [result, setResult] = useState<<SDK_RESULT_TYPE> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!isAuthenticated) return
    let cancelled = false
    setLoading(true)
    const svc = new <SDK_SERVICE>(sdk as never)
    svc.<SDK_CALL>
      .then((r: <SDK_RESULT_TYPE>) => { if (!cancelled) setResult(r) })
      .catch((e: unknown) => { if (!cancelled) setError(e instanceof Error ? e : new Error(String(e))) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [sdk, isAuthenticated])

  if (loading) return <LoadingState height="h-48" />
  if (error) return <EmptyState message={error.message} />

  const rows: Record<string, unknown>[] = <DATA_SELECTOR>
  const totalPages = Math.ceil(rows.length / PAGE_SIZE)
  const pageRows = rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <Card className="col-span-full">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-muted p-2"><<ICON> className="w-4 h-4 text-muted-foreground" /></div>
          <div>
            <CardTitle className="text-base"><TITLE></CardTitle>
            <CardDescription><DESCRIPTION></CardDescription>
          </div>
        </div>
        <ViewAllLink to="<DETAIL_ROUTE>" />
      </CardHeader>
      <CardContent className="pt-0 px-0">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/50">
            <tr>{COLUMNS.map(c => <th key={c.key} className="px-4 py-2 text-left font-medium text-muted-foreground whitespace-nowrap">{c.label}</th>)}</tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr key={i} className="border-b last:border-0 hover:bg-muted/30 cursor-pointer transition-colors" onClick={() => navigate('<DETAIL_ROUTE>')}>
                {COLUMNS.map(c => <td key={c.key} className="px-4 py-2 max-w-xs truncate">{String(row[c.key] ?? '—')}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-2 border-t text-xs text-muted-foreground">
            <span>Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, rows.length)} of {rows.length}</span>
            <div className="flex gap-2">
              <button disabled={page === 0} onClick={e => { e.stopPropagation(); setPage(p => p - 1) }} className="px-2 py-1 rounded border disabled:opacity-40 hover:bg-muted transition-colors">Prev</button>
              <button disabled={page >= totalPages - 1} onClick={e => { e.stopPropagation(); setPage(p => p + 1) }} className="px-2 py-1 rounded border disabled:opacity-40 hover:bg-muted transition-colors">Next</button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 3: Create `sdk-bar-chart.tsx`**

Write this file to `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-bar-chart.tsx`:

```tsx
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { <ICON> } from 'lucide-react'
import { <SDK_SERVICE> } from '<SDK_IMPORT>'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts'
import { useAuth } from '@/hooks/useAuth'
import { ViewAllLink, LoadingState, EmptyState } from '@/dashboard/chrome'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

export function <COMPONENT_NAME>() {
  const navigate = useNavigate()
  const { sdk, isAuthenticated } = useAuth()
  const [result, setResult] = useState<<SDK_RESULT_TYPE> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!isAuthenticated) return
    let cancelled = false
    setLoading(true)
    const svc = new <SDK_SERVICE>(sdk as never)
    svc.<SDK_CALL>
      .then((r: <SDK_RESULT_TYPE>) => { if (!cancelled) setResult(r) })
      .catch((e: unknown) => { if (!cancelled) setError(e instanceof Error ? e : new Error(String(e))) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [sdk, isAuthenticated])

  if (loading) return <LoadingState height="h-48" />
  if (error) return <EmptyState message={error.message} />

  const chartData: Record<string, unknown>[] = <DATA_SELECTOR>

  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate('<DETAIL_ROUTE>')}>
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-muted p-2"><<ICON> className="w-4 h-4 text-muted-foreground" /></div>
          <div>
            <CardTitle className="text-base"><TITLE></CardTitle>
            <CardDescription><DESCRIPTION></CardDescription>
          </div>
        </div>
        <ViewAllLink to="<DETAIL_ROUTE>" />
      </CardHeader>
      <CardContent className="pt-2">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={chartData} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
            <XAxis dataKey="<X_KEY>" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
            <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{ fontSize: 12, border: 'none', background: 'hsl(var(--card))', borderRadius: 6, boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
              cursor={{ fill: 'hsl(var(--muted))' }}
            />
            <Bar dataKey="<Y_KEY>" radius={[4, 4, 0, 0]}>
              {chartData.map((_, i) => (
                <Cell key={i} fill={`hsl(var(--chart-${(i % 5) + 1}))`} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 4: Create `sdk-ranked-table.tsx`**

Write this file to `skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-ranked-table.tsx`:

```tsx
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { <ICON> } from 'lucide-react'
import { <SDK_SERVICE> } from '<SDK_IMPORT>'
import { useAuth } from '@/hooks/useAuth'
import { ViewAllLink, LoadingState, EmptyState } from '@/dashboard/chrome'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'

const COLUMNS: { key: string; label: string; align?: 'left' | 'right' }[] = <COLUMNS>
const MAX_ROWS = 10

export function <COMPONENT_NAME>() {
  const navigate = useNavigate()
  const { sdk, isAuthenticated } = useAuth()
  const [result, setResult] = useState<<SDK_RESULT_TYPE> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!isAuthenticated) return
    let cancelled = false
    setLoading(true)
    const svc = new <SDK_SERVICE>(sdk as never)
    svc.<SDK_CALL>
      .then((r: <SDK_RESULT_TYPE>) => { if (!cancelled) setResult(r) })
      .catch((e: unknown) => { if (!cancelled) setError(e instanceof Error ? e : new Error(String(e))) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [sdk, isAuthenticated])

  if (loading) return <LoadingState height="h-48" />
  if (error) return <EmptyState message={error.message} />

  const rows: Record<string, unknown>[] = (<DATA_SELECTOR>).slice(0, MAX_ROWS)

  return (
    <Card className="col-span-full">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="flex items-start gap-3">
          <div className="rounded-md bg-muted p-2"><<ICON> className="w-4 h-4 text-muted-foreground" /></div>
          <div>
            <CardTitle className="text-base"><TITLE></CardTitle>
            <CardDescription><DESCRIPTION></CardDescription>
          </div>
        </div>
        <ViewAllLink to="<DETAIL_ROUTE>" />
      </CardHeader>
      <CardContent className="pt-0 px-0">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/50">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-muted-foreground w-8">#</th>
              {COLUMNS.map(c => (
                <th key={c.key} className={`px-4 py-2 font-medium text-muted-foreground whitespace-nowrap ${c.align === 'right' ? 'text-right' : 'text-left'}`}>
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className="border-b last:border-0 hover:bg-muted/30 cursor-pointer transition-colors" onClick={() => navigate('<DETAIL_ROUTE>')}>
                <td className="px-4 py-2 text-muted-foreground text-xs">{i + 1}</td>
                {COLUMNS.map(c => (
                  <td key={c.key} className={`px-4 py-2 max-w-xs truncate ${c.align === 'right' ? 'text-right tabular-nums' : ''}`}>
                    {String(row[c.key] ?? '—')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 5: Verify all four template files exist**

```bash
ls skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-*.tsx
```
Expected: four files listed: `sdk-bar-chart.tsx`, `sdk-data-table.tsx`, `sdk-kpi-card.tsx`, `sdk-ranked-table.tsx`

- [ ] **Step 6: Commit**

```bash
git add skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-kpi-card.tsx
git add skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-data-table.tsx
git add skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-bar-chart.tsx
git add skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-ranked-table.tsx
git commit -m "feat(coded-apps): add sdk-kpi-card, sdk-data-table, sdk-bar-chart, sdk-ranked-table templates"
```

---

## Task 7: Update `build-dashboard.mjs` — SDK placeholder fields

**Files:**
- Modify: `skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs`

- [ ] **Step 1: Add SDK placeholder fields to the `subs` object**

Find the `subs` object in `build-dashboard.mjs` (around line 245–265). It currently ends with:
```javascript
    PIVOT_EXPRESSION: widget.pivotExpression ?? 'rawData',
  };
```

Add four new entries before the closing `};`:
```javascript
    PIVOT_EXPRESSION:   widget.pivotExpression  ?? 'rawData',
    SDK_IMPORT:         widget.sdkImport        ?? '',
    SDK_SERVICE:        widget.sdkService       ?? '',
    SDK_CALL:           widget.sdkCall          ?? '',
    SDK_RESULT_TYPE:    widget.sdkResultType    ?? '{ items?: Array<Record<string, unknown>> }',
  };
```

- [ ] **Step 2: Update the PLAN JSON SCHEMA comment to document SDK fields**

Find the `widgets` field documentation near the bottom of the file (the `PLAN JSON SCHEMA` comment). It lists fields like `"componentName"`, `"template"`, `"dataHook"`, etc.

Add these entries after `"pivotExpression"`:
```javascript
 *       "sdkImport":     string   — (sdk-* templates) npm subpath, e.g. "@uipath/uipath-typescript/jobs"
 *       "sdkService":    string   — (sdk-* templates) class name, e.g. "Jobs"
 *       "sdkCall":       string   — (sdk-* templates) method call expr, e.g. "getAll({ state: 'Running' })"
 *       "sdkResultType": string   — (sdk-* templates) TS type literal for response, e.g. "{ items?: Array<{ state: string }> }"
```

- [ ] **Step 3: Verify the subs object now contains SDK_IMPORT**

```bash
grep "SDK_IMPORT" skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs
```
Expected: two lines (one in subs object, one in schema comment).

- [ ] **Step 4: Commit**

```bash
git add skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs
git commit -m "feat(coded-apps): add SDK placeholder fields to build-dashboard.mjs substitution map"
```

---

## Task 8: Delete retired files and sweep remaining references

**Files:**
- Delete: `skills/uipath-coded-apps/references/dashboards/insights-catalog.md`
- Delete: `skills/uipath-coded-apps/references/dashboards/primitives/data-router.md`

- [ ] **Step 1: Search for all remaining references to the deleted files**

```bash
grep -rn "insights-catalog\|data-router" skills/uipath-coded-apps/
```

Note every match. Update each file to reference `sdk-capabilities.md` instead.

- [ ] **Step 2: Check `primitives/incremental-editor.md` for stale references**

```bash
grep -n "insights-catalog\|data-router\|data\.router\|catalog\.md" skills/uipath-coded-apps/references/dashboards/primitives/incremental-editor.md
```

If any matches: update to reference `sdk-capabilities.md`.

- [ ] **Step 3: Check `plugins/deploy/impl.md` for stale references**

```bash
grep -n "insights-catalog\|data-router" skills/uipath-coded-apps/references/dashboards/plugins/deploy/impl.md
```

If any matches: update accordingly.

- [ ] **Step 4: Delete the two retired files**

```bash
git rm skills/uipath-coded-apps/references/dashboards/insights-catalog.md
git rm skills/uipath-coded-apps/references/dashboards/primitives/data-router.md
```

- [ ] **Step 5: Final sweep — no remaining references to deleted files**

```bash
grep -rn "insights-catalog\|data-router" skills/uipath-coded-apps/
```
Expected: no output.

- [ ] **Step 6: Final sweep — no remaining time constant definitions except in sdk-capabilities.md**

```bash
grep -rn "ONE_DAY_AGO.*86_400_000" skills/uipath-coded-apps/references/
```
Expected: output contains only `sdk-capabilities.md` (the canonical definition).

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat(coded-apps): delete insights-catalog.md and data-router.md, sweep stale references"
```

---

## Verification Checklist

Run after all tasks complete:

- [ ] `grep -rn "insights-catalog\|data-router" skills/uipath-coded-apps/` → **zero results**
- [ ] `ls skills/uipath-coded-apps/assets/templates/dashboard/widgets/sdk-*.tsx` → **4 files**
- [ ] `grep "Phase 3a" skills/uipath-coded-apps/references/dashboards/plugins/build/impl.md` → **present**
- [ ] `grep "Hard Refuse Table" skills/uipath-coded-apps/references/dashboards/sdk-capabilities.md` → **present**
- [ ] `grep "SDK_IMPORT" skills/uipath-coded-apps/assets/scripts/build-dashboard.mjs` → **present**
- [ ] `grep "sdk-capabilities" skills/uipath-coded-apps/references/dashboards/CAPABILITY.md` → **present**
- [ ] `grep "ONE_DAY_AGO.*86_400_000" skills/uipath-coded-apps/references/dashboards/primitives/build-plan.md` → **zero results** (removed from build-plan.md)
