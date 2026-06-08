# SDK Patterns — Skill-Specific Supplement

The canonical SDK reference is fetched live in the parallel blast:
`https://uipath.github.io/uipath-typescript/llms-full-content.txt`

This file covers **only** what that document omits — patterns specific to how the dashboard skill uses the SDK inside generated widget code.

---

## Constructor injection — use `as never`, not bare `sdk`

The SDK docs show `new Jobs(sdk)` but the TypeScript types require a cast:

```typescript
// ✓ Correct — used in every T3-SDK fnBody and T2 compiled code
const svc = new Jobs(sdk as never)

// ✗ Wrong — type error at tsc
const svc = new Jobs(sdk)

// ✗ Wrong — sdk.jobs does not exist at runtime
sdk.jobs.getAll()
```

---

## Paginated response normalisation

SDK methods return either `PaginatedResponse<T>` or `NonPaginatedResponse<T>` depending on options passed. Always normalise:

```typescript
const items = result?.items ?? result?.value ?? []
```

- `PaginatedResponse<T>` → items are under `.items`
- `NonPaginatedResponse<T>` → items are under `.value`
- Either can be `undefined` if the call returns nothing

---

## Dynamic import inside T3-SDK fnBody

The generated widget file has no static SDK imports. Service classes must be loaded dynamically:

```typescript
// Inside fnBody — this is valid TypeScript in an async function
const { Jobs } = await import('@uipath/uipath-typescript/jobs')
const svc = new Jobs(sdk as never)
const result = await svc.getAll({})
const items = result?.items ?? result?.value ?? []
```

Static imports at the top of fnBody are not available — the shell template provides only React and dashboard chrome imports.

---

## Duration — not a direct field, compute it

`JobGetResponse` does not have a `duration` field. Compute from timestamps:

```typescript
const durationMs = new Date(j.endTime).getTime() - new Date(j.startTime).getTime()
const durationMins = Math.round(durationMs / 60_000)
```

---

## fnBody contract

Every T3-SDK `fnBody` must satisfy this interface:

```typescript
type DataFn = (
  sdk: UiPathClient,         // from useAuth().sdk
  getToken: () => Promise<string>  // from useAuth().getToken
) => Promise<Record<string, unknown>[]>
```

The function receives `sdk` and `getToken` as arguments — do not import `useAuth` inside fnBody.
