# Data Router — SDK vs Insights

Rule: SDK for operational state (current counts, list views, snapshots).
      Insights for analytics (historical trends, aggregations, percentiles, derived metrics).

## Routing Table

All Insights API calls are POST JSON with body `{ "tenantId": "<UUID>", "startTime": "...", ... }`.

| Intent signals                                           | Route    | Call                                                       |
|----------------------------------------------------------|----------|------------------------------------------------------------|
| job count, job status, running jobs, failed jobs         | SDK      | orchestrator/jobs → `Jobs.getAll()`                        |
| queue items, queue depth, transaction throughput         | SDK      | orchestrator/queues → `QueueItems.getAll()`                |
| process list, automation inventory                       | SDK      | orchestrator/processes → `Processes.getAll()`              |
| maestro instances, flow runs, active flows               | SDK      | maestro/processes → `ProcessInstances.getAll()`            |
| case status, case backlog                                | SDK      | maestro/cases → `CaseInstances.getAll()`                   |
| case SLA, SLA compliance                                 | SDK      | maestro/cases → `CaseInstances.getSlaSummary()`            |
| action center tasks, pending approvals                   | SDK      | action-center/tasks → `Tasks.getAll()`                     |
| DataFabric entity records                                | SDK      | data-fabric/entities → `Entities.getAll()`                 |
| agent success rate, failure rate, avg duration           | Insights | `agents.getSummaryV2` → POST `/Agents/summaryV2`           |
| agent error spikes, errors over time                     | Insights | `agents.getErrors` → POST `/Agents/errors`                 |
| top erroring agents, error leaderboard                   | Insights | `agents.getTopErroredAgents` → POST `/Agents/topErroredAgents` |
| agent incidents, recurring errors                        | Insights | `agents.getIncidents` → POST `/Agents/incidents`           |
| incident type mix (error/escalation/policy split)        | Insights | `agents.getIncidentDistribution` → POST `/Agents/incidentDistribution` |
| token consumption, AGU, PLTU, cost per agent             | Insights | `agents.getConsumption` → POST `/Agents/consumption`       |
| AGU burn-rate over time                                  | Insights | `agents.getConsumptionTimeline` → POST `/Agents/consumptionTimeline` |
| P50 / P95 latency per agent over time                    | Insights | `agents.getLatencyTimeline` → POST `/Agents/latencyTimeline` |
| agent fleet list, health score, stale agents             | Insights | `agents.getAgents` → POST `/Agents/agents`                 |
| agent invocation count, run volume, agent calls over time | Insights | `agents.getConsumptionTimeline` → POST `/Agents/consumptionTimeline` |
| active agent count, how many agents, fleet size            | Insights | `agents.getAgents` → count `data.agents` array length              |
| agent health overview, important metrics, agent summary    | Insights | `agents.getSummaryV2` (KPIs) + `agents.getAgents` (fleet list)    |
| AGU/PLTU split by complete vs incomplete jobs            | Insights | `agents.getUnitConsumption` → POST `/Agents/summary/unit-consumption` |
| trace latency P50/P95 over time (trace-level)            | Insights | `traceview.getLatencyTimeline` → POST `/Traceview/latencyTimeline` |
| trace errors by agent over time                          | Insights | `traceview.getErrorsTimeline` → POST `/Traceview/errorsTimeline` |
| memory usage (in/out/enabled/disabled)                   | Insights | `traceview.getMemoryTimeline` → POST `/Traceview/memoryTimeline` |
| top memory spaces, memory adoption                       | Insights | `traceview.getTopMemorySpaces` → POST `/Traceview/topMemorySpaces` |
| policy Allow/Deny/NoOp ratio                             | Insights | `governance.getPolicySummary` → POST `/Governance/policy/summary` |
| recent policy decisions, denial feed                     | Insights | `governance.getPolicyTraces` → POST `/Governance/policy/traces` |
| governed operation volume                                | Insights | `governance.getOperationSummary` → POST `/Governance/operation/summary` |
| completed job trend (historical)                         | Insights | `jobs.getCompletedTimeline` → POST `/api/v1.0/InsightsJobs/completed-timeline` |
| job aggregate KPI (total/success/avg duration)           | Insights | `jobs.getSummary` → POST `/api/v1.0/InsightsJobs/summary` |
| top failing processes (historical)                       | Insights | `jobs.getTopFailures` → POST `/api/v1.0/InsightsJobs/top-failures` |

## Tie-breaking Rules
- "job count today" → SDK (current state); "job count over 7 days" → Insights `jobs.getCompletedTimeline`
- "queue depth" → SDK; "queue throughput trend" → no Insights endpoint, stay SDK
- P50/P95/P99 latency → Insights `agents.getLatencyTimeline` (fleet) or `traceview.getLatencyTimeline` (trace)
- "agent health" snapshot → Insights `agents.getAgents` (has `healthScore`); "success rate over time" → `agents.getSummaryV2`
- `governance.getPolicySummary` requires `policy` (UUID) in body in addition to `tenantId`
- "invocation volume" / "run count" / "calls over time" → agents.getConsumptionTimeline (returns time-bucketed aguConsumption; interpret as activity proxy until a dedicated invocation-count endpoint is available)
- "important metrics" / "key metrics" / "overview" with no other qualifier → agents.getSummaryV2 for success/duration KPIs + agents.getAgents for fleet health
- getSummaryV2 is AGGREGATE-ONLY (returns a single summary object for the period, not a time-series array). Never use it as the data source for area, line, or bar charts. Use getErrors, getConsumptionTimeline, or getLatencyTimeline for time-series charts.

## SDK Import Pattern
```typescript
import { UiPath } from '@uipath/uipath-typescript/core';
import { Jobs } from '@uipath/uipath-typescript/jobs';
// Never root imports — always subpath exports
```

## Fallback — When No Route Matches

If the user's metric doesn't match any entry in the Routing Table above:

### Step 1 — Find the closest proxy

| User asks for | Best available proxy | How to note it |
|---|---|---|
| "productivity" / "throughput" | `agents.getConsumptionTimeline` (activity proxy) | "I'll show invocation activity as a proxy for productivity" |
| "error rate %" | `agents.getErrors` (count, not %) + `agents.getSummaryV2` (total) | "I'll show daily error counts — divide by total runs for %" |
| "memory usage per agent" | Not available | Tell user, suggest `traceview.getMemoryTimeline` as fleet-level alternative |
| "compare this month vs last month" | `agents.getSummaryV2` with `startTime`/`endTime` twice | Show two KPI cards with different time windows |
| "real-time agent status" | `agents.getAgents` (last run + healthScore) | "I'll show last-known status — updates when agents run" |
| "SLA compliance" | `agents.getSummaryV2.successRate` | "I'll show success rate as a proxy for SLA compliance" |
| Anything with "cost" or "spend" | `agents.getConsumption` (AGU/PLTU) | "UiPath uses AGU/PLTU units — I'll show those instead of currency" |

### Step 2 — NEVER do these

- **Never generate a widget for a non-existent endpoint.** If no route matches and no proxy fits, the widget must be omitted from the plan.
- **Never guess a field name** that isn't in the Key response fields column of insights-catalog.md.
- **Never use `traceview.*` for agent-level metrics** — traceview is trace/session level, not agent level.

### Step 3 — State the approximation in the plan

When using a proxy, say so explicitly in the plan description (see build-plan.md graceful degradation wording):

```
• Agent Productivity (30 days) — I'll show invocation volume as a
  proxy for productivity; a dedicated productivity metric isn't
  available in the analytics API
```

Never silently substitute — the user needs to be able to correct this in the approval step.

## Insights Hook Pattern
```typescript
import { useInsights } from '@/hooks/useInsights';
// Both startTime AND endTime are required — omitting endTime causes 500 errors
const NOW            = new Date().toISOString()
const SEVEN_DAYS_AGO = new Date(Date.now() - 604_800_000).toISOString()

const { data, loading, error } = useInsights(
  'agents.getSummaryV2',
  { startTime: SEVEN_DAYS_AGO, endTime: NOW }
);
```
