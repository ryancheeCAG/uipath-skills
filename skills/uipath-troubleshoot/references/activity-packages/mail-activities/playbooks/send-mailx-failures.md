---
confidence: medium
---

# Send Mail (SendMailX) Failures

## Context

`UiPath.Mail.Activities` `Send Mail` (`Business.SendMailX`) sends a message through whatever **mail connection** the enclosing scope supplies — Outlook (desktop COM or Graph-backed), Microsoft Graph (modern Outlook/o365 connection), or Gmail. The activity resolves the service from its `Account`/connection, validates against the email block-list governance, then calls the provider's send.

**Exception routing (load-bearing):** `SendMailX` wraps only *truly unexpected* errors (innermost `HResult == 0x8000FFFF`) into a `MailException` — `Cannot connect to Outlook. Your Microsoft Office installation may be corrupted. Repair or reinstall Microsoft Office and try again.` Everything else **propagates raw from the provider**, so the exception **type names the provider and layer**:

- `System.ObjectDisposedException` — **branch 1**: the mail connection/handle was disposed before or during the send.
- `Microsoft.Graph.ServiceException` — **branch 2**: a Microsoft Graph (modern Outlook/o365) API error.
- `Google.GoogleApiException` — **branch 3**: a Gmail API error.
- (`The Mail service is null.` means the `Account`/connection did not resolve — a configuration/binding miss, not a provider error.)

What this looks like:

- A raw `ObjectDisposedException` / `Microsoft.Graph.ServiceException` / `Google.GoogleApiException` at the `Send Mail` node — the message and any HTTP status/code come from the provider SDK.

What can cause it:

1. **Disposed connection (`ObjectDisposedException`).** `Send Mail` runs **outside the live connection scope** (the Outlook/connection scope already exited), a connection/handle is **reused after disposal**, or a parallel branch disposed the session while the send was in flight.
2. **Graph error (`Microsoft.Graph.ServiceException`).** The Graph call was rejected — throttling (HTTP 429), auth/permission (401/403 — token expired, missing `Mail.Send`, no access to a shared mailbox / `SendAs`), bad request (400 — malformed recipient/payload), or mailbox/folder not found (404).
3. **Gmail error (`Google.GoogleApiException`).** The Gmail API was rejected — auth/scope (`invalid_grant`, missing send scope), quota/rate limit (`rateLimitExceeded`, `userRateLimitExceeded`), invalid recipient, or a message exceeding size limits.

What to look for:

- **The exception type** — it directly selects the branch and the provider.
- **For branches 2/3, the provider status/error code** in the message (`429`, `401`/`403`, `400`, `404`; `rateLimitExceeded`, `invalid_grant`) — picks the sub-cause.
- **Scope/lifecycle of the connection** — whether `Send Mail` sits inside the connection/Outlook scope, whether the connection is reused across iterations, and whether any parallel/async branch could dispose it.
- **The `Account`/connection** binding and, for shared mailboxes, the `SendAs`/`From` and the granted permissions.

## Investigation

1. **Capture the exact exception type and provider code.** From `uip or jobs get <job-key> --output json` → `Info`: the type and message; for Graph/Gmail note the HTTP status / error reason in the text.
2. **Branch on the type.**
   - `ObjectDisposedException` → branch 1; go to step 3.
   - `Microsoft.Graph.ServiceException` → branch 2; read the status code.
   - `Google.GoogleApiException` → branch 3; read the error reason.
3. **For branch 1, trace the connection lifecycle** in the `.xaml`: confirm `Send Mail` runs while the connection scope is open, the handle is not reused after a prior scope exit, and no parallel branch disposes it.
4. **For branches 2/3, map the provider code** to throttling / auth / permission / bad-request / not-found and verify against the connection's identity and the recipient/mailbox.

## Resolution

- **Branch 1 — `ObjectDisposedException`:** Keep `Send Mail` inside the live connection/Outlook scope; do not store and reuse a connection/handle after its scope closes — re-acquire it per scope. Remove parallelism that disposes the session mid-send. If looping, ensure the connection outlives the loop or is re-opened each iteration.
- **Branch 2 — `Microsoft.Graph.ServiceException`:** by status —
  - `429` (throttling): add a `Retry Scope` with exponential backoff; reduce send rate / batch size.
  - `401`/`403` (auth/permission): refresh/reconnect the connection; ensure the app/user has `Mail.Send` and (for shared mailboxes) `Send As`/`Send on Behalf` and mailbox access.
  - `400` (bad request): fix the recipient/payload (valid addresses, non-empty required fields).
  - `404` (not found): correct the mailbox/`From`/folder identity.
- **Branch 3 — `Google.GoogleApiException`:** by reason —
  - auth/scope (`invalid_grant`, missing scope): reconnect the Gmail connection with the send scope granted.
  - quota/rate (`rateLimitExceeded`/`userRateLimitExceeded`): back off and retry; spread sends.
  - invalid recipient / size: validate addresses; reduce attachment/body size under Gmail limits.
- **`The Mail service is null.`:** the `Account`/connection is unset or didn't resolve — bind a valid connection and ensure the enclosing scope provides it.

## Anti-patterns (what NOT to do)

- **Treating every `SendMailX` failure as "Outlook is broken".** Only the wrapped `Cannot connect to Outlook…` message is the COM/Office case; `ObjectDisposedException`/Graph/Gmail are different layers with different fixes — read the type.
- **Blind-retrying a `400`/`403`.** Retries help `429`/transient only; auth/permission/bad-request need a real fix.
- **Reusing a connection handle across scopes.** Causes `ObjectDisposedException`; re-acquire per scope.

## Prevention

- Keep send activities within the connection scope's lifetime; don't cache disposed handles.
- Wrap provider sends in a `Retry Scope` tuned for `429`/transient errors only.
- Provision the connection identity with `Mail.Send` (+ shared-mailbox `Send As`) up front; validate recipients before sending.

## Related

- [outlook-application-card-failures](./outlook-application-card-failures.md) — the COM scope that supplies the connection; the `Cannot connect to Outlook…` wrap.
- [send-exchange-mail-failures](./send-exchange-mail-failures.md), [send-smtp-mail-failures](./send-smtp-mail-failures.md) — protocol-specific send paths.
- [o365-activities overview](../../o365-activities/overview.md), [gsuite-activities overview](../../gsuite-activities/overview.md) — the Graph and Gmail providers behind branches 2 and 3.
- [mail-activities overview](../overview.md) — package map and connection models.
