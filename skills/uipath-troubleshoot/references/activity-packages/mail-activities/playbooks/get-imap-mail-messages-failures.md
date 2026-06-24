---
confidence: medium
---

# Get IMAP Mail Messages Failures

## Context

`UiPath.Mail.IMAP.Activities` `Get IMAP Mail Messages` (`GetIMAPMailMessages`) connects to an IMAP server with **MailKit**, authenticates (password/app-password or OAuth2), opens a folder, and reads messages. **MailKit** connection faults (TLS/auth/protocol) are wrapped by UiPath as `MailException` — `Cannot connect to the (IMAP) Mail Service. Please make sure that the provided connection details are correct for the IMAP protocol.` — with the **MailKit exception as the inner exception**; the inner type is the discriminator. The exception to this is the activity's own **`TimeoutMS` guard**, which throws a **raw `System.TimeoutException`** (`The operation has timed out.`) directly from `GetMailActivity` (`TaskExtensions.TimeoutAfter`) — it is *not* wrapped in the `Cannot connect…` message.

> For TLS/auth/protocol faults, read the **inner exception type** under the `Cannot connect…` wrapper — it names the actual fault. A bare `System.TimeoutException: The operation has timed out.` is the separate `TimeoutMS`-guard signature (branch 2).

What this looks like — the production signatures (as the inner/raised type):

- `MailKit.Security.SslHandshakeException` (inner, under `Cannot connect…`) — **branch 1 (TLS)**.
- `System.TimeoutException` — `The operation has timed out.`, **raised raw** by the `TimeoutMS` guard — **branch 2 (timeout)**.
- `MailKit.Security.AuthenticationException` (inner, under `Cannot connect…`) — **branch 3 (auth)**.
- `MailKit.Net.Imap.ImapProtocolException` (inner, under `Cannot connect…`) — **branch 4 (protocol)**.
- (`Mail Folder does not exist for specified client.` if the configured folder can't be opened.)

> **Verified (repro, .NET 8):** `Server=imap.gmail.com`, `Port=143`, `SecureConnection=SslOnConnect`, `TimeoutMS=15000` → `System.TimeoutException: The operation has timed out.` raised raw at `GetMailActivity` — the SSL-on-connect attempt against the plaintext port hangs until the guard fires. A mismatched `SecureConnection`/port can surface as this timeout rather than a fast `SslHandshakeException`.

What can cause it:

1. **TLS handshake (`SslHandshakeException`).** The `SecureConnection` mode doesn't match the port (e.g. `SslOnConnect` on `143`, or `StartTls` on `993`), the server certificate is self-signed / untrusted / expired, a CRL check fails (consider `IgnoreCRL`), or there's a TLS protocol/cipher mismatch.
2. **Timeout (`TimeoutException`).** The connect/read exceeds `TimeoutMS` and the activity's guard throws. Causes: host or port unreachable (wrong `Server`/`Port`, firewall/proxy), a slow/down server, **or** a `SecureConnection`/port mismatch that makes the handshake hang instead of failing fast (e.g. `SslOnConnect` against a plaintext port — verified to time out rather than raise `SslHandshakeException`).
3. **Authentication (`AuthenticationException`).** Wrong username/password; the provider requires an **app password** (Gmail / Office365 with MFA) rather than the account password; an invalid/expired OAuth2 token; or the account is locked / IMAP access disabled.
4. **Protocol (`ImapProtocolException`).** The server returned a malformed/unexpected response or dropped the connection mid-command — an incompatible server, a proxy mangling IMAP, or a transient server fault.

What to look for:

- **The inner exception type** under the `Cannot connect…` wrapper — selects the branch.
- **`Server` / `Port` / `SecureConnection`** vs the provider's documented values (`993` + SSL/TLS, `143` + STARTTLS) — branches 1/2.
- **Auth model** — password vs app-password vs OAuth2, MFA on the account, and whether IMAP is enabled for the mailbox — branch 3.
- **`IgnoreCRL`** and the certificate validity — branch 1.

## Investigation

1. **Capture the raised + inner exception** from `uip or jobs get <job-key> --output json` → `Info`. Note the inner MailKit type.
2. **Branch on the inner type** (Ssl / Timeout / Authentication / Protocol).
3. **Branches 1/2:** check `Server`/`Port`/`SecureConnection` against the provider's IMAP settings; verify the host:port is reachable from the Robot host.
4. **Branch 3:** confirm the credential type the provider requires (app password / OAuth2), whether MFA is on, and that IMAP is enabled for the mailbox.
5. **Branch 4:** check for a proxy/middlebox altering IMAP and whether the failure is transient (retry succeeds).

## Resolution

- **Branch 1 — `SslHandshakeException`:** align `SecureConnection` with the port (`SslOnConnect`/`Auto` for `993`, `StartTls` for `143`); trust/replace an invalid certificate; if a CRL endpoint is unreachable in a locked-down network, set `IgnoreCRL` (deliberately).
- **Branch 2 — `TimeoutException`:** correct `Server`/`Port`; open firewall/proxy access from the Robot host; raise the connect timeout only if the server is legitimately slow.
- **Branch 3 — `AuthenticationException`:** use an **app password** where the provider requires it (Gmail/Office365 + MFA) or a valid OAuth2 token; enable IMAP for the mailbox; verify the username is the full email address.
- **Branch 4 — `ImapProtocolException`:** bypass/repair any IMAP-altering proxy; retry transient faults with backoff; confirm the server speaks standard IMAP.
- **Folder not found (`Mail Folder does not exist…`):** use the server's exact folder name/path (IMAP folder names are case- and separator-sensitive; localized names differ).

## Anti-patterns (what NOT to do)

- **Diagnosing from the outer `Cannot connect…` text alone.** It's the same wrapper for TLS, timeout, auth, and protocol — the **inner type** is the cause.
- **Setting `IgnoreCRL`/disabling cert validation to "make TLS work".** Only valid when a CRL endpoint is genuinely unreachable; otherwise fix the certificate. Disabling validation is a security regression.
- **Using the account password where an app password is required.** Gmail/Office365 with MFA reject it as `AuthenticationException`.

## Prevention

- Configure `Server`/`Port`/`SecureConnection` from the provider's documented IMAP settings.
- Use app passwords or OAuth2 per the provider; confirm IMAP is enabled for the mailbox.
- Reference folders by their exact server names.

## Related

- [move-imap-mail-message-to-folder-failures](./move-imap-mail-message-to-folder-failures.md) — the sibling IMAP move path (folder/command errors).
- [send-smtp-mail-failures](./send-smtp-mail-failures.md) — the same MailKit TLS/connection surface for SMTP.
- [mail-activities overview](../overview.md) — package map and protocol connection models.
