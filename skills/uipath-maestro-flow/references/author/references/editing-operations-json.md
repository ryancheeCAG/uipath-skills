# Flow Editing Operations — Edit / Write Strategy

All flow file modifications via the `Edit` and `Write` tools (read-modify-write of the `.flow` JSON file). This strategy gives full control over every field but requires manual management of definitions, variables, and edge integrity.

> **Apply every recipe in this file with the `Edit` tool (default) or the `Write` tool (only when ≥70% of nodes change).** Each recipe shows the JSON payload that goes into the `new_string` parameter of an `Edit` call. `python`, `node`, `jq`, `sed`, `awk`, and shell heredocs are a last resort for mutations and require explicit user approval after you've surfaced the trade-offs — see SKILL.md rule on scripted mutations and [editing-operations.md — Why not Python / Node / jq / sed?](editing-operations.md#why-not-python--node--jq--sed).
>
> **When to use this strategy:** Edit / Write is required for all non-carve-out `.flow` edits. Use Flow CLI only for connector activity, connector-trigger, and managed HTTP carve-outs documented by their plugins. Inline-agent project lifecycle uses `uip agent init --inline-in-flow` / `uip agent validate --inline-in-flow`, but the `uipath.agent.autonomous` node and edges are authored with this guide. See [editing-operations.md](editing-operations.md) for the strategy selection matrix.

---

## Key Differences from CLI

When editing the `.flow` file with `Edit` / `Write`, **you** are responsible for everything the CLI normally handles:

| Concern | CLI handles | Edit / Write — you must |
|---------|------------|------------------------|
| Definitions | Auto-copied from registry cache | Copy the returned node definition object from `uip maestro flow registry get` into `definitions` array |
| Node variables | Auto-added to `variables.nodes` | Add output variable entries manually (or accept that `variables.nodes` may need regeneration) |
| Edge cleanup on delete | Auto-removes connected edges | Find and remove all edges referencing the deleted node |
| Orphan cleanup | Auto-removes unused definitions and orphaned bindings | Remove definitions no longer referenced by any node; remove connector bindings only when no remaining node uses that connector |
| `targetPort` | Auto-set | Set `targetPort` on every edge (validate rejects without it) |
| `bindings_v2.json` | Auto-managed by `node configure` | Prefer the CLI carve-out for connector/managed HTTP configuration; if using the documented fallback, author top-level `.flow` `bindings[]` and only touch generated files when the plugin explicitly says to |

---

## Pre-flight Checklist

Before editing the `.flow` file, ensure each of the following is handled. These are the concerns the CLI used to manage automatically; under the Edit / Write default, **you** are responsible for them.

1. **Locate the canonical `.flow` file.** Before any `Edit` / `Write`, find the flow project directory — it is the directory that contains `project.uiproj`. The canonical `.flow` lives **next to** that `project.uiproj`, not at the solution root. Commands like `uip solution init <Name>` + `uip maestro flow init <Name>` create nested paths (`<Name>/<Name>/project.uiproj`); the `.flow` you must edit is `<Name>/<Name>/<Name>.flow`, not `<Name>/<Name>.flow`. Run `find . -name project.uiproj -type f` and pin every `Edit` / `Write` call to the sibling file. `uip maestro flow validate <PATH>.flow` will accept a misplaced file, so validation alone does **not** confirm the right target — only the colocation with `project.uiproj` does.
2. **Definitions and versions.** For every new node type, run `uip maestro flow registry get <type> --output json`. Copy the returned node definition object **verbatim** into `definitions[]` — one entry per unique `type:typeVersion`. Depending on CLI/plugin version, the node definition may appear as `Data.Node` or as the top-level object containing fields such as `nodeType`, `version`, and `handleConfiguration`; copy that node object, not the surrounding `Result` / `Code` envelope. Then set each node instance's `typeVersion` to the exact copied definition `version` value. The validator matches `type:typeVersion` exactly; `typeVersion: "1.0.0"` does not match a registry definition with `"version": "1.0"`. Never hand-write or paraphrase definitions (see "Every node type needs a `definitions` entry" in [the Author capability index](../CAPABILITY.md)).
3. **Unique node ID.** Pick a camelCase ID that does not collide with existing node IDs. Prefer meaningful names (`fetchUsers`, `filterActive`) since they become part of every `$vars.<nodeId>.*` expression.
4. **`sourcePort` and `targetPort` on every edge.** Omitting `targetPort` is the #1 validation error (see "`targetPort` is required on every edge" in [the Author capability index](../CAPABILITY.md)). Use `sourcePort`, never `sourceHandle`; `sourceHandle` is not part of the `.flow` edge schema and produces a precise schema error such as `[error] [edges[N].sourcePort] Invalid input: expected string, received undefined` (the path tells you exactly which edge entry is missing the `sourcePort` key). Look up ports in the relevant plugin's `planning.md` or in [file-format.md — Standard ports](../../shared/file-format.md).
5. **Node outputs block (End / Terminate only).** End-style nodes consume their `outputs` block at runtime to map workflow-level `out` variables — see [end/impl.md](plugins/end/impl.md). For action / trigger nodes the instance `outputs` block is **not** consumed by BPMN serialization; the runtime reads the manifest's `outputDefinition` instead. Authoring an action-node `outputs` block matching the manifest is fine and is what the canonical examples show, but adding it does **not** make `$vars.<sourceNodeId>.output` resolve downstream — that contract is `variables.nodes[]` (next item).
6. **`variables.nodes[]` (REQUIRED for every data-producing node — this is what powers `$vars.X.output`).** For each data-producing node, add an entry per output (`output` for action / trigger nodes, plus `error` for action nodes). The BPMN emitter walks `variables.nodes[]` to write the process-level `<uipath:inputOutput id="<nodeId>.<outputId>">` declarations the runtime needs; without them, downstream `$vars.<sourceNodeId>.output` resolves to `undefined` even though `flow validate` passes (MST-9972). The shape per entry: `{ "id": "<nodeId>.<outputId>", "type": "object", "binding": { "nodeId": "<nodeId>", "outputId": "<outputId>" } }`. After your edits, **`uip maestro flow format` regenerates this block from `nodes[]` + `definitions[]`** — running format makes any direct-authored omission self-healing.
7. **On delete — cascade manually.** Remove the node from `nodes`. Then sweep `edges[]` for any with matching `sourceNodeId`/`targetNodeId`. Then prune `definitions[]` if this was the last user of the type. Then check `bindings_v2.json` — but only remove a connector binding if no remaining node uses the same connector (bindings are shared at the connector level).

> **Anti-pattern: editing a `.flow` that is not colocated with `project.uiproj`.**
> A `.flow` file outside the flow project directory is invisible to `uip maestro flow debug`, to the Studio solution, and to any checker that discovers the project via `**/project.uiproj`. It will still pass `uip maestro flow validate <PATH>.flow` because that command only checks JSON-schema correctness of the file you hand it — it does not verify the file is the project's canonical flow. Always edit the `.flow` that sits next to `project.uiproj`.

---

## Edit Tooling

Direct JSON edits use four mechanics. Pick by operation class — same pattern, different tool. The CLI has no `node update` command (see [editing-operations-cli.md § Operations Not Supported by CLI](editing-operations-cli.md#operations-not-supported-by-cli)), so structural mutations of node `inputs`, definition swaps, and array splices are done through direct `.flow` authoring.

| Operation class | Mechanic | When to use |
|----|----|----|
| Surgical leaf-value change (single string/number/bool) | `Edit` | One unique substring in the file. Whitespace-sensitive — re-`Read` first if the file was just rewritten. |
| New node, new edge, new definition entry, new variable | `Read` whole file → reconstruct in chat → `Write` whole file | Adding self-contained sub-objects. Preserves field order; risks dropping fields on files >1000 lines. |
| Replace nested object in array; insert nested fields; idempotent splice | `Edit` / `Write`; `python3` heredoc only after explicit user approval | Surgical structural mutation. Prefer direct authoring first; use a script only when the user has accepted the state-bypass and diff-review trade-off. |
| One-shot extraction or single-field mutation from CLI JSON output | `jq` | Reading `--output json` results. Faster than spawning Python for read-only paths. |

### Canonical heredoc recipe

When the user explicitly approves a scripted structural rewrite, use this shape. Substitute the node-type guard, the field path, and the new value:

```bash
python3 - <<'PY'
import json
flow = json.load(open("<FILE>.flow"))
# Mutate flow here — splice arrays, set nested fields, replace objects.
# Example: insert/overwrite a field on every node of a given type
for node in flow["nodes"]:
    if node.get("type") == "<NODE_TYPE>":
        node.setdefault("inputs", {})["<FIELD>"] = "<VALUE>"
json.dump(flow, open("<FILE>.flow", "w"), indent=2)
PY
uip maestro flow validate <FILE>.flow --output json
```

`json.dump(..., indent=2)` matches the file's existing 2-space indent — `flow format` normalizes layout but does not re-indent unrelated structure, so preserve the canonical 2-space indent on writes.

### `jq` for extracting CLI JSON

Read-only extractions on `--output json` results — no Python needed:

```bash
uip solution upload --output json | jq -r '.Data.Url'
uip maestro flow registry get <NODE_TYPE> --output json | jq '.Data.Node'
```

### Why scripting is approval-gated

- `Edit` on nested JSON is fragile. Indented sibling fields, trailing commas, and quote styles all break the exact-match constraint. One byte of drift, no edit applied.
- Whole-file `Write` is safe but lossy — every field has to round-trip through chat, and large `.flow` files (>500 lines once layout, definitions, and bindings settle) blow the read budget. Use `Write` only for new flows or full reshapes.
- `python3 -c` / heredoc is a fallback for structural rewrites that are too brittle for `Edit` and too large for safe whole-file `Write`. Use it only after surfacing the trade-offs and getting explicit user approval.

---

## Primitive Operations

### Add a node

**Tool:** `uip maestro flow batch-edit` (one CLI call that applies all node + edge mutations atomically and runs validate / format internally)

**One turn.** After `uip maestro flow registry get` returns the definition, issue a single `uip maestro flow batch-edit <flow-file> --spec '@spec.json'` call. The CLI command applies every operation in the spec atomically, regenerates `definitions[]` / `variables.nodes[]` / `layout.nodes` / `bindings[]` from the current node graph, and runs validate + format internally — so this replaces what was previously a parallel batch of `Edit` calls into disjoint `.flow` regions. Do **not** decompose the spec back into per-region `Edit` calls — that loses the atomicity and re-introduces the read-after-write race that the gate turn used to absorb. The Phase 1 [Batch independent `Edit`s in one turn](editing-operations.md#batch-independent-edits-in-one-turn) rule still applies to non-flow files and to partial edits the CLI command doesn't cover.

**Prereq turn:** Run `uip maestro flow registry get <NODE_TYPE> --output json` and copy the returned node definition object (`Data.Node` or the top-level node object, depending on CLI/plugin version). Capture the definition's `version` field — you'll set the node instance's `typeVersion` in the spec to that exact value. Pick a unique camelCase `id` for the new node here too; both the `addNode` and every `addEdge` referencing it use that planned `id`.

**Mutate turn:** One call to `uip maestro flow batch-edit <flow-file> --spec '@spec.json'` (or inline JSON via `--spec '<json>'`). The CLI runs validate + format internally and returns one structured result — no separate gate turn.

#### Spec shape

The spec is an `operations` array. Each entry has a `kind` plus operation-specific fields. The canonical "Add a node" spec wires `addNode` together with N×`addEdge`:

```json
{
  "operations": [
    {
      "kind": "addNode",
      "id": "<UNIQUE_NODE_ID>",
      "type": "<NODE_TYPE>",
      "typeVersion": "<DEFINITION_VERSION>",
      "display": { "label": "<LABEL>" },
      "config": {
        "inputs": {},
        "outputs": {
          "output": {
            "type": "object",
            "description": "The return value of the <node type>",
            "source": "=result.response",
            "var": "output"
          },
          "error": {
            "type": "object",
            "description": "Error information if the <node type> fails",
            "source": "=result.Error",
            "var": "error"
          }
        }
      },
      "bindings": []
    },
    { "kind": "addEdge", "from": "<UPSTREAM_NODE_ID>.<SOURCE_PORT>", "to": "<UNIQUE_NODE_ID>" },
    { "kind": "addEdge", "from": "<UNIQUE_NODE_ID>", "to": "<DOWNSTREAM_NODE_ID>" }
  ]
}
```

The `definition` for this `type:typeVersion` is auto-attached by the CLI from the registry cache populated during the prereq `registry get` — do not include `definitions[]` entries in the spec. `variables.nodes[]` and `layout.nodes` are regenerated from `nodes[]` after the spec is applied.

> **`display` is required on every `addNode` op** — including control-flow nodes (`core.control.end`, `core.logic.terminate`) where it may feel optional. Omitting it produces a vague `[(root)] Schema validation failed: Invalid input: expected object, received undefined` from the CLI, which does NOT pinpoint the missing field. Always include `"display": { "label": "<label>" }` on every `addNode` op, even bare end nodes. See [file-format.md — Node instance](../../shared/file-format.md#node-instance) and [MST-9368](https://uipath.atlassian.net/browse/MST-9368) for the validator-error-clarity follow-up.

> **What actually makes `$vars.<sourceNodeId>.output` resolve is `variables.nodes[]`, which `batch-edit` regenerates from `nodes[]` + `definitions[]` after each spec applies.** The BPMN emitter ignores the action-node instance `outputs` block at serialization — it reads the manifest's `outputDefinition` for the activity-side mapping and reads `variables.nodes[]` for the process-level `<uipath:inputOutput>` declarations downstream nodes depend on. Including an `outputs` block matching the manifest under `config.outputs` is fine (the canonical examples include it for documentation), but you can skip it on action and trigger nodes. End / terminate nodes are different — see [end/impl.md](plugins/end/impl.md). The standard patterns are in [file-format.md — Node outputs](../../shared/file-format.md#node-outputs). MST-9972 still applies; `batch-edit` calls format internally so this is self-healing.

> **No full `model` block in the `addNode` `config`.** BPMN type, serviceType, event definition, and binding/context templates come from the definition the CLI attaches from the registry. Most instance-specific identity fields live under `config.inputs`: `entryPointId`/`isDefaultEntryPoint` for triggers and `color`/`content` for sticky notes. Attached inline-agent resource nodes that declare `model.source: true` use only the minimal instance block `"model": { "source": "<resourceId>" }` under `config`. For `uipath.agent.autonomous`, write the inline agent `projectId` at `config.inputs.source` instead; flow-core hoists source identity into inputs and no instance `model` block is written. See [file-format.md — Instance-specific identity fields](../../shared/file-format.md#instance-specific-identity-fields).

> **No `ui` block on `addNode` ops.** Do NOT put `position`, `size`, or `collapsed` on the op. `batch-edit` regenerates `layout.nodes` from the node graph.

> **(Resource nodes only) populate `bindings`.** Skip unless the node type is one of `uipath.core.rpa-workflow.*`, `uipath.core.agent.*`, `uipath.core.flow.*`, `uipath.core.agentic-process.*`, `uipath.core.api-workflow.*`, or `uipath.core.human-task.*`. For resource nodes, the `addNode` op's `config` stays minimal (just `inputs`/`outputs`) and you populate the op's `bindings` array — two entries per resource (`name` + `folderPath`) with `resourceKey` exactly matching the definition's `model.bindings.resourceKey`. `batch-edit` merges these into the flow's top-level `bindings[]`. The BPMN emit layer rewrites the definition's `<bindings.{name}>` placeholders to `=bindings.{id}` by matching on `(resourceKey, name)`. Without matching `bindings` entries on the op, the CLI's internal validate passes but `uip maestro flow debug` fails with "Folder does not exist or the user does not have access to the folder." The definition stays verbatim from the registry — do NOT rewrite `<bindings.*>` placeholders. See the relevant plugin's `impl.md` for the exact JSON.

> **Layout rule:** Don't pre-compute coordinates. `batch-edit` runs `uip maestro flow format` internally, which arranges nodes horizontally, sets size to `{ "width": 96, "height": 96 }`, and recurses into subflows.

> **Edges go in the same spec as the node.** One `addEdge` op per wiring connection from / to the new node. The `from`/`to` strings use the planned `id` from the same spec — the CLI resolves them after `addNode` runs in spec order. This holds whether one endpoint or both endpoints are added in this step (e.g., scaffolding a fresh subflow). See [Add an edge](#add-an-edge) below for the port-string shape (`<nodeId>.<port>`).

### Delete a node

**Tool:** `Edit` (remove from `nodes[]` + dependent edges + orphaned definitions + `variables.nodes` + `variableUpdates`)

1. Use `Edit` to remove the node object from `nodes`
2. Remove **all edges** where `sourceNodeId` or `targetNodeId` equals the node's `id`
3. If no other node uses the same `type`, remove the definition from `definitions`
4. Remove the node's entry from `variables.nodes`
5. Remove any `variableUpdates` entries keyed by the node's `id`
6. If the node is a connector node, remove its binding from `bindings_v2.json` **only if no other node in the flow uses the same connector**. Bindings are shared at the connector level (keyed by `metadata.Connector`), not per node.

### Add an edge

**Tool:** `Edit` (insert into `edges[]` with `targetPort`)

Use `Edit` to add an edge object to the `edges` array:

```json
{
  "id": "<UNIQUE_EDGE_ID>",
  "sourceNodeId": "<SOURCE_NODE_ID>",
  "sourcePort": "<SOURCE_PORT>",
  "targetNodeId": "<TARGET_NODE_ID>",
  "targetPort": "<TARGET_PORT>"
}
```

**Critical:** `targetPort` is required on every edge. Omitting it produces a validation error.

**Critical:** the outgoing port field is named `sourcePort`, not `sourceHandle`. `sourceHandle` is a UI/runtime term, not valid `.flow` JSON.

**Edge ID:** generate a UUID (matches CLI behavior) or use `e-<sourceNodeId>-<targetNodeId>` if uniqueness across the flow is guaranteed. Short, hand-picked names risk collision when the same source/target pair gets a second edge later.

See each plugin's `planning.md` or [file-format.md — Standard ports](../../shared/file-format.md) for port names by node type.

### Delete an edge

**Tool:** `Edit`

Use `Edit` to remove the edge object from the `edges` array by its `id`.

### Update node inputs

**Tool:** `Edit` (in-place value tweak — preserves node ID and `$vars`)

Use `Edit` to modify the `inputs` object of the target node in-place. No need to delete and re-add.

```json
{
  "id": "checkStatus",
  "type": "core.logic.decision",
  "inputs": {
    "expression": "$vars.fetchData.output.statusCode === 200"
  }
}
```

This is a key advantage of `Edit` — input updates are a single field edit, not the delete + re-add pattern required by the CLI.

---

## Variable Operations

These are `Edit`-only — the CLI does not support variable management. There is no fallback strategy.

### Add a workflow variable

**Tool:** `Edit`

Use `Edit` to add an entry to `variables.globals`:

```json
{
  "id": "<VARIABLE_ID>",
  "direction": "in|out|inout",
  "type": "string|number|boolean|object|array",
  "defaultValue": "<OPTIONAL_DEFAULT>",
  "description": "<OPTIONAL_DESCRIPTION>"
}
```

For `out` variables: add output mapping to **every reachable End node** (see below).
For `inout` variables: add `variableUpdates` entries on nodes that modify the state.

See [variables-and-expressions.md](../../shared/variables-and-expressions.md) for the full schema, type system, and scoping rules.

### Add output mapping on an End node

**Tool:** `Edit`

Use `Edit` to map every `out` variable in `variables.globals` on every reachable End node:

```json
{
  "id": "doneSuccess",
  "type": "core.control.end",
  "typeVersion": "1.0.0",
  "display": { "label": "Done" },
  "inputs": {},
  "outputs": {
    "<VARIABLE_ID>": {
      "source": "=js:<EXPRESSION>"
    }
  }
}
```

Each key in `outputs` must match a variable `id` from `variables.globals` where `direction: "out"`. Missing mappings cause silent runtime failures.

### Add a variable update

**Tool:** `Edit`

Use `Edit` to add an entry to `variables.variableUpdates.<NODE_ID>`:

```json
{
  "variables": {
    "variableUpdates": {
      "<NODE_ID>": [
        {
          "variableId": "<INOUT_VARIABLE_ID>",
          "expression": "=js:<EXPRESSION>"
        }
      ]
    }
  }
}
```

Only `inout` variables can be updated. `in` variables are read-only.

---

## Composite Operations

### Insert a node between two existing nodes

**Tool:** `uip maestro flow batch-edit` (one CLI call that applies bypass-removal + node-add + new-path-wiring atomically).

**Prereq turn:** Run `uip maestro flow registry get <NODE_TYPE> --output json` for the new node type (if a definition isn't already in the file). Pick the new node's `id` here.

**Mutate turn:** One `uip maestro flow batch-edit <flow-file> --spec '@spec.json'`. The spec contains `addNode` + `removeEdge` (the existing bypass) + 2×`addEdge` (the new path):

```json
{
  "operations": [
    { "kind": "addNode", "id": "<NEW_NODE_ID>", "type": "<NODE_TYPE>", "typeVersion": "<DEFINITION_VERSION>", "display": { "label": "<LABEL>" }, "config": { "inputs": {} } },
    { "kind": "removeEdge", "from": "<UPSTREAM_NODE_ID>.<SOURCE_PORT>", "to": "<DOWNSTREAM_NODE_ID>" },
    { "kind": "addEdge", "from": "<UPSTREAM_NODE_ID>.<SOURCE_PORT>", "to": "<NEW_NODE_ID>" },
    { "kind": "addEdge", "from": "<NEW_NODE_ID>", "to": "<DOWNSTREAM_NODE_ID>" }
  ]
}
```

`batch-edit` applies ops in spec order, regenerates `definitions[]` / `variables.nodes[]` / `layout.nodes`, and runs validate + format internally. No separate gate turn.

### Insert a decision branch

**Tool:** `uip maestro flow batch-edit` (one CLI call that adds the decision node, its downstream branch nodes, and the true/false edges).

**Prereq turn:** Run `uip maestro flow registry get core.logic.decision --output json` (if a `core.logic.decision` definition isn't already in the file). Run `registry get` for the downstream node type as well. Pick `id`s for both new nodes here.

**Mutate turn:** One `uip maestro flow batch-edit <flow-file> --spec '@spec.json'`. The spec contains 2×`addNode` (decision + downstream) + edges for the true / false branches:

```json
{
  "operations": [
    { "kind": "addNode", "id": "<DECISION_NODE_ID>", "type": "core.logic.decision", "typeVersion": "<DEFINITION_VERSION>", "display": { "label": "<LABEL>" }, "config": { "inputs": { "expression": "<JS_EXPR>" } } },
    { "kind": "addNode", "id": "<DOWNSTREAM_NODE_ID>", "type": "<DOWNSTREAM_TYPE>", "typeVersion": "<DEFINITION_VERSION>", "display": { "label": "<LABEL>" }, "config": { "inputs": {} } },
    { "kind": "addEdge", "from": "<UPSTREAM_NODE_ID>.<SOURCE_PORT>", "to": "<DECISION_NODE_ID>" },
    { "kind": "addEdge", "from": "<DECISION_NODE_ID>.true", "to": "<DOWNSTREAM_NODE_ID>" },
    { "kind": "addEdge", "from": "<DECISION_NODE_ID>.false", "to": "<EXISTING_FALSE_BRANCH_NODE_ID>" }
  ]
}
```

Decision source ports are `true` / `false`; target port defaults to `input` (omit the `.input` suffix on the `to` field). `batch-edit` runs validate + format internally.

### Remove a node and reconnect

**Tool:** `uip maestro flow batch-edit` (one CLI call: remove the node + add the bypass edge).

**Prereq turn:** `Read` the `.flow` file once to capture the node's upstream and downstream node IDs from `edges[]` — you'll need both for the bypass edge.

**Mutate turn:** One `uip maestro flow batch-edit <flow-file> --spec '@spec.json'`. The spec contains `removeNode` + 1×`addEdge` (the bypass):

```json
{
  "operations": [
    { "kind": "removeNode", "id": "<NODE_ID>" },
    { "kind": "addEdge", "from": "<UPSTREAM_NODE_ID>.<SOURCE_PORT>", "to": "<DOWNSTREAM_NODE_ID>" }
  ]
}
```

`removeNode` cascades: `batch-edit` sweeps `edges[]` for any with matching `sourceNodeId`/`targetNodeId`, prunes orphaned `definitions[]` and `variables.nodes[]` entries, removes the node's `layout.nodes` entry, and (for connector nodes) prunes `bindings_v2.json` only when no remaining node uses the same connector. Validate + format run internally.

### Replace a mock with a real resource node

**Tool:** `uip maestro flow batch-edit` (one CLI call: remove the mock + add the real node with bindings + re-wire edges).

**Prereq turn:** Get the resource node manifest and record the mock's connected edges:

```bash
# In-solution (preferred — no login required):
uip maestro flow registry get "<RESOURCE_NODE_TYPE>" --local --output json

# Tenant registry (if not in solution):
uip maestro flow registry get "<RESOURCE_NODE_TYPE>" --output json
```

Then `Read` the `.flow` file once to capture the mock node's connected edges — you'll need their source/target node IDs to rewire on the new node.

Pick the new node's `id` during planning (before the mutate turn). Both the `addNode` op and every `addEdge` op reference it — the `id` is a planning artifact you decide once and reuse across spec ops.

**Mutate turn:** One `uip maestro flow batch-edit <flow-file> --spec '@spec.json'`. The spec contains `removeNode` (mock) + `addNode` (real resource, with `bindings`) + edge fix-ups:

```json
{
  "operations": [
    { "kind": "removeNode", "id": "<MOCK_NODE_ID>" },
    {
      "kind": "addNode",
      "id": "<NEW_NODE_ID>",
      "type": "<RESOURCE_NODE_TYPE>",
      "typeVersion": "<DEFINITION_VERSION>",
      "display": { "label": "<LABEL>" },
      "config": {
        "inputs": { "<RESOLVED_FIELD>": "<VALUE>" },
        "outputs": {
          "output": { "type": "object", "source": "=result.response", "var": "output" },
          "error":  { "type": "object", "source": "=result.Error",    "var": "error"  }
        }
      },
      "bindings": [
        { "resourceKey": "<RESOURCE_KEY>", "name": "<RESOURCE_NAME>", "value": "<RESOURCE_VALUE>" },
        { "resourceKey": "<RESOURCE_KEY>", "name": "folderPath",       "value": "<FOLDER_PATH>"   }
      ]
    },
    { "kind": "addEdge", "from": "<UPSTREAM_NODE_ID>.<SOURCE_PORT>", "to": "<NEW_NODE_ID>" },
    { "kind": "addEdge", "from": "<NEW_NODE_ID>", "to": "<DOWNSTREAM_NODE_ID>" }
  ]
}
```

The `addNode` op's `config` carries no `model` block — binding/context templates come from the definition that `batch-edit` attaches from the registry. The `bindings` array must include two entries per resource (`name` + `folderPath`) with `resourceKey` matching the definition's `model.bindings.resourceKey`. `batch-edit` merges them into the flow's top-level `bindings[]`, regenerates `variables.nodes[]` and `layout.nodes`, and runs validate + format internally.

### Replace manual trigger with scheduled trigger

**Tool:** `Edit` × 2 (start node in-place, swap definition)

Use `Edit` to modify the start node in-place (no delete/re-add needed):

1. Change `type` from `core.trigger.manual` to `core.trigger.scheduled`
2. Add timer inputs (keep the existing `entryPointId` in `inputs`):
   ```json
   "inputs": {
     "entryPointId": "<existing-uuid>",
     "timerType": "timeCycle",
     "timerPreset": "R/PT1H"
   }
   ```
3. Update the definition in `definitions`:
   - Remove the `core.trigger.manual` definition
   - Add the `core.trigger.scheduled` definition from `uip maestro flow registry get core.trigger.scheduled --output json` (the new definition carries the correct `model.type` and `model.eventDefinition`)
4. Validate: `uip maestro flow validate <ProjectName>.flow --output json`

### Create a subflow

**Tool:** `Edit` (or `Write` if scaffolding from template)

1. Use `Edit` to add a `core.subflow` parent node to `nodes`:
   ```json
   {
     "id": "<SUBFLOW_NODE_ID>",
     "type": "core.subflow",
     "typeVersion": "1.0.0",
     "display": { "label": "<LABEL>" },
     "inputs": {
       "<IN_VAR>": "=js:<EXPRESSION>"
     },
     "outputs": {
       "output": {
         "type": "object",
         "description": "The return value of the subflow",
         "source": "=result.response",
         "var": "output"
       },
       "error": {
         "type": "object",
         "description": "Error information if the subflow fails",
         "source": "=result.Error",
         "var": "error"
       }
     }
   }
   ```

2. Use `Edit` to add a `subflows.<SUBFLOW_NODE_ID>` entry with its own nodes, edges, variables, and layout:
   ```json
   {
     "subflows": {
       "<SUBFLOW_NODE_ID>": {
         "nodes": [
           { "id": "sfStart", "type": "core.trigger.manual", ... },
           { "id": "sfEnd", "type": "core.control.end", ... }
         ],
         "edges": [ ... ],
         "variables": {
           "globals": [
             { "id": "<IN_VAR>", "direction": "in", "type": "..." },
             { "id": "<OUT_VAR>", "direction": "out", "type": "..." }
           ],
           "nodes": []
         },
         "layout": {
           "nodes": {
             "sfStart": { "position": { "x": 200, "y": 144 }, "size": { "width": 96, "height": 96 }, "collapsed": false },
             "sfEnd":   { "position": { "x": 400, "y": 144 }, "size": { "width": 96, "height": 96 }, "collapsed": false }
           }
         }
       }
     }
   }
   ```

3. Subflow's `in` variables must match the parent node's `inputs` keys
4. Map all `out` variables on the subflow's End node `outputs`
5. Parent-scope `$vars` are NOT visible inside the subflow — pass values via inputs
6. Subflow node positions go in the **subflow's own** `layout.nodes` — not in the top-level `layout.nodes`. Each subflow has an independent layout scope.

See [subflow/impl.md](plugins/subflow/impl.md) for the full JSON structure and rules.

---

## Connector Node Configuration (Edit / Write fallback)

When not using `uip maestro flow node configure`, use `Edit` to set up the following manually:

### 1. `inputs.detail` on the node

**Tool:** `Edit`

```json
{
  "inputs": {
    "detail": {
      "connectionId": "<CONNECTION_UUID>",
      "folderKey": "<FOLDER_KEY>",
      "method": "<HTTP_METHOD>",
      "endpoint": "<API_PATH>",
      "bodyParameters": { "<FIELD>": "<VALUE>" },
      "queryParameters": { "<FIELD>": "<VALUE>" },
      "pathParameters": { "<PLACEHOLDER>": "<VALUE>" }
    }
  }
}
```

Source `method`, `endpoint`, and `bodyParameters` / `queryParameters` / `pathParameters` field names from either of these (both read the same upstream IS metadata):

From `uip maestro flow registry get <nodeType> --connection-id <id> --output json`:
- `method` ← `connectorMethodInfo.method`
- `endpoint` ← `connectorMethodInfo.path`
- `bodyParameters.<name>` ← `inputDefinition.fields[].name`
- `queryParameters.<name>` ← `connectorMethodInfo.parameters[]` where `type: query`
- `pathParameters.<name>` ← `connectorMethodInfo.parameters[]` where `type: path` (must match a `{placeholder}` in `endpoint`)

From `uip is resources describe <connector-key> <objectName> --connection-id <id> --operation <Op> --output json`:
- `method` ← `availableOperations[].method`
- `endpoint` ← `availableOperations[].path`
- `bodyParameters.<name>` ← `requestFields[].name`
- `queryParameters.<name>` ← `parameters[]` where `type: query`
- `pathParameters.<name>` ← `parameters[]` where `type: path` (must match a `{placeholder}` in `endpoint`)

### 2. Connection binding in `bindings_v2.json`

**Tool:** `Edit` (or `Write` for a fresh `bindings_v2.json`)

```json
{
  "version": "2.0",
  "resources": [
    {
      "resource": "Connection",
      "key": "<CONNECTION_UUID>",
      "id": "Connection<CONNECTION_UUID>",
      "value": {
        "ConnectionId": {
          "defaultValue": "<CONNECTION_UUID>",
          "isExpression": false,
          "displayName": "<CONNECTOR_KEY> connection"
        }
      },
      "metadata": {
        "ActivityName": "<ACTIVITY_DISPLAY_NAME>",
        "BindingsVersion": "2.2",
        "DisplayLabel": "<CONNECTOR_KEY> connection",
        "UseConnectionService": "true",
        "Connector": "<CONNECTOR_KEY>"
      }
    }
  ]
}
```

See [connector/impl.md](plugins/connector/impl.md) for the full schema and multi-connector examples.
