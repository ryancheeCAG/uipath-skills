# State File — Per-Project Persistence

Every dashboard project has a `.dashboard/state.json` that persists metadata across sessions.
Read it at the start of every build and deploy operation.

## Schema

```json
{
  "app": {
    "name": "Agent Health Dashboard",
    "routingName": "agent-health-dashboard-x7k2",
    "semver": "1.0.0"
  },
  "env": "alpha",
  "org": "appsdev",
  "tenant": "appsdevDefault",
  "cloudUrl": "https://alpha.uipath.com",
  "widgets": ["ActiveAgentsKPI", "ErrorRateTrend", "InvocationVolume"],
  "deployment": {
    "systemName": null,
    "folderKey": null,
    "appUrl": null,
    "lastDeployedAt": null
  }
}
```

## Writing the state file

Write after Phase 7 (after widgets are generated) and after every successful deploy.
Use atomic writes — write to a `.tmp` file, then rename:

```bash
node << 'SCRIPT'
const fs = require('fs'), path = require('path');
const stateDir = path.join('<PROJECT_DIR>', '.dashboard');
fs.mkdirSync(stateDir, { recursive: true });
const state = {
  app: {
    name: '<DASHBOARD_NAME>',
    routingName: '<ROUTING_NAME>',
    semver: '1.0.0'
  },
  env: '<ENV>',
  org: '<ORG_NAME>',
  tenant: '<TENANT_NAME>',
  cloudUrl: '<CLOUD_BASE_URL>',
  widgets: [<WIDGET_COMPONENT_NAMES>],
  deployment: { systemName: null, folderKey: null, appUrl: null, lastDeployedAt: null }
};
const tmpPath = path.join(stateDir, 'state.json.tmp');
const finalPath = path.join(stateDir, 'state.json');
fs.writeFileSync(tmpPath, JSON.stringify(state, null, 2));
fs.renameSync(tmpPath, finalPath);
console.log('✓ state saved');
SCRIPT
```

## Reading the state file

```bash
STATE=$(node -e "try { process.stdout.write(require('fs').readFileSync('.dashboard/state.json','utf8')) } catch { process.stdout.write('{}') }")
ROUTING_NAME=$(node -e "const s=JSON.parse('$STATE' || '{}'); console.log(s.app?.routingName || '')")
FOLDER_KEY=$(node -e "const s=JSON.parse('$STATE' || '{}'); console.log(s.deployment?.folderKey || '')")
SYSTEM_NAME=$(node -e "const s=JSON.parse('$STATE' || '{}'); console.log(s.deployment?.systemName || '')")
```

## Routing name

The routing name is derived from the dashboard title at build time:
```bash
ROUTING_NAME=$(node -e "
  const name = '<DASHBOARD_NAME>'.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-\$)/g, '');
  const suffix = Math.random().toString(36).slice(2, 6);
  console.log(name + '-' + suffix);
")
```

Once set, the routing name NEVER changes — it's the URL slug and package identifier.
If it's already in state.json, reuse it.

## State file location

The state file lives at `<PROJECT_DIR>/.dashboard/state.json`.
The project directory is the folder containing `package.json`.

## Incremental mode detection

If `.dashboard/state.json` exists when the user asks to build a dashboard:
→ Read `primitives/incremental-editor.md` and follow its flow.

If it does NOT exist:
→ This is a fresh build. Follow the normal Phase 1–8 pipeline.
