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
