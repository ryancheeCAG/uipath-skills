# Merge Node — Implementation

## Node Type

`core.logic.merge`

## Definition source

Copy the verbatim definition from the [Definition section below](#definition--corelogicmerge-v10-copy-verbatim) — no CLI call. The embedded `.Data.Node` is the `definitions[]` entry; set the node `typeVersion` to `1.0`.

Confirm: input port `input` (accepts multiple connections), output port `output`.

## JSON Structure

```json
{
  "id": "joinBranches",
  "type": "core.logic.merge",
  "typeVersion": "1.0",
  "display": { "label": "Join Branches" },
  "inputs": {}
}
```

## Adding / Editing

For step-by-step add, delete, and wiring procedures, see [editing-operations.md](../../editing-operations.md). Use the JSON structure above for the node-specific `inputs`.

## Wiring

- `input` — accepts multiple incoming edges (one per parallel branch). All branches must reach the merge before it continues.
- `output` — single outgoing edge to the next downstream node.

See [editing-operations.md](../../editing-operations.md) for edge add procedures.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| Merge never completes | One parallel branch has no path to the merge node | Ensure all forked branches reach the merge |
| Unexpected execution order | Branches assumed to complete in order | Merge waits for all — don't depend on arrival order |

## Definition — `core.logic.merge` v1.0 (copy verbatim)

This is the copy-verbatim registry definition for `definitions[]` — distinct from the example `inputs` snippets above, which you adapt. Copy the entire fenced object exactly; do not edit, trim, elide, or merge it with the snippets. Set the node instance `typeVersion` to the `version` shown here.

> Captured from uip 1.2.0 · node version 1.0 · re-capture on CLI upgrade (see [the staleness fallback](../../../../shared/file-format.md#stale-inlined-definition)).

```json
{
  "nodeType": "core.logic.merge",
  "version": "1.0",
  "category": "control-flow",
  "description": "Join parallel branches into one path",
  "tags": [
    "control-flow",
    "merge"
  ],
  "sortOrder": 20,
  "display": {
    "label": "Merge",
    "icon": "merge"
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
    "type": "bpmn:ParallelGateway"
  },
  "runtimeConstraints": {
    "exclude": [
      "api-function"
    ]
  }
}
```
