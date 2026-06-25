# Loop: close the BPMN test-coverage gap (HIGH scenarios)

## Goal
Port the **HIGH-portability** Flow task-tests to BPMN so BPMN's authoring
coverage mirrors Flow's, where BPMN's surface actually supports the scenario.
Port only Flow scenarios that are general behavior with no/partial BPMN
equivalent. Do **not** invent coverage Flow doesn't have, and do not port
Flow-specific runtime scenarios BPMN cannot exercise (no live-run in BPMN
tests).

## Definition of done
Every newly added BPMN case passes in the `run-coder-eval.yml` cloud eval.

## Hard rules
- Match existing BPMN test structure, fixtures, naming, and `_shared` helpers
  EXACTLY. No new harness or fixture style.
- One scenario group per commit.
- The two gates below are stop-and-ask. Never self-approve them.
- BPMN tests are authoring + operate/diagnose only — no upload/publish/run/pack.
  Mirror Flow scenarios by converting `flow debug` runtime assertions into
  structural / well-formed-XML / checklist assertions, the way existing BPMN
  tests already do.

## Gates
1. **INVENTORY** — produce the Flow-vs-BPMN per-test breakdown, stop, let the
   user pick the subset. Write no tests until the subset is handed back.
   _Status: table delivered; HIGH subset = the 11 Tier-A rows below._
2. **EVAL TRIGGER** — show the exact `gh workflow run` command for
   `run-coder-eval.yml`, stop, wait for go-ahead before firing CI.
   Re-confirm on each re-run.

## HIGH scenario subset (Tier A — 11 cases)
General behavior, no/partial BPMN equivalent, inside BPMN's authoring surface.

| # | Flow source | BPMN target concept |
|---|---|---|
| 1 | edit/add_node | insert node into existing `.bpmn` (surgical edit) |
| 2 | edit/remove_node | delete node + re-wire sequence flows |
| 3 | edit/move_node | move node between branches |
| 4 | edit/update_node | change node config in place |
| 5 | edit/add_output | add output field |
| 6 | edit/group_to_subflow | extract nodes into a subprocess |
| 7 | single_node/subflow | subprocess / call activity |
| 8 | single_node/delay | timer intermediate event |
| 9 | smoke/scheduled_trigger | timer start event |
| 10 | smoke/merge_parallel_sync | parallel gateway fork + sync join |
| 11 | single_node/terminate | terminate / end-event semantics |

## Proposed commit grouping (one group per commit)
- **Commit 1 — `edit/`**: cases 1–6 → new `tests/tasks/uipath-maestro-bpmn/edit/`
- **Commit 2 — structural nodes**: cases 7–9, 11 (subprocess, timer event,
  timer start, terminate) → `tests/tasks/uipath-maestro-bpmn/author/` (or
  `nodes/`, match existing placement)
- **Commit 3 — parallel control flow**: case 10 (parallel gateway join) →
  `author/` or `smoke/`

Final group placement to be confirmed with the user before writing.

## Explicitly NOT ported (Flow-specific / out of BPMN surface)
ixp/*, evaluate/*, connector_features/*, context-grounding/*, transform nodes,
multi_node billing_* (`lifecycle:execute`), execution-asserted multi_node, and
inline-agent scenarios. BPMN has no IXP node, eval framework, transform nodes,
or live-run, so porting these would invent coverage.

## Loop procedure
1. (Gate 1 done) Pick a commit group from the subset.
2. Implement that group's BPMN tasks using exact existing conventions; lint
   with `/lint-task`.
3. **Gate 2**: show the `gh workflow run run-coder-eval.yml ...` command, STOP.
4. On go-ahead: trigger, `gh run watch`, report failures.
5. For each failing BPMN case: propose a fix, re-confirm trigger (Gate 2), re-run.
6. Repeat until all new BPMN cases are green, then commit the group.
7. Next group. Stop when all 11 are green, or hand back to user if blocked.

## Stop condition
All 11 new BPMN cases green in `run-coder-eval.yml`. If blocked, stop and hand
back to the user.
