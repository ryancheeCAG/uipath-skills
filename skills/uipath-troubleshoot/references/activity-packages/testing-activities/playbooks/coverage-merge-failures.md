---
confidence: low
---

# Coverage Merge — Failures (internal activity, InvalidOperationException)

## Context

`UiPath.Testing.Activities.Coverage.CoverageMergeActivity` is an **internal** activity (`[Browsable(false)]`) — users cannot place it on a canvas. The Testing framework runs it **automatically after a test set executes with code coverage enabled**: it downloads each test case's coverage file from Orchestrator, deserializes, merges, and uploads the merged coverage. A fault here is part of the platform's coverage post-processing, not a user-authored step.

What this looks like:
- **`System.InvalidOperationException`** — most commonly `Sequence contains no elements`, raised when a downloaded coverage file deserializes to an **empty or unexpectedly-shaped** structure (no package-execution entries).
- **`InvalidArgumentsException: <param> must not be null or empty.`** — `TestSetExecutionId` or `PackageId` was null/empty when the merge was invoked (internal-wiring problem).

What can cause it:
1. **Empty / corrupt coverage data.** A coverage file downloaded from Orchestrator is empty, truncated, or has no package-execution entries — the merge throws `InvalidOperationException` (`Sequence contains no elements`).
2. **Schema / version mismatch.** Coverage files produced by a different package/runtime version deserialize into a shape the merge does not expect.
3. **Partial / failed test-case executions.** Test cases that did not produce valid coverage leave gaps the merge cannot reconcile.
4. **Missing merge context (`InvalidArgumentsException`).** The framework invoked the merge without a valid `TestSetExecutionId` / `PackageId`.

What to look for:
- This is an **internal** activity — there is no user input on a canvas to "fix." Focus on the coverage feature, the runtime/package versions, and the test set execution that triggered the merge.
- Correlate the fault to a specific **test set execution id** and the package under coverage.

## Investigation

1. **Confirm the activity** is `CoverageMergeActivity` from `uip or jobs get <job-key> --output json` → `Info` / `uip or jobs logs <job-key> --level Error --output json`. A user did not place it — it ran as coverage post-processing.
2. **Confirm code coverage is enabled** on the test set that ran. The merge only runs when coverage is on.
3. **Capture the exception type:** `InvalidOperationException` (empty/corrupt coverage) vs `InvalidArgumentsException` (missing merge context).
4. **Check the test cases' executions** in that test set for partial/failed runs that may have produced empty coverage.
5. **Note package + runtime versions** (`UiPath.Testing.Activities`, robot) for a version/schema mismatch.

## Resolution

- **Empty/corrupt coverage (`InvalidOperationException`):** re-run the test set; if it reproduces, disable code coverage to unblock the run, and capture the test set execution id + package version for escalation — this is a platform-side coverage-merge robustness issue, not a user-fixable activity configuration.
- **Version/schema mismatch:** align the runtime and `UiPath.Testing.Activities` package versions across the test cases in the set.
- **Missing merge context (`InvalidArgumentsException`):** an internal-wiring failure; capture evidence and escalate.

> Because this activity is internal and has no user-facing configuration, the practical user-side action is usually: re-run, disable coverage to unblock, and escalate with the test set execution id, exception, and versions. Do not advise editing the activity — it is not placeable.

## Related

- [testing-activities overview](../overview.md) — CoverageMergeActivity is internal; runs after a coverage-enabled test set.
- [testing-activities investigation guide](../investigation_guide.md) — capture test set execution id, exception type, and package version before concluding.
