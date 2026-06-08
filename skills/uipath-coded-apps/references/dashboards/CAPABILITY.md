# Dashboard Capability

Build or edit a React dashboard powered by Insights RTM and the UiPath TypeScript SDK.

---

## The 3-turn contract

From the user's perspective, building a dashboard looks like this:

1. **They send their request**
2. **They see a polished plan** — no tool calls visible between request and plan
3. **They confirm** — a single bash call runs, progress ticks appear, browser opens

Every internal mechanic (reads, pre-warm, login, intent.json) happens invisibly. The user sees only: plan → confirm → live dashboard.

---

## Turn 2 — Everything in ONE parallel message (this turn)

Fire all of these simultaneously. This is the only turn before the plan.

**Reads (all parallel):**

> **Path note:** All file paths in the table below are relative to `SKILL_BASE_DIR` — the directory where `SKILL.md` lives (shown as "Base directory for this skill:" in your activation message). They are **not** relative to this file's location (`references/dashboards/`). When reading these files, prefix each path with your `SKILL_BASE_DIR`.
>
> Verify: this file's own path is `$SKILL_BASE_DIR/references/dashboards/CAPABILITY.md`

| File | Purpose |
|------|---------|
| `references/dashboards/plugins/build/impl.md` *(from skill root)* | Full build instructions |
| `references/dashboards/primitives/tier-resolution.md` *(from skill root)* | Metric classification + hard-refuse list |
| `references/dashboards/primitives/auth-context.md` *(from skill root)* | Login + credential extraction |
| `references/dashboards/primitives/sdk-patterns.md` *(from skill root)* | Skill-specific SDK patterns (casting, normalisation, dynamic import) |
| `references/dashboards/primitives/build-plan.md` *(from skill root)* | intent.json schema |
| `references/dashboards/aesthetic/layout-patterns.md` *(from skill root)* | Layout rules |
| `assets/scripts/capability-registry.json` *(from skill root)* | Metric catalog |

> All `references/dashboards/` paths are inside this file's own directory. The `assets/` paths are at the skill root — two levels up from this file.

**Also fetch the live SDK documentation in the same message:**

```
WebFetch: https://uipath.github.io/uipath-typescript/llms-full-content.txt
Prompt: Extract all service classes with their import subpaths, method signatures, and response type field names.
```

This is the authoritative SDK reference — always current, maintained by the SDK team. Use it to verify field names before writing `intent.json` or T3-SDK `fnBody`. The `sdk-patterns.md` above covers only what the SDK docs omit (skill-specific casting and normalisation patterns).

**Commands (in the same message):**

```bash
uip login status --output json
```

```bash
node -e "
const fs = require('fs')
fs.existsSync('.dashboard/state.json') ? process.exit(0) : process.exit(1)
" && echo INCREMENTAL || echo FRESH
```

**Pre-warm — fire in background, do NOT wait:**

Derive `<PROJECT_DIR>` from the user's request (e.g. `~/dashboards/agent-health-x7k2` or an absolute path the user specifies), then fire the build script's prewarm mode immediately:

```bash
# run_in_background: true — fire this and continue immediately, do NOT wait
node "<SKILL_BASE_DIR>/assets/scripts/build-dashboard.mjs" --prewarm "<PROJECT_DIR>"
```

This uses the build script to copy the scaffold and run `npm ci` — works correctly on Windows and Unix. Set `run_in_background: true` on this Bash call. The build script emits `PREWARM_DONE` when complete. Continue to the plan output immediately — do not wait.

---

## Turn 2 output — Show the plan (pure text, zero tool calls)

After all reads complete and pre-warm is fired, output the plan directly as text. No more tool calls until the user confirms.

See `plugins/build/impl.md` for the plan format and subsequent phases.

---

## Routing

- `INCREMENTAL` → read `primitives/incremental-editor.md`, then follow it
- `FRESH` → follow `plugins/build/impl.md`

---

## Hard stops

- **Never** read `build-dashboard.mjs` — fully documented in impl.md
- **Never** run `ls`, `find`, or directory exploration
- **Never** read `sdk-capabilities.md` — tier-resolution.md + capability-registry.json are sufficient
- **Never** read files one at a time
- **Never** show tool call output to the user between their request and the plan
- **Never** wait for pre-warm before showing the plan — fire it in background and move on
- **Never** auto-deploy
- **Never** commit generated dashboard files
