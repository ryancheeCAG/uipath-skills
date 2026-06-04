# Tier Resolution — Classifying Metrics

Every metric in `intent.json` has a `tier` field you must set during Phase 3.

## Tier Decision Tree

```
User asks for metric
  → Check hard-refuse list below
    → If match: refuse metric (not whole dashboard), offer alternative
  → Search T1 catalog: exact metric name or alias match?
    → YES: tier = "T1"
  → Search T2 catalog: maps to known SDK service + custom filter?
    → YES: tier = "T2", provide compact params object
  → Else: tier = "T3", write fnBody
```

## Tier 1 — Known catalog metrics

| Metric name | What it shows |
|-------------|--------------|
| `agent-errors` | Daily error counts as trend line |
| `invocation-volume` | Agent runs per day as area chart |
| `top-failing-agents` | Agents ranked by error count |
| `active-agents-kpi` | Count of agents with at least one run |
| `agent-latency` | P50/P95 latency over time |
| `job-failures` | Processes ranked by failure count |
| `job-completion-trend` | Completed jobs per day |
| `governance-policy-summary` | Total governance violations KPI |

## Tier 2 — Parametric metrics

| Metric name | What it does | Required params |
|-------------|-------------|----------------|
| `queue-failure-threshold` | Queues filtered by failureCount | `{ threshold: number, direction: "gt" }` |
| `jobs-duration-threshold` | Jobs filtered by duration | `{ threshold: number, direction: "gt" }` |

T2 params format:
```json
{ "name": "queue-failure-threshold", "tier": "T2", "params": { "threshold": 20, "direction": "gt" } }
```

## Tier 3 — Custom function body

Use when metric doesn't match T1 or T2. Write a typed async function body:

```typescript
const r = await sdk.queues.getAll({ state: 'Faulted' })
return r.items?.map(q => ({ name: q.name, count: q.pendingCount })) ?? []
```

Rules for T3 fnBody:
- Must return `Promise<Array<Record<string, unknown>>>`
- Use `sdk.*` for SDK calls — imports provided by shell template
- Use `await` for all async operations
- No `import` statements
- No JSX

T3 fields required in intent.json:
```json
{ "name": "my-metric", "tier": "T3", "title": "Human Title", "displayAs": "ranked-table", "fnBody": "..." }
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
