"""Tests for the CountLetters low-code-agent checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path


CHECKER = Path(__file__).with_name("check_lowcode_agent_flow.py")


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_lowcode_agent_flow", CHECKER)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checker_targets_flow_project_when_solution_has_agent_sibling(monkeypatch) -> None:
    checker = _load_checker()
    calls: list[tuple] = []

    def fake_assert_flow_has_node_type(hints, *, project_glob="**/project.uiproj"):
        calls.append(("node_type", tuple(hints), project_glob))

    def fake_run_debug(*, timeout=240, project_glob="**/project.uiproj", inputs=None):
        calls.append(("debug", timeout, project_glob, inputs))
        return {"variables": {"globals": {"count": 2}}}

    def fake_assert_output_value(payload, expected):
        calls.append(("output", payload, expected))

    monkeypatch.setattr(checker, "assert_flow_has_node_type", fake_assert_flow_has_node_type)
    monkeypatch.setattr(checker, "run_debug", fake_run_debug)
    monkeypatch.setattr(checker, "assert_output_value", fake_assert_output_value)

    checker.main()

    assert calls == [
        (
            "node_type",
            ("uipath.core.agent",),
            "CountLettersLowCode/CountLettersLowCode/project.uiproj",
        ),
        ("debug", 240, "CountLettersLowCode/CountLettersLowCode/project.uiproj", None),
        ("output", {"variables": {"globals": {"count": 2}}}, 2),
    ]
