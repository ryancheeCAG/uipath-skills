"""Tests for the path-parameter value checker."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


CHECKER = Path(__file__).with_name("check_path_param_value.py")


def _write_flow(tmp_path: Path, detail: dict) -> Path:
    project = tmp_path / "PathParamsTest"
    project.mkdir()
    flow = project / "PathParamsTest.flow"
    flow.write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "id": "getIssue",
                        "type": "core.action.http.v2",
                        "inputs": {"detail": detail},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return flow


def _run_checker(flow: Path, expected_value: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(flow), expected_value],
        capture_output=True,
        text=True,
        check=False,
    )


def test_finds_value_in_body_parameters_url(tmp_path: Path) -> None:
    flow = _write_flow(
        tmp_path,
        {
            "bodyParameters": {
                "url": "https://your-domain.atlassian.net/rest/api/2/issue/ENGCE-00000"
            }
        },
    )

    result = _run_checker(flow, "ENGCE-00000")

    assert result.returncode == 0, result.stderr
    assert "bodyParameters.url" in result.stdout


def test_finds_value_in_native_path_parameters(tmp_path: Path) -> None:
    flow = _write_flow(tmp_path, {"pathParameters": {"issueIdOrKey": "ENGCE-00000"}})

    result = _run_checker(flow, "ENGCE-00000")

    assert result.returncode == 0, result.stderr
    assert "pathParameters" in result.stdout
