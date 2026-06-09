#!/usr/bin/env python3
"""v2 Smoke (CreateEntityRecord) — single activity, Title-only happy path."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_record_state_fields,
    get_activity,
    load,
)

if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)
    activity = get_activity(
        root, "CreateEntityRecord", type_arg="local:CodingAgentsEvalEntity"
    )

    assert_record_state_fields(
        activity,
        required=["Title"],
        optional=[],
        forbidden=["Notes", "Status", "Score", "Price", "IsActive", "EventDate", "ScheduledAt", "Category", "Tags"],
    )

    print(f"PASS: {xaml} — CreateEntityRecord matches v2 smoke spec")
