# XAML Data Service Activities

Activity patterns for `UiPath.DataService.Activities`. All activities are generic (`<TEntity>`) and operate on Data Fabric entity records.

## Package

`UiPath.DataService.Activities`

## Authoring Decision Tree

Branch on two binary signals before writing any Data Service XAML:

1. **`INSIDE_SOLUTION`** — `true` iff `<PROJECT_DIR>` has an ancestor `.uipx` file. Resolve via the walk-up in [Solution membership and properties](#solution-membership-and-properties) below.
2. **`ScopeValue`** — for solution projects, the value the user picks in Studio Desktop's Folder/Tenant radio. Standalone projects always serialize `"Tenant"`.

| `INSIDE_SOLUTION` | `ScopeValue` | Branch | Entity source | Namespace alias + assembly | `x:TypeArguments` |
|---|---|---|---|---|---|
| `false` | `"Tenant"` | **A** | `<PROJECT_DIR>/.entities/EntitiesStore.json` | `<initial>:` from `DataService.<ProjectName>` | `<initial>:<EntityName>` |
| `true` | `"Tenant"` | **A** | `<PROJECT_DIR>/.entities/EntitiesStore.json` | `<initial>:` from `DataService.<ProjectName>` | `<initial>:<EntityName>` |
| `true` | `"Folder"` | **B** | `<SOLUTION_DIR>/resources/solution_folder/entity/[native/]<Name>.json` | `udacsdeb:` from `DataFabric.Entities.<22-char-hash>` | `udacsdeb:<EntityName>_<UUID-with-dashes-as-underscores>` |

> **Constraint.** Folder scope is solution-only — there is no fourth row. If the user wants Folder scope but no `.uipx` exists, route them through [xaml/data-service-project-shape-guide.md](../../../xaml/data-service-project-shape-guide.md) to pick (or convert) the project shape before continuing.

Branch A or B determines the fill-in for every downstream section ([Prerequisites](#prerequisites), [XAML Namespace Declarations](#xaml-namespace-declarations), [Generic Type Argument](#generic-type-argument)). Downstream is mechanical — pick the branch from the table, then follow its sub-section in each.

## Solution membership and properties

Solution-awareness is required only when authoring Data Service activities — this section is the source of truth for the walk-up algorithm, property names, and on-disk locations used by Branch B above.

### Walk up to find the solution

Walk parent directories of `<PROJECT_DIR>` until either a `.uipx` file is found or the filesystem root is reached.

```text
dir = projectRoot
while dir != filesystem root:
    if any *.uipx in dir:
        SOLUTION_DIR = dir
        SOLUTION_FILE = <the .uipx>
        SOLUTION_ID   = (read "SolutionId" field from the JSON manifest)
        INSIDE_SOLUTION = true
        break
    dir = parent(dir)
```

Mirrors `solution-sdk`'s `findNearestParentUipxFile(startDir)`. Works from inside the project directory or the solution directory.

If no `.uipx` is found, `INSIDE_SOLUTION=false` — only Tenant scope is available; see Branch A.

### List Folder-scoped entity artefacts

Once `SOLUTION_DIR` is set, navigate to `<SOLUTION_DIR>/resources/solution_folder/entity/`. If a `native/` subdirectory exists (Studio Desktop's current layout), use that path instead. Each `*.json` file inside is a Folder-scoped entity artefact for Data Service:

- `resource.key` field → `SolutionEntityKey` (resource UUID; also the `EntityId` and the suffix in `x:TypeArguments="udacsdeb:<EntityName>_<UUID-with-dashes-as-underscores>"`)
- `resource.name` field → `SolutionEntityName` (display name; the runtime `BindingsKey` lookup)
- `resource.spec.resourceJson` → stringified entity schema (same shape as one `EntitiesStore.json:Entities[*]` entry)

For the merged local + remote view (including entities in the tenant that aren't yet added to the solution), use the CLI; see [Discovering values for XAML](#discovering-values-for-xaml).

### JIT bundle DLL (the assembly referenced by `xmlns:udacsdeb`)

Three project-local files describe the JIT bundle:

| File | Size | Role |
|---|---|---|
| `<PROJECT_DIR>/.project/JitCustomTypes.json` | ~200 B | Pointer — `bundleHash` only, no schema. Names the cache directory below. |
| `<PROJECT_DIR>/.project/JitCustomTypesSchema.json` | ~25 KB+ | Bundle definition — `jitAssemblyCompilerCommands[0].bundleOptions.entitiesBundle.Types` carries every CLR type's property list, attributes, and enum values that Studio JIT-compiles. |
| `<PROJECT_DIR>/.local/.customtypes/EntitiesBundle_<bundleHash>/DataFabric.Entities.<22-char-suffix>.dll` | precompiled assembly | The actual DLL Studio emits at design time. Suffix matches the `xmlns:udacsdeb` `assembly=...` value and the `AssemblyReference` in `TextExpression.ReferencesForImplementation`. |

`bundleHash` (in `JitCustomTypes.json` and the cache directory name) and the DLL filename suffix are two different deterministic identifiers — both derived from bundle content, but used in different namespaces. The directory is keyed by `bundleHash`; the assembly is keyed by `<suffix>`.

**Runtime story.** This is structurally identical to Branch A: Studio precompiles a real .NET assembly at design time, parks it under `.local/`, and pack bundles it into the deployment archive. The robot loads it at runtime like any other referenced assembly. No runtime JIT, no `AssemblyResolve` hook needed beyond the standard package-relative resolution. If validation says `Cannot create unknown type '...DataFabric.Entities.Bundle}EntityName_<UUID>'`, the bundle DLL is stale or missing — re-open the project in Studio Desktop to regenerate.

### Publishing implication

Solution-resident projects that author Data Service activities must NOT be packed and uploaded standalone via `uip rpa pack` + `uip or packages upload`. Such a `.nupkg` does not carry `resources/solution_folder/` (the solution-level resource artefacts), so Orchestrator's `resourceOverwrites` never gets populated and Folder-scoped Data Service activities lose their `X-UiPath-FolderPath` injection at runtime. The JIT bundle DLL itself ships in the package regardless (it's a normal assembly reference), so the runtime can still construct entity instances — but every API call hits tenant-level routing or 404s. Use `uip solution pack` / `solution publish` / `solution deploy` via [`/uipath:uipath-solution`](../../../../../uipath-solution/SKILL.md) instead.

## Prerequisites

Branch on `INSIDE_SOLUTION` (see [Solution membership and properties](#solution-membership-and-properties) above). Source-of-truth for entity schema and CLR types differs by branch.

### Branch A — Standalone or Tenant scope (`INSIDE_SOLUTION=false`, or solution project with `ScopeValue="Tenant"`)

1. **Package dependency**: `UiPath.DataService.Activities` in `project.json` `dependencies`
2. **Entity import**: Studio > Data Service tab > "Import Entities" pulls entity definitions from the tenant. Studio generates a compiled assembly at `.local/.entities/<hash>/DataService.<ProjectName>.dll`.
3. **`entitiesStores` in project.json** (populated for this branch):
   ```json
   "entitiesStores": [
     {
       "serviceDocument": ".entities/EntitiesStore.json",
       "namespace": "<ProjectName>"
     }
   ]
   ```
4. **Entity metadata** lives in `.entities/EntitiesStore.json` — look up entity IDs, field IDs, field names, types, required flags here.

**Stop conditions (Branch A).** Before any Data Service activity:
1. Read `project.json` → `entitiesStores`. Missing / empty / no entries → **stop**: "No entity stores configured. Import entities via Studio > Data Service tab > Import Entities, then retry."
2. Read `entitiesStores[0].serviceDocument`; check file exists. Missing → **stop**: "EntitiesStore.json not found. Import at least one entity via Studio > Data Service tab > Import Entities, then retry."
3. Read `EntitiesStore.json` → `Entities`. Empty → **stop**: "EntitiesStore.json contains no entities. Import entities via Studio, then retry."

Only entities explicitly imported via Studio have CLR types in the generated DLL. An entity present in `EntitiesStore.json` but not imported produces: `Cannot create unknown type '{clr-namespace:...}EntityName'`.

### Branch B — Solution Folder scope (`INSIDE_SOLUTION=true` AND `ScopeValue="Folder"`)

1. **Package dependency**: same as Branch A.
2. **Entity pick via Studio**: Studio Desktop's `SolutionResourcesWidget` (Folder/Tenant radio + entity picker) writes the entity to the solution. No `EntitiesStore.json` is produced for this branch.
3. **`entitiesStores` in project.json**: `[]` (empty). Studio Desktop intentionally leaves it empty for Folder-scope projects.
4. **Solution resource artefact**: lives at `<SOLUTION_DIR>/resources/solution_folder/entity/native/<EntityName>.json` (preferred) or `<SOLUTION_DIR>/resources/solution_folder/entity/<EntityName>.json` (older layout). Match either path. The `key` field is the entity UUID (= `SolutionEntityKey`); `name` is the display name (= `SolutionEntityName`); `spec.resourceJson` carries the full schema.
5. **JIT bundle**: schema lives in `<PROJECT_DIR>/.project/JitCustomTypesSchema.json` (`jitAssemblyCompilerCommands[0].bundleOptions.entitiesBundle.Types`); `<PROJECT_DIR>/.project/JitCustomTypes.json` is a small pointer file holding just `bundleHash`; the precompiled DLL lives at `<PROJECT_DIR>/.local/.customtypes/EntitiesBundle_<bundleHash>/DataFabric.Entities.<22-char-suffix>.dll`. See [JIT bundle DLL](#jit-bundle-dll-the-assembly-referenced-by-xmlnsudacsdeb) below.
6. **Binding contract**: `<PROJECT_DIR>/.project/PackageBindingsMetadata.json` declares one entry per Data Service activity type (see [Binding source by surface](#binding-source-by-surface) below).

**Stop conditions (Branch B).** Before any solution-scoped Data Service activity:
1. Walk `<SOLUTION_DIR>/resources/solution_folder/entity/[native/]`. No artefact for `<EntityName>` → **stop**: "Entity `<EntityName>` not registered in the solution. Pick it via Studio Desktop's entity picker (Folder scope) or via Studio Web, then retry."
2. Check `<PROJECT_DIR>/.project/JitCustomTypes.json` (pointer) and `<PROJECT_DIR>/.local/.customtypes/EntitiesBundle_<bundleHash>/DataFabric.Entities.<suffix>.dll` (precompiled DLL); if either is absent, the JIT bundle hasn't been built — re-open the project in Studio Desktop to regenerate.
3. For schema lookups, read `spec.resourceJson` from the artefact in step 1 (it is a stringified JSON with the same shape as `EntitiesStore.json:Entities[*]`).

### Entity Lookup Scope

- **Branch A**: read `EntitiesStore.json` only from the current project. Resolve the path via `project.json` → `entitiesStores[0].serviceDocument`. Do not search sibling directories or other projects. If the needed entity isn't there, ask the user to import it via Studio > Data Service tab > "Import Entities".
- **Branch B**: read from `<SOLUTION_DIR>/resources/solution_folder/entity/[native/]<EntityName>.json`. Do not fall back to `EntitiesStore.json` — it is empty for this branch.

## XAML Namespace Declarations

Two conventions exist. Pick by branch.

Shared (both branches):

```xml
xmlns:uda="clr-namespace:UiPath.DataService.Activities;assembly=UiPath.DataService.Activities.Core"
xmlns:udam="clr-namespace:UiPath.DataService.Activities.Models;assembly=UiPath.DataService.Activities.Core"
xmlns:udd="clr-namespace:UiPath.DataService.Definition;assembly=UiPath.DataService.Definition"
xmlns:upr="clr-namespace:UiPath.Platform.ResourceHandling;assembly=UiPath.Platform"
```

The `upr` namespace is required for file activity variables — `DownloadFileFromRecordField.DownloadedFileResource` outputs `upr:ILocalResource`. See [DownloadFileFromRecordField](activities/DownloadFileFromRecordField.md).

### Branch A — Standalone / Tenant entity types

```xml
xmlns:<initial>="clr-namespace:<ProjectName>;assembly=DataService.<ProjectName>"
```

- `<initial>` is Studio-derived (first letter of `ProjectName`, lowercased — e.g. `b:` for `BlankProcess`). The docs use `local:` as the placeholder in examples; any short alias works.
- Must include `assembly=DataService.<ProjectName>`. Without the assembly qualifier the XAML parser cannot locate entity types: `Cannot create unknown type '{clr-namespace:<ProjectName>}EntityName'`.

Imports for `TextExpression.NamespacesForImplementation`:

```xml
<x:String>UiPath.DataService.Activities</x:String>
<x:String>UiPath.DataService.Activities.Models</x:String>
<x:String>UiPath.DataService.Definition</x:String>
<x:String>UiPath.Platform.ResourceHandling</x:String>
<x:String><ProjectName></x:String>
```

Assembly references for `TextExpression.ReferencesForImplementation`:

```xml
<AssemblyReference>UiPath.DataService.Activities.Core</AssemblyReference>
<AssemblyReference>UiPath.DataService.Definition</AssemblyReference>
<AssemblyReference>UiPath.Platform</AssemblyReference>
<AssemblyReference>DataService.<ProjectName></AssemblyReference>
```

### Branch B — Solution Folder-scope entity types

```xml
xmlns:udacsdeb="clr-namespace:UiPath.DataService.Activities.Core.SWEntities.DataFabric.Entities.Bundle;assembly=DataFabric.Entities.<22-char-hash>"
```

- `<22-char-hash>` is content-addressed from the JIT bundle definition. Read the actual value from the project — either the DLL filename at `<PROJECT_DIR>/.local/.customtypes/EntitiesBundle_<bundleHash>/DataFabric.Entities.<suffix>.dll`, or the existing `xmlns:udacsdeb` / `AssemblyReference` in the project's XAML files. Adding / removing / mutating entities in the bundle changes the suffix. Do not hard-code.
- The alias `udacsdeb` is Studio's convention; any short alias resolves at parse time, but Studio Desktop's serializer always writes `udacsdeb`.

Imports for `TextExpression.NamespacesForImplementation`:

```xml
<!-- standard shared xmlns omitted -->
<x:String>UiPath.DataService.Activities.Core.SWEntities.DataFabric.Entities.Bundle</x:String>
```

Assembly references for `TextExpression.ReferencesForImplementation`:

```xml
<AssemblyReference>UiPath.DataService.Activities.Core</AssemblyReference>
<AssemblyReference>UiPath.DataService.Definition</AssemblyReference>
<AssemblyReference>UiPath.Platform</AssemblyReference>
<AssemblyReference>DataFabric.Entities.<22-char-hash></AssemblyReference>
```

The `DataService.<ProjectName>` assembly is NOT referenced for Branch B — entity CLR types live in the JIT bundle, not in the per-project entities DLL.

## Activity Categories

| Category | Activities | Description |
|----------|-----------|-------------|
| **DataService.Entity Record** | `CreateEntityRecord`, `UpdateEntityRecord`, `DeleteEntityRecord`, `GetEntityRecordById`, `QueryEntityRecords` | Single-record CRUD operations |
| **DataService.Batch** | `CreateMultipleEntityRecords`, `UpdateMultipleEntityRecords`, `DeleteMultipleEntityRecords` | Bulk operations on multiple records |
| **DataService.File** | `UploadFileToRecordField`, `DownloadFileFromRecordField`, `DeleteFileFromRecordField` | File attachment operations on entity fields |

## Generic Type Argument

All activities use `x:TypeArguments` — the value **must** be a concrete entity type, never `udd:IEntity`. The concrete form differs by branch:

```xml
<!-- Wrong — interface is rejected -->
<uda:CreateEntityRecord x:TypeArguments="udd:IEntity" ... />

<!-- Branch A (standalone / Tenant) -->
<uda:CreateEntityRecord x:TypeArguments="local:YourEntityName" ... />

<!-- Branch B (solution Folder scope) -->
<uda:CreateEntityRecord x:TypeArguments="udacsdeb:YourEntityName_<UUID-with-dashes-as-underscores>" ... />
```

Branch B's type name is `<EntityName>_<UUID-with-dashes-as-underscores>`. The UUID is `SolutionEntityKey` with dashes replaced by underscores — e.g. `FolderEntity` with key `cb998ac2-2056-f111-8fcb-000d3a32b519` becomes `udacsdeb:FolderEntity_cb998ac2_2056_f111_8fcb_000d3a32b519`. The suffix uniquely identifies the JIT-compiled CLR type inside the project's `DataFabric.Entities.<hash>` bundle.

> **Same-name constraint.** Even though the JIT type name includes the UUID, a solution cannot host two entities with the same `name` — Studio rejects the second add with `Resource was not added to the solution` (the runtime `BindingsKey` lookup is keyed on `SolutionEntityName` alone, so two same-named Folder-scoped resources in one solution would collide at runtime). To reach two same-named entities from different tenant folders, use separate solutions / projects. See [xaml/data-service-project-shape-guide.md § Constraints](../../../xaml/data-service-project-shape-guide.md#constraints).

Using `udd:IEntity` produces: `Selected Entity type (UiPath.DataService.Definition.IEntity) is not valid`.

## Shared Properties (All Activities)

| Property | Type | Default | Category | Description |
|----------|------|---------|----------|-------------|
| `EntityId` | `InArgument<Guid>` | — | — | Entity GUID from `EntitiesStore.json` → `Entities[].Id` |
| `ContinueOnError` | `InArgument<bool>` | `false` | Common | Continue workflow on activity error |
| `TimeoutInMs` | `InArgument<int>` | `30000` | Common | Timeout in milliseconds |

### Solution Scope Properties (Conditional)

These three properties exist on every activity's base class. Studio writes all three as explicit XAML literals on **every** activity — including standalone / Tenant — never omits them. Studio only renders the higher-level Scope radio + entity picker that populate them when the project has a non-empty `SolutionId`; otherwise the picker is the legacy Tenant entity dropdown but the three properties are still serialized. They are never user-typed.

Concrete observed serialization:

| Context | `ScopeValue` | `SolutionEntityKey` | `SolutionEntityName` |
|---|---|---|---|
| Standalone (no solution) | `"Tenant"` | `"{x:Null}"` | `"{x:Null}"` |
| Solution, Scope = Tenant | `"Tenant"` | `"{x:Null}"` | `"{x:Null}"` |
| Solution, Scope = Folder | `"Folder"` | `"<entity-UUID>"` | `"<EntityName>"` |

See [Solution Context](#solution-context-folder-vs-tenant-scope) for runtime semantics.

| Property | Type | Set by | Read at |
|----------|------|--------|---------|
| `ScopeValue` | `InArgument<string>` | Scope radio (`"Folder"` / `"Tenant"`) | Runtime: gates `BindingsKey` (Folder → `SolutionEntityName.literal`; Tenant or null → no key). Not sent to API. |
| `SolutionEntityKey` | `InArgument<string>` | Entity picker — `key` field of the selected solution resource | Design time only: fetches entity schema JSON via `ISolutionResources.GetResourceConfigurationAsync(key)`. **Never read at runtime.** |
| `SolutionEntityName` | `InArgument<string>` | Entity picker — `name` field of the selected solution resource | Both: design-time entity binding contract; runtime lookup key for `Entity.<name>.folderPath` (see [Runtime mechanism](#runtime-mechanism-folder-vs-tenant)). |

## Entity Metadata — EntitiesStore.json (Branch A) and `spec.resourceJson` (Branch B)

Branch A reads metadata from `.entities/EntitiesStore.json`. Branch B reads the same shape from `spec.resourceJson` (stringified JSON) inside the solution resource artefact at `resources/solution_folder/entity/[native/]<EntityName>.json` — same field schema (`Fields[].Id`, `Name`, `SqlType`, `IsSystemField`, `IsRequired`, `FieldDisplayType`, `ReferenceEntity`).

`EntitiesStore.json` structure (Branch A; Branch B's `spec.resourceJson` matches one `Entities[]` entry):

```json
{
  "StoreUrl": "https://<tenant-url>/datafabric/<TenantName>/dataservice_/entities",
  "Entities": [
    {
      "Id": "<entity-guid>",
      "Name": "EntityName",
      "Fields": [
        {
          "Id": "<field-guid>",
          "Name": "FieldName",
          "IsSystemField": false,
          "IsRequired": true,
          "SqlType": { "Name": "NVARCHAR", "LengthLimit": 300, "MaxValue": null, "MinValue": null, "DecimalPrecision": null },
          "FieldDisplayType": "Basic",
          "ReferenceEntity": null
        },
        {
          "Id": "<field-guid>",
          "Name": "RelationshipFieldName",
          "IsSystemField": false,
          "IsRequired": false,
          "SqlType": { "Name": "UNIQUEIDENTIFIER" },
          "FieldDisplayType": "Relationship",
          "ReferenceEntity": { "Name": "ReferencedEntityName", "Id": "<referenced-entity-guid>", "FolderId": "<folder-guid>" }
        }
      ]
    }
  ]
}
```

> `EntitiesStore.json` contains **all entities in the tenant** after the first entity import — not just the imported one. However, only explicitly imported entities have CLR types in the generated DLL.

**System fields** (`IsSystemField: true`) — `Id`, `CreateTime`, `UpdateTime`, `CreatedBy`, `UpdatedBy` — are managed by Data Service. Skip them when building field bindings for Create/Update activities.

## SqlType to XAML Type Mapping

| SqlType.Name | x:TypeArguments | Notes |
|-------------|-----------------|-------|
| `NVARCHAR` | `x:String` | Text fields |
| `MULTILINE` | `x:String` | Multi-line text |
| `INT` | `x:Int32` | Integer |
| `BIGINT` | `x:Int64` | Long integer |
| `FLOAT` | `x:Double` | Floating-point |
| `DECIMAL` | `x:Decimal` | Decimal number |
| `BIT` | `x:Boolean` | True/false |
| `DATETIMEOFFSET` | `x:String` | Pass as ISO 8601 string |
| `DATE` | `x:String` | Pass as ISO 8601 date string |
| `UNIQUEIDENTIFIER` | `x:String` | Pass as GUID string |

## FieldDisplayType Values

| FieldDisplayType | Meaning |
|-----------------|---------|
| `Basic` | Standard scalar field (text, number, boolean, date) |
| `Relationship` | Foreign key reference to another entity (ManyToOne) |
| `File` | File attachment field |
| `ChoiceSetSingle` | Single-select choice set |
| `ChoiceSetMultiple` | Multi-select choice set |
| `AutoNumber` | Auto-incrementing numeric field |

## Solution Context (Folder vs Tenant Scope)

Activities behave differently when the host project lives inside a `.uipx` solution. The switch is `IUserDesignContext.SolutionId` (Studio Desktop or Web — product does not matter). When non-empty, Studio renders solution-aware controls; runtime resolves the folder path from bindings injected by Orchestrator.

### What Studio renders

Studio never exposes the three raw XAML properties (`ScopeValue`, `SolutionEntityKey`, `SolutionEntityName`) in the property grid. They stay `IsVisible=false` and are written by rules from these higher-level controls:

| Control | Visible when | Type | Writes |
|---------|--------------|------|--------|
| `Scope` | `SolutionId` is non-empty | `RadioGroup` — `Folder` / `Tenant` (resource keys `EntityFolderScope`, `EntityTenantScope`) | `ScopeValue` |
| `SolutionEntity` | `SolutionId` non-empty AND `Scope == "Folder"` | `SolutionResourcesWidget` (`ResourceType="entity"`, `ExpectedProperties=["name","key"]`) | `SolutionEntityKey` ← `key`, `SolutionEntityName` ← `name`, and re-morphs the generic `TEntity` type via `EntityJitter` + `IDesignerCustomTypesService` |
| `Entity` (legacy picker) | `SolutionId` empty OR `Scope == "Tenant"` | Studio's classic entity dropdown (populated from `IDesignerDataService.GetEntities()`) | `EntityId` + assembly-cached entity DTO |

Toggling `Scope` Folder→Tenant clears `SolutionEntity.Value`, `SolutionEntityKey.Value`, `SolutionEntityName.Value`, `Entity.Value` and re-initializes the entity picker (`BaseSolutionResourceActivityViewModel.UpdateEntityChoiceOnScope`).

### Runtime mechanism (Folder vs Tenant)

Runtime ignores `SolutionEntityKey` entirely. The activity computes `BindingsKey` from `SolutionEntityName` only when `ScopeValue == "Folder"`:

```text
BindingsKey = (ScopeValue == "Folder") ? SolutionEntityName.literal : null
folderPath  = BindingsHelper.GetBindingValue($"Entity.{BindingsKey}.folderPath", ...)
            // resolves from Orchestrator's resourceOverwrites for the current process
if (folderPath != null) headers["X-UiPath-FolderPath"] = folderPath
```

- **Folder scope, binding present** → `X-UiPath-FolderPath: <folderPath>` injected on every HTTP call (Create/Update/Delete/Query/File). Data Service routes the operation to that folder's entity instance.
- **Folder scope, binding missing** → no header; falls through to tenant resolution by entity name.
- **Tenant scope** → `BindingsKey` is `null`; no header; tenant-level routing.
- **Standalone** → Studio writes `ScopeValue="Tenant"` + `SolutionEntityKey="{x:Null}"` + `SolutionEntityName="{x:Null}"`. Behavior identical to Tenant. If a XAML happens to contain stale `ScopeValue="Folder"` + `SolutionEntityName=<x>` literals from a previous solution context, the runtime still attempts the bindings lookup — but `resourceOverwrites` won't contain a matching entry outside a deployed solution, so the header is omitted and behavior collapses to Tenant. Not destructive.

`SolutionEntityKey` is design-time only: it's the lookup key for `ISolutionResources.GetResourceConfigurationAsync(key)`, which returns the entity schema JSON (used to JIT-compile the `TEntity` CLR type into the in-memory `DataService.<ProjectName>` assembly).

### Binding source by surface

Where the per-entity binding (`name` + `folderPath` that hydrates `resourceOverwrites` at deploy) lives on disk depends on the authoring surface. All surfaces converge to the same `Entity.<SolutionEntityName>.folderPath` lookup at runtime.

#### Studio Desktop (RPA projects)

Canonical binding contract: `<PROJECT_DIR>/.project/PackageBindingsMetadata.json`. One entry per Data Service activity TYPE (per generic-arity-1 class). Example entry from a real Studio Desktop solution project:

```json
"UiPath.DataService.Activities.CreateEntityRecord`1": [{
  "Type": "Entity",
  "PublishNullValues": false,
  "Key":    { "Value": "BindingsKey", "ValueSource": "Property" },
  "Values": {
    "folderPath": { "Value": "",            "ValueSource": "Property" },
    "name":       { "Value": "BindingsKey", "ValueSource": "Property" }
  },
  "Arguments": {
    "Scope":           { "Value": "ScopeKey", "ValueSource": "Property" },
    "BindingsVersion": { "Value": "2.2",       "ValueSource": "Constant" }
  },
  "SubBindings": [],
  "DefaultValueSource": "Property"
}]
```

The entity itself is declared once per solution at `<SOLUTION_DIR>/resources/solution_folder/entity/[native/]<EntityName>.json` — that artefact carries the UUID (`key`), display name (`name`), and full schema (`spec.resourceJson`). Studio Desktop writes the artefact directly when the user picks an entity in the Folder-scope picker.

Studio Desktop does **NOT** produce `bindings_v2.json` for RPA projects. `uip solution resource refresh` against a Studio Desktop RPA project reports `Created: 0, Imported: 0, Skipped: 0` (expected — nothing to read).

#### Studio Web (RPA) / Maestro Flow / Maestro Case scaffold projects

Project-level `bindings_v2.json` is produced and maintained by those surfaces. Schema (one entry per solution-scoped entity):

```json
{
  "resourceType": 6,
  "originalResourceType": "Entity",
  "dynamicValues": {
    "name":       { "defaultValue": "<SolutionEntityName>", "isExpression": false },
    "folderPath": { "defaultValue": "<folder-or-special>",  "isExpression": false }
  }
}
```

- `dynamicValues.name.defaultValue` matches the XAML `SolutionEntityName` and is the runtime lookup key.
- `dynamicValues.folderPath.defaultValue` is the value Orchestrator injects as `X-UiPath-FolderPath`. The sentinel values `"."` and `"solution_folder"` are normalized to undefined → tenant scope.
- `uip solution resource refresh` reads these files and creates / reconciles matching solution resources (kind `Entity`) under `resources/solution_folder/entity/`.

#### Runtime (both surfaces)

At deploy time `solution pack` bundles `resources/solution_folder/` into the `.uipx`. Orchestrator hydrates `resourceOverwrites` from the deployment's resource bindings. The activity reads `Entity.<SolutionEntityName>.folderPath` via `BindingsHelper.GetBindingValue(...)` and, when non-empty, injects `X-UiPath-FolderPath: <folderPath>` on every HTTP request.

### Discovering values for XAML

When authoring a solution-scoped Data Service activity, do NOT hand-pick GUIDs or names. Use the solution CLI from inside `<SOLUTION_DIR>`:

```bash
uip solution resource list --kind Entity --output json
```

Each entry's `Key` is the `SolutionEntityKey` (resource UUID); `Name` is the `SolutionEntityName`. The output is the merged local + remote view. Example (from a Studio Desktop solution with one entity bound and one tenant-side entity that hasn't been added to the solution):

```json
{ "Data": [
  { "Source": "Local",
    "Key":  "62e14a38-9753-f111-8fcb-000d3a45fabb",
    "Name": "FolderScopedEntity",
    "Kind": "entity",
    "Folder": "solution_folder" },
  { "Source": "Remote",
    "Key":       "cb998ac2-2056-f111-8fcb-000d3a32b519",
    "Name":      "FolderEntity",
    "Kind":      "Entity",
    "Type":      "Native",
    "Folder":    "Shared",
    "FolderKey": "812fcfbd-091c-4fdc-8ee5-89a4f4fac189" } ] }
```

Schema differences worth normalizing when comparing entries:

| Field | Local entry | Remote entry |
|---|---|---|
| `Kind` | `"entity"` (lowercase) | `"Entity"` (capitalized) |
| `Type` | absent | `"Native"` for native entities |
| `Folder` | `"solution_folder"` (sentinel) | source folder name (e.g. `"Shared"`) |
| `FolderKey` | absent | folder UUID |

Use case-insensitive comparison on `Kind`. Tolerate missing `Type` / `FolderKey` on local entries.

For the full resource spec on a given UUID:

```bash
uip solution resource get <KEY> --output json
```

For Studio Web / Maestro projects, after editing `bindings_v2.json` (e.g., adding a new entity reference) sync the solution:

```bash
uip solution resource refresh --output json
```

Studio Desktop RPA projects do not need `refresh` — Studio writes the resource artefact directly when the entity is picked. Running `refresh` against a Studio Desktop project is a harmless no-op (`Created: 0, Imported: 0, Skipped: 0`).

These commands live in the `uipath-solution` skill — see [develop-solution.md](../../../../../uipath-solution/references/operate/develop-solution.md) for the full lifecycle (init → project add → resource refresh → pack → publish → deploy).

> **Cross-skill scope.** The `uip df` CLI in `uipath-data-fabric` is tenant-only — no `--solution-id`, no `--folder-path`. Do not use `uip df entities list` to populate `SolutionEntityKey` / `SolutionEntityName`. Use `uip solution resource list --kind Entity` instead.

### Key rule

`SolutionId` presence is the only signal. Do not branch on Studio Desktop vs Studio Web, or on `targetFramework`. If the project has a non-empty `SolutionId` and the entity lives in solution resources, Folder scope is the default; otherwise Tenant.

## Common Pitfalls

- `x:TypeArguments` must be a concrete entity type — `udd:IEntity` is rejected at validation. Branch A: `<initial>:EntityName`. Branch B: `udacsdeb:EntityName_<sanitized-UUID>`.
- Branch A namespace must include the full `assembly=DataService.<ProjectName>` qualifier. Branch B namespace must include `assembly=DataFabric.Entities.<22-char-suffix>` (read the suffix from the DLL filename at `<PROJECT_DIR>/.local/.customtypes/EntitiesBundle_<bundleHash>/`, or from an existing `xmlns:udacsdeb` / `AssemblyReference` in the project's XAML).
- Branch A: `EntitiesStore.json` contains all tenant entities, but only explicitly imported ones have CLR types in the generated DLL. If validation returns `Cannot create unknown type '{clr-namespace:...}EntityName'` — **stop and ask the user** to import the entity via Studio > Data Service tab > "Import Entities". Do not attempt to fix this by changing namespaces or assembly references.
- Branch B: if validation returns `Cannot create unknown type '{clr-namespace:UiPath.DataService.Activities.Core.SWEntities.DataFabric.Entities.Bundle}EntityName_<UUID>'`, the JIT bundle DLL is stale or missing under `.local/.customtypes/`. Re-open the project in Studio Desktop to regenerate; the assembly suffix and `bundleHash` will refresh together.
- For Create / Update activities, populate two things and let Studio's serializer choose `IsInRecordView`:
  1. **`InputEntityInFieldView`** — object-initializer expression (runtime reads this when `IsInRecordView` is false / null).
  2. **`RecordState.SelectedFields`** — field GUIDs and values (Studio card UI reads this).
  Studio Desktop writes `IsInRecordView="{x:Null}"` on the activity element and `<udam:RecordState IsInRecordView="False" ...>` on the inner state. At runtime, `IsInRecordView.Get(context)` defaults `null` to `false` (`BaseViewModelWithTwoViews.cs:78-81`, `UpdateEntityRecord.cs:72`), so the runtime reads `InputEntityInFieldView`. Either `"{x:Null}"` or `"[False]"` on the activity is accepted by validate + build — match what Studio writes (`{x:Null}`) to keep diffs clean.
  Do NOT use `InputEntity` — Studio syncs `SelectedFields` → `InputEntityInFieldView` on load but never syncs `SelectedFields` → `InputEntity`, causing desync bugs.
- Entity fields are NOT WF4 properties on the activity — they must be set via `InputEntityInFieldView` expression and `RecordState.SelectedFields`, not as `<uda:CreateEntityRecord.FieldName>`
