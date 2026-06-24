---
confidence: medium
---

# Save Mail Attachments Failures

## Context

`UiPath.Mail.Activities` `Save Attachments` / `Save Mail Attachments` (`SaveMailAttachments` / `SaveMailAttachmentsX`) downloads a message's attachments to a destination folder, optionally filtered by a filename filter and with an `Overwrite existing files` / `Exclude Inline Attachments` toggle. Writing the files to disk is the failure-prone step.

What this looks like — the production signature:

- `System.IO.IOException` (or its subclass `System.IO.PathTooLongException`) raised at the activity while writing an attachment. Message text comes from the OS/.NET (`The process cannot access the file because it is being used by another process.`, `The file '<name>' already exists.`, `There is not enough space on the disk.`, etc.). Download-stage failures are wrapped as `Error downloading attachments` (`SaveAttachmentsException`).

What can cause it:

- **Target file already exists and overwrite is off.** With `Overwrite existing files` disabled, re-saving an attachment with the same name throws `IOException` (file already exists).
- **Destination file locked / in use.** A previously-saved attachment is still open in another process (Excel, a PDF viewer, a prior step) — `being used by another process`.
- **Destination unavailable or full.** The output folder is a disconnected network share, a path the Robot user cannot write, or a full disk.
- **Path too long.** The destination path + attachment filename exceeds the OS limit → `PathTooLongException`.
- **Illegal characters in the filename filter** (`ArgumentException`, not IOException): `Illegal characters found in filter expression '<filter>'. The following characters are not allowed to appear in a file name: <chars> and are therefore not allowed in file filter expressions.` — a separate input-validation branch.

What to look for:

- **The exact `IOException` message** in `uip or jobs get <job-key> --output json` → `Info` — file-exists vs in-use vs disk-space vs path-too-long picks the branch.
- **`Overwrite existing files`** setting and whether the job reprocesses the same attachment names on re-run.
- **The destination folder** — local vs network share, writable by the Robot's user, and the combined path length (folder + longest attachment name).
- **Whether a downstream/previous step holds the file open** (the saved attachment is read immediately after).

## Investigation

1. **Capture the exact IOException message** from `Info`. If it is instead `ArgumentException` about illegal filter characters, jump to the filter fix.
2. **Inspect the destination and settings** in the `.xaml`: output folder expression, `Overwrite existing files`, filename filter, and whether the names collide across runs.
3. **Map the message to a condition:** already-exists → overwrite/naming; in-use → file lock; disk space / access denied → destination; path length → `PathTooLongException`.

## Resolution

- **File already exists:** enable `Overwrite existing files`, or write to a per-run subfolder / unique filename so names don't collide.
- **File in use / locked:** ensure no prior step keeps the file open (dispose readers, close the app), or save to a fresh path; add a short `Retry Scope` for transient locks.
- **Destination unavailable / full / access denied:** point at a local, writable folder; verify the Robot user's permissions and free space; map/validate the network share before saving.
- **Path too long:** shorten the destination folder or the saved filename (truncate/sanitize the attachment name); enable long-path support only as a last resort.
- **Illegal filter characters (`ArgumentException`):** remove disallowed filename characters from the filter expression — the filter is matched against file names, so the same character rules apply.

## Anti-patterns (what NOT to do)

- **Leaving overwrite off and re-running over the same names.** Idempotent re-runs then fail on the first existing file. Use per-run folders or overwrite deliberately.
- **Reading a saved attachment without releasing the handle, then saving again.** Self-inflicted file lock. Dispose before re-saving.
- **Swallowing the IOException and continuing.** Downstream steps assume the attachment is on disk; a silent miss produces a confusing later failure.

## Prevention

- Save to a unique per-run output folder; set `Overwrite existing files` intentionally.
- Validate the destination (writable, present, enough space) and the path length before the activity.
- Sanitize the filename filter against illegal filename characters.

## Related

- [save-mail-failures](./save-mail-failures.md) — the `Save Mail` FilePath / `ArgumentException` family.
- [for-each-emailx-failures](./for-each-emailx-failures.md) — attachment downloads while iterating a provider collection.
- [mail-activities overview](../overview.md) — package map.
