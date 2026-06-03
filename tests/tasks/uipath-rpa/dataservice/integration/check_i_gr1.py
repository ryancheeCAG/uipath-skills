#!/usr/bin/env python3
"""I-GR1 — GetEntityRecordById with ExpansionDepth=[1], no write-mode bleed."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_attr,
    assert_child_absent,
    get_activity,
    load,
)

if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)
    activity = get_activity(
        root, "GetEntityRecordById", type_arg="local:CodingAgentsEvalEntity"
    )

    assert_attr(activity, "ExpansionDepth", "[1]")

    # No write-mode property bleed
    for forbidden in (
        "DynamicEntityField",
        "InputEntityInFieldView",
    ):
        assert_child_absent(activity, forbidden)

    print(f"PASS: {xaml} — GetEntityRecordById matches I-GR1 spec")
