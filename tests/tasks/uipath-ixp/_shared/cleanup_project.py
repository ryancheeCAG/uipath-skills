#!/usr/bin/env python3
"""
Post-run cleanup for IXP e2e/integration tasks. Two stages, both best-effort:

1. Delete THIS run's project, named in report.json (CWD), written by the agent
   right after creation:
     {"project_name": "<ProjectName from `uip ixp projects create` output>"}

2. Sweep STALE leftover test projects — ones a previous crashed run never
   deleted. OPT-IN via IXP_CLEANUP_SWEEP=1 (only the e2e task sets it, so the
   suite doesn't run N concurrent janitors conflicting on the same deletes).
   Scoped two ways so it can never touch a live/real project:
     - name/title must start with a known test prefix (IXP_CLEANUP_PREFIXES,
       default "codereval-,e2e-test-,ixp-it-" — the last two are legacy
       prefixes, kept so pre-rename leftovers still get swept), and
     - CreatedAt must be older than IXP_CLEANUP_MAX_AGE_HOURS (default 6h) —
       safely beyond the longest task_timeout (~50 min), so a concurrent run's
       freshly-created project is never in range.

Delete is `uip ixp projects delete <name> -y --output json`. Best-effort and
ALWAYS exits 0 (any delete failure is logged as WARN, never fails the test).
NOTE: `delete` 404s on dataset-less (orphaned) project shells that `list` still
returns — those are un-deletable via the current CLI and will WARN each run.
Locally without a tenant this is a no-op.

Env knobs:
  IXP_CLEANUP_SWEEP=1            enable stage 2 sweep (default OFF; set only on e2e)
  IXP_CLEANUP_PREFIXES=a-,b-     comma-separated test-title prefixes to sweep
  IXP_CLEANUP_MAX_AGE_HOURS=6    only sweep projects older than this
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

# codereval- = current root for all coder_eval test projects (codereval-e2e-*,
# codereval-it-*). e2e-test- and ixp-it- are legacy prefixes kept so pre-rename
# leftovers still get swept.
DEFAULT_PREFIXES = "codereval-,e2e-test-,ixp-it-"
DEFAULT_MAX_AGE_HOURS = 6.0
LIST_PAGE_SIZE = 100        # projects fetched per `projects list` page
LIST_MAX_SCAN = 5000        # stop paging after this many (safety bound)


def run(cmd, timeout=60):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception as e:
        print(f"WARN: command failed to invoke ({' '.join(cmd)}): {e}")
        return None


def delete_project(name):
    """Delete one project by name. Idempotent; best-effort."""
    proc = run(["uip", "ixp", "projects", "delete", name, "-y", "--output", "json"])
    if proc is None:
        return
    out = (proc.stdout or proc.stderr or "").strip()
    # Only rc==0 is success. Do NOT treat any error — including 404 — as benign:
    # `uip ixp projects delete <name>` 404s on projects that `projects list` still
    # returns (the CLI's name->id resolution doesn't reach older/deep projects), so
    # a 404 does NOT mean the project is gone. Masking it hid a real failure. With
    # the e2e task as the sole sweeper there are no concurrent-delete races, so any
    # non-zero exit is a genuine failure worth surfacing.
    if proc.returncode == 0:
        print(f"OK: deleted IXP project '{name}'")
    else:
        print(f"WARN: could not delete '{name}' (exit {proc.returncode}): {out[:200]}")


def load_report():
    path = os.path.join(os.getcwd(), "report.json")
    if not os.path.exists(path):
        print(f"SKIP: no report.json at {path}")
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        print(f"SKIP: could not parse report.json: {e}")
        return None


def parse_created_at(value):
    """Parse an IXP CreatedAt timestamp to an aware datetime, or None."""
    if not value or not isinstance(value, str):
        return None
    s = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def cleanup_own_project():
    report = load_report()
    if not report:
        return None
    name = (
        report.get("project_name")
        or report.get("name")
        or report.get("ProjectName")
    )
    if not name:
        print("SKIP: no 'project_name' key in report.json")
        return None
    delete_project(name)
    return name


def sweep_stale(own_name):
    # Opt-IN: the backlog sweep runs ONLY when IXP_CLEANUP_SWEEP=1. Just ONE task
    # (the e2e) enables it, so the whole suite doesn't run N concurrent janitors
    # racing to delete the same projects (which caused 409 conflicts). Every other
    # task only deletes its own project (stage 1).
    if os.environ.get("IXP_CLEANUP_SWEEP", "0") != "1":
        return
    prefixes = tuple(
        p.strip()
        for p in os.environ.get("IXP_CLEANUP_PREFIXES", DEFAULT_PREFIXES).split(",")
        if p.strip()
    )
    if not prefixes:
        return
    try:
        max_age_hours = float(
            os.environ.get("IXP_CLEANUP_MAX_AGE_HOURS", DEFAULT_MAX_AGE_HOURS)
        )
    except ValueError:
        max_age_hours = DEFAULT_MAX_AGE_HOURS

    # Page through the list rather than one giant limit, so we always reach the
    # OLDEST projects (the stale ones we want) regardless of list ordering.
    projects = []
    offset = 0
    while offset < LIST_MAX_SCAN:
        proc = run([
            "uip", "ixp", "projects", "list",
            "-l", str(LIST_PAGE_SIZE), "--offset", str(offset), "--output", "json",
        ])
        if proc is None or proc.returncode != 0:
            if offset == 0:
                print("SKIP sweep: could not list projects (no tenant / auth?)")
                return
            print(f"WARN sweep: list failed at offset {offset}; "
                  f"proceeding with {len(projects)} project(s) fetched")
            break
        try:
            data = json.loads(proc.stdout).get("Data") or {}
        except Exception as e:
            print(f"SKIP sweep: could not parse project list: {e}")
            return
        page = data.get("Projects") or []
        projects.extend(page)
        offset += LIST_PAGE_SIZE
        total = data.get("Total")
        if len(page) < LIST_PAGE_SIZE:
            break
        if isinstance(total, int) and offset >= total:
            break

    now = datetime.now(timezone.utc)
    cutoff_seconds = max_age_hours * 3600
    swept = 0
    for p in projects:
        name = p.get("Name")
        if not name:
            continue
        if name == own_name:  # already handled in stage 1
            continue
        # Match on Name only: test projects are created with the prefixed string
        # as their Name, and only the Title is ever renamed — so Name reliably
        # carries the prefix, and matching Title risks sweeping a real project
        # that merely has a prefixed display title.
        if not name.startswith(prefixes):
            continue
        created = parse_created_at(p.get("CreatedAt"))
        if created is None:
            print(f"SKIP sweep: '{name}' has unparseable CreatedAt; leaving it")
            continue
        age_s = (now - created).total_seconds()
        if age_s < cutoff_seconds:
            continue  # too recent — could be a live concurrent run
        print(f"SWEEP: stale test project '{name}' (age {age_s / 3600:.1f}h)")
        delete_project(name)
        swept += 1
    print(
        f"SWEEP done: {swept} stale test project(s) removed "
        f"(prefixes={list(prefixes)}, older_than={max_age_hours}h)"
    )


def main():
    own = cleanup_own_project()
    sweep_stale(own)
    sys.exit(0)


if __name__ == "__main__":
    main()
