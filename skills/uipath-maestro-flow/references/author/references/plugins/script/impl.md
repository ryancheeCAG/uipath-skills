# Script Node — Implementation

## Node Type

`core.action.script`

## Registry validation

```bash
uip maestro flow registry get core.action.script --output json
```

Confirm: input port `input`, output port `success`, required input `script` (string, non-empty). See [Action Node Structure — Registry validation](../../../../shared/action-nodes.md#registry-validation) for the shared pattern.

## JSON structure

Follow the [Action Node Structure — Standard JSON skeleton](../../../../shared/action-nodes.md#standard-json-skeleton). The script-specific input is a single `script` string:

```json
{
  "inputs": {
    "script": "const items = $vars.fetchData.output.body.items;\nconst total = items.reduce((sum, i) => sum + i.amount, 0);\nreturn { total, count: items.length };"
  }
}
```

## Adding and editing

See [Action Node Structure — Adding and editing procedures](../../../../shared/action-nodes.md#adding-and-editing-procedures). The script node uses the standard input port `input` and output port `success`; no plugin-specific wiring.

## Script rules

1. **Must `return` an object** — `return { key: value }`, not a bare scalar. The return value becomes `$vars.{nodeId}.output`.
2. **`$vars` is a global** — use it directly: `return { upper: $vars.input1.toUpperCase() }`
3. **JavaScript ES2020 (Jint engine)** — see [variables-and-expressions.md](../../../../shared/variables-and-expressions.md) for supported features and Jint constraints.
4. **No `console.log`** — `console` is not available. Use `return { debug: value }` to inspect values.
5. **No external calls** — use the HTTP node or a connector node for API calls.
6. **30-second timeout** — long-running computations will be killed.

## Common patterns

### Transform and return

```javascript
const items = $vars.fetchData.output.body.items;
const filtered = items.filter(i => i.status === "active");
return { items: filtered, count: filtered.length };
```

### Build a payload for a downstream node

```javascript
return {
  subject: `Order ${$vars.orderId} - Confirmation`,
  body: `Your order of ${$vars.orderTotal} has been processed.`,
  recipient: $vars.customerEmail
};
```

### Error check from upstream

```javascript
const error = $vars.httpCall.error;
if (error) {
  return { hasError: true, message: error.message };
}
return { hasError: false, data: $vars.httpCall.output.body };
```

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Script did not return a value | Missing `return` statement | Add `return { ... }` |
| Return value is not an object | Returned a scalar (`return 42`) | Wrap in object: `return { value: 42 }` |
| `$vars.nodeId` is undefined | Upstream node not connected or wrong ID | Check edges and node IDs |
| Timeout after 30s | Script too expensive | Simplify logic or split into multiple scripts |
| `console is not defined` | Used `console.log()` | Remove — use `return { debug: val }` instead |
| `fetch is not defined` | Tried to make HTTP call | Use an HTTP node or connector node instead |

## Definition — `core.action.script` v1.0 (copy verbatim)

This is the copy-verbatim registry definition for `definitions[]` — distinct from the example `inputs` snippets above, which you adapt. Copy the entire fenced object exactly; do not edit, trim, elide, or merge it with the snippets. Set the node instance `typeVersion` to the `version` shown here.

> Captured from uip 1.2.0 · node version 1.0 · re-capture on CLI upgrade (see [the staleness fallback](../../../../shared/file-format.md#stale-inlined-definition)).

```json
{
  "nodeType": "core.action.script",
  "version": "1.0",
  "category": "data-operations",
  "description": "Run custom JavaScript code",
  "tags": [
    "code",
    "javascript",
    "python"
  ],
  "sortOrder": 35,
  "supportsErrorHandling": true,
  "display": {
    "label": "Script",
    "icon": "code"
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
    },
    {
      "position": "right",
      "handles": [
        {
          "id": "success",
          "type": "source",
          "handleType": "output"
        }
      ]
    }
  ],
  "debug": {
    "runtime": "clientScript"
  },
  "model": {
    "type": "bpmn:ScriptTask"
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "script": {
        "type": "string",
        "minLength": 1,
        "errorMessage": "A script function is required",
        "validationSeverity": "warning"
      }
    },
    "required": [
      "script"
    ]
  },
  "inputDefaults": {
    "script": ""
  },
  "outputDefinition": {
    "output": {
      "type": "object",
      "description": "The return value of the script",
      "source": "=result.response",
      "var": "output"
    },
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
  "form": {
    "id": "script-properties",
    "title": "Script configuration",
    "sections": [
      {
        "id": "script",
        "title": "Script",
        "collapsible": true,
        "defaultExpanded": true,
        "fields": [
          {
            "name": "inputs.script",
            "type": "custom",
            "component": "script-editor",
            "componentProps": {
              "language": "javascript",
              "returnType": "any",
              "validationMode": "script",
              "minHeight": 200,
              "placeholder": " // Return an object with your result\nreturn {\n  message: \"Web request response\",\n  data: $vars.httpRequest1.output\n                  };"
            },
            "label": "Code",
            "description": "JavaScript expression that returns a result object"
          }
        ]
      }
    ]
  }
}
```
