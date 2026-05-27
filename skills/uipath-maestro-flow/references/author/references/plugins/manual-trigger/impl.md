# Manual Trigger — Implementation

## Node Type

`core.trigger.manual`

## Definition source

Copy the verbatim definition from the [Definition section below](#definition--coretriggermanual-v10-copy-verbatim) — no CLI call. The embedded `.Data.Node` is the `definitions[]` entry; set the node `typeVersion` to `1.0`.

Confirm: no input port, output port `output`, no required inputs. Definition version `1.0`.

> **Usually already present.** `flow init` scaffolds this node (id `start`) and its `definitions[]` entry. You only author it from scratch when rebuilding or swapping a trigger — see [planning.md](planning.md).

## JSON Structure

```json
{
  "id": "start",
  "type": "core.trigger.manual",
  "typeVersion": "1.0",
  "display": { "label": "Manual Trigger" },
  "inputs": {
    "entryPointId": "<uuid>"
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "Data passed when manually triggering the workflow.",
      "source": "=result.response",
      "var": "output"
    }
  }
}
```

BPMN type (`bpmn:StartEvent`) comes from the `core.trigger.manual` entry in `definitions[]` — never on the instance. Instance-specific identity (`entryPointId`, and `isDefaultEntryPoint` for subflow triggers) lives under `inputs` — see [file-format.md — Instance-specific identity fields](../../../../shared/file-format.md#instance-specific-identity-fields).

## Replacing Manual Trigger with Scheduled

To switch a flow from manual to scheduled start, use the Edit/Write recipe [Replace manual trigger with scheduled trigger](../../editing-operations-json.md#replace-manual-trigger-with-scheduled-trigger). The scheduled-trigger node-specific `inputs` are in [scheduled-trigger/impl.md](../scheduled-trigger/impl.md).

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Two triggers in flow | Both manual and scheduled (or a connector) trigger exist | Remove one — flows must have exactly one trigger |
| Missing `entryPointId` | Trigger instance has no `inputs.entryPointId` | Add a stable UUID at `inputs.entryPointId` |
| Trigger not first | Manual trigger wired downstream of another node | The trigger must be the topology's first node |

## Definition — `core.trigger.manual` v1.0 (copy verbatim)

This is the copy-verbatim registry definition for `definitions[]` — distinct from the example `inputs` snippets above, which you adapt. Copy the entire fenced object exactly; do not edit, trim, elide, or merge it with the snippets. Set the node instance `typeVersion` to the `version` shown here.

> Captured from uip 1.2.0 · node version 1.0 · re-capture on CLI upgrade (see [the staleness fallback](../../../../shared/file-format.md#stale-inlined-definition)).

```json
{
  "nodeType": "core.trigger.manual",
  "version": "1.0",
  "category": "trigger",
  "description": "Start workflow manually",
  "tags": [
    "trigger",
    "start",
    "manual"
  ],
  "sortOrder": 40,
  "display": {
    "label": "Manual trigger",
    "icon": "play",
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
    "entryPointId": true
  },
  "outputDefinition": {
    "output": {
      "type": "object",
      "description": "Data passed when manually triggering the workflow.",
      "source": "null",
      "var": "output"
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
  }
}
```

