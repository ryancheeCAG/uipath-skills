---
confidence: medium
---

# Send Exchange Mail Failures

## Context

`UiPath.Mail.Exchange.Activities` `Send Exchange Mail Message` (`SendExchangeMail`) builds an `EmailMessage` and sends (or saves to Drafts) over **EWS** via an `ExchangeService`. It connects to the Exchange endpoint (explicit Server URL or autodiscover), authenticates (Basic or OAuth/MSAL), validates inputs, attaches files, and submits. The wide range of production exceptions clusters into three surfaces: **connection/auth**, **inputs**, and **attachments**.

What this looks like — production signatures by surface:

- **Connection / auth / endpoint:** `System.UriFormatException` (malformed Server/EWS URL), `Microsoft.Identity.Client.MsalClientException` (OAuth token acquisition failed), `Microsoft.Exchange.WebServices.Data.ServiceRequestException` (EWS request transport failed), `UiPath.Mail.ExchangeException` (`Authentication failed for user <user>.` and other wrapped EWS/connection errors).
- **Inputs:** `System.NullReferenceException`, `System.ArgumentNullException`, `System.ArgumentException`, `System.Collections.Generic.KeyNotFoundException`.
- **Attachments:** `System.IO.FileNotFoundException`.

What can cause it:

1. **Connection / auth / endpoint.**
   - `UriFormatException` — the configured **Exchange Server / EWS URL** is malformed (missing scheme, stray characters, a hostname where a full URL is expected).
   - `MsalClientException` — **OAuth/MSAL** token acquisition failed: wrong client/tenant id, missing app permissions/consent, bad authority, or no cached token for an unattended identity.
   - `ServiceRequestException` — the EWS request could not complete: endpoint unreachable, TLS failure, or **autodiscover** could not locate the endpoint.
   - `ExchangeException` — wrong credentials / wrong-user token (`Authentication failed for user <user>.`).
2. **Inputs.** A required field (`To`/`From`/`Subject`/account/connection) is null or invalid: an uninitialized variable (`NullReferenceException`), a null required argument (`ArgumentNullException`), a malformed value such as a bad address (`ArgumentException`), or a missing lookup key — an account/folder/identity key that isn't present (`KeyNotFoundException`).
3. **Attachments.** An attachment path points to a file that doesn't exist at runtime (`FileNotFoundException`) — moved, never produced upstream, or dev-only.

What to look for:

- **The exception type** maps to the surface; the message narrows the cause.
- **Server URL vs autodiscover** configuration — `UriFormatException`/`ServiceRequestException` are endpoint issues.
- **Auth mode** (Basic vs OAuth) and the MSAL app config (client/tenant id, permissions, consent) — `MsalClientException`/`ExchangeException`.
- **Each required input** (`To`/`From`/`Subject`/account) traced to its producer — branch 2.
- **Attachment paths** resolved on the **Robot host** — branch 3.

## Investigation

1. **Capture the exact type and message** from `uip or jobs get <job-key> --output json` → `Info`.
2. **Map to a surface:** URL/MSAL/ServiceRequest/Exchange-auth → connection/auth; Null/ArgumentNull/Argument/KeyNotFound → inputs; FileNotFound → attachment.
3. **Connection/auth:** validate the Server URL format (or that autodiscover resolves), the MSAL app registration (ids, permissions, consent), and the credential/identity in `Authentication failed for user <user>.`.
4. **Inputs:** substitute runtime values for `To`/`From`/`Subject`/account; find the null/malformed one or the missing lookup key.
5. **Attachment:** confirm each attachment path exists where the job ran and that the upstream producer completed first.

## Resolution

- **`UriFormatException`:** provide a well-formed EWS URL (`https://<host>/EWS/Exchange.asmx`) or enable/repair autodiscover; remove stray characters.
- **`MsalClientException`:** fix the OAuth app — correct client/tenant id and authority, grant and consent the required permissions, ensure a token is obtainable for the (unattended) identity.
- **`ServiceRequestException`:** make the endpoint reachable (network/TLS), correct the URL or autodiscover; retry transient transport errors with backoff.
- **`ExchangeException` (`Authentication failed for user <user>.`):** fix credentials / use the correct identity; the message names the failing user.
- **Inputs (`NullReference`/`ArgumentNull`/`Argument`/`KeyNotFound`):** initialize and validate `To`/`From`/`Subject`/account before the activity; use valid email address formats; ensure any account/folder/identity key the activity looks up actually exists.
- **`FileNotFoundException`:** ensure the attachment file exists at the referenced path on the Robot host (order the producing step first; guard with `Path Exists`).

## Anti-patterns (what NOT to do)

- **Retrying an auth/URL/input error.** Retries help transient `ServiceRequestException` only; `MsalClientException`/`UriFormatException`/input errors need a real fix.
- **Passing a bare hostname as the EWS URL.** Provide the full `…/EWS/Exchange.asmx` URL or rely on configured autodiscover.
- **Referencing a dev-machine attachment path.** Validate attachments on the host that runs the job.

## Prevention

- Configure a valid EWS endpoint (or autodiscover) and an OAuth app with the right permissions/consent up front; prefer OAuth as Basic auth is deprecated.
- Validate `To`/`From`/`Subject` and attachment paths before sending; guard optional attachments with `Path Exists`.

## Related

- [get-exchange-mail-messages-failures](./get-exchange-mail-messages-failures.md) — the sibling EWS read path; same connection/auth surface.
- [send-mailx-failures](./send-mailx-failures.md), [send-smtp-mail-failures](./send-smtp-mail-failures.md) — other send paths (Graph/Gmail, SMTP).
- [o365-activities overview](../../o365-activities/overview.md) — modern Graph send, the migration target away from EWS.
- [mail-activities overview](../overview.md) — package map and connection models.
