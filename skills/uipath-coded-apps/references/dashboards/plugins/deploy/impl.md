# Dashboard Deploy Plugin

Deploys a built dashboard to Automation Cloud as a Coded Web App.
Uses state.json to distinguish fresh deploys from upgrades.

## Pre-flight

```bash
# Verify login
uip login status --output json

# Read state.json
STATE=$(cat .dashboard/state.json 2>/dev/null || echo '{}')
ROUTING_NAME=$(node -e "const s=JSON.parse(process.env.STATE||'{}'); console.log(s.app?.routingName||'')" STATE="$STATE")
SYSTEM_NAME=$(node -e "const s=JSON.parse(process.env.STATE||'{}'); console.log(s.deployment?.systemName||'')" STATE="$STATE")
FOLDER_KEY=$(node -e "const s=JSON.parse(process.env.STATE||'{}'); console.log(s.deployment?.folderKey||'')" STATE="$STATE")
SEMVER=$(node -e "const s=JSON.parse(process.env.STATE||'{}'); console.log(s.app?.semver||'1.0.0')" STATE="$STATE")
```

If `ROUTING_NAME` is empty → state.json missing or corrupt. Tell user to run the build first.

## Step 1 — Classify deploy type

- `SYSTEM_NAME` is empty → **Fresh deploy** (first time this dashboard is deployed)
- `SYSTEM_NAME` is non-empty → **Upgrade deploy** (updating an existing deployment)

Show the user:
```
Deploy plan:
  Dashboard:    <app.name>
  Version:      <SEMVER> → <next semver>
  Routing name: <ROUTING_NAME>
  Type:         Fresh deploy  OR  Upgrade (<SYSTEM_NAME>)
  Folder:       <resolved folder name> (key: <FOLDER_KEY>)
```

Ask: **"Confirm deploy?"** — wait for `y`.

## Step 2 — Resolve folder key (fresh deploy only)

If `FOLDER_KEY` is empty (fresh deploy):

```bash
uip or folders list --output json
```

Ask user: "Which folder should this dashboard live in?" with the list.
Once confirmed:
```bash
FOLDER_KEY=$(uip or folders list --output json | node -e "
  const fs=require('fs'), data=JSON.parse(fs.readFileSync('/dev/stdin','utf8'));
  const folder = data.find(f => f.Name === '<FOLDER_NAME>');
  console.log(folder?.Key || '');
")
```

## Step 3 — Bump version

```bash
NEXT_SEMVER=$(node -e "
  const [major, minor, patch] = '<SEMVER>'.split('.').map(Number);
  console.log([major, minor, patch + 1].join('.'));
")
```

## Step 4 — Production build (strip PAT)

Temporarily rename `.env.local` so PAT doesn't enter the bundle:

```bash
cd <PROJECT_DIR>
[ -f .env.local ] && mv .env.local .env.local.deploy-bak
npm run build
BUILD_EXIT=$?
[ -f .env.local.deploy-bak ] && mv .env.local.deploy-bak .env.local
[ $BUILD_EXIT -ne 0 ] && echo "BUILD_FAILED" && exit 1
```

## Step 5 — Pack

```bash
uip codedapp pack dist \
  -n "${ROUTING_NAME}" \
  -v "${NEXT_SEMVER}" \
  --output json
```

## Step 6 — Publish

```bash
uip codedapp publish \
  -n "${ROUTING_NAME}" \
  -v "${NEXT_SEMVER}" \
  --output json
```

If 5xx error → retry once after 5 seconds (Cloudflare transient errors).

## Step 7 — Deploy

**Fresh deploy:**
```bash
uip codedapp deploy \
  -n "<app.name>" \
  --routing-name "${ROUTING_NAME}" \
  --folder-key "${FOLDER_KEY}" \
  --output json
```

**Upgrade deploy:**
```bash
uip codedapp deploy \
  -n "<app.name>" \
  --routing-name "${ROUTING_NAME}" \
  --folder-key "${FOLDER_KEY}" \
  --output json
```

Parse the response for `appUrl` or `systemName`.

## Step 8 — Update state.json

```bash
node << 'SCRIPT'
const fs = require('fs'), path = require('path');
const stateDir = '.dashboard';
const fp = path.join(stateDir, 'state.json');
const state = JSON.parse(fs.readFileSync(fp, 'utf8'));
state.app.semver = process.env.NEXT_SEMVER;
state.deployment.folderKey = process.env.FOLDER_KEY;
state.deployment.systemName = process.env.SYSTEM_NAME || state.deployment.systemName;
state.deployment.appUrl = process.env.APP_URL || state.deployment.appUrl;
state.deployment.lastDeployedAt = new Date().toISOString();
const tmp = fp + '.tmp';
fs.writeFileSync(tmp, JSON.stringify(state, null, 2));
fs.renameSync(tmp, fp);
console.log('✓ state updated');
SCRIPT
```

## Step 9 — Show result

```
✅ Your **<app.name>** is live!

<appUrl>

Version <NEXT_SEMVER> deployed to <folder name>.
```

## Error handling

- `npm run build` fails → fix build errors first (see `../../debug.md`)
- `uip codedapp pack` fails → check dist/ exists; run npm run build first
- `uip codedapp publish` fails with 409 (version conflict) → bump version and retry
- `uip codedapp deploy` fails with folder error → verify folder key with `uip or folders list`
- State.json corrupt → show raw error, ask user to run build again to regenerate

## Dashboard-specific rules

- App type is always **Web** — never pass `-t Action`
- Routing name is permanent — never change it after first deploy
- PAT must NOT be in production bundle — `failBuildIfPatSet` plugin enforces this at build time
