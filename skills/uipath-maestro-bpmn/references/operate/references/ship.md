# Ship

Use this journey to package, upload, publish, or deploy a BPMN Process Orchestration project.

## Pre-flight

1. Confirm the user wants a cloud-side action.
2. Confirm local validation has run.
3. Confirm Integration Service enrichment is complete for executable connector elements.
4. Regenerate or refresh package metadata with the supported CLI path.
5. Inspect generated files for public-safety issues before committing or sharing.

## Studio Web upload

Use Studio Web upload when the user says publish without specifying Orchestrator deployment. Report the Studio Web URL when the CLI returns one.

## Orchestrator deployment

Only deploy to Orchestrator when the user explicitly asks for deployment. Confirm package identity, target folder/context, and runtime expectations before publishing.

## Failure handling

If package or upload fails:

- Capture the high-level error category.
- Check generated package files against [shared/project-layout.md](../../shared/project-layout.md).
- Return to Author for BPMN/source fixes.
- Use Diagnose only after a process has actually run or faulted in the runtime.
