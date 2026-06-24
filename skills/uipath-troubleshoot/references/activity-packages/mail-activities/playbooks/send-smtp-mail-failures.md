---
confidence: medium
---

# Send SMTP Mail Message Failures

## Context

`UiPath.Mail.SMTP.Activities` `Send SMTP Mail Message` (`SendMail`) sends a message straight to an SMTP server with **MailKit** — no Outlook/desktop dependency. It builds the message (parsing addresses), connects (`Server`/`Port`/`SecureConnection`), optionally authenticates, and submits; success requires SMTP status `250`. Connection-time failures are wrapped by UiPath as `MailException` — `Cannot connect to the (SMTP) Mail Service. Please make sure that the provided connection details are correct for the SMTP protocol.` — with the **MailKit exception as the inner exception**.

> For connection failures, read the **inner exception type** under the `Cannot connect…` wrapper. Input/format errors are thrown directly before connecting.

What this looks like — production signatures grouped by surface:

- **Inputs / address format:** `System.FormatException` (malformed email address), `System.ArgumentException`, `System.ArgumentNullException`, `System.NullReferenceException`, `System.Collections.Generic.KeyNotFoundException`.
- **TLS:** `MailKit.Security.SslHandshakeException`.
- **SMTP command:** `MailKit.Net.Smtp.SmtpCommandException`.

What can cause it:

1. **Inputs / address format.** A `To`/`From`/`Cc`/`Bcc` value isn't a valid address → `FormatException` from address parsing (a missing `@`, stray spaces, a display name without `<>`, a delimiter mismatch when multiple recipients are passed). A required field (`From`, `Server`, body) is null/uninitialized → `ArgumentNullException`/`NullReferenceException`; an out-of-range/invalid argument → `ArgumentException`; a missing lookup key (account/config) → `KeyNotFoundException`.
2. **TLS handshake (`SslHandshakeException`).** `SecureConnection` doesn't match the port (`StartTls` for `587`, `SslOnConnect` for `465`); server certificate untrusted/expired; a failing CRL check (consider `IgnoreCRL`); or a protocol/cipher mismatch.
3. **SMTP command rejected (`SmtpCommandException`).** The server refused a command: **authentication required/failed**, **relay denied** (`5.7.x` — sender not allowed to relay / not authenticated), **recipient rejected** (`550` unknown/blocked address), **sender rejected**, or **message/size policy** violation. The exception carries the SMTP status code.

What to look for:

- **The exception type** (and inner type under `Cannot connect…`) selects the surface.
- **The SMTP status code** in an `SmtpCommandException` (`5.7.x` relay/auth, `550` recipient, `552/523` size) — picks the sub-cause — branch 3.
- **`Server`/`Port`/`SecureConnection`** vs the provider's documented SMTP settings — branch 2.
- **Recipient/sender address strings** and the multi-recipient delimiter — branch 1.
- **Whether auth is required** by the server and whether credentials/app-password/OAuth are set — branch 3.

## Investigation

1. **Capture the exact type, message, and any SMTP status code** from `uip or jobs get <job-key> --output json` → `Info`. For connection failures, note the inner MailKit type.
2. **Map to a surface:** Format/Argument/Null/KeyNotFound → inputs; `SslHandshakeException` → TLS; `SmtpCommandException` → command (read the status code).
3. **Inputs:** substitute runtime values for `To`/`From`/`Cc`/`Bcc` and find the malformed/missing one; check the multi-recipient separator.
4. **TLS:** compare `Server`/`Port`/`SecureConnection` with the provider's SMTP settings; check the certificate.
5. **Command:** decode the SMTP status — auth, relay, recipient, or size — and verify credentials/permissions accordingly.

## Resolution

- **Inputs / format:** validate and sanitize addresses before sending (`From`/`To`/`Cc`/`Bcc` must be well-formed; use the correct delimiter for multiple recipients); initialize required fields (`From`, `Server`, body); ensure any looked-up account/config key exists.
- **`SslHandshakeException`:** align `SecureConnection` with the port (`StartTls`/`587`, `SslOnConnect`/`465`); trust/replace an invalid certificate; set `IgnoreCRL` only when a CRL endpoint is genuinely unreachable.
- **`SmtpCommandException`** by status:
  - `5.7.x` relay/auth: authenticate (set credentials / app password / OAuth); use a server/account permitted to relay for the sender domain.
  - `550` recipient: correct the recipient address; confirm the mailbox exists/accepts mail.
  - sender rejected: use an authorized `From` for the relay.
  - size/policy: reduce attachment/message size under the server's limit.
- **Connection wrap (`Cannot connect to the (SMTP) Mail Service…`):** the inner type (TLS/timeout/socket) is the cause; fix per branch 2 or correct `Server`/`Port`/reachability.

## Anti-patterns (what NOT to do)

- **Retrying a `550`/relay/auth rejection.** These are deterministic policy errors; fix the address/credentials/relay rights. Retry only transient connection faults.
- **Splicing unvalidated user data into `To`/`From`.** Malformed addresses throw `FormatException` before sending; validate first.
- **Mismatching `SecureConnection` and port.** `StartTls` on `465` or `SslOnConnect` on `587` produces `SslHandshakeException`. Match the provider's documented pairing.
- **Disabling certificate validation to force TLS.** A security regression unless a CRL endpoint is genuinely unreachable.

## Prevention

- Validate recipient/sender addresses before sending; use the correct multi-recipient delimiter.
- Configure `Server`/`Port`/`SecureConnection` and authentication from the provider's documented SMTP settings; use app passwords / OAuth where required.
- Treat a non-`250` result as failure; surface the SMTP status rather than swallowing it.

## Related

- [get-imap-mail-messages-failures](./get-imap-mail-messages-failures.md) — the same MailKit TLS/connection surface for IMAP.
- [send-mailx-failures](./send-mailx-failures.md), [send-exchange-mail-failures](./send-exchange-mail-failures.md) — other send paths (Outlook/Graph/Gmail, EWS).
- [send-outlook-mail-failures](./send-outlook-mail-failures.md) — the SMTP/Graph fallback referenced there for unattended sends.
- [mail-activities overview](../overview.md) — package map and protocol connection models.
