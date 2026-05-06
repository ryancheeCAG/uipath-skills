# Operate - Package, ship, run, and manage BPMN processes

Capability index for cloud-side lifecycle work. Operate owns packaging, upload, publish/deploy, debug/run, and instance management. These actions may contact UiPath services or external systems.

> Inherits universal rules from [SKILL.md](../../SKILL.md). Authoring and validation live in [author/CAPABILITY.md](../author/CAPABILITY.md); post-run investigation lives in [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md).

## When to use this capability

- Package a Maestro BPMN Process Orchestration project.
- Upload a project to Studio Web.
- Publish or deploy a packaged process when explicitly requested.
- Debug or run a process instance after explicit consent.
- Inspect jobs, processes, process versions, instances, variables, incidents, and traces.
- Pause, resume, cancel, retry, migrate, or move a running instance when explicitly requested.

## Critical rules

1. **Never debug or run without explicit consent** - process execution can call external systems and create real side effects.
2. **Validate before operate** - do not upload, publish, debug, or run until Author validation is complete or the user accepts known draft warnings.
3. **Refresh/generate package resources before cloud actions** - stale generated JSON can break bindings even when BPMN source is correct.
4. **Default publish wording to Studio Web upload unless the user explicitly asks for Orchestrator deployment** - keep deploy semantics explicit.
5. **Report identifiers plainly** - summarize returned Studio Web URLs, package IDs, process IDs, job IDs, instance IDs, and folder context when available.
6. **Do not retry before diagnosis** - identify root cause first, then decide whether retry is appropriate.

## Workflow

| Journey | Read |
| --- | --- |
| Package and upload or publish | [references/ship.md](references/ship.md) |
| Debug/run and inspect execution | [references/run.md](references/run.md) |
| Manage a running instance | [references/manage.md](references/manage.md) |

## Common tasks

| I need to... | Read these |
| --- | --- |
| Prepare for Studio Web upload | [references/ship.md](references/ship.md) + [shared/project-layout.md](../shared/project-layout.md) |
| Deploy to Orchestrator | [references/ship.md](references/ship.md) |
| Run/debug a BPMN process | [references/run.md](references/run.md) |
| Inspect job or instance status | [references/run.md](references/run.md) |
| Pause/resume/cancel/retry | [references/manage.md](references/manage.md) |
| Diagnose a failed run | [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md) |

## Anti-patterns

- **Never treat package generation as source authoring** - generated files reflect BPMN plus enrichment.
- **Never upload a draft with unresolved Integration Service enrichment unless the user explicitly wants a non-executable draft review.**
- **Never run lifecycle commands just to validate XML.**
- **Never retry a faulted instance without checking incidents and deployed asset correlation.**

## References

### Operate-scoped

- [ship.md](references/ship.md) - package, upload, publish, deploy
- [run.md](references/run.md) - debug, run, status, traces
- [manage.md](references/manage.md) - pause, resume, cancel, retry, migrate, cursor movement

### Cross-capability

- [shared/project-layout.md](../shared/project-layout.md) - package files and content
- [shared/cli-conventions.md](../shared/cli-conventions.md) - side effects, login, JSON output
- [author/validation.md](../author/references/validation.md) - pre-operate validation
- [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md) - failure investigation
