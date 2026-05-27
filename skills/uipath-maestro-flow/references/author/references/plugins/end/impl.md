# End Node — Implementation

## Node Type

`core.control.end`

## Definition source

Copy the verbatim definition from the [Definition section below](#definition--corecontrolend-v10-copy-verbatim) — no CLI call. The embedded `.Data.Node` is the `definitions[]` entry; set the node `typeVersion` to `1.0`.

Confirm: input port `input`, no output ports.

## JSON Structure

### Without Output Mapping

```json
{
  "id": "doneSuccess",
  "type": "core.control.end",
  "typeVersion": "1.0",
  "display": { "label": "Done" },
  "inputs": {}
}
```

### With Output Mapping

When the workflow declares `out` variables, every End node must map all of them:

```json
{
  "id": "doneSuccess",
  "type": "core.control.end",
  "typeVersion": "1.0",
  "display": { "label": "Done" },
  "inputs": {},
  "outputs": {
    "processedCount": {
      "source": "=js:$vars.processData.output.count"
    },
    "resultSummary": {
      "source": "=js:$vars.formatOutput.output.summary"
    }
  }
}
```

Each key in `outputs` must match a variable `id` from `variables.globals` where `direction: "out"`.

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure above for the node-specific `inputs` and `outputs`.

Output mapping must be added with `Edit` against the `.flow` file — see [Edit/Write: Add output mapping](../../editing-operations-json.md#add-output-mapping-on-an-end-node).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Missing output mapping | `out` variable not mapped on this End node | Add `outputs.{varId}.source` expression for every `out` variable |
| Output expression unresolvable | `$vars` reference points to unreachable node | Ensure the node is upstream and connected via edges |
| Runtime silent failure | Output mapping missing on one reachable End node | Check **all** End nodes, not just the primary path |

## Definition — `core.control.end` v1.0 (copy verbatim)

This is the copy-verbatim registry definition for `definitions[]` — distinct from the example `inputs` snippets above, which you adapt. Copy the entire fenced object exactly; do not edit, trim, elide, or merge it with the snippets. Set the node instance `typeVersion` to the `version` shown here.

> Captured from uip 1.2.0 · node version 1.0 · re-capture on CLI upgrade (see [the staleness fallback](../../../../shared/file-format.md#stale-inlined-definition)).

```json
{
  "nodeType": "core.control.end",
  "version": "1.0",
  "category": "control-flow",
  "description": "Mark the end of a workflow path",
  "tags": [
    "control-flow",
    "end",
    "finish",
    "complete"
  ],
  "sortOrder": 20,
  "display": {
    "label": "End",
    "icon": "circle-check",
    "shape": "circle"
  },
  "handleConfiguration": [
    {
      "position": "left",
      "handles": [
        {
          "id": "input",
          "type": "target",
          "handleType": "input"
        }
      ]
    }
  ],
  "model": {
    "type": "bpmn:EndEvent"
  },
  "runtimeConstraints": {
    "exclude": [
      "api-function"
    ]
  }
}
```
