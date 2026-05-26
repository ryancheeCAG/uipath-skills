# Decision Node — Implementation

## Node Type

`core.logic.decision`

## Registry Validation

```bash
uip maestro flow registry get core.logic.decision --output json
```

Confirm: input port `input`, output ports `true` and `false`, required input `expression`.

## JSON Structure

```json
{
  "id": "checkStatus",
  "type": "core.logic.decision",
  "typeVersion": "1.0",
  "display": { "label": "Check Status" },
  "inputs": {
    "expression": "$vars.fetchData.output.statusCode === 200"
  }
}
```

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure above for the node-specific `inputs`.

## Expression Examples

```javascript
// Simple comparison
$vars.fetchData.output.statusCode === 200

// Boolean field
$vars.processData.output.isValid

// Compound condition
$vars.httpCall.output.statusCode === 200 && $vars.httpCall.output.body.count > 0

// String check
$vars.classify.output.category === "urgent"

// Null check
$vars.lookupUser.output.user !== null
```

## Wiring

Output ports: `true` and `false`. Both branches must be wired. See [editing-operations.md](../../editing-operations.md) for edge add procedures.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Expression does not evaluate to boolean | Expression returns non-boolean value | Ensure expression uses comparison operators (`===`, `>`, etc.) |
| `$vars.nodeId` is undefined | Upstream node not connected or wrong ID | Check edges and node IDs |
| Only one branch wired | Missing true or false edge | Add the missing edge — both branches are required |

## Definition — `core.logic.decision` v1.0 (copy verbatim)

This is the copy-verbatim registry definition for `definitions[]` — distinct from the example `inputs` snippets above, which you adapt. Copy the entire fenced object exactly; do not edit, trim, elide, or merge it with the snippets. Set the node instance `typeVersion` to the `version` shown here.

> Captured from uip 1.2.0 · node version 1.0 · re-capture on CLI upgrade (see [the staleness fallback](../../../../shared/file-format.md#stale-inlined-definition)).

```json
{
  "nodeType": "core.logic.decision",
  "version": "1.0",
  "category": "control-flow",
  "description": "Branch based on a true/false condition",
  "tags": [
    "control-flow",
    "if",
    "loop",
    "switch"
  ],
  "sortOrder": 20,
  "display": {
    "label": "Decision",
    "icon": "trending-up-down"
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
          "id": "true",
          "type": "source",
          "handleType": "output",
          "label": "{inputs.trueLabel}",
          "constraints": {
            "minConnections": 1
          }
        },
        {
          "id": "false",
          "type": "source",
          "handleType": "output",
          "label": "{inputs.falseLabel}",
          "constraints": {
            "minConnections": 1
          }
        }
      ],
      "visible": true
    }
  ],
  "debug": {
    "runtime": "clientScript"
  },
  "model": {
    "type": "bpmn:InclusiveGateway"
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "expression": {
        "type": "string",
        "minLength": 1,
        "errorMessage": "A condition expression is required"
      },
      "trueLabel": {
        "type": "string"
      },
      "falseLabel": {
        "type": "string"
      }
    },
    "required": [
      "expression"
    ]
  },
  "outputDefinition": {
    "matchedCase": {
      "type": "string",
      "description": "The label of the matched branch (true/false label)",
      "var": "matchedCase"
    },
    "matchedCaseId": {
      "type": "string",
      "description": "The branch that was taken (true or false)",
      "var": "matchedCaseId"
    }
  },
  "inputDefaults": {
    "trueLabel": "True",
    "falseLabel": "False"
  },
  "form": {
    "id": "decision-properties",
    "title": "Decision configuration",
    "sections": [
      {
        "id": "condition",
        "title": "Condition",
        "fields": [
          {
            "name": "inputs.expression",
            "type": "custom",
            "component": "script-editor",
            "componentProps": {
              "language": "javascript",
              "returnType": "boolean",
              "validationMode": "expression",
              "minHeight": 100,
              "placeholder": "e.g., $vars.data.status === \"approved\" && $vars.data.amount > 1000"
            },
            "label": "Expression",
            "description": "JavaScript expression that evaluates to true or false"
          },
          {
            "name": "inputs.trueLabel",
            "type": "text",
            "label": "True branch label",
            "description": "Label shown when condition is true"
          },
          {
            "name": "inputs.falseLabel",
            "type": "text",
            "label": "False branch label",
            "description": "Label shown when condition is false"
          }
        ]
      }
    ]
  }
}
```
