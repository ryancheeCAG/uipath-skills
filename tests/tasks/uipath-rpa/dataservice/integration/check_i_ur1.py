#!/usr/bin/env python3
"""I-UR1 — UpdateEntityRecord with 4 fields; Notes/Status forbidden in RecordState."""

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
        root, "UpdateEntityRecord", type_arg="local:CodingAgentsEvalEntity"
    )

    assert_attr(activity, "IsInRecordView", "[False]")
    assert_input_entity_anti_pattern(activity)

    # Update payload: exactly these 4 fields; Notes/Status must be absent.
    # Title is the schema-required field on the entity, so its DynamicEntityField
    # still carries IsRequired="True" even in a partial update.
    assert_record_state_fields(
        activity,
        required=["Title"],
        optional=["Score", "Price", "IsActive"],
        forbidden=["Notes", "Status"],
    )

    print(f"PASS: {xaml} — UpdateEntityRecord RecordState matches I-UR1 spec")
