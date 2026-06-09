#!/usr/bin/env python3
"""v2 Integration (multi-record file lifecycle) — fields, modes, data flow."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    _local_attr,
    get_activities,
    get_activity,
    get_arg_expression,
    load,
)

FILE_ENTITY = "local:CodingAgentsEvalFileEntity"
EXPECTED_FIELDS = {"Attachment", "Report", "attachmentFile"}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def first_token(expr: str | None) -> str:
    m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", expr or "")
    return m.group(1) if m else ""


def by_field(activities: list, kind: str) -> dict[str, object]:
    """Group activities by their Field attribute. Fails on duplicates or missing fields."""
    out: dict[str, object] = {}
    for a in activities:
        f = _local_attr(a, "Field")
        if not f:
            fail(f"{kind} activity missing Field attribute")
        if f in out:
            fail(f"duplicate {kind} activity for Field={f!r}")
        out[f] = a
    return out


if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)

    # --- CreateMultiple ---
    create = get_activity(root, "CreateMultipleEntityRecords", type_arg=FILE_ENTITY)
    created_var = get_arg_expression(create, "OutputRecords")
    if not created_var:
        fail("CreateMultipleEntityRecords.OutputRecords is not bound")
    created_token = first_token(created_var)

    # --- Uploads ---
    uploads = get_activities(root, "UploadFileToRecordField", type_arg=FILE_ENTITY)
    if len(uploads) != 3:
        fail(f"expected exactly 3 UploadFileToRecordField activities, found {len(uploads)}")
    uploads_by_field = by_field(uploads, "UploadFileToRecordField")
    if set(uploads_by_field.keys()) != EXPECTED_FIELDS:
        fail(
            f"Upload fields {sorted(uploads_by_field.keys())} do not match "
            f"expected {sorted(EXPECTED_FIELDS)}"
        )

    has_file_resource_mode = False
    for fname, u in uploads_by_field.items():
        rid = get_arg_expression(u, "RecordId") or ""
        if first_token(rid) != created_token:
            fail(
                f"Upload on Field={fname!r} RecordId must derive from "
                f"{created_var!r}; got {rid!r}"
            )
        file_path = get_arg_expression(u, "FilePath")
        file_resource = get_arg_expression(u, "FileResource")
        if file_path and file_resource:
            fail(
                f"Upload on Field={fname!r} sets both FilePath and FileResource — "
                "modes are mutually exclusive"
            )
        if not file_path and not file_resource:
            fail(f"Upload on Field={fname!r} sets neither FilePath nor FileResource")
        if file_resource:
            has_file_resource_mode = True
    if not has_file_resource_mode:
        fail(
            "expected at least one UploadFileToRecordField using FileResource mode "
            "(none observed; all uploads used FilePath)"
        )

    # --- Downloads ---
    downloads = get_activities(
        root, "DownloadFileFromRecordField", type_arg=FILE_ENTITY
    )
    if len(downloads) != 3:
        fail(
            f"expected exactly 3 DownloadFileFromRecordField activities, "
            f"found {len(downloads)}"
        )
    downloads_by_field = by_field(downloads, "DownloadFileFromRecordField")
    if set(downloads_by_field.keys()) != EXPECTED_FIELDS:
        fail(
            f"Download fields {sorted(downloads_by_field.keys())} do not match "
            f"expected {sorted(EXPECTED_FIELDS)}"
        )

    resource_only_count = 0
    for fname, d in downloads_by_field.items():
        rid = get_arg_expression(d, "RecordId") or ""
        if first_token(rid) != created_token:
            fail(
                f"Download on Field={fname!r} RecordId must derive from "
                f"{created_var!r}; got {rid!r}"
            )
        if not get_arg_expression(d, "DownloadedFileResource"):
            fail(f"Download on Field={fname!r} DownloadedFileResource is not bound")
        if not get_arg_expression(d, "FilePath"):
            resource_only_count += 1
    if resource_only_count < 1:
        fail(
            "expected at least one resource-only Download (no FilePath set); "
            "all downloads specified a FilePath"
        )

    # --- DeleteFile ---
    deletes = get_activities(root, "DeleteFileFromRecordField", type_arg=FILE_ENTITY)
    if len(deletes) != 3:
        fail(
            f"expected exactly 3 DeleteFileFromRecordField activities, found {len(deletes)}"
        )
    deletes_by_field = by_field(deletes, "DeleteFileFromRecordField")
    if set(deletes_by_field.keys()) != EXPECTED_FIELDS:
        fail(
            f"DeleteFile fields {sorted(deletes_by_field.keys())} do not match "
            f"expected {sorted(EXPECTED_FIELDS)}"
        )
    for fname, df in deletes_by_field.items():
        rid = get_arg_expression(df, "RecordId") or ""
        if first_token(rid) != created_token:
            fail(
                f"DeleteFile on Field={fname!r} RecordId must derive from "
                f"{created_var!r}; got {rid!r}"
            )

    print(
        f"PASS: {xaml} — multi-record file lifecycle; "
        f"3 uploads/downloads/deletes across {sorted(EXPECTED_FIELDS)}; "
        f"FileResource mode present; resource-only download present"
    )
