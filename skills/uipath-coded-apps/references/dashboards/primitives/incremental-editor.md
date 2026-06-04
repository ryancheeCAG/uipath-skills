# Incremental Editor

Handles ADD / REMOVE / CHANGE / REBUILD requests on existing dashboards.

## Trigger

Detects `.dashboard/state.json` at session start or after `BUILD_RESULT`.

## edit-intent.json schema

Write to `<PROJECT_DIR>/edit-intent.json`:

```json
// ADD
{ "op": "ADD", "projectDir": "/abs/path", "metric": { "name": "job-failures", "tier": "T1" } }

// REMOVE
{ "op": "REMOVE", "projectDir": "/abs/path", "target": "InvocationVolume" }

// CHANGE (timeRange only)
{ "op": "CHANGE", "projectDir": "/abs/path", "target": "ErrorRateTrend", "delta": { "timeRange": "7d" } }

// REBUILD
{ "op": "REBUILD", "projectDir": "/abs/path" }
```

## Run command

```bash
node "${SKILL_BASE_DIR}/assets/scripts/build-dashboard.mjs" "${EDIT_INTENT_PATH}"
```

## Events to watch

- `HAND_EDIT_DETECTED:{"widget":"X"}` — file was hand-edited. Warn user before overwriting.
- `TSC_PASS` — edit validated clean
- `TSC_FAIL:{"errors":"..."}` — surface to user
- `INCREMENTAL_READY:{"op":"ADD","widget":"X"}` — done; hot-reload fires automatically

## Rules

1. Only regenerate affected widget files — never the full scaffold.
2. Routing name never changes on edit.
3. After REMOVE or CHANGE: always regenerate Dashboard.tsx and widgets/index.ts.
4. Do not touch .env.local unless user explicitly requests a config change.
