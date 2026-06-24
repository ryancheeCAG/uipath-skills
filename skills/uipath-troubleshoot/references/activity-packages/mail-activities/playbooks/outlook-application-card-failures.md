---
confidence: medium
---

# Outlook Application Card Failures

## Context

`UiPath.Mail.Activities` `Use Outlook 365` / `Outlook Application Card` (`Business.OutlookApplicationCard`) is the **scope** activity that opens the local **Outlook desktop** through COM interop and hands a connection to the child mail activities nested inside it (`Send Mail`/`SendMailX`, `For Each Email`, `Save Mail`, etc.). It attaches to (or launches) `OUTLOOK.EXE` under the Robot's Windows user, resolves the configured **account**, and runs its body. Failures happen while opening or binding that COM session — before any child activity runs.

What this looks like — the two production signatures:

- `System.Runtime.InteropServices.COMException` (e.g. `Library not registered`, `REGDB_E_CLASSNOTREG`, `Unable to cast COM object…`) at the card — **branch 1 (COM layer)**.
- `System.SystemException` at the card, message `Cannot open Outlook. Outlook is already open in another session. Close all open instances of Outlook.` — **branch 2 (session conflict)**. The card may also throw `The account <name> could not be found.` (account not resolvable) and, at design time, `The card is not configured or value is not available at design time.`

What can cause it:

1. **COM layer (`COMException`).** Outlook desktop **not installed** on the Robot host (the card needs the client, not just a mailbox); a **bitness mismatch** between the Robot process and the installed Outlook; a **corrupted Office registry / type library** (common after an Office update); an **orphaned `OUTLOOK.EXE`** holding the COM server; or the host was flipped to **New Outlook**, which removes the Desktop COM API entirely.
2. **Session conflict / account (`SystemException`).** Outlook is **already open in another Windows session** (e.g. an interactive user's session while the Robot runs unattended), so the card cannot attach — `Outlook is already open in another session`. Or the configured **account name does not match** any profile under the Robot's user (`The account <name> could not be found.`).

What to look for:

- **The exception class** — `COMException` → branch 1; `SystemException` with "already open in another session" → branch 2.
- **Outlook install + bitness on the Robot host** (`File > Account > About Outlook` for bitness) — load-bearing for branch 1.
- **Whether another Outlook session is running** for a different user on the host, and whether the run is **unattended** — load-bearing for branch 2.
- **Classic vs New Outlook** on the host — New Outlook has no COM API; a recent toggle is a frequent regression.
- **The card's `Account`** value vs the profiles configured for the Robot's Windows user.

## Investigation

1. **Capture the exact error, account, and host.** From `uip or jobs get <job-key> --output json` → `Info`: the exception class and message. From the `.xaml`: the card's `Account` and whether children depend on a specific mailbox. From the job: the Robot **host** and attended/unattended mode.
2. **Branch on the signature.**
   - `COMException` / cast / `Library not registered` → branch 1; go to step 3.
   - `SystemException` "already open in another session" or `The account … could not be found.` → branch 2; go to step 4.
3. **Confirm branch 1 (COM layer).** Verify desktop Outlook is installed on the **Robot host** and note its bitness vs the Robot process. Check for an orphaned `OUTLOOK.EXE` and whether the host is on **New Outlook** (no COM). A botched Office update corrupting the type library produces the cast / not-registered error.
4. **Confirm branch 2 (session conflict / account).** Determine whether Outlook is already running in another user's session on the host (the card cannot share it), and whether the run is unattended. Compare the card's `Account` against the profiles available to the Robot's Windows user.

## Resolution

- **Branch 1 — COM layer:**
  - Install **desktop Outlook** on every Robot host running the process; match **bitness** to the Robot process; run an Office **Quick Repair** if the type library is corrupted; clear any orphaned `OUTLOOK.EXE` before the run.
  - If the host is on **New Outlook**, toggle back to **Classic Outlook** (New Outlook has no Desktop COM API), or migrate to the modern Graph **o365-activities** which need no desktop client.
- **Branch 2 — session conflict / account:**
  - Ensure no competing **Outlook session** is open under another user on the host; for unattended runs, dedicate the host or run in the same session that owns Outlook.
  - Set the card's `Account` to a profile that exists for the Robot's Windows user; verify the account name matches exactly.
- **Prefer Graph for unattended.** When the automation does not specifically need the desktop client, replace the card + child activities with the modern Graph **o365-activities** (`UiPath.MicrosoftOffice365.Activities`) — OAuth, no COM, no session/bitness fragility.

## Anti-patterns (what NOT to do)

- **Running the card unattended against a host with no Outlook / on New Outlook.** It requires the Classic desktop client and a profile; use Graph o365-activities instead.
- **Sharing one Outlook install across an interactive user and the Robot.** The "already open in another session" error is structural — separate the sessions or move to Graph.
- **Lowering Outlook security/programmatic-access by hand on each host.** Brittle and a security regression; fix install/bitness/session instead.

## Prevention

- Reserve the Outlook Application Card for **attended** desktop automations that genuinely need the user's Outlook; default unattended mail to Graph **o365-activities** or **SMTP**.
- Provision Robot hosts with matching-bitness **Classic** Outlook and a profile for the Robot's user; pin Outlook to Classic to avoid the New Outlook regression.

## Related

- [send-mailx-failures](./send-mailx-failures.md) — child `Send Mail` failures inside the card scope.
- [send-outlook-mail-failures](./send-outlook-mail-failures.md), [get-outlook-mail-failures](./get-outlook-mail-failures.md) — the classic Outlook COM activities; same COM surface (install, bitness, New Outlook).
- [o365-activities overview](../../o365-activities/overview.md) — modern Graph/OAuth mail, the preferred unattended path.
- [mail-activities overview](../overview.md) — package map and connection models.
