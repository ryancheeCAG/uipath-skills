# Attended Re-authentication / Hardware-token Handoff Pattern

Design-altitude reference for portal automations where a step requires a login the robot **cannot** perform — a physical hardware 2FA token, smart card, biometric, or any interactive sign-in that cannot be scripted. The planner cites this pattern in the SDD; **`uipath-rpa` implements it.** This guide specifies the design contract, not the build.

## When it applies

The PDD's robot-attendance or signing-modality signals (see [pdd-analysis-guide.md](pdd-analysis-guide.md) — "Robot attendance", "Signing modality") indicate a human must complete authentication mid-process. Trigger words: `hardware token`, `smart card`, `physical 2FA`, `OTP device`, `biometric`, `human present for login`.

Distinguish from automatable factors first — do **not** apply this pattern when the second factor is a **soft** token (Google/Microsoft/Okta TOTP, SMS/email code the robot can read). Those are scripted inside `uipath-rpa` and need no human handoff. This pattern is for factors no software can supply.

## Verified primitives (UiPath)

- **Attended automations** run inside the user's interactive session under human supervision — a person is at the machine. ([docs](https://docs.uipath.com/robot/standalone/2024.10/admin-guide/attended-automations))
- **Interactive sign-in** lets the human authenticate the session; the canonical MFA pattern is *human logs in first, then hands off to the attended robot*. ([docs](https://docs.uipath.com/robot/standalone/2023.4/admin-guide/setting-up-interactive-sign-in))
- A **physical** token cannot be automated — the handoff is mandatory, not a fallback.

## Two design shapes

Pick per the PDD; default to **A** when the login is the very first step, **B** when authentication recurs or the session expires mid-run.

**A — Login-before-handoff (attended-first).** The human completes the token login, *then* starts/hands off to the attended robot, which inherits the authenticated session. Simplest; no in-process pause. Fits "human opens the portal each morning, then triggers the bot."

**B — Mid-run pause + resume (state-aware handoff).** The robot runs to the auth gate, **pauses** and surfaces a blocking prompt to the human ("complete the token login, then continue"), the human authenticates in the same session, and the robot **verifies the post-login state before resuming**. Fits a long run that hits a re-auth gate, or a session that expires partway.

## Handoff contract (what the SDD specifies)

For shape B, the SDD's §9 *Interactive Authentication / Re-auth Handoff* subsection pins down — at business altitude, no activities:

1. **Handoff point** — the process step where the robot pauses.
2. **Human action** — exactly what the person does (insert token, complete portal login).
3. **Resume condition / state anchor** — the observable post-login state the robot checks before continuing (authenticated URL reached, dashboard element present). **Load-bearing:** never resume blindly on a timer.
4. **No-completion behavior** — timeout, then abort with notification (`[DEFAULT]` 5-min wait unless the PDD states otherwise).
5. **Attendance** — Attended is mandatory; record it in §16 Robot type.

## Rules

1. **State-verify before resume.** The robot asserts the authenticated state anchor (element/URL) before the next step. A pause that resumes on a fixed delay is a defect — the human may not be done.
2. **Restart-safe surroundings.** The work *after* the gate must be idempotent / re-runnable, because a failed handoff aborts and reruns. Design the post-login loop to resume from the last committed item, not from scratch with duplicates.
3. **One gate, one contract.** If the process re-authenticates N times (session expiry), the same contract applies at each gate — describe it once and reference it; do not duplicate.
4. **Do not script the unscriptable.** Never design around "read the hardware token value" — it cannot be done. The factor is the human's.

## Routing boundary

| The SDD (planner) specifies | `uipath-rpa` implements |
|---|---|
| Where the gate sits in the process map (§2 node) | The pause mechanism (interactive prompt / form / message) |
| The handoff contract (§9 subsection) | The state-anchor selector / element check |
| Attended robot requirement (§16) | Retry/timeout activities, session handling |
| A re-auth test scenario (§17) | The test implementation |

Per Critical Rule 8, the planner does **not** name activities or describe the pause/resume implementation — it routes the build to `uipath-rpa`, citing this pattern.

## SDD placement

- **§2 Process Map** — show the handoff as an explicit node (e.g., `Pause: human token login` → `Verify authenticated`).
- **§9 Application Inventory** — the *Interactive Authentication / Re-auth Handoff* subsection carries the handoff contract (table in the RPA template).
- **§16 Deployment Environment** — Robot type = Attended; add a runtime prerequisite that a human operator is present.
- **§17 Testing Strategy** — a re-auth scenario (handoff completes → resumes; handoff times out → aborts cleanly).
