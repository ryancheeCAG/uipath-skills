# Greenfield Authoring

Use this journey when creating a new Maestro BPMN Process Orchestration project.

## Steps

1. Confirm the requested process shape, entry points, external systems, and any resources that already exist.
2. Create the canonical project scaffold using the available Maestro BPMN scaffolding command or the repository's current Maestro project template.
3. Create or edit the primary `.bpmn` file as the source of record.
4. Add one root executable process by default.
5. Add start/end events, tasks, gateways, subprocesses, sequence flows, and diagram geometry.
6. Add root variables, entry point IDs, and mappings when needed.
7. Add documented non-Integration-Service UiPath service shells only when the user intent is clear.
8. For Integration Service activities/triggers, follow [plugins/integration-service/planning.md](plugins/integration-service/planning.md) and leave CLI-owned details to enrichment.
9. Run local validation from [validation.md](validation.md).
10. Hand off to Operate only after validation is clean or the remaining issues are explicit user-approved warnings.

## Design defaults

- Prefer a simple root process before adding pools or collaborations.
- Prefer readable deterministic element IDs.
- Keep diagram layout simple and inspectable.
- Use placeholder-safe resource names until discovery/enrichment resolves real resources.
- Keep all examples and fixtures synthetic.

## Done state

Authoring is done when BPMN source is coherent, generated or CLI-managed files are up to date or intentionally absent, validation has been run, and any Integration Service enrichment blockers are documented.
