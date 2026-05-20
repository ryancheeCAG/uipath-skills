#!/usr/bin/env python3
"""Ensure the Slack #office-bellevue fixture exists for Flow e2e tasks."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any, Callable


FOLDER_PATH = "Shared/uipath-maestro-flow"
CONNECTOR_KEY = "uipath-salesforce-slack"
CHANNEL_NAME = "office-bellevue"
ADDRESS = "700 Bellevue Way NE, Suite 2000, Bellevue, WA 98004"
CURATED_CHANNELS = (
    "curated_channels?fields=id,name&types=public_channel,private_channel"
    "&exclude_archived=false&limit=1000"
)
CONVERSATIONS = "conversations"
CONVERSATIONS_QUERY = "limit=1000&exclude_archived=false&types=public_channel,private_channel"


def _extract_json(stdout: str) -> dict[str, Any]:
    """Parse JSON from CLI output that may include log lines before the payload."""
    for i, line in enumerate(stdout.splitlines()):
        if line.lstrip().startswith("{"):
            return json.loads("\n".join(stdout.splitlines()[i:]))
    raise ValueError(f"no JSON object found in output: {stdout[:500]}")


def _run_uip(args: list[str], *, timeout: int = 60) -> dict[str, Any]:
    result = subprocess.run(
        ["uip", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"uip {' '.join(args)} failed with exit {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    try:
        payload = _extract_json(result.stdout)
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc
    if payload.get("Result") == "Failure":
        raise RuntimeError(f"uip {' '.join(args)} returned failure: {payload}")
    return payload


RunUip = Callable[[list[str]], dict[str, Any]]


def _folder_key(run_uip: RunUip) -> str:
    payload = run_uip(["or", "folders", "get", FOLDER_PATH, "--output", "json"])
    key = ((payload.get("Data") or {}).get("Key") or "").strip()
    if not key:
        raise RuntimeError(f"could not resolve folder key for {FOLDER_PATH!r}: {payload}")
    return key


def _slack_connection_id(run_uip: RunUip, folder_key: str) -> str:
    payload = run_uip(
        [
            "is",
            "connections",
            "list",
            CONNECTOR_KEY,
            "--folder-key",
            folder_key,
            "--output",
            "json",
        ]
    )
    connections = payload.get("Data") or []
    enabled = [
        c for c in connections if str(c.get("State") or "").lower() == "enabled"
    ]
    if not enabled:
        raise RuntimeError(
            f"no enabled {CONNECTOR_KEY!r} connection in {FOLDER_PATH!r}: {payload}"
        )
    enabled.sort(key=lambda c: str(c.get("IsDefault") or "").lower() != "yes")
    return str(enabled[0]["Id"])


def _pagination(data: dict[str, Any]) -> tuple[bool, str | None]:
    pagination = data.get("Pagination") or {}
    has_more = str(pagination.get("HasMore") or "").lower() == "true"
    token = pagination.get("NextPageToken")
    return has_more, str(token) if token else None


def _find_channel_in_resource(
    run_uip: RunUip,
    connection_id: str,
    object_name: str,
    initial_query: str | None = None,
) -> dict[str, Any] | None:
    query: str | None = None
    while True:
        args = [
            "is",
            "resources",
            "run",
            "list",
            CONNECTOR_KEY,
            object_name,
            "--connection-id",
            connection_id,
            "--output",
            "json",
        ]
        effective_query = query or initial_query
        if effective_query:
            args.extend(["--query", effective_query])
        payload = run_uip(args)
        data = payload.get("Data") or {}
        for item in data.get("items") or []:
            if str(item.get("name") or "").lower() == CHANNEL_NAME:
                return item
        has_more, token = _pagination(data)
        if not has_more or not token:
            return None
        query = f"nextPage={token}"


def _find_channel(run_uip: RunUip, connection_id: str) -> dict[str, Any] | None:
    channel = _find_channel_in_resource(run_uip, connection_id, CURATED_CHANNELS)
    if channel is not None:
        return channel
    return _find_channel_in_resource(
        run_uip, connection_id, CONVERSATIONS, CONVERSATIONS_QUERY
    )


def _create_channel(run_uip: RunUip, connection_id: str) -> dict[str, Any]:
    payload = run_uip(
        [
            "is",
            "resources",
            "run",
            "create",
            CONNECTOR_KEY,
            "conversations",
            "--connection-id",
            connection_id,
            "--body",
            json.dumps({"name": CHANNEL_NAME, "is_private": False}),
            "--output",
            "json",
        ],
        timeout=90,
    )
    channel = payload.get("Data") or {}
    if not channel.get("id"):
        raise RuntimeError(f"created Slack channel did not return an id: {payload}")
    return channel


def _set_description(run_uip: RunUip, connection_id: str, channel_id: str) -> None:
    run_uip(
        [
            "is",
            "resources",
            "run",
            "create",
            CONNECTOR_KEY,
            "set_channel_description",
            "--connection-id",
            connection_id,
            "--body",
            json.dumps({"channel": channel_id, "purpose": ADDRESS}),
            "--output",
            "json",
        ],
        timeout=90,
    )


def _has_expected_description(channel: dict[str, Any]) -> bool:
    purpose = channel.get("purpose") or {}
    value = str(purpose.get("value") or "")
    return all(part in value for part in ADDRESS.split(", "))


def ensure_office_bellevue_channel(
    *, run_uip: Callable[..., dict[str, Any]] = _run_uip
) -> dict[str, str]:
    folder_key = _folder_key(run_uip)
    connection_id = _slack_connection_id(run_uip, folder_key)
    channel = _find_channel(run_uip, connection_id)
    if channel is None:
        channel = _create_channel(run_uip, connection_id)
    channel_id = str(channel.get("id") or "")
    if not channel_id:
        raise RuntimeError(f"Slack channel {CHANNEL_NAME!r} has no id: {channel}")
    if not _has_expected_description(channel):
        _set_description(run_uip, connection_id, channel_id)
    return {"connection_id": connection_id, "channel_id": channel_id}


def main() -> None:
    try:
        result = ensure_office_bellevue_channel()
    except Exception as exc:  # noqa: BLE001 - command-line fixture should report all failures
        sys.exit(f"FAIL: {exc}")
    print(
        f"OK: Slack #{CHANNEL_NAME} ready "
        f"(connection_id={result['connection_id']}, channel_id={result['channel_id']})"
    )


if __name__ == "__main__":
    main()
