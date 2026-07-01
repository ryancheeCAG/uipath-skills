#!/usr/bin/env python3
"""Conversational custom Tool-guardrail check (conversational Critical Rule 1).

Conversational agents support ONE guardrail type: a `$guardrailType: "custom"`
deterministic rule scoped to a Tool. Built-in validators (`pii_detection`,
`harmful_content`, etc.) are autonomous-only and never run on conversational
agents. The runtime-effective location for a conversational guardrail is each
tool's `resources/<Tool>/resource.json` -> `guardrail.policies[]`; the
`agent.json` root `guardrails[]` array is only the Studio Web display mirror.

PASS requires ALL of:
  1. No `builtInValidator` guardrail anywhere (agent.json root OR any tool
     resource.json) — a built-in validator on a conversational agent is a
     silent runtime no-op.
  2. At least one tool `resource.json` whose `guardrail.policies[]` holds a
     custom word-rule guardrail that:
       - `$guardrailType` == "custom"
       - `selector.scopes` contains "Tool" and NOT "Agent"/"Llm"
       - `selector.matchNames` is non-empty
       - has a rule with `$ruleType` == "word", `operator` == "contains",
         `value` == "CONFIDENTIAL", and a `fieldSelector.$selectorType`
       - `action.$actionType` == "block"
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "DocGuardSol" / "DocGuardBot"
AGENT = ROOT / "agent.json"
RESOURCES = ROOT / "resources"

BUILTIN_VALIDATORS = {
    "pii_detection",
    "prompt_injection",
    "harmful_content",
    "intellectual_property",
    "user_prompt_attacks",
}
FORBIDDEN_SCOPES = {"Agent", "Llm"}
VALID_SELECTOR_TYPES = {"all", "specific"}


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def is_builtin(g: dict) -> bool:
    return g.get("$guardrailType") == "builtInValidator" or g.get("validatorType") in BUILTIN_VALIDATORS


def is_valid_custom_word(g: dict) -> bool:
    if g.get("$guardrailType") != "custom":
        return False
    selector = g.get("selector") or {}
    scopes = selector.get("scopes") or []
    if "Tool" not in scopes or (set(scopes) & FORBIDDEN_SCOPES):
        return False
    if not (selector.get("matchNames") or []):
        return False
    if (g.get("action") or {}).get("$actionType") != "block":
        return False
    for rule in g.get("rules") or []:
        if rule.get("$ruleType") != "word":
            continue
        if (rule.get("fieldSelector") or {}).get("$selectorType") not in VALID_SELECTOR_TYPES:
            continue
        if rule.get("operator") != "contains":
            continue
        if rule.get("value") != "CONFIDENTIAL":
            continue
        return True
    return False


def main() -> None:
    agent = load(AGENT)

    root_guardrails = [("agent.json root guardrails[]", g) for g in (agent.get("guardrails") or [])]

    tool_policy_guardrails = []  # (source_label, guardrail)
    if RESOURCES.is_dir():
        for rj in sorted(RESOURCES.glob("*/resource.json")):
            r = load(rj)
            policies = ((r.get("guardrail") or {}).get("policies")) or []
            for g in policies:
                tool_policy_guardrails.append((f"{rj.relative_to(ROOT)} guardrail.policies[]", g))

    # 1. No built-in validators anywhere.
    builtins = [(src, g) for src, g in (root_guardrails + tool_policy_guardrails) if is_builtin(g)]
    if builtins:
        lines = [
            "FAIL: built-in validator guardrail(s) found — built-in validators "
            "are autonomous-only and do NOT run on conversational agents:"
        ]
        for src, g in builtins:
            vt = g.get("validatorType") or g.get("$guardrailType")
            lines.append(f"  - in {src}: name={g.get('name', '?')!r} ({vt})")
        sys.exit("\n".join(lines))
    print("OK: no built-in validator guardrails (agent.json root + per-tool resource.json)")

    # 2. A valid custom word Tool-guardrail in a tool resource.json guardrail.policies[].
    valid = [(src, g) for src, g in tool_policy_guardrails if is_valid_custom_word(g)]
    if not valid:
        root_valid = [g for _, g in root_guardrails if is_valid_custom_word(g)]
        if root_valid and not any(is_valid_custom_word(g) for _, g in tool_policy_guardrails):
            sys.exit(
                "FAIL: the custom word guardrail is only in agent.json root "
                "guardrails[], not in any tool's resources/<Tool>/resource.json "
                "-> guardrail.policies[]. For conversational agents the per-tool "
                "policies[] location is runtime-effective; the agent.json root "
                "array is only the Studio Web display mirror, so this guardrail "
                "would not run."
            )
        sys.exit(
            "FAIL: no valid custom word-rule Tool guardrail found in any "
            "resources/<Tool>/resource.json -> guardrail.policies[]. Required: "
            '$guardrailType=="custom", selector.scopes contains "Tool" (no '
            'Agent/Llm) with matchNames, a word rule (operator "contains", '
            'value "CONFIDENTIAL"), and action.$actionType=="block".'
        )
    src, g = valid[0]
    print(f"OK: custom word Tool-guardrail in {src}")
    print(f"    scopes={g['selector']['scopes']} matchNames={g['selector'].get('matchNames')} action=block")

    print("\nAll conversational custom-guardrail checks passed (conversational Critical Rule 1).")


if __name__ == "__main__":
    main()
