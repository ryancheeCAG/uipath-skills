# HTTP Request Node — Authoring from the StandardResource (SR) cache

When the prompt targets a known SaaS vendor action (e.g. "send a slack message to channel #order-ops", "create a jira ticket in project ENGCE"), use the SR cache to keep the vendor payload shape ready to plug into a connector-mode HTTP node. The first time you encounter a (connector, action) pair, you build the SR yourself from vendor docs and cache it. On subsequent runs you just read.

> **The cli does NOT fetch vendor docs or IS metadata for you.** `standardize` is a thin validator + storer. The agent reads vendor docs (via WebFetch + training data) and constructs the SR.

## Step 0: vendor name → connector key

Map each vendor in the prompt to its IS connector key. If unknown, run `uip is connectors list --output json | jq '.Data[] | {key,vendorName}'` and grep. Common mappings:

| Prompt term | Connector key |
|---|---|
| slack | `uipath-salesforce-slack` |
| jira | `uipath-atlassian-jira` |
| outlook / o365 | `uipath-microsoft-outlook365` |
| gmail | `uipath-google-gmail` |
| salesforce | `uipath-salesforce-sfdc` |
| servicenow | `uipath-servicenow-servicenow` |
| sendgrid | `uipath-sendgrid-sendgrid` |

This table is intentionally connector-only. Method, path, and field shape for every action come from vendor docs at authoring time (Step 1 below). Do NOT assume a path from memory — read the docs each time. Vendor APIs version, deprecate, and rename.

The phrase "using http-request" in the prompt names the **node type** (`core.action.http.v2`), NOT the auth mode. If the vendor has an IS connector, use connector mode + SR cache. Never default to manual mode.

## Lazy cache loop

```bash
KEY="<CONNECTOR_KEY>"
OBJ="<OPERATION_OBJECT>"   # the slug you'll use everywhere; pick what reads naturally
CID="<CONNECTION_ID>"

uip is resources sr "$KEY" "$OBJ" --connection-id "$CID" --output json
# Cache hit → done. Cache miss → build the SR (see "Build an SR" below), then:
# uip is resources standardize "$KEY" "$OBJ" --connection-id "$CID" --from-sr <path>
# uip is resources sr "$KEY" "$OBJ" --connection-id "$CID" --output json
```

Cache path: `~/.uipath/cache/integrationservice/<tenantId>/<connector>/<connection>/<object>.standard.json`. TTL 24h.

## Build an SR on cache miss

The agent owns this step. The cli does nothing here — you read docs and produce a JSON file.

### 1. Read the vendor docs

For each (vendor, action) you need:

1. Identify the vendor's official API docs URL. Use `WebSearch` if needed. Do NOT skip this step — even for SaaS you've seen before, the vendor may have versioned, deprecated, or renamed the endpoint since training.
2. `WebFetch` the docs page for the specific operation. Pull:
   - HTTP method (POST / GET / …).
   - Vendor URL **relative to the connection's base URL**, i.e. with the host stripped. Verify the host you stripped matches `uip is connections base-url <connection-id> --output json` so the connector proxy resolves to the same place at runtime.
   - Request body fields — names, types, required vs optional, enums, descriptions.
   - Reference fields (lookups) — endpoint paths and the response-shape mapping (`lookupValue` + `lookupNames`).
   - Response shape if the next node consumes it.

If a field is a reference, capture the lookup endpoint + value/name fields under `reference`. Read the docs for the lookup endpoint too — its path is also vendor-specific.

### 2. Write the SR JSON

Match the [StandardResource format](../../../../../../uipath-platform/references/integration-service/standard-resource-format.md). Minimum required structure:

```jsonc
{
  "name": "<object-slug>",
  "path": "<vendor-relative-path>",        // extracted from WebFetch of vendor docs in Step 1
  "type": "standard",
  "elementKey": "<connector-key>",
  "displayName": "<Human Name>",
  "custom": "no",
  "metadata": {
    "baseUrl": "<from uip is connections base-url>",
    "method": {
      "POST": {                              // verb keys: POST/GET/PUT/PATCH/DELETE
        "path": "<vendor-relative-path>",
        "method": "POST",
        "operation": "Create",               // Create | List | Retrieve | Update | Replace | Delete
        "description": "<from docs>",
        "parameters": []
      }
    },
    "primaryKey": ["<id-field-name>"]
  },
  "fields": {
    "<field-name>": {
      "name": "<field-name>",
      "displayName": "<from docs>",
      "type": "string",                      // string | integer | number | boolean | date | date-time
      "description": "<from docs>",
      "required": true,
      "request": true,
      "design": { "position": "primary" },
      "reference": {                         // OPTIONAL — only for lookup fields
        "objectName": "<lookup-object-name-from-docs>",
        "path": "<lookup-endpoint-from-docs>",
        "lookupValue": "<id-field-on-lookup-response>",
        "lookupNames": ["<display-field-on-lookup-response>"]
      }
    }
  }
}
```

Save to a tmp path (e.g. `/tmp/<connector>-<object>.sr.json`).

### 3. Cache it

```bash
uip is resources standardize "$KEY" "$OBJ" \
  --connection-id "$CID" \
  --from-sr /tmp/<connector>-<object>.sr.json \
  --output json
```

`standardize` validates the JSON against `StandardResourceSchema` and writes it to the cache path. On validation error it tells you which field is wrong; fix the JSON and re-run.

### Alternative: compact spec → expander

If you'd rather author the shorter ipe-style spec (~58% smaller JSON, expander adds boilerplate), write a `<op>.spec.json` and pass `--from-spec` instead. See the [generate-standard-resource skill](https://github.com/UiPath/skills/blob/main/skills/uipath-platform/references/integration-service/standard-resource-format.md) for the spec shape.

## Reading SR for an HTTP-request-activity node

After `sr` returns the cached SR, pull these fields:

| HTTP-node field | SR source |
|---|---|
| `method` | First verb in `metadata.method` |
| `url` (relative) | `metadata.method.<VERB>.path` — this IS the vendor path; you authored it from docs |
| Base URL preview | `metadata.baseUrl` (do NOT hardcode into `url`; connector mode prepends it at runtime) |
| Required body fields | `Object.keys(fields).filter(f => fields[f].request && fields[f].required)` |
| Optional body fields | `Object.keys(fields).filter(f => fields[f].request && !fields[f].required)` |
| Reference lookups (channel→id, user→id) | `fields[name].reference` — resolve via [reference-resolution.md](../../../../../../uipath-platform/references/integration-service/reference-resolution.md) |
| Reference field UX hints | `fields[name].design.description` |

## End-to-end shape

Prompt example (any two-vendor "send X and create Y" flow follows this shape):
> "Create a flow that sends a `<vendor-A>` message AND creates a `<vendor-B>` record — using http-request activity."

Agent steps:

1. Parse → `[(<connector-key-A>, <action-A>), (<connector-key-B>, <action-B>)]`.
2. Resolve each `connectionId` via `uip is connections list <connector-key> --all-folders --output json`.
3. For each pair: `uip is resources sr <connector> <object> --connection-id <id> --output json`. Cache hit → use it. Cache miss → continue.
4. On cache miss: `WebFetch <vendor-api-docs-url>` for each action. Extract method, vendor relative path, required + optional fields, references. Build SR JSON files (see "Build an SR on cache miss" above).
5. `uip is resources standardize <connector> <object> --connection-id <id> --from-sr <path> --output json` for each. Validates + caches.
6. Re-read via `sr`. Extract `method`, `url` (vendor relative path), body field names, references.
7. Resolve reference fields to IDs (e.g. channel name → id via the reference endpoint declared in the SR).
8. Author two `core.action.http.v2` nodes following [impl.md — Step 3 connector mode](impl.md#step-3--configure-the-node). The `--detail` JSON shape:

```jsonc
{
  "authentication": "connector",
  "targetConnector": "<connector-key>",       // from Step 1
  "connectionId": "<connection-id>",          // from Step 2
  "folderKey": "<folder-key>",                // from connections list
  "method": "<verb-from-sr>",                 // metadata.method.<VERB>.method
  "url": "<vendor-relative-path-from-sr>",    // metadata.method.<VERB>.path — vendor URL, NOT IS slug
  "body": { /* body shape from sr.fields, with reference fields resolved to IDs */ }
}
```

9. Wire `start` → node-A → node-B → `end` per [impl.md — Step 5](impl.md#step-5--wire-edges).
10. `uip maestro flow validate "<ProjectName>.flow" --output json`.

Every concrete value (`method`, `url`, body field set, reference endpoints) MUST come from a live `sr` read in this run. None of them are baked into this doc.

## When to use SR cache vs raw `http-request` discovery

| Use SR cache | Use raw `http-request` |
|---|---|
| Repeated vendor action with stable payload shape | One-off identifier resolution (channel id from name, user id from email) |
| Need the full body shape + references + base URL ready to plug in | Need a single vendor-API value before composing |
| Building the same flow shape across multiple prompts → cache pays off | Vendor endpoint with no documented schema; probe to verify |

Both coexist. `http-request` (via `uip is resources run create <connector> http-request --body '{"method":"GET","url":"<vendor-path>"}'`) stays the right tool for resolving lookup values.

## Anti-patterns

- Do NOT call `uip is resources standardize` without `--from-spec` or `--from-sr`. There is no auto path. The cli will error and tell you so.
- Do NOT use IS curated slugs as the HTTP node `url`. IS slugs are object names (often identical to the `<object>` argument, e.g. `/create_issue` for object `create_issue`). They are NOT vendor endpoints. The HTTP node `url` must be the vendor's documented relative path — that's why you ran WebFetch in Step 1.
- Do NOT use absolute vendor URLs in the HTTP node `url`. In connector mode `url` is RELATIVE; the connection prepends the base URL.
- Do NOT skip reference resolution. SR's `fields[name].reference` says where to look — resolve to IDs before stuffing into the body.
- Do NOT fall back to manual mode + `uipath-uipath-http` just because the prompt says "http-request". That phrase names the node type, not the auth mode. If the vendor has an IS connector, use it.
- Do NOT use placeholder auth tokens (`<SLACK_BOT_TOKEN>`, `<JIRA_BASIC_AUTH_B64>`, `Bearer <TOKEN>`) in headers. If you find yourself typing those, you're in the wrong mode — switch to connector mode and bind a real connection.

### Concrete failure to avoid

A flow built from the prompt "create a flow to send a slack message and create a jira ticket using http-request" should NOT produce:

```jsonc
// WRONG — manual mode for vendors that have IS connectors
{ "detail": { "connector": "uipath-uipath-http", "connectionId": "ImplicitConnection",
  "bodyParameters": { "authentication": "manual",
    "url": "https://slack.com/api/chat.postMessage",
    "headers": { "Authorization": "Bearer <SLACK_BOT_TOKEN>" }, ... } } }
```

Correct: read vendor docs → build SR → cache via `standardize --from-sr` → author connector-mode HTTP node with `targetConnector: "uipath-salesforce-slack"`, real `connectionId`, RELATIVE `url: "/chat.postMessage"`.
