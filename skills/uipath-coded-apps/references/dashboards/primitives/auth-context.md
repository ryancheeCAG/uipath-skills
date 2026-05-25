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
