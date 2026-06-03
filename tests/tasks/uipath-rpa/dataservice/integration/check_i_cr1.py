#!/usr/bin/env python3
"""I-CR1 — CreateEntityRecord with all scalar field types + required/optional split."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_attr,
    assert_input_entity_anti_pattern,
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

    # Baseline attributes
    assert_attr(activity, "ScopeValue", "Tenant")
    assert_attr(activity, "IsInRecordView", "[False]")

    # Anti-pattern: must use InputEntityInFieldView, not bare InputEntity
    assert_input_entity_anti_pattern(activity)

    # RecordState: Title required + 6 optional fields
    assert_record_state_fields(
        activity,
        required=["Title"],
        optional=["Notes", "Score", "Price", "IsActive", "EventDate", "ScheduledAt"],
    )

    print(f"PASS: {xaml} — CreateEntityRecord RecordState matches I-CR1 spec")
