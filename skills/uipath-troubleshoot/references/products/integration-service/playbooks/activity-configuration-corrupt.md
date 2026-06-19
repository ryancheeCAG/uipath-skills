---
confidence: medium
---

# Activity Configuration Corrupt (DAP-RT-1000 / DAP-RT-1100 / DAP-GE-3001)

## Context

What this looks like — the activity's stored configuration is incomplete, null, or failed to migrate, so IS cannot build the request:

| Code | Name | Specific cause |
|---|---|---|
| `DAP-RT-1000` | ActivityConfigurationNull | Activity configuration is null/empty — corrupt or failed-to-deserialize config blob |
| `DAP-RT-1100` | HttpMethodMissing | Activity built without an HTTP method — incomplete/corrupt configuration |
| `DAP-GE-3001` | InvalidMigration | Activity failed to migrate to a newer connector schema version |

What can cause it:
- Activity package upgraded and the old configuration didn't migrate cleanly (`3001`, `1000`)
- Project/package corruption during publish or merge — the config blob is empty or malformed (`1000`, `1100`)
- Activity was partially configured or hand-edited, leaving a required field (HTTP method) unset (`1100`)

What to look for:
- `IsServiceError: false` — the failure is IS-side, before any provider call
- `ProviderErrorCode` and `ConnectionId` are typically absent — nothing reached the connection layer
- Whether the failure started immediately after an activity package upgrade (points to `3001`/migration)

## Investigation

1. **Confirm it is config-layer, not connection or provider** — `IsServiceError: false`, no `ProviderErrorCode`. The connection ping is healthy; the problem is the activity definition.
2. **Read the workflow source** — open the failing activity in the project. Verify the configuration blob is present and complete:
   - **`DAP-RT-1100`:** check the HTTP method is set on the activity.
   - **`DAP-RT-1000`:** check the activity's configuration is not empty/null.
3. **Check for a recent package upgrade** — compare the activity package version against the project history. `DAP-GE-3001` indicates a migration the package could not complete.
4. `uip is activities list <connector-key>` — confirm the activity still exists and is supported in the installed package version.

## Resolution

- **`DAP-RT-1100`:** open the activity and set the HTTP method (or reconfigure the operation), then republish.
- **`DAP-RT-1000`:** re-create the activity from a clean state — delete and re-add it, reconfigure inputs, republish. If project corruption is suspected, restore from source control.
- **`DAP-GE-3001`:** re-open the project in Studio to run the activity migration, or downgrade to the previous connector package version if migration cannot complete; then re-validate and republish.
- After any fix, re-run to confirm the config-layer error clears before checking for downstream provider errors.
