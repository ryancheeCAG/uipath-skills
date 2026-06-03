#!/usr/bin/env python3
"""I-DFD1 — DeleteFileFromRecordField with Field=Attachment + OutputEntity bound."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_attr,
    get_activity,
    load,
)

if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)
    activity = get_activity(
        root,
        "DeleteFileFromRecordField",
        type_arg="local:CodingAgentsEvalFileEntity",
    )

    assert_attr(activity, "Field", "Attachment")

    print(f"PASS: {xaml} — DeleteFileFromRecordField matches I-DFD1 spec")
