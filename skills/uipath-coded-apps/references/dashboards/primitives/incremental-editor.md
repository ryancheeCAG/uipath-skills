# Incremental Editor

Use when `.dashboard/state.json` exists in the project directory — the user wants to
edit an existing dashboard, not start from scratch.

## Detection

At the start of a dashboard request, check before reading anything else:

```bash
ls .dashboard/state.json 2>/dev/null && echo "INCREMENTAL" || echo "FRESH"
```

If INCREMENTAL → follow this guide.
If FRESH → follow the normal build/impl.md pipeline.

## Step 1 — Read current state

```bash
STATE=$(cat .dashboard/state.json)
```

Parse: `app.name`, `app.routingName`, `widgets[]` (existing component names).

## Step 2 — Read existing widget files

Read all existing widget files from `src/dashboard/widgets/`.
Note which ones exist and their current content.

## Step 3 — Classify the user's request

| User says | Action |
|---|---|
| "add X widget" | Add new widget file, update Dashboard.tsx, update App.tsx routes |
| "remove X widget" | Delete widget file, update Dashboard.tsx, update App.tsx routes |
| "change X to show Y instead" | Rewrite only that widget file |
| "regenerate everything" | Treat as fresh build (ask to confirm) |

## Step 4 — Hand-edit detection

Before writing any file, check if it differs from what the skill would generate.
If the user has hand-edited a widget, warn before overwriting:

```
⚠️ I notice <WidgetName> has been customized since I last generated it.
Overwrite with the new version, or keep your changes and skip this widget?
(overwrite / keep)
```

Wait for explicit confirmation before overwriting a hand-edited file.

## Step 5 — Apply changes

**Adding a widget:**
1. Generate the new widget file (same Node.js heredoc as Phase 7)
2. Generate the new detail view file
3. Update `src/dashboard/Dashboard.tsx` — add widget to correct row
4. Update `src/app/App.tsx` — inject new import + route
5. Update `src/dashboard/widgets/index.ts` — add export

**Removing a widget:**
1. Delete the widget file
2. Delete the detail view file
3. Update Dashboard.tsx — remove widget
4. Update App.tsx — remove import + route
5. Update widgets/index.ts — remove export

**Changing a widget:**
1. Rewrite only the widget file
2. If the endpoint changed, update the detail view too
3. Other files unchanged

## Step 6 — Update state.json

After changes, update `widgets[]` in state.json to reflect the new list.
Use the atomic write pattern from state-file.md.

## Step 7 — Validate + show summary

Run `tsc --noEmit`. If it passes, show a clean summary of what changed.

## Anti-patterns

- Do NOT regenerate the entire project for a single widget addition
- Do NOT overwrite hand-edits without asking
- Do NOT change routing names on edit — they are permanent
- Do NOT change the .env.local file unless the user explicitly asks to change environments
