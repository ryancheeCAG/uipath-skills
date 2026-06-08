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
  → T3-SDK: agent writes fnBody
```

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

Use when the metric doesn't match T1 or T2. There is now one path: T3-SDK.

All Insights metrics that aren't in the T1 catalog should use T3-SDK with the Insights SDK service classes — the same pattern as all other SDK services.

### T3-SDK: agent writes an async function body

```json
{
  "name": "incident-distribution",
  "tier": "T3",
  "title": "Incident Distribution",
  "description": "Types of agent incidents",
  "displayAs": "ranked-table",
  "columns": "[{key:\"name\",label:\"Type\"},{key:\"count\",label:\"Count\",align:\"right\" as const}]",
  "fnBody": "const { Agents } = await import('@uipath/uipath-typescript/agents')\nconst svc = new Agents(sdk as never)\nconst result = await svc.getIncidentDistribution(THIRTY_DAYS_AGO, NOW)\nreturn result?.data ?? []"
}
```

`displayAs` must be one of: `kpi-card`, `ranked-table`, `data-table`.

For `kpi-card`, also provide `valueField` (which field to display) and optionally `valueLabel`:
```json
{
  "name": "total-active-agents",
  "tier": "T3",
  "title": "Total Active Agents",
  "displayAs": "kpi-card",
  "valueField": "count",
  "valueLabel": "active agents",
  "fnBody": "const { Agents } = await import('@uipath/uipath-typescript/agents')\nconst svc = new Agents(sdk as never)\nconst result = await svc.getAll(THIRTY_DAYS_AGO, NOW)\nreturn [{ count: result?.items?.length ?? 0 }]"
}
```

### fnBody rules
- Returns `Promise<Array<Record<string, unknown>>>`
- Use dynamic import: `const { ServiceClass } = await import('@uipath/uipath-typescript/...')`
- Use constructor injection: `new ServiceClass(sdk as never)`
- `sdk` and `getToken` are available as parameters — do not import `useAuth`
- No JSX, no static top-level imports
- Time constants available: `NOW`, `ONE_DAY_AGO`, `SEVEN_DAYS_AGO`, `THIRTY_DAYS_AGO`, `NINETY_DAYS_AGO`

### SDK service class reference

Use constructor injection in every fnBody. Never use dot-chain syntax.

```typescript
// Correct
const svc = new Jobs(sdk as never)
const results = await svc.getAll({})

// Wrong — sdk.jobs does not exist
const results = await sdk.jobs.getAll({})
```

| Service class | Import subpath | Key fields |
|--------------|----------------|------------|
| `Agents` | `@uipath/uipath-typescript/agents` | 14 Insights methods for agent metrics |
| `Governance` | `@uipath/uipath-typescript/governance` | `getPolicyTraces()`, `getOperationSummary()` |
| `Memory` | `@uipath/uipath-typescript/memory` | `getTimeline()`, `getCallsTimeline()`, `getTopSpaces()` |
| `Jobs` | `@uipath/uipath-typescript/jobs` | `key`, `state`, `processName`, `startTime`, `endTime` |
| `Queues` | `@uipath/uipath-typescript/queues` | `id`, `name`, `maxRetries`, `acceptsRejectedItems` |
| `Assets` | `@uipath/uipath-typescript/assets` | `id`, `name`, `hasValue`, `value` |
| `Tasks` | `@uipath/uipath-typescript/tasks` | `id`, `title`, `priority`, `status`, `assignedTo` |
| `Processes` | `@uipath/uipath-typescript/processes` | `id`, `name`, `key`, `processType` |
| `Entities` | `@uipath/uipath-typescript/entities` | `id`, `name`, `displayName`, `entityType` |
| `Cases` | `@uipath/uipath-typescript/cases` | `processKey`, `runningCount`, `completedCount` |

**Insights methods take positional Date params** (not options object):
```typescript
// Correct — startTime and endTime are positional Date arguments
new Agents(sdk as never).getErrorsTimeline(THIRTY_DAYS_AGO, NOW)

// Wrong — options style does not match SDK signature
new Agents(sdk as never).getErrors({ startTime: THIRTY_DAYS_AGO, endTime: NOW })
```

Time constants are `Date` objects: `NOW`, `ONE_DAY_AGO`, `SEVEN_DAYS_AGO`, `THIRTY_DAYS_AGO`, `NINETY_DAYS_AGO`.

Note: `getAll()` on non-Insights services returns paginated or non-paginated response. Access items via `result?.items ?? result?.value ?? []`.

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
| Governance policy summary | Requires a specific policy UUID the build script cannot infer | Ask user for the UUID, then use T3-SDK with `Governance` from `@uipath/uipath-typescript/governance` |

## SDK usage patterns

Patterns specific to how the dashboard skill uses the SDK inside generated widget code.

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
