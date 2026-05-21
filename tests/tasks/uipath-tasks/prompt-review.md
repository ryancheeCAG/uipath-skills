# `tests/tasks/uipath-tasks/` — prompt review

Existing test prompts vs. natural-user rewrites. Methodology in [hitl-prompts-review.html](../../hitl-prompts-review.html) and [CLAUDE.md](../../CLAUDE.md).

## Scope of this folder

The `uipath-tasks` skill wraps the `uip tasks` CLI for UiPath Action Center — listing, fetching, assigning/reassigning/unassigning, and completing tasks (ExternalTask, FormTask, AppTask). These tests exercise CLI command coverage, type-routing behavior, mutually-exclusive flag handling, and refusal of out-of-scope asks.

## Insider markers seen in this folder

- Every prompt opens with the harness instruction: **"Before starting, load the uipath-tasks skill and follow its workflow."**
- CLI flags named in user voice: `--output json`, `--user` vs. `--user-id`, `--task-type`, `--folder-id`, `--as-admin`, `--type`, `--action`, `--data`
- Internal API routing exposed: "generic endpoint" vs. "type-hint endpoint (faster, type-specific route)", "elevated path"
- Eval-harness verbs: "Do NOT retry", "Do NOT re-login", "Run each command once and move on", "Save a summary to `report.json`", "purely about refusal"
- Test-fixture leakage: folder ID `123`, task IDs `7654321` / `5555555` / `3000001-3` / `1111111` / `2222222`, fake emails `alice@company.com` / `bob@company.com`
- CLI gotcha trivia stated as customer-side constraint: "Task IDs are numeric, not GUIDs", "`--user` and `--user-id` are mutually exclusive"
- Skill-rule callbacks: "refer to the skill's Critical Rules or the 'Not in scope' section"

## Verdict summary

| Verdict | Count |
|---|---|
| Insider — fixable | 4 |
| Insider — legitimate (CLI/refusal/antipattern coverage) | 1 |
| Mixed | 0 |
| Natural | 0 |

## Per-test review

### All tests

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `smoke_discovery` | Insider — fixable | 6 numbered CLI steps; `--output json` on every call; differentiates the "generic endpoint" vs. the "type-hint endpoint (faster, forms endpoint)"; "Do NOT retry or login"; "Do NOT invent new task IDs." | "I want to take a look at what's pending in our Action Center. Show me all the tasks across folders, then narrow it down to folder 123, and pull up the details on task 7654321 — it's a form task. While you're at it, who could I assign tasks in that folder to?" |
| `smoke_assignment` | Insider — fixable | "List assignable users for folder 123 — use `tasks users`"; "Assign task 1111111 to alice@company.com using the email form (`--user`)"; "Assign task 2222222 to user ID 54321 using the numeric form (`--user-id`)"; "`--user` and `--user-id` are mutually exclusive." | "Who can I assign tasks to in folder 123? Then assign task 1111111 to alice@company.com, and assign task 2222222 to user 54321. After that, hand 1111111 over to bob@company.com instead, and take 2222222 off whoever's plate it's on." |
| `smoke_completion` | Insider — fixable | "ExternalTask allows optional `--action` and `--data`. Do NOT include them — verify the minimal form works."; "FormTask requires BOTH `--action` and `--data`."; "Every complete call must include `--type <TaskType>` and `--folder-id 123`." | "I've got three tasks in folder 123 I need to close out. Task 3000001 is an external task — just mark it complete, nothing else. Task 3000002 is a form approval; approve it with the comment 'Looks good'. Task 3000003 is an app task — mark it verified." |
| `smoke_negative_guards` | Insider — legitimate | Four asks (create task, re-complete a completed task, complete a form task without data, look up a GUID-style ID) wrapped in: "refer to the skill's Critical Rules or 'Not in scope' section", "Do NOT run any uip tasks commands. This test is purely about refusal", and a strict `report.json` schema. | _Keep mostly as-is — this is a refusal/scope-policing test that needs the eval-harness scaffolding (refusal contract + `report.json` schema) to grade._ The four-ask portion could be humanized in tone ("I've got four things…") but the structural insider-ness is intrinsic to the test's purpose. |
| `e2e_fetch_tasks` | Insider — fixable | Numbered "Steps (run in order, use `--output json` on every uip tasks command)"; "Record `UIPATH_URL`, `Organization`, and `Tenant` from the response"; differentiates "generic endpoint" vs. "type-hint endpoint (faster, type-specific route)"; "still run `uip tasks list --as-admin --output json` to exercise the elevated path." | "I'm doing a quick read-only audit of what's sitting in our Action Center right now — don't change anything. Tell me which tenant I'm pointed at, list everything across folders, and then pick the first task and show me everything you can find about it (including who in that folder it could be assigned to and what else is in the same folder). If the tenant has no tasks at all, just confirm that as an admin." |

## Notes for the PR description

- **Key distinction from HITL**: HITL tests evaluate the agent's *design judgment* (which node, how to wire it). uipath-tasks tests mostly evaluate the agent's *CLI execution* (which subcommand, which flag, in what order). That's a legitimate test goal — but the insider-y prompts are still measuring "does the agent obey my numbered step list" rather than "can the agent translate a real intent into the right CLI call." Rewrites preserve the **observable customer intent** and let the test re-grade whether the skill is self-describing.
- **`smoke_negative_guards` is the one we should leave alone**: it's a refusal test, and refusal tests need the eval contract (`report.json` schema, "this test is purely about refusal") to grade. The four-ask wording inside it could still be humanized in tone, but the surrounding eval scaffolding is justified.
- **Recurring pattern across the four fixable prompts**: the harness instructs the agent both *what to do* and *what flags to use*. The rewrites strip the flag literacy and just describe the goal — which is a stronger test of whether the skill's own documentation is teaching the agent the right routing.
- **`task_id` naming is consistent and good** — `skill-tasks-smoke-assignment` etc. — no change needed there.
