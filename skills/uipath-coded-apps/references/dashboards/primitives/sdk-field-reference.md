# SDK Field Reference

Authoritative source of truth for TypeScript SDK service classes. Read during Phase 1 parallel blast.

When the UiPath Insights RTM API is onboarded to the TypeScript SDK, this file will be updated to include its service classes and response shapes. Until then, Insights metrics use the `useInsights` hook (T1 and T3-Insights paths).

Fetch latest docs: `https://uipath.github.io/uipath-typescript/llms-full-content.txt`
Use only when a service class is absent from this file.

---

## Import subpaths

```typescript
import { Jobs }             from '@uipath/uipath-typescript/jobs'
import { Queues }           from '@uipath/uipath-typescript/queues'
import { Assets }           from '@uipath/uipath-typescript/assets'
import { Tasks }            from '@uipath/uipath-typescript/tasks'
import { Processes }        from '@uipath/uipath-typescript/processes'
import { Entities }         from '@uipath/uipath-typescript/entities'
import { Cases }            from '@uipath/uipath-typescript/cases'
import { MaestroProcesses,
         ProcessInstances } from '@uipath/uipath-typescript/maestro-processes'
import { UiPath }           from '@uipath/uipath-typescript/core'
```

Always use constructor injection in T3-SDK fnBody:
```typescript
const svc = new Jobs(sdk as never)         // ✓ correct
const r   = await svc.getAll({})
// Never: sdk.jobs.getAll()                // ✗ does not exist
```

**Dynamic import is required inside fnBody** — the generated file has no static SDK imports. Always use `await import(...)` to load the service class:

```typescript
// Correct — dynamic import inside async function
const { Jobs } = await import('@uipath/uipath-typescript/jobs')
const svc = new Jobs(sdk as never)

// Wrong — static imports are not available in fnBody context
import { Jobs } from '@uipath/uipath-typescript/jobs'  // ✗ not available
sdk.jobs.getAll()  // ✗ does not exist
```

---

## Jobs — `@uipath/uipath-typescript/jobs`

### `getAll(options?)` → `PaginatedResponse<JobGetResponse>`

| Field | Type | Notes |
|-------|------|-------|
| `key` | `string` | UUID — use this as ID |
| `state` | `JobState` | `Running`, `Successful`, `Faulted`, `Stopped`, `Suspended` |
| `processName` | `string` | Name of the process (not `name`) |
| `createdTime` | `Date` | When job was created |
| `startTime` | `Date` | When execution started |
| `endTime` | `Date` | When execution ended |
| `inputArguments` | `string \| null` | JSON string |
| `outputArguments` | `string \| null` | JSON string |

Access items: `result?.items ?? result?.value ?? []`

**Duration** (not a direct field — compute it):
```typescript
const durationMs = new Date(j.endTime).getTime() - new Date(j.startTime).getTime()
```

---

## Queues — `@uipath/uipath-typescript/queues`

### `getAll(options?)` → `PaginatedResponse<QueueGetResponse>`

| Field | Type | Notes |
|-------|------|-------|
| `id` | `number` | |
| `name` | `string` | |
| `maxRetries` | `number` | |
| `acceptsRejectedItems` | `boolean` | |

⚠ **No `failureCount` or transaction count fields.** Queue transaction analytics are not exposed through this endpoint. Use T3-Insights or T3-SDK with a queue items endpoint for failure analysis.

---

## Assets — `@uipath/uipath-typescript/assets`

### `getAll(options?)` → `PaginatedResponse<AssetGetResponse>`

| Field | Type |
|-------|------|
| `id` | `number` |
| `name` | `string` |
| `hasValue` | `boolean` |
| `value` | `string` (encrypted) |

---

## Tasks — `@uipath/uipath-typescript/tasks`

### `getAll(options?)` → `PaginatedResponse<TaskGetResponse>`

| Field | Type |
|-------|------|
| `id` | `number` |
| `title` | `string` |
| `priority` | `TaskPriority` |
| `status` | `string` |
| `assignedTo` | `UserLoginInfo` |
| `createdTime` | `Date` |

---

## Processes — `@uipath/uipath-typescript/processes`

### `getAll(options?)` → `PaginatedResponse<ProcessGetResponse>`

| Field | Type |
|-------|------|
| `id` | `number` |
| `name` | `string` |
| `key` | `string` |
| `processType` | `string` |

---

## Entities — `@uipath/uipath-typescript/entities`

### `getAll()` → `EntityGetResponse[]`

| Field | Type |
|-------|------|
| `id` | `string` (UUID) |
| `name` | `string` |
| `displayName` | `string` |
| `entityType` | `string` |

### `getAllRecords(entityId, options?)` → `PaginatedResponse<EntityRecord>`

`EntityRecord` has a fixed `Id` (UUID) field plus dynamic fields matching the entity schema.

---

## Cases — `@uipath/uipath-typescript/cases`

### `getAll()` → `CaseGetAllResponse[]`

| Field | Type |
|-------|------|
| `processKey` | `string` |
| `runningCount` | `number` |
| `completedCount` | `number` |

---

## Common patterns

```typescript
// Paginated result — always normalise this way
const items = result?.items ?? result?.value ?? []

// Filter by state (Jobs)
const running = items.filter((j: any) => j.state === 'Running')

// Compute duration
const mins = (endMs - startMs) / 60_000

// Sort descending by a numeric field
items.sort((a: any, b: any) => (b.fieldName ?? 0) - (a.fieldName ?? 0))
```
