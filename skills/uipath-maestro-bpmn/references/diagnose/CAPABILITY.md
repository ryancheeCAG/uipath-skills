# Diagnose - Investigate failed BPMN runs

Capability index for post-run investigation. Diagnose owns incidents, variables, element executions, deployed asset correlation, traces, and known failure patterns.

> Inherits universal rules from [SKILL.md](../../SKILL.md). Running and lifecycle live in [operate/CAPABILITY.md](../operate/CAPABILITY.md); source fixes live in [author/CAPABILITY.md](../author/CAPABILITY.md).

## When to use this capability

- Triage a failed debug or deployed process run.
- Read incidents and faulting element IDs.
- Inspect runtime variables and element executions.
- Fetch the deployed BPMN asset when local files may differ.
- Map runtime failures back to BPMN source and generated package metadata.
- Identify failures caused by unresolved Integration Service enrichment, bad bindings, missing diagrams, invalid mappings, or stale package files.

## Critical rules

1. **Investigate in priority order** - incidents, variables, deployed BPMN correlation, element executions, then traces.
2. **Fetch deployed BPMN when local source may differ** - do not assume the working tree matches what ran.
3. **Map failures to BPMN element IDs** - use IDs to identify the source node, gateway, event, sequence flow, or extension that needs Author work.
4. **Separate runtime symptoms from source fixes** - Diagnose explains root cause; Author edits source.
5. **Do not expose private runtime data** - redact tenant, user, connection, folder, URL, payload, and secret values in summaries.

## Workflow

| Journey | Read |
| --- | --- |
| Triage a failed run | [references/troubleshooting-guide.md](references/troubleshooting-guide.md) |
| Recognize recurring failure patterns | [references/failure-modes.md](references/failure-modes.md) |

## Common tasks

| I need to... | Read these |
| --- | --- |
| Find the faulting element | [references/troubleshooting-guide.md](references/troubleshooting-guide.md) |
| Compare local and deployed BPMN | [references/troubleshooting-guide.md](references/troubleshooting-guide.md) |
| Diagnose binding or generated JSON issues | [references/failure-modes.md](references/failure-modes.md) + [shared/project-layout.md](../shared/project-layout.md) |
| Diagnose Integration Service runtime issues | [references/failure-modes.md](references/failure-modes.md) + [author/plugins/integration-service](../author/references/plugins/integration-service/) |
| Fix the source | [author/CAPABILITY.md](../author/CAPABILITY.md) |

## Anti-patterns

- **Never start with verbose traces when incidents are available.**
- **Never assume local BPMN is the deployed asset.**
- **Never retry before root cause is known.**
- **Never paste private incident payloads or connection details into docs, commits, or issue comments.**
- **Never patch generated package files as the only fix for a BPMN source defect.**

## References

### Diagnose-scoped

- [troubleshooting-guide.md](references/troubleshooting-guide.md) - diagnostic priority ladder
- [failure-modes.md](references/failure-modes.md) - recurring failure patterns

### Cross-capability

- [shared/bpmn-xml-contract.md](../shared/bpmn-xml-contract.md) - XML authoring and validation boundaries
- [shared/project-layout.md](../shared/project-layout.md) - generated files and package shape
- [shared/variables-bindings-expressions.md](../shared/variables-bindings-expressions.md) - mappings and binding expressions
- [shared/public-safety.md](../shared/public-safety.md) - redaction and sanitization
