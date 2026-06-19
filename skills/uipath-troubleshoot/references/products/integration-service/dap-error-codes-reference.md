# DAP Runtime Error Codes (Integration Service)

Integration Service emits a structured error code on every failure: `DAP-<LAYER>-<CODE>`, appended to the user message as _"Error code: DAP-RT-1101."_. Layers:

- **RT** — runtime (execution failures; the agent's primary focus)
- **GE** — general (connection / auth / migration)
- **DT** — design time (Studio canvas; **out of scope** for runtime triage — surfaced directly to the user in Studio, never in execution telemetry)

This reference maps each runtime/general DAP code to its playbook. Use it to route from a code seen in execution telemetry to the right investigation.

## Telemetry customEvent fields

At runtime the failure is also emitted as a telemetry `customEvent`. Read these fields before matching a playbook — they are the primary evidence:

| Field | Use for root-cause |
|-------|--------------------|
| `ErrorCode` | Numeric IS code — the primary classifier (maps to a playbook below). |
| `Error` | Exception type (`RuntimeException`, `GeneralException`). |
| `ErrorMessage` | Human-readable IS message. |
| `ProviderErrorCode` / `ProviderErrorMessage` | The connector / 3rd-party API's own code + message (e.g. the underlying 401/403 reason). **Decisive for `DAP-RT-1101`.** |
| `RequestId` | Correlation ID — trace the call to the connector. |
| `IsServiceError` | `true` = downstream API failure; `false` = IS-side exception. |
| `ConnectionId` | Which connection failed (for auth / connection issues). |

> If the failure surfaced through Maestro (BPMN service task), the same root cause also carries a Maestro IntSvc code (`102002`, `102003`, …). The DAP code is more specific — prefer it when present. The Maestro-keyed playbooks ([connection-invalid.md](./playbooks/connection-invalid.md), [connection-auth-expired.md](./playbooks/connection-auth-expired.md), [operation-failed.md](./playbooks/operation-failed.md), [trigger-not-firing.md](./playbooks/trigger-not-firing.md)) cover the same failures from the Maestro surface.

## Retry semantics

IS auto-retries before surfacing a failure. Knowing this disambiguates transient vs sustained:

- **Retried (max 2):** `429`, `423`, `5xx`. Token auto-refreshed on `401`.
- **Not retried (non-transient):** `408`, `501`, `502`, `504`.
- A `retry-exception` SRE alert means **retries were exhausted** — treat as a sustained provider/network problem, not a transient blip.

## Code → playbook map

### Connection & authentication

| Code | Name | Playbook |
|------|------|----------|
| `DAP-GE-3004` | FailedToGetAccessToken | [token-refresh-failed.md](./playbooks/token-refresh-failed.md) |
| `DAP-GE-3000` | FailedToGetConnection | [connection-not-resolved.md](./playbooks/connection-not-resolved.md) |
| `DAP-GE-3005` | ConnectionDisabled | [connection-not-resolved.md](./playbooks/connection-not-resolved.md) |
| `DAP-RT-1002` | ConnectionIdNull | [connection-not-resolved.md](./playbooks/connection-not-resolved.md) |

### HTTP / request execution

| Code | Name | Playbook |
|------|------|----------|
| `DAP-RT-1101` | RequestFailed | [request-failed.md](./playbooks/request-failed.md) |
| `DAP-RT-1103` | HttpClientException | [http-client-exception.md](./playbooks/http-client-exception.md) |
| `DAP-RT-1100` | HttpMethodMissing | [activity-configuration-corrupt.md](./playbooks/activity-configuration-corrupt.md) |

### Triggers (polling / webhook)

| Code | Name | Playbook |
|------|------|----------|
| `DAP-RT-1051` | TriggerExecutionFailed | [trigger-execution-failed.md](./playbooks/trigger-execution-failed.md) |
| `DAP-RT-1050` | TriggerDataMissing | [trigger-execution-failed.md](./playbooks/trigger-execution-failed.md) |
| `DAP-RT-1052` | TriggerNoMatches | [trigger-execution-failed.md](./playbooks/trigger-execution-failed.md) |

### Deserialization & output mapping

| Code | Name | Playbook |
|------|------|----------|
| `DAP-RT-1005` | ApiResponseMismatch | [response-mapping-mismatch.md](./playbooks/response-mapping-mismatch.md) |
| `DAP-RT-1155` | DataTableFieldTypeMismatch | [response-mapping-mismatch.md](./playbooks/response-mapping-mismatch.md) |
| `DAP-RT-1156` | TypedDataTableNotConstructedProperly | [response-mapping-mismatch.md](./playbooks/response-mapping-mismatch.md) |
| `DAP-RT-1000` | ActivityConfigurationNull | [activity-configuration-corrupt.md](./playbooks/activity-configuration-corrupt.md) |
| `DAP-GE-3001` | InvalidMigration | [activity-configuration-corrupt.md](./playbooks/activity-configuration-corrupt.md) |

### Design-time (DT) — out of scope

`DAP-DT-2000`–`2349` (metadata fetch failures, unsupported activity/method, object-not-found, duplicate fields, …) fire in Studio while building a workflow and block the canvas. They do **not** appear in runtime execution telemetry. Do not author runtime playbooks for DT codes — they are surfaced to the user directly in Studio.
