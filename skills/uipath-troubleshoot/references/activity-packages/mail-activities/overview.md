# Mail Activities

UiPath's mail activity packages — the **modern unified** `UiPath.Mail.Activities` and `UiPath.Mail.Exchange.Activities`, plus the **classic** per-protocol packages. These talk to a mail system from the Robot directly (desktop COM or a protocol/EWS connection) or, for the modern business activities, through whatever provider connection the enclosing scope supplies. Distinct from the pure-Graph **o365-activities** (`UiPath.MicrosoftOffice365.Activities`) and the Gmail **gsuite-activities** — though the modern business activities can route through those providers via a connection.

## Packages

- **Modern unified** — `UiPath.Mail.Activities`. Provider-agnostic business activities driven by the connection the enclosing scope supplies (Outlook desktop-COM or Graph, Gmail, or Exchange):
  - **Scope:** `Use Outlook 365` / `Outlook Application Card` (`Business.OutlookApplicationCard`) — opens the Outlook session for nested activities.
  - **Send / iterate:** `Send Mail` (`Business.SendMailX`), `For Each Email` (`Business.ForEachEmailX`).
  - **Files:** `Save Mail` (`SaveMail`), `Save Attachments` (`SaveMailAttachments`), `Create HTML Content` (`Business.CreateHtmlContent`).
- **Exchange (EWS)** — `UiPath.Mail.Exchange.Activities`: `Get Exchange Mail Messages` (`GetExchangeMailMessages`), `Send Exchange Mail Message` (`SendExchangeMail`). Talk to Exchange over EWS (`Microsoft.Exchange.WebServices`), Basic auth or OAuth/MSAL.
- **Classic Outlook (desktop COM)** — `UiPath.Mail.Outlook.Activities`. Drives the locally installed **Outlook desktop application** through COM interop: `Send Outlook Mail Message` (`SendOutlookMail`), `Get Outlook Mail Messages` (`GetOutlookMailMessages`), `Move Outlook Mail Message`, `Reply To Outlook Mail Message`, `Mark Outlook As Read`. Requires Outlook installed **and** a configured mail profile in the session the Robot runs as.
- **Classic protocol** — `UiPath.Mail.SMTP.Activities` (`Send SMTP Mail Message`), `UiPath.Mail.IMAP.Activities`, `UiPath.Mail.POP3.Activities`, `UiPath.Mail.EWS.Activities`. Protocol-level mail (MailKit / EWS) that talks to a mail server directly, no desktop client. `Send SMTP Mail Message` and `Get/Move IMAP Mail` live here.

## How the modern business activities run — exception routing (load-bearing)

The `UiPath.Mail.Activities` business activities resolve a mail service from the connection their scope supplies, then call the provider. **The exception type names the provider and layer** — diagnose from the type, not the activity display name:

- **Truly-unexpected** errors (innermost `HResult == 0x8000FFFF`) are wrapped as `UiPath.Mail.MailException` — `Cannot connect to Outlook. Your Microsoft Office installation may be corrupted…`. This is the COM/Office case **only**.
- **Provider exceptions propagate raw:** `Microsoft.Graph.ServiceException` (modern Outlook/o365 via Graph), `Google.GoogleApiException` (Gmail), `System.ObjectDisposedException` (a disposed/out-of-scope connection). Read the HTTP/provider status for the sub-cause.
- **Protocol connect failures** (MailKit IMAP/SMTP/POP3) are wrapped as `MailException` — `Cannot connect to the ({protocol}) Mail Service. Please make sure that the provided connection details are correct for the {protocol} protocol.` — with the **MailKit exception as the inner** (`SslHandshakeException`, `AuthenticationException`, `ImapCommandException`, `SmtpCommandException`, `TimeoutException`). The inner type is the discriminator.
- **Exchange/EWS failures** are wrapped as `UiPath.Mail.ExchangeException` (e.g. `Authentication failed for user <user>.`), though some EWS types (`ServiceVersionException`, `ServiceResponseException`, `ServiceRequestException`) and an aggregated bind error (`AggregateException`) surface raw.

A folder that can't be opened on a protocol/EWS connection surfaces as `Mail Folder does not exist for specified client.`

## How Outlook (desktop COM) activities run

The classic `Send Outlook Mail Message` (and the Outlook Application Card scope) does **not** call a mail API. It:

1. Attaches to (or launches) the local **OUTLOOK.EXE** via COM interop, under the Windows user the Robot runs as.
2. Uses that user's default (or a named) **Outlook profile / account** to compose and send the message through the Outlook Object Model.
3. Returns when Outlook accepts the item into the Outbox / Sent Items.

Because the call goes through the desktop application, failures cluster around the **COM layer** (Outlook installed/registered, process bitness, orphaned `OUTLOOK.EXE`, New Outlook removing the COM API), the **session/UI** (a security prompt, Work Offline, or Outlook already open in another session), and the **inputs** (uninitialized `To`/`Subject`/`Body` or a bad attachment path). This makes the Outlook COM activities fragile on unattended Robots, where there is no interactive desktop to dismiss a prompt.

> For unattended or server-side mail with no Outlook install, prefer **Send SMTP Mail Message** (`UiPath.Mail.SMTP.Activities`) or the modern Graph **o365-activities** — both avoid the desktop COM dependency entirely.

## Common Failure Families

- **COM cast / library not registered** — `Unable to cast COM object …` / `Library not registered` (`REGDB_E_CLASSNOTREG`, `TYPE_E_LIBNOTREGISTERED`). Outlook not installed/registered, a process-vs-Outlook **bitness** mismatch, corrupted Office registry/type-library, an orphaned `OUTLOOK.EXE`, or a host flipped to **New Outlook**.
- **Timeout / hang** — the activity blocks until `TimeoutMS` elapses. A hidden security prompt ("A program is trying to send an email message on your behalf"), Outlook in **Work Offline** mode, or a slow first-launch of the profile.
- **Uninitialized input** — `Object reference not set to an instance of an object` from a null `To`/`Subject`/`Body` variable or an empty/null attachment path.
- **TLS / connection (protocol)** — `SslHandshakeException` (port/`SecureConnection` mismatch, untrusted cert), `TimeoutException` (host/port unreachable), `AuthenticationException` (wrong creds / app-password / OAuth) — wrapped in `Cannot connect to the ({protocol}) Mail Service…`.
- **SMTP/IMAP command rejected** — `SmtpCommandException` (relay/auth/recipient, by SMTP status) / `ImapCommandException` (folder doesn't exist, rights).
- **Exchange (EWS)** — `ServiceVersionException` (feature needs a newer `ExchangeVersion`), `ServiceResponseException`/`ServiceRequestException` (request rejected/transport), `MsalClientException` (OAuth), `AggregateException` (per-message bind), wrapped as `ExchangeException`.
- **File I/O** — `ArgumentException` (illegal `FilePath`/HTML-resource path) and `IOException`/`PathTooLongException` (saving mail/attachments: file exists, locked, disk, path length).

## Package

NuGet: `UiPath.Mail.Activities` (modern business activities + Outlook Application Card + file activities), `UiPath.Mail.Exchange.Activities` (EWS), `UiPath.Mail.Outlook.Activities` (desktop COM), `UiPath.Mail.SMTP.Activities` (SMTP), `UiPath.Mail.IMAP.Activities` / `UiPath.Mail.POP3.Activities` / `UiPath.Mail.EWS.Activities` (protocol). Outlook COM activities require Outlook installed and a profile on the Robot host; protocol/EWS activities require only network access to the mail server; the modern business activities require the connection their scope supplies.
