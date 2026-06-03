#!/usr/bin/env python3
"""I-UMR1 — two UpdateMultipleEntityRecords activities (retry pattern)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_child_absent,
    get_activities,
    load,
)

ENTITY_TYPE = "local:CodingAgentsEvalEntity"

if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)
    activities = get_activities(
        root, "UpdateMultipleEntityRecords", type_arg=ENTITY_TYPE
    )

    if len(activities) != 2:
        print(
            f"FAIL: expected 2 UpdateMultipleEntityRecords on {ENTITY_TYPE}, got {len(activities)}",
            file=sys.stderr,
        )
        sys.exit(1)

    for activity in activities:
        for forbidden in ("DynamicEntityField", "InputEntityInFieldView"):
            assert_child_absent(activity, forbidden)

    print(f"PASS: {xaml} — UpdateMultipleEntityRecords retry pattern matches I-UMR1 spec")
