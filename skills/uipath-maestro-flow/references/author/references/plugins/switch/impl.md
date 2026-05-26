# Switch Node — Implementation

## Node Type

`core.logic.switch`

## Registry Validation

```bash
uip maestro flow registry get core.logic.switch --output json
```

Confirm: input port `input`, dynamic output ports `case-{id}` + `default`, required input `cases`.

## JSON Structure

```json
{
  "id": "routeByPriority",
  "type": "core.logic.switch",
  "typeVersion": "1.0",
  "display": { "label": "Route by Priority" },
  "inputs": {
    "cases": [
      {
        "id": "high",
        "label": "High Priority",
        "expression": "$vars.classify.output.priority === 'high'"
      },
      {
        "id": "medium",
        "label": "Medium Priority",
        "expression": "$vars.classify.output.priority === 'medium'"
      },
      {
        "id": "low",
        "label": "Low Priority",
        "expression": "$vars.classify.output.priority === 'low'"
      }
    ]
  }
}
```

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure above for the node-specific `inputs`.

## Wiring

Each case creates a dynamic output port `case-{id}`. An optional `default` port handles unmatched values. Ensure edge `sourcePort` matches `case-{id}` exactly. See [editing-operations.md](../../editing-operations.md) for edge add procedures.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| No case matched, no default wired | All case expressions false and no default edge | Add a `default` edge or ensure cases are exhaustive |
| Case expression error | Invalid JavaScript in case expression | Check `=js:` expression syntax |
| Wrong port name in edge | Port ID doesn't match case ID | Ensure edge `sourcePort` is `case-{id}` matching the case's `id` field |
| `$vars.nodeId` is undefined | Upstream node not connected or wrong ID | Check edges and node IDs |

## Definition — `core.logic.switch` v1.0 (copy verbatim)

This is the copy-verbatim registry definition for `definitions[]` — distinct from the example `inputs` snippets above, which you adapt. Copy the entire fenced object exactly; do not edit, trim, elide, or merge it with the snippets. Set the node instance `typeVersion` to the `version` shown here.

> Captured from uip 1.2.0 · node version 1.0 · re-capture on CLI upgrade (see [the staleness fallback](../../../../shared/file-format.md#stale-inlined-definition)).

```json
{
  "nodeType": "core.logic.switch",
  "version": "1.0",
  "category": "control-flow",
  "description": "Route to one of many branches by condition",
  "tags": [
    "control-flow",
    "switch",
    "case",
    "when"
  ],
  "sortOrder": 20,
  "display": {
    "label": "Switch",
    "icon": "between-horizontal-start"
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
          "id": "case-{item.id}",
          "type": "source",
          "handleType": "output",
          "label": "{item.label || 'Case ' + (index + 1)}",
          "repeat": "inputs.cases"
        },
        {
          "id": "default",
          "type": "source",
          "handleType": "output",
          "label": "Default",
          "visible": "inputs.hasDefault"
        }
      ],
      "visible": true
    }
  ],
  "debug": {
    "runtime": "clientScript"
  },
  "model": {
    "type": "bpmn:ExclusiveGateway"
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "cases": {
        "type": "array",
        "minItems": 1,
        "errorMessage": "At least one case is required",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "string"
            },
            "label": {
              "type": "string"
            },
            "expression": {
              "type": "string",
              "minLength": 1,
              "errorMessage": "A condition expression is required"
            }
          },
          "required": [
            "expression"
          ]
        }
      },
      "hasDefault": {
        "type": "boolean"
      }
    },
    "required": [
      "cases"
    ]
  },
  "outputDefinition": {
    "matchedCase": {
      "type": "string",
      "description": "The label of the matched case",
      "var": "matchedCase"
    },
    "matchedCaseId": {
      "type": "string",
      "description": "The ID of the matched case (null for default)",
      "var": "matchedCaseId"
    }
  },
  "inputDefaults": {
    "cases": [
      {
        "id": "default-1",
        "label": "Case 1",
        "expression": ""
      },
      {
        "id": "default-2",
        "label": "Case 2",
        "expression": ""
      }
    ],
    "hasDefault": true
  },
  "form": {
    "id": "switch-properties",
    "title": "Switch configuration",
    "sections": [
      {
        "id": "cases",
        "title": "Cases",
        "description": "Each case is evaluated in order. The first condition that returns true is taken.",
        "collapsible": true,
        "defaultExpanded": true,
        "fields": [
          {
            "name": "inputs.cases",
            "type": "custom",
            "label": "Switch cases",
            "component": "case-list-editor",
            "componentProps": {
              "minCases": 1,
              "maxCases": 10,
              "expressionPlaceholder": "e.g., $vars.value <= 30",
              "expressionValidationFields": [
                {
                  "subPath": "expression",
                  "validationMode": "expression",
                  "expectedType": "boolean"
                }
              ]
            }
          },
          {
            "name": "inputs.hasDefault",
            "type": "switch",
            "label": "Include default case",
            "description": "Add a fallback path when no conditions match",
            "defaultValue": true
          }
        ]
      }
    ]
  },
  "runtimeConstraints": {
    "exclude": [
      "api-function"
    ]
  }
}
```
