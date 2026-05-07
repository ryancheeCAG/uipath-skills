# Solution Scenarios

Real multi-project recipes that the step-by-step files don't cover head-on. Each scenario has the setup, the behavior to expect, the gotcha that bites, and a fix. Read these before starting on a complex solution — most of them surface during `solution resource refresh` or `solution deploy run`.

> All scenarios assume you've already read [develop-solution.md](develop-solution.md) and [pack-and-deploy.md](pack-and-deploy.md). The references below tie back to specific steps there.

---

## Scenario 1 — Same-name resource across cloud folders

You have two tools (or two bindings, or two project references) that target a resource with **the same name in different cloud folders**. Most common case: an agent with two API Workflow tools, both called "API Workflow", living in `Shared/Solution 50` and `Shared/DependenciesSolution`. RCS is happy with this — names are unique per folder, not globally — but the solution flattens both into a single `resources/solution_folder/process/api/` directory.

### Setup

Two bindings in the agent's `bindings_v2.json`, same `value.name.defaultValue`, different `value.folderPath.defaultValue`:

```json
{
  "version": "2.0",
  "resources": [
    { "resource": "process", "key": "API Workflow",
      "value": { "name": { "defaultValue": "API Workflow" },
                 "folderPath": { "defaultValue": "Shared/Solution 50" } },
      "metadata": { "subType": "api", "bindingsVersion": "2.2", "solutionsSupport": "true" } },
    { "resource": "process", "key": "API Workflow",
      "value": { "name": { "defaultValue": "API Workflow" },
                 "folderPath": { "defaultValue": "Shared/DependenciesSolution" } },
      "metadata": { "subType": "api", "bindingsVersion": "2.2", "solutionsSupport": "true" } }
  ]
}
```

Each tool's `resource.json` carries the cloud key in `referenceKey` and the cloud FQN in `properties.folderPath`.

### What happens at `solution resource refresh`

```
Synced 2 resources (0 already in solution)
```

The SDK applies `addResourceWithUniqueName`: the first import lands as `API_Workflow.json` with the first cloud key; the second hits a name conflict and is **suffixed** to `API_Workflow_1.json` with the second cloud key.

```
resources/solution_folder/process/api/
├── API_Workflow.json     (key=6337a36e..., name="API Workflow")
└── API_Workflow_1.json   (key=5aaddd83..., name="API Workflow_1")  ← suffix added by SDK
```

The `_1` suffix is **expected and stable** — re-running refresh does not bump it further. Tool resource files are not touched; their `referenceKey` still points at the right cloud GUID.

### Gotchas

- **Tool dialogs in Studio Web may show only one tool** opening correctly. This is an SW UI bug present even on solutions authored entirely in Studio Web — confirmed by inspecting raw `Solution.uis` exports. The packed and deployed runtime is unaffected: the agent's `runtimeDependencies` carry distinct `resourceKey` + cloud `folderKey` per tool, so Orchestrator dispatches to the correct cloud workflow.
- **Tool-agent dedup collapses bindings in the agent's nupkg** to one entry per `processName`. The packed `content/bindings_v2.json` shows a single `key: "API Workflow"` even though the agent has two tools. This is shared with Studio Web's server-side pack output. Don't try to fix it at the bindings layer — the deploy-time resolution path uses `tool.referenceKey → solution resource → debug_overwrites → cloud folder`, not the collapsed binding.
- **Don't rename `processName` on the second tool by hand to dodge the collapse.** It changes the agent's call signature without rewriting the agent code/prompt that references the tool, and the next `agent validate` will revert it.

### Verify

```bash
uip solution resource list --solution-folder ./MySolution --source local --output json
```

You should see two `process`/`api` entries with **different keys** but matching the cloud GUIDs you wanted (compare against `uip maestro flow registry search "API Workflow"`).

> See: [develop-solution.md — Step 7: Refresh Resources](develop-solution.md#step-7-refresh-resources).

---

## Scenario 2 — Cross-reference inside the same solution

A coordinator agent (or flow, or process) needs to invoke another agent in the **same solution**. Both projects ship together, neither exists in cloud yet at refresh time.

### Setup

Solution has `Coordinator/` (agent) and `Worker/` (agent). Coordinator's `agent.json` declares a tool whose `referenceKey` should resolve to Worker — but Worker isn't on cloud, so its cloud key doesn't exist.

```
MySolution/
├── MySolution.uipx
├── Coordinator/
│   ├── agent.json
│   ├── resources/WorkerTool/resource.json
│   └── bindings_v2.json
├── Worker/
│   └── agent.json
└── resources/solution_folder/
    ├── process/agent/Coordinator.json    (auto on add)
    └── process/agent/Worker.json         (auto on add)
```

The right `referenceKey` for the Worker tool is the **solution-resource key** of `Worker.json` (read from `uip solution resource list --source local --output json`), **not** the `projectId` from `.uipx`.

```jsonc
// Coordinator/resources/WorkerTool/resource.json
{
  "$resourceType": "tool",
  "name": "WorkerTool",
  "type": "agent",
  "location": "solution",                              // ← intra-solution, not "external"
  "referenceKey": "<solution-resource-key-of-Worker>", // from `resource list --source local`
  "properties": {
    "processName": "Worker",
    "folderPath": "solution_folder"
  }
}
```

### What happens at refresh + pack

- `solution project add` writes `Worker.json` and `Coordinator.json` under `resources/solution_folder/process/agent/` with stable solution-resource keys (UUIDs minted by the SDK at add time).
- `resource refresh` doesn't re-mint those keys — they're stable for the life of the solution.
- At pack, the Coordinator's `runtimeDependencies` entry for the Worker tool carries the same solution-resource key as `referenceKey`. Orchestrator's deploy pipeline resolves intra-solution links by matching this key to a sibling resource in the deployment.

### Gotchas

- **Don't put the cloud key of a different (already-published) Worker** if you intend to ship Worker as part of this solution. `referenceKey` to a cloud key skips the intra-solution link and points the runtime at the cloud copy — which may or may not exist in the target tenant at deploy time.
- **The solution-resource key is stable across refreshes within an instance** but **regenerates if you delete and re-create the solution** (`solution new` → mint fresh UUIDs). Hard-coding the key in `resource.json` survives normal refresh cycles but breaks if anyone wipes-and-recreates. If that's a risk, rebuild the file from `resource list --source local` output as part of CI.
- **`location` must be `"solution"`, not `"external"`** for intra-solution tools. SW UI shows external-tool dialogs differently and won't render the link state correctly.
- **Worker → Coordinator cycles**: nothing prevents you from declaring a tool in Worker that points back at Coordinator. The runtime supports it; if the agent prompts loop, that's an authoring issue, not a deploy one.

### Verify

```bash
uip solution resource list --source local --output json | jq '.Data[] | select(.Kind == "process")'
```

The keys you see here are what `referenceKey` should be in any `location: "solution"` tool resource file.

> See: [develop-solution.md — Step 6: List Resources](develop-solution.md#step-6-list-resources).

---

## Scenario 3 — Shared cloud resource across projects

Two (or more) projects in the solution declare a binding to the **same cloud resource** — typically a shared queue, asset, or storage bucket that multiple agents/processes read from.

### Setup

`ProjectA/bindings_v2.json` and `ProjectB/bindings_v2.json` both contain:

```json
{ "resource": "queue", "key": "OrdersQueue",
  "value": { "name": { "defaultValue": "OrdersQueue" },
             "folderPath": { "defaultValue": "Shared/Production" } },
  "metadata": { "subType": "queue", "bindingsVersion": "2.2", "solutionsSupport": "true" } }
```

Same name, same folder, same cloud GUID.

### What happens at refresh

```
Synced 1 resources (0 already in solution)
```

(Or `Imported: 1, Skipped: 1` depending on iteration order.) The first project's binding triggers `addOrUpdateResourceToSolutionAsync`, which imports `OrdersQueue` into the solution with its cloud GUID as the solution-resource key. The second project's binding hits the same cloud GUID — already in `knownResourceKeys` from the first import — and **skips silently**. No suffix, no duplicate, no error.

### Gotchas

- **The skip is idempotent across refreshes** for cloud-imported resources. If you ever see two `OrdersQueue.json` entries (without distinct cloud keys), something else is wrong — most likely a binding's `folderPath` placeholder differs (`solution_folder` vs `Shared/Production`) and the second binding falls through the [virtual-creation path](#scenario-4--local-virtualasset-without-cloud-counterpart) instead of the import path.
- **Refresh does NOT update the resource's local config** if the cloud-side definition changed (e.g. queue retry count edited in OR after import). Refresh is import-only by design; mutations are reserved for explicit local edits via SW UI or a future `solution resource update` CLI command.
- **At deploy, both projects' runtime dependencies point at the same `resourceKey`.** This is correct — they share the cloud resource. The deploy folder gets one queue (or one link to an existing one if you've used `deploy config link`).
- **At publish/upload time you cannot have two solution-level entries with the same cloud key.** If you accidentally produce that state by hand-editing files, `pack` rejects with a duplicate-key error.

### Verify

```bash
uip solution resource list --source local --kind Queue --output json | jq '.Data[] | select(.Name == "OrdersQueue")'
```

Exactly one entry, with a key that matches the cloud GUID returned by `uip resource queue get OrdersQueue --folder-path "Shared/Production"`.

> See: [develop-solution.md — Step 7: Refresh Resources](develop-solution.md#step-7-refresh-resources).

---

## Scenario 4 — Local virtual asset / queue without cloud counterpart

You're shipping a **brand-new** asset (or queue, or bucket) as part of the solution — it doesn't exist in the target tenant yet. You want it provisioned at deploy time, with a value you'll set per environment.

### Setup

A binding to a resource that **isn't** in cloud:

```json
{ "resource": "asset", "key": "ApiBaseUrl",
  "value": { "name": { "defaultValue": "ApiBaseUrl" },
             "folderPath": { "defaultValue": "solution_folder" } },
  "metadata": { "subType": "StringAsset", "bindingsVersion": "2.2", "solutionsSupport": "true" } }
```

The `folderPath: "solution_folder"` placeholder signals "this resource lives inside the solution, not in a specific cloud folder." Use a real cloud FQN (`"Shared/Production"`) only if you want the asset deployed to that exact folder during `deploy run`.

### What happens at refresh

```
Synced 1 resources (0 already in solution)
```

RCS lookup fails (resource doesn't exist), the sync falls through to `createVirtualResourceAsync`, and the asset is created **as a virtual stub** with a local UUID:

```
resources/solution_folder/asset/stringAsset/ApiBaseUrl.json
```

The stub has `value: ""` (or the type's placeholder default — `false` for boolean, `0` for number).

### Idempotency on re-refresh

Re-running `solution resource refresh` is a no-op for virtuals at the same `(kind, folder, name)` — the second pass detects the existing stub and skips:

```
Synced 0 resources (1 already in solution)
```

If two bindings point at the same name in **different non-`solution_folder` cloud folders**, both create stubs and the second is suffixed `_1` (same SDK uniqueness algorithm as Scenario 1).

### What happens at deploy

`solution deploy run --config-file <path>` validates the deployment config server-side. A virtual asset with no value fails fast:

```
[1009] asset ApiBaseUrl: Invalid argument 'Value'
```

This is **expected** — you must either set a value or link the asset to an existing cloud one before deploy. Two options:

```bash
# Option A: set a value (e.g. environment-specific)
uip solution deploy config set deploy-config.json ApiBaseUrl value "https://api.production.example.com"

# Option B: link to an existing cloud asset
uip solution deploy config link deploy-config.json ApiBaseUrl \
  --name ProductionApiUrl --folder-path "Shared/Production"

# Then deploy
uip solution deploy run -n MyDeployment --package-name MySolution --package-version 1.0.0 \
  --folder-name MySolution --parent-folder-path Shared --config-file deploy-config.json
```

### Gotchas

- **`folderPath: "solution_folder"` vs `"."` vs a real cloud FQN** — all three normalize to "no specific cloud folder" *for the binding*, but the resulting virtual has different `folders[0].fullyQualifiedName` on disk. Stick with `"solution_folder"` (Studio Web's convention) unless you have a reason.
- **Don't set the asset value in `bindings_v2.json` thinking it'll flow through.** Bindings carry name + folder. The value lives in the deploy config (per-environment) or, for virtuals, comes from `deploy config set`.
- **Type-specific required fields** beyond `value`: bucket needs `storageContainer`, others have their own. Refresh fills these with type-appropriate placeholders (empty string / 0 / false). Same `[1009] Invalid argument` deploy error if left at placeholder.
- **A virtual asset has no `referenceKey` in any tool resource file** — bindings reference virtuals by name + folder, not by key. Don't try to copy a stub's UUID into a tool's `referenceKey`.
- **Virtuals are not pushed to RCS by `solution upload`.** Upload writes the solution to Studio Web; the virtual remains local until deploy turns it into a real cloud resource (or you link it to an existing one).

### Verify

```bash
# Virtual exists locally
uip solution resource list --source local --kind Asset --output json

# Deploy config has the resource and its `configuration.value`
uip solution deploy config get MySolution -d deploy-config.json --output json
jq '.resources[] | select(.name == "ApiBaseUrl")' deploy-config.json
```

> See: [pack-and-deploy.md — Configuration Workflow](pack-and-deploy.md#configuration-workflow).

---

## Scenario 5 — Manual edits when the CLI doesn't cover the case

There's no `solution resource update` command yet. When you need to change something on a resource that's already in the solution and `solution resource refresh` is import-only (it reconciles binding additions, not field edits on existing entries), you have three options ordered by preference:

1. **Edit in Studio Web** — `solution upload`, edit in the SW UI, re-export. The proper way; SDK does all the validation and back-references.
2. **`solution deploy config set` / `link` / `unlink`** — for changes that only need to apply at deploy time (per-environment values, link state). Touches only the deploy config file, not the solution-level resources.
3. **Hand-edit the JSON directly** — the escape hatch when neither of the above fits and you don't want a full SW round-trip. Works, but **not ideal** — there's no validation, the SDK can silently undo your change on the next refresh if your edit conflicts with what bindings would re-derive, and structural mistakes corrupt the solution. Use only when you understand which fields the SDK leaves alone.

This scenario covers (3) — what's safe to hand-edit and what's not.

### What the SDK actually compares

`addOrUpdateResourceToSolutionAsync` calls `compareResourceSpecs` to decide if a resource is `Unchanged` / `Updated`. That comparison **looks at `resource.spec` only** (with reference and secret properties excluded). Top-level fields on `resource` (`name`, `key`, `kind`, `description`, `folders`, etc.) are not part of the spec compare — but most of them carry identity or relationship semantics that other parts of the system rely on.

### Solution-level resource files (`resources/solution_folder/<kind>/<name>.json`)

Open the file. The shape is roughly:

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "key": "11de87d3-...",                // identity — never edit
    "name": "MyResource",                 // identity — never edit
    "kind": "asset",                      // identity — never edit
    "type": "stringAsset",                // identity — never edit
    "apiVersion": "orchestrator.uipath.com/v1",  // managed — never edit
    "description": "...",                 // free text — safe to edit
    "isOverridable": true,                // SW link UI toggle — safe but stays `true` in practice
    "dependencies": [...],                // SDK-managed cross-refs — never edit
    "runtimeDependencies": [...],         // computed at pack — never edit
    "files": [...],                       // SDK-managed — never edit
    "folders": [{ "fullyQualifiedName": "solution_folder" }],  // edit moves the resource — risky (see below)
    "spec": {
      "name": "MyResource",               // duplicate of top-level — must stay in sync if you ever edit name
      "type": "Text",                     // identity — never edit
      "value": "",                        // safe to edit (asset value, queue config, bucket retention, etc.)
      "scope": "global",                  // safe but rarely needs editing
      ...                                 // see kind-specific guidance below
    },
    "locks": []                           // SDK-managed — never edit
  }
}
```

| Editable | Why | Caveats |
|---|---|---|
| `resource.description` | Free-text, not referenced by anything | None |
| `resource.spec.<runtime-config>` | The reason most edits exist (asset `value`, queue retry/auto-retry, bucket `tags`/`retentionPeriod`/`retentionAction`, process `tags`/`retentionPeriod`/`hiddenForAttendedUser`/`alwaysRunning`/`autoStartProcess`) | These DO trigger `Updated` on next refresh. That's fine — the next refresh just re-saves with your edited spec. Don't edit reference fields (anything ending in `Reference`, `Ref`, `Key`) by hand. |
| `resource.spec.tags` | List of strings, no relationships | None |
| `resource.isOverridable` | Toggle for whether SW lets bindings link this | Setting to `false` blocks SW link UI — usually leave `true` |

| **Don't edit** | Why |
|---|---|
| `resource.key` | Cross-references everywhere; rename breaks bindings and dependent resources |
| `resource.name` | Bindings find resources by name; rename without updating bindings → bindings unresolved at deploy. SW or `solution upload` round-trip is the only safe way to rename |
| `resource.kind` / `resource.type` / `apiVersion` | Identity — switching kind is "delete + create new", do that explicitly |
| `resource.spec.name` / `resource.spec.type` | Must match top-level; SDK's `compareResourceSpecs` flags any drift |
| `resource.dependencies` | SDK rebuilds these at refresh from `bindings_v2.json`; manual edits get overwritten |
| `resource.runtimeDependencies` | Recomputed at every pack — manual edits lost on next pack |
| `resource.files`, `resource.locks` | Managed; never appear in user-edit scenarios |
| `resource.folders` | Moves the resource. For a *cloud-imported* resource the folder is `solution_folder` (placeholder) — editing it doesn't change cloud location, only confuses sync. For a *virtual* resource that you authored at a non-`solution_folder` folder, edit at the binding (`bindings_v2.json`) and let refresh re-create — don't edit the resource file directly |
| `resource.spec.<reference-fields>` | E.g. `storageBucketReference`, `retentionBucketRef`. The SDK rewrites these when the target's link state changes; hand-edits get clobbered. (Also see [SOL-7051](https://uipath.atlassian.net/browse/SOL-7051) — the rewrite isn't always applied automatically; that's a known bug, not a license to hand-edit dependents arbitrarily) |

### Examples — safe edits

```jsonc
// asset/stringAsset/MyAsset.json — set a default value
"spec": { "name": "MyAsset", "type": "Text", "scope": "global",
          "value": "https://api.production.example.com" }   // ← edit this

// queue/Queue/OrdersQueue.json — change retry count
"spec": { ..., "maxNumberOfRetries": 5, ... }                // ← edit this

// process/api/MyApi.json — change retention
"spec": { ..., "retentionPeriod": 14, ... }                  // ← edit this

// bucket/Bucket/Storage.json — adjust tags
"spec": { ..., "tags": [{ "name": "Env", "value": "prod" }], ... }
```

After any solution-level edit, run a sanity check:

```bash
uip solution resource list --solution-folder . --source local --output json
```

The list should show your resource with the new spec. If `resource refresh` reverts the change on the next run, you edited a field the bindings re-derive — back out and use the deploy-config path or SW UI instead.

### Deploy config files (`deploy-config.json`)

Same principle, looser rules. The deploy config is **per-deployment**, not per-solution — editing it doesn't mutate the solution itself, only what `solution deploy run` provisions. Three editing paths:

1. **`uip solution deploy config set <file> <resource> <prop> <value>`** — preferred. Validated, scoped, idempotent.
2. **`uip solution deploy config link/unlink <file> <resource> ...`** — for binding to existing cloud resources or removing the binding.
3. **Manual JSON edits** — fall back to this when the CLI doesn't cover what you need (e.g. nested cross-reference fields like `configuration.storageBucketReference.key`, or adding a fresh `linkToResource` block from scratch). Same shape as the SDK writes:

```jsonc
{
  "resources": [
    {
      "kind": "asset",
      "name": "MyAsset",
      "resourceKey": "11de87d3-...",
      "folderPaths": ["solution_folder"],
      "configuration": {
        "value": "manually-edited-value",   // ← safe to edit by hand
        "description": "...",                // ← safe
        "tags": [...]                        // ← safe
      },
      "linkToResource": {                    // ← safe to add/remove/edit by hand
        "name": "ProductionAsset",
        "folderPath": "Shared/Production"
      }
    }
  ]
}
```

**Manual editing of the deploy config is not ideal** — there's no schema validation in the CLI, and a bad edit fails server-side at `deploy run` (often with a generic `ValidationFailed`). But it's the pragmatic escape hatch when:

- You need to set a nested property `config set` doesn't expose (e.g. `configuration.storageBucketReference.key` to work around [SOL-7051](https://uipath.atlassian.net/browse/SOL-7051)).
- You're scripting a config transform (CI step injecting per-environment secrets, etc.) and want a single JSON-patch step instead of N CLI calls.
- The CLI surface is missing a flag for the field you need.

In those cases: edit the file, run `uip solution deploy run --config-file <path>`, and let the deploy validation catch any structural mistakes. Deploy errors come back fast and verbose enough to localize the bad field.

> See: [pack-and-deploy.md — Configuration Workflow](pack-and-deploy.md#configuration-workflow) for the standard `set`/`link`/`unlink` flow.

---

## Cross-cutting failure modes

These don't fit a single scenario but bite often enough to call out.

| Symptom | Likely cause | Fix |
|---|---|---|
| `[1009] <kind> <name>: Invalid argument 'Value'` at deploy | Virtual resource without `value` set (Scenario 4) | `deploy config set <file> <name> value <val>` or `deploy config link <file> <name> --name <existing>` |
| `Folder already exists` at deploy | `--folder-name` collides with an existing folder under `--parent-folder-path` | Pick a different `--folder-name`, or `solution deploy uninstall <existing>` first |
| Suffix `_N` keeps growing on re-refresh (`_1`, `_2`, `_3`...) | Old CLI version (pre-suffix-amplification fix) | Upgrade `@uipath/cli` to a build that ships the SDK bump (`resource-builder-sdk` ≥ `2025.11.0-alpha3780`); the current refresh is idempotent on cloud key |
| Tool dialog in Studio Web doesn't open for one of two same-name tools | SW UI bug — affects pure-SW solutions too (Scenario 1) | Verified at deploy/runtime — ignore the UI symptom; check the tool resolves correctly via `resource list --source remote` after deploy |
| Refresh imports 0 of N bindings, no warnings | `bindings_v2.json` not at expected path (project root, not nested) | Move file to `<ProjectName>/bindings_v2.json`; `agent validate` regenerates it for agent projects |
| `processKey` collision on `solution publish` | Republishing same name+version | Bump version (`solution pack --version 1.0.1 …`); the feed rejects duplicate `name+version` pairs |

---

## Related

- [solution.md](solution.md) — Overview, lifecycle diagram, command tree
- [develop-solution.md](develop-solution.md) — Step-by-step: new, project add, refresh, list
- [pack-and-deploy.md](pack-and-deploy.md) — Step-by-step: pack, publish, deploy, configuration
- [activate-and-manage.md](activate-and-manage.md) — Activate, uninstall, manage packages
