#!/usr/bin/env python3
"""v2 Smoke (UpdateEntityRecord) — partial Title-only update happy path."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_record_state_fields,
    get_activity,
    get_arg_expression,
    load,
)

if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)
    activity = get_activity(
        root, "UpdateEntityRecord", type_arg="local:CodingAgentsEvalEntity"
    )

    assert_record_state_fields(
        activity,
        required=["Title"],
        optional=[],
        forbidden=["Notes", "Status", "Score", "Price", "IsActive", "EventDate", "ScheduledAt", "Category", "Tags"],
    )

    record_id_expr = get_arg_expression(activity, "RecordId")
    if not record_id_expr:
        print(
            "FAIL: UpdateEntityRecord.RecordId is not bound",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"PASS: {xaml} — UpdateEntityRecord matches v2 smoke spec")
