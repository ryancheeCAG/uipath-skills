# Hybrid Deterministic Decision-Tree — Approach & Pilot (the "fourth approach")

Goal: replace LLM *turns* on the determinizable spine with a deterministic tree executor; fall back to the LLM exactly where evidence can't decide. Grounded, evidence-based, consistent resolution preserved.

## The hybrid (user's framing)
- A **deterministic executor** walks `dispatch → gather → branch → leaf`: run a command, read a field from the response, follow the branch, emit cause+fix. Zero LLM on covered paths → no run-to-run variance (the failure of the exception-table attempt: same case fast-pathed 47 turns one run, 143 the next).
- At any node it **can't resolve from evidence** (no branch matches, opaque signature, missing field, low-confidence leaf), it hands to the **LLM**, which either (a) **continues down the path** — picks the child branch from the evidence — or (b) **jumps to another node/leaf** to continue the investigation. Then control can return to the deterministic walk.
- Identity resolution (which folder/job — needs the prompt or a user question) is itself a hybrid/LLM step; the deterministic tree takes over once the entity + core evidence are gathered.

## Data model (per the architecture analysis)
- `gather` node: `cmd` (templated with bound vars), `bind` (extract fields: jsonpath-lite or regex over gathered text), `next`.
- `branch` node: `on` (a bound var), `cases` (`when` predicate → `goto`), `default` (→ `goto`, often an llm node).
- `leaf` node: `cause`, `fix`, `confidence`, `playbook` (resolution_ref — never inlined, to avoid drift).
- `llm` node: hand to the LLM loop with the partial trace + bound context; mode `continue` (pick child) or `jump` (re-enter elsewhere).
- Cross-system: a leaf on a `fast_path:no` symptom (stuck parent / incident) is **forbidden as terminal** — it carries a mandatory `goto` into the child gather, carrying the bound child key. Collect ALL leaves on the path (root cause + propagation), matching multi-domain RESOLUTION.md.

## Build → Verify → Run
- **Build:** dispatch root from `exception-table.md`; gather/branch/leaf skeletons from playbook `## Investigation`/`## Resolution`; LLM fills predicates/binds **constrained to fields present in the matching test fixtures**; deterministic compile + lint (no terminal symptom leaf; every cmd a known verb; every playbook ref resolves).
- **Verify:** replay every test through the **zero-LLM executor** against its `manifest.json` oracle; assert it reaches that test's expected leaf. This is a deterministic regression gate (no LLM noise) + drift detection.
- **Run:** triage resolves identity + gathers core bundle → executor walks the deterministic spine → LLM fallback on any unresolved node (seeded with the trace) → presenter renders the leaf set.

## VALIDATED (pilot, zero-LLM executor against real test fixtures)

- **Single-domain deterministic leaf:** `connector-general-disabled` → folder→job→get→logs→`DAP-GE-3005`→branch→`leaf_disabled` (correct cause+fix+playbook = RESOLUTION), **0 LLM calls**, ~6 steps. Same fixtures → same leaf every run (kills the exception-table attempt's 47↔143-turn variance).
- **Hybrid fallback boundary:** `connector-null-reference` (opaque NRE, no DAP code) → deterministic gather then **bind-miss → `llm_signature` (jump)** — hands to the LLM exactly where evidence can't decide.
- **Cross-system traversal (the killer case):** `maestro-stuck-rpa-job` → parent `ProcessOrchestration`/`Running` (symptom, not terminal) → `maestro incidents` (job_key==instance_key) → `errorCode 170002` (symptom, not terminal) → dispatch on child exception FQN `UiPath.UIAutomationNext...NodeNotFoundException` → `leaf_uia_selector` (root cause in the CHILD, not the stuck parent). **0 LLM calls** on the spine; ~10 steps. This is the case that broke the dedicated-agent approach (wrong "parent cancelled") and took the baseline 194 LLM turns. "Symptom forbidden as terminal" is the structural encoding of symptom≠cause.

Matching rule confirmed: branches are on **structured tokens only** (codes, enums, exception FQN); message-text / sub-cause / perceptual judgments are `llm` nodes (e.g. the exact selector correction). The executor is deterministic *control flow* with the LLM as a *narrow classifier* at perception nodes — not regex-everything.

## Coverage boundary
Deterministic: exact code/HRESULT/exception-FQN signatures with field-evaluable branches + multi-system traversals with explicit child keys. LLM-driven: opaque/wrapper signatures, perceptual/judgment causes, novelty, ambiguous-evidence → ask-user.

## PILOT (this dir)
- `is-tree.json` — minimal Integration Service tree: resolve folder/job → gather job+logs → branch on the DAP error code → leaf (or llm node).
- `tree_executor.py` — the zero-LLM executor + replay harness: walks the tree against a test's `fixtures/mocks/responses/manifest.json`, prints the reached leaf + trace.
- Validate on `connector-general-disabled` (DAP-GE-3005 → "connection disabled" leaf), deterministically, zero LLM. Then extend to the maestro traversal as the cross-system proof.
