---
confidence: medium
---

# Get Test Data Queue Item — Failures (empty/not-found vs NullReference)

## Context

`UiPath.Testing.Activities.GetTestDataQueueItem` (`Get Test Data Queue Item`) fetches the next item from a **Test Data Queue** in an Orchestrator folder, deserializes its JSON `Content` into a `Dictionary<string, object>`, and sets `Output`. Failures split between activity-thrown `TestingActivitiesException` (clear messages) and a raw `System.NullReferenceException`.

What this looks like:
- **Activity-thrown (clear cause):** `UiPath.Testing.Exceptions.TestingActivitiesException` with one of:
  - `Queue is empty or all items are consumed` — no unconsumed item available.
  - `Queue <name> not exist.` — the queue name does not resolve in the folder.
  - `We received queue item <id>, consumed <flag> from queue <name> but it's Content is null` — item exists but its content is null.
  - `Test data queue item is not a JSON: <error>` — the item content is not valid JSON.
- **`System.NullReferenceException`:** raised around the activity when a **required input is unbound** (`QueueName` or `Output` not set) or when a **null field in the returned dictionary** is dereferenced by a **downstream** activity (the fault is reported against the data flow, not this activity's own throw).

What can cause it:
1. **Queue empty / fully consumed.** All items already consumed (`MarkConsumed = true` on prior reads), or the queue was never populated.
2. **Wrong queue / folder.** `QueueName` typo, or `FolderPath` points at a folder without that queue.
3. **Unbound `QueueName` / `Output` (`NullReferenceException`).** A required argument is null at run time (e.g. `QueueName` bound to an unset variable; `Output` not wired to a variable).
4. **Null value consumed downstream (`NullReferenceException`).** The item was fetched, but a key the workflow reads is missing/null, and a later activity dereferences it.
5. **Malformed item content.** Content stored as non-JSON, or null content.

What to look for:
- **The message** distinguishes the activity-thrown cases unambiguously.
- **A bare `NullReferenceException` with no `Queue…` message** → inspect input bindings (`QueueName`/`Output`) and the downstream consumer of `Output`, not the queue itself.

## Investigation

1. **Capture the exact type + message** from `uip or jobs get <job-key> --output json` → `Info` / `uip or jobs logs <job-key> --level Error --output json`.
2. **If `Queue <name> not exist.`:** verify the queue name and the resolved Orchestrator folder (`FolderPath`). Confirm the Test Data Queue exists in that folder.
3. **If `Queue is empty or all items are consumed`:** check whether the queue was populated and whether earlier reads consumed all items.
4. **If content-null / not-JSON:** inspect the offending item's content shape.
5. **If `NullReferenceException`:** read the workflow source — confirm `QueueName` and `Output` are bound to real values, then trace where `Output` is consumed downstream and which key is null.

## Resolution

- **Queue not found:** correct `QueueName` / `FolderPath` to the folder that holds the queue.
- **Empty/consumed:** populate the queue before the run, or use a fresh/replenished queue; if re-reading is intended, account for `MarkConsumed`.
- **Unbound input (`NullReferenceException`):** bind `QueueName` to a non-null value and wire `Output` to a variable.
- **Null downstream value:** guard the consuming activity for missing/null keys, or ensure producers populate every key the workflow reads.
- **Malformed content:** fix the item-producing step so content is valid JSON / non-null.

## Anti-patterns (what NOT to do)

- **Assuming every fault here is "queue missing."** A bare `NullReferenceException` is usually an input-binding or downstream-null problem, not the queue.
- **Ignoring `MarkConsumed`** when a queue reads as empty on a re-run.

## Related

- [testing-activities investigation guide](../investigation_guide.md) — execution context and required-input checks.
- [testing-activities overview](../overview.md) — test data queue activities require a provisioned Test Data Queue in the target folder.
