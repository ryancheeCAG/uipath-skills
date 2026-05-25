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
Check `Data.Status == "Logged in"`. If not → stop, tell user to run `uip login`.

Extract from response (fields are under `Data.`, not top-level):
- `Data.Organization` → ORG
- `Data.Tenant` → TENANT
- `Data.BaseUrl` → CLOUD_BASE_URL (e.g. `https://alpha.uipath.com`)

**No `tenantId` in this output.** Read PAT and TENANT_ID from `~/.uipath/.auth`
as described in `../../primitives/auth-context.md` Steps 3–4.

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
Read PAT and tenantId from `~/.uipath/.auth` (env-file format) as described in `../../primitives/auth-context.md` Step 3. Then copy the scaffold template and write `.env.local`:

```bash
SKILL_ASSETS="$(node -e "console.log(require.resolve('@uipath/cli/package.json').replace('/package.json',''))")/../../skills/uipath-coded-apps/assets"

# Read token from .auth file (env-file format)
PAT=$(grep -m1 '^UIPATH_ACCESS_TOKEN=' ~/.uipath/.auth | cut -d'=' -f2-)
TENANT_ID=$(grep -m1 '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
# Fallback: JSON format
if [ -z "$PAT" ]; then
  PAT=$(node -e "const a=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.uipath/.auth','utf8')); console.log(a.UIPATH_ACCESS_TOKEN||a.access_token||'')" 2>/dev/null)
  TENANT_ID=$(node -e "const a=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.uipath/.auth','utf8')); console.log(a.UIPATH_TENANT_ID||a.tenantId||'')" 2>/dev/null)
fi

# Derive API base URL (insert "api." subdomain) from DATA_BASE_URL
if echo "$DATA_BASE_URL" | grep -q "alpha";    then API_BASE_URL="https://alpha.api.uipath.com"
elif echo "$DATA_BASE_URL" | grep -q "staging"; then API_BASE_URL="https://staging.api.uipath.com"
else API_BASE_URL="https://api.uipath.com"
fi

cp -r "${SKILL_ASSETS}/templates/dashboard/scaffold/." <PROJECT_DIR>/
cd <PROJECT_DIR>
cat > .env.local << EOF
VITE_UIPATH_CLOUD_URL=${DATA_BASE_URL}
VITE_UIPATH_BASE_URL=${API_BASE_URL}
VITE_UIPATH_ORG_NAME=<ORG_NAME>
VITE_UIPATH_TENANT_NAME=<TENANT_NAME>
VITE_INSIGHTS_TENANT_ID=${TENANT_ID}
VITE_UIPATH_PAT=${PAT}
EOF
npm ci
```

No client ID, no scope, no OAuth setup required. The PAT comes from the active `uip login` session. For production deployment the PAT is stripped before build (failBuildIfPatSet Vite plugin enforces this).

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
- `npm ci` fails with network error → retry once; if still failing check internet connectivity
- `tsc --noEmit` errors → fix; max 2 fix attempts before asking user
- Dev server fails → still report success with `tsc` passing; note server issue
