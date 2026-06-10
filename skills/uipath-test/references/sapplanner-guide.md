# SAP Planner — Transport Coverage Guide

How to query SAP transaction coverage for a Test Manager project using `uip tm sapplanner coverage`. Answers: which SAP transactions (TCodes) are touched by your transports, which test cases / test sets cover them, and which are unused.

> **Dev-build only (preview).** The command is not yet on the published `uip` binary. Use the local CLI build:
> ```bash
> node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage --project-key <PROJECT_KEY> --output json
> ```
> Once the next CLI release ships, swap `node "C:\repos\cli\packages\cli\dist\index.js"` for plain `uip`. Every command in this guide uses the dev-build form.

## When to Use

- Pre-release impact analysis: which SAP transactions are affected by a set of transports.
- Coverage gap audit: which transactions are exercised by tests, which are not.
- Connector scoping: same audit constrained to a single SAP connector on the project.
- Time-windowed regression review: coverage activity within a date range.
- **Coverage-driven execution**: fetch coverage, split into fits vs gaps, run every fit's test cases as one execution, wait for completion, report pass/fail per test case and a separate gap list. See [Coverage-driven execution & reporting](#coverage-driven-execution--reporting) below.

## Surface

```
uip tm sapplanner coverage [options]
```

One subcommand under `sapplanner`. No `build`, `report`, or other verbs exist today.

## Options

| Flag | Required | Purpose |
|---|---|---|
| `--project-key <KEY>` | Yes | Test Manager project key (e.g. `DEMO`). |
| `--connector-id <UUID>` | No | Scope to a single SAP connector. Omit to include every SAP connector registered on the project. |
| `--transports <ID...>` | No | Restrict to these transport numbers (space-separated, variadic). Omit to include all transports. |
| `--include-unused` | No | Include transactions with no execution history. Default: server returns only used transactions (`usageRating > 0`). |
| `--from-date <ISO>` | No | Lower bound for transaction execution. ISO-8601 (e.g. `2026-01-01` or `2026-01-01T00:00:00Z`). |
| `--to-date <ISO>` | No | Upper bound for transaction execution. ISO-8601. |
| `--limit <N>` | No | Results per page. Default: 20. |
| `--offset <N>` | No | Results to skip. Server default: 0. |
| `-t, --tenant <NAME>` | No | Tenant name. Defaults to the authenticated tenant. |
| `--output <FMT>` | No | `json` (default — always use this), `table`, `yaml`, `plain`. |

> Date parsing rejects invalid input upfront with `Invalid date "<raw>". Use an ISO-8601 value like 2026-01-01 or 2026-01-01T00:00:00Z.` — no silent fallback.

## Output Schema

Envelope:
```json
{
  "Result": "Success",
  "Code": "SapPlannerCoverage",
  "Data": [ /* coverage rows */ ]
}
```

Each row:

| Field | Type | Meaning |
|---|---|---|
| `TCode` | string | SAP transaction code (e.g. `ME22`). |
| `TCodeDesc` | string | Human description (e.g. `Change Purchase Order`). |
| `UsageRating` | number | Execution-frequency score. `0` only appears when `--include-unused` is set. |
| `TestCases` | array | Test cases covering this TCode. Each: `{ TestCaseId, TestCaseObjKey }`. |
| `TestSets` | array | Test sets covering this TCode. Each: `{ TestSetId, TestSetObjKey }`. |

Empty `TestCases` + `TestSets` on a row = used in production but **no test coverage**. This is the primary signal for gap analysis.

### Duplicate TCodes — interpret as Interface variants, not separate connectors

When the response contains multiple rows with the **same `TCode`**, they are **not** from different SAP connectors. They are the same transaction on the same connector, split by **Interface type** — `WinGui`, `WebGui`, `Fiori`, etc. The current output schema does not expose the interface field, so the rows look identical apart from differing `UsageRating`, `TestCases`, and `TestSets`.

How to handle this in analysis:

- **Do not deduplicate by `TCode`.** Each row represents real, distinct coverage on a separate UI surface. Collapsing them hides interface-specific gaps (e.g. `ME22` covered on WinGui but not Fiori).
- **Do not attribute duplicates to multiple connectors.** `--connector-id` scoping already constrains to one connector; duplicates inside that scope are interface variants.
- When summarising coverage for the user, group by `TCode` but list each row separately ("ME22 — 2 interface variants: 1 covered, 1 gap"). Ask the user which interface a row corresponds to if it matters — the CLI cannot tell you today.
- When this matters for a workflow, surface the limitation explicitly so the user knows the interface dimension is opaque in the current preview build.

## Examples

### List first page of used transactions (default)

```bash
node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage \
  --project-key DEMO --output json
```

Server defaults: `onlyUsed: true`, all connectors, all transports, limit 20.

### Include unused transactions, scope to one connector, page deeper

```bash
node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage \
  --project-key DEMO \
  --connector-id b7741d2b-9500-0000-6b20-0b499e3c8808 \
  --include-unused \
  --limit 100 --offset 100 \
  --output json
```

### Restrict to specific transports within a date window

```bash
node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage \
  --project-key DEMO \
  --transports TR0001 TR0002 \
  --from-date 2026-01-01 --to-date 2026-06-01 \
  --output json
```

### Filter to coverage-gap rows only (client-side JMESPath)

```bash
node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage \
  --project-key DEMO --include-unused \
  --output json \
  --output-filter "[?length(TestCases) == \`0\` && length(TestSets) == \`0\`].{TCode: TCode, Desc: TCodeDesc, Usage: UsageRating}"
```

### Partition fits vs gaps in one call

```bash
node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage \
  --project-key DEMO --from-date 2026-05-27 --to-date 2026-06-10 \
  --output json \
  --output-filter "{Fits: [?length(TestCases) > \`0\`], Gaps: [?length(TestCases) == \`0\` && length(TestSets) == \`0\`]}"
```

### Full pipeline — fits run + gaps report (PowerShell)

```powershell
$cli  = "C:\repos\cli\packages\cli\dist\index.js"
$proj = "<PROJECT_KEY>"

# 1. Pull coverage
$cov = (& node $cli tm sapplanner coverage --project-key $proj `
          --from-date 2026-05-27 --to-date 2026-06-10 --output json) | ConvertFrom-Json

# 2. Segregate
$fits = $cov.Data | Where-Object { $_.TestCases.Count -gt 0 }
$gaps = $cov.Data | Where-Object { $_.TestCases.Count -eq 0 -and $_.TestSets.Count -eq 0 }

# 3. Dedupe test case IDs
$ids = $fits | ForEach-Object { $_.TestCases.TestCaseId } | Select-Object -Unique

# 4. Run all fits (space-separated UUIDs)
$run = (& node $cli tm testcases run --project-key $proj --test-case-id @ids --async --output json) | ConvertFrom-Json
$execId = $run.Data.ExecutionId

# 5. Wait
& node $cli tm wait --execution-id $execId --project-key $proj --timeout 1800 --output json | Out-Null

# 6. Fits report (per test case)
$logs = (& node $cli tm executions testcaselogs list --execution-id $execId --project-key $proj --output json) | ConvertFrom-Json
$logs.Data | Select-Object TestCaseObjKey, TestCaseName, Status, StartTime, EndTime

# 7. Gaps report (per row, sorted by usage)
$gaps | Sort-Object -Property UsageRating -Descending |
  Select-Object TCode, TCodeDesc, UsageRating
```

## Workflows

### Coverage-driven execution & reporting

End-to-end pipeline: pull coverage → segregate fits vs gaps → run every unique fit test case as one execution → wait for terminal state → produce two reports (fits with pass/fail, gaps prioritized by usage).

**Inputs**

- `<PROJECT_KEY>` — required.
- Optional time window: `<FROM>` / `<TO>` (ISO-8601). Omit for all-time.
- Optional connector scope: `<CONNECTOR_ID>`.

**Preconditions**

1. Authenticated: `uip login status --output json`.
2. Default Orchestrator folder set on the project (parent skill Critical Rule #10). Set with `uip tm project set-default-folder --project-key <KEY> --folder-key <FOLDER_KEY>`.
3. Test cases linked to automations. `uip tm testcases run` requires `IsAutomated: true` and a linked package on each target. Inspect with `uip tm testcases list --project-key <KEY> --output json` and `IsAutomated`. Link missing ones with `uip tm testcases link-automation`.

**Steps**

1. **Pull coverage** for the window.
   ```bash
   node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage \
     --project-key <PROJECT_KEY> \
     [--from-date <FROM> --to-date <TO>] \
     [--connector-id <UUID>] \
     --output json
   ```
   Empty `Data` → stop. No SAP activity in window. Report this and exit.

2. **Segregate fits vs gaps per row.** Fit row: `TestCases.length > 0`. Gap row: `TestCases.length == 0 AND TestSets.length == 0`. Test-set-only coverage (empty `TestCases`, non-empty `TestSets`) is neither — surface separately if present (rare).

   JMESPath partition shortcut:
   ```bash
   --output-filter "{Fits: [?length(TestCases) > \`0\`], Gaps: [?length(TestCases) == \`0\` && length(TestSets) == \`0\`]}"
   ```

   > Duplicate `TCode` rows are SAP Interface variants (WinGui / WebGui / Fiori) of the same connector, not separate connectors. Do not dedupe by `TCode` — a TCode can legitimately be a fit in one variant and a gap in another.

3. **Collect unique test-case IDs from all fit rows.** The same test case can appear under multiple TCodes (one automation covering several transactions) and under multiple interface variants. Dedupe by `TestCaseId`.

   PowerShell:
   ```powershell
   $coverage = node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage `
     --project-key <KEY> --output json | ConvertFrom-Json
   $testCaseIds = $coverage.Data |
     Where-Object { $_.TestCases.Count -gt 0 } |
     ForEach-Object { $_.TestCases.TestCaseId } |
     Select-Object -Unique
   ```

   Bash (jq):
   ```bash
   node "..." tm sapplanner coverage --project-key <KEY> --output json |
     jq -r '.Data[] | select(.TestCases | length > 0) | .TestCases[].TestCaseId' |
     sort -u
   ```

4. **Run all fits in one execution.** `--test-case-id` is **space-separated** for multiple UUIDs.
   ```bash
   node "..." tm testcases run \
     --project-key <PROJECT_KEY> \
     --test-case-id <UUID1> <UUID2> <UUID3> \
     --async \
     --output json
   ```
   Capture `ExecutionId` from the response (under `Data`). `--async` returns immediately; omit to block synchronously (then skip Step 5).

5. **Wait for terminal state.**
   ```bash
   node "..." tm wait \
     --execution-id <EXECUTION_ID> \
     --project-key <PROJECT_KEY> \
     --timeout 1800 \
     --output json
   ```
   Default timeout per command. Override `--timeout` (seconds) for long suites.

6. **Pull per-test-case results — fits report.**
   ```bash
   node "..." tm executions testcaselogs list \
     --execution-id <EXECUTION_ID> \
     --project-key <PROJECT_KEY> \
     --output json
   ```
   Each row exposes `TestCaseId`, `TestCaseName`, `Status` (`Passed` / `Failed` / `Skipped` / …), `StartTime`, `EndTime`. For top-line counts use `uip tm executions get-stats --execution-id <ID> --project-key <KEY> --output json`.

7. **Compose the two reports.**

   **Fits report (pass/fail per test case, with the TCodes each covers):**

   | Test Case (Key) | Name | TCodes Covered | Status | Duration |
   |---|---|---|---|---|

   Annotate each row with the TCodes it covers by reverse-mapping from the Step 1 payload: for each `TestCaseId` in the test-case-log list, collect every `TCode` whose `TestCases[].TestCaseId` matches. Then surface counters (`Passed / Failed / Skipped / Total`).

   **Gaps report (prioritized by usage):**

   | TCode | Description | UsageRating | Interface Variant # | Priority |
   |---|---|---|---|---|

   Sort by `UsageRating` desc. Each gap row from Step 2 is one TCode × interface variant — keep rows separate. Recommend authoring tests for the top 3 by usage; cite the variant index so the author knows which interface is in scope.

**Output to user**

Two sections, in order:
1. **Fits — execution result.** Pass/fail counters, per-test-case table, link to the Test Manager execution URL.
2. **Gaps — coverage holes.** Prioritized table, recommendation block with `uip tm testcases create` / `link-automation` commands.

**Failure handling**

| Condition | Action |
|---|---|
| Step 1 returns `Data: []` | Stop. Report "no SAP activity in window." No execution, no gap report (nothing to report). |
| Zero fits collected in Step 3 | Skip Steps 4–7. Produce gap report only. Tell the user no automated coverage exists for this window. |
| `--test-case-id` rejected: test case not automated | The corresponding `IsAutomated` is false or `link-automation` was never run. Reuse Preconditions step 3 to fix. |
| `set-default-folder` not run | `testcases run` fails. Set the folder and retry. |
| Per-`uip` retries | Cap at 3 per parent skill Critical Rule #4. |



1. Verify auth: `uip login status --output json`. Re-login if needed.
2. Resolve the project: `uip tm project list --filter <NAME_OR_KEY> --output json`. Capture `PROJECT_KEY`.
3. Run coverage with unused transactions included:
   ```bash
   node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage \
     --project-key <PROJECT_KEY> --include-unused --output json
   ```
4. Filter for rows where both `TestCases` and `TestSets` are empty. Those are the gaps.
5. For each gap row with `UsageRating > 0`, recommend a new test case (highest production usage, no coverage = highest risk).
6. Page with `--limit` / `--offset` until `Data` is shorter than `--limit`.

### Transport impact preview

1. Collect the transport IDs in the proposed release.
2. Run coverage scoped to those transports:
   ```bash
   node "C:\repos\cli\packages\cli\dist\index.js" tm sapplanner coverage \
     --project-key <PROJECT_KEY> --transports <ID1> <ID2> … --output json
   ```
3. Aggregate `TestCases` / `TestSets` across rows. Those are the regression sets to schedule before the transports promote.
4. Cross-reference with `uip tm executions list-filtered --labels <RELEASE_LABEL>` to confirm coverage was actually exercised in recent runs.

### Connector-scoped review

When the project has multiple SAP connectors and only one is in scope for the review:
1. Get the connector UUID from your project's connector registry (out of scope for this guide — ask the user).
2. Pass `--connector-id <UUID>` to constrain results to that connector's transactions only.

## Pagination

- `--limit` caps a single response (default 20).
- `--offset` skips rows; combine with `--limit` to walk pages.
- Stop paginating when the returned `Data` length is less than `--limit`.

## Error Handling

| Failure | Likely cause | Fix |
|---|---|---|
| `Invalid date "<raw>"` | Bad `--from-date` / `--to-date` format. | Use `YYYY-MM-DD` or full ISO-8601. |
| Auth error from `initializeContextWithProject` | Missing login or no access to the project. | `uip login`, then verify project access with `uip tm project list --filter <PROJECT_KEY>`. |
| `403 Forbidden` (TM forbidden message) | User lacks Test Manager read permission on the project. | Ask a project owner to grant access. |
| `unknown command 'sapplanner'` | You invoked the published `uip` binary instead of the local dev build. | Use `node "C:\repos\cli\packages\cli\dist\index.js" …`. |
| Empty `Data` array | No transactions match the filters (or `--include-unused` was needed). | Drop the date / transport filters, or add `--include-unused`. |

Cap retries at 3 per the parent skill's Critical Rules. On the 4th failure, stop and report to the user.

## Anti-patterns

- **Do NOT collapse duplicate `TCode` rows.** Same TCode appearing twice = same connector, different SAP Interface (WinGui / WebGui / Fiori / …). The interface field is not in the current output schema. Deduplicating loses interface-level coverage gaps. See *Duplicate TCodes* in the Output Schema section.
- **Do NOT mix `--include-unused` with date filters and expect zero-usage rows in that window.** `--include-unused` lifts the `onlyUsed` server flag globally; date bounds still apply to execution history. A truly unused transaction has no executions to date-bound.
- **Do NOT page without checking response length.** A returned `Data` array shorter than `--limit` means you've reached the end — keep paging and you'll just get empty arrays.
- **Do NOT guess connector UUIDs.** No `sapplanner connectors list` exists yet. Ask the user, or look them up via the Test Manager UI / project configuration.
- **Do NOT swap `uip tm sapplanner` for the dev-build path silently.** When the command lands in a public `uip` release, update this guide and the SKILL.md row to drop the `node "…\index.js"` prefix.
