from __future__ import annotations

from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]


def test_slack_tasks_prepare_shared_office_bellevue_fixture() -> None:
    for rel in [
        "slack_channel_description/slack_channel_description.yaml",
        "slack_weather_pipeline/slack_weather_pipeline.yaml",
    ]:
        text = (TASK_ROOT / rel).read_text()

        assert "../../_shared/ensure_slack_office_bellevue.py" in text
        assert '--output json' in text
        assert "-o json" not in text
        assert "Do not substitute #office or any other Slack channel" in text
