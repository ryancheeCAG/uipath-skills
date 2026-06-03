#!/usr/bin/env python3
"""I-UF1 — UploadFileToRecordField with FilePath mode + camelCase attachmentFile."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_attr,
    assert_attr_absent,
    get_activity,
    load,
)

if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)
    activity = get_activity(
        root,
        "UploadFileToRecordField",
        type_arg="local:CodingAgentsEvalFileEntity",
    )

    # Field name is case-sensitive: must be `attachmentFile`, not `AttachmentFile`
    assert_attr(activity, "Field", "attachmentFile")

    # FilePath and FileResource are mutually exclusive; we use FilePath
    assert_attr_absent(activity, "FileResource")

    print(f"PASS: {xaml} — UploadFileToRecordField matches I-UF1 spec")
