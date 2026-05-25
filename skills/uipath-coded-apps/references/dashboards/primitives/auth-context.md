# Auth Context Resolution

Read BEFORE any SDK or Insights API call.

## Step 1 — Verify login
```bash
uip login status --output json
```
If `isLoggedIn` is false → stop, tell user to run `uip login`.

## Step 2 — Extract org / tenant
```json
{
  "isLoggedIn": true,
  "accountName": "<ORG_NAME>",
  "tenantName": "<TENANT_NAME>",
  "userId": "<USER_UUID>"
}
```

## Step 3 — Read PAT and tenantId from ~/.uipath/.auth

The `.auth` file is env-file format (`KEY=VALUE` lines, not JSON):
```bash
# Read access token (used as VITE_UIPATH_PAT in .env.local)
PAT=$(grep -m1 '^UIPATH_ACCESS_TOKEN=' ~/.uipath/.auth | cut -d'=' -f2-)

# Read tenant UUID (used as VITE_INSIGHTS_TENANT_ID)
TENANT_ID=$(grep -m1 '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
```

If the file is JSON (some CLI versions): parse with node:
```bash
PAT=$(node -e "const a=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.uipath/.auth','utf8')); console.log(a.UIPATH_ACCESS_TOKEN||a.access_token||'')")
TENANT_ID=$(node -e "const a=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.uipath/.auth','utf8')); console.log(a.UIPATH_TENANT_ID||a.tenantId||'')")
```

Try the env-file approach first; fall back to JSON if `$PAT` is empty.

## Step 4 — Detect environment from login URL

```bash
uip login status --output json
```
Inspect the `url` or `cloudUrl` field:
```
contains "alpha"   → VITE_UIPATH_BASE_URL=https://alpha.api.uipath.com
contains "staging" → VITE_UIPATH_BASE_URL=https://staging.api.uipath.com
otherwise          → VITE_UIPATH_BASE_URL=https://api.uipath.com
```

## Error handling
- `isLoggedIn: false` → tell user to run `uip login`, stop
- `PAT` is empty after both parse attempts → tell user to re-run `uip login`, stop
- `TENANT_ID` is empty → use empty string for now; Insights calls will 400 but SDK calls still work
