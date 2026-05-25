# Dashboard Generation Capability — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dashboard-generation capability to `skills/uipath-coded-apps` so an agent can turn a natural-language prompt into a deployed React dashboard backed by UiPath Insights RTM APIs and the TS SDK.

**Architecture:** Extend the skill via a new `references/dashboards/` subtree (capability hub + plugins + primitives) and `assets/templates/dashboard/` (React scaffold + widget templates). Existing 17 reference files are untouched. SKILL.md receives 3 surgical edits. A disambiguation block routes intent silently for strong signals; explicit question only when ambiguous.

**Tech Stack:** TypeScript 5.4, React 18, Vite 5, Recharts 2, shadcn/ui, Tailwind CSS 3, `@uipath/uipath-typescript`, UiPath Insights RTM API (HTTP POST, base `…/insightsrtm_`)

> **Env-var convention note:** The plan uses `VITE_UIPATH_ORG_NAME` / `VITE_UIPATH_TENANT_NAME` to match the existing `web-app-template.md` convention. The design spec used shorter names (`VITE_UIPATH_ORG` / `VITE_UIPATH_TENANT`) — treat this plan as authoritative.

---

## File Map

### Modified
| File | Change |
|------|--------|
| `skills/uipath-coded-apps/SKILL.md` | Update description; add disambiguation block after Critical Rules; add dashboard row to Task Navigation table |

### New — skill documentation
| File | Purpose |
|------|---------|
| `skills/uipath-coded-apps/references/dashboards/CAPABILITY.md` | Dashboard hub: 10 critical rules + plugin router |
| `skills/uipath-coded-apps/references/dashboards/plugins/build/impl.md` | 8-phase build pipeline (Plan→Approve→Scaffold→Validate→Preview) |
| `skills/uipath-coded-apps/references/dashboards/plugins/deploy/impl.md` | Thin deploy delegation to `pack-publish-deploy.md` |
| `skills/uipath-coded-apps/references/dashboards/primitives/auth-context.md` | Resolve org/tenant/tenantId from uip login |
| `skills/uipath-coded-apps/references/dashboards/primitives/build-plan.md` | Plan format + approval gate rules |
| `skills/uipath-coded-apps/references/dashboards/primitives/data-router.md` | 26-row SDK vs Insights routing table |
| `skills/uipath-coded-apps/references/dashboards/primitives/insights-client.md` | InsightsClient pattern (4 namespaces, POST, tenantId) |
| `skills/uipath-coded-apps/references/dashboards/insights-catalog.md` | Full static Insights capability catalog |

### New — scaffold template
| File | Purpose |
|------|---------|
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/package.json` | Dependencies |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/vite.config.ts` | Vite — `base: './'`, SDK shims |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/tsconfig.json` | Strict TypeScript |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/tailwind.config.ts` | UiPath color tokens |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/uipath.json` | SDK OAuth config |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/index.html` | HTML entry |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/.env.example` | Committed placeholder env |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/index.css` | Tailwind directives + CSS vars |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/main.tsx` | React entry |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/App.tsx` | Auth gate + shell mount |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/hooks/useAuth.ts` | SDK PKCE + `getToken` for Insights |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/hooks/useInsights.ts` | Insights data hook |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/lib/insights-client.ts` | InsightsClient — 4 namespaces |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/lib/sdk-client.ts` | TS SDK init helpers |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/components/DashboardShell.tsx` | Layout + sidebar nav |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/components/WidgetGrid.tsx` | Responsive CSS grid |
| `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/components/MetricCard.tsx` | KPI card base |

### New — widget templates
| File | Placeholders filled by agent |
|------|------------------------------|
| `skills/uipath-coded-apps/assets/templates/dashboard/widgets/area-chart.tsx` | COMPONENT_NAME, DATA_HOOK, TITLE, X_KEY, Y_KEY |
| `skills/uipath-coded-apps/assets/templates/dashboard/widgets/bar-chart.tsx` | same |
| `skills/uipath-coded-apps/assets/templates/dashboard/widgets/donut-chart.tsx` | COMPONENT_NAME, DATA_HOOK, TITLE, DATA_KEY, NAME_KEY |
| `skills/uipath-coded-apps/assets/templates/dashboard/widgets/kpi-card.tsx` | COMPONENT_NAME, DATA_HOOK, TITLE, VALUE_KEY |
| `skills/uipath-coded-apps/assets/templates/dashboard/widgets/line-chart.tsx` | COMPONENT_NAME, DATA_HOOK, TITLE, X_KEY, Y_KEY |
| `skills/uipath-coded-apps/assets/templates/dashboard/widgets/data-table.tsx` | COMPONENT_NAME, DATA_HOOK, TITLE, COLUMNS |

### New — scripts + eval tasks
| File | Purpose |
|------|---------|
| `skills/uipath-coded-apps/assets/scripts/discover-capabilities.mjs` | Enriches Insights catalog with live tenant data |
| `tests/tasks/uipath-coded-apps/dashboard/dashboard_build.yaml` | Eval: NLP build + correct SDK/Insights routing |
| `tests/tasks/uipath-coded-apps/dashboard/dashboard_disambiguate.yaml` | Eval: Ambiguous intent triggers question |
| `tests/tasks/uipath-coded-apps/dashboard/dashboard_incremental.yaml` | Eval: Add widget to existing dashboard |

---

## Task 1: Directory structure + first eval task

**Files:**
- Create: all new subdirectories
- Create: `tests/tasks/uipath-coded-apps/dashboard/dashboard_build.yaml`

- [ ] **Step 1: Create directories**

Run from `C:\Work\skills`:
```bash
mkdir -p skills/uipath-coded-apps/references/dashboards/plugins/build \
         skills/uipath-coded-apps/references/dashboards/plugins/deploy \
         skills/uipath-coded-apps/references/dashboards/primitives \
         skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/hooks \
         skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/lib \
         skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/components \
         skills/uipath-coded-apps/assets/templates/dashboard/widgets \
         skills/uipath-coded-apps/assets/scripts \
         tests/tasks/uipath-coded-apps/dashboard
```

- [ ] **Step 2: Write the NLP-build eval task**

Create `tests/tasks/uipath-coded-apps/dashboard/dashboard_build.yaml`:
```yaml
task_id: uipath-coded-apps-dashboard-build
description: >
  Validates that the dashboard capability generates a plan before scaffolding,
  routes agent metrics to Insights and queue items to SDK, and produces a
  TypeScript-clean project.
tags: [uipath-coded-apps, smoke, dashboard]

sandbox:
  driver: tempdir
  node: {}

initial_prompt: |
  Create a dashboard for my team showing:
  - Agent success rate over the last 7 days
  - Current active queue items by folder
  - P95 process execution time

  Do NOT ask for approval, confirmation, or feedback.
  Do NOT pause between planning and implementation.
  Before starting, load the uipath-coded-apps skill and follow its workflow.

success_criteria:
  - type: file_exists
    description: "Scaffold package.json created"
    path: "package.json"
    weight: 1.5
    pass_threshold: 1.0

  - type: file_exists
    description: ".env.local written with base URL"
    path: ".env.local"
    weight: 1.0
    pass_threshold: 1.0

  - type: file_contains
    description: "Agent success rate widget uses Insights agents namespace"
    path: "src/widgets"
    pattern: "useInsights.*agents\\."
    weight: 2.0
    pass_threshold: 1.0

  - type: file_contains
    description: "Queue items widget uses SDK (not Insights)"
    path: "src/widgets"
    pattern: "QueueItems|queues\\.getAll"
    weight: 2.0
    pass_threshold: 1.0

  - type: command_executed
    description: "tsc --noEmit ran"
    tool_name: "Bash"
    command_pattern: 'tsc\s+--noEmit'
    min_count: 1
    weight: 1.5
    pass_threshold: 1.0

  - type: file_contains
    description: ".env.local has VITE_UIPATH_BASE_URL"
    path: ".env.local"
    pattern: "VITE_UIPATH_BASE_URL="
    weight: 1.0
    pass_threshold: 1.0
```

- [ ] **Step 3: Commit**
```bash
git add tests/tasks/uipath-coded-apps/
git commit -m "test: add dashboard_build eval task"
```

---

## Task 2: SKILL.md — 3 surgical edits

**Files:**
- Modify: `skills/uipath-coded-apps/SKILL.md`

- [ ] **Step 1: Update the frontmatter description**

In `skills/uipath-coded-apps/SKILL.md`, replace line 3:
```
description: "Always invoke for `app.config.json` or `action-schema.json` files. UiPath Coded Web Apps & Coded Action Apps via `uip codedapp` and `@uipath/uipath-typescript` SDK. Scaffold, build, debug, deploy. For .cs/XAML→uipath-rpa, Python→uipath-agents."
```
With:
```
description: "UiPath Coded Web Apps, Action Apps (app.config.json, action-schema.json), and admin dashboards. Build and deploy apps via uip codedapp + TS SDK. Generate analytics/KPI/observability dashboards from NLP using Insights RTM API. For .cs/XAML→uipath-rpa, Python→uipath-agents, .flow→uipath-maestro-flow."
```

- [ ] **Step 2: Add disambiguation block**

Insert the following block immediately before the `## Task Navigation` heading (after the last Critical Rule, rule 16):
```markdown

## Disambiguation — Apps vs Dashboards

**Route directly to Apps workflow** (sections below) when you see:
`web app`, `action app`, `codedapp`, `app.config.json`, `action-schema.json`,
`scaffold app`, `deploy app`, `pack`, `publish`, `push`, `pull`, `debug app`

**Route directly to [references/dashboards/CAPABILITY.md](references/dashboards/CAPABILITY.md) when you see:**
`dashboard`, `analytics`, `KPI`, `metrics`, `Insights`, `observability`,
`admin console`, `report`, `chart`, `trend`, `governance report`, `agent metrics`

**When intent is ambiguous** — render this verbatim, wait for digit `1` or `2` only:

> Which fits your goal?
> 1. **Build or modify a Web App or Action App** — scaffold a UI, form, or app that deploys to Automation Cloud
> 2. **Generate a dashboard** — analytics or admin view from a natural-language description

```

- [ ] **Step 3: Add dashboard row to Task Navigation table**

Append this row to the Task Navigation table (after the last existing row):
```markdown
| **Generate an admin dashboard from NLP** | [references/dashboards/CAPABILITY.md](references/dashboards/CAPABILITY.md) |
```

- [ ] **Step 4: Validate description length**

Run from `C:\Work\skills`:
```bash
bash hooks/validate-skill-descriptions.sh
```
Expected: no errors (description is ~230 chars, well under 1024).

- [ ] **Step 5: Commit**
```bash
git add skills/uipath-coded-apps/SKILL.md
git commit -m "feat(coded-apps): add dashboard disambiguation + capability router to SKILL.md"
```

---

## Task 3: CAPABILITY.md

**Files:**
- Create: `skills/uipath-coded-apps/references/dashboards/CAPABILITY.md`

- [ ] **Step 1: Write the file**

```markdown
---
name: uipath-coded-apps/dashboards
---

# Dashboard Capability

## When to Use This Capability
- User wants a dashboard, analytics view, KPI summary, or metric report
- NLP prompt describes data to visualize ("agent success rates", "queue SLA", "governance violations")
- Iterating on an existing dashboard (adding widgets, changing chart types)

## Critical Rules
1. Read `primitives/auth-context.md` BEFORE any SDK or Insights API call
2. ALWAYS derive a plain-language plan before writing code — read `primitives/build-plan.md`
3. HALT at the approval gate — do not scaffold until user confirms the plan
4. Route each metric to SDK or Insights via `primitives/data-router.md` — never guess the source
5. NEVER hardcode tenant IDs, org names, or folder paths in generated code
6. NEVER auto-deploy — deploy pipeline always requires explicit user confirmation
7. Use the HTTP client from `primitives/insights-client.md` for all Insights API calls
8. All tokens flow through `useAuth()` — never store tokens in state, localStorage, or env vars at runtime
9. Run `tsc --noEmit` before claiming success
10. Every list call paginates — ≤50 rows per page, never load all

## Plugin Router

| I want to...                                  | Read                                           |
|-----------------------------------------------|------------------------------------------------|
| Create or edit a dashboard                    | [plugins/build/impl.md](plugins/build/impl.md) |
| Deploy a built dashboard to Automation Cloud  | [plugins/deploy/impl.md](plugins/deploy/impl.md) |

## Reference Files
- [primitives/auth-context.md](primitives/auth-context.md) — auth session resolution
- [primitives/build-plan.md](primitives/build-plan.md) — plan generation + approval gate
- [primitives/data-router.md](primitives/data-router.md) — SDK vs Insights routing
- [primitives/insights-client.md](primitives/insights-client.md) — Insights HTTP client
- [insights-catalog.md](insights-catalog.md) — Insights capability catalog
```

- [ ] **Step 2: Verify all links in the file resolve**
```bash
ls skills/uipath-coded-apps/references/dashboards/plugins/build/impl.md \
   skills/uipath-coded-apps/references/dashboards/plugins/deploy/impl.md \
   skills/uipath-coded-apps/references/dashboards/primitives/auth-context.md \
   skills/uipath-coded-apps/references/dashboards/primitives/build-plan.md \
   skills/uipath-coded-apps/references/dashboards/primitives/data-router.md \
   skills/uipath-coded-apps/references/dashboards/primitives/insights-client.md \
   skills/uipath-coded-apps/references/dashboards/insights-catalog.md 2>&1 || echo "MISSING — create these in later tasks"
```
Expected: "MISSING" for now — these are created in Tasks 4–7.

- [ ] **Step 3: Commit**
```bash
git add skills/uipath-coded-apps/references/dashboards/CAPABILITY.md
git commit -m "feat(coded-apps): add dashboard CAPABILITY.md hub"
```

---

## Task 4: Primitives — auth-context.md + build-plan.md

**Files:**
- Create: `skills/uipath-coded-apps/references/dashboards/primitives/auth-context.md`
- Create: `skills/uipath-coded-apps/references/dashboards/primitives/build-plan.md`

- [ ] **Step 1: Write auth-context.md**

```markdown
# Auth Context Resolution

Read BEFORE any SDK or Insights API call.

## Step 1 — Verify login
```bash
uip login status --output json
```
If `isLoggedIn` is false → stop, tell user to run `uip login`.

## Step 2 — Extract fields
```json
{
  "isLoggedIn": true,
  "accountName": "<ORG_NAME>",
  "tenantName": "<TENANT_NAME>",
  "userId": "<USER_UUID>"
}
```

## Step 3 — Resolve tenantId (UUID)
Insights RTM endpoints require `tenantId` (UUID) in every POST body — NOT the tenant name string.
Read from the `uip` CLI `.auth` file:
```bash
uip login status --output json
```
The output includes a `tenantId` field. If not present in that command, read the raw auth file:
```bash
cat ~/.uipath/.auth | node -e \
  "const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')); \
   console.log(d.tenantId || d.TenantId)"
```
Cache the resolved tenantId in memory for the session — never write to disk.
Write it to `.env.local` during scaffold Phase 6 so the React app can use it at runtime.

## Step 4 — Construct base URLs

Detect environment from the cloud URL returned by login status:
```
URL contains "alpha"   → VITE_UIPATH_BASE_URL=https://alpha.api.uipath.com
URL contains "staging" → VITE_UIPATH_BASE_URL=https://staging.api.uipath.com
Otherwise              → VITE_UIPATH_BASE_URL=https://api.uipath.com
```

All service URLs are derived at runtime in the React app:
```
SDK base:     ${VITE_UIPATH_BASE_URL}/${VITE_UIPATH_ORG_NAME}/${VITE_UIPATH_TENANT_NAME}
Insights RTM: ${VITE_UIPATH_BASE_URL}/${VITE_UIPATH_ORG_NAME}/${VITE_UIPATH_TENANT_NAME}/insightsrtm_
Jobs base:    ${VITE_UIPATH_BASE_URL}/${VITE_UIPATH_ORG_NAME}/${VITE_UIPATH_TENANT_NAME}
```

## Error handling
- 401 → token expired → re-run `uip login`, retry once
- Missing accountName/tenantName → tell user: "Run `uip login` and try again"
- Cannot resolve tenantId → fall back to reading `~/.uipath/.auth` directly
```

- [ ] **Step 2: Write build-plan.md**

```markdown
# Plan Generation + Approval Gate

## Plan Format
Render as a numbered markdown list in chat. No code blocks, no JSON.
Each line: `N. <Widget name> (<time frame>) [SDK | Insights] — <chart type>, <aggregation>`

Example output to show the user:
```
Here's what I'll build. Confirm to proceed, or tell me what to change.

1. Agent Success Rate (last 7 days)      [Insights] — area chart, daily % success
2. Active Queue Items by folder          [SDK]      — bar chart, snapshot count
3. P95 Process Execution Time            [Insights] — KPI card, weekly avg ms
4. Pending Action Center Tasks           [SDK]      — KPI card, live count
5. Governance Violations (last 30 days)  [Insights] — line chart, daily count
6. Maestro Flow Runs by status           [SDK]      — donut chart, snapshot
```

## Approval Gate Rules
- ANY positive response → proceed to scaffold
  (yes, looks good, do it, go ahead, 👍, confirmed, ship it)
- Widget edit request → update that line only, re-show ONLY the changed lines, re-ask
- "Remove X" → strike item from list, show updated list, re-ask
- "Add X" → derive route via data-router.md, append item, show updated list, re-ask
- Rejection without edit → ask: "What would you like to change?"
- Never re-show the full plan after partial edits — show diffs only

## Four-Axis Metric Decomposition
For each metric mentioned in the NLP prompt, derive:
- **Shape**: `line | bar | area | donut | kpi | table`
- **Time frame**: `realtime | hourly | daily | weekly | monthly`
- **Aggregation**: `count | sum | avg | p50 | p95 | p99`
- **Service**: `SDK` or `Insights` (resolve via data-router.md)

## Anti-patterns
- Do NOT start scaffolding before explicit approval
- Do NOT infer approval from silence or a question ("which folder?")
- Do NOT re-derive the entire plan if only one widget changes
- Do NOT show code or file paths in the plan — plain language only
```

- [ ] **Step 3: Commit**
```bash
git add skills/uipath-coded-apps/references/dashboards/primitives/auth-context.md \
        skills/uipath-coded-apps/references/dashboards/primitives/build-plan.md
git commit -m "feat(coded-apps): add dashboard primitives auth-context + build-plan"
```

---

## Task 5: Primitives — data-router.md + insights-catalog.md

**Files:**
- Create: `skills/uipath-coded-apps/references/dashboards/primitives/data-router.md`
- Create: `skills/uipath-coded-apps/references/dashboards/insights-catalog.md`

- [ ] **Step 1: Write data-router.md**

```markdown
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

## SDK Import Pattern
```typescript
import { UiPath } from '@uipath/uipath-typescript/core';
import { Jobs } from '@uipath/uipath-typescript/jobs';
// Never root imports — always subpath exports
```

## Insights Hook Pattern
```typescript
import { useInsights } from '../hooks/useInsights';
// Key is namespace.method
const { data, loading, error } = useInsights(
  'agents.getSummaryV2',
  { startTime: '2025-01-01T00:00:00Z' }
);
```
```

- [ ] **Step 2: Write insights-catalog.md**

```markdown
# Insights Capability Catalog

Source: "Insights APIs to use for dashboard as code" (internal Confluence)
Base URL pattern: `${VITE_UIPATH_BASE_URL}/${ORG}/${TENANT}/insightsrtm_/<namespace>/<endpoint>`
Environment values for VITE_UIPATH_BASE_URL:
  alpha:   https://alpha.api.uipath.com
  staging: https://staging.api.uipath.com
  prod:    https://api.uipath.com
All calls: POST JSON body. All require `tenantId` (UUID). Add `startTime`/`endTime` (ISO 8601) per endpoint.

---

## Agents namespace — POST /Agents/...

| Method                         | Route suffix                       | Key metrics                                    | Shape       |
|--------------------------------|------------------------------------|------------------------------------------------|-------------|
| `agents.getSummaryV2`          | Agents/summaryV2                   | Success rate, failure rate, avg duration, Δ    | kpi, table  |
| `agents.getErrors`             | Agents/errors                      | Error count over time per agent                | area, line  |
| `agents.getTopErroredAgents`   | Agents/topErroredAgents            | Top-N erroring agents leaderboard              | bar, table  |
| `agents.getIncidents`          | Agents/incidents                   | Paged incident table                           | table       |
| `agents.getIncidentDistribution` | Agents/incidentDistribution      | Error / Escalation / Policy split              | donut, kpi  |
| `agents.getConsumption`        | Agents/consumption                 | Top agents by AGU/PLTU                         | bar, table  |
| `agents.getConsumptionTimeline`| Agents/consumptionTimeline         | AGU burn-rate over time                        | area, line  |
| `agents.getLatencyTimeline`    | Agents/latencyTimeline             | P50 / P95 latency per agent                    | line        |
| `agents.getAgents`             | Agents/agents                      | Fleet list with healthScore                    | table       |
| `agents.getUnitConsumption`    | Agents/summary/unit-consumption    | AGU/PLTU by complete vs incomplete jobs        | kpi, bar    |
| `agents.getNames`              | Agents/names                       | Agent name list (filter dropdowns)             | filter only |

Not for MVP: `agents.getProcessEscalations`

---

## Traceview namespace — POST /Traceview/...

| Method                           | Route suffix                   | Key metrics                              | Shape      |
|----------------------------------|--------------------------------|------------------------------------------|------------|
| `traceview.getLatencyTimeline`   | Traceview/latencyTimeline      | P50/P95 trace latency over time          | line       |
| `traceview.getErrorsTimeline`    | Traceview/errorsTimeline       | Trace errors per agent per bucket        | area, line |
| `traceview.getMemoryTimeline`    | Traceview/memoryTimeline       | In/out/enabled/disabled memory counts    | area       |
| `traceview.getMemoryCallsTimeline` | Traceview/memoryCallsTimeline | Memory API calls over time               | bar        |
| `traceview.getTopMemorySpaces`   | Traceview/topMemorySpaces      | Most-active memory spaces                | bar, table |
| `traceview.getUnitConsumption`   | Traceview/unitConsumption      | Per-agent AIU + PLTU from traces         | table, bar |

Not for MVP: `traceview.getSpansByTraceId`, `traceview.getSpansByReferenceId`

---

## Governance namespace — POST /Governance/...

| Method                          | Route suffix                      | Key metrics                       | Shape       |
|---------------------------------|-----------------------------------|-----------------------------------|-------------|
| `governance.getPolicySummary`   | Governance/policy/summary         | Allow/Deny/NoOp for one policy    | donut, kpi  |
| `governance.getPolicyTraces`    | Governance/policy/traces          | Per-evaluation trace table        | table       |
| `governance.getOperationSummary`| Governance/operation/summary      | Governed operation volume         | bar, kpi    |

Note: `getPolicySummary` requires additional `policy` (UUID) field in body.

---

## Jobs namespace — POST /api/v1.0/InsightsJobs/... (base: jobsBase)

| Method                          | Route suffix                                  | Key metrics                          | Shape      |
|---------------------------------|-----------------------------------------------|--------------------------------------|------------|
| `jobs.getSummary`               | api/v1.0/InsightsJobs/summary                 | KPI: total/success count, avg time   | kpi        |
| `jobs.getCompletedTimeline`     | api/v1.0/InsightsJobs/completed-timeline      | Completed jobs over time by state    | area, line |
| `jobs.getUncompletedTimeline`   | api/v1.0/InsightsJobs/uncompleted-timeline    | Pending/running jobs over time       | area, line |
| `jobs.getTopFailures`           | api/v1.0/InsightsJobs/top-failures            | Processes by failed-job count        | bar        |
| `jobs.getFailuresByReason`      | api/v1.0/InsightsJobs/failures-by-reason      | Failures by exception type           | bar, donut |
| `jobs.getProcessDetails`        | api/v1.0/InsightsJobs/process-details         | Per-process success/duration table   | table      |
| `jobs.getFailureDetails`        | api/v1.0/InsightsJobs/failure-details         | Detailed failure rows (drill-down)   | table      |

---

## Not in Insights — use SDK instead

Current operational state: live job/queue/task counts, process inventory, case SLA summaries,
DataFabric entity records, Maestro instance lists, Action Center task counts.

---

## Suggested Dashboard Packages

| Dashboard                | Primary endpoints                                                                  |
|--------------------------|------------------------------------------------------------------------------------|
| Executive Fleet Health   | getSummaryV2, jobs.getSummary, getIncidentDistribution, getConsumptionTimeline      |
| Jobs Operations          | jobs.getCompletedTimeline, jobs.getTopFailures, jobs.getProcessDetails             |
| Agent Reliability        | getErrors, getTopErroredAgents, getIncidents, getLatencyTimeline                   |
| Agent Cost / FinOps      | getConsumption, getConsumptionTimeline, getUnitConsumption, getAgents              |
| Traces & Memory          | traceview.getLatencyTimeline, traceview.getErrorsTimeline, traceview.getMemoryTimeline |
| Governance Posture       | governance.getPolicySummary, governance.getPolicyTraces, governance.getOperationSummary |
```

- [ ] **Step 3: Commit**
```bash
git add skills/uipath-coded-apps/references/dashboards/primitives/data-router.md \
        skills/uipath-coded-apps/references/dashboards/insights-catalog.md
git commit -m "feat(coded-apps): add data-router + insights-catalog primitives"
```

---

## Task 6: Primitive — insights-client.md

**Files:**
- Create: `skills/uipath-coded-apps/references/dashboards/primitives/insights-client.md`

- [ ] **Step 1: Write the file**

```markdown
# Insights HTTP Client

Temporary HTTP client until Insights lands in `@uipath/uipath-typescript`.
When SDK ships: replace `InsightsClient` with the SDK class in `sdk-client.ts`.
No widget files, no hook call sites change on migration.

## Client Implementation (generated into every dashboard as `src/lib/insights-client.ts`)

```typescript
// All RTM endpoints (Agents, Traceview, Governance): base = …/insightsrtm_
// Jobs endpoints: base = …/<ORG>/<TENANT>  path = /api/v1.0/InsightsJobs/…

export interface InsightsParams {
  tenantId: string;        // UUID from VITE_INSIGHTS_TENANT_ID — never the tenant name string
  startTime?: string;      // ISO 8601, e.g. "2025-01-01T00:00:00Z"
  endTime?: string;        // ISO 8601
  limit?: number;
  [key: string]: unknown;
}

export class InsightsClient {
  constructor(
    private rtmBase: string,   // ${VITE_UIPATH_BASE_URL}/${ORG}/${TENANT}/insightsrtm_
    private jobsBase: string,  // ${VITE_UIPATH_BASE_URL}/${ORG}/${TENANT}
    private getToken: () => Promise<string>
  ) {}

  private async post<T>(base: string, path: string, body: InsightsParams): Promise<T> {
    const token = await this.getToken();
    const res = await fetch(`${base}/${path}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (res.status === 401) throw new Error('INSIGHTS_AUTH_EXPIRED');
    if (!res.ok) throw new Error(`Insights ${res.status}: ${base}/${path}`);
    return res.json() as Promise<T>;
  }

  agents = {
    getSummaryV2:             (p: InsightsParams) => this.post(this.rtmBase, 'Agents/summaryV2', p),
    getErrors:                (p: InsightsParams) => this.post(this.rtmBase, 'Agents/errors', p),
    getTopErroredAgents:      (p: InsightsParams) => this.post(this.rtmBase, 'Agents/topErroredAgents', p),
    getIncidents:             (p: InsightsParams) => this.post(this.rtmBase, 'Agents/incidents', p),
    getIncidentDistribution:  (p: InsightsParams) => this.post(this.rtmBase, 'Agents/incidentDistribution', p),
    getConsumption:           (p: InsightsParams) => this.post(this.rtmBase, 'Agents/consumption', p),
    getConsumptionTimeline:   (p: InsightsParams) => this.post(this.rtmBase, 'Agents/consumptionTimeline', p),
    getLatencyTimeline:       (p: InsightsParams) => this.post(this.rtmBase, 'Agents/latencyTimeline', p),
    getAgents:                (p: InsightsParams) => this.post(this.rtmBase, 'Agents/agents', p),
    getUnitConsumption:       (p: InsightsParams) => this.post(this.rtmBase, 'Agents/summary/unit-consumption', p),
    getNames:                 (p: InsightsParams) => this.post(this.rtmBase, 'Agents/names', p),
  };

  traceview = {
    getLatencyTimeline:     (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/latencyTimeline', p),
    getErrorsTimeline:      (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/errorsTimeline', p),
    getMemoryTimeline:      (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/memoryTimeline', p),
    getMemoryCallsTimeline: (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/memoryCallsTimeline', p),
    getTopMemorySpaces:     (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/topMemorySpaces', p),
    getUnitConsumption:     (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/unitConsumption', p),
  };

  governance = {
    getPolicySummary:    (p: InsightsParams & { policy: string }) =>
                           this.post(this.rtmBase, 'Governance/policy/summary', p),
    getPolicyTraces:     (p: InsightsParams) => this.post(this.rtmBase, 'Governance/policy/traces', p),
    getOperationSummary: (p: InsightsParams) => this.post(this.rtmBase, 'Governance/operation/summary', p),
  };

  jobs = {
    getSummary:            (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/summary', p),
    getCompletedTimeline:  (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/completed-timeline', p),
    getUncompletedTimeline:(p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/uncompleted-timeline', p),
    getTopFailures:        (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/top-failures', p),
    getFailuresByReason:   (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/failures-by-reason', p),
    getProcessDetails:     (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/process-details', p),
    getFailureDetails:     (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/failure-details', p),
  };
}
```

## Initialization in sdk-client.ts

```typescript
import { InsightsClient } from './insights-client';

const base   = import.meta.env.VITE_UIPATH_BASE_URL;
const org    = import.meta.env.VITE_UIPATH_ORG_NAME;
const tenant = import.meta.env.VITE_UIPATH_TENANT_NAME;

export function createInsightsClient(getToken: () => Promise<string>): InsightsClient {
  return new InsightsClient(
    `${base}/${org}/${tenant}/insightsrtm_`,
    `${base}/${org}/${tenant}`,
    getToken
  );
}
```

## useInsights hook — namespace-qualified key

```typescript
// Key format: 'namespace.method'
// Examples: 'agents.getSummaryV2' | 'traceview.getLatencyTimeline' | 'governance.getPolicySummary'
// tenantId is injected automatically from useAuth() — callers only pass startTime/endTime/etc.
const { data, loading, error } = useInsights(
  'agents.getSummaryV2',
  { startTime: '2025-01-01T00:00:00Z' }
);
```

## SDK Migration Steps (when @uipath/uipath-typescript/insights ships)
1. In `sdk-client.ts`: replace `createInsightsClient(...)` with SDK Insights service init
2. Update `useInsights.ts` to use the SDK namespace calls
3. Delete `src/lib/insights-client.ts` from the scaffold template
4. Update `insights-catalog.md`: remove "HTTP client" note
No widget files change on migration — hook interface is stable.
```

- [ ] **Step 2: Commit**
```bash
git add skills/uipath-coded-apps/references/dashboards/primitives/insights-client.md
git commit -m "feat(coded-apps): add insights-client primitive (4-namespace HTTP client)"
```

---

## Task 7: plugins/build/impl.md

**Files:**
- Create: `skills/uipath-coded-apps/references/dashboards/plugins/build/impl.md`

- [ ] **Step 1: Write the file**

```markdown
# Dashboard Build Plugin

Full pipeline: NLP prompt → plan approval → scaffold → widgets → validate → preview.

## Tool-Use Budget
≤ 14 tool calls for a 6-widget dashboard. Never exceed 20 total.

## Phase 1 — Boot (1 tool-use block)
Read ALL the following in a single parallel message:
- `../../primitives/auth-context.md`
- `../../primitives/build-plan.md`
- `../../primitives/data-router.md`
- `../../insights-catalog.md`

## Phase 2 — Preflight (1 Bash)
```bash
uip login status --output json
```
Extract: `accountName` → ORG, `tenantName` → TENANT, `tenantId` → UUID.
Detect environment from cloud URL (see auth-context.md Step 4).
If not logged in → stop, tell user to run `uip login`.

## Phase 3 — Metric Derivation (0 tool calls)
For each metric in the NLP prompt, derive using build-plan.md four-axis decomposition:
- Shape, time frame, aggregation, service (SDK or Insights)
- Route each metric using data-router.md routing table

## Phase 4 — Plan (0 tool calls)
Render the plan in chat using the format in build-plan.md.
Show [SDK] or [Insights] label + method for each widget.
Do NOT write any files yet.

## Phase 5 — Approval Gate (0 tool calls)
HALT. Wait for user response.
Follow approval gate rules in build-plan.md exactly.
Do not proceed until explicit approval is received.

## Phase 6 — Scaffold (1 Bash)
Copy the scaffold template and write env vars. Substitute:
- `<API_BASE_URL>` from Phase 2 environment detection
- `<ORG_NAME>` from Phase 2 `accountName`
- `<TENANT_NAME>` from Phase 2 `tenantName`
- `<TENANT_UUID>` from Phase 2 `tenantId`
- `<CLIENT_ID>` — ask user if not already known (point to `../../oauth-client-setup.md` if needed)

```bash
SKILL_ROOT="$(uip tools path @uipath/codedapp-tool 2>/dev/null | xargs dirname)/../../skills/uipath-coded-apps"
cp -r "${SKILL_ROOT}/assets/templates/dashboard/scaffold/." <PROJECT_DIR>/
cd <PROJECT_DIR>
cat > .env.local << 'EOF'
VITE_UIPATH_BASE_URL=<API_BASE_URL>
VITE_UIPATH_ORG_NAME=<ORG_NAME>
VITE_UIPATH_TENANT_NAME=<TENANT_NAME>
VITE_UIPATH_CLIENT_ID=<CLIENT_ID>
VITE_UIPATH_SCOPE=OR.Jobs OR.Queues OR.Tasks OR.DataFabric OR.Folders openid profile
VITE_INSIGHTS_TENANT_ID=<TENANT_UUID>
EOF
echo ".env.local" >> .gitignore
npm install
npx shadcn@latest init --defaults --force
```

> **Note on SKILL_ROOT path:** The exact path to skill assets depends on how the plugin is installed. If the above path resolution fails, ask the user for the skills repo path or read from `~/.claude/plugins/cache/` directly.

## Phase 7 — Widget Generation (1 parallel Write block)
Read the appropriate widget template files from `../../assets/templates/dashboard/widgets/`.
For each widget in the approved plan, write one file to `<PROJECT_DIR>/src/widgets/`:
- Fill `<COMPONENT_NAME>` → PascalCase name (e.g. `AgentSuccessRate`)
- Fill `<DATA_HOOK>` → full `useInsights(...)` or SDK hook call with correct key
- Fill `<TITLE>` → human label from the plan
- Fill `<X_KEY>` / `<Y_KEY>` / `<COLUMNS>` → field names from the API's response structure (see insights-catalog.md for response shapes)

Write ALL widget files in a single message with parallel Write calls.

Also write `<PROJECT_DIR>/src/widgets/index.ts` exporting all components.

Also update `<PROJECT_DIR>/src/App.tsx` to import and render the widgets inside `DashboardShell`.

## Phase 8 — Validate + Summary (2 Bash)
```bash
# Validate TypeScript
cd <PROJECT_DIR> && tsc --noEmit
```
If errors → fix them before proceeding. Common fixes:
- Missing import → add import at top of file
- Type mismatch on `data` from `useInsights` → add `as <ExpectedType>` cast with a comment

```bash
# Smoke-test dev server starts
cd <PROJECT_DIR> && npm run dev &
sleep 4 && curl -s http://localhost:5173 | grep -q "root" && echo "SERVER_OK" && kill %1
```

Show summary:
```
Dashboard ready. Run `npm run dev` to preview at http://localhost:5173.

Widgets:
1. <Widget 1 name> — <one sentence description>
2. <Widget 2 name> — <one sentence description>
...

To deploy: say "deploy this dashboard" and I'll run the pack → publish → deploy pipeline.
```

## Incremental Mode (existing dashboard)
If a `<PROJECT_DIR>/src/widgets/` directory already exists:
1. Read all existing widget files before writing
2. Write ONLY new widget files (do not regenerate existing ones)
3. Update `index.ts` to add the new export
4. Run `tsc --noEmit` after addition

## Error Handling
- `npm install` fails → check Node version (`node --version`, needs ≥ 18)
- `shadcn init` fails → skip shadcn, continue with plain Tailwind classes
- `tsc --noEmit` type errors → fix errors; max 2 fix attempts before asking user
- Dev server fails to start → still report success with `tsc` passing; note server issue
```

- [ ] **Step 2: Commit**
```bash
git add skills/uipath-coded-apps/references/dashboards/plugins/build/impl.md
git commit -m "feat(coded-apps): add dashboard build plugin (8-phase pipeline)"
```

---

## Task 8: plugins/deploy/impl.md

**Files:**
- Create: `skills/uipath-coded-apps/references/dashboards/plugins/deploy/impl.md`

- [ ] **Step 1: Write the file**

```markdown
# Dashboard Deploy Plugin

## Pre-flight
1. Verify project has a `package.json` with a `build` script
2. Run: `npm run build`
   - If it fails → fix build errors before proceeding (see `../../debug.md` for common issues)
3. Bump `version` in `package.json` — re-publish without a version bump will fail

## Deploy Pipeline
Dashboard projects are standard Coded Web Apps. Follow the full pipeline:

→ Read [../../pack-publish-deploy.md](../../pack-publish-deploy.md) for all steps.

## Dashboard-specific Rules
- App type is always **Web** — never pass `-t Action` to `uip codedapp publish`
- The app name should match the dashboard title from the build plan
- After deploy, verify the live URL loads without auth errors before reporting success
- If the user has not yet created an OAuth external app, follow `../../oauth-client-setup.md`
```

- [ ] **Step 2: Verify the delegated link resolves**
```bash
ls skills/uipath-coded-apps/references/pack-publish-deploy.md
```
Expected: file exists.

- [ ] **Step 3: Commit**
```bash
git add skills/uipath-coded-apps/references/dashboards/plugins/deploy/impl.md
git commit -m "feat(coded-apps): add dashboard deploy plugin"
```

---

## Task 9: Scaffold — config files

**Files:**
- Create: `scaffold/package.json`, `scaffold/vite.config.ts`, `scaffold/tsconfig.json`, `scaffold/tsconfig.node.json`, `scaffold/tailwind.config.ts`, `scaffold/uipath.json`, `scaffold/index.html`, `scaffold/.env.example`, `scaffold/postcss.config.js`

All paths relative to `skills/uipath-coded-apps/assets/templates/dashboard/scaffold/`.

- [ ] **Step 1: package.json**
```json
{
  "name": "uipath-dashboard",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@uipath/uipath-typescript": "latest",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "recharts": "^2.12.0",
    "react-router-dom": "^6.23.0",
    "path-browserify": "^1.0.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.4.0",
    "vite": "^5.2.0"
  }
}
```

- [ ] **Step 2: vite.config.ts**

Mirror the existing `web-app-template.md` exactly — `base: './'`, `global: 'globalThis'`, `path-browserify`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './',
  define: {
    global: 'globalThis',
  },
  resolve: {
    alias: {
      path: 'path-browserify',
    },
  },
  optimizeDeps: {
    include: ['@uipath/uipath-typescript'],
  },
})
```

- [ ] **Step 3: tsconfig.json**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 4: tsconfig.node.json**
```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts", "tailwind.config.ts"]
}
```

- [ ] **Step 5: tailwind.config.ts**
```typescript
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: 'hsl(var(--card))',
        'card-foreground': 'hsl(var(--card-foreground))',
        primary: 'hsl(var(--primary))',
        'primary-foreground': 'hsl(var(--primary-foreground))',
        muted: 'hsl(var(--muted))',
        'muted-foreground': 'hsl(var(--muted-foreground))',
        border: 'hsl(var(--border))',
        destructive: 'hsl(var(--destructive))',
        'destructive-foreground': 'hsl(var(--destructive-foreground))',
      },
    },
  },
  plugins: [],
} satisfies Config
```

- [ ] **Step 6: postcss.config.js**
```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 7: uipath.json**
```json
{
  "scope": "OR.Jobs OR.Queues OR.Tasks OR.DataFabric OR.Folders openid profile",
  "clientId": ""
}
```
Note: `clientId` is left blank — filled in from `VITE_UIPATH_CLIENT_ID` at runtime via `App.tsx`.

- [ ] **Step 8: index.html**
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>UiPath Dashboard</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 9: .env.example**
```
VITE_UIPATH_BASE_URL=https://api.uipath.com
VITE_UIPATH_ORG_NAME=
VITE_UIPATH_TENANT_NAME=
VITE_UIPATH_CLIENT_ID=
VITE_UIPATH_SCOPE=OR.Jobs OR.Queues OR.Tasks OR.DataFabric OR.Folders openid profile
VITE_INSIGHTS_TENANT_ID=
```

- [ ] **Step 10: Commit**
```bash
git add skills/uipath-coded-apps/assets/templates/dashboard/scaffold/package.json \
        skills/uipath-coded-apps/assets/templates/dashboard/scaffold/vite.config.ts \
        skills/uipath-coded-apps/assets/templates/dashboard/scaffold/tsconfig.json \
        skills/uipath-coded-apps/assets/templates/dashboard/scaffold/tsconfig.node.json \
        skills/uipath-coded-apps/assets/templates/dashboard/scaffold/tailwind.config.ts \
        skills/uipath-coded-apps/assets/templates/dashboard/scaffold/postcss.config.js \
        skills/uipath-coded-apps/assets/templates/dashboard/scaffold/uipath.json \
        skills/uipath-coded-apps/assets/templates/dashboard/scaffold/index.html \
        skills/uipath-coded-apps/assets/templates/dashboard/scaffold/.env.example
git commit -m "feat(coded-apps): add dashboard scaffold config files"
```

---

## Task 10: Scaffold — src/index.css, main.tsx, App.tsx

**Files:**
- Create: `scaffold/src/index.css`, `scaffold/src/main.tsx`, `scaffold/src/App.tsx`

- [ ] **Step 1: src/index.css**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --border: 214.3 31.8% 91.4%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --radius: 0.5rem;
  }
}
```

- [ ] **Step 2: src/main.tsx**
```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

- [ ] **Step 3: src/App.tsx**
```tsx
import React from 'react'
import type { UiPathSDKConfig } from '@uipath/uipath-typescript/core'
import { AuthProvider, useAuth } from './hooks/useAuth'
import DashboardShell from './components/DashboardShell'

const sdkConfig: UiPathSDKConfig = {
  clientId: import.meta.env.VITE_UIPATH_CLIENT_ID as string,
  scopes: (import.meta.env.VITE_UIPATH_SCOPE as string).split(' '),
  organizationName: import.meta.env.VITE_UIPATH_ORG_NAME as string,
  tenantName: import.meta.env.VITE_UIPATH_TENANT_NAME as string,
  baseUrl: import.meta.env.VITE_UIPATH_BASE_URL as string,
}

function AppContent() {
  const { isAuthenticated, isLoading, login, error } = useAuth()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-muted-foreground text-sm">Loading…</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center space-y-4">
          {error && <p className="text-destructive text-sm">{error}</p>}
          <button
            onClick={() => void login()}
            className="rounded-md bg-primary px-6 py-2 text-primary-foreground text-sm font-medium hover:opacity-90"
          >
            Sign in with UiPath
          </button>
        </div>
      </div>
    )
  }

  return <DashboardShell />
}

export default function App() {
  return (
    <AuthProvider config={sdkConfig}>
      <AppContent />
    </AuthProvider>
  )
}
```

- [ ] **Step 4: Commit**
```bash
git add skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/
git commit -m "feat(coded-apps): add dashboard scaffold src entry files"
```

---

## Task 11: Scaffold — hooks (useAuth.ts, useInsights.ts)

**Files:**
- Create: `scaffold/src/hooks/useAuth.ts`
- Create: `scaffold/src/hooks/useInsights.ts`

- [ ] **Step 1: src/hooks/useAuth.ts**

Uses the SDK's built-in PKCE flow (same as `web-app-template.md`) and additionally stores the raw access token in a module-level ref so `getToken()` can serve Insights API calls.

```typescript
import React, { useState, useEffect, useRef, createContext, useContext, useCallback } from 'react'
import type { ReactNode } from 'react'
import { UiPath, UiPathError } from '@uipath/uipath-typescript/core'
import type { UiPathSDKConfig } from '@uipath/uipath-typescript/core'

interface AuthContextType {
  isAuthenticated: boolean
  isLoading: boolean
  sdk: UiPath
  tenantId: string
  login: () => Promise<void>
  logout: () => void
  getToken: () => Promise<string>
  error: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Module-level token cache for Insights API calls.
// Safe: single-page app, single session, in-memory only.
let _cachedToken: string | null = null

export const AuthProvider: React.FC<{ children: ReactNode; config: UiPathSDKConfig }> = ({
  children,
  config,
}) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sdk] = useState<UiPath>(() => new UiPath(config))
  const didInit = useRef(false)

  useEffect(() => {
    // Guard against React Strict Mode double-invoke — OAuth codes are single-use.
    if (didInit.current) return
    didInit.current = true

    const init = async () => {
      setIsLoading(true)
      setError(null)
      try {
        if (sdk.isInOAuthCallback()) {
          await sdk.completeOAuth()
          window.history.replaceState({}, document.title, window.location.pathname)
        }
        setIsAuthenticated(sdk.isAuthenticated())
      } catch (err) {
        setError(err instanceof UiPathError ? err.message : 'Authentication failed')
      } finally {
        setIsLoading(false)
      }
    }

    void init()
  }, [sdk])

  const login = useCallback(async () => {
    await sdk.login()
  }, [sdk])

  const logout = useCallback(() => {
    _cachedToken = null
    sdk.logout()
    setIsAuthenticated(false)
  }, [sdk])

  // getToken: used by InsightsClient for raw bearer token access.
  // Strategy: use the SDK's internal token manager via a lightweight probe request.
  // If the SDK exposes a public getAccessToken() method in future versions, prefer that.
  const getToken = useCallback(async (): Promise<string> => {
    if (_cachedToken) return _cachedToken
    // Probe: call a minimal SDK endpoint to trigger token refresh if needed,
    // then read from sessionStorage where the SDK persists it.
    const keys = Object.keys(sessionStorage)
    const tokenKey = keys.find(
      (k) => k.includes('access_token') || k.includes('accessToken')
    )
    if (tokenKey) {
      const raw = sessionStorage.getItem(tokenKey)
      if (raw) {
        try {
          // SDK may store JSON { value, expiry } or raw string
          const parsed = JSON.parse(raw) as { value?: string; access_token?: string }
          _cachedToken = parsed.value ?? parsed.access_token ?? raw
        } catch {
          _cachedToken = raw
        }
        if (_cachedToken) return _cachedToken
      }
    }
    throw new Error('Access token not available — ensure user is authenticated')
  }, [])

  const value: AuthContextType = {
    isAuthenticated,
    isLoading,
    sdk,
    tenantId: import.meta.env.VITE_INSIGHTS_TENANT_ID as string,
    login,
    logout,
    getToken,
    error,
  }

  return React.createElement(AuthContext.Provider, { value }, children)
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
```

> **Implementation note on `getToken`:** The SDK stores its OAuth token in `sessionStorage`. The exact key varies by SDK version. During first integration, open browser devtools → Application → Session Storage and find the key containing `access_token` after login. If the key pattern changes, update the `tokenKey` finder above or switch to using `sdk.getAccessToken()` if that method is added.

- [ ] **Step 2: src/hooks/useInsights.ts**

```typescript
import { useState, useEffect } from 'react'
import { useAuth } from './useAuth'
import { InsightsClient, type InsightsParams } from '../lib/insights-client'

type AgentsMethods    = keyof InsightsClient['agents']
type TraceviewMethods = keyof InsightsClient['traceview']
type GovernanceMethods = keyof InsightsClient['governance']
type JobsMethods      = keyof InsightsClient['jobs']

export type InsightsKey =
  | `agents.${AgentsMethods}`
  | `traceview.${TraceviewMethods}`
  | `governance.${GovernanceMethods}`
  | `jobs.${JobsMethods}`

export function useInsights<T>(
  key: InsightsKey,
  params: Omit<InsightsParams, 'tenantId'>,
  deps: unknown[] = []
) {
  const { getToken, tenantId } = useAuth()
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    const base    = import.meta.env.VITE_UIPATH_BASE_URL as string
    const org     = import.meta.env.VITE_UIPATH_ORG_NAME as string
    const tenant  = import.meta.env.VITE_UIPATH_TENANT_NAME as string
    const client  = new InsightsClient(
      `${base}/${org}/${tenant}/insightsrtm_`,
      `${base}/${org}/${tenant}`,
      getToken
    )

    const [ns, method] = key.split('.') as [
      'agents' | 'traceview' | 'governance' | 'jobs',
      string
    ]
    const fullParams: InsightsParams = { ...params, tenantId }
    const call = (client[ns] as Record<string, (p: InsightsParams) => Promise<T>>)[method]

    call(fullParams)
      .then((d) => { if (!cancelled) setData(d) })
      .catch((e: Error) => { if (!cancelled) setError(e) })
      .finally(() => { if (!cancelled) setLoading(false) })

    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, error, loading }
}
```

- [ ] **Step 3: Commit**
```bash
git add skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/hooks/
git commit -m "feat(coded-apps): add dashboard scaffold hooks (useAuth + useInsights)"
```

---

## Task 12: Scaffold — lib (insights-client.ts, sdk-client.ts) + components

**Files:**
- Create: `scaffold/src/lib/insights-client.ts`
- Create: `scaffold/src/lib/sdk-client.ts`
- Create: `scaffold/src/components/DashboardShell.tsx`
- Create: `scaffold/src/components/WidgetGrid.tsx`
- Create: `scaffold/src/components/MetricCard.tsx`

- [ ] **Step 1: src/lib/insights-client.ts**

This is the TypeScript implementation of the pattern documented in `primitives/insights-client.md`:
```typescript
export interface InsightsParams {
  tenantId: string
  startTime?: string
  endTime?: string
  limit?: number
  [key: string]: unknown
}

export class InsightsClient {
  constructor(
    private rtmBase: string,
    private jobsBase: string,
    private getToken: () => Promise<string>
  ) {}

  private async post<T>(base: string, path: string, body: InsightsParams): Promise<T> {
    const token = await this.getToken()
    const res = await fetch(`${base}/${path}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })
    if (res.status === 401) throw new Error('INSIGHTS_AUTH_EXPIRED')
    if (!res.ok) throw new Error(`Insights ${res.status}: ${path}`)
    return res.json() as Promise<T>
  }

  agents = {
    getSummaryV2:            (p: InsightsParams) => this.post(this.rtmBase, 'Agents/summaryV2', p),
    getErrors:               (p: InsightsParams) => this.post(this.rtmBase, 'Agents/errors', p),
    getTopErroredAgents:     (p: InsightsParams) => this.post(this.rtmBase, 'Agents/topErroredAgents', p),
    getIncidents:            (p: InsightsParams) => this.post(this.rtmBase, 'Agents/incidents', p),
    getIncidentDistribution: (p: InsightsParams) => this.post(this.rtmBase, 'Agents/incidentDistribution', p),
    getConsumption:          (p: InsightsParams) => this.post(this.rtmBase, 'Agents/consumption', p),
    getConsumptionTimeline:  (p: InsightsParams) => this.post(this.rtmBase, 'Agents/consumptionTimeline', p),
    getLatencyTimeline:      (p: InsightsParams) => this.post(this.rtmBase, 'Agents/latencyTimeline', p),
    getAgents:               (p: InsightsParams) => this.post(this.rtmBase, 'Agents/agents', p),
    getUnitConsumption:      (p: InsightsParams) => this.post(this.rtmBase, 'Agents/summary/unit-consumption', p),
    getNames:                (p: InsightsParams) => this.post(this.rtmBase, 'Agents/names', p),
  }

  traceview = {
    getLatencyTimeline:     (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/latencyTimeline', p),
    getErrorsTimeline:      (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/errorsTimeline', p),
    getMemoryTimeline:      (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/memoryTimeline', p),
    getMemoryCallsTimeline: (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/memoryCallsTimeline', p),
    getTopMemorySpaces:     (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/topMemorySpaces', p),
    getUnitConsumption:     (p: InsightsParams) => this.post(this.rtmBase, 'Traceview/unitConsumption', p),
  }

  governance = {
    getPolicySummary:     (p: InsightsParams & { policy: string }) =>
                            this.post(this.rtmBase, 'Governance/policy/summary', p),
    getPolicyTraces:      (p: InsightsParams) => this.post(this.rtmBase, 'Governance/policy/traces', p),
    getOperationSummary:  (p: InsightsParams) => this.post(this.rtmBase, 'Governance/operation/summary', p),
  }

  jobs = {
    getSummary:             (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/summary', p),
    getCompletedTimeline:   (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/completed-timeline', p),
    getUncompletedTimeline: (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/uncompleted-timeline', p),
    getTopFailures:         (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/top-failures', p),
    getFailuresByReason:    (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/failures-by-reason', p),
    getProcessDetails:      (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/process-details', p),
    getFailureDetails:      (p: InsightsParams) => this.post(this.jobsBase, 'api/v1.0/InsightsJobs/failure-details', p),
  }
}
```

- [ ] **Step 2: src/lib/sdk-client.ts**
```typescript
import { UiPath } from '@uipath/uipath-typescript/core'
import { Jobs } from '@uipath/uipath-typescript/jobs'
import { QueueItems } from '@uipath/uipath-typescript/queues'
import { Tasks } from '@uipath/uipath-typescript/tasks'
import { Entities } from '@uipath/uipath-typescript/entities'

export function createSdkServices(sdk: UiPath) {
  return {
    jobs:       new Jobs(sdk),
    queueItems: new QueueItems(sdk),
    tasks:      new Tasks(sdk),
    entities:   new Entities(sdk),
  }
}
```

- [ ] **Step 3: src/components/DashboardShell.tsx**
```tsx
import React from 'react'
import WidgetGrid from './WidgetGrid'

interface NavItem {
  label: string
  id: string
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Overview', id: 'overview' },
]

export default function DashboardShell() {
  const [active, setActive] = React.useState('overview')

  return (
    <div className="flex h-screen bg-background text-foreground">
      {/* Sidebar */}
      <aside className="w-56 border-r flex flex-col py-4 px-3 gap-1 shrink-0">
        <div className="text-sm font-semibold px-2 py-1 mb-2 text-muted-foreground uppercase tracking-wide">
          Dashboard
        </div>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => setActive(item.id)}
            className={`text-sm px-3 py-2 rounded-md text-left transition-colors ${
              active === item.id
                ? 'bg-primary text-primary-foreground'
                : 'hover:bg-muted text-foreground'
            }`}
          >
            {item.label}
          </button>
        ))}
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto p-6">
        <WidgetGrid />
      </main>
    </div>
  )
}
```

- [ ] **Step 4: src/components/WidgetGrid.tsx**
```tsx
import React from 'react'

interface WidgetGridProps {
  children?: React.ReactNode
}

export default function WidgetGrid({ children }: WidgetGridProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {children}
    </div>
  )
}
```

- [ ] **Step 5: src/components/MetricCard.tsx**
```tsx
import React from 'react'

interface MetricCardProps {
  title: string
  value: string | number
  delta?: string
  loading?: boolean
  error?: string | null
}

export default function MetricCard({ title, value, delta, loading, error }: MetricCardProps) {
  return (
    <div className="rounded-lg border bg-card p-4 space-y-1">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
        {title}
      </p>
      {loading ? (
        <div className="h-8 w-24 animate-pulse rounded bg-muted" />
      ) : error ? (
        <p className="text-sm text-destructive">{error}</p>
      ) : (
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-semibold">{value}</span>
          {delta && (
            <span className="text-xs text-muted-foreground">{delta}</span>
          )}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 6: Commit**
```bash
git add skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/lib/ \
        skills/uipath-coded-apps/assets/templates/dashboard/scaffold/src/components/
git commit -m "feat(coded-apps): add dashboard scaffold lib + components"
```

---

## Task 13: Widget templates

**Files:**
- Create: all 6 files in `assets/templates/dashboard/widgets/`

All paths relative to `skills/uipath-coded-apps/assets/templates/dashboard/widgets/`.

- [ ] **Step 1: area-chart.tsx**
```tsx
import React from 'react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
// IMPORT: import { useInsights } from '../hooks/useInsights'

export function <COMPONENT_NAME>() {
  const { data, loading, error } = <DATA_HOOK>

  if (loading) return <div className="h-64 animate-pulse rounded-lg bg-muted" />
  if (error) return <div className="rounded-lg border bg-card p-4 text-sm text-destructive">{error.message}</div>

  return (
    <div className="rounded-lg border bg-card p-4">
      <h3 className="mb-3 text-sm font-medium text-muted-foreground"><TITLE></h3>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data as Record<string, unknown>[]}>
          <XAxis dataKey="<X_KEY>" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Area
            dataKey="<Y_KEY>"
            fill="hsl(var(--primary))"
            stroke="hsl(var(--primary))"
            fillOpacity={0.2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
```

- [ ] **Step 2: bar-chart.tsx**
```tsx
import React from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
// IMPORT: import { useInsights } from '../hooks/useInsights'

export function <COMPONENT_NAME>() {
  const { data, loading, error } = <DATA_HOOK>

  if (loading) return <div className="h-64 animate-pulse rounded-lg bg-muted" />
  if (error) return <div className="rounded-lg border bg-card p-4 text-sm text-destructive">{error.message}</div>

  return (
    <div className="rounded-lg border bg-card p-4">
      <h3 className="mb-3 text-sm font-medium text-muted-foreground"><TITLE></h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data as Record<string, unknown>[]}>
          <XAxis dataKey="<X_KEY>" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey="<Y_KEY>" fill="hsl(var(--primary))" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
```

- [ ] **Step 3: donut-chart.tsx**
```tsx
import React from 'react'
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
// IMPORT: import { useInsights } from '../hooks/useInsights'

const COLORS = [
  'hsl(var(--primary))',
  'hsl(215 100% 60%)',
  'hsl(150 60% 50%)',
  'hsl(30 100% 60%)',
]

export function <COMPONENT_NAME>() {
  const { data, loading, error } = <DATA_HOOK>

  if (loading) return <div className="h-64 animate-pulse rounded-lg bg-muted" />
  if (error) return <div className="rounded-lg border bg-card p-4 text-sm text-destructive">{error.message}</div>

  const chartData = Array.isArray(data) ? data : Object.entries(data as Record<string, number>).map(([name, value]) => ({ name, value }))

  return (
    <div className="rounded-lg border bg-card p-4">
      <h3 className="mb-3 text-sm font-medium text-muted-foreground"><TITLE></h3>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie data={chartData as Record<string, unknown>[]} dataKey="<DATA_KEY>" nameKey="<NAME_KEY>" innerRadius={60} outerRadius={90}>
            {(chartData as Record<string, unknown>[]).map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
```

- [ ] **Step 4: kpi-card.tsx**
```tsx
import React from 'react'
import MetricCard from '../components/MetricCard'
// IMPORT: import { useInsights } from '../hooks/useInsights'

export function <COMPONENT_NAME>() {
  const { data, loading, error } = <DATA_HOOK>

  const value = data ? String((data as Record<string, unknown>)['<VALUE_KEY>'] ?? '—') : '—'

  return (
    <MetricCard
      title="<TITLE>"
      value={value}
      loading={loading}
      error={error?.message}
    />
  )
}
```

- [ ] **Step 5: line-chart.tsx**
```tsx
import React from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
// IMPORT: import { useInsights } from '../hooks/useInsights'

export function <COMPONENT_NAME>() {
  const { data, loading, error } = <DATA_HOOK>

  if (loading) return <div className="h-64 animate-pulse rounded-lg bg-muted" />
  if (error) return <div className="rounded-lg border bg-card p-4 text-sm text-destructive">{error.message}</div>

  return (
    <div className="rounded-lg border bg-card p-4">
      <h3 className="mb-3 text-sm font-medium text-muted-foreground"><TITLE></h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data as Record<string, unknown>[]}>
          <XAxis dataKey="<X_KEY>" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Line dataKey="<Y_KEY>" stroke="hsl(var(--primary))" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
```

- [ ] **Step 6: data-table.tsx**
```tsx
import React, { useState } from 'react'
// IMPORT: import { useInsights } from '../hooks/useInsights'

// COLUMNS format: [{ key: 'fieldName', label: 'Column Header' }, ...]
const COLUMNS: { key: string; label: string }[] = <COLUMNS>

const PAGE_SIZE = 25

export function <COMPONENT_NAME>() {
  const { data, loading, error } = <DATA_HOOK>
  const [page, setPage] = useState(0)

  if (loading) return <div className="h-40 animate-pulse rounded-lg bg-muted" />
  if (error) return <div className="rounded-lg border bg-card p-4 text-sm text-destructive">{error.message}</div>

  const rows = Array.isArray(data) ? data as Record<string, unknown>[] : []
  const totalPages = Math.ceil(rows.length / PAGE_SIZE)
  const pageRows = rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <div className="rounded-lg border bg-card col-span-full overflow-hidden">
      <div className="px-4 py-3 border-b">
        <h3 className="text-sm font-medium text-muted-foreground"><TITLE></h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/50">
            <tr>
              {COLUMNS.map((c) => (
                <th key={c.key} className="px-4 py-2 text-left font-medium text-muted-foreground whitespace-nowrap">
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr key={i} className="border-b last:border-0 hover:bg-muted/30">
                {COLUMNS.map((c) => (
                  <td key={c.key} className="px-4 py-2 max-w-xs truncate">
                    {String(row[c.key] ?? '—')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-2 border-t text-xs text-muted-foreground">
          <span>
            Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, rows.length)} of {rows.length}
          </span>
          <div className="flex gap-2">
            <button disabled={page === 0} onClick={() => setPage(p => p - 1)}
              className="px-2 py-1 rounded border disabled:opacity-40">Prev</button>
            <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)}
              className="px-2 py-1 rounded border disabled:opacity-40">Next</button>
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 7: Commit**
```bash
git add skills/uipath-coded-apps/assets/templates/dashboard/widgets/
git commit -m "feat(coded-apps): add 6 dashboard widget templates"
```

---

## Task 14: discover-capabilities.mjs

**Files:**
- Create: `skills/uipath-coded-apps/assets/scripts/discover-capabilities.mjs`

- [ ] **Step 1: Write the script**
```javascript
#!/usr/bin/env node
// Reads the static insights-catalog.md and optionally enriches it with live
// DataFabric entity names from the active uip login session.
// Usage: node discover-capabilities.mjs [--output json]
// Output: prints the catalog summary; non-zero exit if login is invalid.

import { execSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const CATALOG_PATH = join(__dirname, '../templates/dashboard/insights-catalog.md')

function getLoginStatus() {
  try {
    const raw = execSync('uip login status --output json', { encoding: 'utf8', stdio: ['pipe','pipe','pipe'] })
    return JSON.parse(raw)
  } catch {
    return null
  }
}

const status = getLoginStatus()
if (!status?.isLoggedIn) {
  console.error('Not logged in — run `uip login` first')
  process.exit(1)
}

const catalog = readFileSync(CATALOG_PATH, 'utf8')
const namespaces = ['Agents', 'Traceview', 'Governance', 'Jobs']
const counts = {}
for (const ns of namespaces) {
  const matches = catalog.match(new RegExp(`\\b${ns}\\b`, 'g'))
  counts[ns] = matches ? matches.length : 0
}

const result = {
  org: status.accountName,
  tenant: status.tenantName,
  tenantId: status.tenantId ?? '(resolve from .auth file)',
  catalogFile: CATALOG_PATH,
  namespaceCoverage: counts,
  status: 'ready',
}

if (process.argv.includes('--output') && process.argv.includes('json')) {
  console.log(JSON.stringify(result, null, 2))
} else {
  console.log(`Insights catalog loaded for ${result.org}/${result.tenant}`)
  console.log(`Namespaces: ${Object.entries(counts).map(([k,v]) => `${k}(${v})`).join(', ')}`)
  console.log(`tenantId: ${result.tenantId}`)
}
```

- [ ] **Step 2: Verify it parses cleanly**
```bash
node --input-type=module < skills/uipath-coded-apps/assets/scripts/discover-capabilities.mjs --help 2>&1 | head -3 || echo "Script syntax OK"
```

- [ ] **Step 3: Commit**
```bash
git add skills/uipath-coded-apps/assets/scripts/discover-capabilities.mjs
git commit -m "feat(coded-apps): add discover-capabilities.mjs script"
```

---

## Task 15: Remaining eval tasks

**Files:**
- Create: `tests/tasks/uipath-coded-apps/dashboard/dashboard_disambiguate.yaml`
- Create: `tests/tasks/uipath-coded-apps/dashboard/dashboard_incremental.yaml`

- [ ] **Step 1: Write dashboard_disambiguate.yaml**
```yaml
task_id: uipath-coded-apps-dashboard-disambiguate
description: >
  Validates that an ambiguous prompt triggers the Apps vs Dashboards
  disambiguation question before any action is taken.
tags: [uipath-coded-apps, activation, dashboard]

sandbox:
  driver: tempdir
  node: {}

initial_prompt: |
  I need to create something to track my automation performance.

success_criteria:
  - type: command_executed
    description: "Agent asks disambiguation question — no files written before question"
    tool_name: "AskUserQuestion"
    command_pattern: '.*'
    min_count: 1
    weight: 2.0
    pass_threshold: 1.0

  - type: file_exists
    description: "No package.json created before disambiguation"
    path: "package.json"
    weight: 1.0
    pass_threshold: 0.0
    invert: true
```

- [ ] **Step 2: Write dashboard_incremental.yaml**
```yaml
task_id: uipath-coded-apps-dashboard-incremental
description: >
  Validates that adding a widget to an existing dashboard only writes the
  new widget file and does not re-scaffold the entire project.
tags: [uipath-coded-apps, smoke, dashboard]

sandbox:
  driver: tempdir
  node: {}
  setup: |
    mkdir -p src/widgets
    echo '{"name":"my-dashboard","version":"1.0.0"}' > package.json
    echo 'export {}' > src/widgets/index.ts

initial_prompt: |
  Add a widget to my existing dashboard showing governance violations
  over the last 30 days. The dashboard is at the current directory.

  Do NOT ask for approval, confirmation, or feedback.
  Before starting, load the uipath-coded-apps skill and follow its workflow.

success_criteria:
  - type: file_exists
    description: "New governance widget file created"
    path: "src/widgets"
    weight: 2.0
    pass_threshold: 1.0

  - type: file_contains
    description: "New widget uses governance Insights endpoint"
    path: "src/widgets"
    pattern: "governance\\.get"
    weight: 2.0
    pass_threshold: 1.0

  - type: command_executed
    description: "tsc --noEmit ran after adding widget"
    tool_name: "Bash"
    command_pattern: 'tsc\s+--noEmit'
    min_count: 1
    weight: 1.0
    pass_threshold: 1.0
```

- [ ] **Step 3: Commit**
```bash
git add tests/tasks/uipath-coded-apps/dashboard/
git commit -m "test: add dashboard disambiguate + incremental eval tasks"
```

---

## Task 16: Final validation + link check

**Files:**
- Verify: all new files exist and all relative links in SKILL.md and CAPABILITY.md resolve

- [ ] **Step 1: Run description-length validator**
```bash
bash C:\Work\skills\hooks\validate-skill-descriptions.sh
```
Expected: no errors.

- [ ] **Step 2: Verify all referenced files exist**
```bash
# Check all links in CAPABILITY.md resolve
ls skills/uipath-coded-apps/references/dashboards/plugins/build/impl.md
ls skills/uipath-coded-apps/references/dashboards/plugins/deploy/impl.md
ls skills/uipath-coded-apps/references/dashboards/primitives/auth-context.md
ls skills/uipath-coded-apps/references/dashboards/primitives/build-plan.md
ls skills/uipath-coded-apps/references/dashboards/primitives/data-router.md
ls skills/uipath-coded-apps/references/dashboards/primitives/insights-client.md
ls skills/uipath-coded-apps/references/dashboards/insights-catalog.md
# Check deploy link
ls skills/uipath-coded-apps/references/pack-publish-deploy.md
# Check widget templates
ls skills/uipath-coded-apps/assets/templates/dashboard/widgets/area-chart.tsx
ls skills/uipath-coded-apps/assets/templates/dashboard/widgets/bar-chart.tsx
ls skills/uipath-coded-apps/assets/templates/dashboard/widgets/donut-chart.tsx
ls skills/uipath-coded-apps/assets/templates/dashboard/widgets/kpi-card.tsx
ls skills/uipath-coded-apps/assets/templates/dashboard/widgets/line-chart.tsx
ls skills/uipath-coded-apps/assets/templates/dashboard/widgets/data-table.tsx
```
Expected: all files exist, no errors.

- [ ] **Step 3: Verify scaffold TypeScript is valid (dry run)**
```bash
cd skills/uipath-coded-apps/assets/templates/dashboard/scaffold
npm install --ignore-scripts 2>&1 | tail -3
npx tsc --noEmit 2>&1 | head -20
```
Expected: `tsc --noEmit` exits 0. If errors appear, fix them before committing.

- [ ] **Step 4: Final commit**
```bash
git add .
git commit -m "feat(coded-apps): complete dashboard generation capability

- SKILL.md: new description, disambiguation block, nav row
- references/dashboards/: CAPABILITY.md, 2 plugins, 4 primitives, insights-catalog
- assets/templates/dashboard/: scaffold (15 files) + 6 widget templates
- assets/scripts/: discover-capabilities.mjs
- tests/tasks/: 3 eval tasks (build, disambiguate, incremental)

Insights API: 4-namespace HTTP client (agents, traceview, governance, jobs)
Base URL: VITE_UIPATH_BASE_URL (alpha/staging/prod) + org/tenant/insightsrtm_
Migration path: swap InsightsClient for SDK when uipath-typescript/insights ships"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** All 9 spec sections have tasks: SKILL.md edits (Task 2), CAPABILITY.md (Task 3), primitives (Tasks 4–6), plugins (Tasks 7–8), scaffold (Tasks 9–12), widget templates (Task 13), discovery script (Task 14), eval tasks (Tasks 1+15)
- [x] **No placeholders:** Every step has exact file content or exact commands
- [x] **Type consistency:** `InsightsParams` defined in Task 12 (`insights-client.ts`), imported in Task 11 (`useInsights.ts`) — types match. `InsightsClient` namespace structure consistent across primitive doc (Task 6) and TypeScript file (Task 12). `UiPathSDKConfig` prop passed from `App.tsx` (Task 10) to `AuthProvider` (Task 11) — matches
- [x] **Env var alignment:** `VITE_UIPATH_ORG_NAME` / `VITE_UIPATH_TENANT_NAME` used consistently (matching `web-app-template.md`) across scaffold files, `.env.example`, build plugin, and auth context
- [x] **Eval task schema:** All 3 tasks follow the `test-task-template.yaml` schema (`task_id`, `description`, `tags`, `sandbox`, `initial_prompt`, `success_criteria`)
- [x] **`@uipath/cli` not in env_packages:** All 3 eval tasks use `sandbox: { node: {} }` — no `@uipath/cli` listed per task-authoring rules
