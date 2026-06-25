---
confidence: high
---

# Compare Text — Output Report Write Failure (UnauthorizedAccess)

## Context

`UiPath.Testing.Activities.CompareText` (`Compare Text`) compares `BaselineText` against `TargetText` and **writes an HTML differences report** to `OutputFilePath` (default `differences.html`). When the robot cannot write to that path, the activity faults with `System.UnauthorizedAccessException` from the file write.

What this looks like:
- `System.UnauthorizedAccessException` (often `Access to the path '<path>' is denied.`) originating from `CompareText` / `CompareTextService` while producing the diff report.
- The comparison itself may have completed; the fault is on the **output write**.

What can cause it:
1. **Protected / system directory.** `OutputFilePath` targets a location the robot's identity cannot write — `C:\`, `C:\Windows`, `C:\Program Files`, another user's profile.
2. **Read-only / ACL-restricted folder.** The target directory exists but the robot account lacks write permission.
3. **Path is a directory, not a file.** `OutputFilePath` points at an existing folder, so the write is denied.
4. **File locked / open.** A previous `differences.html` is open in another process (a viewer) or locked by a prior run.
5. **Relative default on an unattended robot.** The `differences.html` default resolves against the robot's working directory, which may be a protected/non-writable location in the robot session.

> **Different cause — not this playbook.** A `TestingActivitiesException` carrying the comparison-result message (`The analyzed texts are equivalent.` / `The analyzed texts are different.`) is the assertion reporting its result with `ContinueOnFailure = false`, not a write failure — the comparison ran and the report was produced. That is an assertion outcome; do not change `OutputFilePath` for it. See [testing-activities investigation guide](../investigation_guide.md) for distinguishing an assertion outcome from an execution fault.

## Investigation

1. **Capture the exact message** from `uip or jobs get <job-key> --output json` → `Info` / `uip or jobs logs <job-key> --level Error --output json`. Confirm the type is `UnauthorizedAccessException` and read the denied path.
2. **Read `OutputFilePath`** from the workflow source. Note absolute vs relative, and whether the directory is system/protected.
3. **Check the target directory** on the robot host: does it exist, is the path a file (not a folder), and can the robot's identity write there?
4. **Check for a lock:** is a prior report file open or held by another process?

## Resolution

- **Protected/system path:** set `OutputFilePath` to a writable location — the project output folder, a temp directory, or a folder the robot account owns.
- **Permission gap:** grant the robot account write permission on the target folder, or choose a folder it already owns.
- **Path is a directory:** point `OutputFilePath` at a **file** (include the filename), not a folder.
- **File locked:** ensure no viewer holds the previous report; write to a uniquely-named file per run if needed.
- **Relative default:** use a fully-qualified, writable path instead of the bare `differences.html` default on unattended robots.

## Anti-patterns (what NOT to do)

- **Treating `The analyzed texts are different.` as a write failure.** That is a designed assertion result; do not change `OutputFilePath` for it.
- **Pointing `OutputFilePath` at a system directory** and assuming the robot can write there.
- **Reusing a fixed report filename** that may be held open between runs.

## Related

- [attach-document-file-not-found](./attach-document-file-not-found.md) — the diff report written here is often attached downstream.
- [testing-activities investigation guide](../investigation_guide.md) — designed test failure vs execution fault.
