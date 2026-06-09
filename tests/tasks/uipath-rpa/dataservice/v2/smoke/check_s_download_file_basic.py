#!/usr/bin/env python3
"""v2 Smoke (DownloadFileFromRecordField) — file read activity, no bleed."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_attr,
    assert_child_absent,
    get_activity,
    get_arg_expression,
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

    assert_attr(activity, "Field", "Attachment")

    for forbidden in (
        "DynamicEntityField",
        "InputEntityInFieldView",
    ):
        assert_child_absent(activity, forbidden)

    record_id_expr = get_arg_expression(activity, "RecordId")
    if not record_id_expr:
        print(
            "FAIL: DownloadFileFromRecordField.RecordId is not bound",
            file=sys.stderr,
        )
        sys.exit(1)

    resource_expr = get_arg_expression(activity, "DownloadedFileResource")
    if not resource_expr:
        print(
            "FAIL: DownloadFileFromRecordField.DownloadedFileResource is not bound to a variable",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"PASS: {xaml} — DownloadFileFromRecordField matches v2 smoke spec")
