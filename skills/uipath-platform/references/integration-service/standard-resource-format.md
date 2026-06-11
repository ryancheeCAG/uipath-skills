# StandardResource (SR) JSON format

Canonical shape of a single connector action, **authored by the agent from vendor API docs**, cached locally by `uip is resources standardize --from-sr`, and read by `uip is resources sr`. Downstream consumers (Maestro Flow, API Workflow HTTP-request-activity authoring) use SR to populate the vendor URL + payload shape without hardcoding vendor specifics.

> **The cli never builds SRs from IS metadata.** IS metadata uses curated slugs and reshaped field names that don't map to the vendor's real HTTP surface. The agent reads vendor docs (e.g. `WebFetch https://api.slack.com/methods/chat.postMessage`) and writes the SR JSON; the cli validates it against the schema below and caches.

> **Schema source of truth:** the protobuf message at [cloud-elements/api `pkg/periodic/v2alpha6/standard_resource.pb.go`](https://github.com/cloud-elements/api/blob/main/pkg/periodic/v2alpha6/standard_resource.pb.go). Field names below match the JSON tags emitted by the Go generator. The cli's zod schema mirrors this shape and is permissive (unknown fields pass through) so newly-added .pb.go fields don't reject cached SRs.

The tables below cover the load-bearing fields for HTTP-request-activity authoring. Full surface (including bulk, hydration, poller hooks, dictionary widgets, solution-resource bindings) lives in the .pb.go.

## Top-level

| Key | Type | Notes |
|---|---|---|
| `name` | string | Operation slug. Matches the `<object>` argument. |
| `path` | string | API path for the action (e.g. `/issue`, `/chat.postMessage`). |
| `type` | string | Usually `"standard"`. |
| `subType` | string? | E.g. `"standard"`, `"custom"`. |
| `section` / `category` | string? | UI grouping. |
| `elementKey` | string | Connector key (e.g. `uipath-atlassian-jira`). |
| `displayName` | string | Human label. |
| `custom` | `"yes" \| "no"` | Custom-operation flag. |
| `isPriority` | boolean? | Marks priority operations. |
| `baseObject` | string? | Parent object name (when derived). |
| `isHidden` | boolean? | Hide from UI. |
| `executionType` | string? | E.g. `"sync"`, `"async"`. |
| `compatibleProjectTypes` | string[]? | Overrides element-metadata.json project-type allowlist. |
| `metadata` | object | See below. |
| `fields` | `Record<string, FieldDef>` | Field map keyed by dotted name (e.g. `fields.project.id`). |
| `experimental` | `Record<string, any>?` | Temporary / experimental key-value bag. |

## metadata

| Key | Type | Notes |
|---|---|---|
| `baseUrl` | string? | **CLI-runtime extension** (not in canonical .pb.go). Vendor base URL (e.g. `https://slack.com/api`). The agent populates this when authoring the SR from vendor docs — verify against `uip is connections base-url <connection-id> --output json` so the value matches the connection at runtime. Build the HTTP-node URL as `baseUrl + method.<VERB>.path`. |
| `method` | `Record<VERB, MethodDef>` | Per-verb action descriptor. Single entry in v1 (the verb the SR was standardized for). |
| `primaryKey` | `string[]` | Field names that identify the response record (e.g. `["id"]`, `["ts"]`, `["sys_id"]`). Empty for actions without an identifier (SendGrid send). |
| `hasCustomFieldDiscovery` | boolean? | True if the connector exposes custom-field discovery for this resource. |
| `searchableJoins` / `hasSearchables` | string[]? / boolean? | Filter-builder hints. |
| `bulk` | object? | Bulk-action descriptor (see .pb.go `StandardResourceBulk`). |
| `events` | object? | Polling / webhook / hydration event blocks (see .pb.go `StandardResourceEvent`). |
| `discovery` | `Discovery?` | **CLI / ipe extension** (not in canonical .pb.go). Cascading SRs (e.g. Jira create_issue) authored via `standardize --from-spec`. See below. |
| `experimental` | `Record<string, any>?` | Temporary / experimental key-value bag. |

### MethodDef

| Key | Type | Notes |
|---|---|---|
| `path` | string | Same as top-level `path`. |
| `method` | string | HTTP verb (POST, GET, PUT, PATCH, DELETE). |
| `operation` | string | `Create`, `List`, `Retrieve`, `Update`, `Replace`, `Delete`. |
| `description` | string? | Human description. |
| `responseDisplayName` | string? | Label for the response shape (e.g. "Message"). |
| `parameters` | `Parameter[]` | Path/query/header params (NOT body fields — those live in top-level `fields`). |

### Discovery (cascading)

Cascading actions (Jira create_issue: project + issuetype → custom fields) declare:

```jsonc
{
  "scopeFields": ["fields.project.id", "fields.issuetype.id"],
  "path": "/issue/createmeta/{fields.project.id}/issuetypes/{fields.issuetype.id}",
  "fieldsAt": "fields",
  "pagination": { "style": "startAt", "limitParam": "maxResults", "offsetParam": "startAt" },
  "transform": {
    "language": "js",
    "version": 1,
    "entry": "toStandardFields",
    "code": "function toStandardFields(input) { ... }"
  }
}
```

Cascading SRs are authored — `standardize --from-spec` reads a compact spec + `transform.js` sibling and inlines the JS as `transform.code`. The pure auto path (no `--from-spec`) does NOT generate `transform.code`.

## fields[name]

Keyed by FLAT dotted name (no nested objects). Examples: `channel`, `fields.project.id`, `personalizations[0].to[0].email`, `value[*].body.contentType`.

| Sub-key | Type | Notes |
|---|---|---|
| `name` | string | Same as the field map key. |
| `displayName` | string | UI label. |
| `description` | string? | |
| `type` | `"string"`/`"integer"`/`"number"`/`"boolean"`/`"date"`/`"date-time"` | Defaults `"string"`. |
| `format` | string? | Refines type (`"email"`, `"date-time"`, `"int64"`). |
| `mask` | string? | Display mask. |
| `custom` | `"yes" \| "no"` | Marks tenant-custom fields. |
| `sortOrder` | number? | UI order. Present on request fields, omitted on response-only. |
| `isPriority` | boolean? | Promotes to primary UI section. |
| `primaryKey` | boolean? | True on response identifier fields. |
| `defaultValue` | any? | Default if unset. |
| `enum` | `EnumValue[]` | Allowed values, each `{ value, name? }`. |
| `reference` | `Reference?` | Lookup metadata — see below. |
| `design` | `Design?` | UI rendering hints — see below. |
| `method` | `Record<VERB, { request?, response?, required?, dependsOn? }>?` | Per-verb participation. Canonical shape. |
| `request` / `required` / `response` | boolean? | **CLI-collapsed flags** — `transformMetadataToStandardResource` lifts `method[VERB].{request,required,response}` to the top level for HTTP-node authoring convenience. |
| `nativeType` | string? | Vendor's native type. |
| `pattern` | string? | Validation regex. |
| `searchable` / `searchableOperators` / `searchableNames` / `searchableDisplayName` | various | Filter-builder hints. |
| `refName` / `refPointer` | string? | Reference indirection in JSON. |
| `events` | `Record<string, any>?` | Per-event field metadata (see .pb.go `StandardResourceFieldEventMetadata`). |
| `isCuratedEventField` / `isHybridField` / `isDebugTriggerQueryParameter` | boolean? | Authoring flags from the canonical shape. |
| `experimental` | `Record<string, any>?` | Temporary / experimental key-value bag. |

### Reference (lookups)

| Sub-key | Type | Notes |
|---|---|---|
| `objectName` | string | Logical lookup target (`project`, `channels`, `User`, `sys_user`). |
| `path` | string | Lookup endpoint. May include `{token}` placeholders bound by `dependsOn`. |
| `filterPattern` | string? | Search-with-input pattern (`/project/search?query={searchTerm}`). |
| `childPath` | string? | Hierarchical pickers (Outlook folder tree). |
| `folderField`/`folderValue` | string? | Folder-scoped lookups. |
| `dependsOn` | `string[]` | Fields that must be resolved first. |
| `lookupValue` | string | Field on the lookup result used as the bound value (`id`, `accountId`). |
| `lookupNames` | `string[]` | Fields used for display matching (`["name", "key"]`, `["displayName", "emailAddress"]`). |

### Design

| Sub-key | Type | Notes |
|---|---|---|
| `position` | `"primary" \| "secondary"` | UI placement; `primary` for required fields, `secondary` otherwise. |
| `isMultiSelect` | boolean? | |
| `delimiter` | string? | Multi-select delimiter (default `","`). |
| `enableUserOverride` | boolean? | Allow typing a raw value instead of picking. |
| `loadByDefault` | boolean? | Pre-load lookup on form render. |
| `displayPattern` | string? | Template for lookup display (`"{name}"`, `"{displayName} ({email})"`). |
| `component` | string? | Custom UI component (`"FolderPicker"`). |
| `requiredGroups` | `string[]` | Mutual-inclusion group names (e.g. Slack `["messageContent"]` — at least one of `text`/`blocks` required). |
| `fieldActions` | `FieldAction[]` | Conditional show/hide rules (Slack `reply_broadcast` shown only when `thread_ts` is set). |
| `textBlocks` | `TextBlock[]?` | UI message blocks (see .pb.go `StandardResourceTextBlock`). |
| `dictionaryWidget` | object? | Dictionary widget config. |
| `solutionResourceKind` / `solutionResourceSubTypes` / `selection` | various | Bind to solution-resource types (asset / queue / connection / connector). |
| `requiredOptions` / `preSelectedOptions` / `optionDescriptions` | various | Scopes / permissions widget config. |
| `exposeAsSubBinding` / `validation` / `setSolutionHeaders` / `sendSolutionContextInBody` / `valueExtractionPattern` | various | Specialized UX / runtime flags. |
| `isHidden` | boolean? | Hide the field. |

## Worked example — shape only

> **The vendor name + URLs below are illustrative.** Do NOT copy these values into a real SR — they may be stale, wrong for the connection's API version, or simply not what the docs say today. The point of the example is to show the JSON SHAPE. The values in any real SR you cache must come from a live `WebFetch` of the vendor's docs in the run that authored it.

```jsonc
{
  "name": "send_message",
  "path": "<vendor relative path from docs>",
  "type": "standard",
  "elementKey": "uipath-salesforce-slack",
  "displayName": "Send Message",
  "custom": "no",
  "metadata": {
    "baseUrl": "<vendor base url from connection base-url>",
    "method": {
      "POST": {
        "path": "<vendor relative path from docs>",
        "method": "POST",
        "operation": "Create",
        "description": "<from docs>",
        "responseDisplayName": "Message",
        "parameters": []
      }
    },
    "primaryKey": ["ts"]
  },
  "fields": {
    "channel": {
      "name": "channel",
      "displayName": "Channel",
      "type": "string",
      "custom": "no",
      "sortOrder": 1,
      "isPriority": true,
      "reference": {
        "objectName": "<lookup object name from docs>",
        "path": "<lookup endpoint from docs>",
        "lookupValue": "<id field on the lookup response>",
        "lookupNames": ["<display field(s) on the lookup response>"]
      },
      "design": { "position": "primary", "isMultiSelect": false, "enableUserOverride": true, "loadByDefault": true, "displayPattern": "{name}" },
      "request": true,
      "required": true
    },
    "text": {
      "name": "text",
      "displayName": "Message text",
      "type": "string",
      "custom": "no",
      "sortOrder": 2,
      "design": { "position": "primary", "requiredGroups": ["messageContent"] },
      "request": true,
      "required": false
    }
  }
}
```

## Cache envelope on disk

```jsonc
{
  "cachedAt": 1717900000000,         // ms epoch
  "data": { /* StandardResource above */ }
}
```

Location: `~/.uipath/cache/integrationservice/<tenantId>/<connectorKey>/<connectionId>/<objectName>.standard.json`. TTL 24h. `--refresh` busts.
