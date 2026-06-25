---
confidence: high
---

# Attach Document — File Not Found

## Context

`UiPath.Testing.Activities.AttachDocument` (`Attach Document`) attaches a file to the current test case in Orchestrator. It first checks that the input file exists, and that check runs **before** any Orchestrator call. When the file is missing, the activity faults with `System.IO.FileNotFoundException` whose **message is the resolved file path** (e.g. `System.IO.FileNotFoundException: C:\reports\summary.pdf`). The job faults the moment the activity runs.

What this looks like:
- `System.IO.FileNotFoundException` originating in `AttachDocumentService.AttachDocument` / `AttachDocument` activity, message = a file path.
- Fault is synchronous at the activity; no Orchestrator/test-case frames in the stack.

What can cause it:
1. **Wrong path.** The `FilePath` value points to a file that does not exist — typo, wrong folder, wrong extension.
2. **Relative path vs working directory.** A relative `FilePath` (e.g. `differences.html`, `output\report.pdf`) resolves against the **robot's working directory at runtime**, which differs from the Studio dev machine. The file exists where the developer expects but not relative to where the robot runs.
3. **File not produced yet.** An earlier activity that was supposed to create the file (a report export, a `CompareText` diff, a download) failed, was skipped, or wrote to a different path — so the attach runs against a missing artifact.
4. **Robot-vs-dev machine difference.** A path that exists on the developer's machine (`C:\Users\<dev>\…`) does not exist on the unattended robot host.
5. **Network / UNC path unreachable.** A `\\server\share\…` path the robot's identity cannot reach (mapped drive not present in the robot session, share permissions) resolves as not-found.
6. **File deleted / moved between steps.** A temp file cleaned up before the attach ran.

## Investigation

1. **Capture the exact message** from `uip or jobs get <job-key> --output json` → `Info` and `uip or jobs logs <job-key> --level Error --output json`. The message **is the path** the activity tried to attach — read it verbatim.
2. **Read the `FilePath` input** from the workflow source (the failing `.xaml`/`.cs`). Note whether it is absolute or relative, literal or a variable/expression.
3. **If relative:** determine the robot's working directory for the job and resolve the path against it — it will not match the developer's expectation.
4. **If the file is produced upstream:** check whether the producing activity actually ran and wrote to the exact path the attach reads. Compare the producer's output path with `FilePath` character-for-character.
5. **If absolute and machine-specific or UNC:** confirm the path exists on the **robot host** under the robot's identity, not the dev machine.

## Resolution

- **Wrong/typo path:** correct `FilePath` to the actual file location.
- **Relative path:** use a fully-qualified path, or anchor the relative path to a known base (e.g. the project directory / a known output folder) so it resolves identically on the robot.
- **File not produced:** ensure the upstream producer ran successfully and wrote to the same path the attach reads; guard the attach so it runs only when the file exists.
- **Machine-specific / UNC path:** use a path that exists on the robot host under the robot's identity; for shares, ensure the robot session has the mapping/permissions, or stage the file locally first.
- **Optional / best-effort attachment:** guard with a `File.Exists` check (or Try Catch) before `Attach Document` so a missing artifact does not fault the test.

## Anti-patterns (what NOT to do)

- **Assuming a relative path resolves to the project folder.** It resolves against the robot's working directory, which is not the project folder on an unattended run.
- **Attaching a file produced by a step that may have been skipped** without checking the file exists first.
- **Hardcoding a developer-machine path** (`C:\Users\<dev>\…`) that won't exist on the robot.

## Related

- [compare-text-output-write-failures](./compare-text-output-write-failures.md) — `CompareText`'s `OutputFilePath` is a common upstream producer of a file later attached.
- [testing-activities overview](../overview.md) — Test Job vs Studio execution context (AttachDocument only attaches to a test case in a Test Job).
