# Tenant Licensing

View and allocate licenses for a UiPath tenant: see what products are granted, how much is consumed, what's still available in the org pool, and apply an updated allocation.

> For full option details, use `--help` (e.g., `uip platform tenants show-licenses --help`).

---

## When to Use

- Inspect a tenant's current license summary (allocated / consumed / available)
- Allocate, reallocate, or top up licenses for a tenant
- Move quantities between sibling tenants in the same organization

## Prerequisites

- Authenticated (`uip login`)
- Org-admin or licensing-admin permissions on the target organization
- The **tenant key** (GUID) of the tenant you're operating on

---

## Concepts

**Tenant key** — GUID identifying a tenant within an organization. Always required as the first positional argument.

**Service license** — A grant of products (with quantities) for a single service-type within a tenant (e.g., `orchestrator`, `aicenter`). A tenant typically has multiple service licenses, one per service-type. The CLI **auto-routes** each input product to the service license that already owns its code — you do not specify the service-type yourself.

**Overlay semantics** — `allocate-licenses` overlays absolute quantities by code. Running it twice with the same input is a no-op. There is no "+N" / "-N" delta mode; to top up, compute the new absolute quantity and send that.

**Current interval filter** — `show-licenses` only returns products whose `startDate` ≤ now ≤ `endDate`. Expired or future grants are hidden.

### Product codes ↔ friendly names

The CLI accepts only product codes. Translate friendly names → codes before calling `allocate-licenses`. If a code is not in this table, fall back to the raw code.

| Code | Friendly name |
|---|---|
| `RU` | Robot Units |
| `AIU` | AI Units |
| `AGU` | Agent Units |
| `PLTU` | Platform Units |
| `TEU` | Test Execution Units |
| `HEAL` | Heals |
| `HEALTEST` | Test Heals |
| `SPR` | ScreenPlay Runs |
| `FCCU` | Financial Crimes Units |
| `MRSU` | Medical Record Summarization Units |
| `LU` | Lending Units |
| `PERFTEST` | Performance Testing |
| `PERFTEST-RUNTIME` | Performance Testing Runtime |
| `TAUNATT` | Test Automation Unattended Robot |
| `UNATT` | Unattended Robot |
| `UNATT-HOSTING` | Unattended Hosting Robot |
| `APPTESTR` | App Test Robot |

---

## Show Tenant License Summary

`uip platform tenants show-licenses <tenant-key> [--organization <account-id>]`

Returns one row per active product granted to the tenant.

**Output fields per row:**

| Field | Meaning |
|---|---|
| `code` | Product code |
| `name` | Friendly name (falls back to `code` if unknown) |
| `allocated` | Quantity granted to this tenant |
| `availableForAllocation` | Units still in the org pool that could be granted to this tenant |
| `allocatedAcrossOtherTenants` | Quantity granted to other tenants in the same org |
| `totalUnitsInAccount` | Org-level cap for this code |
| `consumed` | Units the tenant has already used |
| `startDate` / `endDate` | License validity window (ISO 8601) |

```bash
# Full summary
uip platform tenants show-licenses 296b7134-6691-43db-b48a-2d95ed3ab031 --output json

# Just one product
uip platform tenants show-licenses <tenant-key> --output json \
  --output-filter "Data[?code=='PLTU'] | [0]"

# Just the codes the tenant has
uip platform tenants show-licenses <tenant-key> --output json \
  --output-filter "Data[].code"
```

`--organization <account-id>` overrides the org GUID from the current login. Rarely needed.

---

## Allocate Licenses to a Tenant

`uip platform tenants allocate-licenses <tenant-key> --input <path> [--organization <account-id>]`

The `--input` flag points to a JSON file containing an array of `{code, quantity}` entries:

```json
[
  { "code": "PLTU", "quantity": 500 },
  { "code": "RU",   "quantity": 1200 }
]
```

The CLI reads the tenant's existing service licenses, routes each input product to the service license that already owns its code, merges with the current allocation (overlay by code), and PUTs the result. Multi-service-type allocations issue one PUT per service-type.

### Conversational workflow (use this when the user gives intent in friendly names)

1. **Discover** — run `show-licenses` first to see what codes the tenant has, current `allocated`, and `availableForAllocation`.
2. **Take user intent** — e.g., "set platform units to 500 and top up robot units by 200".
3. **Compute absolute quantities** — `allocate-licenses` is overlay, not additive. For "top up by N", read current `allocated` from step 1 and produce `current + N`.
4. **Confirm** — restate the change in friendly names with current → new values:
   > "I'll set Platform Units to 500 (currently 300) and Robot Units to 1200 (currently 1000). Proceed?"
5. **Translate** friendly names → codes using the table above. Disambiguate at confirmation if a friendly name could map to multiple codes.
6. **Write delta to a temp file** at `/tmp/uip-licensing-delta-<timestamp>.json`.
7. **Allocate** — run the command.
8. **Verify** — re-run `show-licenses` and report the diff in friendly names.
9. **Cleanup** — delete the temp file on success. On failure, keep it and tell the user the path so they can inspect / retry.

```bash
TS=$(date +%s)
DELTA="/tmp/uip-licensing-delta-${TS}.json"

cat > "${DELTA}" <<'EOF'
[
  { "code": "PLTU", "quantity": 500 },
  { "code": "RU",   "quantity": 1200 }
]
EOF

uip platform tenants allocate-licenses <tenant-key> \
  --input "${DELTA}" --output json

# Verify
uip platform tenants show-licenses <tenant-key> --output json

rm "${DELTA}"
```

### Power-user workflow

If the user already has a `delta.json` they maintain (e.g., from version control), just apply it:

```bash
uip platform tenants allocate-licenses <tenant-key> \
  --input ./delta.json --output json
```

---

## Common Patterns

### Top up by N

```text
1. show-licenses   →  read current `allocated` for the code
2. compute new     →  new = current + N
3. allocate-licenses with absolute new value
```

### Rebalance between tenants

Two `allocate-licenses` calls — lower one tenant's allocation, raise another's. Org-level `totalUnitsInAccount` stays constant.

### Dry run

There is no `--dry-run` flag. `show-licenses` is read-only — call it before and after any change to compare.

### Plan a multi-product change atomically

The CLI applies one PUT per service-type. If your delta spans two service-types and the second PUT fails, the first is already committed. Mitigation: keep deltas small, or split into per-service-type calls and verify each.

---

## Error Modes

| Error message | Likely cause | Fix |
|---|---|---|
| `Could not read input file: <path>` | wrong `--input` path or the file is empty | check the path; `cat <path>` to inspect |
| `Invalid input JSON.` | not a JSON array, or an entry is missing `code`/`quantity` | validate against the schema in **Allocate** above |
| `No service licenses found for tenant '<key>'.` | wrong tenant key, or the tenant has no licenses in this org | verify the GUID; the tenant may belong to a different org (try `--organization`) |
| `Cannot route product code(s) for tenant '<key>': <CODE>.` | the code isn't on any of the tenant's existing service licenses | the org doesn't have that product, or it's already fully consumed elsewhere — check the error's "Codes currently allocated" hint |
| `Error connecting to the License Resource Manager.` | not logged in, expired token, or wrong org | `uip login status`; re-login if needed |
| `Error reading service licenses for the organization.` | LRM API unreachable or 4xx/5xx | retry; if persistent, check token scopes and org-admin permissions |