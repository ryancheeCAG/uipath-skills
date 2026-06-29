# Decision Tree: Build-from-Playbooks + LLM-Driven Walk

Decision (user): build per-domain trees FROM the playbooks; at runtime the **LLM walks** the tree — deterministic where a branch is exact, **investigates to choose the child** where it isn't. Grounded, evidence-based, consistent resolution.

## Runtime model — LLM-driven walk

The agent loads the in-scope domain tree + the evidence gathered so far, and walks node by node:

- **gather node** — run the node's `cmd` (skip if already gathered); record the evidence; extract the node's `reads` fields into the evidence context.
- **branch node** — read the `on` discriminator from evidence, consider the `children`:
  - If a child's condition is `evaluator: exact` and matches the observed structured token (code/enum/FQN/count/exists) → **take it deterministically** (no judgment).
  - If conditions are `evaluator: judgment` (fuzzy message, sub-cause, semantic) → the **LLM picks** the child whose condition the evidence best supports, **citing the evidence**.
  - If no child fits / evidence is insufficient → the LLM **investigates**: run the candidate children's `cmd`s (or the node's `gather_more` hints) to get the data that discriminates, then re-decide. If still unresolved → it may **jump** to another node/leaf, or fall to the free-form hypothesis loop (seeded with the trace).
- **leaf node** — emit `cause` + the fix from `resolution_ref` (a pointer into the playbook `## Resolution` — never inlined, so it can't drift). Confidence from the playbook frontmatter.
- **symptom node** (`symptom: true`) — a stuck/cancelled parent or a wrapper/incident. **Forbidden as terminal**: it MUST carry a `goto` (or children) into the child/sub-execution. Encodes symptom≠cause structurally.

Constraints that keep it grounded/consistent: the LLM moves only among the tree's defined children (or an explicit jump), every move cites evidence, and fixes come from `resolution_ref`. Variance is bounded because each node poses ONE narrow question, not open-ended planning.

## Node schema

```json
{
  "id": "string",
  "kind": "gather | branch | leaf | symptom",
  "cmd": "templated uip command (gather/symptom)",
  "reads": { "var": { "path|regex": "..." } },
  "on": "var (branch/symptom)",
  "children": [
    { "when": { "field": "var", "op": "eq|matches|exists|gt|lt|contains", "value": "..." },
      "evaluator": "exact | judgment",
      "judgment_q": "the question the LLM answers when evaluator=judgment",
      "goto": "node_id" }
  ],
  "default": "node_id (often an llm/jump or another tree)",
  "cause": "leaf only",
  "resolution_ref": "playbook#section (leaf only)",
  "confidence": "high|medium|low (leaf)",
  "symptom": true,
  "routes_to": "domain-tree entry (cross-system jump, carries the bound child key)"
}
```

`evaluator: exact` = deterministic branch (the walk doesn't need the LLM to choose). `evaluator: judgment` = the LLM chooses, with `judgment_q` as the bounded prompt. A playbook is "deterministic" iff all its branches are `exact`; hybrids mix.

## Builder — playbook → tree

Per playbook (one domain at a time):
1. **Harvest (script):** parse `## Investigation` numbered steps → `gather` nodes (commands); `## Context` "what can cause it" + signatures → `branch` discriminators + candidate children; `## Resolution` `**If X:**` bullets → `leaf` nodes with `resolution_ref`; frontmatter `confidence`.
2. **LLM-fill (subagent), constrained by the test fixtures:** map each prose branch to a `when` predicate + `evaluator` tag, and each `reads` var to a real field path — **only fields that appear in the matching test's fixtures** (no hallucinated paths). Exact tokens (codes/enums/FQN) → `evaluator: exact`; fuzzy/message/semantic → `evaluator: judgment` + `judgment_q`.
3. **Compile/lint (script):** resolve `goto`/`routes_to`; dedup shared prefixes into a DAG; lint — no terminal `symptom` node, every `cmd` a known uip verb, every `resolution_ref` resolves, every `evaluator:exact` predicate references a fixture-present field.
4. **Verify:** the LLM-walk (or the deterministic executor for the all-exact subset) reaches the test's expected leaf.

Dispatch root from `exception-table.md` (signature→domain); per-domain subtrees from that domain's playbooks; assemble + lazy-load.

## IS DOMAIN — built from playbooks (generated/)

The builder was fanned over the Integration Service domain (one subagent per playbook, each constrained by a matching test's fixtures, writing to `generated/<playbook>.tree.json`). Result — **6 of 9 IS playbooks → subtrees**, all valid JSON, plus `generated/is-dispatch.json` (the dispatch root routing signature→subtree):

| Subtree | nodes | class | exact / judgment |
|---|---|---|---|
| connector-runtime-exception (DAP-RT) | 16 | hybrid | 6 / 2 |
| connector-general-exception (DAP-GE) | 15 | hybrid | 3 / 3 |
| connector-aggregate-exception (wrapper→unwrap) | 12 | hybrid | 6 / 2 |
| connector-remote-exception (IPC→unwrap) | 15 | hybrid | 3 / 5 |
| connector-null-reference (opaque NRE) | 13 | hybrid | 2 / 4 |
| connection-invalid (message→structured checks) | 18 | hybrid | 4 / 5 |

Uncovered (no dedicated test fixture → LLM-loop fallback via the dispatch default): `connection-auth-expired`, `operation-failed` (reached via the DAP-RT-1101 leaf cross-ref), `trigger-not-firing`.

Observations: every clean error-code playbook compiled to a deterministic spine + a few judgment leaves; wrappers (Aggregate/Remote) → deterministic unwrap + FQN-redispatch; opaque NRE → honest exact-entry + judgment causes. No false determinism. The builder grounds every `reads` path in real fixture fields.

Also built earlier: `generated/read-range-null-reference.tree.json` (Excel, judgment-dominated) — the opaque-spectrum example.

## Status
Pilot proved the WALK (executor, hand-authored trees) AND the BUILDER (playbook→tree, fan-out over the full IS domain). This doc holds the schema + LLM-walk contract. **Next:** (1) the LLM-walk runtime wired into the skill (load dispatch+subtree → walk → investigate/judge at judgment nodes → loop-fallback at llm nodes); (2) the replay gate — annotate each IS test with `expected_leaf` and replay the all-`exact` paths through the executor (deterministic, noise-free regression). Uncovered playbooks + other domains extend by adding subtrees + dispatch rows.
