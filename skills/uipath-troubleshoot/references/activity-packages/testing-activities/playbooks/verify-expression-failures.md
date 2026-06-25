---
confidence: medium
---

# Verify Expression — Failures (assertion fail vs operand NullReference)

## Context

`UiPath.Testing.Activities.VerifyExpression` (`Verify Expression`) evaluates a single boolean `Expression`, builds an assertion message, and (in a Test Job) posts the result to Orchestrator. Two distinct failure surfaces share this activity:

What this looks like:
- **Assertion failed (designed):** `UiPath.Testing.Exceptions.TestingActivitiesException: Verification failed. The expression '<expr>' returned 'False'.` — the activity evaluated the expression to `False` (or the verification did not hold) and `ContinueOnFailure = false`, so the job faults.
- **Operand evaluation error:** `System.NullReferenceException` (or another raw .NET exception) thrown while **evaluating `Expression`** — *before* an assertion result exists. The stack is in expression evaluation, not in the assertion message builder.

What can cause it:
1. **Verification legitimately false (designed).** The condition under test is false at run time. The activity worked; the test asserted something untrue. Not an activity defect.
2. **Null dereference inside the expression (`NullReferenceException`).** `Expression` dereferences a variable/property that is null at run time — e.g. `customer.Name = "X"` where `customer` is null, `dt.Rows(0)(...)` on an empty `DataTable`, a no-match lookup that returned null, an output argument from a prior activity that was never set.
3. **Uninitialized operand.** A variable used in `Expression` was never assigned (default null) because an upstream activity was skipped or failed silently.

What to look for:
- **The exception type** selects the surface: `TestingActivitiesException` → designed assertion fail; `NullReferenceException`/other → operand evaluation.
- **The `'<expr>' returned '<value>'` message** (TestingActivitiesException) — names the expression and the value it evaluated to.
- **The stack frame** — an NRE inside expression evaluation points at the operands, not the activity.

## Investigation

1. **Capture the exact type + message** from `uip or jobs get <job-key> --output json` → `Info` / `uip or jobs logs <job-key> --level Error --output json`.
2. **If `TestingActivitiesException` (`Verification failed…`):** confirm with the user whether the verification was **expected** to pass. If yes → investigate why the operand value differs (the data/system under test changed), not the activity. If the job should not fault on a failed check → the fix is `ContinueOnFailure`, not the activity.
3. **If `NullReferenceException` / other:** read `Expression` from the workflow source and identify every variable/property it dereferences. Determine which one is null at run time and which upstream activity was supposed to populate it.

## Resolution

- **If the verification is correctly false** (real defect in the system under test): fix the system/data under test; the test is doing its job.
- **If a failed assertion should not fault the job:** set `ContinueOnFailure = true` so the result is recorded without faulting.
- **If `NullReferenceException` from the expression:** ensure the dereferenced operand is populated before `Verify Expression` runs — guard for null (e.g. evaluate `customer IsNot Nothing AndAlso …`), or fix/verify the upstream activity that should have set it.
- **If an upstream activity was skipped/failed:** restore that activity's output so the operand is non-null.

## Anti-patterns (what NOT to do)

- **"Fixing" the activity for a `Verification failed` fault.** That is the designed result of a false assertion — investigate the operands or `ContinueOnFailure`, not the activity.
- **Suppressing a `NullReferenceException` with `ContinueOnFailure`.** That hides a real null-operand bug; `ContinueOnFailure` governs assertion *results*, not evaluation crashes — fix the null operand.

## Related

- [verify-expression-with-operator-failures](./verify-expression-with-operator-failures.md) — two-operand variant; adds the assertion-reporting `HttpRequestException` surface.
- [testing-activities investigation guide](../investigation_guide.md) — distinguishing a designed test failure from an execution fault.
