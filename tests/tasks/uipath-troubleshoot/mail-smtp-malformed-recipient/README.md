# Mail SMTP Send — Malformed Recipient (FormatException)

Replays staging job `412aeed8-a277-4e78-bf8f-57a8c098d4a0` (`SendStatusReport`,
folder Shared). Fault: `System.FormatException: The specified string is not in
the form required for an e-mail address.` raised by the **Send SMTP Mail
Message** activity (`UiPath.Mail.SMTP.Activities.SendMail`) while building the
message. Maps to `mail-activities/playbooks/send-smtp-mail-failures.md` —
**Inputs / address format** branch.

## What this scenario uncovers

**Root Cause:** The `Send SMTP Mail Message` activity's `To` is the literal
string **`finance team distribution list`** — a human description, not a valid
e-mail address. `System.Net.Mail` address parsing
(`MailAddressParser.TryParseAddress` → `MailMessageBuilder.AddRecipientsToMail`)
rejects it at **message construction, before any SMTP connection** — so no
server, TLS, or auth is involved. The fix is to set `To` to a valid address (or
semicolon-separated list) and validate recipient inputs before the send.

This is **not** a TLS/SSL handshake problem, **not** auth, **not** a server
outage/relay rejection, and **not** a connect timeout — the activity never
reached the server. (`Server=smtp.gmail.com`, `Port=587`, `StartTls` are fine
and irrelevant to this fault.)

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | snapshot of the failing `MailRepro` project — `Send SMTP Mail Message` with `To="finance team distribution list"`, project type Windows |
| `fixtures/mocks/responses/*.json` | **real** `uip` captures from `.local/investigations/raw`, scrubbed |
| `fixtures/mocks/responses/manifest.json` | dispatch table (first-match) |

The decisive evidence:

1. `or jobs get` / `or jobs logs --level Error` → `System.FormatException: The
   specified string is not in the form required for an e-mail address.` at
   `SendMail`, frames into `MailAddressParser.TryParseAddress` →
   `MailMessageBuilder.AddRecipientsToMail` — **no TLS/connect frame**.
2. `or jobs history` → `Pending → Running → Faulted` (clean dispatch; fault is
   in execution).
3. `process/Main.xaml` → `To="finance team distribution list"` — the malformed
   recipient.

## Provenance / scrub

Captured from a real staging fault. Scrubbed: host → `MOCK-HOST`, account →
`UIPATH\REPLACEMENT_USER`, personal-workspace email → `original_email@test.com`.
Error texts, job key (`412aeed8-…`), and folder key (`defb8e05-…`) kept verbatim.

## Success criteria

Scores the conclusion, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent matched `send-smtp-mail-failures` **Inputs / address format** branch and
  reached the same root cause as `RESOLUTION.md`: the malformed `To` recipient
  (`finance team distribution list`) fails address parsing before any connect.
- Conclusion recommends a valid-address fix / recipient validation and must NOT
  land on a TLS/SSL, auth, server-outage, or timeout cause.

## Sibling scenario

`mail-imap-timeout` covers the *connection-time* IMAP fault (raw
`TimeoutException` from the `TimeoutMS` guard). This SMTP scenario covers the
*input-validation* fault (`FormatException` before connect) — a deliberately
distinct activity, exception class, and playbook branch.
