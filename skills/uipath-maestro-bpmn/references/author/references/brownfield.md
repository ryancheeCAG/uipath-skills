# Brownfield Authoring

Use this journey when inspecting or editing an existing Maestro BPMN Process Orchestration project.

## Steps

1. Inventory local files: BPMN source, project metadata, generated JSON, and any package output.
2. Identify the primary `.bpmn` source file and preserve imported extension XML.
3. Parse the BPMN mentally before editing: definitions, root process, diagrams, IDs, variables, bindings, entry points, and service extensions.
4. Classify requested edits as model-owned XML, CLI-owned enrichment, generated package metadata, or cloud lifecycle.
5. Make reviewable source edits in `.bpmn` for model-owned XML.
6. For Integration Service changes, follow [plugins/integration-service/impl.md](plugins/integration-service/impl.md) and use CLI enrichment where available.
7. Reconcile IDs, sequence flows, gateway defaults, boundary attachments, and diagram geometry.
8. Run local validation from [validation.md](validation.md).
9. Summarize whether generated JSON needs regeneration before Operate.

## Preservation rules

- Preserve unknown `uipath:*` extension elements.
- Preserve existing `uipath:migrationVersion` values.
- Preserve tags unless the user asks to remove them.
- Preserve generated JSON for comparison, but do not treat it as the source of truth over BPMN.

## Red flags

- BPMN imports without any diagram.
- A diagram plane references a missing process, collaboration, or subprocess.
- Rendered elements lack shapes or waypoints.
- Entry point variables reference the wrong start event.
- Context values reference missing bindings.
- Integration Service elements contain hand-authored connection details.
- Generated JSON contains private tenant data in a file intended for commit.
