#!/usr/bin/env python3
"""v2 Integration (single-record CRUD lifecycle) — composition + data-flow.

Asserts: 5 entity-record activities present, RecordState shapes on Create +
Update, ContinueOnError on Create/Update/Delete, ExpansionDepth=[1] on the
first GetById, and RecordId on every downstream step references the same
upstream OutputEntity variable.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_activity_order,
    assert_arg_references,
    assert_attr,
    assert_child_absent,
    assert_record_state_fields,
    get_activities,
    get_activity,
    get_arg_expression,
    load,
    parent_map,
    under,
)

ENTITY = "local:CodingAgentsEvalEntity"


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
            "GetEntityRecordById",
            "UpdateEntityRecord",
            "GetEntityRecordById",
            "DeleteEntityRecord",
        ],
    )

    # --- Create ---
    create = get_activity(root, "CreateEntityRecord", type_arg=ENTITY)
    assert_record_state_fields(
        create,
        required=["Title"],
        optional=["Notes", "Score", "Price", "IsActive", "EventDate", "ScheduledAt"],
        forbidden=["Category", "Tags"],
    )
    assert_attr(create, "ContinueOnError", "[True]")
    created_var = get_arg_expression(create, "OutputEntity")
    if not created_var:
        fail("CreateEntityRecord.OutputEntity is not bound to a variable")

    # --- GetById activities (expect 2 in document order) ---
    gets = get_activities(root, "GetEntityRecordById", type_arg=ENTITY)
    if len(gets) != 2:
        fail(f"expected exactly 2 GetEntityRecordById activities, found {len(gets)}")
    get1, get2 = gets

    # First Get: ExpansionDepth=[1], OutputEntity bound, no write-mode bleed
    assert_attr(get1, "ExpansionDepth", "[1]")
    for forbidden in ("DynamicEntityField", "InputEntityInFieldView"):
        assert_child_absent(get1, forbidden)
    if not get_arg_expression(get1, "OutputEntity"):
        fail("first GetEntityRecordById.OutputEntity is not bound")
    assert_arg_references(get1, "RecordId", created_var, ".Id")

    # Second Get: OutputEntity bound to a different variable, RecordId chained
    if not get_arg_expression(get2, "OutputEntity"):
        fail("second GetEntityRecordById.OutputEntity is not bound")
    assert_arg_references(get2, "RecordId", created_var, ".Id")

    # --- Update ---
    update = get_activity(root, "UpdateEntityRecord", type_arg=ENTITY)
    assert_record_state_fields(
        update,
        required=["Title"],
        optional=["Score", "Price", "IsActive"],
        forbidden=["Notes", "EventDate", "ScheduledAt", "Category", "Tags"],
    )
    assert_attr(update, "ContinueOnError", "[True]")
    assert_arg_references(update, "RecordId", created_var, ".Id")

    # --- Delete ---
    delete = get_activity(root, "DeleteEntityRecord", type_arg=ENTITY)
    for forbidden in ("DynamicEntityField", "InputEntityInFieldView"):
        assert_child_absent(delete, forbidden)
    assert_attr(delete, "ContinueOnError", "[True]")
    assert_arg_references(delete, "RecordId", created_var, ".Id")

    # --- Null guard: post-Create activities live under an If or FlowDecision ---
    parents = parent_map(root)
    guarded = [get1, update, get2, delete]
    if not all(
        under(a, parents, "If") or under(a, parents, "FlowDecision") for a in guarded
    ):
        fail(
            "post-Create activities (Get/Update/Get/Delete) must all live under an "
            "If or FlowDecision ancestor (null guard on createdRecord)"
        )

    print(
        f"PASS: {xaml} — lifecycle composition shapes correctly; "
        f"RecordId chains from {created_var!r}; null guard present"
    )
