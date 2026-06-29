# Plan: uipath-planner feedback issues (PILOT-6044/6045/6046)

**Branch:** `fix/uipath-planner/fix_feedback_issues`
**Date:** 2026-06-29
**Status:** Analysis complete; scope decided with owner. Fixes NOT yet applied. This doc is the implementer handover.
**Audience:** an AI agent implementing the fixes. Work per-issue; each task is independently verifiable.
**Re-verify all line numbers with Grep before editing** — files shift.

---

## 1. The three issues

All three are feedback-derived skill-improvement tickets (PILOT / Autopilot, component Studio Desktop, Normal, Open). Each was filed after using `uipath-planner` on a real finance engagement and was already partially addressed; what remains are the residual gaps.

| Issue | Source feedback | Residual ask |
|---|---|---|
| [PILOT-6046](https://uipath.atlassian.net/browse/PILOT-6046) | UV-14878 | First-class attended re-authentication / hardware-token handoff (resumable-pause) pattern for portal automations. |
| [PILOT-6045](https://uipath.atlassian.net/browse/PILOT-6045) | UV-14867, UV-14929 | (1) native diagram rendering + reflow; (2) official ASDD Word section auto-mapping; (3) buildable low-code UiPath Apps route. |
| [PILOT-6044](https://uipath.atlassian.net/browse/PILOT-6044) | UV-14914 | Estimation accelerator: opportunity register → complexity band → pack-hours → contingency; unify Core-RPA + Agentic matrices with Pack-Hours catalogue. |

## 2. Scope lens

`uipath-planner` is **plan-and-design only** (Critical Rule 1). Outputs: SDD markdown, plan/tasks markdown, live `TaskCreate`. Rule 8 / Anti-pattern 7: **route, do not redescribe** specialist build flows. Repo rules: self-contained skills, no committed template binaries, cross-platform scripts, no stale content. Every requirement is judged design/routing (in) vs. build/tooling-that-belongs-elsewhere (out).

## 3. Scope decisions (confirmed with owner 2026-06-29)

| Item | Verdict | Decision |
|---|---|---|
| PILOT-6046 design pattern + detection upgrade | **In scope** | Implement in planner. |
| PILOT-6046 build recipe | **Out** | Belongs to `uipath-rpa`. |
| PILOT-6045 #1 diagram image rendering | **Doc-only** | No tooling/dependency. Improve manual-render guidance only. |
| PILOT-6045 #2 ASDD generator | **Crosswalk only** | Section-mapping reference; user supplies the canonical ASDD skeleton (like `--reference-doc` for styles). No binary committed. |
| PILOT-6045 #3 low-code Apps design | **In scope** | Add SDD template + mapping row. |
| PILOT-6045 #3 low-code Apps build route | **Out** | No builder exists in toolchain — manual deliverable + separate ticket. |
| PILOT-6044 estimation accelerator | **Descoped** | Does not fit planner's unit of work. Document why; revisit in `uipath-automation-discovery` or a new sizing skill. |

---

## 4. Fix plan

### Phase 1 — PILOT-6046: attended re-auth / hardware-token handoff pattern

**Current state.** `references/pdd-analysis-guide.md` already *detects* the signal:
- "Signing modality" row (`:212`) — hardware token / smart card / qualified signature.
- "Robot attendance" row (`:214`) — 2FA / OTP / human present.
- Destinations (`:219`) route both to §9 Application Inventory / §16 Deployment Environment with `[SME REVIEW]`.

Gap: no architectural **pattern** — only a detect-and-flag. The reporter had to design the resumable pause from scratch.

- [ ] **1.0 (BLOCKING) Confirm the real UiPath primitive before writing.** Web-search / verify current product docs for how an **attended** robot handles a human hardware-token login mid-run: synchronous attended pause-and-prompt (message box / input dialog, human logs in, robot continues) vs. long-running **suspend/resume** (persistence + Action Center/trigger resume). Attended + same-machine handoff is likely the synchronous form; suspend/resume is the unattended/orchestrated form. Writing the wrong primitive is worse than the current SME-review punt. Record the verified primitive(s) in the new reference.
- [ ] **1.1 Add `references/attended-reauth-pattern-guide.md`** — a **design** reference (not a build recipe). Cover: where the re-auth checkpoint sits in the process map; the human-handoff contract (what the human does, what signals "done"); resume condition; restart-safety / idempotency of the surrounding loop; attended-vs-unattended implications; what is delegated to `uipath-rpa`. Keep it design-altitude per Rule 8 — no activity names, no XAML.
- [ ] **1.2 Upgrade detection → first-class SDD subsection.** In `pdd-analysis-guide.md` destinations (`:219`) and the RPA template, replace "flag `[SME REVIEW]`" for the attendance/signing signal with: emit a named **"Attended Re-authentication / Hardware-token Handoff"** subsection (attach to the process map and/or §16) that describes the checkpoint at design altitude and **routes the build to `uipath-rpa`**. Cite `attended-reauth-pattern-guide.md`.
- [ ] **1.3 Patterns routing note.** In `references/multi-skill-patterns-guide.md`, add a one-line note that an SDD carrying an attended re-auth checkpoint routes the checkpoint build to `uipath-rpa` (no new pattern number — it lives inside the RPA build step).
- [ ] **1.4 Keep out of scope:** the suspend/resume vs. attended-prompt implementation, the form/dialog, the activities. Do NOT write these — `uipath-rpa` owns UIA end-to-end.

### Phase 2 — PILOT-6045 #3: low-code UiPath Apps design route

**Current state.** `platform-availability-guide.md:27` lists UiPath Apps (low-code) as on-prem-available and the documented alternative when Coded Apps is blocked (`:28`), but says "No CLI/skill in this toolchain builds it." There is **no template** (only rpa/flow/case/agent/coded-app/api-workflow) and **no Template-Mapping row** (`product-selection-guide.md:336-343`), so a designed app falls through.

- [ ] **2.1 Add `assets/templates/apps-lowcode-sdd-template.md`** — model on `coded-app-sdd-template.md` (screens, data sources, user journeys, app-level data flow). Add a prominent header note: **build is a manual deliverable (UiPath Apps designer); no CLI/skill builds it.** Keep `Generated by: uipath-planner` (bare, per Critical Rule 5 — no `v<VERSION>`).
- [ ] **2.2 Add the Template-Mapping row** in `product-selection-guide.md` single-product table (`:336-343`): `UiPath Apps (low-code) | ../assets/templates/apps-lowcode-sdd-template.md`.
- [ ] **2.3 Wire the Coded-Apps-blocked alternative.** Where the Constraint Gate replaces blocked Coded Apps with low-code Apps (`product-selection-guide.md` Level 1.75 gate `:170`, and availability matrix `:28`), point the alternative at the new template + a §18/Next-Steps note that the build is a manual Apps-designer deliverable.
- [ ] **2.4 Out of scope:** an actual low-code Apps builder. File a **separate ticket** for a future `uipath-apps` (low-code) builder skill; reference it from the template header so the gap is tracked, not silently absorbed.

### Phase 3 — PILOT-6045 #1: diagram rendering (doc-only)

**Current state.** `scripts/sdd-to-docx.sh:10-12,73-77` keeps Mermaid as code blocks and warns to render externally. `sdd-generation-guide.md:477` already offers the user the choice (leave as-is / render externally and insert). Decision: **no tooling** — `mmdc`/Node+Chromium dependency rejected; remote renderers leak customer architecture.

- [ ] **3.1 Sharpen the manual-render guidance** in `sdd-generation-guide.md` (near `:477`) and the `sdd-to-docx.sh` warning: name the concrete manual path (e.g., paste the Mermaid into a renderer / mermaid.live, export PNG/SVG, replace the code block in the .docx) and state it's a deliverable-polish step, not required for a valid SDD. Keep it tool-agnostic; do not endorse a service that receives the diagram if the architecture is sensitive.
- [ ] **3.2 "Reflow" is a non-issue — document it.** The planner generates Mermaid from the current step set every run (`rpa-sdd-template.md:142` "build the process map STRICTLY from the steps extracted in Phase 1"), so regeneration reflows. Add one line clarifying that diagram edits come from regenerating the SDD, not hand-editing nodes. No code change.

### Phase 4 — PILOT-6045 #2: ASDD section crosswalk (user-supplied skeleton)

**Current state.** `--reference-doc` already applies the customer's fonts/styles. Mapping into the official ASDD *section skeleton* is manual. Decision: **crosswalk reference only** — user brings the skeleton; no binary committed; no auto-mapper encoding a PS-internal template that goes stale.

- [ ] **4.1 Add `references/asdd-crosswalk-guide.md`** — a mapping table: planner SDD H2/H3 → official ASDD section. Where the planner SDD reorganizes content for implementation (Anti-pattern 4), state the many-to-one / one-to-many mappings explicitly. Instruct the user to supply their current ASDD skeleton (it is the authoritative source; this table is a starting crosswalk that may drift).
- [ ] **4.2 Link from the docx path.** In `sdd-generation-guide.md` Word-output step and the `sdd-to-docx.sh` `--reference-doc` usage, add: "to map content into the official ASDD section structure, see `asdd-crosswalk-guide.md`; supply your ASDD skeleton — section structure is not auto-generated."
- [ ] **4.3 Out of scope:** committing the ASDD `.docx`, and any auto-mapper that hardcodes the skeleton.

### Phase 5 — PILOT-6044: estimation accelerator (descoped, documented)

Estimation is **portfolio-level sizing** (the source sized 23 opportunities); the planner is **one PDD → one SDD**. Different unit of work, audience (pre-sales/delivery vs. implementation), and deliverable. Org-wide opportunity discovery already lives in `uipath-automation-discovery`.

- [ ] **5.1 Record the descope** in this doc's §6 and in the PILOT-6044 ticket: not a planner fit; recommended home is `uipath-automation-discovery` (extends its tiered prioritization) or a new `uipath-estimation` skill. The matrices + Pack-Hours catalogue must be sourced from an **authoritative UiPath PS reference** — the ~6k-hour gap was an accuracy failure, so unverified tables are the risk, not the plumbing.
- [ ] **5.2 No planner code change.** (Optional future bridge, not now: a per-SDD complexity-band hint using app-count/variations/decomposition the planner already extracts — low value alone.)

---

## 5. Verification

| Check | Method | Pass |
|---|---|---|
| New references reachable | every new `references/*.md` + template linked from SKILL.md or a guide | no orphans |
| Links resolve | grep `\]\(` in `skills/uipath-planner/`; each relative target exists and stays inside the skill folder | all pass |
| Template superset | new low-code-apps template diffed per Critical Rule 6 conventions; `Generated by: uipath-planner` bare | pass |
| Description budgets | `bash hooks/validate-skill-descriptions.sh` | exit 0 (only if frontmatter touched) |
| Skill status | new template/refs don't change status; `python3 scripts/check-skill-status.py` if README affected | pass |
| Pattern/rule refs | grep `Pattern [0-9]` / `Critical Rule` — no dangling numbers introduced | pass |
| 6046 primitive verified | reference cites verified product behavior, not from-memory | pass |
| Tests | `/test-coverage uipath-planner`; add/adjust tasks for the new low-code-Apps mapping + attended-reauth subsection; `/lint-task` clean | pass |

## 6. Out of scope (explicit)

- **Estimation accelerator (PILOT-6044)** — descoped from planner; re-home to `uipath-automation-discovery` / new skill with PS-verified matrices.
- **Attended re-auth build recipe** — `uipath-rpa`.
- **Low-code Apps builder** — no builder in toolchain; separate ticket.
- **Mermaid→image tooling** — rejected (dependency / privacy); manual render documented instead.
- **ASDD auto-mapper / committed ASDD binary** — crosswalk reference + user-supplied skeleton only.

## 7. Suggested PR shaping

- One PR for **Phase 1 (6046)** — self-contained, highest value.
- One PR for **Phases 2–4 (6045 residuals)** — all SDD-design/doc changes, no new dependencies.
- **Phase 5 (6044)** — ticket update + this doc; no code PR.
