# Final Resolution

---

**Root Cause:** The `SendStatusReport` process faults in its **Send SMTP Mail
Message** activity (`UiPath.Mail.SMTP.Activities.SendMail`, package
`UiPath.Mail.Activities`) with `System.FormatException: The specified string is
not in the form required for an e-mail address.` The activity's `To` recipient
is the literal string **`finance team distribution list`** — a human
description, not a valid e-mail address. While **building** the message,
`MailMessageBuilder.AddRecipientsToMail` → `MailAddressCollection.ParseValue` →
`MailAddressParser.TryParseAddress` rejects it. The failure happens at
**message construction, before any SMTP connection is attempted** — no server,
TLS, or authentication is involved.

This maps to the **Send SMTP Mail Message failures** playbook, the
**Inputs / address format** branch —
`references/activity-packages/mail-activities/playbooks/send-smtp-mail-failures.md`.

**What went wrong:** The `SendStatusReport` job (started 2026-06-24T09:25:55Z)
dispatched and ran cleanly (`Pending → Running → Faulted`), then faulted ~11
seconds later when `Send SMTP Mail Message` tried to parse its recipient list
and the `To` value was not a parseable address.

**Why:** `To="finance team distribution list"` contains spaces and no `@`/domain
— it is not a valid RFC address (nor a semicolon-separated list of addresses).
`System.Net.Mail` address parsing throws `FormatException` as the activity
assembles the `MailMessage`. The stack is entirely in the address-builder
(`MailAddressParser` / `MailMessageBuilder.AddRecipientsToMail`); the
`TimeoutAfter`/`SendMailActivity` frames are just the activity's outer async
wrapper — there is **no** network/connect frame, confirming the fault precedes
any send.

This is **NOT** a TLS/SSL handshake problem, **NOT** an authentication or
credential failure, **NOT** an SMTP server outage or relay rejection, and
**NOT** a connect timeout — the activity never reached the server. The `Server`
(`smtp.gmail.com`) and `Port`/`SecureConnection` (`587`/`StartTls`) are fine and
irrelevant to this fault.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: `SendStatusReport` — Faulted at 2026-06-24T09:26:06Z (folder Shared, key `defb8e05-e36b-4c36-bf11-0b4d08ce6cd1`), host `MOCK-HOST`, identity `newrobot` (Unattended)
- `or jobs get` `Info` / `or jobs logs --level Error`: `System.FormatException: The specified string is not in the form required for an e-mail address.` at `SendMail "SendMail"`, frames into `MailAddressParser.TryParseAddress` → `MailMessageBuilder.AddRecipientsToMail`
- `or jobs history`: `Pending → Running → Faulted` (clean dispatch; fault is in execution)

### Mail Activities (Surface / Root Cause)
- Activity (from `Main.xaml`): `SendMail` (`UiPath.Mail.SMTP.Activities`)
- Config (from `Main.xaml`): `To="finance team distribution list"` (the
  malformed recipient), `From="sender@test.com"`, `Server="smtp.gmail.com"`,
  `Port="587"`, `SecureConnection="StartTls"`
- The `To` value is a description, not an address — `MailAddressParser` rejects
  it before connecting.

---

**Immediate fix (correct the recipient input):**

1. **Set `To` to a valid e-mail address** (or a semicolon-separated list of
   addresses) — e.g. resolve "finance team distribution list" to its actual
   address `finance-dl@yourcompany.com`.
   - **Where:** the `Send SMTP Mail Message` activity in `Main.xaml`.
   - **Who:** RPA developer.
2. **Validate recipient inputs before SendMail.** If `To`/`Cc`/`Bcc` are
   data-driven (asset, queue, config), guard them — verify each entry parses as
   an address (or wrap the send in Try Catch) so a bad value is caught with a
   clear message instead of faulting the job.

**Do NOT** change the `Server`/`Port`/`SecureConnection`, credentials, or TLS
mode — none of those are the cause; the message never reached the server.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `Send SMTP Mail Message` `To` is a malformed address (`"finance team distribution list"`), so address parsing throws `FormatException` at message build, before connecting | High | Confirmed | Yes | `System.FormatException` at `MailAddressParser.TryParseAddress`/`MailMessageBuilder.AddRecipientsToMail` (`or jobs get`/`logs`) + `To="finance team distribution list"` in `Main.xaml` | Set `To` to a valid address / list; validate recipients before send |
| H2 | TLS/SSL handshake or SecureConnection mismatch | Low | Rejected | No | Stack has no TLS/connect frame; fault is in address parsing, before connect | n/a |
| H3 | Authentication / credential failure | Low | Rejected | No | No auth frame / AuthenticationException; never reached the server | n/a |
| H4 | SMTP server outage / relay rejection / connect timeout | Low | Rejected | No | No SmtpCommandException/TimeoutException; fault precedes the connection | n/a |

---

Would you like help applying the fix — correcting the `To` value and adding a
recipient-validation guard before `Send SMTP Mail Message`? I can also clean up
the `.local/investigations/` folder if you no longer need it.
