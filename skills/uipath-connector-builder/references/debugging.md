# Connector Debugging Guide

Workflow: inspect → understand → identify the misconfiguration → fix with a single
addressed write → re-validate. Tooling: `connector inspect`, `state query <pointer>`,
`state patch <pointer>`, `connector validate`.

## Investigation steps
1. `connector inspect` — auth types, config, resources, hooks, events.
2. `state query` the relevant slice:
   - Auth → `element.json/configuration`, then `.../configuration/{key}`
   - Resource → `element.json/resources`, then `.../resources/{METHOD}/{url-encoded-path}` + `standard-resources/{name}`
   - Hook → `hooks/{file}.js` + `.../resources/{M}/{P}/hooks`
   - Event → `element.json/configuration/event.poller.configuration` + `standard-resources/{name}/metadata/events`
3. Cross-reference: resources[] ↔ SR files (paths match), hook `ref`s ↔ `hooks/` files,
   configuration[] ↔ auth-type requirements, element-metadata flags ↔ capabilities.
4. `connector validate` for automated checks.

## Connection issues
- **OAuth redirect loop / error**: wrong `oauth.authorization.url` (often the token URL
  by mistake), missing scopes, hardcoded `oauth.callback.url` (periodic sets it),
  `typeOauth` false when it should be true.
- **Token exchange fails**: wrong `oauth.token.url`; vendor expects/rejects
  `oauth.basic.header`; creds in wrong place (body vs header). Check any
  `oauthOnTokenExchange` override.
- **Works then fails after expiry**: `oauth.token.refresh.url` unset, refresh interval
  too long, or wrong param mapping in `oauthOnTokenRefresh`.
- **API key unauthorized**: wrong header name, missing prefix (`Bearer `/`Token `),
  or key sent as query when the vendor wants a header. Check the global `value` parameter.

## Resource issues
- **Empty results**: wrong `vendorPath`, `responseBodyRoot` extracts the wrong path,
  postRequest hook filters wrongly, or broken pagination.
- **404**: `vendorPath` typo/version, path-param `vendorName` mismatch, wrong/missing
  `base.url`, deprecated endpoint.
- **Create/Update sends wrong data**: `requestBodyRoot` wraps in the wrong key,
  preRequest hook mangles the body, CE↔vendor field-name mismatch.
- **Fields don't show in Studio**: missing `requestCurated`/`responseCurated` on field
  method entries, no `curated` block in `metadata.method.{METHOD}`, or `design.isHidden`.
- **Object shows in Studio but has NO methods under it**: the SR's
  `metadata.method.<VERB>.{reference ?? path}` doesn't resolve to the element.json resource
  `path` (the IS slug `/<object>`), so Periodic can't link the method. Usual cause: a
  cache-synced SR still carrying the **vendor** path. `connector validate` flags this as
  "SR linkage broken". Fix: set the SR method's `reference` (or `path`) to `/<object>` —
  re-running `resource sync-from-cache` normalizes it automatically.
- **Methods aren't curated activities**: `resource create` / `resource sync-from-cache`
  curate by default; a method with no `curated` block was created with `--no-curate` — add
  one with `resource method curate`.

## Hook issues
- **done() not called**: an exception or a branch skips `done()`.
- **Hook not applied**: not registered in element.json `hooks[]`, `ref`/filename
  mismatch (case-sensitive), wrong `type` or resource/method.
- **Global hook over-applies**: move it from top-level `hooks[]` to the specific resource.

## Event / pagination issues
- **Events not working**: `hasEvents` unset, missing event config keys, malformed
  `event.poller.configuration` JSON.
- **Polling returns everything**: missing date filter in the URL, wrong
  `updatedDateField`, or date-format mismatch.
- **Only first page**: wrong `paginatorVersion`/`pagination.type`, or missing nextPage
  handling in a preRequest hook.

## See also
- [hooks.md](hooks.md), [events.md](events.md), [configuration.md](configuration.md),
  [element-json.md](element-json.md)
