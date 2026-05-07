# Maestro BPMN Frontend XML Contract

Status: planning contract for `uipath-maestro-bpmn`. This document is sanitized for the public skills repository. It summarizes source-backed frontend and packaging behavior without including raw private XML, tenant data, URLs, connection IDs, folder data, private names, or local paths.

## Scope

This is the authoring contract for model-generated UiPath Maestro BPMN XML. It defines the XML shapes a coding agent may generate directly, the UiPath extension elements the model may write, and the pieces that must be generated or enriched by CLI tooling before upload, debug, publish, or deploy.

The contract is planning/research only. It does not implement the skill or introduce a public CLI surface.

## Source Inventory

Frontend serialization source of truth:

- UiPath moddle descriptor registration and extension element construction.
- BPMN XML import, diagram validation, object extraction, extension mapping, warning behavior, and import migrations.
- BPMN XML export, diagram filtering, geometry merge, definitions construction, exporter metadata, and CDATA fixup.
- Design-time contracts for Integration Service, Orchestrator, HITL, message events, timer triggers, case scheduler, API workflow, business rules, and agents.
- BPMN node, edge, lane, group, object, parent, shape, documentation, and flow builders.
- Conversion helpers for root, tasks, events, gateways, boundaries, subprocesses, scripts, and edges.
- Canvas validation rules that should be mirrored by a CLI validator.
- Packaging helpers for bindings, entry points, operate metadata, package descriptors, case conversion, and asset copy support.

Private examples may be used only to confirm structural coverage. Public docs and fixtures must use synthetic XML and public-safe summaries.

## Baseline BPMN Document

Generated XML must be valid BPMN 2.0 with the UiPath extension namespace:

- `bpmn:definitions` must include standard BPMN, BPMNDI, DI, DC, and UiPath namespaces. The UiPath namespace URI is `http://uipath.org/schema/bpmn` with prefix `uipath`.
- A root `bpmn:process` is the normal source unit. A root `bpmn:collaboration` with participants is importable, but process-orchestration agent authoring should default to one executable process unless the user explicitly asks for pools.
- At least one `bpmndi:BPMNDiagram` with `bpmndi:BPMNPlane` is required for frontend import. Imports without diagrams throw. Diagrams whose plane references missing elements are filtered.
- Every visible flow node and edge should have BPMN DI: `bpmndi:BPMNShape` with bounds for nodes and `bpmndi:BPMNEdge` with waypoints for edges.
- Exporter metadata is written by frontend export as either `UiPath Studio Web (https://uipath.com)` or standalone `UiPath (https://bpmn.uipath.com)`, plus an exporter version. Model-authored XML can omit this and let the frontend/CLI normalize it.
- Conditions and scripts are expression-normalized on import. Conditional sequence-flow expressions and scripts should use a leading `=` in authoring docs and validation.
- CDATA is the expected representation for JSON bodies, JSON schemas, script bodies, variable schemas, custom output bodies, and case-management payload bodies.

## Supported BPMN Authoring Surface

Model-authored XML may generate these BPMN families directly:

- Events: `startEvent`, `endEvent`, `boundaryEvent`, `intermediateCatchEvent`, `intermediateThrowEvent`.
- Event definitions: timer, message, signal, error, escalation, conditional, link, and terminate where supported by the frontend/runtime path.
- Gateways: exclusive, inclusive, parallel, event-based, and complex gateways.
- Tasks and activities: task, service task, send task, receive task, user task, manual task, business rule task, script task, and call activity.
- Containers: subprocess and event subprocess. Expanded subprocesses require a second BPMN diagram for the subprocess canvas when the frontend needs to render nested content.
- Flow and annotation elements: sequence flow, message flow, association, data input/output association, group, text annotation, categories, messages, signals, errors, escalations, data stores, global tasks, item definitions, and resources.
- Loop markers: standard and multi-instance loop characteristics. UiPath collection/element metadata belongs under the loop characteristic extension elements.

Conservative authoring defaults:

- Use one root process and one blank start event unless a trigger entry point is needed.
- Use sequence flows for intra-process routing. Do not use message flows inside one pool.
- For exclusive/inclusive gateway splits, put conditions on outgoing sequence flows and set a default flow when applicable.
- Boundary error events must attach to an activity and reference a valid error definition.
- Event subprocesses should have one start event. Regular subprocess starts should not have event definitions.
- Avoid cross-boundary sequence flows between subprocess scopes or pools.

## UiPath Moddle Namespace

The UiPath moddle descriptor uses XML tag aliases in lower case. Public docs should prefer lower-case XML examples such as `uipath:variables`, `uipath:activity`, and `uipath:entryPointId`, while referring to descriptor type names in prose only when needed.

Descriptor-defined top-level extension elements:

- `uipath:variables version="v1"` with `uipath:input`, `uipath:inputOutput`, and `uipath:output` variable children.
- `uipath:casevariables version="v1"` with `uipath:inputOutput` case variable children.
- `uipath:bindings version="v1"` with `uipath:binding` children.
- `uipath:entryPointId value="..."`.
- `uipath:event version="v1"` for event-like service types.
- `uipath:activity version="v1"` for activity-like service types.
- `uipath:mapping version="v1"` for `BPMN.Variables` input/output mappings.
- `uipath:scriptVersion value="..."`.
- `uipath:migrationVersion version="..."`.
- `uipath:intsvcActivityConfig version="..."`.
- `uipath:loopCharacteristics inputCollection="..." inputElement="..."`.
- `uipath:caseManagement version="v1"` with CDATA body.
- `uipath:retry ...`.
- `uipath:errorMapping version="v1"` with `uipath:error` children.
- `uipath:tags` with `uipath:tag key="...">value</uipath:tag`.
- `uipath:isTransactionRoot version="v1" value="true|false"`.

Shared child elements:

- `uipath:type value="<service type>" version="v1|beta|..."`.
- `uipath:context` containing context `uipath:input` entries and optional `uipath:inputSchema`.
- `uipath:input name type subType value target` with optional CDATA body.
- `uipath:output name type subType source var target custom internal` with optional CDATA body.
- `uipath:inputSchema` with a JSON schema CDATA body.

## Process-Level Extensions

Root process extension elements define project-wide variables, resource bindings, migration version, and transaction behavior.

Use `uipath:variables` on the root process for public entry point input/output contracts and global process variables:

- Variables have `id`, `name`, `type`, optional `subType`, `elementId`, optional `canonicalId`, optional `default`, optional `custom`, optional `internal`, and optional CDATA body.
- `elementId` scopes an input variable to a start event when used for entry point inputs.
- Root output variables become entry point output schema properties.
- `jsonSchema` variables carry the schema in the element body, with `$schema` stripped during package entry-point generation.
- `file` variables become job attachment references in entry-point schema.
- `float` and `double` variables map to JSON schema type `number` with format.

Use `uipath:bindings` on the root process for resources that must become `bindings_v2.json` resources:

- Binding attributes include `id`, `name`, `type`, `elementId`, `default`, `resource`, `resourceSubType`, `resourceKey`, and `propertyAttribute`.
- Node context inputs refer to bindings as expressions with the `=bindings.<binding id>` convention.
- `folderKey` and `folderPath` binding property attributes are skipped by the packaging generator as standalone binding resources.
- Resource families observed in packaging code include process, process agent subtype, business rule, queue, app, connection, event trigger, property, and time trigger.

Use `uipath:entryPointId` on root-level start events that should become runnable entry points. Packaging emits entry point file paths in the form `/content/<bpmn-file>#<start-event-id>` with the unique ID from this extension.

Use `uipath:migrationVersion` as import migration metadata. The current frontend runs registered migrations after import; CLI validation should preserve unknown versions and report unsupported downgrade/upgrade assumptions instead of deleting them.

Use `uipath:isTransactionRoot` on the root process when the entry point should be marked as a transaction root.

## Activity and Event Extensions

UiPath activity/event extensions attach under the BPMN element's `bpmn:extensionElements`.

Service type selection:

- Event-like service types produce `uipath:event`: `Intsvc.WaitForEvent`, `Intsvc.EventTrigger`, `Maestro.ReceiveMessageEvent`, and `Maestro.SendMessageEvent`.
- Execution-like service types produce `uipath:activity`: `Intsvc.ActivityExecution`, `Intsvc.AsyncExecution`, agent execution types, workflow execution types, unified HTTP request, Orchestrator starts, queue creation, HITL, business rules, API workflows, and case scheduler.
- `BPMN.Variables` produces `uipath:mapping` for variable input/output mapping.

Activity/event structure:

- `uipath:type` carries the service type and version.
- `uipath:context` carries design-time selection fields such as process name, folder path, connection binding, connector key, activity, operation, object name, or message name.
- `uipath:input` carries runtime input values. For JSON bodies, put JSON in CDATA and set the schema-defined `name` and `target`.
- `uipath:output` maps service outputs to variables. `var` is the legacy/current target variable attribute; `target` may also appear.
- `uipath:inputSchema` preserves field-level type information when frontend export merges split fields into a single JSON input.
- `skipCondition` is an attribute on `uipath:activity`.

Special cases:

- Script tasks use BPMN `script` CDATA plus `scriptFormat="JavaScript"`. Their UiPath inputs are merged into a single JSON `uipath:input name="args" target="bodyField"` and an `inputSchema` is written in context.
- Start events can combine `uipath:entryPointId` with event/activity extensions.
- End events, script tasks, subprocesses, boundary events, intermediate events, and supported Integration Service types may carry UiPath extensions.
- Subprocesses can have their own `uipath:variables` in the subprocess extension elements for scoped variables.
- Multi-instance loop characteristics can carry `uipath:loopCharacteristics` under the loop characteristic's own extension elements.
- `uipath:retry` and `uipath:errorMapping` may appear even when no other service content exists.
- `uipath:caseManagement` is a CDATA payload extension used by case-management-generated or related nodes. Model authors should not invent this payload without a dedicated case-management contract.
- `uipath:tags` are key/body pairs and were observed in private exports. They should be preserved on round trip.

## Design Schema Service Types

The design-schema JSON files define service type names, version strings, context fields, input body shape, and output mapping defaults.

Authorable non-Integration-Service service types:

- `BPMN.Variables`: variable mapping on tasks, start/end events, script tasks, and subprocesses.
- `BPMN.ScriptTask`: script task metadata; script source still lives in BPMN `script`.
- `Actions.HITL`: action app task with app id/version/actions/folder/task title context and `HitlTaskArguments` JSON input.
- `Orchestrator.StartJob` and `Orchestrator.StartAgentJob`: process or agent process execution with resource bindings for release key/name/folder and `JobArguments` JSON input.
- `Orchestrator.ExecuteApiWorkflowAsync`: API workflow execution with resource binding for release key/name/folder and `JobArguments`.
- `Orchestrator.BusinessRules`: business rule execution with process-like resource binding and `JobArguments`.
- `Orchestrator.CreateQueueItem`: queue item creation with queue/folder bindings and `ItemData`.
- `Maestro.ReceiveMessageEvent`: message receive with message name context and `ItemData`.
- `Maestro.SendMessageEvent`: message send with message name context and `ItemData`.
- `Maestro.CasePlanScheduler`: case scheduler context and `caseManagerInput`.
- `A2A.AgentExecution`: agent execution with dynamic schema.

Integration Service service types:

- `Intsvc.ActivityExecution`.
- `Intsvc.AsyncExecution`.
- `Intsvc.HttpExecution`.
- `Intsvc.UnifiedHttpRequest`.
- `Intsvc.WaitForEvent`.
- `Intsvc.EventTrigger`.
- `Intsvc.TimerTrigger`.
- `Intsvc.SyncAgentExecution` and `Intsvc.AsyncAgentExecution`.
- `Intsvc.SyncWorkflowExecution` and `Intsvc.AsyncWorkflowExecution`.

## Model-Owned XML

The model may generate these pieces directly when it has enough user intent:

- Standard BPMN control flow, task/event/gateway structure, subprocess nesting, loop markers, edge conditions, default flows, error boundaries, timer/message/error definitions, and diagram coordinates.
- Root process variables and straightforward variable mapping with generated stable IDs.
- Entry point IDs as generated stable IDs when a root start event is intended to be runnable.
- Non-secret Orchestrator/HITL/message service type shells using placeholder-safe context fields and variable references.
- Script task BPMN `script` CDATA, `scriptVersion`, merged args input, and output mapping.
- Retry and error mapping shape when the user specifies retry/error behavior.
- Tags when the user gives non-private labels to preserve as metadata.

Generated IDs should be deterministic within the file, readable enough for review, and stable across small edits where possible. Generated docs and examples must use synthetic names and placeholder resource values only.

## CLI-Owned or CLI-Enriched Pieces

The CLI must generate, enrich, or validate these before any real upload/debug/publish path:

- Integration Service activity selection and operation metadata from registry-backed schemas.
- Integration Service trigger metadata: connector key, operation, object name, connection binding, folder fields, filter expression, parameters, and trigger property bindings.
- Integration Service connection binding resources, including resource key, property attribute, display label, connector metadata, and `UseConnectionService`.
- Dynamic input and output schemas for connector activities, event triggers, HTTP/unified HTTP, external agents, external workflows, API workflows, and generated outputs.
- `bindings_v2.json`, including deduped resource entries and metadata such as `BindingsVersion`, `ActivityName`, `DisplayLabel`, `SolutionsSupport`, `SubType`, `Connector`, and parent resource keys for trigger properties.
- `entry-points.json`, including entry point input/output JSON schema extraction from root variables and file path/unique ID wiring.
- `operate.json`, including project ID, main file, content type, portable target framework, and runtime options.
- `package-descriptor.json`, including package file manifest entries for BPMN, generated JSON files, and related Flow/agent assets when applicable.
- NuGet-compliant package identifiers and final package output paths.
- BPMN parse validation using UiPath moddle and package-tool XML parsing.
- Canvas validation parity for connection rules, gateway rules, start-event rules, subprocess crossing rules, boundary error rules, required fields, no-assignment expressions, missing root variables, and solution resource references.
- Project scaffolding, including `project.uiproj`, canonical BPMN filename, and generated support files.

For the first implementation, the recommended split is model-authored BPMN plus CLI validation/enrichment. Full CLI emission of complete BPMN should wait until the contract, registry schema generation, and layout expectations are stable.

## Packaging Contract

A Process Orchestration package content folder contains:

- One or more `.bpmn` files.
- `bindings_v2.json`.
- `entry-points.json`.
- `operate.json`.
- `package-descriptor.json`.

Packaging behavior:

- Browser-side packaging copies BPMN and relevant JSON files, parses BPMN with frontend serialization, creates bindings and entry points, then writes operate and package descriptor files.
- The .NET Process Orchestration tool copies top-level `.bpmn` and `.json` files, generates `bindings_v2.json` and `entry-points.json` when absent, then creates `operate.json` and `package-descriptor.json`.
- The entry point type is `processorchestration` in the browser-side helper for Process Orchestration/Flow compatibility, while the .NET tool uses the lower-case Process Orchestration project type constant.
- `operate.json` uses portable target framework and unattended runtime options.
- `package-descriptor.json` maps `operate.json`, `entry-points.json`, `bindings_v2.json`, and BPMN files under `content/`.
- Flow and case-management compatibility paths exist in the frontend utility, but the BPMN skill should treat them as dependent-resource/package concerns unless the user asks for mixed projects.

## Validation Contract

CLI validation should combine XML parse checks, UiPath extension checks, packaging checks, and canvas semantics:

- BPMN XML parses with the UiPath moddle descriptor.
- At least one valid diagram and plane exists.
- Diagram plane references valid root process/collaboration/subprocess elements.
- Every rendered node has a shape and every rendered edge has waypoints.
- Root process extension elements are structurally valid: variables, bindings, migration version, transaction marker.
- Root start event entry point IDs are unique and point to root-level start events.
- Entry point input variables have `elementId` matching the start event.
- Binding references in context values resolve to root bindings.
- Required service-type context/input fields are present according to design schema.
- Sequence flows connect legal source/target types and do not cross subprocess or pool boundaries illegally.
- Message flows do not connect elements within the same pool.
- Gateway splits have valid conditional/default flow setup and avoid superfluous/fake joins.
- Each scope has at most one blank start event.
- Event subprocesses have exactly one start event; regular subprocess start events do not carry event definitions.
- Error boundary events and error event subprocesses reference valid, non-duplicated error definitions in their scope.
- Expressions used in conditions, scripts, variables, and skip conditions avoid assignment operators where the frontend forbids them.
- Output variable references have matching root or scoped variables.
- Solution resource references resolve when validating inside a solution context.

## Migration Contract

Frontend import currently runs versioned migrations after XML import. Model-generated files should prefer the current extension shapes in this document instead of relying on migrations. CLI validation should:

- Preserve existing `uipath:migrationVersion` values.
- Report old or unknown migration versions as warnings unless the file cannot be interpreted.
- Avoid rewriting private or user-authored extension payloads without an explicit normalize command.
- Keep variable-scope migration behavior conservative; the frontend has disabled automatic cross-scope variable relocation for compatibility.

## Synthetic Coverage Targets

The fixture corpus should cover these public-safe structural points:

- Large and medium processes use hundreds of sequence flows, many tasks/service tasks, exclusive gateways, boundary error events, intermediate events, timers, messages, terminate ends, groups, annotations, and BPMN DI.
- UiPath extensions appear both at root process level and node level.
- Representative projects include `uipath:variables`, `uipath:bindings`, `uipath:entryPointId`, `uipath:activity`, `uipath:event`, `uipath:mapping`, `uipath:context`, `uipath:input`, `uipath:output`, `uipath:inputSchema`, `uipath:scriptVersion`, `uipath:retry`, `uipath:caseManagement`, `uipath:tags`, `uipath:loopCharacteristics`, and `uipath:migrationVersion`.
- Observed service type families include `BPMN.Variables`, `Intsvc.ActivityExecution`, `Intsvc.EventTrigger`, `Intsvc.WaitForEvent`, `Actions.HITL`, `Orchestrator.StartJob`, and `Orchestrator.StartAgentJob`.
- The first public fixture set should be small and synthetic: minimal linear process, gateway plus boundary error, Integration Service activity/trigger shell, and subprocess plus multi-instance.

## Open Decisions

- Whether public commands should live under `uip maestro bpmn ...` or reuse existing `uip maestro ...` lifecycle commands plus BPMN-specific subcommands.
- Whether the first CLI validator should use the frontend TypeScript serializer, the .NET packaging parser, runtime parser code, or a shared parser boundary.
- Which Integration Service fields can be safely model-authored as placeholders and which must always come from registry enrichment.
- Whether `Intsvc.EventTrigger` should be represented only on root start events for agent authoring, or also as intermediate wait events when existing exports contain that shape.
- How much diagram layout should be deterministic in the model versus normalized by CLI auto-layout.
- Where finalized sanitized fixtures should live and how they should be kept free of private source material.
