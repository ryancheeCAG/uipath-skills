---
confidence: high
---

# Create HTML Content Failures

## Context

`UiPath.Mail.Activities` `Create HTML Content` (`Business.CreateHtmlContent`) builds an HTML email body and lets you embed local resources (images, files) referenced **by file path**. Before composing, it validates each referenced path. A bad path is rejected with `System.ArgumentException` carrying one of three verbatim messages:

- `Directory "<path>" doesn't exist.` — a referenced directory is missing.
- `There are invalid characters in the file path.` — the path contains characters illegal on the OS.
- `File "<path>" does not exist.` — a referenced file is missing.

What this looks like:

- `System.ArgumentException` at the `Create HTML Content` node, message matching one of the three above.

What can cause it:

- **Embedded-resource path points to a missing file/directory.** An image or attachment referenced by the HTML content was moved, never produced by an upstream step, or lives on the dev machine but not the Robot host.
- **Invalid characters in the path.** A dynamic path segment (often spliced from upstream data) contains characters not allowed in a Windows path.
- **Relative path resolved against the wrong working directory.** A relative resource path that works in Studio resolves differently under the Robot, landing on a non-existent directory.

What to look for:

- **Which of the three messages** fired — directory-missing, invalid-chars, or file-missing — names the branch directly.
- **The referenced path(s)** in the `Create HTML Content` configuration: literal vs expression-bound, absolute vs relative, and whether each one exists on the **Robot host** that ran the job (not the developer machine).
- **Upstream producers** of any embedded file (a prior download/render step) — whether it actually ran and wrote to the expected path before this activity.

## Investigation

1. **Read the exact message** from `uip or jobs get <job-key> --output json` → `Info`. Map it to the branch (directory / invalid-chars / file).
2. **Resolve the referenced path** by substituting runtime variable values. For a relative path, resolve it against the Robot's working directory, not Studio's.
3. **Verify existence on the Robot host.** Confirm whether the directory/file is present where the job ran; check that the upstream step that should produce it succeeded first.

## Resolution

- **`Directory "<path>" doesn't exist.`** Create the directory before the activity (`Create Directory`), or point the reference at an existing absolute path. For relative paths, anchor them to a known base (the project folder or an absolute output dir).
- **`There are invalid characters in the file path.`** Sanitize the dynamic path segment (replace `Path.GetInvalidPathChars()` / illegal filename chars). Do not splice raw upstream text into a resource path.
- **`File "<path>" does not exist.`** Ensure the upstream step that produces the embedded file runs and completes before `Create HTML Content`; reference the exact output path it wrote. Guard with `Path Exists` and skip/substitute the resource when absent.

## Anti-patterns (what NOT to do)

- **Assuming Studio paths work on the Robot.** Relative paths and dev-only files are the top cause; always validate against the host that runs the job.
- **Embedding a resource path before the producing step ran.** Order the workflow so the file exists first, or guard with `Path Exists`.

## Prevention

- Use absolute, validated paths for embedded resources; sanitize any dynamic segment.
- Guard each referenced resource with `Path Exists` and provide a fallback when optional.

## Related

- [save-mail-failures](./save-mail-failures.md) — the sibling FilePath / `ArgumentException` family for `Save Mail`.
- [send-mailx-failures](./send-mailx-failures.md) — `Send Mail` (`SendMailX`) consumes the HTML body this activity produces.
- [mail-activities overview](../overview.md) — package map.
