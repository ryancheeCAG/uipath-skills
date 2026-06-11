# Connector Overview — the mental model

A connector wraps a vendor's REST API into UiPath Studio activities and triggers.
**Udon** (the Integration Service runtime) sits between Studio and the vendor API,
standardising pagination, authentication, parameter mapping, and error handling.

## The 5 CRUD activities + curated + HTTP Request

Every connector automatically gets 5 CRUD activities, each a dropdown listing every
standard resource that implements that method:

| Activity | Method   | Description                              |
|----------|----------|------------------------------------------|
| List     | GET      | Filtered list. Supports CEQL query.      |
| Get      | GETBYID  | Retrieve a single record by ID.          |
| Create   | POST     | Insert a new record.                     |
| Update   | PATCH/PUT| Modify an existing record.               |
| Delete   | DELETE   | Remove a record by ID.                   |

A **curated activity** is a standalone activity shown alongside the 5 CRUDs (e.g.
"Get Support Request"). It comes from a `metadata.method.{METHOD}.curated` block in
the SR file; its fields use `requestCurated`/`responseCurated` visibility and a
`design.position` of Primary / Secondary / None. Every connector also gets a free
**HTTP Request** activity (hide it via `hasHttpRequest` in element-metadata.json).

## File layout (periodic-{elementKey}/)

```
app/element/
├── element.json              # Core definition: auth, configuration[], resources[], parameters[], hooks[]
├── element-metadata.json     # Catalog entry: name, categories, capability flags
├── image.svg                 # Icon
├── hooks/*.js                # JS pre/post request transformers (extracted from element.json by scripts/build)
├── standard-resources/*.json # Per-object metadata: fields, methods, curated, events
└── event-hook/               # Event/polling hook definitions
```

## How the files link

element.json tells Udon HOW to call the vendor (vendorPath, parameters, hooks).
Standard resources tell Udon WHAT the data looks like (fields, types, method config).

1. **resource entry → SR file**: `standardResourceName: "accounts"` →
   `standard-resources/accounts.json` (canonical link). The SR filename is independent
   of the path. Older connectors without `standardResourceName` match on SR `path`.
2. **resource entry → hook files**: each `resources[].hooks[].ref` names a file in `hooks/`.
3. **global hooks**: top-level `hooks[]`, same `ref` field; always run for every request.
4. **system resources**: element.json resource entries with NO SR file and no
   `standardResourceName` → never appear in activities. Internal only (onProvision,
   oauthOnTokenRefresh, provisionAuthValidation). Override built-ins by matching their path.

## Connector key format

- Official UiPath: `uipath-{vendor}-{product}` (e.g. `uipath-salesforce-sfdc`)
- Custom / design: `{tenant|org}-{vendor}-{app}`; repo name = `periodic-` + key.

## Scope

In scope: RESTful JSON APIs, OpenAPI/Postman import, single base URL, polling/webhook
events, JS hooks. Out of scope: GraphQL, SOAP/XML, SDKs, multiple base URLs.

## See also
- [element-json.md](element-json.md) — element.json internals
- [configuration.md](configuration.md) — config + auth keys
- [standard-resources.md](standard-resources.md) — SR / field shape
