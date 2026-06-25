# Final Resolution

---

**Root Cause:** The `Verify Expression` activity
(`UiPath.Testing.Activities.VerifyExpression`) in `Main.xaml` evaluates the
boolean `Expression` `[loadedValue.Length > 0]`. The operand `loadedValue` is a
`String` variable declared on the `Validate Result` sequence but **never
assigned**, so it is `Nothing` (null) at run time. Evaluating `.Length` on a
null reference throws `System.NullReferenceException` while the runtime is
**resolving the activity's argument** — *before* the activity body runs. There
is no assertion result; the expression itself blew up during operand
evaluation.

This maps to:
`references/activity-packages/testing-activities/playbooks/verify-expression-failures.md`
— the **operand-evaluation / NullReferenceException** branch (null dereference
inside the expression; uninitialized operand). It is **not** the designed
"Verification failed" assertion surface.

**What went wrong:** The `ResultValidation` job (key
`685af108-640a-4766-a24c-e23b980d67fa`, started 2026-06-25T07:39:14.757Z)
faulted ~3.6 seconds after launch. The `Verify Expression` activity is the
only activity in the workflow; it faulted as the runtime tried to compute its
`Expression` operand.

**Why operand evaluation, not the assertion:** The exception type is
`System.NullReferenceException`, not
`UiPath.Testing.Exceptions.TestingActivitiesException`. The stack confirms the
failure happened during **argument resolution**, before the activity could
produce an assertion result:

```
System.NullReferenceException: Object reference not set to an instance of an object.
   at ...Main_Expressions...__Expr0Get()
   at Microsoft.VisualBasic.Activities.VisualBasicValue`1.Execute(CodeActivityContext context)
   at System.Activities.CodeActivity`1.InternalExecuteInResolutionContext(...)
   at System.Activities.InArgument`1.TryPopulateValue(...)
   at System.Activities.ActivityInstance.ResolveArguments(...)
```

`__Expr0Get` → `VisualBasicValue.Execute` → `TryPopulateValue` →
`ResolveArguments` is the WF runtime computing the `Expression` argument. A
designed assertion failure would instead surface as a
`TestingActivitiesException: Verification failed. The expression '...' returned
'False'.` — there is no such message here.

---

**This is NOT:**

- **NOT a designed assertion failure (`TestingActivitiesException`
  "Verification failed").** The exception is a raw
  `System.NullReferenceException` thrown during expression evaluation; there is
  no `Verification failed. The expression '...' returned 'False'` message and
  no assertion result. The expression never finished evaluating, so it could
  not have "returned False."
- **NOT fixable with `ContinueOnFailure = True`.** `ContinueOnFailure` governs
  what happens when an assertion *result* is false — it records the result
  instead of faulting. It does **not** catch a `NullReferenceException` thrown
  while evaluating the operand. Setting it here would hide a real null-operand
  bug, not fix it.
- **NOT the assertion-report HTTP / Orchestrator posting path.** The job
  faulted during argument resolution inside the workflow, not while posting a
  Test Manager / assertion result over HTTP. There is no `HttpRequestException`
  and no reporting frame in the stack.
- **NOT a different activity.** The only activity in `Main.xaml` is
  `Verify Expression`, and both the Orchestrator `Info` stack and the job-log
  .NET stack name `VerifyExpression "Verify Expression"` at
  `Sequence "Validate Result"` at `Main "Main"`.
- **NOT an Orchestrator / folder / permission / credential problem.** The
  folder `Shared` resolved (key `defb8e05-e36b-4c36-bf11-0b4d08ce6cd1`), the
  job ran, and the fault is a code-level null dereference in the workflow's
  expression — not a sign-in, rights, or routing failure.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `ResultValidation` — Faulted at 2026-06-25T07:39:18.390Z (ran ~3.6 s),
  key `685af108-640a-4766-a24c-e23b980d67fa`, Id `68034824`.
- Job type: Unattended, `Source: Manual`, on machine `MOCK-HOST`, folder
  `Shared` (key `defb8e05-e36b-4c36-bf11-0b4d08ce6cd1`).
- `Info` (job get): `Object reference not set to an instance of an object.` →
  `in Main.xaml` → `at VerifyExpression "Verify Expression"` → `at Sequence
  "Validate Result"` → `at Main "Main"`, then
  `System.NullReferenceException` with the argument-resolution stack
  (`__Expr0Get` → `VisualBasicValue.Execute` → `InArgument.TryPopulateValue` →
  `ResolveArguments`).

### Testing Activities (Root Cause)
- Job log (Error): the same NRE and stack, scoped to
  `Verify Expression` — the `--- .NET stack trace ---` block confirms the
  failure is in expression evaluation, with no `Verification failed` message.
- `Main.xaml` (smoking gun):
  - The `Validate Result` `Sequence` declares
    `<Variable x:TypeArguments="x:String" Name="loadedValue" />` with **no
    default value** — `loadedValue` is `Nothing` at run time.
  - `<uta:VerifyExpression DisplayName="Verify Expression"
    Expression="[loadedValue.Length > 0]" ContinueOnFailure="False" ... />`
    dereferences `loadedValue.Length` on that null variable.
- No upstream activity assigns `loadedValue` (the sequence contains only the
  variable declaration and the `Verify Expression` activity), so the operand
  is null on the first and every run.

---

**Immediate fix:**

Populate or null-guard the operand so the `Expression` does not dereference a
null `loadedValue`. Pick one:

1. **Assign / load `loadedValue` before Verify Expression.** Add the upstream
   step that is supposed to set `loadedValue` (e.g. read the value it should
   validate into `loadedValue`) so it is a non-null `String` when
   `Verify Expression` runs. This is the correct fix if the workflow is missing
   the step that produces the value under test.
   - **Why:** The whole point of the check is to validate a real loaded value;
     restoring the producing step makes the operand non-null and lets the
     assertion evaluate truthfully.

2. **Null-guard the Expression.** Change the `Expression` to evaluate the null
   case first, e.g.
   `loadedValue IsNot Nothing AndAlso loadedValue.Length > 0`.
   - **Why:** Short-circuits before `.Length` is called on a null reference, so
     a missing/null value yields `False` (a clean assertion result) instead of
     crashing during evaluation.

Do **not** set `ContinueOnFailure = True` to make the fault go away — it does
not catch the `NullReferenceException` (that is an evaluation crash, not an
assertion result) and would only mask a real null-operand bug.

After applying the fix, re-run `ResultValidation` and confirm the job no longer
faults during `Verify Expression`.

---

**Preventive fix:**

1. **Initialize testing operands.** Give every variable an expression
   references a default value (or assign it in a guaranteed-to-run upstream
   step) before it reaches a `Verify Expression` / assertion activity, so an
   uninitialized operand can never throw during evaluation.
   - **Why:** Uninitialized operands are the most common cause of an NRE inside
     a Verify Expression rather than a clean assertion result.
   - **Who:** RPA / test developer.

2. **Null-guard expressions that dereference reference types.** When an
   expression calls a member (`.Length`, `.Name`, `.Rows(0)`, etc.) on a value
   that can be null, guard with `IsNot Nothing AndAlso ...` so a null operand
   produces a deterministic assertion result instead of a crash.
   - **Why:** Keeps real assertion failures distinguishable from evaluation
     crashes.
   - **Who:** RPA / test developer.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `Verify Expression` threw `System.NullReferenceException` during operand evaluation because the Expression `loadedValue.Length > 0` dereferences the uninitialized `String` variable `loadedValue` (null) — verify-expression-failures operand-NRE branch | High | Confirmed | Yes | NRE stack through `__Expr0Get`/`VisualBasicValue.Execute`/`TryPopulateValue`/`ResolveArguments`; `loadedValue` declared with no default and never assigned in `Main.xaml`; `Expression="[loadedValue.Length > 0]"` | Assign/load `loadedValue` upstream, or null-guard the Expression (`loadedValue IsNot Nothing AndAlso loadedValue.Length > 0`); do NOT use `ContinueOnFailure` |
| H2 | Designed assertion failure (`TestingActivitiesException` "Verification failed") | Low | Eliminated | No | Exception type is `NullReferenceException`, not `TestingActivitiesException`; no `Verification failed ... returned 'False'` message; stack is in argument resolution, not the assertion builder | n/a |

---

Would you like me to apply the null-guard / initialization fix to `Main.xaml`,
or clean up the `.local/investigations/` folder?
