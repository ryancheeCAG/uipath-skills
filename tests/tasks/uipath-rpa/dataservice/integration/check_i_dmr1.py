#!/usr/bin/env python3
"""I-DMR1 — DeleteMultipleEntityRecords with Guid input + Guid FailedRecords."""

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
        "DeleteMultipleEntityRecords",
        type_arg="local:CodingAgentsEvalEntity",
    )

    for forbidden in ("DynamicEntityField", "InputEntityInFieldView"):
        assert_child_absent(activity, forbidden)

    print(f"PASS: {xaml} — DeleteMultipleEntityRecords matches I-DMR1 spec")
