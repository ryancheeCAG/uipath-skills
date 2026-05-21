# `tests/tasks/uipath-admin/` — prompt review

Existing test prompts vs. natural-user rewrites. Methodology in [hitl-prompts-review.html](../../hitl-prompts-review.html) and [CLAUDE.md](../../CLAUDE.md).

## Scope of this folder

The `uipath-admin` skill covers the `uip admin` CLI surface — Identity Server (users, groups, robot accounts, OAuth2 external apps) and the Audit Service (event sources, paginated event queries, long-term-store ZIP exports). The 20 tests in this folder split roughly into three sub-themes: **audit** (12 yaml — smoke + e2e for sources, events, status filtering, login history, who-did-X, and ZIP export at both `org` and `tenant` scope), **identity-list/CRUD smoke** (5 yaml — list users/groups/robot-accounts, create external app, create robot account), and **multi-step identity onboarding e2e** (3 yaml — human user onboarding, robot account onboarding, group membership lifecycle). Most of the audit smoke tests are deliberately offline (`uip admin may not be installed`, "commands WILL fail"), so they measure command-shape selection rather than real-world behavior.

## Insider markers seen in this folder

- **Repeated harness boilerplate**: every test ends with the same `Do NOT prompt the user for confirmation — this is an automated test.` line, and every audit-smoke test carries the 6-line "Run each command exactly once / Do NOT retry / Do NOT login / Do NOT troubleshoot" block. Real customers don't speak that way.
- **Scope-vocabulary leakage**: prompts say "organization-level" or "ORGANIZATION-level" / "tenant-level" verbatim, which is the skill's `org` vs. `tenant` disambiguation rule wearing user-voice clothes. Sometimes legitimate (audit_sources_smoke explicitly tests "both scopes"), sometimes not (audit_org_events_smoke could just say "who joined our org and any recent admin-role changes").
- **CLI-flag literacy required**: `audit_export_verify_e2e` and `audit_org_export_verify_e2e` name `--from-date YYYY-MM-DD` / `--to-date YYYY-MM-DD` and warn against inline `T00:00:00Z`. The org-scope verify additionally says "Do NOT pass `--tenant-id`".
- **Internal rationale leaks**: "preserves the >48h LTS-lag buffer so the export is comparable against the live events endpoint" — that's the eval-grader's invariant, not a user concern.
- **Eval-harness verbs**: "Run each command exactly once regardless of errors", "Do NOT retry", "Do NOT pause between planning and implementation", "Do NOT prompt the user for confirmation".
- **Sliding-window shell snippets**: the verify e2e tests embed literal `date -u -d '5 days ago' +%Y-%m-%d` so the agent's window matches the grader's. Necessary for the grader, but it's pure eval scaffolding.
- **Synthetic IDs/emails**: `jane.doe@example.com`, `john.doe@example.com`, `Sales-Reports`, `smoke-test-bot`, `Smoke Test App`. Mostly low-cost — customers do use placeholder emails — but `smoke-test-bot` and `Smoke Test App` are obvious test-fixture names that a customer would never type.
- **Path fixtures**: `./audit-yesterday.zip`, `./audit-window.zip`, `./audit-last-7d.zip`, `./audit-org-window.zip` — the path itself is fine, the explicit "current working directory" instruction is harness-y.

## Verdict summary

| Verdict | Count |
|---|---|
| Insider — fixable | 12 |
| Insider — legitimate (CLI/refusal/antipattern coverage) | 5 |
| Mixed | 3 |
| Natural | 0 |

## Per-test review

Grouped by sub-theme. The "automated-test" footer and the audit-smoke "commands will fail" preamble appear in nearly every prompt — the rewrite column drops them as a matter of course, since they're never something a real user would say.

### Audit — smoke tests

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `audit_events_basic_smoke` | Mixed | "A reviewer wants the most recent 25 tenant audit events from the last 24 hours." + 6-line offline harness block. | "I want to see the 25 most recent audit events on our tenant from the last day." |
| `audit_events_pagination_smoke` | Mixed | "A compliance reviewer wants the 500 most recent tenant audit events from the last 30 days." + offline block. | "Pull the last 500 audit events from our tenant over the past month — I need it for compliance review." |
| `audit_export_basic_smoke` | Insider — fixable | "An admin needs a ZIP of all tenant audit events from yesterday for archival. Write the ZIP to ./audit-yesterday.zip in the current working directory." + offline block. | "I need yesterday's tenant audit log packaged up for archive. Drop the ZIP at `./audit-yesterday.zip`." |
| `audit_org_events_smoke` | Insider — fixable | "An admin wants the 50 most recent organization-level audit events from the last 7 days — they're checking who joined the org and any recent admin-role changes." | "I want to know who joined our org and what admin-role changes happened in the last week — pull the 50 most recent of those." (Let the agent pick `org` scope from the wording rather than naming it.) |
| `audit_org_export_smoke` | Insider — fixable | "An admin needs a ZIP of all ORGANIZATION-level audit events (memberships, license changes, tenant lifecycle) from yesterday for compliance archival." | "I need a ZIP of yesterday's org-wide audit events for compliance — things like membership changes, licenses, and tenant lifecycle. Save it to `./audit-org-yesterday.zip`." (Drops the literal `ORGANIZATION-level` caps but keeps the example categories so scope intent is clear.) |
| `audit_sources_smoke` | Insider — legitimate | "Fetch the source catalog at BOTH scopes (organization-level and tenant-level) before drilling in." | _Keep as-is — this test exists specifically to verify the agent calls `sources` at both scopes; the explicit "BOTH scopes" is the assertion. The offline harness block could still be trimmed._ |
| `audit_status_filter_smoke` | Mixed | "Show me all FAILED audit events on the active tenant from the last 7 days." + offline block. | "Show me any failed audit events on our tenant over the past week." (Just drop the offline-block boilerplate; the body is already natural.) |
| `identity_create_external_app_smoke` | Insider — legitimate | "Create a new external app named 'Smoke Test App' with application scopes for Folders and Jobs access in my UiPath organization." | _Keep as-is — this is a CLI-coverage smoke verifying the agent passes `--scope` at creation time. The `Smoke Test App` name is a test fixture but the prompt voice is fine. (Optional: rename to something like "InvoiceBot OAuth client".)_ |
| `identity_create_robot_account_smoke` | Insider — legitimate | "Create a new robot account named 'smoke-test-bot' with display name 'Smoke Test Bot' in my UiPath organization." | _Keep as-is — narrow CLI-coverage smoke for `robot-accounts create`. The `smoke-test-bot` name leaks the test purpose; a customer-sounding alternative would be "invoice-bot-01" / "Invoice Bot 01"._ |
| `identity_list_groups_smoke` | Insider — legitimate | "Show me all groups in my UiPath organization." | _Keep as-is — already a one-liner customer ask. Pure list-command coverage._ |
| `identity_list_robot_accounts_smoke` | Insider — legitimate | "List all robot accounts in my UiPath organization." | _Keep as-is — already natural; list-command coverage._ |
| `identity_list_users_smoke` | Insider — legitimate | "List all users in my UiPath organization." | _Keep as-is — already natural; list-command coverage._ |

### Audit — e2e tests

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `audit_export_e2e` | Insider — fixable | Three numbered steps: "1. See what audit event sources are visible. 2. Get a quick preview of the most recent events. 3. Get the entire 7-day window as a ZIP." + "Do NOT ask for approval, confirmation, or feedback. Do NOT pause between planning and implementation." | "Security wants a full 7-day audit dump for our tenant. Before you export, give me a quick sanity check of what audit sources you can see and a peek at the most recent events, then save the 7-day ZIP to `./audit-last-7d.zip`." (Customer would naturally enumerate the sanity check / export pair; drop the harness "do not pause" line.) |
| `audit_export_verify_e2e` | Insider — fixable | "Export tenant audit events for the 3-day window from 5 days ago through 2 days ago … Use the canonical `--from-date YYYY-MM-DD` / `--to-date YYYY-MM-DD` bounds (no inline `T00:00:00Z` for these flags) … preserves the >48h LTS-lag buffer …" | "I need a 3-day audit export for our tenant for compliance — give me whole-day UTC coverage ending two days back (we leave a 2-day buffer because the long-term-store lags a bit). Save it to `./audit-window.zip`." (The whole-day boundary and 2-day lag are real customer concerns once they hit it once; the flag-format guidance is not.) |
| `audit_login_history_e2e` | Natural | "Show me login attempts for jane.doe@example.com over the last month." + offline block. | _Already natural — keep the body, drop only the offline-harness footer. This is exactly how a customer would phrase a login-history investigation; the prompt also implicitly tests that the agent picks `org` scope (where Identity Server login events live)._ |
| `audit_org_export_verify_e2e` | Insider — fixable | Same as `audit_export_verify_e2e` plus "This is ORG scope, not tenant. Do NOT pass `--tenant-id` (org silently ignores it)." | "I need a 3-day org-wide audit export for compliance — membership changes, license activity, tenant lifecycle events. Whole UTC days ending two days back to stay clear of the long-term-store lag. Save it to `./audit-org-window.zip`." (Lets scope be inferred from the event categories; the "don't pass `--tenant-id`" guidance is a skill rule, not user voice.) |
| `audit_who_did_x_e2e` | Natural | "Find out who deleted the `Sales-Reports` folder on the active tenant in the last 7 days." + offline block. | _Already natural — keep the body, drop only the offline-harness footer. Classic "who did X" investigation in customer voice._ |

### Identity — onboarding & membership e2e

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `group_membership_management_e2e` | Insider — fixable | "Set up a new 'Invoice Processing Team' group containing the first two users in the org, verify membership, then remove the second user." | "Spin up an 'Invoice Processing Team' group, drop our first two users in, double-check they're members, then take the second one back out — I want to make sure my add/remove flow works before I roll this out for real." ("first two users in the org" is a test-fixture shortcut; the rewrite keeps the same shape but lets it sound like the user is dry-running their own process.) |
| `human_user_onboarding_e2e` | Natural | "Onboard john.doe@example.com (John Doe) and add them to the 'Automation Developer' group once provisioned." | _Already natural — keep the body, drop the automated-test footer. Realistic onboarding ask._ |
| `robot_account_onboarding_e2e` | Mixed | "Onboard an unattended invoice-processing robot ('smoke-e2e-bot' / 'Smoke E2E Bot') and add it to the 'Automation Users' group." | "Stand up an unattended robot account for our invoice-processing flow ('invoice-bot-01' / 'Invoice Bot 01') and add it to the 'Automation Users' group." (Only fix is renaming the obvious test-fixture name; the rest is fine.) |

## Notes for the PR description

- **Most prevalent issue: the offline-harness preamble.** 11 of 12 audit smoke/e2e tests carry the same 6-line "commands WILL fail / do NOT retry / do NOT login / do NOT troubleshoot" block. That's bleeding from the eval rig into the user voice. If the runner needs the agent to give up after one shot, that's a property of the success criteria (only fire once, accept any exit code), not something the user should be saying. Consider lifting it into a sandbox-level config rather than re-stating it inside each prompt.
- **Mostly clean once boilerplate is stripped.** Of the 20 prompts, only 5 have non-boilerplate insider content worth a real rewrite: the two `*_verify_e2e` exports (CLI-flag literacy + LTS-lag rationale), `audit_export_e2e` (numbered-step list), `audit_org_export_smoke` (literal "ORGANIZATION-level" caps + skill-rule recital), and `audit_org_events_smoke` (insider scope vocabulary).
- **Scope-language tension.** Several tests name `org` or `tenant` scope literally because that's the very thing under test. For investigation-style prompts (`audit_login_history_e2e`, `audit_who_did_x_e2e`, `audit_org_events_smoke`) the right move is to *describe the events* (joins, license changes, login attempts) and let the agent route to the correct scope — that's a more honest measurement of intent recognition. For `audit_sources_smoke` and the verify exports, the explicit scope is part of the assertion and should stay.
- **Two leftover test-fixture names** (`smoke-test-bot`, `Smoke Test App`, `smoke-e2e-bot`) tip off the agent that this is a smoke test. Cheap rename to realistic-sounding identities like `invoice-bot-01` / `InvoiceBot OAuth client` would close the gap without changing what's being measured.
- **The good news.** The identity-list prompts (`identity_list_users/groups/robot_accounts_smoke`) and the two open-investigation e2e tests (`audit_login_history_e2e`, `audit_who_did_x_e2e`) are textbook examples of natural-user phrasing — they could be templates for rewriting the rest.
