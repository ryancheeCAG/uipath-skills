---
confidence: medium
---

# Get Exchange Mail Messages Failures

## Context

`UiPath.Mail.Exchange.Activities` `Get Exchange Mail Messages` (`GetExchangeMailMessages`) reads messages from an Exchange mailbox over **EWS** (Exchange Web Services, `Microsoft.Exchange.WebServices`). It connects through an `ExchangeService` (Basic auth or OAuth/MSAL), resolves the target folder, runs an optional `FilterExpression`, and binds the matching messages. UiPath wraps connection/auth and many EWS errors in `UiPath.Mail.ExchangeException`; some EWS exceptions and an aggregated bind error surface raw.

What this looks like — the production signatures:

- `Microsoft.Exchange.WebServices.Data.ServiceVersionException` — **branch 1**: `The parameter "<name>" is only valid for Exchange Server version Exchange2010 or a later version.`
- `System.AggregateException` — **branch 2**: multiple per-message bind failures aggregated during the read.
- `Microsoft.Exchange.WebServices.Data.ServiceResponseException` — **branch 3**: an EWS request was rejected (folder/item not found, access denied, mailbox not found).
- `UiPath.Mail.ExchangeException` — **branch 4**: connection/auth wrapped by UiPath, e.g. `Authentication failed for user <user>.`; also the folder guard `Mail Folder does not exist for specified client.`

What can cause it:

1. **Feature/version mismatch.** A `FilterExpression` (or property) used requires Exchange2010+, but the configured `ExchangeVersion` is set lower — EWS rejects the parameter for that version.
2. **Per-message bind failures.** Reading a batch, some message binds fail (item moved/deleted between enumerate and bind, permission on specific items, corrupt item) — the activity aggregates them into `AggregateException`; the real causes are the inner exceptions.
3. **EWS request rejected.** The folder or mailbox doesn't exist, the account lacks rights, or `From`/impersonation targets a mailbox the connection can't read — `ServiceResponseException` with an EWS error code.
4. **Connection / auth.** Wrong credentials or a wrong-user token (`Authentication failed for user <user>.`), a bad/unreachable endpoint, or autodiscover failing — surfaced as `ExchangeException`.

What to look for:

- **The exception type** — it selects the branch.
- **`ExchangeVersion` vs the feature used** (`FilterExpression`, specific properties) — load-bearing for branch 1.
- **For `AggregateException`, the inner exceptions** — they hold the per-item causes; do not stop at the aggregate.
- **Folder + `Account`/impersonation** — folder path resolves (`Mail Folder does not exist…`), and the connection identity has rights to the target mailbox — branches 3/4.
- **Auth mode** (Basic vs OAuth/MSAL) and the user in `Authentication failed for user <user>.` — branch 4.

## Investigation

1. **Capture the exact type and message** from `uip or jobs get <job-key> --output json` → `Info`. For `AggregateException`, expand the inner exceptions.
2. **Branch on the type** (version / aggregate / response / exchange-wrapper).
3. **Branch 1:** compare the configured `ExchangeVersion` against the parameter/feature the activity uses; the message names the parameter.
4. **Branch 2:** read each inner exception — typically `ServiceResponseException` (item not found / access denied) per failing message.
5. **Branches 3/4:** verify the folder path, the target mailbox, the connection identity's rights, the endpoint URL, and the auth mode/user.

## Resolution

- **Branch 1 — `ServiceVersionException`:** raise the configured `ExchangeVersion` to one that supports the parameter (Exchange2010 or later), or drop the unsupported `FilterExpression`/property.
- **Branch 2 — `AggregateException`:** handle per-item failures — fetch promptly so items aren't moved/deleted between enumerate and bind, skip/Try-Catch individual binds, and grant rights on the specific items/mailbox. Fix the dominant inner cause.
- **Branch 3 — `ServiceResponseException`:** correct the folder path / mailbox; grant the connection identity access (or set impersonation/`Send As` appropriately); confirm the item still exists.
- **Branch 4 — `ExchangeException` (auth/connection):** fix credentials or the OAuth token (correct user, valid app/permissions); set a reachable EWS endpoint or working autodiscover; the `Authentication failed for user <user>.` message names the failing identity.

## Anti-patterns (what NOT to do)

- **Reporting only the `AggregateException`.** It is a wrapper; the actionable cause is inside. Always expand inner exceptions.
- **Assuming a missing folder is an auth problem (or vice versa).** `Mail Folder does not exist…` is a path issue; `Authentication failed for user…` is identity. Read the message.
- **Leaving `ExchangeVersion` at a low default and using newer filters.** That guarantees branch 1; align version to features used.

## Prevention

- Set `ExchangeVersion` to match the features (filters/properties) the workflow uses.
- Use a connection identity with explicit rights to the target mailbox/folder; prefer OAuth where Basic auth is deprecated.
- Bind/read promptly and guard per-item operations so a single bad item doesn't fail the batch.

## Related

- [send-exchange-mail-failures](./send-exchange-mail-failures.md) — the sibling EWS send path; same connection/auth surface.
- [o365-activities overview](../../o365-activities/overview.md) — modern Graph reads, the migration target away from EWS.
- [mail-activities overview](../overview.md) — package map and connection models.
