# Action Node Structure

Reference for the boilerplate shared by every action-node `impl.md` in this skill. Plugin docs should link here for the standard parts and only spell out what is plugin-specific: the registry type string, plugin-specific input fields, plugin-specific rules, debug entries, and node-type configuration workflows.

## Definition contract

Every action node needs its `.Data.Node` definition in `definitions[]`, with the node instance `typeVersion` matching the definition `version`.

- **In-scope built-in `core.*` nodes** (script, transform, decision, switch, loop, merge, delay, end, terminate, subflow, manual/scheduled triggers, mock): the verbatim definition is **embedded** in that node's plugin `impl.md` (`## Definition — <type> v<version> (copy verbatim)`). Copy it from there — no CLI call.
- **CLI-fetched nodes** (`core.action.http` / `core.action.http.v2`, `core.action.queue.*`, connector `uipath.connector.*`, resource `uipath.core.*` / `uipath.*`): fetch with `uip maestro flow registry get <node-type> --output json` and copy the returned `.Data.Node`.

Either way, inspect `handleConfiguration` for the input port name, output port name(s), required inputs, and (where applicable) the model `serviceType`. Plugin `impl.md` records what to confirm for that specific node type.

## Standard JSON skeleton

All action nodes share this base shape on the node instance:

```json
{
  "id": "<nodeId>",
  "type": "<node-type>",
  "typeVersion": "<version>",
  "display": { "label": "<Label>" },
  "inputs": { /* plugin-specific — see plugin impl.md */ },
  "outputs": {
    "output": {
      "type": "object",
      "description": "<plugin-specific description>",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the action fails.",
      "source": "=result.Error",
      "var": "error"
    }
  }
}
```

`outputs.output` documents the success payload referenced downstream as `=js:$vars.{nodeId}.output`. `outputs.error` documents the failure shape; the runtime routes to the implicit `error` port when the action faults. See [Implicit error port on action nodes](file-format.md#implicit-error-port-on-action-nodes).

> **For action nodes the instance `outputs` block is documentation, not the runtime contract.** What actually exposes the node's outputs as process-level `$vars.{nodeId}.output` is the matching `variables.nodes[]` entry — see [file-format.md — Node outputs](file-format.md#node-outputs). The BPMN emitter ignores the action-node instance `outputs` block at serialization (the manifest's `outputDefinition` drives the activity-side mapping). End / terminate nodes are the exception: their instance `outputs` block IS consumed to map workflow-level `out` variables. `uip maestro flow format` regenerates `variables.nodes[]` from the current node graph (MST-9972), so running format after structural edits self-heals an omitted entry.

## Standard ports

| Direction | Common name(s) | Notes |
| --- | --- | --- |
| Input (target) | `input` | Every action node accepts a single input edge on `input`. |
| Output (success, source) | `output`, `default`, or `success` | Name varies by plugin — the node's definition (embedded block or `registry get`) is authoritative. |
| Output (error, source) | `error` | Implicit on every action node via `outputs.error`. |

Some plugins add dynamic source ports (e.g., HTTP `branch-{id}` from `inputs.branches`); those are documented in the plugin's own `impl.md`.

## Adding and editing procedures

For step-by-step add, delete, and wiring instructions, see [editing-operations.md](../author/references/editing-operations.md) and the JSON recipes in [editing-operations-json.md](../author/references/editing-operations-json.md). Plugin `impl.md` files describe only the inputs and wiring patterns that are specific to the node type.

## Migrating a plugin to reference this template

When converting an existing plugin `impl.md` to use this template:

- **Keep in the plugin:** registry type string, `typeVersion`, plugin-specific input fields, plugin-specific configuration workflow (e.g., `node configure` for HTTP/connector nodes), plugin-specific rules, common patterns, debug table.
- **Replace with a link here:** generic JSON skeleton, generic `outputs` block (`=result.response` / `=result.Error`), generic registry-validation prose, generic "Adding / Editing" cross-reference.
