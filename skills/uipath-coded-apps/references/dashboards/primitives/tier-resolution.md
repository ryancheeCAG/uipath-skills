# Tier Resolution — Classifying Metrics

Every metric in `intent.json` has a `tier` field you must set during Phase 3.

## Tier Decision Tree

```
User asks for metric
  ↓
T0 — Impossible check (FIRST — before anything else)
  → Does the metric match the Hard Refuse list?
    → YES: refuse only that metric, explain why, offer the closest alternative
           (other metrics in the request still build normally)
  ↓
T1 — Catalog check
  → Exact name or alias match in capability-registry.json t1?
    → YES: tier = "T1"
  ↓
T2 — Parametric check
  → Maps to a known SDK service + user-controlled filter parameter?
    → YES: tier = "T2", include compact params object
  ↓
T3 — Custom
  → tier = "T3"
  → Has Insights SDK service + method? → T3-Insights (namespace + method + template)
  → Else → T3-SDK (agent writes fnBody)
```

## T0 — Impossible (Hard Refuse)

## Tier 1 — Known catalog metrics

| Metric name | What it shows |
|-------------|--------------|
| `agent-errors` | Daily error counts as trend line |
| `invocation-volume` | AGU consumption over time as area chart (uses getConsumptionTimeline — xKey: timeSlice, yKey: aguConsumption) |
| `top-failing-agents` | Agents ranked by error count |
| `active-agents-kpi` | Count of agents with at least one run |
| `agent-latency` | P50/P95 latency over time |
| `job-failures` | Processes ranked by failure count |
| `job-completion-trend` | Completed jobs per day |

## Tier 2 — Parametric metrics

| Metric name | What it does | Required params |
|-------------|-------------|----------------|
| `jobs-duration-threshold` | Jobs running longer than threshold (minutes) | `{ threshold: number, direction: "gt" }` |
| `jobs-by-state` | Jobs filtered by execution state | `{ value: "Faulted" \| "Running" \| "Stopped" \| "Successful" }` |
| `tasks-by-status` | Action Center tasks filtered by status | `{ value: "Pending" \| "Completed" \| "Unassigned" }` |
| `cases-running-above` | Maestro processes where running case count exceeds threshold | `{ threshold: number, direction: "gt" }` |

T2 params format:
```json
// Numeric filter
{ "name": "jobs-duration-threshold", "tier": "T2", "params": { "threshold": 30, "direction": "gt" } }

// String equality filter
{ "name": "jobs-by-state", "tier": "T2", "params": { "value": "Faulted" } }
{ "name": "tasks-by-status", "tier": "T2", "params": { "value": "Pending" } }
```

## Tier 3 — Custom metrics

Use when the metric doesn't match T1 or T2. Two sub-paths:

### T3-Insights: custom Insights RTM endpoint

For Insights RTM endpoints **not in the T1 catalog but present in `InsightsClient`**. `InsightsKey` is a **closed type union** — only the exact methods listed below are valid. Guessing a method name will cause `Argument of type '"agents.getTopInvokedAgents"' is not assignable to parameter of type 'InsightsKey'`.

**Complete valid InsightsKey list (28 keys):**

| Namespace | Valid methods |
|-----------|--------------|
| `agents` | `getSummaryV2` `getErrors` `getTopErroredAgents` `getIncidents` `getIncidentDistribution` `getConsumption` `getConsumptionTimeline` `getLatencyTimeline` `getAgents` `getUnitConsumption` `getNames` |
| `traceview` | `getLatencyTimeline` `getErrorsTimeline` `getMemoryTimeline` `getMemoryCallsTimeline` `getTopMemorySpaces` `getUnitConsumption` |
| `governance` | `getPolicySummary` `getPolicyTraces` `getOperationSummary` |
| `jobs` | `getSummary` `getCompletedTimeline` `getUncompletedTimeline` `getTopFailures` `getFailuresByReason` `getProcessDetails` `getFailureDetails` |

The build script validates your `namespace.method` against this list at code-generation time and fails early with the valid options rather than at `tsc`.

Example:
```json
{
  "name": "incident-distribution",
  "tier": "T3",
  "title": "Incident Distribution",
  "namespace": "agents",
  "method": "getIncidentDistribution",
  "template": "donut-chart",
  "dataSelector": "(data as any)?.data ?? []",
  "xKey": "name",
  "yKey": "value",
  "description": "Incident types as a breakdown"
}
```

### T3-SDK: custom SDK query or custom HTTP call

Two use cases:

**1. TypeScript SDK service** — use constructor injection:
```json
{
  "name": "faulted-queues",
  "tier": "T3",
  "title": "Faulted Queue Items",
  "displayAs": "ranked-table",
  "columns": "[{key:\"name\",label:\"Queue\"},{key:\"count\",label:\"Faulted\",align:\"right\" as const}]",
  "fnBody": "const { Queues } = await import('@uipath/uipath-typescript/queues')\nconst svc = new Queues(sdk as never)\nconst r = await svc.getAll({ state: 'Faulted' })\nreturn (r?.items ?? []).map((q: any) => ({ name: q.name ?? '', count: q.transactionsCount ?? 0 }))"
}
```

**2. Insights endpoint NOT in InsightsKey** — use `getToken() + fetch()` directly. This is the same pattern `InsightsClient` uses internally:
```typescript
// fnBody for a custom Insights HTTP call
const token = await getToken()
const cloudUrl = import.meta.env.VITE_UIPATH_CLOUD_URL
const org      = import.meta.env.VITE_UIPATH_ORG_NAME
const tenant   = import.meta.env.VITE_UIPATH_TENANT_NAME
const tenantId = import.meta.env.VITE_INSIGHTS_TENANT_ID
const res = await fetch(
  `${cloudUrl}/${org}/${tenant}/insightsrtm_/Agents/topInvokedAgents`,
  {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ tenantId, startTime: THIRTY_DAYS_AGO, endTime: NOW }),
  }
)
if (!res.ok) throw new Error(`Insights ${res.status}`)
return (await res.json())?.data ?? []
```

Never use `(sdk as any)._config` or other internal SDK properties — `getToken()` is the documented way to get a bearer token.

T3-SDK rules for fnBody:
- Must return `Promise<Array<Record<string, unknown>>>`
- Use constructor injection: `new ServiceClass(sdk as never)` — never `sdk.serviceName.method()`
- **SDK service classes must use dynamic import inside fnBody** — static imports are not available in the generated file. The shell provides React, UI components, and `useAuth` only.
  ```typescript
  // Inside fnBody — dynamic import is valid in async functions
  const { Jobs } = await import('@uipath/uipath-typescript/jobs')
  const svc = new Jobs(sdk as never)
  const result = await svc.getAll({})
  ```
- Use `await` for all async operations
- No JSX, no static `import` statements at the top level of fnBody

### SDK service class reference

Use constructor injection in every fnBody. Never use dot-chain syntax.

```typescript
// Correct
const svc = new Jobs(sdk as never)
const results = await svc.getAll({})

// Wrong — sdk.jobs does not exist
const results = await sdk.jobs.getAll({})
```

| Service class | Import subpath | Key response fields |
|--------------|----------------|---------------------|
| `Jobs` | `@uipath/uipath-typescript/jobs` | `key`, `state`, `processName`, `startTime`, `endTime`, `createdTime` |
| `Queues` | `@uipath/uipath-typescript/queues` | `id`, `name`, `maxRetries`, `acceptsRejectedItems` |
| `Assets` | `@uipath/uipath-typescript/assets` | `id`, `name`, `hasValue`, `value` |
| `Tasks` | `@uipath/uipath-typescript/tasks` | `id`, `title`, `priority`, `status`, `assignedTo`, `createdTime` |
| `Processes` | `@uipath/uipath-typescript/processes` | `id`, `name`, `key`, `processType` |
| `Entities` | `@uipath/uipath-typescript/entities` | `id`, `name`, `displayName`, `entityType` |
| `Cases` | `@uipath/uipath-typescript/cases` | `processKey`, `runningCount`, `completedCount` |
| `MaestroProcesses` | `@uipath/uipath-typescript/maestro-processes` | varies |

Note: `getAll()` returns paginated or non-paginated response. Access items via `result?.items ?? result?.value ?? []`.

## T0 Hard Refuse List

**Refuse ONLY the specific metric — not the whole dashboard.** Offer to build the remaining metrics. Always provide the closest achievable alternative.

Checked before T1/T2/T3. If a metric matches any row below, it cannot be built in any tier — the data simply does not exist in the platform.

| User asks for | Reason | Suggest instead |
|--------------|--------|----------------|
| Agent cost in dollars | Platform tracks AGU, not currency | `invocation-volume` for AGU consumption |
| CPU/memory per agent | Not exposed by any API | `agent-latency` for fleet-level latency |
| Who triggered a job | Job records carry no end-user identity | `job-completion-trend` by process |
| Cross-tenant data | Single-tenant scope only | Multi-widget view within one tenant |
| SLA breach % | No SLA metadata in platform | Success rate from `job-completion-trend` |
| Error message text | No aggregation endpoint | `agent-errors` for counts |
| Governance policy summary | Requires a policy UUID the build script cannot infer | Ask user for the UUID, then use T3-Insights: `{ namespace: "governance", method: "getPolicySummary", ... }` with the UUID in the request |

## SDK usage patterns

The canonical SDK reference is fetched live in the parallel blast:
`https://uipath.github.io/uipath-typescript/llms-full-content.txt`

These patterns cover **only** what that document omits — patterns specific to how the dashboard skill uses the SDK inside generated widget code.

### Constructor injection — use `as never`, not bare `sdk`

The SDK docs show `new Jobs(sdk)` but the TypeScript types require a cast:

```typescript
// ✓ Correct — used in every T3-SDK fnBody and T2 compiled code
const svc = new Jobs(sdk as never)

// ✗ Wrong — type error at tsc
const svc = new Jobs(sdk)

// ✗ Wrong — sdk.jobs does not exist at runtime
sdk.jobs.getAll()
```

### Paginated response normalisation

SDK methods return either `PaginatedResponse<T>` or `NonPaginatedResponse<T>` depending on options passed. Always normalise:

```typescript
const items = result?.items ?? result?.value ?? []
```

- `PaginatedResponse<T>` → items are under `.items`
- `NonPaginatedResponse<T>` → items are under `.value`
- Either can be `undefined` if the call returns nothing

### Dynamic import inside T3-SDK fnBody

The generated widget file has no static SDK imports. Service classes must be loaded dynamically:

```typescript
// Inside fnBody — this is valid TypeScript in an async function
const { Jobs } = await import('@uipath/uipath-typescript/jobs')
const svc = new Jobs(sdk as never)
const result = await svc.getAll({})
const items = result?.items ?? result?.value ?? []
```

Static imports at the top of fnBody are not available — the shell template provides only React and dashboard chrome imports.

### Duration — not a direct field, compute it

`JobGetResponse` does not have a `duration` field. Compute from timestamps:

```typescript
const durationMs = new Date(j.endTime).getTime() - new Date(j.startTime).getTime()
const durationMins = Math.round(durationMs / 60_000)
```

### fnBody contract

Every T3-SDK `fnBody` must satisfy this interface:

```typescript
type DataFn = (
  sdk: UiPathClient,         // from useAuth().sdk
  getToken: () => Promise<string>  // from useAuth().getToken
) => Promise<Record<string, unknown>[]>
```

The function receives `sdk` and `getToken` as arguments — do not import `useAuth` inside fnBody.
