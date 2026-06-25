# Compare Text Failure — Output Report Write Denied (UnauthorizedAccess)

This scenario replays a **real** captured Orchestrator job in which the
`Compare Text` activity (`UiPath.Testing.Activities.CompareText`) threw
`System.UnauthorizedAccessException` while **writing its HTML differences
report** to a non-writable `OutputFilePath`. The job faulted with
`Access to the path 'C:\Windows\System32' is denied.`, and the .NET stack runs
through `GenerateCustomDiffService.GenerateHtmlOutput` →
`CompareTextService.CompareText` → `CompareText.ExecuteAsync` — i.e. the write
fails **before** any assertion gate.

## What this scenario uncovers

**Root Cause:** The `Compare Text` activity in `Main.xaml` has
`OutputFilePath="C:\Windows\System32"`. That path is a **protected / system
directory** the robot account cannot write to (and is also an existing
directory, not a file). When the activity tries to write its diff report there,
the file write is denied with `System.UnauthorizedAccessException`. The
comparison itself is irrelevant to the fault — the texts differing
(`Report total: 100` vs `Report total: 105`) never gets a chance to be reported
because the report write fails first.

This maps to:
`references/activity-packages/testing-activities/playbooks/compare-text-output-write-failures.md`
(protected/system `OutputFilePath`).

The user is framed as **off-host** (not on MOCK-HOST), so the agent diagnoses
from Orchestrator evidence plus the project source in the working directory and
recommends the source fix.

## Sibling comparison (compare-text-output-write-failures)

| Cause | Signature | Why NOT (or why) this scenario |
|---|---|---|
| **Protected / system directory** | `UnauthorizedAccessException` writing to `C:\`, `C:\Windows`, etc. | **This scenario:** `OutputFilePath="C:\Windows\System32"` |
| Read-only / ACL-restricted folder | Folder exists, robot lacks write ACL | Not this — the denied path is a protected system location |
| Path is a directory, not a file | `OutputFilePath` points at a folder | Contributing: `C:\Windows\System32` is also a directory |
| File locked / open | Prior report held by a viewer | Not this — no lock; clean access-denied |
| Assertion result (NOT this playbook) | `TestingActivitiesException` carrying `The analyzed texts are different.` | Not this — the write failed before any assertion ran; the texts differing is irrelevant |

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | real failing project snapshot: `Main.xaml` with `Compare Text` `OutputFilePath="C:\Windows\System32"` |
| `fixtures/mocks/responses/*.json` | **real captured** `uip` envelopes (scrubbed) — folders list, the single faulted job, `jobs get`, `jobs history`, `jobs logs --level Error` |
| `fixtures/mocks/responses/manifest.json` | dispatch table (first match wins; quoted + unquoted variants) |

> **Note on fixtures.** Fixtures here were captured from a real
> RegressionTextCheck faulted job and scrubbed: host `UIP-PW06WJSK` →
> `MOCK-HOST`, `UIPATH\DAN.MOROSANU` → `UIPATH\REPLACEMENT_USER`, the folder
> owner email → `original_email@test.com`. The job key, folder key, error text
> and stack, `OrchestratorUserIdentity: newrobot`, timestamps and ids are kept
> verbatim. The faulted `jobs list` includes only the target job.

## Success criteria

This scenario **scores the conclusion, not the trajectory**. The only graded
outcomes are:

- Agent invoked the `uipath-troubleshoot` skill (`skill_triggered`).
- Agent matched `compare-text-output-write-failures.md` and reached the same
  conclusion as `RESOLUTION.md`: the `Compare Text` output-report write was
  denied because `OutputFilePath` (`C:\Windows\System32`) is a non-writable
  protected directory, the agent cited that value from `Main.xaml`, and the fix
  is to point `OutputFilePath` at a writable file path — NOT a text mismatch /
  assertion failure, NOT auth, NOT Orchestrator (`llm_judge`).
