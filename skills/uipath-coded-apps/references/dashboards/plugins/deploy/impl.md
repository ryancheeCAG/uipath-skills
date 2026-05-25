# Dashboard Deploy Plugin

Deploys a built dashboard to Automation Cloud as a Coded Web App.

## Pre-flight

```bash
# 1. Verify login
uip login status --output json   # must show Data.Status == "Logged in"

# 2. Read state.json (must exist — run build first if missing)
STATE=$(cat .dashboard/state.json 2>/dev/null || echo '{}')
APP_NAME=$(node -e "const s=JSON.parse(process.env.STATE||'{}'); console.log(s.app?.name||'')" STATE="$STATE")
ROUTING_NAME=$(node -e "const s=JSON.parse(process.env.STATE||'{}'); console.log(s.app?.routingName||'')" STATE="$STATE")
SEMVER=$(node -e "const s=JSON.parse(process.env.STATE||'{}'); console.log(s.app?.semver||'1.0.0')" STATE="$STATE")
SYSTEM_NAME=$(node -e "const s=JSON.parse(process.env.STATE||'{}'); console.log(s.deployment?.systemName||'')" STATE="$STATE")
FOLDER_KEY=$(node -e "const s=JSON.parse(process.env.STATE||'{}'); console.log(s.deployment?.folderKey||'')" STATE="$STATE")
```

If `ROUTING_NAME` is empty → state.json is missing or corrupt. Tell user to run the build first.

## Step 1 — Classify deploy type

- `SYSTEM_NAME` empty → **Fresh deploy** (first time this dashboard is deployed)
- `SYSTEM_NAME` non-empty → **Upgrade deploy** (update existing deployment)

## Step 2 — Resolve folder key

If `FOLDER_KEY` is empty (fresh deploy or folder lost):

```bash
# --all is required — without it the list is capped at 50 and may miss folders
uip or folders list --all --output json
```

Present the list to the user. Ask: "Which folder should this dashboard live in?"

> **Note:** `--all` bypasses the 50-item default cap. If the org has many folders, response may be slow — this is expected.

Once the user confirms a folder name:
```bash
FOLDER_KEY=$(uip or folders list --all --output json | node -e "
  const data = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  const match = data.find(f => f.Name === '<FOLDER_NAME>');
  if (!match) { console.error('Folder not found'); process.exit(1); }
  console.log(match.Key);
")
```

## Step 3 — Bump version

```bash
NEXT_SEMVER=$(node -e "
  const [major, minor, patch] = '<SEMVER>'.split('.').map(Number);
  console.log([major, minor, patch + 1].join('.'));
")
```

**Version pre-check** — avoid a publish 409 by confirming this version doesn't exist yet:
```bash
EXISTING=$(uip codedapp list --output json 2>/dev/null | \
  node -e "const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')); \
    const pkg=d.find(p=>p.Name==='${ROUTING_NAME}' && p.Version==='${NEXT_SEMVER}'); \
    console.log(pkg?'EXISTS':'OK')" 2>/dev/null || echo "SKIP")
if [ "${EXISTING}" = "EXISTS" ]; then
  # Auto-bump to next patch
  NEXT_SEMVER=$(node -e "const [a,b,c]='${NEXT_SEMVER}'.split('.').map(Number); console.log([a,b,c+1].join('.'))")
fi
```

## Step 4 — Show plan + confirm

Show the user:
```
Deploy plan:
  Dashboard:    <APP_NAME>
  Version:      <SEMVER> → <NEXT_SEMVER>
  Routing name: <ROUTING_NAME>
  Type:         Fresh deploy  OR  Upgrade (<SYSTEM_NAME>)
  Folder:       <folder name> (key: <FOLDER_KEY>)
```

Ask: **"Confirm deploy?"** — wait for `y` before proceeding.

## Step 5 — Production build (strip PAT)

Temporarily move `.env.local` so PAT doesn't enter the bundle.
Restore it regardless of build success or failure:

```bash
cd <PROJECT_DIR>
[ -f .env.local ] && mv .env.local .env.local.deploy-bak
npm run build
BUILD_EXIT=$?
# Restore unconditionally — runs on success AND failure
[ -f .env.local.deploy-bak ] && mv .env.local.deploy-bak .env.local
[ $BUILD_EXIT -ne 0 ] && echo "BUILD_FAILED" && exit 1
```

## Step 6 — Pack

`-n` here is the **routing slug** (package identifier, not display name):

```bash
uip codedapp pack dist \
  -n "${ROUTING_NAME}" \
  -v "${NEXT_SEMVER}" \
  --output json
```

## Step 7 — Publish (with transient-error retry)

`-n` here is the **routing slug** (same as pack):

```bash
for ATTEMPT in 1 2 3 4; do
  PUBLISH_OUT=$(uip codedapp publish \
    -n "${ROUTING_NAME}" \
    -v "${NEXT_SEMVER}" \
    --output json 2>&1)
  PUBLISH_EXIT=$?

  # Success
  [ $PUBLISH_EXIT -eq 0 ] && break

  # 409 version conflict — increment version and retry
  if echo "${PUBLISH_OUT}" | grep -q "409\|already exists"; then
    NEXT_SEMVER=$(node -e "const [a,b,c]='${NEXT_SEMVER}'.split('.').map(Number); console.log([a,b,c+1].join('.'))")
    # Re-pack with new version before retrying publish
    uip codedapp pack dist -n "${ROUTING_NAME}" -v "${NEXT_SEMVER}" --output json
    continue
  fi

  # Transient Cloudflare errors (520/522/524) or HTML response — wait and retry
  if echo "${PUBLISH_OUT}" | grep -qE "5[0-9]{2}|<!DOCTYPE|<html"; then
    WAIT=$((ATTEMPT * 5))
    sleep $WAIT
    continue
  fi

  # Non-retryable error
  echo "Publish failed: ${PUBLISH_OUT}" && exit 1
done
[ $PUBLISH_EXIT -ne 0 ] && echo "Publish failed after 4 attempts" && exit 1

# Extract deployVersion from publish response (needed for upgrade state tracking)
DEPLOY_VERSION=$(echo "${PUBLISH_OUT}" | node -e "
  const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  console.log(d.DeploymentVersion || d.deploymentVersion || '');
" 2>/dev/null || echo "")
```

## Step 8 — Deploy

`-n` here is the **friendly display name** (shown in Orchestrator app catalog):

```bash
DEPLOY_OUT=$(uip codedapp deploy \
  -n "${APP_NAME}" \
  --routing-name "${ROUTING_NAME}" \
  --folder-key "${FOLDER_KEY}" \
  --output json 2>&1)
DEPLOY_EXIT=$?

# Routing-name collision — regenerate suffix and retry (up to 3 times)
COLLISION_ATTEMPTS=0
while echo "${DEPLOY_OUT}" | grep -qiE "conflict|already.*exist|routing.*name" && [ $COLLISION_ATTEMPTS -lt 3 ]; do
  COLLISION_ATTEMPTS=$((COLLISION_ATTEMPTS+1))
  NEW_SUFFIX=$(node -e "process.stdout.write(Math.random().toString(36).slice(2,6))")
  NEW_ROUTING=$(echo "${ROUTING_NAME}" | sed "s/-[a-z0-9]*$/-${NEW_SUFFIX}/")
  # Update routing name and re-pack + re-publish + re-deploy with new slug
  uip codedapp pack dist -n "${NEW_ROUTING}" -v "${NEXT_SEMVER}" --output json
  uip codedapp publish -n "${NEW_ROUTING}" -v "${NEXT_SEMVER}" --output json
  DEPLOY_OUT=$(uip codedapp deploy \
    -n "${APP_NAME}" \
    --routing-name "${NEW_ROUTING}" \
    --folder-key "${FOLDER_KEY}" \
    --output json 2>&1)
  DEPLOY_EXIT=$?
  [ $DEPLOY_EXIT -eq 0 ] && ROUTING_NAME="${NEW_ROUTING}" && break
done

[ $DEPLOY_EXIT -ne 0 ] && echo "Deploy failed: ${DEPLOY_OUT}" && exit 1

# Parse response
SYSTEM_NAME_NEW=$(echo "${DEPLOY_OUT}" | node -e "
  const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  console.log(d.SystemName || d.systemName || '');
" 2>/dev/null || echo "")
APP_URL=$(echo "${DEPLOY_OUT}" | node -e "
  const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  console.log(d.AppUrl || d.appUrl || '');
" 2>/dev/null || echo "")
```

## Step 9 — Update state.json

```bash
node << 'SCRIPT'
const fs = require('fs'), path = require('path');
const fp = path.join('.dashboard', 'state.json');
const state = JSON.parse(fs.readFileSync(fp, 'utf8'));
state.app.semver = process.env.NEXT_SEMVER;
state.app.routingName = process.env.ROUTING_NAME;          // update if collision changed it
state.deployment.folderKey = process.env.FOLDER_KEY;
state.deployment.systemName = process.env.SYSTEM_NAME_NEW || state.deployment.systemName;
state.deployment.deployVersion = process.env.DEPLOY_VERSION || state.deployment.deployVersion;
state.deployment.appUrl = process.env.APP_URL || state.deployment.appUrl;
state.deployment.lastDeployedAt = new Date().toISOString();
const tmp = fp + '.tmp';
fs.writeFileSync(tmp, JSON.stringify(state, null, 2));
fs.renameSync(tmp, fp);
console.log('✓ state updated');
SCRIPT
```

## Step 10 — Report

```
✅ Your **<APP_NAME>** is live.

<APP_URL>

Version <NEXT_SEMVER> deployed to <folder name>.
To update it later, say "deploy this dashboard" again.
```

## Error handling

| Error | Action |
|---|---|
| `npm run build` fails | Fix build errors first (`see ../../debug.md`); PAT is restored automatically |
| `uip codedapp pack` fails | Verify `dist/` exists; run `npm run build` first |
| Publish 409 (version conflict) | Auto-increments version and retries (handled in Step 7 loop) |
| Publish 5xx / HTML response | Retry with exponential backoff (handled in Step 7 loop) |
| Deploy routing-name conflict | Auto-regenerates suffix and retries (handled in Step 8 loop) |
| Deploy folder error | Re-run `uip or folders list --all` and verify the key |
| state.json corrupt | Show raw error; user must run build again to regenerate |

## Dashboard-specific rules

- App type is always **Web** — never pass `-t Action`
- Routing name is permanent after first successful deploy — never change it manually
- PAT must NOT be in production bundle — `failBuildIfPatSet` Vite plugin enforces this
- `deployVersion` in state.json is the Orchestrator integer version (separate from semver) — required for upgrade path
