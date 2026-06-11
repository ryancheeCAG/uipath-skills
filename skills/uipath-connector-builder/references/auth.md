# Authentication in UiPath Integration Service connectors

A connector's authentication block tells the server which auth flow to run
when a tenant creates a connection. Two pieces are involved:

1. **Config entries** in element.json `configuration[]`: every credential
   or endpoint URL gets one entry. The server uses these to render the
   connection form AND to drive the OAuth dance / API-key wiring at runtime.
2. **Top-level fields**: `authentication.type`, `typeOauth`,
   `elementMetadata.authenticationTypes`. Together they tell periodic
   which flow to use.

`auth set` writes all of these in one shot.

## Supported auth types

All 14 auth types periodic recognises are supported:

| auth-type               | Use when                                        |
|-------------------------|-------------------------------------------------|
| oauth2                  | OAuth 2.0 Authorization Code flow.              |
| oauth2Pkce              | OAuth 2.0 Authorization Code + PKCE.            |
| oauth2ClientCredentials | OAuth 2.0 Client Credentials (no user).         |
| oauth2Password          | OAuth 2.0 Resource Owner Password.              |
| oauth1                  | OAuth 1.0a / Token-Based Authentication (TBA).  |
| basic                   | HTTP Basic (username + password).               |
| jwtOauth                | JWT-bearer OAuth.                               |
| jwtOauth2               | JWT-bearer OAuth 2.0.                           |
| custom                  | A custom static authorization header.           |
| customApiKey            | Vendor uses a static API key (header or query). |
| personalAccessToken     | Personal access token authorization header.     |
| awsv4                   | AWS Signature v4.                               |
| googleServiceAccount    | Google service-account JSON.                    |
| rsaCertificate          | RSA private-key certificate.                    |

OAuth/JWT types additionally accept a rich scope surface (--scope-options,
--required-scopes, --preselected-scopes, --scope-delimiter, --scope-hint-text,
--scope-screen-type) that builds an `oauth.scope` MULTISELECT. The scope
option list can also be managed standalone with `auth scope set|add|delete`.

## OAuth 2.0 (authorization_code)

Required CLI arguments:
- --authorization-url    Login/consent page (where the user grants access)
- --token-url            Token exchange endpoint
- --scope                Space-delimited scope string

Optional:
- --token-refresh-url    Defaults to --token-url
- --token-revoke-url

What gets written to element.json:
- 16 config entries (oauth.api.key, oauth.api.secret, oauth.callback.url,
  oauth.authorization.url, oauth.token.url, oauth.token.refresh.url,
  oauth.token.revoke.url, oauth.scope, oauth.basic.header,
  oauth.user.token, oauth.user.refresh.token, oauth.user.refresh.time,
  oauth.user.refresh.interval, oauth.decode.authorization.code,
  authentication.time, expires_in)
- authentication = { "type": "oauth2" }
- typeOauth = true
- elementMetadata.authenticationTypes appends "oauth2"
- A resources[] entry of type "oauthOnTokenRefresh" pointing at the
  refresh URL — periodic calls this when the access token expires.

## customApiKey

Required:
- --api-key-param-name   Vendor's header or query parameter name
                         (e.g. 'X-API-Key', 'Authorization',
                         'subscription-key'). Decided from vendor docs.

Optional:
- --api-key-location     'header' (default) or 'query'
- --api-key-prefix       Literal prefix prepended to the key value (e.g.
                         'Bearer '). Empty = no prefix.
- --key-config-name      Internal config key. Defaults to 'custom.api.key'.
                         Override with a vendor-meaningful name if your
                         docs/parameter mappings reference a different
                         name (e.g. 'subscription.key').
- --key-config-display-name  UI label. Defaults to 'API Key'.

What gets written:
- 1 secret config entry (the chosen key name, PASSWORD type, encrypted,
  groupBy="customApiKey").
- 1 global parameter in element.json `parameters[]` mapping
  ${configuration.<key-config-name>} into the vendor header / query
  parameter name with the optional prefix.
- authentication = { "type": "customApiKey" }
- typeOauth = false
- elementMetadata.authenticationTypes appends "customApiKey"

## Re-running auth set

`auth set` is idempotent on identical inputs — re-running with the
same arguments returns `unchanged`. If any existing entry would be
modified by the new inputs, it fails with a `configConflict` error
listing every diff. Use `--force` to apply.

## See also

- [configuration.md](configuration.md) — config keys per auth type
- [system-resources.md](system-resources.md) — auth-validation, token-refresh overrides
- [element-json.md](element-json.md) — what scaffold produces
