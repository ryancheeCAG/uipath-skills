# Greenfield Authoring

Use this journey when creating a new Maestro BPMN Process Orchestration project.

## Steps

1. Confirm the requested process goal, trigger, major steps, external systems, and resources that already exist.
2. Create or reuse a local solution directory with a `.uipx` manifest.
3. Create the BPMN project as a child directory of that solution and register it in the solution manifest.
4. Create or edit the primary `.bpmn` file as the source of record.
5. **Pass 1: build the standard BPMN skeleton** from [planning-arch.md](planning-arch.md): root process, starts, tasks, gateways, subprocesses, events, error paths, sequence flows, and BPMN DI.
6. Summarize the process shape and ask the operator to confirm it before filling executable UiPath metadata when the process is non-trivial.
7. **Pass 2: fill model-owned UiPath XML** from [planning-impl.md](planning-impl.md): root variables, entry point IDs, mappings, bindings, scripts, retry/error metadata, and documented non-Integration-Service service shells.
8. For Integration Service activities/triggers, follow [plugins/integration-service/planning.md](plugins/integration-service/planning.md) and leave CLI-owned details to enrichment.
9. Run local validation from [validation.md](validation.md).
10. Hand off to Operate only after validation is clean or the remaining issues are explicit user-approved warnings.

Typical local setup:

```bash
uip solution init --help --output json
uip solution init MySolution --output json
cd MySolution
uip maestro bpmn init MyProcess --output json
uip solution project list --output json
```

Use `uip solution init` when the probe succeeds. If the installed CLI returns
`unknown command 'init'`, substitute `uip solution new MySolution --output json`
with the same arguments. Current `uip maestro bpmn init` registers the project
when it runs inside a solution. If an older CLI does not register it, use
`uip solution project add MyProcess MySolution.uipx --output json`. If a project
was created outside a solution, import it before continuing with upload,
publish, debug, or run.

## Design defaults

- Prefer a simple root process before adding pools or collaborations.
- Prefer readable deterministic element IDs.
- Keep diagram layout simple and inspectable.
- Use placeholder-safe resource names until discovery/enrichment resolves real resources.
- Keep pass 1 skeleton diffs separate from pass 2 execution metadata when practical.
- Keep all examples and fixtures synthetic.

## Shape confirmation prompt

For non-trivial processes, summarize:

- Trigger and entry point.
- Ordered happy path.
- Branches, joins, and default paths.
- Error, timeout, and terminate behavior.
- Subprocess boundaries.
- External-system placeholders and enrichment blockers.

Proceed to pass 2 only after the operator confirms the shape or the edit is small enough to summarize without a formal stop.

## Done state

Authoring is done when BPMN source is coherent, generated or CLI-managed files are up to date or intentionally absent, validation has been run, and any Integration Service enrichment blockers are documented.
