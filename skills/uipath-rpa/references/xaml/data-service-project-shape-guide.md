# Data Service — Project Shape Guide (Solution vs Standalone)

**Scope.** This guide covers project-shape selection only when the automation uses `UiPath.DataService.Activities` (Data Fabric entities). It does not address other resource types.

The decision is a project-level architectural choice. Make it **before** running `uip rpa init` or `uip solution init` — converting Solution → Standalone is destructive (see [Reversibility](#reversibility) below).

## Decision

| Data Service need | Project shape | Why |
|---|---|---|
| Workflow targets a Tenant-scoped entity only | **Standalone** (`uip rpa init`) | Tenant-scoped entities work in both standalone and solution shapes; standalone has lower lifecycle overhead. |
| Workflow targets a Folder-scoped entity | **Solution** (`uip solution init`) | Folder scope requires the solution layer — `<SOLUTION_DIR>/resources/solution_folder/entity/[native/]<Name>.json` → Orchestrator `resourceOverwrites` → `X-UiPath-FolderPath` header. Standalone projects cannot bind Folder-scoped entities. |
| Multiple processes in one solution will share a Data Service entity | **Solution** | One resource artefact per solution; every member project sees the same `(key, name)` pair. |
| Throwaway / prototype hitting one tenant entity | **Standalone** | Avoid solution lifecycle cost. |

**Default.** Standalone, unless the user named "solution" / `.uipx` / a Folder-scoped requirement. If ambiguous, ask — never silently pick Solution.

## Constraints

- **One entity name per solution.** Two entities with the same `name`, even if they live in different tenant folders, cannot both be Folder-scoped resources in the same solution. Adding the second yields:
  > `Resource was not added to the solution`
  > `Error: System.Exception: Resource was not added to the solution, HResult -2146233088`

  This is by design — the runtime `BindingsKey` lookup is keyed on `SolutionEntityName` alone, so two same-named Folder-scoped resources in one solution would collide. To reach two same-named entities from different tenant folders, split them across separate solutions / projects.

## Reversibility

- **Standalone → Solution** — non-destructive. From the parent directory: `uip solution init <SolutionName>` then `uip solution project add <projectPath>`. The standalone project becomes a solution member; nothing in the project itself is rewritten.
- **Solution → Standalone** — destructive. Tearing down the `.uipx` discards `resources/solution_folder/**` and any Folder-scoped activity bindings in member projects break at runtime. Convert by copying the project out of the solution tree and stripping Folder-scoped activity references manually.

## Next steps

| Decision | Route to |
|---|---|
| Standalone chosen | [environment-setup.md § `uip rpa init` flag selection](../environment-setup.md#uip-rpa-init-flag-selection) |
| Solution chosen | [`/uipath:uipath-solution`](../../../uipath-solution/SKILL.md) for `init` / `project add` / `pack` / `publish` / `deploy` |
| Branch routing within Data Service (`INSIDE_SOLUTION` × `ScopeValue` → A or B) | [activity-docs/UiPath.DataService.Activities/25.9/overview.md § Authoring Decision Tree](../activity-docs/UiPath.DataService.Activities/25.9/overview.md#authoring-decision-tree) |
