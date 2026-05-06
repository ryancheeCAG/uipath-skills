# Run

Use this journey to debug or run a BPMN process and inspect execution status.

## Consent gate

Before any debug or run:

- Explain that execution can call external systems.
- Confirm input arguments and target folder/context.
- Confirm the project has passed validation and required enrichment.
- Ask for explicit consent.

## Execution summary

When a run starts, report:

- Studio Web URL, if returned.
- Process, job, or instance ID, if returned.
- Folder/context, if known.
- Input summary, with secrets redacted.
- Next inspection command or status path.

## Status and traces

Start with status and incidents before verbose traces. Traces can be large and should be pulled only when incidents and variables are insufficient.

If execution faults, hand off to [diagnose/CAPABILITY.md](../../diagnose/CAPABILITY.md).
