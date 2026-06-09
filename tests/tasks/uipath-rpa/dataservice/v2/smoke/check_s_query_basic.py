#!/usr/bin/env python3
"""v2 Smoke (QueryEntityRecords) — read-only activity, no write-mode bleed."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_child_absent,
    get_activity,
    get_arg_expression,
    load,
)

if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)
    activity = get_activity(
        root, "QueryEntityRecords", type_arg="local:CodingAgentsEvalEntity"
    )

    for forbidden in (
        "DynamicEntityField",
        "InputEntityInFieldView",
    ):
        assert_child_absent(activity, forbidden)

    expr = get_arg_expression(activity, "OutputRecords")
    if not expr:
        print(
            "FAIL: QueryEntityRecords.OutputRecords is not bound to a variable",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"PASS: {xaml} — QueryEntityRecords matches v2 smoke spec")
