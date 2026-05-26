# Delay Node — Implementation

## Node Type

`core.logic.delay`

## Registry Validation

```bash
uip maestro flow registry get core.logic.delay --output json
```

Confirm: input port `input`, output port `output`, required inputs `timerType` and `timerPreset`.

## JSON Structure

### Duration-Based (Preset)

```json
{
  "id": "wait15min",
  "type": "core.logic.delay",
  "typeVersion": "1.0",
  "display": { "label": "Wait 15 Minutes" },
  "inputs": {
    "timerType": "timeDuration",
    "timerPreset": "PT15M"
  }
}
```

### Duration-Based (Custom ISO 8601)

```json
{
  "id": "waitCustom",
  "type": "core.logic.delay",
  "typeVersion": "1.0",
  "display": { "label": "Wait 1 Day 5 Hours" },
  "inputs": {
    "timerType": "timeDuration",
    "timerPreset": "custom",
    "timerValue": "P1DT5H30M"
  }
}
```

### Date-Based (Wait Until)

```json
{
  "id": "waitUntil",
  "type": "core.logic.delay",
  "typeVersion": "1.0",
  "display": { "label": "Wait Until April 15" },
  "inputs": {
    "timerType": "timeDate",
    "timerPreset": "custom",
    "timerDate": "=js:$vars.scheduledDate"
  }
}
```

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure above for the node-specific `inputs`. BPMN type and event definition come from the definition in `definitions[]`.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Invalid timer value | Malformed ISO 8601 string | Check format: `P[n]Y[n]M[n]W[n]DT[n]H[n]M[n]S` |
| Missing `timerValue` | `timerPreset: "custom"` but no `timerValue` | Add `timerValue` with ISO 8601 duration |
| Missing `timerDate` | `timerType: "timeDate"` but no `timerDate` | Add `timerDate` with ISO 8601 datetime or `=js:` expression |
| BPMN timer event not emitted | Wrong `core.logic.delay` definition in `definitions[]` | Re-copy from `uip maestro flow registry get core.logic.delay --output json` — the definition carries `model.eventDefinition: "bpmn:TimerEventDefinition"` |

## Definition — `core.logic.delay` v1.0 (copy verbatim)

This is the copy-verbatim registry definition for `definitions[]` — distinct from the example `inputs` snippets above, which you adapt. Copy the entire fenced object exactly; do not edit, trim, elide, or merge it with the snippets. Set the node instance `typeVersion` to the `version` shown here.

> Captured from uip 1.2.0 · node version 1.0 · re-capture on CLI upgrade (see [the staleness fallback](../../../../shared/file-format.md#stale-inlined-definition)).

```json
{
  "nodeType": "core.logic.delay",
  "version": "1.0",
  "category": "control-flow",
  "description": "Pause execution for a duration or until a date",
  "tags": [
    "control",
    "flow",
    "logic",
    "delay",
    "timer",
    "wait"
  ],
  "sortOrder": 20,
  "display": {
    "label": "Delay",
    "icon": "timer"
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
          "id": "output",
          "type": "source",
          "handleType": "output"
        }
      ]
    }
  ],
  "model": {
    "type": "bpmn:IntermediateCatchEvent",
    "eventDefinition": "bpmn:TimerEventDefinition",
    "values": {
      "timerType": "inputs.timerType",
      "timerValue": "inputs.timerValue",
      "timerPreset": "inputs.timerPreset",
      "timerDate": "inputs.timerDate"
    }
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "timerType": {
        "type": "string",
        "minLength": 1,
        "errorMessage": "Timer type is required"
      },
      "timerPreset": {
        "type": "string",
        "minLength": 1,
        "errorMessage": "Duration is required"
      },
      "timerValue": {
        "type": "string"
      },
      "timerDate": {
        "type": "string"
      }
    },
    "required": [
      "timerType",
      "timerPreset"
    ],
    "allOf": [
      {
        "if": {
          "properties": {
            "timerType": {
              "const": "timeDuration"
            },
            "timerPreset": {
              "const": "custom"
            }
          },
          "required": [
            "timerType",
            "timerPreset"
          ]
        },
        "then": {
          "properties": {
            "timerValue": {
              "type": "string",
              "minLength": 1,
              "pattern": "^P(?!$)(\\d+Y)?(\\d+M)?(\\d+W)?(\\d+D)?(T(?=\\d)(\\d+H)?(\\d+M)?(\\d+S)?)?$",
              "errorMessage": "Custom duration is required (ISO 8601 format, e.g., PT15M, PT1H, P1D)"
            }
          },
          "required": [
            "timerValue"
          ]
        }
      },
      {
        "if": {
          "properties": {
            "timerType": {
              "const": "timeDate"
            }
          },
          "required": [
            "timerType"
          ]
        },
        "then": {
          "properties": {
            "timerDate": {
              "type": "string",
              "minLength": 1,
              "errorMessage": "Date is required"
            }
          },
          "required": [
            "timerDate"
          ]
        }
      }
    ]
  },
  "inputDefaults": {
    "timerType": "timeDuration",
    "timerPreset": "PT15M"
  },
  "form": {
    "id": "delay-properties",
    "title": "Delay",
    "sections": [
      {
        "id": "timer",
        "title": "Timer",
        "collapsible": true,
        "defaultExpanded": true,
        "fields": [
          {
            "name": "inputs.timerType",
            "type": "select",
            "label": "Type",
            "options": [
              {
                "label": "Duration",
                "value": "timeDuration"
              },
              {
                "label": "Date",
                "value": "timeDate"
              }
            ]
          },
          {
            "name": "inputs.timerPreset",
            "type": "select",
            "label": "Duration",
            "options": [
              {
                "label": "5 seconds",
                "value": "PT5S"
              },
              {
                "label": "15 seconds",
                "value": "PT15S"
              },
              {
                "label": "30 seconds",
                "value": "PT30S"
              },
              {
                "label": "1 minute",
                "value": "PT1M"
              },
              {
                "label": "5 minutes",
                "value": "PT5M"
              },
              {
                "label": "15 minutes",
                "value": "PT15M"
              },
              {
                "label": "30 minutes",
                "value": "PT30M"
              },
              {
                "label": "1 hour",
                "value": "PT1H"
              },
              {
                "label": "6 hours",
                "value": "PT6H"
              },
              {
                "label": "12 hours",
                "value": "PT12H"
              },
              {
                "label": "1 day",
                "value": "P1D"
              },
              {
                "label": "1 week",
                "value": "P1W"
              },
              {
                "label": "Custom",
                "value": "custom"
              }
            ],
            "rules": [
              {
                "id": "duration-presets",
                "conditions": [
                  {
                    "when": "inputs.timerType",
                    "is": "timeDuration"
                  }
                ],
                "effects": {
                  "visible": true
                }
              }
            ]
          },
          {
            "name": "inputs.timerValue",
            "type": "custom",
            "component": "iso-expression-field",
            "label": "Custom duration",
            "placeholder": "PT15M",
            "description": "ISO 8601 duration - use the AI button to generate from natural language",
            "componentProps": {
              "expressionType": "duration",
              "supportsExpressions": true
            },
            "rules": [
              {
                "id": "custom-duration",
                "conditions": [
                  {
                    "when": "inputs.timerType",
                    "is": "timeDuration"
                  },
                  {
                    "when": "inputs.timerPreset",
                    "is": "custom"
                  }
                ],
                "effects": {
                  "visible": true
                }
              }
            ]
          },
          {
            "name": "inputs.timerDate",
            "type": "datetime",
            "label": "Value",
            "description": "The date and time when the workflow should continue",
            "rules": [
              {
                "id": "date-format",
                "conditions": [
                  {
                    "when": "inputs.timerType",
                    "is": "timeDate"
                  }
                ],
                "effects": {
                  "visible": true
                }
              }
            ]
          }
        ]
      }
    ]
  }
}
```
