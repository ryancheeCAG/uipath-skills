# Failure Modes

## Missing diagram

Studio Web import rejects BPMN without a valid diagram and plane. Add `bpmndi:BPMNDiagram`, `bpmndi:BPMNPlane`, shapes for nodes, and edges for sequence flows.

## Orphaned diagram plane

A diagram plane references a process, collaboration, or subprocess that no longer exists. Point the plane to a valid element or remove the orphaned diagram.

## Missing shape or waypoint

Rendered elements without BPMN DI may parse but fail to render correctly. Add bounds for nodes and waypoints for edges.

## Entry point mismatch

Entry point inputs reference a start event through `elementId`, but the start event lacks the matching `uipath:entryPointId` or the ID is duplicated. Fix root start event extensions and variable scoping.

## Binding reference missing

A node context value refers to `=bindings.<id>` but no matching root binding or generated binding resource exists. Fix the BPMN binding source or rerun CLI enrichment/generation.

## Integration Service draft executed

An Integration Service activity or trigger was left as model-authored draft intent and reached upload/debug/run without CLI enrichment. Enrich connector metadata, connection binding, dynamic schemas, and generated resources before operating.

## Stale generated package files

Generated JSON no longer reflects the BPMN source. Regenerate package metadata and verify package descriptor content before upload or deploy.

## Invalid gateway defaults

Exclusive or inclusive gateways have ambiguous conditions, missing defaults, or a default flow that points to the wrong sequence flow. Fix outgoing conditions and default references.

## Boundary error mismatch

A boundary error event references a missing or duplicate error definition, or is attached to an invalid activity. Reconcile the error definition within the correct scope.

## Expression treated as literal

An expression field is authored as a plain literal string. Use expression form where the frontend/runtime expects evaluation, and avoid assignment operators in fields where validation forbids assignment.
