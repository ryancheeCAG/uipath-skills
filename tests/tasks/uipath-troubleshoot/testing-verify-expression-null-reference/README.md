# Verify Expression Failure — Operand NullReferenceException (uninitialized variable)

This scenario replays a **real captured** faulted Orchestrator job where the
`Verify Expression` activity (`VerifyExpression`,
`UiPath.Testing.Activities`) threw a `System.NullReferenceException`. The
exception is raised during **operand / expression evaluation** — while the WF
runtime resolves the activity's `Expression` argument, *before* the activity
body runs — because the `Expression` `[loadedValue.Length > 0]` dereferences
the `String` variable `loadedValue`, which is declared but never assigned
(`Nothing`).

## What this scenario uncovers

**Root Cause:** The `Verify Expression` activity in `Main.xaml` evaluates
`Expression="[loadedValue.Length > 0]"`. `loadedValue` is a `String` variable
on the `Validate Result` sequence with no default and no upstream assignment,
so it is null at run time. Calling `.Length` on it throws
`System.NullReferenceException` during argument resolution. The stack runs
through `__Expr0Get` → `Microsoft.VisualBasic.Activities.VisualBasicValue.Execute`
→ `System.Activities.InArgument.TryPopulateValue` → `ResolveArguments` — proving
the failure is in operand evaluation, **not** in the activity's own assertion
code, and **not** a designed "Verification failed" assertion result.

This maps to:
`references/activity-packages/testing-activities/playbooks/verify-expression-failures.md`
— the operand-evaluation / NullReferenceException branch (null dereference /
uninitialized operand).

The correct agent behavior is to identify the NRE as an operand-evaluation
crash, cite the `Expression` and the unassigned `loadedValue` variable from
`Main.xaml`, and recommend initializing / loading / null-guarding the operand —
**without** mistaking it for a designed assertion failure or proposing
`ContinueOnFailure` (which governs assertion results, not evaluation crashes).

## Two surfaces of Verify Expression (why this one is the operand NRE)

| Surface | Signature | Why NOT / IS this scenario |
|---|---|---|
| Designed assertion failure | `UiPath.Testing.Exceptions.TestingActivitiesException: Verification failed. The expression '...' returned 'False'.` | NOT this — exception is a raw `NullReferenceException`; no `Verification failed`/`returned 'False'` message; the expression never finished evaluating |
| Assertion-report HTTP error | `HttpRequestException` while posting the assertion result | NOT this — no HTTP frame; fault is during argument resolution inside the workflow |
| **Operand evaluation NRE** | **`System.NullReferenceException` thrown evaluating `Expression`; stack in `VisualBasicValue.Execute` / `InArgument.TryPopulateValue` / `ResolveArguments`** | **This scenario — null `loadedValue` dereferenced by `[loadedValue.Length > 0]`** |

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | snapshot of the failing UiPath project (`Main.xaml` with the `Verify Expression` activity + the uninitialized `loadedValue` variable; `project.json`) |
| `fixtures/mocks/responses/*.json` | **real captured** scrubbed `uip` responses (folders list, jobs list, jobs get, jobs history, jobs logs) |
| `fixtures/mocks/responses/manifest.json` | dispatch table (first-match), quoted + unquoted variants |

> **Scrub.** Captured evidence was scrubbed before commit:
> `UIP-PW06WJSK` → `MOCK-HOST`; `UIPATH\DAN.MOROSANU` → `UIPATH\REPLACEMENT_USER`;
> `dan.morosanu@uipath.com` → `original_email@test.com`. The job key, folder
> key, full error text + stack, `Shared`, `OrchestratorUserIdentity: newrobot`,
> timestamps and ids are kept verbatim. The captured faulted-jobs list contained
> many unrelated jobs; this scenario's jobs-list fixture includes only the
> single target job.

## Success criteria

This scenario **scores the conclusion, not the trajectory**. The only graded
outcomes are:

- Agent invoked the `uipath-troubleshoot` skill (`skill_triggered`).
- Agent matched the operand-NullReference branch of
  `verify-expression-failures.md` and reached the same conclusion as
  `RESOLUTION.md`: the NRE is thrown by `Verify Expression` during operand /
  expression evaluation (argument resolution, not the assertion result),
  caused by the uninitialized/null `loadedValue` dereferenced by the
  `Expression` `[loadedValue.Length > 0]`, and fixed by initializing / loading
  / null-guarding the operand — not by `ContinueOnFailure`, and not by
  blaming a designed assertion failure, the assertion-report HTTP path, or a
  different activity (`llm_judge`).
