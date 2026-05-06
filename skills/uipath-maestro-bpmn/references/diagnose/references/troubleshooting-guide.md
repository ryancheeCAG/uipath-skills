# Troubleshooting Guide

Use this priority ladder for failed or misbehaving BPMN runs.

## Step 1 - Confirm context

Collect public-safe identifiers:

- Process or package name.
- Instance/job ID.
- Folder/context label.
- Approximate run time.
- Local commit or package version, if known.

Do not record secrets, tenant URLs, connection IDs, or payload data in public notes.

## Step 2 - Read incidents

Find the incident category, message, and faulting BPMN element ID. If multiple incidents exist, start with the first root fault and avoid chasing downstream cancellation noise.

## Step 3 - Inspect runtime variables

Inspect variables around the faulting element. Redact private payloads. Check whether expected outputs were missing, malformed, or literal strings instead of evaluated expressions.

## Step 4 - Correlate deployed BPMN

Fetch the deployed BPMN asset when local source may differ. Compare:

- Faulting element ID.
- Root variables and mappings.
- Binding expressions.
- Integration Service extension content.
- Diagram and sequence-flow structure when the failure is import or package related.

## Step 5 - Check generated package files

If the failure is binding, entry point, package, or runtime metadata related, inspect generated JSON:

- `bindings_v2.json`
- `entry-points.json`
- `operate.json`
- `package-descriptor.json`

Generated-file mismatch usually means Author should fix BPMN or rerun CLI generation/enrichment.

## Step 6 - Pull traces last

Use verbose traces only when incidents, variables, deployed asset, and package files do not explain the issue.

## Output

Return a concise diagnosis:

- Faulting element ID.
- User-visible symptom.
- Likely root cause.
- Whether the fix belongs in BPMN source, CLI enrichment, generated package files, or cloud configuration.
- Safe next action.
