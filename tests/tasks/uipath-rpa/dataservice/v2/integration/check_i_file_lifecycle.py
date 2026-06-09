#!/usr/bin/env python3
"""v2 Integration (file lifecycle) — 6 activities on FileEntity with createdRecord.Id chain."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_activity_order,
    assert_arg_references,
    assert_attr,
    assert_attr_bool,
    assert_record_state_fields,
    get_activity,
    get_arg_expression,
    load,
)

FILE_ENTITY = "local:CodingAgentsEvalFileEntity"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)

    # --- Activity order in document order ---
    assert_activity_order(
        root,
        [
            "CreateEntityRecord",
            "UploadFileToRecordField",
            "UpdateEntityRecord",
            "GetEntityRecordById",
            "DownloadFileFromRecordField",
            "DeleteFileFromRecordField",
        ],
    )

    # --- Create ---
    create = get_activity(root, "CreateEntityRecord", type_arg=FILE_ENTITY)
    assert_record_state_fields(
        create,
        required=["Title"],
        optional=[],
        forbidden=["Attachment", "Report", "Contract", "attachmentFile"],
    )
    created_var = get_arg_expression(create, "OutputEntity")
    if not created_var:
        fail("CreateEntityRecord.OutputEntity is not bound")

    # --- Upload ---
    upload = get_activity(root, "UploadFileToRecordField", type_arg=FILE_ENTITY)
    assert_attr(upload, "Field", "Contract")
    assert_arg_references(upload, "RecordId", created_var, ".Id")
    if not get_arg_expression(upload, "FilePath"):
        fail("UploadFileToRecordField.FilePath is not bound (FilePath mode expected)")

    # --- Update (partial Title-only) ---
    update = get_activity(root, "UpdateEntityRecord", type_arg=FILE_ENTITY)
    assert_record_state_fields(
        update,
        required=["Title"],
        optional=[],
        forbidden=["Attachment", "Report", "Contract", "attachmentFile"],
    )
    assert_arg_references(update, "RecordId", created_var, ".Id")

    # --- Get ---
    get = get_activity(root, "GetEntityRecordById", type_arg=FILE_ENTITY)
    assert_arg_references(get, "RecordId", created_var, ".Id")
    if not get_arg_expression(get, "OutputEntity"):
        fail("GetEntityRecordById.OutputEntity is not bound")

    # --- Download ---
    download = get_activity(root, "DownloadFileFromRecordField", type_arg=FILE_ENTITY)
    assert_attr(download, "Field", "Contract")
    assert_arg_references(download, "RecordId", created_var, ".Id")
    if not get_arg_expression(download, "FilePath"):
        fail("DownloadFileFromRecordField.FilePath is not bound (explicit save path expected)")
    downloaded_var = get_arg_expression(download, "DownloadedFileResource")
    if not downloaded_var:
        fail("DownloadFileFromRecordField.DownloadedFileResource is not bound")

    # --- DeleteFile ---
    delete_file = get_activity(root, "DeleteFileFromRecordField", type_arg=FILE_ENTITY)
    assert_attr(delete_file, "Field", "Contract")
    assert_attr_bool(delete_file, "ContinueOnError", True)
    assert_arg_references(delete_file, "RecordId", created_var, ".Id")
    if not get_arg_expression(delete_file, "OutputEntity"):
        fail("DeleteFileFromRecordField.OutputEntity is not bound")

    print(
        f"PASS: {xaml} — file lifecycle composition; "
        f"RecordId chains from {created_var!r}; downloaded resource: {downloaded_var!r}"
    )
