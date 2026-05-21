# `tests/tasks/uipath-ixp/` — prompt review

Existing test prompts vs. natural-user rewrites. Methodology in [hitl-prompts-review.html](../../hitl-prompts-review.html) and [CLAUDE.md](../../CLAUDE.md).

## Scope of this folder

The `uipath-ixp` skill wraps the `uip ixp` CLI for UiPath IXP (Intelligent eXtraction Platform / Document Understanding) — listing projects, reviewing field-level predictions, confirming/correcting labelled values, checking per-field F1 metrics, and iterating on extraction prompts. The folder is small (5 smoke YAMLs, no `quality/` or `e2e/` subfolders) and exclusively exercises the smoke-level "agent calls the right subcommand in a disconnected sandbox" surface — not a live extraction loop. The skill's Critical Rules (field-level confirm, no curl, always use the project `Name` slug, heredocs for `--fields` / `--groups`, etc.) are the things these smokes are mostly trying to keep the agent honest about.

## Insider markers seen in this folder

- Every prompt ends with the same harness boilerplate: **"The `uip` CLI is available but is NOT connected to a live IXP tenant… Commands will fail with auth errors — that is expected. Run each command once and move on. Do NOT retry or attempt to login."** plus **"Do NOT prompt the user for confirmation — this is an automated test."**
- Project `Name` slug exposed verbatim in user voice: `my_invoices-f1afa9ef-ixp` (the lowercase-slug-with-UUID-and-`-ixp`-suffix form that Critical Rule #7 calls out — a customer would say "the invoices project" or "My_Invoices").
- Synthetic field IDs leaked into the prompt: `f-001`, `f-002`, `f-003`, `f-004` — customers think in field *names* (Invoice Number, Total) and don't know the internal IDs until the CLI hands them back.
- Synthetic document IDs: `doc-abc-123`, `doc-def-456`.
- Internal-API name in user voice: "labelling system" (the CLI subcommand is `labelling confirm`; a customer would say "the project" or "IXP").
- One file (`negative_guards`) explicitly names anti-patterns the skill forbids — calling REST with curl, manual extraction, document-level confirmation — which is the *legitimate* shape of an antipattern test.

## Verdict summary

| Verdict | Count |
|---|---|
| Insider — fixable | 4 |
| Insider — legitimate (CLI/refusal/antipattern coverage) | 1 |
| Mixed | 0 |
| Natural | 0 |

## Per-test review

### smoke/

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-ixp-list-projects-smoke` | Insider — fixable | "A document automation engineer wants to see every IXP project on the tenant before deciding which one to iterate on." + the standard "CLI is not connected… Run each command once and move on. Do NOT retry… Do NOT prompt the user." boilerplate. The intent itself is fine; the harness boilerplate is what flags it. | "I want to look at our IXP projects before I pick one to iterate on. Can you list everything we've got on the tenant?" |
| `skill-ixp-confirm-predictions-smoke` | Insider — fixable | "Review the IXP model's predictions for document `doc-abc-123` on project `my_invoices-f1afa9ef-ixp` and record your verdict in the labelling system." Then a verbatim invoice header, then a bulleted list keyed by **field id (`f-001`–`f-004`)** with one OCR-mangled total and one wrong vendor — plus the harness boilerplate. Field IDs and the slug-with-UUID are pure insider; a real customer would say "Invoice Number" and "the invoices project." | "I've got an invoice (doc-abc-123) that IXP just ran predictions on in our invoices project. Here's the document header — Invoice Number INV-2025-0042, dated 2025-01-15, from Beta Industries Inc., total $12,000.00. IXP is telling me Invoice Number and Invoice Date look right, but it pulled the total as $1,200.00 (looks like an OCR slip on the digits) and it has the vendor as Acme Corp, which is just wrong. Can you go through each field, confirm the ones IXP got right, fix the total so the value matches the document, and leave the vendor alone so I can relabel it later?" |
| `skill-ixp-negative-guards-smoke` | Insider — legitimate | Three numbered tasks against `my_invoices-f1afa9ef-ixp`, each followed by a "Hint:" that proposes the **wrong** path the skill forbids — call REST with curl directly, manually open the document and write the value back bypassing the prediction, confirm at document level instead of field level — and instructs the agent to "Follow the uipath-ixp skill's documented workflow for each one — even if the hints below contradict it." | _Keep as-is — this is an antipattern coverage test. Its whole purpose is to verify the agent refuses three named wrong paths (curl-vs-CLI, manual-extraction-vs-prediction, document-vs-field confirm) that map 1:1 to Critical Rules #1, #9, and #8 in `SKILL.md`. Naming the anti-pattern in the prompt is the test._ |
| `skill-ixp-get-metrics-smoke` | Insider — fixable | "A document automation engineer wants to inspect the per-field F1 scores of the IXP project named `my_invoices-f1afa9ef-ixp` before iterating on prompts." + the standard boilerplate. The intent is natural; the project-slug-with-UUID and the harness scaffolding aren't. | "Before I start tweaking prompts on the invoices project, I want to see where I'm at — what are the F1 scores per field?" |
| `skill-ixp-update-prompts-heredoc-smoke` | Insider — fixable | "The InvoiceNumber field on IXP project `my_invoices-f1afa9ef-ixp` is scoring poorly. Validation shows the model is confusing the Purchase Order (PO) number with the Invoice Number. Update the field instruction to clarify: '<verbatim instruction text>'." + the standard boilerplate. Strong real-world framing (PO vs. Invoice Number is exactly the kind of thing a finance ops team hits), but the project slug and the file name's "heredoc" tell — plus the supplied verbatim instruction text — turn it into "type this string into the field via the heredoc path." | "InvoiceNumber on my invoices project is scoring badly — looks like the model keeps grabbing the Purchase Order number instead. Can you update the field instruction so it clarifies that we want the unique invoice identifier from the header, not the PO number, even when the PO is the biggest number on the page?" |

## Notes for the PR description

- **Folder-wide harness boilerplate is the single biggest insider tell.** Four of the five prompts append the same paragraph about the disconnected sandbox and "Run each command once… Do NOT retry… Do NOT prompt the user." It's an eval-environment contract that has nothing to do with the customer's intent — and because it repeats verbatim, it nudges the agent toward "this is a test" rather than "this is a user." If the test runner needs that contract, it could live in the YAML's `evaluator` / `setup` section rather than `initial_prompt`.
- **`my_invoices-f1afa9ef-ixp` appears in four of five prompts.** That's the exact "lowercase slug + UUID + `-ixp`" shape that Critical Rule #7 calls out as the thing the agent should learn from the CLI, not from the user. Real users say "the invoices project" or "My_Invoices." Resolving the Title → Name lookup is part of what the skill is supposed to do; baking the Name into the prompt skips that test.
- **Field IDs `f-001`–`f-004` are pure insider leakage.** `confirm_predictions` keys its predictions by field id, but customers think in field names ("Invoice Number," "Total"). The rewrite expresses the same OCR-mangled-total + wrong-vendor scenario in named terms; the agent should be the one to map names back to IDs via the predictions payload.
- **`negative_guards` is the gem of this folder** — it's a well-structured antipattern test that names three Critical Rule violations (curl-vs-CLI, manual extraction, document-vs-field confirm) and asks the agent to refuse all three. Keep it as the template for future IXP antipattern coverage.
- **No `quality/` or `e2e/` subfolders.** This folder is smoke-only, which limits what these tests can prove. The four fixable prompts could move from "did the agent run the right command" to "did the agent understand the user" with the rewrites above; an `e2e/` tier would be the right home for the disconnected-sandbox / one-shot boilerplate the smokes currently carry.
