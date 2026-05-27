# Subflow Node — Implementation

## Node Type

`core.subflow`

## Definition source

Copy the verbatim definition from the [Definition section below](#definition--coresubflow-v10-copy-verbatim) — no CLI call. The embedded `.Data.Node` is the `definitions[]` entry; set the node `typeVersion` to `1.0`.

Confirm: input port `input`, output ports `output` and `error`.

## Parent Node JSON

```json
{
  "id": "subflow1",
  "type": "core.subflow",
  "typeVersion": "1.0",
  "display": { "label": "Add Numbers", "icon": "layers" },
  "inputs": {
    "a": 2,
    "b": 3
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

## Subflow Definition

Subflow contents are stored in a top-level `subflows` object keyed by the parent node's ID:

```json
{
  "subflows": {
    "subflow1": {
      "nodes": [
        {
          "id": "subflow1Start",
          "type": "core.trigger.manual",
          "typeVersion": "1.0",
          "display": { "label": "Start" },
          "inputs": {
            "entryPointId": "unique-uuid-here",
            "isDefaultEntryPoint": true
          },
          "outputs": {
            "output": {
              "type": "object",
              "description": "Data passed when manually triggering the workflow.",
              "source": "null",
              "var": "output"
            }
          }
        },
        {
          "id": "script1",
          "type": "core.action.script",
          "typeVersion": "1.0",
          "display": { "label": "Add Numbers" },
          "inputs": {
            "script": "return { result: $vars.subflow1Start.output.a + $vars.subflow1Start.output.b };"
          },
          "outputs": {
            "output": {
              "type": "object",
              "description": "The return value of the script",
              "source": "=result.response",
              "var": "output"
            },
            "error": {
              "type": "object",
              "description": "Error information if the script fails",
              "source": "=result.Error",
              "var": "error",
              "schema": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["code", "message", "detail", "category", "status"],
                "properties": {
                  "code": { "type": "string" },
                  "message": { "type": "string" },
                  "detail": { "type": "string" },
                  "category": { "type": "string" },
                  "status": { "type": "integer" }
                },
                "additionalProperties": false
              }
            }
          },
          "outputs": {
            "output": {
              "type": "object",
              "description": "The return value of the script",
              "source": "=result.response",
              "var": "output"
            },
            "error": {
              "type": "object",
              "description": "Error information if the script fails",
              "source": "=result.Error",
              "var": "error"
            }
          }
        },
        {
          "id": "subflow1End",
          "type": "core.control.end",
          "typeVersion": "1.0",
          "display": { "label": "End" },
          "inputs": {},
          "outputs": {
            "result": { "source": "=js:$vars.script1.output.result" }
          }
        }
      ],
      "edges": [
        {
          "id": "sf-e1",
          "sourceNodeId": "subflow1Start",
          "sourcePort": "output",
          "targetNodeId": "script1",
          "targetPort": "input"
        },
        {
          "id": "sf-e2",
          "sourceNodeId": "script1",
          "sourcePort": "success",
          "targetNodeId": "subflow1End",
          "targetPort": "input"
        }
      ],
      "variables": {
        "globals": [
          {
            "id": "a",
            "direction": "in",
            "type": "number",
            "defaultValue": 0,
            "triggerNodeId": "subflow1Start"
          },
          {
            "id": "b",
            "direction": "in",
            "type": "number",
            "defaultValue": 0,
            "triggerNodeId": "subflow1Start"
          },
          {
            "id": "result",
            "direction": "out",
            "type": "number",
            "defaultValue": 0
          }
        ],
        "nodes": []
      },
      "layout": {
        "nodes": {
          "subflow1Start": { "position": { "x": 200, "y": 144 }, "size": { "width": 96, "height": 96 }, "collapsed": false },
          "script1":       { "position": { "x": 400, "y": 144 }, "size": { "width": 96, "height": 96 }, "collapsed": false },
          "subflow1End":   { "position": { "x": 600, "y": 144 }, "size": { "width": 96, "height": 96 }, "collapsed": false }
        }
      }
    }
  }
}
```

## Subflow Rules

1. Every subflow **must** have its own Start node (`core.trigger.manual`) and End node (`core.control.end`)
2. Subflow `variables.globals` with `direction: "in"` map to the parent node's `inputs`
3. Subflow `in` variables **must** have `triggerNodeId` set to the subflow's Start node ID — this makes them accessible via `$vars.{startNodeId}.output.{varId}`
4. Subflow `variables.globals` with `direction: "out"` map to the parent node's outputs, accessible via `$vars.{subflowNodeId}.output` in the parent flow
5. Parent-scope `$vars` are **not** visible inside the subflow — pass values explicitly via inputs
6. Subflow nodes must have inline `outputs` defined on them (Start node needs `outputs.output`, Script nodes need `outputs.output` and `outputs.error`)
7. Subflows can be nested (subflow inside subflow), up to 3 levels
8. Each subflow has its own `nodes`, `edges`, `variables`, and `layout` sections
9. Subflow node positions go in the subflow's own `layout.nodes` — NOT in the top-level `layout.nodes`. Each subflow scope is independent.

## Creating a Subflow

For the step-by-step procedure, see [Edit/Write: Create a subflow](../../editing-operations-json.md#create-a-subflow). Use the parent node JSON and subflow definition structures above for the node-specific fields.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `$vars.inputData` undefined inside subflow script | Missing `triggerNodeId` on subflow `in` variable, or using `$vars.{varId}` directly | Add `triggerNodeId: "{startNodeId}"` to each `in` variable and access via `$vars.{startNodeId}.output.{varId}` |
| `$vars.parentNode` undefined inside subflow | Parent scope not accessible | Pass values via subflow `in` variables |
| Subflow output is null | Missing output mapping on subflow's End node | Map all `out` variables in the End node's `outputs` |
| Script output is null | Missing inline `outputs` on script node | Add `outputs.output` and `outputs.error` inline on the script node |
| Missing Start/End node | Subflow lacks required trigger or end | Add `core.trigger.manual` (with `outputs` and `entryPointId`) and `core.control.end` to the subflow |
| Nesting limit exceeded | Subflow nested more than 3 levels deep | Flatten the structure or use resource nodes for deeper composition |

## Definition — `core.subflow` v1.0 (copy verbatim)

This is the copy-verbatim registry definition for `definitions[]` — distinct from the example `inputs` snippets above, which you adapt. Copy the entire fenced object exactly; do not edit, trim, elide, or merge it with the snippets. Set the node instance `typeVersion` to the `version` shown here.

> Captured from uip 1.2.0 · node version 1.0 · re-capture on CLI upgrade (see [the staleness fallback](../../../../shared/file-format.md#stale-inlined-definition)).

```json
{
  "nodeType": "core.subflow",
  "version": "1.0",
  "category": "control-flow",
  "description": "Group steps into a reusable subflow",
  "tags": [
    "subflow",
    "composite",
    "container",
    "subprocess"
  ],
  "sortOrder": 20,
  "supportsErrorHandling": true,
  "display": {
    "label": "Subflow",
    "icon": "layers"
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
    "type": "bpmn:SubProcess"
  },
  "outputDefinition": {
    "error": {
      "type": "object",
      "description": "Error information if the node fails",
      "source": "=Error",
      "var": "error",
      "schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": [
          "code",
          "message",
          "detail",
          "category",
          "status"
        ],
        "properties": {
          "code": {
            "type": "string",
            "description": "Error code as a string"
          },
          "message": {
            "type": "string",
            "description": "High-level error message"
          },
          "detail": {
            "type": "string",
            "description": "Detailed error description"
          },
          "category": {
            "type": "string",
            "description": "Error category"
          },
          "status": {
            "type": "integer",
            "description": "HTTP status code"
          }
        },
        "additionalProperties": false
      }
    }
  },
  "drillable": true,
  "runtimeConstraints": {
    "exclude": [
      "api-function"
    ]
  }
}
```
