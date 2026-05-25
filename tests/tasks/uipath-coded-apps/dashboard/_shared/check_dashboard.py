"""
Shared validation script for dashboard skill tests.
Run from the generated project directory (tempdir sandbox).

Usage:
  python3 check_dashboard.py [--min-widgets N] [--require-insights] [--require-sdk]
                              [--require-recipe ENDPOINT] [--require-starttime]

Exit 0 = all checks pass. Exit 1 = failure with details on stdout.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

def fail(msg: str) -> None:
    print(f"FAIL: {msg}", flush=True)
    sys.exit(1)

def check(condition: bool, msg: str) -> None:
    if not condition:
        fail(msg)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-widgets", type=int, default=1,
                        help="Minimum number of widget files in src/widgets/")
    parser.add_argument("--require-insights", action="store_true",
                        help="At least one widget must use useInsights")
    parser.add_argument("--require-sdk", action="store_true",
                        help="At least one widget must use SDK (not useInsights) for data")
    parser.add_argument("--require-recipe", default=None,
                        help="At least one widget must use this Insights endpoint, e.g. agents.getErrors")
    parser.add_argument("--require-starttime", action="store_true",
                        help="At least one widget must use a startTime constant (not inline Date arithmetic)")
    parser.add_argument("--no-tsc", action="store_true",
                        help="Skip tsc --noEmit check (use when node_modules not installed)")
    args = parser.parse_args()

    cwd = Path.cwd()

    # 1. Project structure
    check((cwd / "package.json").exists(), "package.json not found — scaffold did not run")
    check((cwd / ".env.local").exists(), ".env.local not found — env vars not written")
    check((cwd / "src").is_dir(), "src/ directory missing")
    check((cwd / "vite.config.ts").exists(), "vite.config.ts missing")

    # 2. Required env vars
    env_content = (cwd / ".env.local").read_text()
    for var in ["VITE_UIPATH_CLOUD_URL", "VITE_UIPATH_BASE_URL",
                "VITE_UIPATH_ORG_NAME", "VITE_UIPATH_TENANT_NAME",
                "VITE_INSIGHTS_TENANT_ID", "VITE_UIPATH_PAT"]:
        check(var in env_content, f".env.local missing {var}")

    # 3. PAT value is non-empty
    pat_line = next((l for l in env_content.splitlines() if l.startswith("VITE_UIPATH_PAT=")), "")
    pat_value = pat_line.split("=", 1)[1] if "=" in pat_line else ""
    check(len(pat_value) > 10, "VITE_UIPATH_PAT is empty or suspiciously short — auth will fail")

    # 4. Widget files
    widgets_dir = cwd / "src" / "widgets"
    check(widgets_dir.is_dir(), "src/widgets/ directory missing")
    widget_files = [f for f in widgets_dir.iterdir()
                    if f.suffix == ".tsx" and f.name != "index.ts"]
    check(len(widget_files) >= args.min_widgets,
          f"Expected >= {args.min_widgets} widget(s), found {len(widget_files)}")

    # 5. index.ts exports
    index_ts = widgets_dir / "index.ts"
    check(index_ts.exists(), "src/widgets/index.ts missing — DashboardShell can't import widgets")

    # Concatenate all widget file contents for pattern checks
    all_widget_content = "\n".join(f.read_text() for f in widget_files)

    # 6. useInsights usage
    if args.require_insights:
        check("useInsights" in all_widget_content,
              "No widget uses useInsights — Insights routing not applied")

    # 7. SDK usage (not Insights)
    if args.require_sdk:
        sdk_patterns = ["QueueItems", "Jobs.getAll", "Processes.getAll",
                        "Tasks.getAll", "Entities.getAll", "CaseInstances"]
        found_sdk = any(p in all_widget_content for p in sdk_patterns)
        check(found_sdk, f"No widget uses SDK patterns {sdk_patterns} — SDK routing not applied")

    # 8. Specific endpoint usage
    if args.require_recipe:
        check(args.require_recipe in all_widget_content,
              f"No widget uses endpoint '{args.require_recipe}' — recipe not applied correctly")

    # 9. startTime constants (not raw Date.now arithmetic)
    if args.require_starttime:
        has_constant = any(
            c in all_widget_content
            for c in ["ONE_DAY_AGO", "SEVEN_DAYS_AGO", "THIRTY_DAYS_AGO", "NINETY_DAYS_AGO"]
        )
        # Also accept if they compute it from Date.now but assign to a named variable
        has_derived = bool(re.search(r"const \w+(?:Ago|Start|Time)\s*=\s*new Date", all_widget_content))
        check(has_constant or has_derived,
              "Widgets use inline Date.now() arithmetic — expected named startTime constant")

    # 10. No hardcoded tenant IDs or org names in widget files
    # (basic check: no UUID-looking strings that aren't from env vars)
    hardcoded_uuid = re.search(
        r'["\']([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})["\']',
        all_widget_content
    )
    check(hardcoded_uuid is None,
          f"Hardcoded UUID found in widget: {hardcoded_uuid.group(1) if hardcoded_uuid else ''}")

    # 11. App.tsx imports widgets
    app_tsx = cwd / "src" / "App.tsx"
    check(app_tsx.exists(), "src/App.tsx missing")
    app_content = app_tsx.read_text()
    check("widgets" in app_content.lower(),
          "App.tsx does not import from src/widgets — dashboard has no content")

    # 12. TypeScript compilation
    if not args.no_tsc:
        node_modules = cwd / "node_modules"
        if node_modules.is_dir():
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                capture_output=True, text=True, cwd=str(cwd)
            )
            if result.returncode != 0:
                fail(f"tsc --noEmit failed:\n{result.stdout}\n{result.stderr}")
        else:
            print("SKIP: node_modules not present, skipping tsc check", flush=True)

    widget_names = [f.stem for f in widget_files]
    print(f"PASS: {len(widget_files)} widget(s): {', '.join(widget_names)}", flush=True)

if __name__ == "__main__":
    main()
