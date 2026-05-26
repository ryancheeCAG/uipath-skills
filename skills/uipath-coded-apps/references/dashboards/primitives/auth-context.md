# Auth Context Resolution

Read BEFORE any SDK or Insights API call.

## Step 1 — Verify login
```bash
uip login status --output json
```
Check `Data.Status == "Logged in"`. If not → stop, tell user to run `uip login`.

Actual output shape:
```json
{
  "Result": "Success",
  "Data": {
    "Status": "Logged in",
    "BaseUrl": "https://alpha.uipath.com",
    "Organization": "<ORG_NAME>",
    "Tenant": "<TENANT_NAME>",
    "Expiration Date": "2026-05-25T13:35:25.000Z"
  }
}
```
Fields: `Data.Organization` → ORG, `Data.Tenant` → TENANT, `Data.BaseUrl` → cloud URL.
There is **no `tenantId` in this output** — read it from `~/.uipath/.auth` in Step 3.

## Step 2 — Extract ORG and TENANT
```bash
STATUS=$(uip login status --output json)
ORG=$(echo "$STATUS"    | node -e "process.stdout.write(JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')).Data.Organization)")
TENANT=$(echo "$STATUS" | node -e "process.stdout.write(JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')).Data.Tenant)")
DATA_BASE_URL=$(echo "$STATUS" | node -e "process.stdout.write(JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')).Data.BaseUrl)")
```

## Step 3 — Read PAT and tenantId from ~/.uipath/.auth

The `.auth` file is env-file format (`KEY=VALUE` lines, not JSON):
```bash
# Read access token (still needed for tenantId context; no longer written to .env.local)
PAT=$(grep -m1 '^UIPATH_ACCESS_TOKEN=' ~/.uipath/.auth | cut -d'=' -f2-)

# Read tenant UUID (used as VITE_INSIGHTS_TENANT_ID)
TENANT_ID=$(grep -m1 '^UIPATH_TENANT_ID=' ~/.uipath/.auth | cut -d'=' -f2-)
```

Fallback — some CLI versions write JSON:
```bash
if [ -z "$PAT" ]; then
  PAT=$(node -e "const a=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.uipath/.auth','utf8')); console.log(a.UIPATH_ACCESS_TOKEN||a.access_token||'')" 2>/dev/null)
  TENANT_ID=$(node -e "const a=JSON.parse(require('fs').readFileSync(process.env.HOME+'/.uipath/.auth','utf8')); console.log(a.UIPATH_TENANT_ID||a.tenantId||'')" 2>/dev/null)
fi
```

Try env-file first; fall back to JSON if `$PAT` is empty.

## Step 4 — Derive base URLs from Data.BaseUrl

Two separate base URLs are needed (Insights RTM ≠ SDK API):

```bash
# Cloud URL: used for Insights RTM  (e.g. https://alpha.uipath.com)
CLOUD_BASE_URL="${DATA_BASE_URL}"

# API URL: used for TS SDK calls — insert "api." subdomain
if echo "$DATA_BASE_URL" | grep -q "alpha";   then API_BASE_URL="https://alpha.api.uipath.com"
elif echo "$DATA_BASE_URL" | grep -q "staging"; then API_BASE_URL="https://staging.api.uipath.com"
else API_BASE_URL="https://api.uipath.com"
fi
```

| Env var | Value | Used for |
|---|---|---|
| `VITE_UIPATH_CLOUD_URL` | `https://alpha.uipath.com` | Insights RTM base (`/ORG/TENANT/insightsrtm_`) |
| `VITE_UIPATH_BASE_URL` | `https://alpha.api.uipath.com` | TS SDK base URL |

## Error handling
- `Data.Status != "Logged in"` → tell user to run `uip login`, stop
- `PAT` is empty after both parse attempts → warn user (tenantId may still be available); PAT is no longer required for dashboard auth
- `TENANT_ID` is empty → Insights calls will 400 but SDK calls still work; warn user
