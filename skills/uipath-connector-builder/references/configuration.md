# Configuration Reference

Config entries live in `element.json → configuration[]`. Authentication, pagination,
and events are ALL config keys — values are set per-connection at creation time.

## Config Entry Object
`key` (dot-notation, e.g. `oauth.api.key`), `name`, `description`, `type` (widget),
`defaultValue`, `required`, `internal` (system-set), `hide`, `hideFromConsole`,
`encrypt` (secrets), `active` (true), `companyConfig`/`resellerConfig` (false),
`isPrivate` (redact in responses), `displayOrder`, `configScreenType`.
Optional: `groupControl`, `groupBy`, `options` (`[{"description","value"}]`),
`design`, `hintText`.

## Config Types (widgets)
`TEXTFIELD_32|64|128|256|1000` (by max length; 128 = most fields, 1000 = URLs),
`TEXTAREA` (keys/certs/JSON), `PASSWORD` (masked, auto-encrypt), `BOOLEAN`,
`COMBO` (single-select), `MULTISELECT` (OAuth scopes), `CODE_EDITOR`.

## Config Screen Types
`"pre"` (must fill on creation), `"pre-optional"` (optional on creation), `"none"` (hidden).

## Auth as configuration
Authentication is config keys + `authentication.type`. Key sets per type:

- **OAuth2**: `oauth.api.key`, `oauth.api.secret` (encrypted, isPrivate),
  `oauth.callback.url` (auto-set, do NOT hardcode), `oauth.authorization.url`,
  `oauth.token.url`, `oauth.token.refresh.url`, `oauth.token.revoke.url`,
  `oauth.scope`, `oauth.basic.header`, `oauth.user.token`,
  `oauth.user.refresh.token`, `oauth.user.refresh.interval` (sec, default 3600).
  Set `authentication.type:"oauth2"`, `typeOauth:true`.
- **OAuth2 PKCE** adds `oauth.pkce.code.challenge.verifier`, `oauth.pkce.code.challenge`,
  `oauth.pkce.code.challenge.method` (`"S256"`).
- **OAuth2 Client Credentials**: subset — no auth URL, no refresh token.
- **customApiKey** (the on-disk type for any "API key" auth — the UI labels it "API key",
  but never use periodic's bare `apiKey`): one PASSWORD secret config (default
  `custom.api.key`, encrypted, isPrivate, `groupBy:"customApiKey"`) + one
  `type:"value"` parameter mapping `${configuration.<name>}` into the vendor
  header/query. Location, name, and prefix come from vendor docs. Set
  `authentication.type:"customApiKey"`, `typeOauth:false`.
- **basic**: `username`, `password` (encrypted).
- **jwtOauth**: `jwt.oauth.consumer.key`, `jwt.oauth.private.key`, `jwt.oauth.username`,
  `jwt.oauth.token.url`, `jwt.oauth.scope`. `typeOauth:true`.
- **awsv4**: `aws.api.key`, `aws.api.secret`, `aws.region`, `aws.service.name`, `aws.host`.

## Multi-auth (groupControl)
An `authentication.type` COMBO with `"groupControl": true` plus per-type config
entries tagged with `groupBy`. Fields without `groupBy` always show; comma-separated
`groupBy` shows the field for multiple groups.

## Pagination keys
`pagination.type` (cursor/offset/page), `pagination.max`, `base.url` (TEXTFIELD_1000),
`filter.response.nulls`. `paginatorVersion` at top level selects the engine.

## design (MULTISELECT, e.g. scopes)
`requiredOptions` (cannot deselect), `preSelectedOptions` (pre-checked), `delimiter`,
`enableUserOverride`.

## Event keys
`event.notification.enabled`, `event.vendor.type` (`polling`/`webhook`),
`event.poller.refresh_interval` (minutes, default 15), `event.poller.configuration`
(JSON blob). See [events.md](events.md).

## See also
- [auth.md](auth.md), [system-resources.md](system-resources.md), [events.md](events.md)
