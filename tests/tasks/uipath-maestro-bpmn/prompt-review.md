# `tests/tasks/uipath-maestro-bpmn/` — prompt review

Existing test prompts vs. natural-user rewrites. Methodology in [hitl-prompts-review.html](../../hitl-prompts-review.html) and [CLAUDE.md](../../CLAUDE.md).

## Scope of this folder

`uipath-maestro-bpmn` is the Maestro BPMN Process Orchestration skill — authoring `.bpmn` XML projects, packaging them with `uip maestro bpmn ...`, and operating/diagnosing runs in the cloud. The 17 yaml tests split into seven subfolders covering author (2), authoring of specific task types (3), connector boundary + registry discovery (2), nodes / wrapper-shape coverage (3), an end-to-end author+validate+pack flow (2), operate/diagnose (1), and smoke (4). Because BPMN itself is a public standard, the customer-vs-insider line here is unusually narrow: "exclusive gateway", "user task", "service task", "boundary event" are real customer vocabulary, but `uipath:activity` shells with literal `Orchestrator.StartAgentJob`-style type strings, `bindings_v2.json`, `entry-points.json`, `uipath:migrationVersion`, and `uipath:scriptVersion="v3"` are not.

## Insider markers seen in this folder

- **Skill-rule callback header on 17/17 prompts:** every prompt opens with `Load and follow the uipath-maestro-bpmn skill.` — this is a harness affordance, not a customer phrase. A real customer says what they want; the agent decides which skill applies.
- **Literal `uipath:activity` type strings** in user voice: `Orchestrator.StartAgentJob`, `Orchestrator.ExecuteApiWorkflowAsync`, `Orchestrator.BusinessRules`, `Orchestrator.CreateQueueItem`, `Orchestrator.CreateAndWaitForQueueItem`, `Orchestrator.StartAgenticProcess(Async)`, `Orchestrator.StartCaseMgmtProcess(Async)`, `Orchestrator.StartJob`, `A2A.AgentExecution`, `Intsvc.WaitForEvent`, `Maestro.SendMessageEvent`, `Maestro.CasePlanScheduler`, `Maestro.CaseManagerGuardrails`, `Maestro.CaseRulesEvaluator`, `Actions.HITL`. Customers know "Slack post message", not `Intsvc.*` type IDs.
- **BPMN element machine names in user voice:** `bpmn:serviceTask`, `bpmn:sendTask`, `bpmn:scriptTask`, `bpmn:userTask`, `bpmn:businessRuleTask`, `bpmn:callActivity`, `bpmn:receiveTask`, `bpmn:intermediateThrowEvent`, `bpmn:process` id, `bpmn:error`. A user says "approval task" or "send a Slack notification"; the colonized names are XSD-element names.
- **UiPath BPMN extension XML internals:** `uipath:variables version="v1"`, `uipath:migrationVersion` (`5`, `11`, `11.5`), `uipath:scriptVersion` (`v2`, `v3`), `uipath:input name="args"`, `uipath:output var=...`, namespace URL `http://uipath.org/schema/bpmn`, `=vars.<id>` expression syntax.
- **Generated package-file inventory** dropped into user voice: `project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`. The skill says CLI owns these; customers don't enumerate them.
- **Triple-nested project paths**: e.g. `ApiWorkflowDispatch/ApiWorkflowDispatch/ApiWorkflowDispatch.bpmn`, `ScriptNormalizer/ScriptNormalizer/ScriptNormalizer.bpmn` — clearly a harness fixture path, not how a user describes a project location.
- **Literal CLI invocations** with `--output json`: `uip maestro bpmn validate ... --output json`, `uip maestro bpmn pack ... --output json`, plus the verbatim python3 XML-parse fallback in `init_pack_validate`.
- **Harness guard rails:** `Do not upload, publish, deploy, debug, or run`, `Do not ask for approval or pause for feedback`, `Do NOT pause between planning and implementation`, `Do NOT retry, cancel, migrate, move a cursor`, `Do not inspect mocks/, fixtures/, or response JSON files directly`.
- **Eval-grader output contracts:** "Save outputs under a local `registry-evidence/` directory", "write your inspection report at `inspection-report.md`", "Use these exact ownership labels: `BPMN source`, `Generated package metadata`, `Integration Service enrichment`, and `Cloud configuration`", "Send packed output to a local `fixture-pack-output/` directory".
- **Test-fixture leakage:** `job-triage-001`, `inst-triage-001`, `folder-public` (public-safe but still fixture-style), the 8 hard-coded `fixtures/validation/<name>/` paths.
- **Skill machine-name `uipath-maestro-bpmn` quoted in the user line** — a customer would say "Maestro BPMN" or just describe what they want.

## Verdict summary

| Verdict | Count |
|---|---|
| Insider — fixable | 5 |
| Insider — legitimate (CLI/refusal/antipattern/wrapper-coverage) | 8 |
| Mixed | 4 |
| Natural | 0 |

No prompt is fully natural — every one starts with the harness-style `Load and follow the uipath-maestro-bpmn skill.` opener. Treat that opener as a folder-wide fixable across the board even where the rest of the prompt is legitimately insider.

## Per-test review

### `author/`

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-bpmn-gateway-sequence-flows` | Mixed | Opens with "Load and follow the uipath-maestro-bpmn skill." Describes a sensible invoice-triage process (exclusive gateway on `amount >= 1000`, parallel gateway for follow-up tasks) but pins the file to `InvoiceTriageBpmn/InvoiceTriageBpmn.bpmn`, demands "BPMN DI shapes and waypoints for every visible node and edge", and adds the "do not upload, publish, deploy, debug, or run" guard. | "I need a Maestro BPMN process for invoice triage. It starts manually with an `invoiceId` and `amount`, records the intake, then splits: invoices of $1,000 or more go to a manager review, everything else auto-approves. After the routing decision, two follow-ups should run in parallel — notify the requester and archive the decision — and then the process ends. Project name is `InvoiceTriageBpmn`. Please draft the diagram and the conditional routing locally; don't run or deploy it yet." |
| `skill-bpmn-simple-approval-bpmn` | Insider — legitimate | Spells out the full BPMN-extension contract: `bpmn:sendTask` with `Orchestrator.CreateQueueItem`, `bpmn:scriptTask` with `scriptFormat="JavaScript"` and `uipath:scriptVersion v3`, `uipath:variables version="v1"`, `uipath:migrationVersion 11/11.5`, Jint constraints. The grader checks for exact extension shells. | _Keep as-is — wrapper-shape coverage test. The grader (`check_simple_approval_bpmn.py`) asserts presence of these exact `uipath:activity` types and metadata versions, so the prompt has to surface them. Worth dropping just the "Load and follow the uipath-maestro-bpmn skill" header._ |

### `authoring/`

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-bpmn-api-workflow-task` | Mixed | Forces project at `ApiWorkflowDispatch/ApiWorkflowDispatch/...`, requires a `bpmn:serviceTask` with `uipath:activity` type `Orchestrator.ExecuteApiWorkflowAsync`, lists the 5 generated package files, and ends with the antipattern guard "Do not model as a business rule, call activity, script task, or generic task." | "I need a Maestro BPMN process called `ApiWorkflowDispatch` that runs an API Workflow to sync a customer record. It should start manually with `customerId` and `requestedBy`, call the API workflow as a service step, capture the invocation handle and status/result, and route to a success end event with a boundary error path to a failure end event. Build it locally so we can inspect it — don't publish or run anything yet." (The antipattern phrasing — "model it as the API-workflow activity, not as a generic service task or business rule" — is legitimate coverage and can be added as a final sentence if the test is specifically checking that choice.) |
| `skill-bpmn-business-rule-task` | Mixed | Same skeleton as the API-workflow test but for `Orchestrator.BusinessRules` on a `bpmn:businessRuleTask`, with the antipattern guard "Do not use a generic service task for the business rule." | "We have a loan-precheck step that needs to run our business rules engine. Create a Maestro BPMN project `BusinessRuleDecision`: manual start with applicant score and requested amount, evaluate eligibility through our business-rules step, then an exclusive gateway routes to an approved end event or a review end event based on the rule outcome. Build it locally. (The eligibility step should use the dedicated business-rule task, not a generic service task.)" |
| `skill-bpmn-script-jint-lifecycle` | Insider — legitimate | Requires `bpmn:scriptTask` with `scriptFormat="JavaScript"`, `uipath:scriptVersion v3`, Jint-only behavior, and the triple-nested project path. | _Keep as-is — script-lifecycle authoring contract. The test is verifying the agent knows the Maestro script-task metadata contract (Jint, `v3`, no Node APIs). Worth dropping the "Load and follow…" opener and the triple-nested path._ |

### `connector/`

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-bpmn-integration-service-boundary` | Mixed | Asks for a "draft executable boundary" for a Slack Integration Service step and names CLI-owned enrichment: `bindings_v2.json`, "dynamic schemas", "generated outputs". Demands a README listing "the exact CLI-owned enrichment blockers before upload or run." | "I want to sketch a Maestro BPMN process `SlackDigestBoundaryBpmn` that prepares a digest and posts it to Slack through our Integration Service connector. Just the skeleton, variables, and diagram for now — leave the Slack connector step as a draft placeholder, since the actual connector wiring and connection binding will come from the CLI. Add a short notes file calling out what still needs CLI enrichment before we can upload or run it." |
| `skill-bpmn-registry-discovery` | Insider — legitimate | Names the `uip` CLI explicitly, mandates `--output json`, dictates the `registry-evidence/` directory, and asks for raw JSON for catalog, filtered lookup, and detail. | _Keep as-is — CLI-coverage smoke. The whole point is verifying the agent exercises the registry discovery CLI surface and saves the raw JSON the grader inspects._ |

### `e2e/`

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-bpmn-author-validate-pack` | Insider — legitimate | Spells out two exact CLI invocations: `uip maestro bpmn validate PurchaseApproval/PurchaseApproval.bpmn --output json` and `uip maestro bpmn pack PurchaseApproval dist --output json`. | _Keep as-is — end-to-end CLI lifecycle coverage. The point is that the agent reaches for `validate` and `pack` with `--output json`._ |
| `skill-bpmn-e2e-invoice-exception-triage` | Mixed | Natural-sounding process (manual start, classify, exclusive gateway by risk, user task for review) but enumerates all 5 generated package files and finishes with "Do NOT pause between planning and implementation. Build the complete local project end-to-end in a single pass." | "Build me a Maestro BPMN project called `InvoiceExceptionTriage`. It starts with an `invoiceId` and `amount`, a script step classifies risk, and an exclusive gateway either auto-approves low-risk invoices or routes high-risk ones to a `Review invoice` user task that ends in a `reviewed` end event. Keep everything synthetic and local — no upload or run. Build the whole thing in one shot so we can review it." |

### `nodes/`

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-bpmn-contract-variant-wrappers` | Insider — legitimate | Enumerates 15 distinct `uipath:activity` wrapper types verbatim (Orchestrator/A2A/Maestro/Intsvc families) plus `uipath:migrationVersion` values `5`/`11`/`11.5` and legacy `uipath:scriptVersion v2` preservation. | _Keep as-is — wrapper-family-coverage matrix. There is no customer-voice phrasing for "visit each of these 15 internal activity types"; this test exists specifically to verify the catalog is covered._ |
| `skill-bpmn-hitl-rpa-wrappers` | Insider — legitimate | Forces `bpmn:userTask` with `Actions.HITL` and `bpmn:serviceTask` with `Orchestrator.StartJob` — the test is about which wrapper shell the agent reaches for. | _Keep as-is — wrapper-choice coverage (the agent's job is to pick `Actions.HITL` for the HITL step and `Orchestrator.StartJob` for the RPA step rather than substitute generic tasks)._ |
| `skill-bpmn-script-jint-guidance` | Insider — legitimate | Deepest insider in the folder: names the BPMN-extension namespace URL, demands `uipath:input name="args"` with top-level identifier access, `=vars.<id>` variable-id expressions, output mapping via `var` (not `name`), full Jint constraint list. | _Keep as-is — script-authoring-rule contract. This is a documentation-driven correctness test, not an intent-recognition test. Worth dropping the "Load and follow…" opener._ |

### `operate-diagnose/`

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-bpmn-operate-diagnose-minimal-fault-triage` | Mixed | Customer-shaped opening ("A BPMN process run failed. Diagnose it.") but pins fixture IDs (`job-triage-001`, `inst-triage-001`, `folder-public`), then mandates the four exact ownership labels (`BPMN source`, `Generated package metadata`, `Integration Service enrichment`, `Cloud configuration`) and the long "Do NOT retry, cancel, migrate, move a cursor, debug, run, upload, publish, deploy" guard, plus "do not inspect `mocks/`, `fixtures/`, or response JSON files directly." | "One of our Maestro BPMN runs failed and I need a short diagnosis. The job is `job-triage-001`, instance `inst-triage-001`, folder `folder-public`. Use the Maestro CLI to pull the incident and figure out: which BPMN element faulted, what a user would see, the likely root cause, and whether the fix lives in the BPMN source, the generated package files, the Integration Service connector wiring, or cloud configuration. Then tell me the safe next step — don't retry or restart anything, just write up the findings in `diagnosis.md`." (The four ownership labels are a grader contract — fine to leave the "use these exact labels" line in if the grader requires verbatim strings.) |

### `smoke/`

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-bpmn-imported-xml-inspect` | Insider — legitimate | Lists three fixture `.bpmn` paths to inspect, mandates `inspection-report.md` at workspace root, and requires each section to cite a real `bpmn:process` id and a fixture-specific token like a `bpmn:error` reference, an `Intsvc.*` extension type, or `multiInstance` loop metadata. | _Keep as-is — anti-hallucination inspection test. The token-citation requirement exists specifically to defeat the agent passing by writing plausible-sounding prose, so the prompt has to name what counts as evidence._ |
| `skill-bpmn-init-pack-validate` | Insider — legitimate | Tells the agent to use `uip` CLI when supported and gives the exact python3 XML-parse fallback as a fallback command. | _Keep as-is — CLI-coverage smoke with a deterministic fallback. The verbatim `python3 -c ...` line is there so the grader can score "did you actually run a validation command" rather than "did you read the file and declare it valid". Dropping the "Load and follow…" opener is still worthwhile._ |
| `skill-bpmn-validation-fixtures-pack` | Insider — fixable | Lists eight hard-coded `fixtures/validation/<name>/` paths to pack and sets `fixture-pack-output/`. Not a customer ask at all. | _Keep as-is — fixture-pack smoke. There is no natural-customer voice for "pack each of our 8 fixture projects"; this is a corpus regression test. Worth at minimum dropping the "Load and follow…" opener._ |
| `skill-bpmn-validation-fixtures` | Insider — legitimate | Tells the agent to run `bash .maintenance/check-validation-fixtures.sh` and report results. | _Keep as-is — fixture-corpus health check, pure smoke. Not a customer-shaped task._ |

## Notes for the PR description

- **Folder-wide `Load and follow the uipath-maestro-bpmn skill.` header.** All 17 prompts open with it. It's a harness affordance — the skill discovery system should already activate the right skill from the user's actual ask. Stripping this single line across the folder would remove the most pervasive insider marker without changing what any test grades.
- **Wrapper-coverage tests dominate.** 8 of 17 prompts (`nodes/*`, `authoring/script_jint_lifecycle`, `author/simple_approval_bpmn`, parts of `e2e/`) exist specifically to verify the agent reaches for the correct `uipath:activity` type string (`Orchestrator.StartAgentJob`, `Actions.HITL`, `Maestro.SendMessageEvent`, etc.). These are legitimately insider — there's no customer-voice substitute for "use the right XSD element from a 15-item catalog." Worth flagging in the maintainer summary so reviewers don't try to "naturalize" them.
- **Triple-nested project paths** (`ApiWorkflowDispatch/ApiWorkflowDispatch/ApiWorkflowDispatch.bpmn`) appear in 4 of the `authoring/` and `e2e/` prompts. They're harness fixture conventions and read very clearly as test scaffolding to any reader, but they're easy to flatten in the prompt (the grader doesn't actually need the user to dictate the layout — it just needs the file to exist at a known location).
- **Strongest fixable cases worth rewriting:** `author/gateway_sequence_flows.yaml`, `authoring/api_workflow_task.yaml`, `authoring/business_rule_task.yaml`, `e2e/invoice_exception_triage.yaml`, and `connector/integration_service_boundary.yaml`. Each has a real customer scenario underneath that we can recover, and the test would still grade the same thing once the wrapper-choice intent is preserved.
- **Operate/diagnose is the closest to natural** ("A BPMN process run failed. Diagnose it.") and could become a strong reference template for what a humanized Maestro BPMN prompt looks like if the fixture-ID and label-contract concessions are kept short and scoped at the end.
