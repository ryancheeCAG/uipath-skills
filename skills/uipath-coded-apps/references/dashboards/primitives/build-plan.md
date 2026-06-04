# Build Plan — intent.json Schema

## intent.json

Agent writes this file. Build script reads it.

```json
{
  "dashboardName": "Operations Health",
  "timeRange": "30d",
  "projectDir": "/absolute/path/to/project",
  "routingName": "operations-health-x7k2",
  "orgName": "appsdev",
  "tenantName": "appsdevDefault",
  "cloudUrl": "https://alpha.uipath.com",
  "apiUrl": "https://alpha.api.uipath.com",
  "tenantId": "<UUID>",
  "clientId": "<OAuth app client ID>",
  "metrics": [
    { "name": "agent-errors", "tier": "T1" },
    {
      "name": "queue-failure-threshold",
      "tier": "T2",
      "params": { "threshold": 20, "direction": "gt" }
    },
    {
      "name": "faulted-items",
      "tier": "T3",
      "title": "Faulted Items by Queue",
      "displayAs": "ranked-table",
      "columns": ["name", "pending"],
      "fnBody": "const r = await sdk.queues.getAll({ state: 'Faulted' })\nreturn r.items?.map(q => ({ name: q.name, pending: q.pendingCount })) ?? []"
    }
  ]
}
```

## Valid values

| Field | Values |
|-------|--------|
| `timeRange` | `"1d"`, `"7d"`, `"30d"`, `"90d"` |
| `metrics[].tier` | `"T1"`, `"T2"`, `"T3"` |
| T2 `params.direction` | `"gt"`, `"lt"`, `"eq"`, `"gte"`, `"lte"`, `"neq"` |

## Routing name

Derive at plan time: `<kebab-dashboard-name>-<4-char-random>`. Example: `agent-health-x7k2`.
Store in intent.json. Never change after first build.

## Approval gate rules

Show plan in plain English. HALT. Wait for:
- Explicit confirmation: "go ahead", "yes", "build it", "looks good", "confirm"
- Edit request: update intent.json, re-render plan, HALT again
