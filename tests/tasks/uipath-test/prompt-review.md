# `tests/tasks/uipath-test/` — prompt review

Existing test prompts vs. natural-user rewrites. Methodology in [hitl-prompts-review.html](../../hitl-prompts-review.html) and [CLAUDE.md](../../CLAUDE.md).

## Scope of this folder

The `uipath-test` skill is the UiPath Test Manager assistant — it manages Test Manager projects, test cases, test sets, executions, and generates shareable test reports via the `uip tm` CLI surface. The three eval YAMLs here cover (1) authenticating + discovering Test Manager projects, (2) walking the project → test set → test case hierarchy, and (3) generating a persona-tailored (QA Engineer) test report from a real test set. All three are discovery / happy-path workflow tests rather than CLI-flag coverage or refusal tests.

## Insider markers seen in this folder

- **Skill-loader preamble on every prompt**: every test starts with `"Before starting, load the uipath-test skill and follow its workflow."` — that is harness language, not customer language. A real Test Manager user wouldn't know the skill exists, let alone instruct the agent to load it.
- **"the skill" referenced as a known artifact**: `report_generation.yaml` says "using the default filename convention from the skill" — the user voice doesn't reference the skill's own conventions; they'd just ask for a file with a sensible name or omit the filename entirely.
- **Product name capitalized as a proper noun** (`UiPath Test Manager`) — borderline. Real users do say "Test Manager" but the phrasing across all three prompts is uniformly clinical/spec-like, which feels harness-authored.
- **Persona token in bold** (`**QA Engineer**`) in `report_generation.yaml` — markdown styling inside a user prompt is an eval-harness affordance signaling the grader which persona path to score against. Real users wouldn't bold their role.
- **Eval-fixture nudges**: "Pick a test set that actually has data so the report is meaningful" / "Find a project that actually has test sets" — these are guardrails for the grader (avoid empty-result branches), not how a customer asks. A customer typically has a specific project/set in mind, or asks the agent to pick anything.

No CLI flag names, no `uip tm` command strings, no internal IDs, no embedded JSON, and no skill-rule callbacks beyond the loader preamble. The harness leakage here is shallow and uniform — fixing the preamble + a couple of phrasings flips all three to natural.

## Verdict summary

| Verdict | Count |
|---|---|
| Insider — fixable | 3 |
| Insider — legitimate (CLI/refusal/antipattern coverage) | 0 |
| Mixed | 0 |
| Natural | 0 |

## Per-test review

### All tests

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-test-auth-project-discovery` (`auth_project_discovery.yaml`) | Insider — fixable | "Before starting, load the uipath-test skill and follow its workflow. I want to see my UiPath Test Manager projects. Help me discover what I have access to." The body is close to natural, but the leading skill-loader instruction is pure harness language. | "Can you show me which Test Manager projects I have access to? I'm not sure what's there and want to get the lay of the land." |
| `skill-test-report-generation-qa` (`skill-test-report-generation-qa.yaml`) | Insider — fixable | "Before starting, load the uipath-test skill ... Generate a **QA Engineer** test report from one of my UiPath Test Manager test sets. Pick a test set that actually has data so the report is meaningful, and save the report file in the current working directory using the default filename convention from the skill." Skill-loader preamble, bolded persona token, "default filename convention from the skill", and an eval-fixture nudge ("pick one that actually has data") all signal harness authorship. | "I need a QA-engineer-style test report out of Test Manager. Pick one of my test sets that has recent runs and save the report here in my current folder — whatever filename makes sense." |
| `skill-test-testset-hierarchy-discovery` (`testset_hierarchy_discovery.yaml`) | Insider — fixable | "Before starting, load the uipath-test skill ... Walk me through the structure of one of my UiPath Test Manager projects. Find a project that actually has test sets, list its test sets, and for the first test set show me the test cases inside." Loader preamble plus the same eval-fixture nudge ("find a project that actually has test sets"). The numbered walk ("list test sets, then show test cases inside the first one") is a harness recipe; a real user would just ask for the structure. | "I'm new to one of our Test Manager projects and want to understand how it's organized. Can you walk me through a project that's actually being used — what test sets it has, and what's inside one of them?" |

## Notes for the PR description

- **Single dominant pattern: the skill-loader preamble.** All three prompts open with `"Before starting, load the uipath-test skill and follow its workflow."` Dropping that one line moves every prompt closer to natural — it's the highest-leverage single fix in this folder, and the same pattern likely exists across other skill folders.
- **Eval-fixture nudges leak through twice** (`"Pick a test set that actually has data"`, `"Find a project that actually has test sets"`). These exist to keep the grader off empty-result code paths but they read as harness scaffolding. Consider seeding fixture data so the prompt doesn't need to defend against it.
- **No CLI-flag coverage tests in this folder.** Unlike Orchestrator/platform skills, none of these three tests are evaluating whether the agent reaches for a specific flag (`--user` vs `--user-id`, etc.), so there are zero "legitimately insider" prompts to leave alone. Every prompt here is testing intent recognition and judgment, which means every prompt should sound like a customer.
- **The persona token in `report_generation.yaml` (`**QA Engineer**`) should stay as a concept but lose the bold markdown** — customers say "I need a QA-style report" without styling it, and the bolding is a tell that a grader is keying off the exact string.
