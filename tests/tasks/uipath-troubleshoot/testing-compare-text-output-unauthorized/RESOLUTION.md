# Final Resolution

---

**Root Cause:** The `Compare Text` activity
(`UiPath.Testing.Activities.CompareText`) in `Main.xaml` is configured with
`OutputFilePath="C:\Windows\System32"`. `Compare Text` writes an HTML
**differences report** to `OutputFilePath`, but `C:\Windows\System32` is a
**protected / system directory** the robot account cannot write to (and it is
an existing directory, not a file). When the activity tries to write the
report there, the file write is denied:
`System.UnauthorizedAccessException: Access to the path 'C:\Windows\System32'
is denied.`

This maps to:
`references/activity-packages/testing-activities/playbooks/compare-text-output-write-failures.md`
(protected/system `OutputFilePath`).

**What went wrong:** The `RegressionTextCheck` job (started
2026-06-25T07:40:16.913Z, folder `Shared`) faulted ~2 seconds after launch when
its `Compare Text` activity produced its diff report. The .NET stack is
unambiguous about where the failure occurs:

```
System.UnauthorizedAccessException: Access to the path 'C:\Windows\System32' is denied.
   ... System.IO.File.WriteToFile(...)
   at UiPath.Testing.Activities.Services.GenerateCustomDiffService.GenerateHtmlOutput(List`1 differences, String outputPath)
   at UiPath.Testing.Activities.Services.GenerateCustomDiffService.GenerateTextOutput(...)
   at UiPath.Testing.Activities.Services.CompareTextService.CompareText(CompareTextSettings settings)
   at UiPath.Testing.Activities.CompareText.ExecuteAsync(...)
```

The fault is a **file write** (`File.WriteToFile` → `GenerateHtmlOutput`), not a
comparison or assertion outcome.

**Why:** `Compare Text` always writes its differences report to
`OutputFilePath` as part of producing its result. That write happens **before**
any assertion gate. So the write to a non-writable path fails first, and the
fact that the baseline and target texts differ (`Report total: 100` vs
`Report total: 105`) never matters — no assertion result is ever reported. The
texts differing is irrelevant to this fault.

---

**This is NOT these other causes:**

- **NOT a text-mismatch / failed assertion.** A `TestingActivitiesException`
  carrying `The analyzed texts are different.` would be the assertion reporting
  its result — the comparison ran and the report was produced. That is **not**
  what happened here: the exception is `System.UnauthorizedAccessException` from
  `File.WriteToFile` / `GenerateHtmlOutput`, i.e. the report write failed before
  any assertion result. Do **not** "fix" this by changing the texts or the
  comparison; the texts differing is irrelevant.
- **NOT a credential / authentication / password problem.** The robot
  authenticated and ran; the job reached the `Compare Text` activity. This is a
  filesystem write denial, not a sign-in failure.
- **NOT an Orchestrator connectivity / API / tenant problem.** Orchestrator
  dispatched the job, it ran on `MOCK-HOST`, and Orchestrator captured the
  fault. The failure is inside the workflow at the report write.
- **NOT a bug in the comparison logic or a different activity.** The stack names
  exactly `CompareText.ExecuteAsync` → `CompareTextService.CompareText` →
  `GenerateCustomDiffService.GenerateHtmlOutput`. The failing operation is the
  HTML report write, nothing else.

---

**Evidence:**

### Orchestrator (Propagation)
- Folder: `Shared` (key `defb8e05-e36b-4c36-bf11-0b4d08ce6cd1`)
- Job: `RegressionTextCheck` — Faulted at 2026-06-25T07:40:19.153Z (job key
  `2569ee8e-449a-42b8-a761-4dfd5ed2aa49`), ran ~2.2 seconds
- Job type: Unattended, source Manual, machine `MOCK-HOST`
- Robot identity: `OrchestratorUserIdentity: newrobot`
- `uip or jobs get 2569ee8e-449a-42b8-a761-4dfd5ed2aa49 --output json` →
  `Info`:
  `Access to the path 'C:\Windows\System32' is denied.` → `Main.xaml` →
  `CompareText "Compare Text"` → `Sequence "Check Regression Text"` →
  `Main "Main"`, with the full `System.UnauthorizedAccessException` stack
  through `GenerateCustomDiffService.GenerateHtmlOutput` /
  `CompareTextService.CompareText` / `CompareText.ExecuteAsync`.
- `uip or jobs logs 2569ee8e-449a-42b8-a761-4dfd5ed2aa49 --level Error --output json`
  → the same `UnauthorizedAccessException` + .NET stack at the report write.

### Testing Activities (Root Cause)
- `Main.xaml`: a `Sequence "Check Regression Text"` containing a single
  `CompareText "Compare Text"` activity with:
  - `OutputFilePath="C:\Windows\System32"` — **the smoking gun**: a protected
    system directory the robot cannot write to.
  - `BaselineText="Report total: 100"`, `TargetText="Report total: 105"`,
    `ComparisonType="Line"`, `ContinueOnFailure="True"`.
- The combination of the `File.WriteToFile` / `GenerateHtmlOutput` stack and the
  `OutputFilePath="C:\Windows\System32"` in source is the signature of an
  output-report write to a non-writable path.

---

**Immediate fix:**

1. **Point `OutputFilePath` at a writable FILE path.**
   - **What:** In `Main.xaml`, change the `Compare Text` activity's
     `OutputFilePath` from `C:\Windows\System32` to a writable file the robot
     account can create — e.g. a file in the project output folder or a temp
     directory (for example a fully-qualified path under the project's output
     directory, ending in a `.html` filename), not a protected/system folder
     and not a bare directory.
   - **Why:** `Compare Text` writes its HTML differences report to
     `OutputFilePath`. `C:\Windows\System32` is a protected system location the
     robot cannot write to (and is a directory, not a file), so the write is
     denied. A writable file path lets the report write succeed.

2. **Re-run `RegressionTextCheck` and confirm.**
   - **What:** After repointing `OutputFilePath`, re-run the process from
     Orchestrator (folder `Shared`) and confirm the job no longer faults at the
     `Compare Text` step.
   - **Why:** Verifies the output-write denial was the only blocker. Note the
     comparison may still report the texts as different — that is the designed
     assertion result, separate from this write failure, and is handled by
     `ContinueOnFailure`.

---

**Preventive fix:**

1. **Never point `OutputFilePath` at a protected/system directory or a bare
   folder.** Use a fully-qualified, writable file path (project output or temp)
   for every `Compare Text` (and similar testing activities) report.
   - **Why:** Protected paths (`C:\`, `C:\Windows`, `C:\Program Files`) and
     directory-only paths are the most common reason a diff-report write is
     denied on an unattended robot.
   - **Who:** RPA developer.

2. **Validate writability of report paths at design time.** Prefer a path the
   robot account owns; on unattended robots avoid the bare `differences.html`
   relative default, which resolves against the robot working directory.
   - **Who:** RPA developer / platform team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `Compare Text` `OutputFilePath="C:\Windows\System32"` is a non-writable protected directory, so writing the HTML diff report fails with `UnauthorizedAccessException` (compare-text-output-write-failures) | High | Confirmed | Yes | `jobs get`/`jobs logs` `System.UnauthorizedAccessException: Access to the path 'C:\Windows\System32' is denied.` with stack through `GenerateHtmlOutput`/`CompareTextService.CompareText`; `OutputFilePath="C:\Windows\System32"` in `Main.xaml` | Set `OutputFilePath` to a writable file path (project output / temp) |
| H2 | The fault is a failed text-comparison assertion ("The analyzed texts are different.") | Low | Eliminated | No | The exception is `UnauthorizedAccessException` from `File.WriteToFile`/`GenerateHtmlOutput`, not a `TestingActivitiesException` assertion result; the write failed before any assertion gate | n/a |

---

Would you like me to draft the exact `OutputFilePath` change for `Main.xaml`,
or clean up the `.local/investigations/` folder?
