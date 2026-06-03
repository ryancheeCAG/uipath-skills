#!/usr/bin/env python3
"""I-DF1 — DownloadFileFromRecordField with FilePath + Field=Report."""

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
        "DownloadFileFromRecordField",
        type_arg="local:CodingAgentsEvalFileEntity",
    )

    assert_attr(activity, "Field", "Report")

    print(f"PASS: {xaml} — DownloadFileFromRecordField matches I-DF1 spec")
