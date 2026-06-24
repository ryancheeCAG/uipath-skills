---
confidence: medium
---

# Move IMAP Mail Message To Folder Failures

## Context

`UiPath.Mail.IMAP.Activities` `Move IMAP Mail Message To Folder` (`MoveIMAPMailMessageToFolder`) moves a previously-fetched IMAP message to a destination folder over **MailKit**. It requires an authenticated IMAP session and a valid `MailMessage` input, then issues an IMAP `MOVE`/`COPY`+`STORE` against the destination mailbox.

What this looks like — the production signatures:

- `MailKit.Net.Imap.ImapCommandException` — **branch 1**: the IMAP server rejected the move command (destination folder doesn't exist, name invalid, or insufficient rights).
- `System.IO.IOException` — **branch 2**: the connection dropped or a socket error occurred mid-operation.
- (Design-time/validation: `You must provide a value for <property>` if `MailMessage` is not supplied.)

What can cause it:

1. **Command rejected (`ImapCommandException`).** The **destination folder does not exist** on the server (the activity creates nothing — the mailbox must already exist), the folder **name/path is wrong** (IMAP names are case-sensitive and use a server-specific hierarchy separator, often `/` or `.`; localized names differ), or the account **lacks rights** to write to the destination. The UiPath guard `Mail Folder does not exist for specified client.` covers the not-found case.
2. **Connection dropped (`IOException`).** The IMAP session was lost mid-move — server idle-timeout between fetch and move, network blip, or a half-open socket — so the `MOVE`/`COPY` fails with a socket/`IOException`.

What to look for:

- **The exception type** — `ImapCommandException` → branch 1; `IOException` → branch 2.
- **The destination folder name/path** vs the server's actual folder list (exact case, correct hierarchy separator) — branch 1.
- **The account's rights** on the destination mailbox (shared/other-user mailboxes) — branch 1.
- **Time/idle gap between fetching the message and moving it**, and connection stability — branch 2.

## Investigation

1. **Capture the exact type and message** from `uip or jobs get <job-key> --output json` → `Info`.
2. **Branch 1 (`ImapCommandException`):** list the server's folders and compare the destination string exactly (case + separator). Confirm the folder exists and the account can write to it.
3. **Branch 2 (`IOException`):** check whether a long gap or idle period separates the fetch and the move, and whether the connection is stable from the Robot host.

## Resolution

- **Branch 1 — `ImapCommandException` / folder not found:** use the destination folder's exact server name and hierarchy path (correct separator and case); create the mailbox on the server first if it doesn't exist (the activity won't); grant the account write rights to the destination (especially for shared mailboxes).
- **Branch 2 — `IOException` / dropped connection:** keep the session alive (move promptly after fetch; avoid long idle gaps), wrap the move in a `Retry Scope` to recover from transient socket drops, and ensure stable network/firewall access to the IMAP server from the Robot host.
- **Missing `MailMessage` (validation):** bind a valid fetched `MailMessage` to the activity; it must come from a `Get IMAP Mail Messages` on the same connection.

## Anti-patterns (what NOT to do)

- **Assuming the activity creates the destination folder.** It does not — a non-existent mailbox yields `ImapCommandException`. Create it server-side first.
- **Hardcoding a folder name with the wrong separator/case.** IMAP paths are server-specific (`Archive`, `INBOX/Archive`, `INBOX.Archive` differ). Use the server's exact name.
- **Long delay between fetch and move with no retry.** Idle-disconnect causes `IOException`; move promptly and retry transient drops.

## Prevention

- Resolve and validate the destination folder against the server's folder list before moving; pre-create it if needed.
- Move promptly after fetching on the same connection; wrap in a `Retry Scope` for transient socket errors.

## Related

- [get-imap-mail-messages-failures](./get-imap-mail-messages-failures.md) — the sibling IMAP read path; the source of the `MailMessage` and the shared connection/TLS surface.
- [mail-activities overview](../overview.md) — package map and protocol connection models.
