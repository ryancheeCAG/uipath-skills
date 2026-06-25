# Testing Activities Investigation Guide

## Data Correlation

Before using fetched data, verify it matches the user's reported problem:

- **Activity identity** — the faulted activity's class and namespace match the reported failure (e.g., `UiPath.Testing.Activities.VerifyExpressionWithOperator`, `UiPath.Testing.Activities.CompareText`). Verify activities, `CompareText`, AttachDocument, and the test-data-queue activities run different code paths; do not treat them interchangeably.
- **Execution context** — confirm whether the job is a **Test Job** (started from an Orchestrator Test Set / Test Manager, with test-case context) or a plain process / Studio run. This is load-bearing: assertion-reporting (`HttpRequestException`), document attachment, and coverage merge only do their full work in a Test Job. A "failure" reported from Studio may be a no-op path, not the real fault.
- **Test case / test set** — the test case (and its test set execution) in evidence is the one the user is asking about. Coverage-merge faults are scoped to a specific test set execution id.
- **Target resource** — the resource identifier in evidence matches what the user reports: the queue name and Orchestrator folder for `GetTestDataQueueItem`, the `FilePath` for `AttachDocument`, the `OutputFilePath` for `CompareText`. Don't substitute a similarly-named resource.
- **Workflow file** — if the project has multiple workflows, the error originates from the one the user is asking about, not a different `.xaml` / `.cs` using the same activity.

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## Distinguishing a real defect from a designed test failure

A `TestingActivitiesException` from a Verify activity (`Verification failed…`) is the **test asserting something false** with `ContinueOnFailure = false` — the activity worked correctly; the verification result was negative. `CompareText` raises the same exception type carrying its comparison-result message. This is **not** an activity malfunction. Before treating it as a defect, confirm with the user whether the verification was *expected* to pass:

- If the assertion was expected to pass → investigate why the **operands** differ (the data/system under test changed), not the activity.
- If the job should not fault on a failed assertion → the fix is setting `ContinueOnFailure = true`, not "fixing" the activity.

A raw `NullReferenceException` / `HttpRequestException` / `UnauthorizedAccessException` / `FileNotFoundException`, by contrast, is an **execution** fault — diagnose it as a real failure.

## Testing Prerequisites

Gather and verify before drawing conclusions:

1. **Activity class + display name** — from the workflow source or stack trace. The namespace selects the playbook.
2. **Execution context** — Test Job vs Studio vs plain process (see above). Capture how the job was started.
3. **Faulted exception type + message** — verbatim from `uip or jobs get <job-key> --output json` → `Info` and `uip or jobs logs <job-key> --level Error --output json`. The exception type selects the failure family.
4. **Stack frames** — whether the fault is inside the activity's own code (`AttachDocumentService`, `CompareTextService`, `AssertionService.PostAssertionToOrchestrator`) or in operand evaluation / a downstream activity. A fault in `AssertionService.Post…` is a reporting failure; a fault in the user's expression is an operand problem.
5. **Activity input properties** — from the workflow source (not a summary): `Expression` / `FirstExpression` / `SecondExpression` / `Operator` (Verify), `BaselineText` / `TargetText` / `OutputFilePath` / `ContinueOnFailure` (CompareText), `FilePath` (AttachDocument), `QueueName` / `FolderPath` / `Output` (GetTestDataQueueItem). The playbook names the subset that matters.
6. **Package version** — `UiPath.Testing.Activities` version from `project.json`. Message text and behavior shift across versions.

## Domain-specific data gathering

1. **Job logs at Error level** — these activities log the assertion message and the fault. `uip or jobs logs <job-key> --level Error --output json` carries the exception type, message, and stack.
2. **Activity traces** — when available, pull test-case execution traces; they show whether the activity reached the assertion-report POST, the file-write, or faulted earlier in operand evaluation.
