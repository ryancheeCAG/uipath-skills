#!/usr/bin/env python3
"""v2 Integration (relationship-join query) — Owner.Title dot-notation + cross-entity."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    _local_attr,
    assert_simple_filters_contain,
    get_activity,
    get_arg_expression,
    load,
)

FILE_ENTITY = "local:CodingAgentsEvalFileEntity"
ENTITY = "local:CodingAgentsEvalEntity"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def first_token(expr: str | None) -> str:
    m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", expr or "")
    return m.group(1) if m else ""


if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)

    query = get_activity(root, "QueryEntityRecords", type_arg=FILE_ENTITY)
    assert_simple_filters_contain(query, [("Owner.Title", "contains")])

    # Dot-notation filter requires ExpansionDepth >= 2 to materialize the
    # nested record (skill ref: data-service-filter-builder-guide.md §
    # Relationship dot-notation). Below that depth the filter silently
    # mis-matches at runtime even though validate passes.
    depth_raw = (_local_attr(query, "ExpansionDepth") or "").strip()
    depth_stripped = depth_raw[1:-1].strip() if depth_raw.startswith("[") and depth_raw.endswith("]") else depth_raw
    try:
        depth = int(depth_stripped)
    except ValueError:
        fail(f"QueryEntityRecords.ExpansionDepth must be a numeric literal >= 2 for Owner.Title; got {depth_raw!r}")
    if depth < 2:
        fail(
            f"QueryEntityRecords.ExpansionDepth must be >= 2 for one-dot relationship filter "
            f"(Owner.Title); got {depth}. At depth < 2 the filter silently mis-matches."
        )

    query_out = get_arg_expression(query, "OutputRecords")
    if not query_out:
        fail("QueryEntityRecords.OutputRecords is not bound")

    get = get_activity(root, "GetEntityRecordById", type_arg=ENTITY)
    record_id = get_arg_expression(get, "RecordId") or ""
    if first_token(record_id) != first_token(query_out):
        fail(
            f"GetEntityRecordById.RecordId must derive from {query_out!r}; "
            f"got {record_id!r}"
        )
    if not get_arg_expression(get, "OutputEntity"):
        fail("GetEntityRecordById.OutputEntity is not bound")

    print(
        f"PASS: {xaml} — relationship join wires {query_out} → GetEntityRecordById"
    )
