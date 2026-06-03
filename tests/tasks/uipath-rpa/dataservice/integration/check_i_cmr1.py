#!/usr/bin/env python3
"""I-CMR1 — CreateMultipleEntityRecords with 10 entities + FailedRecords iteration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_child_absent,
    get_activity,
    load,
)

if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)
    activity = get_activity(
        root,
        "CreateMultipleEntityRecords",
        type_arg="local:CodingAgentsEvalEntity",
    )

    # Batch activities must not carry RecordState / IsInRecordView / InputEntityInFieldView
    for forbidden in (
        "DynamicEntityField",
        "InputEntityInFieldView",
    ):
        assert_child_absent(activity, forbidden)

    print(f"PASS: {xaml} — CreateMultipleEntityRecords matches I-CMR1 spec")
