---
confidence: medium
---

# For Each Email Failures

## Context

`UiPath.Mail.Activities` `For Each Email` (`Business.ForEachEmailX`) iterates a collection of messages and runs its body per email. The collection is often **lazy/queryable** — backed by a live provider session (Outlook COM, Graph, Gmail, Exchange) — so iterating, applying a filter, or downloading attachments inside the loop can trigger **per-item provider calls**. Failures therefore surface at the loop, not at the original fetch.

What this looks like — the two production signatures:

- `System.TimeoutException` raised during iteration — **branch 1 (provider timeout)**.
- `System.SystemException` raised during iteration — **branch 2 (provider/session error)**, including the wrapped `Cannot download attachments for the email with subject '<subject>'. The underlying email provider for this message could not be determined.` and the filter-on-manual-list guard `Provided email list was created manually and you cannot apply filters to it. You can still iterate over it, but please remove the filters.`

What can cause it:

1. **Provider timeout.** The lazy collection hits the server on each iteration (or attachment download), and a slow mailbox, a large folder, or a degraded provider connection exceeds the timeout. Common when the loop body downloads attachments or reads full bodies one message at a time.
2. **Provider/session error.** The underlying session dropped or is inconsistent mid-loop (an Outlook COM session closed/detached on an unattended host → `SystemException`); the message's **provider can't be determined** for an attachment download (a message object built manually or from a different provider than the loop expects); or a **filter is applied to a manually-built list** that does not support querying.

What to look for:

- **The exception class** — `TimeoutException` → branch 1; `SystemException` (incl. the "underlying email provider could not be determined" / "created manually … remove the filters" messages) → branch 2.
- **How the collection was produced** — a `Get Mail Messages`/`For Each Email` over a **live provider** query vs a list assembled in the workflow. A manually-built `List<MailMessage>` cannot be filtered and may lack provider context for attachment downloads.
- **What the loop body does per item** — attachment downloads / full-body reads multiply provider round-trips and are the usual timeout source.
- **`TimeoutMS`** on the source/provider activity, and the provider type (COM vs Graph vs Gmail vs Exchange).

## Investigation

1. **Capture the error and the loop shape.** From `uip or jobs get <job-key> --output json` → `Info`: the exception class and message. From the `.xaml`: how the iterated collection was produced, whether a `Filter` is set on `For Each Email`, and what the body does per item.
2. **Branch on the signature.**
   - `TimeoutException` → branch 1; go to step 3.
   - `SystemException` (provider-undetermined / manual-list / COM session) → branch 2; go to step 4.
3. **Confirm branch 1 (timeout).** Determine whether each iteration triggers a provider call (lazy collection + per-item attachment/body access). Compare the per-item work against the configured timeout and the folder size.
4. **Confirm branch 2 (provider/session).** Check whether the collection is a manually-built list (no query/filter support, no provider context), whether a `Filter` is set on such a list, and — for COM providers — whether the session could have closed mid-loop on an unattended host.

## Resolution

- **Branch 1 — provider timeout:**
  - Raise `TimeoutMS` on the source/provider activity above the worst per-item duration (milliseconds).
  - Reduce per-iteration provider work: fetch fields/attachments in the original `Get` (eager) instead of per item, lower `Top`/page size, or `OnlyUnreadMessages` to shrink the set.
  - Materialize the collection (`.ToList()`) **before** the loop when the body does not need live server state, so iteration does not re-hit the provider.
- **Branch 2 — provider/session error:**
  - **Provider undetermined for attachment download:** download attachments from a message obtained through the same provider/connection (don't build messages manually then download); use the provider's own `Save Attachments` path.
  - **Filter on a manual list:** remove the `Filter` from `For Each Email` when iterating a hand-built list, or produce the collection from a provider query that supports filtering.
  - **COM session loss:** keep the Outlook session alive for the whole loop (attended/foreground Outlook), wrap the body in a `Retry Scope`, or move to a Graph/Exchange provider that does not depend on a desktop session.

## Anti-patterns (what NOT to do)

- **Doing heavy per-item provider work inside the loop and "just raising the timeout".** It only delays the failure on large folders — eager-fetch or page instead.
- **Applying a `Filter` to a manually-assembled email list.** It is unsupported by design; filter at the source query.
- **Iterating a live COM collection across a long-running loop on an unattended Robot.** The session can drop mid-loop; materialize first or use Graph/Exchange.

## Prevention

- Produce iterated collections from a provider query (filterable, provider-aware), not by hand.
- Eager-fetch needed fields/attachments at the source; keep loop bodies free of per-item provider round-trips where possible.
- Size `TimeoutMS` to the slowest realistic per-item operation.

## Related

- [save-mail-attachments-failures](./save-mail-attachments-failures.md) — attachment-download failures (the `Save Attachments` path).
- [send-mailx-failures](./send-mailx-failures.md), [outlook-application-card-failures](./outlook-application-card-failures.md) — sibling business activities and the COM session surface.
- [mail-activities overview](../overview.md) — package map and provider/connection models.
