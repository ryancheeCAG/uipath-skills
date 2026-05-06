# Manage

Use this journey to intervene in a running or faulted BPMN process instance.

## Supported decisions

- Pause.
- Resume.
- Cancel.
- Retry after diagnosis.
- Migrate version.
- Move cursor/goto when the runtime supports it and the user explicitly requests it.

## Rules

- Confirm the target instance and folder/context before acting.
- Diagnose fault root cause before retry.
- Explain expected side effects of the lifecycle action.
- Report the resulting instance status.

## Handoff

If the action reveals a modeling or binding problem, return to Author with the BPMN element ID, incident summary, and generated file mismatch if relevant.
