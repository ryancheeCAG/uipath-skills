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
SKILL_ASSETS="$(node -e "console.log(require.resolve('@uipath/cli/package.json').replace('/package.json',''))")/../../skills/uipath-coded-apps/assets"
cp -r "${SKILL_ASSETS}/templates/dashboard/scaffold/." <PROJECT_DIR>/
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
npm ci
```

> **Note on `npm ci`:** The scaffold template ships a committed `package-lock.json`, so `npm ci` skips version resolution and runs ~2× faster than `npm install`. If the lockfile is absent for any reason, fall back to `npm install`.

> **Note on SKILL_ASSETS path:** If the path resolution fails, ask the user for the path to the skills repo `assets/` directory and substitute directly.

## Phase 7 — Widget Generation (1 parallel Write block)
Read the appropriate widget template files from `../../assets/templates/dashboard/widgets/`.
For each widget in the approved plan, write one file to `<PROJECT_DIR>/src/widgets/`:
- Fill `<COMPONENT_NAME>` → PascalCase name (e.g. `AgentSuccessRate`)
- Fill `<DATA_HOOK>` → full `useInsights(...)` or SDK hook call with correct key
- Fill `<TITLE>` → human label from the plan
- Fill `<X_KEY>` / `<Y_KEY>` / `<COLUMNS>` → field names from the API response structure (see insights-catalog.md)

Write ALL widget files in a single message with parallel Write calls.
Also write `<PROJECT_DIR>/src/widgets/index.ts` exporting all components.
Update `<PROJECT_DIR>/src/App.tsx` to import and render the widgets inside `DashboardShell`.

## Phase 8 — Validate + Summary (2 Bash)
```bash
cd <PROJECT_DIR> && tsc --noEmit
```
If errors → fix them before proceeding. Common fixes:
- Missing import → add import at top of file
- Type mismatch on `data` → add `as <ExpectedType>` cast

```bash
cd <PROJECT_DIR> && npm run dev &
sleep 4 && curl -s http://localhost:5173 | grep -q "root" && echo "SERVER_OK" && kill %1
```

Show summary:
```
Dashboard ready. Run `npm run dev` to preview at http://localhost:5173.

Widgets:
1. <Widget 1 name> — <one sentence description>
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
- `npm ci` fails with "missing package-lock.json" → fall back to `npm install`
- `npm ci` fails with 401/403 → check `GH_NPM_REGISTRY_TOKEN` is set (needed for `@uipath/uipath-typescript`)
- `tsc --noEmit` errors → fix; max 2 fix attempts before asking user
- Dev server fails → still report success with `tsc` passing; note server issue
