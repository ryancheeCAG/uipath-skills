# Variables, Bindings, and Expressions

## Variables

Use root `uipath:variables version="v1"` for entry point contracts and process globals.

Variables may include:

- `id`
- `name`
- `type`
- `subType`
- `elementId`
- `canonicalId`
- `default`
- `custom`
- `internal`
- CDATA body for schema-like variable content

Entry point inputs use `elementId` to scope an input variable to the corresponding root-level start event. Root output variables become entry point output schema properties. JSON schema variables carry the schema body in CDATA; generated entry-point schema should strip `$schema`.

Subprocesses can carry scoped `uipath:variables` in subprocess extension elements. Do not silently move variables across scopes.

## Bindings

Use root `uipath:bindings version="v1"` for resources that become `bindings_v2.json` entries.

Binding attributes may include:

- `id`
- `name`
- `type`
- `elementId`
- `default`
- `resource`
- `resourceSubType`
- `resourceKey`
- `propertyAttribute`

Node context inputs refer to bindings as expressions in the `=bindings.<binding id>` form. Folder key/path binding attributes can exist to support resource shape, but package generation may skip them as standalone resources.

Never paste real tenant folder keys, connection IDs, release keys, queue IDs, URLs, or private names into skill examples.

## Mappings

Use `uipath:mapping version="v1"` for `BPMN.Variables` input/output mapping on tasks, start/end events, script tasks, and subprocesses.

Output mappings should target declared root or scoped variables. Missing variables should be fixed in the BPMN source before package generation.

## Expressions

Conditions, scripts, variable mappings, and skip conditions are expression-normalized during import. Author expressions in the frontend-compatible form and avoid assignment operators where canvas validation forbids assignment.

Use a leading `=` for expressions where the frontend/runtime expects expression content. Treat plain strings as literals.

## Script tasks

Script tasks use BPMN `script` CDATA with `scriptFormat="JavaScript"`. UiPath script inputs are merged into a single JSON `uipath:input name="args"` body with an `inputSchema` in context. Script outputs must map to declared variables.
