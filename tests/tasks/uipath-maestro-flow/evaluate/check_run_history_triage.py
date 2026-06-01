#!/usr/bin/env python3
"""Validate Flow eval run history, failed-row triage, and compare outputs."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def load(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        fail(f"{path} does not exist")
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")
    if not isinstance(doc, dict):
        fail(f"{path} should contain a JSON object")
    return doc


def walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def collect_ids(value: Any) -> set[str]:
    ids: set[str] = set()
    for item in walk(value):
        if isinstance(item, str):
            ids.update(UUID_RE.findall(item))
    return ids


def data(doc: dict[str, Any]) -> Any:
    return doc.get("Data", doc)


def status_value(doc: dict[str, Any]) -> str:
    d = data(doc)
    if isinstance(d, dict):
        for key in ("Status", "status", "State", "state", "RunStatus", "runStatus"):
            if d.get(key) is not None:
                return str(d[key]).lower()
    return ""


def assert_code(path: str, expected: str) -> dict[str, Any]:
    doc = load(path)
    if doc.get("Code") != expected:
        fail(f"{path} Code should be {expected!r}, got {doc.get('Code')!r}")
    return doc


def extract_rows(doc: dict[str, Any]) -> list[dict[str, Any]]:
    d = data(doc)
    containers = [d, doc]
    for container in containers:
        if isinstance(container, dict):
            for key in ("Results", "DataPoints", "Rows"):
                rows = container.get(key)
                if isinstance(rows, list):
                    return [r for r in rows if isinstance(r, dict)]
        elif isinstance(container, list):
            return [r for r in container if isinstance(r, dict)]

    for item in walk(doc):
        if (
            isinstance(item, list)
            and item
            and all(isinstance(row, dict) for row in item)
            and any(
                "DataPoint" in row or "Score" in row or "EvaluatorScores" in row
                for row in item
            )
        ):
            return item
    return []


def main() -> None:
    start_a = assert_code("flow-run-a-start.json", "MaestroFlowEvalRunStarted")
    status_a = assert_code("flow-run-a-status.json", "MaestroFlowEvalRunStatus")
    status_b = assert_code("flow-run-b-status.json", "MaestroFlowEvalRunStatus")
    failed = assert_code("flow-only-failed-results.json", "MaestroFlowEvalRunResults")
    run_list = assert_code("flow-run-list.json", "MaestroFlowEvalRunList")
    compare = assert_code("flow-run-compare.json", "MaestroFlowEvalRunComparison")

    if status_value(status_a) not in {"completed", "failed"}:
        fail(f"run A should be terminal, got status {status_value(status_a)!r}")
    if status_value(status_b) not in {"completed", "failed"}:
        fail(f"run B should be terminal, got status {status_value(status_b)!r}")

    ids_a = collect_ids(start_a) | collect_ids(status_a)
    ids_b = collect_ids(status_b) | collect_ids(load("flow-run-b-start.json"))
    if not ids_a:
        fail("could not find run A id in start/status JSON")
    if not ids_b:
        fail("could not find run B id in start/status JSON")
    if ids_a == ids_b:
        fail(f"expected two distinct run ids, got {sorted(ids_a)}")

    failed_rows = extract_rows(failed)
    if not failed_rows:
        fail("--only-failed results returned no rows; expected bad-bob")
    failed_blob = json.dumps(failed_rows, sort_keys=True).lower()
    if "bad-bob" not in failed_blob:
        fail("failed-results JSON does not include the intentionally failing bad-bob case")
    if "good-alice" in failed_blob:
        fail("--only-failed results should not include good-alice")

    list_ids = collect_ids(run_list)
    if not (ids_a & list_ids) or not (ids_b & list_ids):
        fail("run list does not include both run ids")

    compare_ids = collect_ids(compare)
    if not (ids_a & compare_ids) or not (ids_b & compare_ids):
        fail("compare output does not include both run ids")
    compare_rows = extract_rows(compare)
    if not compare_rows:
        fail("compare output has no data-point comparison rows")

    print(
        "OK: Flow eval run lifecycle saved terminal statuses, only-failed "
        "triage for bad-bob, run list entries, and compare rows"
    )


if __name__ == "__main__":
    main()
