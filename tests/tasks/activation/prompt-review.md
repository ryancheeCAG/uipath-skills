# `tests/tasks/activation/` — prompt review

Existing test prompts vs. natural-user rewrites. Methodology in [hitl-prompts-review.html](../../hitl-prompts-review.html) and [CLAUDE.md](../../CLAUDE.md).

## Scope of this folder

This folder is **not** a normal eval folder — it's a single classification harness (`activation.yaml`) whose `initial_prompt` is literally `${row.prompt}`, hydrated from 19 `.jsonl` corpora (one per UiPath skill, plus `negative.jsonl`). One agent run per row; 18 stacked `skill_triggered` criteria compute per-skill precision/recall/F1 from the same trace. Goal: does the right skill (and **only** the right skill) activate for a given user-style prompt? Total dataset is **951 rows** (~50 positives per skill, 50 negatives).

Because this is an **activation classifier**, the prompt corpus is *deliberately* heterogeneous: pure-goal customer asks ("I want a human to review the AI-generated RCA before it gets posted to ServiceNow"), error-paste asks ("`uip codedagent eval` errors with 'Could not find the following evaluators: exact-match'"), and "user-already-knows-the-CLI" asks ("Run `uip codedapp pack dist` on my project"). All three are valid activation signals — a customer who pastes a `uip ...` command must still route to the right skill. So insider-y phrasing here is mostly *by design*.

## Insider markers seen in this folder

- `uip <subcommand>` CLI literacy across most skill files (heaviest in `uipath-agents`, `uipath-coded-apps`, `uipath-llm-configuration-byo-connections`)
- Internal feature names: `agenthub-llm-call`, `jarvis-natural-language-query`, `AllModels` / `AnyModelWithOwnAdditions`, `rpa-legacy`, `AppTask`
- Generated/source filenames in the user voice: `agent.json`, `caseplan.json`, `bindings_v2.json`, `operate.json`, `package-descriptor.json`, `.bpmn`, `.flow`, `.xaml`
- Schema-direction vocabulary: "declare an `inout` variable in a flow"
- Verbatim error tokens: `IntSvcArgumentsError`, `invalid_client`, `Invalid dist directory`, `Folder key required`, `Error while copying content to a stream`
- One ID-shaped fixture: `task 2970`, `task 12345`, `alice@company.com`, `INV:88`, record `42a-bbb`
- A skill-name slash-command: `/uipath-feedback` (`uipath-feedback-001`) — explicitly a "user typed the slash command" activation signal

None of the truly-bad eval-harness leakage markers from the HITL review (`$vars.<id>.output`, embedded `.flow` JSON in the prompt body, "Validate the flow after building / Do NOT run flow debug", "load the X skill first") appear in this corpus. The harness contract lives in `activation.yaml` / `success_criteria`, not in the prompts themselves.

## Verdict summary

| Verdict | Count |
|---|---|
| Insider — fixable | 0 yaml |
| Insider — legitimate (CLI/refusal/antipattern coverage) | 1 yaml |
| Mixed | 0 yaml |
| Natural | 0 yaml |

There is only one yaml file (`activation.yaml`) and its `initial_prompt` is a pure template `${row.prompt}`. The substantive review target is the 951 jsonl rows it dispatches. Per-row breakdown below.

## Per-test review

### `activation.yaml` (the only yaml)

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-activation` | Insider — legitimate | `initial_prompt: "${row.prompt}"`. The yaml is a pure dispatcher; harness identity is enforced via `success_criteria.*.skill_triggered` and per-row `expected_skill`, not via wording in the prompt. | _Keep as-is — the prompt **is** the row, by construction. The yaml has no harness language to remove._ |

### Per-jsonl-file assessment (951 rows total)

Each file is a *corpus*, not a single test, so I assessed it as a whole rather than per-row. Counts are approximate flagged-row counts from a marker scan (`uip `, `agenthub-llm`, `inout`, internal feature names, generated-filename leakage); see the methodology below the table.

| File | Rows | Flagged (insider-shaped) | Predominant character | Verdict |
|---|---|---|---|---|
| `uipath-agents.jsonl` | 50 | ~11 | Mix of natural ("Build a UiPath agent that classifies incoming support tickets and posts the category to Slack") and CLI/error-paste ("`uip codedagent eval` errors with…") | **Legitimate** — agent skill must route on CLI as well as natural intent |
| `uipath-coded-apps.jsonl` | 50 | ~9 | Heavy `uip codedapp …` literacy alongside "Build and deploy my coded app end-to-end" | **Legitimate** — heavy CLI is the target customer (devs scaffolding apps) |
| `uipath-data-fabric.jsonl` | 50 | ~2 | Almost entirely natural ("List all Data Fabric entities in my tenant"); two CLI/error rows | **Legitimate** — overwhelmingly natural, two rows test error-paste routing |
| `uipath-troubleshoot.jsonl` | 50 | ~1 | Natural support-ticket voice: "Why did my job fail?", "Diagnose this publish error from Studio" | **Legitimate** — model corpus of natural prompts |
| `uipath-feedback.jsonl` | 26 | ~3 | Mostly natural ("Send feedback to UiPath"); one row is `/uipath-feedback` slash, one names `uip feedback send` | **Legitimate** — slash-command and CLI-name routing are activation signals for this skill specifically |
| `uipath-governance.jsonl` | 50 | ~2 | Almost entirely natural ("Create a new AOps governance policy for Studio"); two CLI-name rows | **Legitimate** |
| `uipath-human-in-the-loop.jsonl` | 54 | ~2 | Strongly natural — "I need a human to review the AI-generated RCA before it gets posted to ServiceNow", "Add a quick form approval after the invoice extraction node" | **Legitimate** — best natural-voice corpus in the folder |
| `uipath-llm-configuration-byo-connections.jsonl` | 45 | ~10 | Heaviest insider density. Names internal feature flags (`agenthub-llm-call`, `jarvis-natural-language-query`, `AllModels`, `AnyModelWithOwnAdditions`) | **Mixed — see note below** |
| `uipath-maestro-bpmn.jsonl` | 50 | ~4 | Mostly natural ("Add an exclusive gateway with three outgoing branches…"); 4 rows name generated artifacts (`operate.json`, `bindings_v2.json`) or raw error codes | **Legitimate** |
| `uipath-maestro-case.jsonl` | 50 | ~10 | Heavy `caseplan.json` / `bindings_v2.json` / `sdd.md` literacy, but those *are* the user-facing artifacts the skill produces | **Legitimate** — filenames are part of customer mental model here |
| `uipath-maestro-flow.jsonl` | 47 | ~18 | Pervasive `.flow` filename and `uip maestro flow …` literacy. But `.flow` is the literal customer artifact — they have a file called that. | **Legitimate** — `.flow` is customer-facing |
| `uipath-planner.jsonl` | 41 | 0 | All natural, vague "where do I start?" prompts — this is exactly the skill's job (route uncertain users) | **Legitimate / Natural** |
| `uipath-platform.jsonl` | 51 | ~6 | Mix of natural ("Log me in to UiPath Cloud") and CLI ("`uip login` against staging") | **Legitimate** — the platform/auth skill *is* the CLI |
| `uipath-review.jsonl` | 50 | ~6 | Natural review asks ("Is this solution any good?"); some rows name `agent.json` or `.flow` which are the artifacts being reviewed | **Legitimate** |
| `uipath-rpa.jsonl` | 103 | ~3 | Largely natural / realistic ("Build a UiPath XAML workflow … that opens https://… in Chrome incognito"); 3 rows test `uip rpa-legacy` routing | **Legitimate** |
| `uipath-solution.jsonl` | 50 | 0 | All natural PDD→SDD asks | **Natural** |
| `uipath-tasks.jsonl` | 34 | ~3 | Natural ("Reassign task 778 from John to Mary"); one row names `AppTask` and one names `uip tasks complete` | **Legitimate** |
| `uipath-test.jsonl` | 50 | 0 | All natural Test Manager asks | **Natural** |
| `negative.jsonl` | 50 | n/a | Mix of unrelated dev tasks (Terraform, Flask, cron) plus deliberate **adversarial near-misses** (UiPath Process Mining, UiPath AI Center, UiPath Document Understanding, UiPath Insights, Camunda BPMN, Power Automate, Automation Anywhere, Blue Prism, Node-RED) | **Legitimate** — adversarial UiPath-adjacent prompts are essential to measure cross-skill false-positive rate |

**Marker-scan methodology**: a row is "flagged" if its `prompt` contains any of `uip ` (CLI invocation), `$vars`, `agenthub-llm`, `inout`, `AllModels` / `AnyModelWithOwnAdditions`, `caseplan`, `bindings_v2`, `.flow`, `.bpmn`, `operate.json`, `package-descriptor`, `agent.json`, `codedagent`, `codedapp`, `AppTask`, `jarvis`, `IntSvcArgumentsError`, `rpa-legacy`. A flagged row is not automatically *wrong* — see the BYO-connections note below for the only real concern.

### One sub-corpus to look at: `uipath-llm-configuration-byo-connections.jsonl`

10 of 45 rows (~22%) lean on UiPath-internal feature flags that a customer would not say verbatim:

- `agenthub-llm-call` — internal feature name
- `jarvis-natural-language-query` — internal feature name (Jarvis is the AskAI codename)
- `AllModels` / `AnyModelWithOwnAdditions` — internal enum values describing how a feature accepts BYO connections

Customer voice would be: "Set up our own Bedrock connection for the assistant in AgentHub so all our agent calls go through our AWS account" rather than `Register our customer-managed Azure OpenAI for agenthub-llm-call`. If the activation eval already has natural-voice variants of these (rows 001–007 do), the insider rows mostly add CLI-syntax-recognition coverage rather than business-intent coverage — which is fine for routing, but worth checking that the natural-voice precision/recall isn't being inflated by the easier insider rows.

This is a corpus-curation suggestion, not a yaml-prompt fix. The activation harness itself (the one yaml) is sound.

## Notes for the PR description

- **The folder has only one yaml and it's a pure dispatcher**: `initial_prompt: "${row.prompt}"`. There is no harness-language leakage in the yaml itself to rewrite. The whole question collapses to whether the 951 jsonl rows look like things real users say.
- **By design, the corpus must include CLI-literate prompts** — devs paste `uip codedapp pack dist`, error messages, and filenames into agents constantly, and the activation classifier has to route those too. Most flagged rows are legitimate-by-construction.
- **One sub-corpus worth a second pass — `uipath-llm-configuration-byo-connections.jsonl`** — leans on UiPath-internal feature names (`agenthub-llm-call`, `jarvis-natural-language-query`, `AllModels`, `AnyModelWithOwnAdditions`) that no external customer would say. The natural-voice positives in the same file (rows 001–007) cover the customer intent; the insider rows risk inflating recall.yes against synthetic phrasings that real users never produce. Consider rebalancing or labeling these as "CLI/expert" subset for stratified scoring.
- **`negative.jsonl` is in good shape**: deliberate adversarial near-misses for adjacent UiPath products (Process Mining, AI Center, Document Understanding, Insights) and competitor workflow tools (Camunda, Power Automate, Automation Anywhere, Blue Prism, Node-RED) — exactly the false-positive surface this eval should be measuring.
- **Comparison with the HITL prompt review**: the HITL folder had pervasive `$vars.<id>.output`, "Validate the flow after building. Do NOT run flow debug.", and embedded `.flow` JSON — none of that lives in the activation corpus. The activation prompts are noticeably cleaner because the harness contract is entirely in `success_criteria`, not in the prompt body.
