# SAP Change Impact Analysis Guide

Detailed instructions to use SAP Change Impact Analysis in UiPath Test Manager.

## Prerequisites

- Authenticated session
- CLI surface probed (see [/uipath:uipath-test § Critical Rules #2](../SKILL.md#critical-rules)). Commands below use the post-rename shape; translate via the [Pre-rename fallbacks](../SKILL.md#pre-rename-fallbacks) table on a pre-rename CLI.
- A Test Manager project key

---

## Workflow

> **Every step ends by printing its result table.** Each step below has an **Output** sub-section with a required table. Print that table to the user before starting the next step — do not batch all output into the final step, and do not skip a step's table because the data feeds the next step. Four steps → four tables.

1. **Change Detection - Fetch impacted transactions (TCodes) in transports**
    - User will ask you to analyze transports for a given time range.
    - If duration is not provided, take last 14 days as default. Convert duration given by the user to StartDate and EndDate. EndDate is usually current date.
    - See if user asked for top n transactions. Use 10 by default, if not provided by user.
    - Use --offset parameter ONLY when user asked skip first N TCodes. Use 0 by default.
    - Use this command: 
        `uip tm sapplanner coverage --project-key <PROJECT_KEY> --from-date <FROM_DATE> --to-date <TO_DATE> --offset <OFFSET> --limit <LIMIT> --output json`
    - **Output (required):** Print this table now, before step 2. One row per (TCode, test case) pair — one test case per row.

      | Column | Content |
      |--------|---------|
      | TCode | The impacted transaction code |
      | Test Case ObjKey | Test case key, format `ProjectKey:100` |
      | Title | Test case title |

2. **Test Planner - Filter Automated test cases**
    - For each test case in output of (1), run the follwoing command:
        `uip tm testcases list --project-key ITP --filter <TESTCASE_KEY> --output json`
    - <TESTCASE_KEY> is in the format: ProjectKey:100.
    - From the output above, find if all of the properties have not null values:
        AutomationTestCaseName + AutomationProjectName + AutomationId + StudioWebProjectId + StudioWebFileId
    - If all of them have value, it is an automated test case. Do this for each test case.
    - **Output (required):** Print this table now, before step 3. One row per automated test case.

      | Column | Content |
      |--------|---------|
      | TCode | The impacted transaction code |
      | Test Case ObjKey | Test case key, format `ProjectKey:100` |
      | Title | Test case title |

3. **Test Executor - Execute ONLY the automated test cases for impacted transactions**
    - Refer to the automated test cases filtered in (2).
    - The project needs a default Orchestrator folder before `run`. Set it first (Critical Rule #10): `uip tm project set-default-folder --project-key <PROJECT_KEY> --folder-key <FOLDER_KEY> --output json`. Get folder keys with `uip or folders list -n <FOLDER_NAME> --all --output json`.
    - Get the Ids of the test cases, and run the following command:
      `uip tm testcases run --project-key <PROJECT_KEY> --execution-type automated --name <name> --test-case-id <TEST_CASE_ID_1> <TEST_CASE_ID_2> ... --output json`
      `--test-case-id` takes a **space-separated** list of test case Ids.
      <name> - generate name for test execution yourself
    - Do not block the session (Critical Rule #12). Capture `ExecutionId` from the JSON, then launch the wait in the background: `uip tm wait --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --timeout 1800 --output json`. On completion, fetch results with `uip tm executions get-stats --execution-id <EXECUTION_ID> --project-key <PROJECT_KEY> --output json`.
    - **Output (required):** After `get-stats` returns, print this table now, before step 4. One row per executed test case.

      | Column | Content |
      |--------|---------|
      | TCode | The impacted transaction code |
      | Test Case ObjKey | Test case key, format `ProjectKey:100` |
      | Title | Test case title |
      | Result | `Passed` / `Failed` / `None` (not run / no result) |

4. **Test Execution Reporter - Present the output report to the user**

    Emit three tables in this order. One row per TCode in each. Do not merge them.

    **Table 1 — Executed automated test cases (results).** One row per TCode.

    | Column | Content |
    |--------|---------|
    | TCode | The impacted transaction code |
    | Test Cases | Subtable of every executed automated test case for that TCode — one test case per line: `ObjKey` · `Title` · Result (`Passed` / `Failed` / `None`) |

    - Pull results from the `get-stats` JSON of step 3. Map each test case status to `Passed`, `Failed`, or `None` (not run / no result).
    - After this table, if any test case has result `Failed`, print this action line: **"Look into the failed test cases above and fix the test case execution issue."**

    **Table 2 — Non-automated test cases.** One row per TCode.

    | Column | Content |
    |--------|---------|
    | TCode | The impacted transaction code |
    | Test Cases | Subtable of every test case for that TCode that was NOT automated (failed the step 2 automated check) — one per line: `ObjKey` · `Title` |

    - After this table, if it has any rows, print this action line: **"Automate the test cases above so they become part of the test factory."**

    **Table 3 — TCodes with no test cases.** One row per TCode that has no associated test case. Order by relevance descending — relevance is the TCode priority in the user's SAP system, so the top rows are what they should automate first.

    | Column | Content |
    |--------|---------|
    | TCode | The impacted transaction code |
    | Relevance | Relevance score / rank from the step 1 `coverage` output |

    - After this table, if it has any rows, print this action line: **"Immediately prioritize creating automated test cases for the TCodes above — they have no test coverage."**

    - Add no other explanation, summary, or commentary. Output only the three tables and the three action lines above (each printed only when its table has qualifying rows).
