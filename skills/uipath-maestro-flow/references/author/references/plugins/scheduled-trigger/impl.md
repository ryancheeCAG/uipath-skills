# Scheduled Trigger — Implementation

## Node Type

`core.trigger.scheduled`

## Definition source

Copy the verbatim definition from the [Definition section below](#definition--coretriggerscheduled-v11-copy-verbatim) — no CLI call. The embedded `.Data.Node` is the `definitions[]` entry; set the node `typeVersion` to `1.1`.

Confirm: no input port, output port `output`, required inputs `timerType` and `timerPreset`.

## JSON Structure

### Preset Frequency

```json
{
  "id": "scheduledStart",
  "type": "core.trigger.scheduled",
  "typeVersion": "1.0",
  "display": { "label": "Every Hour" },
  "inputs": {
    "entryPointId": "<uuid>",
    "timerType": "timeCycle",
    "timerPreset": "R/PT1H"
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the trigger.",
      "source": "=result.response",
      "var": "output"
    }
  }
}
```

### Custom Frequency

```json
{
  "id": "scheduledStart",
  "type": "core.trigger.scheduled",
  "typeVersion": "1.0",
  "display": { "label": "Every 45 Minutes" },
  "inputs": {
    "entryPointId": "<uuid>",
    "timerType": "timeCycle",
    "timerPreset": "custom",
    "timerValue": "R/PT45M"
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the trigger.",
      "source": "=result.response",
      "var": "output"
    }
  }
}
```

BPMN type (`bpmn:StartEvent`) and event definition (`bpmn:TimerEventDefinition`) come from the `core.trigger.scheduled` entry in `definitions[]` — never on the instance.

## Replacing Manual Trigger with Scheduled

For the step-by-step procedure, use [Edit/Write: Replace manual trigger with scheduled trigger](../../editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger). Use the JSON structures above for the node-specific `inputs`.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Invalid timer value | Malformed ISO 8601 repeating interval | Check format: `R/P[duration]` (e.g., `R/PT1H`) |
| Missing `timerValue` | `timerPreset: "custom"` but no `timerValue` | Add `timerValue` with ISO 8601 repeating interval |
| BPMN timer event not emitted | `core.trigger.scheduled` definition wrong or missing | Re-copy the verbatim definition from the [Definition section below](#definition--coretriggerscheduled-v11-copy-verbatim) — it carries `model.eventDefinition: "bpmn:TimerEventDefinition"`. If still wrong, the embedded copy may be stale — fall back to `uip maestro flow registry get core.trigger.scheduled --output json` |
| Two triggers in flow | Both manual and scheduled triggers exist | Remove one — flows must have exactly one trigger |

## Definition — `core.trigger.scheduled` v1.1 (copy verbatim)

This is the copy-verbatim registry definition for `definitions[]` — distinct from the example `inputs` snippets above, which you adapt. Copy the entire fenced object exactly; do not edit, trim, elide, or merge it with the snippets. Set the node instance `typeVersion` to the `version` shown here.

> Captured from uip 1.2.0 · node version 1.1 · re-capture on CLI upgrade (see [the staleness fallback](../../../../shared/file-format.md#stale-inlined-definition)).

```json
{
  "nodeType": "core.trigger.scheduled",
  "runtimeConstraints": {
    "exclude": [
      "api-function"
    ]
  },
  "version": "1.1",
  "category": "trigger",
  "description": "Start workflow on a schedule or interval",
  "tags": [
    "trigger",
    "start",
    "event",
    "schedule",
    "timer",
    "cron"
  ],
  "sortOrder": 40,
  "display": {
    "label": "Scheduled trigger",
    "icon": "calendar-clock",
    "shape": "circle"
  },
  "handleConfiguration": [
    {
      "position": "right",
      "handles": [
        {
          "id": "output",
          "type": "source",
          "handleType": "output",
          "showButton": true,
          "constraints": {
            "forbiddenTargetCategories": [
              "trigger"
            ]
          }
        }
      ],
      "visible": true
    }
  ],
  "model": {
    "type": "bpmn:StartEvent",
    "entryPointId": true,
    "eventDefinition": "bpmn:TimerEventDefinition",
    "values": {
      "timerType": "inputs.timerType",
      "timerValue": "inputs.timerValue",
      "timerPreset": "inputs.timerPreset"
    }
  },
  "toolbarExtensions": {
    "design": {
      "actions": [
        {
          "id": "change-trigger-type",
          "icon": "square-mouse-pointer",
          "label": "Change trigger type"
        }
      ]
    }
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "timerType": {
        "type": "string",
        "minLength": 1
      },
      "timerPreset": {
        "type": "string",
        "minLength": 1,
        "errorMessage": "Frequency is required"
      },
      "timerValue": {
        "type": "string"
      }
    },
    "required": [
      "timerPreset"
    ],
    "if": {
      "properties": {
        "timerPreset": {
          "const": "custom"
        }
      }
    },
    "then": {
      "required": [
        "timerValue"
      ],
      "properties": {
        "timerValue": {
          "type": "string",
          "minLength": 1,
          "pattern": "^R\\d*\\/(P(?=\\d|T)(\\d+Y)?(\\d+M)?(\\d+W)?(\\d+D)?(T(?=\\d)(\\d+H)?(\\d+M)?(\\d+S)?)?(\\/\\d{4}-\\d{2}-\\d{2}(T\\d{2}:\\d{2}(:\\d{2}(\\.\\d+)?)?(Z|[+-]\\d{2}:\\d{2})?)?)?|\\d{4}-\\d{2}-\\d{2}(T\\d{2}:\\d{2}(:\\d{2}(\\.\\d+)?)?(Z|[+-]\\d{2}:\\d{2})?)?\\/P(?=\\d|T)(\\d+Y)?(\\d+M)?(\\d+W)?(\\d+D)?(T(?=\\d)(\\d+H)?(\\d+M)?(\\d+S)?)?)$",
          "errorMessage": {
            "minLength": "Cycle expression is required",
            "pattern": "Cycle expression must be in ISO 8601 repeating interval format (e.g., R/PT1H, R/P1D, R/2026-05-14T09:00:00Z/P1W)"
          }
        }
      }
    }
  },
  "inputDefaults": {
    "timerType": "timeCycle",
    "timerPreset": "R/PT1H"
  },
  "form": {
    "id": "scheduled-trigger-properties",
    "title": "Scheduled trigger",
    "sections": [
      {
        "id": "schedule",
        "title": "Schedule",
        "collapsible": false,
        "defaultExpanded": true,
        "fields": [
          {
            "name": "inputs.timerPreset",
            "type": "select",
            "label": "Frequency",
            "description": "Runs at fixed intervals aligned to the clock (e.g., every hour on the hour)",
            "options": [
              {
                "label": "Every 5 minutes",
                "value": "R/PT5M"
              },
              {
                "label": "Every 15 minutes",
                "value": "R/PT15M"
              },
              {
                "label": "Every 30 minutes",
                "value": "R/PT30M"
              },
              {
                "label": "Every hour",
                "value": "R/PT1H"
              },
              {
                "label": "Every 6 hours",
                "value": "R/PT6H"
              },
              {
                "label": "Every 12 hours",
                "value": "R/PT12H"
              },
              {
                "label": "Daily",
                "value": "R/P1D"
              },
              {
                "label": "Weekly",
                "value": "R/P1W"
              },
              {
                "label": "Custom",
                "value": "custom"
              }
            ]
          },
          {
            "name": "inputs.timerValue",
            "type": "custom",
            "component": "iso-expression-field",
            "label": "Cycle expression",
            "placeholder": "R/PT1H",
            "description": "ISO 8601 repeating interval - use the AI button to generate from natural language",
            "componentProps": {
              "expressionType": "repeating-interval"
            },
            "rules": [
              {
                "id": "custom-cycle",
                "conditions": [
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
          }
        ]
      }
    ]
  }
}
```
