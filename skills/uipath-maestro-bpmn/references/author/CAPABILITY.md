# Author - Create and edit BPMN Process Orchestration projects

Capability index for local BPMN project authoring. Author owns source edits, local inspection, validation, and CLI enrichment planning. It does not upload, publish, debug, or run cloud instances.

> Inherits universal rules from [SKILL.md](../../SKILL.md). Read [shared/bpmn-xml-contract.md](../shared/bpmn-xml-contract.md) before changing XML boundaries.

## When to use this capability

- Create a Maestro BPMN project scaffold.
- Edit `.bpmn` XML for process structure, diagrams, variables, bindings, entry points, scripts, timers, messages, gateways, subprocesses, boundary errors, and documented non-Integration-Service UiPath extensions.
- Inspect an existing BPMN project and identify source versus generated files.
- Plan Integration Service nodes/triggers that must be CLI-enriched.
- Run local validation before handing off to Operate.

## Critical rules

1. **Read the BPMN XML contract before editing** - the frontend contract defines which XML the model may author and which pieces require CLI generation or enrichment.
2. **Default to reviewable file edits for BPMN source** - edit `.bpmn` directly for model-owned XML so diffs stay inspectable.
3. **Do not hand-author Integration Service details** - use [plugins/integration-service/](references/plugins/integration-service/) for the planning and implementation boundary.
4. **Keep generated package files derived** - if `bindings_v2.json`, `entry-points.json`, `operate.json`, or `package-descriptor.json` is stale, prefer regeneration or validation over manual patching.
5. **Every Studio Web-visible element needs diagram geometry** - ensure diagrams, planes, shapes, bounds, edges, and waypoints exist for rendered nodes and flows.
6. **Validate once the full local edit is coherent** - intermediate BPMN edits may be invalid while IDs, flows, and diagrams are being reconciled.
7. **Preserve unknown imported extensions** - do not delete extension elements the skill cannot interpret unless the user explicitly asks for normalization.
8. **Use synthetic examples only** - never copy private exported BPMN into local fixtures, docs, or comments.

## Workflow

| Journey | Read |
| --- | --- |
| Create a new BPMN project | [references/greenfield.md](references/greenfield.md) |
| Edit an existing BPMN project | [references/brownfield.md](references/brownfield.md) |
| Choose what the model may write | [shared/bpmn-xml-contract.md](../shared/bpmn-xml-contract.md) |
| Work with Integration Service nodes/triggers | [references/plugins/integration-service/](references/plugins/integration-service/) |

## Common tasks

| I need to... | Read these |
| --- | --- |
| Understand project files | [shared/project-layout.md](../shared/project-layout.md) |
| Add or revise BPMN structure | [references/brownfield.md](references/brownfield.md) + [shared/bpmn-xml-contract.md](../shared/bpmn-xml-contract.md) |
| Add variables, mappings, or bindings | [shared/variables-bindings-expressions.md](../shared/variables-bindings-expressions.md) |
| Add an Integration Service activity or trigger | [references/plugins/integration-service/](references/plugins/integration-service/) |
| Prepare for upload or run | [references/validation.md](references/validation.md) then [operate/CAPABILITY.md](../operate/CAPABILITY.md) |
| Keep authored content public-safe | [shared/public-safety.md](../shared/public-safety.md) |

## Anti-patterns

- **Never omit BPMN DI for a process intended for Studio Web.**
- **Never patch generated JSON to hide a BPMN source problem.**
- **Never paste a real connection ID, folder key, tenant URL, or exported XML snippet into the project.**
- **Never downgrade an Integration Service node to a generic task just because enrichment is unavailable** - keep the node as a draft intent and report the blocker.
- **Never assume imported extension XML is disposable** - preserve first, normalize only on explicit request.

## References

### Author-scoped

- [greenfield.md](references/greenfield.md) - create-new-project journey
- [brownfield.md](references/brownfield.md) - edit-existing-project journey
- [validation.md](references/validation.md) - local validation checklist
- [plugins/integration-service/](references/plugins/integration-service/) - Integration Service planning and CLI enrichment boundary

### Cross-capability

- [shared/bpmn-xml-contract.md](../shared/bpmn-xml-contract.md) - model-owned versus CLI-owned XML
- [shared/project-layout.md](../shared/project-layout.md) - source and generated files
- [shared/variables-bindings-expressions.md](../shared/variables-bindings-expressions.md) - variables, bindings, mappings, expressions
- [shared/cli-conventions.md](../shared/cli-conventions.md) - CLI and side-effect conventions
- [shared/public-safety.md](../shared/public-safety.md) - sanitization rules
