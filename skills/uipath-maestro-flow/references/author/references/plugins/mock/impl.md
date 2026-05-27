# Mock — Implementation

## Node Type

`core.logic.mock`

## Definition source

Copy the verbatim definition from the [Definition section below](#definition--corelogicmock-v10-copy-verbatim) — no CLI call. The embedded `.Data.Node` is the `definitions[]` entry; set the node `typeVersion` to `1.0`.

Confirm: input port `input`, output port `output`, no required inputs. Definition version `1.0`.

## JSON Structure

```json
{
  "id": "<nodeId>",
  "type": "core.logic.mock",
  "typeVersion": "1.0",
  "display": { "label": "<Placeholder Label>" },
  "inputs": {},
  "outputs": {
    "output": {
      "type": "object",
      "description": "Mock output value",
      "source": "=result.response",
      "var": "output"
    }
  }
}
```

BPMN type (`bpmn:Task`) comes from the `core.logic.mock` entry in `definitions[]` — never on the instance.

## Adding and Editing

A mock uses the standard `input` port and `output` port; no plugin-specific wiring. For add / delete / wire procedures see [editing-operations.md](../../editing-operations.md) and the JSON recipes in [editing-operations-json.md](../../editing-operations-json.md).

## Replacing a Mock with a Real Node

When the resource becomes available, swap the mock for the real resource node: [Replace a mock with a real resource node](../../editing-operations-json.md#replace-a-mock-with-a-real-resource-node). Discovery and decision steps are in [planning.md](planning.md).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Mock left at publish | Placeholder never resolved | Replace with the real resource node, or confirm with the user it is intentional and note it in Open Questions |
| `$vars.<mockId>.output` is empty downstream | Mock emits only a placeholder object | Expected — wire real logic once the mock is replaced |
| Mock used where a sibling resource exists | Should have used `--local` discovery | Replace with the in-solution resource node ([planning.md](planning.md)) |

## Definition — `core.logic.mock` v1.0 (copy verbatim)

This is the copy-verbatim registry definition for `definitions[]` — distinct from the example `inputs` snippets above, which you adapt. Copy the entire fenced object exactly; do not edit, trim, elide, or merge it with the snippets. Set the node instance `typeVersion` to the `version` shown here.

> Captured from uip 1.2.0 · node version 1.0 · re-capture on CLI upgrade (see [the staleness fallback](../../../../shared/file-format.md#stale-inlined-definition)).

```json
{
  "nodeType": "core.logic.mock",
  "version": "1.0",
  "category": "control-flow",
  "description": "Placeholder node for prototyping",
  "tags": [
    "blank",
    "todo"
  ],
  "sortOrder": 20,
  "display": {
    "label": "Mock",
    "icon": "square-dashed"
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
      ],
      "visible": true
    },
    {
      "position": "right",
      "handles": [
        {
          "id": "output",
          "type": "source",
          "handleType": "output"
        }
      ],
      "visible": true
    }
  ],
  "model": {
    "type": "bpmn:Task"
  },
  "outputDefinition": {
    "output": {
      "type": "object",
      "description": "Mock output value",
      "source": "null",
      "var": "output"
    }
  },
  "runtimeConstraints": {
    "exclude": [
      "api-function"
    ]
  }
}
```

