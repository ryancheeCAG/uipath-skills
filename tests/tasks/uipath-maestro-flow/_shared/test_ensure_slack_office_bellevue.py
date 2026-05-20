from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).with_name("ensure_slack_office_bellevue.py")


def _load_script():
    spec = importlib.util.spec_from_file_location("ensure_slack_office_bellevue", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_extract_json_tolerates_cli_noise() -> None:
    script = _load_script()

    payload = script._extract_json(
        "Tool factory already registered for project type 'Flow', skipping.\n"
        '{"Result":"Success","Data":{"ok":true}}'
    )

    assert payload == {"Result": "Success", "Data": {"ok": True}}


def test_existing_channel_with_address_does_not_mutate() -> None:
    script = _load_script()
    calls: list[tuple[str, ...]] = []

    def fake_run(args: list[str], **_: Any) -> dict[str, Any]:
        calls.append(tuple(args))
        if args[:3] == ["or", "folders", "get"]:
            return {"Data": {"Key": "folder-key"}}
        if args[:3] == ["is", "connections", "list"]:
            return {
                "Data": [
                    {
                        "Id": "connection-id",
                        "State": "Enabled",
                        "IsDefault": "Yes",
                    }
                ]
            }
        if args[:4] == ["is", "resources", "run", "list"]:
            return {
                "Data": {
                    "items": [
                        {
                            "id": "C123",
                            "name": script.CHANNEL_NAME,
                            "purpose": {"value": script.ADDRESS},
                        }
                    ],
                    "Pagination": {"HasMore": "false"},
                }
            }
        raise AssertionError(f"unexpected call: {args}")

    result = script.ensure_office_bellevue_channel(run_uip=fake_run)

    assert result == {"connection_id": "connection-id", "channel_id": "C123"}
    assert not any(call[:4] == ("is", "resources", "run", "create") for call in calls)


def test_missing_channel_is_created_and_described() -> None:
    script = _load_script()
    calls: list[tuple[str, ...]] = []

    def fake_run(args: list[str], **_: Any) -> dict[str, Any]:
        calls.append(tuple(args))
        if args[:3] == ["or", "folders", "get"]:
            return {"Data": {"Key": "folder-key"}}
        if args[:3] == ["is", "connections", "list"]:
            return {"Data": [{"Id": "connection-id", "State": "Enabled"}]}
        if args[:4] == ["is", "resources", "run", "list"]:
            return {"Data": {"items": [], "Pagination": {"HasMore": "false"}}}
        if args[:4] == ["is", "resources", "run", "create"] and args[4] == "uipath-salesforce-slack":
            if args[5] == "conversations":
                return {"Data": {"id": "CNEW", "name": script.CHANNEL_NAME}}
            if args[5] == "set_channel_description":
                body = json.loads(args[args.index("--body") + 1])
                assert body == {"channel": "CNEW", "purpose": script.ADDRESS}
                return {"Data": {"ok": True}}
        raise AssertionError(f"unexpected call: {args}")

    result = script.ensure_office_bellevue_channel(run_uip=fake_run)

    assert result == {"connection_id": "connection-id", "channel_id": "CNEW"}
    assert any(call[5] == "conversations" for call in calls if len(call) > 5)
    assert any(call[5] == "set_channel_description" for call in calls if len(call) > 5)


def test_existing_channel_with_wrong_description_is_updated() -> None:
    script = _load_script()
    calls: list[tuple[str, ...]] = []

    def fake_run(args: list[str], **_: Any) -> dict[str, Any]:
        calls.append(tuple(args))
        if args[:3] == ["or", "folders", "get"]:
            return {"Data": {"Key": "folder-key"}}
        if args[:3] == ["is", "connections", "list"]:
            return {"Data": [{"Id": "connection-id", "State": "Enabled"}]}
        if args[:4] == ["is", "resources", "run", "list"]:
            return {
                "Data": {
                    "items": [
                        {
                            "id": "C123",
                            "name": script.CHANNEL_NAME,
                            "purpose": {"value": "old value"},
                        }
                    ],
                    "Pagination": {"HasMore": "false"},
                }
            }
        if args[:6] == [
            "is",
            "resources",
            "run",
            "create",
            "uipath-salesforce-slack",
            "set_channel_description",
        ]:
            return {"Data": {"ok": True}}
        raise AssertionError(f"unexpected call: {args}")

    result = script.ensure_office_bellevue_channel(run_uip=fake_run)

    assert result == {"connection_id": "connection-id", "channel_id": "C123"}
    assert any(call[5] == "set_channel_description" for call in calls if len(call) > 5)


def test_conversations_list_fallback_handles_curated_cache_lag() -> None:
    script = _load_script()
    calls: list[tuple[str, ...]] = []

    def fake_run(args: list[str], **_: Any) -> dict[str, Any]:
        calls.append(tuple(args))
        if args[:3] == ["or", "folders", "get"]:
            return {"Data": {"Key": "folder-key"}}
        if args[:3] == ["is", "connections", "list"]:
            return {"Data": [{"Id": "connection-id", "State": "Enabled"}]}
        if args[:4] == ["is", "resources", "run", "list"]:
            object_name = args[5]
            if object_name.startswith("curated_channels"):
                return {"Data": {"items": [], "Pagination": {"HasMore": "false"}}}
            if object_name == "conversations":
                return {
                    "Data": {
                        "items": [
                            {
                                "id": "C123",
                                "name": script.CHANNEL_NAME,
                                "purpose": {"value": script.ADDRESS},
                            }
                        ],
                        "Pagination": {"HasMore": "false"},
                    }
                }
        raise AssertionError(f"unexpected call: {args}")

    result = script.ensure_office_bellevue_channel(run_uip=fake_run)

    assert result == {"connection_id": "connection-id", "channel_id": "C123"}
    assert any(call[5] == "conversations" for call in calls if len(call) > 5)
