# Dashboard Capability

Build, edit, or deploy UiPath dashboards powered by Insights RTM and the TypeScript SDK.

---

## Step 0 — Detect intent BEFORE loading anything

Read the user's message and classify it as one of three intents. **Do not load any files yet.**

| User says | Intent | What to do next |
|-----------|--------|-----------------|
| "build me a dashboard", "show me X metrics", "create a dashboard for…" | **BUILD** | Follow the Build path below |
| "add/remove/change a widget", "update the chart", "make it 7 days" | **EDIT** | Follow the Edit path below |
| "deploy this", "publish it", "make it live", "ship it to the team", "deploy the dashboard" | **DEPLOY** | Follow the Deploy path below |

If the intent is unclear, ask one question: "Do you want to build a new dashboard, edit an existing one, or deploy it to Automation Cloud?"

---

## Path A — BUILD (new dashboard)

### Turn 2 — Everything in ONE parallel message

Fire all of these simultaneously. Use multiple tool calls in one response — do not wait for one before starting another.

> **Path note:** All file paths are relative to `SKILL_BASE_DIR` — the directory where `SKILL.md` lives. Not relative to this file's location.

**4 file reads (parallel):**

| File | Purpose |
|------|---------|
| `references/dashboards/plugins/build/impl.md` *(from skill root)* | Build instructions, plan format, intent.json schema |
| `references/dashboards/primitives/tier-resolution.md` *(from skill root)* | Metric classification, SDK service reference |
| `references/dashboards/aesthetic/layout-patterns.md` *(from skill root)* | Layout rules |
| `assets/scripts/capability-registry.json` *(from skill root)* | Metric catalog |

**2 commands (same message):**

```bash
uip login status --output json
```

```bash
node -e "
const fs = require('fs')
fs.existsSync('.dashboard/state.json') ? process.exit(0) : process.exit(1)
" && echo INCREMENTAL || echo FRESH
```

**Pre-warm (same message — `run_in_background: true` on the Bash tool call):**

```bash
node "<SKILL_BASE_DIR>/assets/scripts/build-dashboard.mjs" --prewarm "<PROJECT_DIR>"
```

⚠️ `run_in_background: true` is a tool call parameter, not a shell flag. Without it, the call blocks for 60–90s before the plan appears.

**After all reads:** output the plan as pure text. No tool calls until user confirms. See `plugins/build/impl.md`.

**Routing:**
- `INCREMENTAL` → read `primitives/incremental-editor.md`, then follow it
- `FRESH` → follow `plugins/build/impl.md`

---

## Path B — EDIT (change existing dashboard)

Read `primitives/incremental-editor.md` in the same message as `uip login status --output json`. Follow it.

---

## Path C — DEPLOY

### Step 1 — Read the deploy plugin FIRST (before any CLI commands)

```
Read: references/dashboards/plugins/deploy/impl.md  *(from skill root)*
```

Read this file in parallel with:

```bash
uip login status --output json
```

**Do not run any other commands until you have read the deploy plugin and presented the plan to the user.**

### Step 2 — Present the deploy plan (pure text, zero CLI calls)

Read `.dashboard/state.json` in memory to get the app name, version, and routing name. Then output the plan:

```
Your **[Dashboard Name]** is ready to be deployed.

📦  Version:    [current] → [bumped]
🔗  URL path:   [routing-name]
📁  Folder:     AdminDashboards
🔄  Type:       Fresh deploy  OR  Updating existing deployment

📌  Do you want to pin this dashboard to the Governance UI?
   → "deploy and pin" — visible in the Governance section
   → "deploy" — deploy without pinning
```

**HALT. Do not run any CLI command until the user confirms.**

### Step 3 — Follow plugins/deploy/impl.md

After user confirms, follow every step in `plugins/deploy/impl.md` exactly as written. Do not invent steps, do not run `uip tools list`, do not run `npm run build` before the plan is confirmed.

---

## Scope

This skill only handles dashboard building, editing, and deploying. For anything else, respond:

> "This skill is for UiPath dashboard generation only. For [what they asked], please use the appropriate skill."

---

## Hard stops

- **Never** run ANY CLI command before presenting the plan and getting user confirmation
- **Never** improvise deploy steps — always read `plugins/deploy/impl.md` first
- **Never** run `uip tools list`, `npm run build`, or any command not in the relevant impl.md
- **Never** use `"agent-health-dashboard"` (routing slug) as the `-n` flag — always use the human-readable display name from state.json
- **Never** run `uip codedapp publish` without `-n` and `--version` flags
- **Never** fetch the live SDK docs URL — it takes 60–90s
- **Never** read `build-dashboard.mjs` — documented in impl.md
- **Never** run `ls`, `find`, or directory exploration
- **Never** read files one at a time
- **Never** commit generated dashboard files
- **Never** auto-deploy without explicit user confirmation
