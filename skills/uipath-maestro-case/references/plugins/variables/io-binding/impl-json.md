# I/O Binding — Implementation

> **Phase split.** Phase 3 only (Step 9.8). Phase 2 writes task shape (schema with empty `value` fields) but does not bind values. See [`../../../phased-execution.md`](../../../phased-execution.md).

Wire task inputs by editing `caseplan.json` directly. Runs after all tasks are created and enriched (Step 9) and after global variable + output wiring is complete.

## Task Input Shape

`task.data.inputs[]` — binding = setting `value`:

```json
{ "name": "in_CustomerId", "type": "string",
  "id": "vA1b2C3d4", "var": "vA1b2C3d4",
  "elementId": "Stage_verify-tKYC001",
  "value": "=vars.customerId" }
```

Inputs are populated with empty `value` from the `tasks describe` schema when `data.context.taskTypeId` is set during the task plugin's impl-json write. Input IDs are random (`v` + 8 chars).

## Task Output Shape

`task.data.outputs[]` — read-only, set at enrichment:

```json
{ "name": "KycResult", "type": "string",
  "id": "kycResult", "var": "kycResult", "value": "kycResult",
  "source": "=KycResult", "target": "=kycResult",
  "elementId": "Stage_verify-tKYC001" }
```

Output IDs are name-based camelCase per [uniqueness rule](../global-vars/impl-json.md#uniqueness-rule). `source` reads from the task response — never changes even when `var` is counter-suffixed.

## Binding Procedure

For each task input in `tasks.md`:

**Literals/expressions** — write the value string directly to `input.value`:
```
"=vars.amount"  |  "=metadata.ExternalId"  |  "50"  |  "=js:new Date()"
```

**Cross-task references** (`input <- "Stage A"."Task X".outputName`) — resolve first:

1. Find Stage A by `data.label`, Task X by `displayName`
2. Find output by `name` in `task.data.outputs[]`, read its `var` field
3. Write `=vars.<var>` to target input's `value`

```text
# pseudocode — not executed. Realize via Read → reason → Write/Edit.
src_output = find_output_by_name(src_task, "outputName")
target_input["value"] = f"=vars.{src_output['var']}"
```

After all bindings, run the end-of-Phase-3 validator. It performs three cross-reference checks:

### Check 1 — `=vars.X` reference resolution

Verify every bound input has a non-empty `value`, and every `=vars.X` reference resolves to an existing entry in one of:
- Any task `data.outputs[].id` (the resolver match key; mirrors `var` under skill convention)
- Variables `inputOutputs[].id`
- Variables `inputs[].id`

Variables array path is schema-dependent — `root.data.uipath.variables.{inputOutputs,inputs}[].id` in v19, top-level `variables.{inputOutputs,inputs}[].id` in v20 (Rule 18).

> **Scan key:** match by `.id`, NOT `.var`. The runtime resolver matches on `Variable.id` (`VariablesService.findVariableByVariableId`). Under the skill convention `id === var` on self-declaring outputs, scanning by `.var` is harmless in practice, but `.id` is symmetric with the resolver.

Also scan `=vars.X` references in:
- Edge guard expressions (`edges[].data.conditionExpression`)
- Entry / exit condition expressions (stage and task)
- SLA expressions
- `=js:` expressions anywhere they appear

Same resolution rule applies — these are read-side consumers of the variable namespace.

### Check 2 — Out-arg producer presence (Q10 Option II)

For every entry in `root.data.uipath.variables.outputs[]` (formal Out-arg entries), the entry's `var` field is a POINTER to the variable slot that should hold the value at case end (audit knowledge doc §4.6). Validation gates on whether the SDD declared a `Default`:

| SDD Case Variables row for this Out-arg | Required at validate time | If missing |
|---|---|---|
| **Has `Default` value** | `root.inputOutputs[]` companion exists with `id === <var>` AND `default` field is non-empty. (Producer task is OPTIONAL — companion's default is the fallback.) | ERROR — companion was supposed to be written by variables plugin |
| **No `Default` value** | At least one `task.data.outputs[]` entry exists with `id === <var>`. (No companion is written when there's no Default per [`../global-vars/impl-json.md` § Out argument](../global-vars/impl-json.md).) | ERROR — Out-arg has no value source |

Pseudocode:

```text
for entry in root.outputs[]:
  var = entry.var
  has_companion_default = exists(io in root.inputOutputs[] where io.id == var and io.default not empty)
  has_producer_task    = exists(t in all task.outputs[] where t.id == var)

  if sdd_row(name=entry.name).default is not empty:
      if not has_companion_default: ERROR("Out-arg with Default lacks companion default")
  else:
      if not has_producer_task: ERROR("Out-arg without Default lacks producing task output")
```

On ERROR, AskUserQuestion:

```
Out-argument "<name>" (id <random>, var <var>) has no value source:
  SDD row Default: <"" | "<value>">
  Companion root.inputOutputs[].id="<var>": <missing | default="">
  Producing task.data.outputs[].id="<var>": <missing>
Either:
  (a) Add an `outputs: ... <- <connectorField>` row to a task that produces this value (matching <var>)
  (b) Add a Default value to the SDD Case Variables row
  (c) Recategorize the variable
```

### Check 3 — Type mismatch warnings

Where a `=vars.X` reference resolves to a declaration with a different `type` than the consuming input expects, log WARNING. Proceed (string coercion is common and runtime-tolerant).

## Connector Tasks

Connector task input values are written during Step 9.7 (connector detail), not during this I/O binding step. Resolve cross-task `var` IDs before constructing the `input-values` body from `tasks.md`:

```json
{ "body": { "email": "=vars.employeeEmail", "caseRef": "=metadata.ExternalId" } }
```

Use `=js:()` only for expressions with operators (e.g., `=js:(vars.amount > 5000)`). See [connector-activity/impl-json.md](../../../plugins/tasks/connector-activity/impl-json.md).

## End-to-End: Task A Output → Task B Input

"Validate Expense Data" produces `validationResult`, consumed by "Enrich Employee Details":

```json
// 1. Task A output (auto-enriched) — Stage "Submission", task.data.outputs[]
{ "name": "ValidationResult", "var": "validationResult", "id": "validationResult",
  "value": "validationResult", "source": "=ValidationResult", "target": "=validationResult",
  "type": "string", "elementId": "Stage_submit-tValidate01" }

// 2. Task B input after binding — value set to =vars.<output.var>
{ "name": "in_ValidationResult", "value": "=vars.validationResult",
  "type": "string", "id": "vXr9pQ2mK", "var": "vXr9pQ2mK",
  "elementId": "Stage_submit-tEnrich02" }
```

Two things must exist: output on Task A with a `var` field, and bound input on Task B referencing `=vars.<var>`. Root `inputOutputs` companion entries for task outputs are optional — see [global-vars/impl-json.md § Task Output → inputOutputs Wiring](../global-vars/impl-json.md#task-output--inputoutputs-wiring).

## Error Handling

All issues go to the shared issue list per [logging/impl-json.md](../../logging/impl-json.md). No fuzzy matching, no auto-creation, no retries.

| Check | Severity | Action |
|---|---|---|
| Placeholder task (no `data.inputs[]`) | `SKIPPED` | Skip all bindings |
| Input name not found (exact match) | `ERROR` | Skip binding — log available inputs |
| Source output not found (exact match) | `ERROR` | Skip binding — log available outputs |
| `=vars.X` not in any task `outputs[].id` or root `inputOutputs[].id` / `inputs[].id` | `ERROR` | Skip binding |
| Out-arg formal entry's `var` doesn't match any task `outputs[].id` AND companion has no `default` | `ERROR` | Log Out-arg producer issue (Check 2 above); AskUserQuestion |
| Type mismatch (input vs variable) | `WARNING` | Proceed |

Example log entry (pseudocode — record in-reasoning, not via subprocess):

```text
# pseudocode — not executed
issues.append({"severity": "ERROR", "step": "9", "plugin": "io-binding",
    "message": f'input "{name}" not found on task "{task}" — available: {available}',
    "context": {"task": task, "stage": stage, "input": name, "available": available}})
```
