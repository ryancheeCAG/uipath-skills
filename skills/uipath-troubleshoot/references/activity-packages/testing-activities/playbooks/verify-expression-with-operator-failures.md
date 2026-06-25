---
confidence: medium
---

# Verify Expression With Operator — Failures (assertion fail, operand error, assertion-report HTTP)

## Context

`UiPath.Testing.Activities.VerifyExpressionWithOperator` (`Verify Expression With Operator`) evaluates `FirstExpression` and `SecondExpression`, compares them with `Operator` (Equal, NotEqual, GreaterThan, …), builds an assertion message, and (in a Test Job) **posts the result to Orchestrator**. Three failure surfaces share this activity:

What this looks like:
- **Assertion failed (designed):** `UiPath.Testing.Exceptions.TestingActivitiesException: Verification failed. The expression '<first>'<v1> was not <operator> the expression '<second>'<v2>.` — the comparison did not hold and `ContinueOnFailure = false`.
- **Operand evaluation error:** `System.NullReferenceException` (or other raw .NET exception) while evaluating `FirstExpression`/`SecondExpression` — before the comparison.
- **Assertion-reporting failure:** `System.Net.Http.HttpRequestException` when **posting the assertion result to Orchestrator / Test Manager** fails. The comparison may have evaluated fine; the POST (`AssertionService.Assert` → `PostAssertionToOrchestrator`) failed. Only reachable in a **Test Job**.

What can cause it:
1. **Comparison legitimately false (designed).** Actual ≠ expected at run time. The activity worked; the test asserted something untrue.
2. **Null/uninitialized operand (`NullReferenceException`).** One expression dereferences a null variable/property, or uses an output argument never set upstream. See [verify-expression-failures](./verify-expression-failures.md).
3. **Assertion-report POST failed (`HttpRequestException`).** Orchestrator / Test Manager unreachable from the robot, a transient network blip, proxy/TLS interception, an expired/invalid token, or an Orchestrator 5xx — while reporting the verification result.
4. **User expression performs HTTP.** Rare: an operand expression itself calls an HTTP API that throws `HttpRequestException` during evaluation (stack is in the expression, not in `AssertionService`).

What to look for:
- **Exception type** selects the surface.
- **Stack frame for `HttpRequestException`:** frames in `AssertionService` / `PostAssertionToOrchestrator` → reporting failure (cause 3); frames in expression evaluation → operand HTTP (cause 4).
- **The `'<first>'<v1> was not <operator> '<second>'<v2>` message** (TestingActivitiesException) — names both operands, their values, and the operator.

## Investigation

1. **Capture the exact type + message** from `uip or jobs get <job-key> --output json` → `Info` / `uip or jobs logs <job-key> --level Error --output json`.
2. **If `TestingActivitiesException` (`Verification failed…`):** confirm whether the comparison was expected to hold (see [verify-expression-failures](./verify-expression-failures.md) — designed-fail vs operand-changed; `ContinueOnFailure` if the job should not fault).
3. **If `NullReferenceException`:** identify which operand is null and the upstream activity that should have set it.
4. **If `HttpRequestException`:** read the stack. If it is in the assertion-report POST → check the robot's connectivity to Orchestrator, robot/Orchestrator auth/token validity, proxy/TLS, and whether the failure is transient (re-run). If it is in expression evaluation → the user's expression is making the HTTP call; fix/guard that call.

## Resolution

- **If the comparison is correctly false:** fix the system/data under test; the test is doing its job. To avoid faulting on a failed check, set `ContinueOnFailure = true`.
- **If `NullReferenceException`:** populate/guard the null operand before the activity; fix the upstream producer.
- **If `HttpRequestException` from the assertion-report POST:** restore robot↔Orchestrator connectivity and valid auth; re-run if the failure was transient. This is an infrastructure/reporting failure, not a verification-logic problem — do **not** change the expressions or operator.
- **If `HttpRequestException` from the expression:** move the HTTP call out of the assertion operand, or guard/handle it; keep `Verify Expression With Operator` operands as already-resolved values.

## Anti-patterns (what NOT to do)

- **Changing the operator/expressions for an `HttpRequestException`.** The verification logic is not the cause when the fault is in the assertion-report POST or an operand's HTTP call.
- **"Fixing" the activity for a `Verification failed` fault.** Designed result of a false comparison.
- **Embedding live HTTP calls inside an assertion operand.** Resolve values first; pass results to the activity.

## Related

- [verify-expression-failures](./verify-expression-failures.md) — single-operand variant; shared assertion-fail and operand-NRE surfaces.
- [testing-activities investigation guide](../investigation_guide.md) — execution context (assertion reporting only happens in a Test Job) and designed-fail vs execution-fault.
