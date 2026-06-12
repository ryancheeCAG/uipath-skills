# SAP Planner — Transport Coverage Guide

Query SAP transaction coverage for a Test Manager project via `uip tm sapplanner coverage`, run the automated test cases that cover used transactions, and report fits/gaps in one pass.

> **Dev-build only (preview).** Not on the published `uip` binary yet. Use the local CLI build:
> ```bash
> node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage --project-key <PROJECT_KEY> --output json
> ```
> When the next CLI release ships, swap `node "C:\repos\cli\packages\cli\dist\index.js"` for plain `uip`.

## Surface

```
uip tm sapplanner coverage [options]
```

Only `coverage` exists under `sapplanner`. No `build`, `report`, `connectors list`.

## Options

| Flag | Required | Purpose |
|---|---|---|
| `--project-key <KEY>` | Yes | Test Manager project key. |
| `--connector-id <UUID>` | No | Scope to one SAP connector. Omit = all connectors on the project. |
| `--transports <ID...>` | No | Restrict to these transport numbers (space-separated, variadic). |
| `--include-unused` | No | Include `usageRating == 0` rows. Default: only-used. |
| `--from-date <ISO>` | No | Lower bound for execution history (ISO-8601). |
| `--to-date <ISO>` | No | Upper bound for execution history (ISO-8601). |
| `--limit <N>` | No | Results per page. Default: 20. |
| `--offset <N>` | No | Results to skip. Default: 0. |
| `-t, --tenant <NAME>` | No | Tenant name. Defaults to authenticated tenant. |
| `--output <FMT>` | No | Always pass `--output json`. |

Bad dates fail upfront: `Invalid date "<raw>". Use an ISO-8601 value like 2026-01-01 or 2026-01-01T00:00:00Z.`

## Output Schema

```json
{ "Result": "Success", "Code": "SapPlannerCoverage", "Data": [ /* rows */ ] }
```

Row fields:

| Field | Type | Meaning |
|---|---|---|
| `TCode` | string | SAP transaction (e.g. `ME22N`). |
| `TCodeDesc` | string | Description. |
| `UsageRating` | number | Execution-frequency score. `0` only when `--include-unused`. |
| `TestCases` | array | `{ TestCaseId, TestCaseObjKey }[]`. |
| `TestSets` | array | `{ TestSetId, TestSetObjKey }[]`. |

Empty `TestCases` + empty `TestSets` = **gap**. Non-empty `TestCases` = **fit**.

### Duplicate `TCode` rows = Interface variants

Same TCode on multiple rows = same connector split by SAP Interface (WinGui / WebGui / Fiori). The interface field is **not** in the response schema. Do **not** dedupe by `TCode` — a TCode can be a fit on one interface and a gap on another. Keep rows separate in the report.

## The Workflow

Pull coverage → identify automated fits → execute → emit one combined report.

### Step 1. Pull coverage

```bash
node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage \
  --project-key <PROJECT_KEY> \
  [--from-date <FROM> --to-date <TO>] \
  [--connector-id <UUID>] \
  --output json
```

`Data: []` → stop. No SAP activity in window. Emit gap-empty + fit-empty report.

### Step 2. Segregate fits vs gaps

- **Fit row**: `TestCases.length > 0`.
- **Gap row**: `TestCases.length == 0 AND TestSets.length == 0`.
- **Test-set-only** (empty `TestCases`, non-empty `TestSets`): rare. Surface separately if present; not runnable via `testcases run`.

JMESPath partition shortcut:
```bash
--output-filter "{Fits: [?length(TestCases) > \`0\`], Gaps: [?length(TestCases) == \`0\` && length(TestSets) == \`0\`]}"
```

### Step 3. Collect unique `TestCaseId`s from fit rows

The same `TestCaseId` can appear under multiple TCodes and multiple interface variants. Dedupe.

```powershell
$cli = "C:\repos\cli\packages\cli\dist\index.js"
$cov = (& node $cli tm sapplanner coverage --project-key <KEY> --output json) | ConvertFrom-Json
$fits = $cov.Data | Where-Object { $_.TestCases.Count -gt 0 }
$candidateIds = $fits | ForEach-Object { $_.TestCases.TestCaseId } | Select-Object -Unique
```

### Step 4. Find which candidates are actually automated

**Do NOT trust `IsAutomated` from `testcases list`.** It frequently reads `false` even when the case is linked to a runnable Orchestrator package. `testcases run --execution-type automated` will accept a case that `IsAutomated` claims is manual, and reject one it claims is automated.

The authoritative signal is the presence of **linked-package fields** on the list row. A test case is automated when **any** of these is present and non-empty:

- `PackageIdentifier` — Orchestrator package name (e.g. `ayushi.test.automation`)
- `PackageEntryPointUniqueId` — linked entry point UUID
- `AutomationId` / `AutomationTestCaseName` / `AutomationProjectName` — XAML-based link

Classify a row as **manual** only when **all** are absent.

```powershell
$tcList = (& node $cli tm testcases list --project-key <KEY> --output json) | ConvertFrom-Json
$automatedIds = $tcList.Data |
  Where-Object {
    $candidateIds -contains $_.Id -and (
      $_.PackageIdentifier -or
      $_.PackageEntryPointUniqueId -or
      $_.AutomationId -or
      $_.AutomationTestCaseName -or
      $_.AutomationProjectName
    )
  } |
  Select-Object -ExpandProperty Id
```

Bash (jq):
```bash
node "..." tm testcases list --project-key <KEY> --output json |
  jq -r --argjson ids '["<UUID1>","<UUID2>"]' \
    '.Data[] | select((.Id | IN($ids[])) and (
        .PackageIdentifier // .PackageEntryPointUniqueId //
        .AutomationId // .AutomationTestCaseName // .AutomationProjectName
    )) | .Id'
```

Result: `$automatedIds` = fits that can actually run. Cases in `$candidateIds` but not `$automatedIds` are manual fits — list them in the report as "covered, not automated."

### Step 5. Resolve the Orchestrator folder hosting the linked package

Required because `uip tm testcases run` reads from the project's **default folder**, and a Test Manager project can map to 50+ Orchestrator folders. Don't guess by folder name — resolve from the `PackageIdentifier` and `PackageEntryPointUniqueId` carried on the test-case row (collected in Step 4).

Find candidate folders by package identifier:

```bash
uip or processes list --all-folders --output json \
  --output-filter "[?ProcessKey == '<PackageIdentifier>' || contains(ProcessKey, '<PackageIdentifier>')].{FolderKey: FolderKey, FolderPath: FolderPath, ProcessKey: ProcessKey, ProcessVersion: ProcessVersion}"
```

Each match exposes `FolderKey`, `FolderPath`, `ProcessKey`. Confirm the entry point matches `PackageEntryPointUniqueId` from Step 4 — **always pass `--package-name`** to narrow:

```bash
uip tm testcases list-automations --project-key <KEY> --folder-key <FOLDER_KEY> --package-name <PackageIdentifier> --output json
```

Without `--package-name` this command returns every entry point in the folder (one session saw 5559 rows). With it, you get only the package's entry points; confirm `Id` matches `PackageEntryPointUniqueId`.

Set the resolved folder as the project default:

```bash
uip tm project set-default-folder --project-key <KEY> --folder-key <FOLDER_KEY> --output json
```

**Pagination note.** `or processes list --all-folders` returns 50 rows per call with `Pagination.HasMore: true` when more exist. `--output-filter` runs client-side over the current page only. If the current page yields no matches and `HasMore` is true, advance with `--offset 50`, `--offset 100`, … until a match appears or `HasMore: false`. Never list-all-then-grep client-side without checking `HasMore` — you'll miss matches on later pages.

### Step 6. Run automated fits

Preconditions:
- Default folder set on the project (Step 5 above).
- `--execution-type automated` is **required** by the dev-build CLI. Omitting it errors: `required option '--execution-type <type>' not specified`.

```bash
node "..." tm testcases run \
  --project-key <PROJECT_KEY> \
  --test-case-id <UUID1> <UUID2> <UUID3> \
  --execution-type automated \
  --async \
  --output json
```

`--test-case-id` is **space-separated** for multiple UUIDs. Capture `Data.ExecutionId`.

`$automatedIds` empty → skip to Step 9 and emit fits-empty + gaps report.

### Step 7. Wait for terminal state

```bash
node "..." tm wait \
  --execution-id <EXECUTION_ID> \
  --project-key <PROJECT_KEY> \
  --timeout 1800 \
  --output json
```

### Step 8. Pull per-test-case results

```bash
node "..." tm executions testcaselogs list \
  --execution-id <EXECUTION_ID> \
  --project-key <PROJECT_KEY> \
  --output json
```

Each row has `TestCaseId`, `TestCaseName`, `Status` (`Passed` / `Failed` / `Skipped`), `StartTime`, `EndTime`, `HasError`. For totals: `uip tm executions get-stats --execution-id <ID> --project-key <KEY> --output json`.

**Distinguish test-logic failure from infrastructure failure.** A `Status: Failed` row with `HasError: false` means the automation never ran — typically a robot-session issue (`Robot.Session.UserLogonFailed`, `ERROR_LOGON_FAILURE`, machine unavailable). Report this as an infrastructure failure, not a coverage failure: the TCode is still effectively unvalidated this run. Test-logic failures have `HasError: true` with assertion details.

### Step 9. Emit the combined report

**Fits — covered TCodes** (annotate each row with its execution result by joining `TestCaseId` back to the Step 1 payload):

| Test Case (Key) | Name | TCodes Covered | Automated? | Status | Cause |
|---|---|---|---|---|---|

- Automated, Status=Passed → ✅
- Automated, Status=Failed, HasError=true → ❌ assertion/exception (include error message)
- Automated, Status=Failed, HasError=false → ⚠ infrastructure (cite robot/machine + Windows logon error)
- Manual (in `$candidateIds` minus `$automatedIds`) → 🟡 covered, manual only — not executed this run

**Gaps — uncovered TCodes** (sort `UsageRating` desc; keep interface variants separate):

| Priority | TCode | Description | UsageRating | Interface Variant # |
|---|---|---|---|---|

Recommend authoring tests for the top 3 by usage. Include `uip tm testcases create` + `link-automation` template for each.

### Failure handling

| Condition | Action |
|---|---|
| Step 1 returns `Data: []` | Stop. Report "no SAP activity in window." |
| Step 4 yields zero automated fits | Skip Steps 6–8. Emit fits report listing manual-only coverage + gaps report. |
| `testcases run` rejects: `required option '--execution-type <type>' not specified` | Re-issue with `--execution-type automated`. |
| `testcases run` rejects: case not automated despite `PackageIdentifier` present | Re-confirm via `uip tm testcases list-automations --project-key <KEY> --folder-key <FOLDER_KEY>`. Stale link → re-run `link-automation`. |
| `executions retry` returns `HTTP 404: TestSet does not exist` | The ad-hoc test set from the original `testcases run` was reaped. Start a **fresh** `testcases run` instead of retrying. |
| `set-default-folder` not run | `testcases run` fails. Set the folder, then retry. |
| Robot logon failure on every retry, different robot each time | Robot/machine Windows credentials are invalid for that machine. Fix in Orchestrator before running again — repeated retries on the same machine will keep failing. |

## Standalone Examples

First page of used transactions:
```bash
node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage --project-key DEMO --output json
```

Include unused, scope to a connector, paginate:
```bash
node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage \
  --project-key DEMO --connector-id <UUID> --include-unused \
  --limit 100 --offset 100 --output json
```

Restrict to transports in a date window:
```bash
node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage \
  --project-key DEMO --transports TR0001 TR0002 \
  --from-date 2026-01-01 --to-date 2026-06-01 --output json
```

Gap rows only:
```bash
node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage \
  --project-key DEMO --include-unused --output json \
  --output-filter "[?length(TestCases) == \`0\` && length(TestSets) == \`0\`].{TCode: TCode, Desc: TCodeDesc, Usage: UsageRating}"
```

## Pagination

- `--limit` caps a single response (default 20).
- `--offset` skips rows.
- Stop when returned `Data.length < --limit`.

## Errors

| Failure | Fix |
|---|---|
| `Invalid date "<raw>"` | Use `YYYY-MM-DD` or full ISO-8601. |
| `unknown command 'sapplanner'` | Invoked the published `uip` instead of the dev build. Use `node "C:\repos\cli\packages\cli\dist\index.js" …`. |
| Auth error from `initializeContextWithProject` | `uip login`, then verify with `uip tm project list --filter <KEY> --output json`. |
| `403 Forbidden` | User lacks Test Manager read permission on the project. |
| Empty `Data` | No transactions match. Drop date/transport filters or add `--include-unused`. |
| `HTTP 404: TestSet does not exist` on `executions retry` | Run a fresh `testcases run` instead — ad-hoc test set was reaped. |

Cap retries at 3 (parent skill Critical Rule #4).

## Anti-patterns

- **Do NOT classify automation status via `IsAutomated`.** It lies. Use `PackageIdentifier` / `PackageEntryPointUniqueId` / `AutomationId` instead. See Step 4.
- **Do NOT omit `--execution-type automated` on `testcases run`.** The dev-build CLI rejects the call.
- **Do NOT list `tm testcases list-automations` for a whole folder.** Production folders contain thousands of entry points (one session saw 5559 rows). Always pass `--package-name <PackageIdentifier>` to narrow.
- **Do NOT guess the default Orchestrator folder by name.** Resolve it from `PackageIdentifier` via `or processes list --all-folders` + `--output-filter`, then verify the entry point matches `PackageEntryPointUniqueId`. See Step 5.
- **Do NOT use `executions retry` for an infrastructure-failed run after the ad-hoc test set is gone.** Start a fresh `testcases run`.
- **Do NOT collapse duplicate `TCode` rows.** Different SAP Interface variants of the same connector. Dedupe loses interface-level gaps.
- **Do NOT mix `--include-unused` with date filters and expect zero-usage rows in that window.** `--include-unused` lifts the `onlyUsed` server flag globally; date bounds still apply to execution history.
- **Do NOT page without checking response length.** `Data.length < --limit` = end of results.
- **Do NOT guess connector UUIDs.** No `sapplanner connectors list` exists. Ask the user.
- **Do NOT keep retrying after a robot-logon failure on the same machine.** Fix the Windows credentials in Orchestrator first.
- **Do NOT swap `node "…\index.js"` for plain `uip` silently.** When the command lands in a public release, update this guide and the SKILL.md row in the same commit.
