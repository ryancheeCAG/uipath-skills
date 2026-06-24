---
confidence: high
---

# Save Mail Failures

## Context

`UiPath.Mail.Activities` `Save Mail` (`SaveMail`) writes a `System.Net.Mail.MailMessage` to disk as an `.eml` (MIME) file. Inputs: `MailMessage` (the message to save) and `FilePath` (destination). When `FilePath` has no extension, the activity generates a filename from the message subject and appends it. The write goes through `MimeMailService.SaveMail` (`mimeMessage.WriteTo(filePath)`).

What this looks like — the production signature for this activity is:

- `System.ArgumentException` raised at the `Save Mail` node (often `Illegal characters in path.`, `The path is not of a legal form.`, or an empty-path message from `System.IO`).

What can cause it:

- **Invalid `FilePath`.** The resolved path contains characters illegal on the target OS (`< > : " | ? *` on Windows, or control chars), is empty/whitespace after expression resolution, is a malformed/reserved name (`CON`, `NUL`, a bare drive letter), or mixes separators in a way the `System.IO` path APIs reject. `Path.GetExtension` / `FileInfo` throw `System.ArgumentException` before any bytes are written.
- **Subject-derived filename with no folder.** When `FilePath` is only a filename (no directory) and the subject yields illegal filename characters, the generated `<subject>.eml` is rejected.

What to look for:

- **The exact `ArgumentException` message** in `uip or jobs get <job-key> --output json` → `Info` — `Illegal characters in path` / `path is not of a legal form` / empty path confirms the input is malformed, not the message object.
- **The `FilePath` expression** in the workflow source — literal vs expression-bound, whether it resolves to a directory or a full filename, and whether any upstream value (a subject, a customer name, a timestamp) is concatenated into it unsanitized.
- **Distinguish from a *too-long* path** — that surfaces as `Cannot save the file because the path is too long.` (the `SaveMailX` guard) or `System.IO.PathTooLongException`, not `ArgumentException`. Different fix (shorten the path), see [save-mail-attachments-failures](./save-mail-attachments-failures.md) for the IOException family.

## Investigation

1. **Capture the exact error and the `FilePath`.** From `uip or jobs get <job-key> --output json` → `Info`: confirm the type is `System.ArgumentException` and read the message. From the `.xaml`: the `Save Mail` node's `FilePath` expression and whether it is a directory or a full path.
2. **Resolve the path the activity actually used.** Substitute the runtime values of every variable concatenated into `FilePath`. Identify the offending segment — an illegal character, an empty value, or an unsanitized upstream string (subject/sender/customer name spliced into the filename).
3. **Confirm it is the path, not the message.** A null `MailMessage` throws elsewhere (`Email message is null.` in `SaveMailX`); a missing required input is a design-time validation error (`You must provide a value for <property>`). An `ArgumentException` at runtime is the path.

## Resolution

- **Illegal characters / malformed path:** Sanitize `FilePath` before the activity. Strip or replace characters not allowed by the OS (build the name with `String.Concat` over a whitelist, or replace `Path.GetInvalidFileNameChars()` / `Path.GetInvalidPathChars()` with `_`). Never splice a raw subject/sender into the filename — emails routinely contain `:`, `/`, `?`.
- **Empty / unresolved path:** Initialize `FilePath` and guard against empty before the activity. If you pass only a folder, ensure it is a valid existing directory so the subject-derived filename can be appended.
- **Reserved name / bare drive:** Provide a full path including a filename and extension (`C:\Out\message.eml`), not a reserved device name or a bare `C:`.

## Anti-patterns (what NOT to do)

- **Splicing the email subject straight into the filename.** Subjects contain `:`/`/`/`?` constantly; this is the most common source of the `ArgumentException`. Always sanitize.
- **Wrapping `Save Mail` in a Try Catch and continuing.** A swallowed write turns "email not saved" into a silent success; downstream steps that read the `.eml` then fail with a confusing "file not found".

## Prevention

- Sanitize any dynamic path segment against `Path.GetInvalidFileNameChars()` before binding it to `FilePath`.
- Pass an absolute, normalized path; validate the directory exists (`Create Directory` upstream) rather than relying on implicit creation.

## Related

- [save-mail-attachments-failures](./save-mail-attachments-failures.md) — the IOException / path-too-long family for the attachment-saving activity.
- [mail-activities overview](../overview.md) — package map and the modern-business vs classic distinction.
