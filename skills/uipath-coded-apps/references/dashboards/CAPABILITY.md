# Dashboard Capability — Entry Point

Build or edit a Coded Web App dashboard powered by Insights RTM and the UiPath TypeScript SDK.

## When to use this capability

- User asks for a dashboard, chart, report, or metric visualization
- User asks to "add/remove/change" widgets on an existing dashboard

## Critical Rules

1. Read `primitives/tier-resolution.md` BEFORE classifying any metric — do not guess tiers from memory.
2. Fire pre-warm before showing the plan — hidden from user.
3. Always use plain English in the plan — no API names, no tier labels.
4. HALT after plan — do not build until user confirms.
5. Parse EVERY build script output line — miss a T3_RETRY and the build exits with code 2.
6. Never auto-deploy — deploy requires explicit user confirmation.

## Plugin Router

| User intent | Plugin |
|-------------|--------|
| Build new dashboard | `plugins/build/impl.md` |
| Edit existing dashboard | `primitives/incremental-editor.md` |
| Deploy dashboard | `plugins/deploy/impl.md` |

## Reference Navigation

| Doc | Purpose |
|-----|---------|
| `primitives/tier-resolution.md` | T1/T2/T3 classification rules + hard-refuse list |
| `primitives/build-plan.md` | intent.json schema + routing name rules |
| `primitives/auth-context.md` | How to extract org/tenant/tenantId from uip login |
| `primitives/state-file.md` | .dashboard/state.json schema |
| `primitives/incremental-editor.md` | edit-intent.json schema + ADD/REMOVE/CHANGE flow |
| `primitives/insights-client.md` | Temporary Insights HTTP client (until SDK ships) |
| `aesthetic/layout-patterns.md` | 10 immutable layout rules |
| `aesthetic/charting.md` | Chart type selection guide |
| `sdk-capabilities.md` | Full capability registry with aliases |
