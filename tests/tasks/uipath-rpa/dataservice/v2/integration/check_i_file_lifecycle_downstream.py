#!/usr/bin/env python3
"""v2 Integration (file lifecycle) — downloaded resource is consumed downstream.

Replaces the brittle `file_contains: '.LocalPath'` substring check. The intent
of the criterion is "the agent integrated the downloaded resource into the
workflow", not "the agent typed .LocalPath verbatim". Any reference to the
bound `DownloadedFileResource` variable outside the Download activity itself
proves that consumption.
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    get_activity,
    get_arg_expression,
    load,
)

FILE_ENTITY = "local:CodingAgentsEvalFileEntity"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def first_token(expr: str | None) -> str:
    m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", expr or "")
    return m.group(1) if m else ""


if __name__ == "__main__":
    xaml_path = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml_path)

    download = get_activity(root, "DownloadFileFromRecordField", type_arg=FILE_ENTITY)
    downloaded_var_expr = get_arg_expression(download, "DownloadedFileResource")
    if not downloaded_var_expr:
        fail("DownloadFileFromRecordField.DownloadedFileResource is not bound")

    var = first_token(downloaded_var_expr)
    if not var:
        fail(
            f"DownloadFileFromRecordField.DownloadedFileResource expression "
            f"{downloaded_var_expr!r} has no leading variable name"
        )

    full_text = Path(xaml_path).read_text(encoding="utf-8")
    download_text = ET.tostring(download, encoding="unicode")
    pat = re.compile(rf"\b{re.escape(var)}\b")
    refs_total = len(pat.findall(full_text))
    refs_in_download = len(pat.findall(download_text))
    refs_outside = refs_total - refs_in_download

    if refs_outside < 1:
        fail(
            f"downloaded-resource variable {var!r} is bound on "
            f"DownloadFileFromRecordField but never referenced elsewhere in "
            f"the XAML — the agent must consume the resource downstream (log "
            f"a property, pass to another activity, store in a variable used "
            f"later, etc.)"
        )

    print(
        f"PASS: {xaml_path} — downloaded resource {var!r} referenced "
        f"{refs_outside} time(s) outside the Download activity"
    )
