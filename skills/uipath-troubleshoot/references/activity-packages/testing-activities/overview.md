# Testing Activities

Activities from `UiPath.Testing.Activities` — the package that drives **test automation**: assertions/verifications, text comparison, test data queues, document attachment, and (internally) code-coverage merge. Built for **test cases** executed as **Test Jobs** from Orchestrator Test Sets / Test Manager; many activities behave differently when run from Studio or a plain (non-test) process.

Namespaces: `UiPath.Testing.Activities`, `UiPath.Testing.Exceptions`.

## Execution context — Test Job vs Studio vs plain process

Several activities only do their full work inside a **Test Job** (started from Orchestrator with test-case context):

- **Verify / assertion activities** (`VerifyExpression`, `VerifyExpressionWithOperator`, `VerifyRange`, `VerifyControl`, and the assertion path of `CompareText`) evaluate their operands, then **POST the assertion result to Orchestrator** (`AssertionService.Assert` → `PostAssertionToOrchestrator`) when running publishable in a Test Job. The POST is skipped from Studio / non-test runs.
- **AttachDocument** attaches the file to the **current test case** in Orchestrator. From Studio it copies into `.local\attachments\<jobId>` and logs *"Skipped attaching document…"*; in a plain process it does nothing useful.
- **CoverageMergeActivity** is `[Browsable(false)]` — an **internal** activity users cannot place on a canvas. It runs automatically after a test set executes with **code coverage** enabled.

The context determines which failures are even reachable: an assertion-reporting `HttpRequestException` only happens in a Test Job; a coverage-merge fault only happens in a coverage-enabled test set.

## Exception families

- **Assertion / verification failure** — `UiPath.Testing.Exceptions.TestingActivitiesException`. For Verify activities, raised when the verification evaluates to **fail** AND `ContinueOnFailure = false`, which faults the job (designed behavior — the test asserted something false): `Verification failed. The expression '{0}' returned '{1}'.`, `Verification failed. The expression '{0}'{1} was not {2} the expression '{3}'{4}.`. `CompareText` raises the same exception type carrying its comparison-result message (`The analyzed texts are equivalent.` / `The analyzed texts are different.`).
- **Operand / expression evaluation error** — generic .NET exceptions (most often `System.NullReferenceException`) thrown while evaluating the **user's** `Expression` / `FirstExpression` / `SecondExpression` *before* the assertion is computed. Origin is the user's expression, not the activity.
- **Assertion-reporting failure** — `System.Net.Http.HttpRequestException` when the POST of the assertion result to Orchestrator / Test Manager fails (Test Job only). The verification itself may have evaluated fine.
- **File I/O** — `System.IO.FileNotFoundException` (`AttachDocument`: the `FilePath` input does not exist at runtime); `System.UnauthorizedAccessException` (`CompareText`: the `OutputFilePath` diff report is not writable).
- **Test data queue** — `TestingActivitiesException` (`Queue is empty or all items are consumed`, `Queue {0} not exist.`, content-null, non-JSON content) or `System.NullReferenceException` (unbound `QueueName` / `Output`, or null fields in the returned dictionary dereferenced downstream).
- **Coverage merge (internal)** — `System.InvalidOperationException` (`Sequence contains no elements`) from empty/corrupt coverage data; `InvalidArgumentsException` (`{0} must not be null or empty.`) for null `TestSetExecutionId` / `PackageId`.

## Package

NuGet: `UiPath.Testing.Activities`. Assertion and AttachDocument activities are meaningful only in a Test Job; test data queue activities require a Test Data Queue provisioned in the target Orchestrator folder; coverage merge requires code coverage enabled on the test set.
