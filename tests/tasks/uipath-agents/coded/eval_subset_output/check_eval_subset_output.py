#!/usr/bin/env python3
"""Validate a targeted `uip codedagent eval --eval-ids` run."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("subset-eval")


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")
    if not isinstance(value, dict):
        fail(f"{path} should contain a JSON object")
    return value


def result_case_id(case: dict) -> str:
    for key in ("evaluationId", "evaluationName", "id", "testId", "testName", "name"):
        value = case.get(key)
        if value:
            return str(value)
    return json.dumps(case, sort_keys=True)


def main() -> None:
    if not ROOT.is_dir():
        fail(f"project directory {ROOT} does not exist")

    eval_sets = sorted((ROOT / "evaluations" / "eval-sets").glob("*.json"))
    if not eval_sets:
        fail("no eval-set JSON found")
    eval_set = load(eval_sets[0])
    cases = eval_set.get("evaluations") or []
    ids = {c.get("id") for c in cases if isinstance(c, dict)}
    expected_ids = {"case-selected", "case-skipped-a", "case-skipped-b"}
    if ids != expected_ids:
        fail(f"eval-set case ids should be {sorted(expected_ids)}, got {sorted(ids)}")

    result_path = ROOT / "selected-results.json"
    if not result_path.is_file():
        result_path = Path("selected-results.json")
    if not result_path.is_file():
        fail("selected-results.json was not written")
    results = load(result_path)
    rows = results.get("evaluationSetResults")
    if not isinstance(rows, list) or not rows:
        fail(f"selected-results.json has no evaluationSetResults. Keys: {list(results)}")
    names = [result_case_id(row) for row in rows if isinstance(row, dict)]
    if len(rows) != 1:
        fail(f"expected exactly one selected result row, got {len(rows)} rows: {names}")
    if "selected" not in names[0].lower():
        fail(f"the only result row should be case-selected, got {names[0]!r}")

    runs = rows[0].get("evaluationRunResults") or []
    if not runs:
        fail("selected result row has no evaluationRunResults")
    bad_scores = []
    for run in runs:
        score = (run.get("result") or {}).get("score") if isinstance(run, dict) else None
        if score != 1.0:
            bad_scores.append(score)
    if bad_scores:
        fail(f"selected case should score 1.0, got bad scores {bad_scores!r}")
    print("OK: eval set has three cases, --eval-ids run saved only case-selected with score 1.0")


if __name__ == "__main__":
    main()
