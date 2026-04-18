# UiPath.DataService.Activities — Eval Scenarios

**Package**: `UiPath.DataService.Activities` 25.9  
**Org**: datafabric | **Tenant**: CodingAgentsEvals

## Overview

This document defines the complete evaluation scenario suite for the `UiPath.DataService.Activities` 25.9 activity pack in RPA workflows. The scenarios test an AI coding agent's ability to generate correct XAML workflows using all 11 Data Service activities — from basic CRUD operations through compound filtered queries to multi-activity composition workflows.

The suite covers **71 scenarios** across 5 categories:

- **Negative Skill Activation** (2 scenarios) — CI gate. Verifies the agent does NOT activate DataService for prompts that belong elsewhere.
- **Positive Skill Activation** (3 scenarios) — CI gate. Verifies the agent correctly routes Data Service / Data Fabric prompts to the right skill.
- **Smoke** (3 scenarios) — CI gate. Verifies correct activity selection across all 11 activities with no property-level checks.
- **Integration** (57 scenarios) — Daily. Exhaustive per-activity configuration validation covering every property, field type, filter operator, anti-pattern, and error-path.
- **Quality** (6 scenarios) — Daily. Realistic multi-activity workflows that test data flow, type consistency, and sequencing across activity categories.

Every scenario specifies an agent prompt, expected XAML structure, and pass/fail criteria. Scenarios are designed for the `coder_eval` framework and will be implemented as YAML task files. Two fixed entities in the `CodingAgentsEvals` tenant (`CodingAgentsEvalEntity` and `CodingAgentsEvalFileEntity`) serve as the shared test fixtures across all scenarios — no dynamic entity creation or record writes occur as part of the eval.

## Activities in Scope

| # | Activity | Category |
|---|----------|----------|
| 1 | `CreateEntityRecord` | Entity Record |
| 2 | `GetEntityRecordById` | Entity Record |
| 3 | `UpdateEntityRecord` | Entity Record |
| 4 | `DeleteEntityRecord` | Entity Record |
| 5 | `QueryEntityRecords` | Entity Record |
| 6 | `CreateMultipleEntityRecords` | Batch |
| 7 | `UpdateMultipleEntityRecords` | Batch |
| 8 | `DeleteMultipleEntityRecords` | Batch |
| 9 | `UploadFileToRecordField` | File |
| 10 | `DownloadFileFromRecordField` | File |
| 11 | `DeleteFileFromRecordField` | File |

---

## Validation Model (Current Scope)

Each scenario evaluates two conditions after the agent generates a workflow:

| Condition | What it checks | How |
|-----------|---------------|-----|
| **Build-time** | XAML compiles without errors — namespaces, type arguments, required arguments, RecordState structure | `uip rpa get-errors --file-path <xaml> --project-dir <dir> --output json` returns no errors |
| **Output semantics** | Generated XAML matches the expected structural patterns for the given prompt — correct activity, EntityId, field bindings, namespace declarations, output wiring | Parse XAML and assert specific attributes and element structure |

Assertion depth varies by tier:
- **Smoke**: correct activity elements present in XAML + build passes — no property-level checks
- **Integration**: comprehensive property validation on every attribute of the single activity under test
- **Quality**: correct data flow between activities, type consistency across the workflow, correct sequencing — no per-activity property details

Each task prompt passes entity and field names as context to the agent. Entities and fields are fixed, pre-existing resources in CodingAgentsEvals — no dynamic entity creation or record writes occur as part of the eval. The agent resolves GUIDs from `EntitiesStore.json`.

Two entities are used across all scenarios:

| Entity | Fields | Used In |
|--------|--------|---------|
| `CodingAgentsEvalEntity` | `Title` (NVARCHAR, required), `Notes` (NVARCHAR), `Status` (NVARCHAR), `Score` (INT), `Price` (DECIMAL), `IsActive` (BIT), `EventDate` (DATE), `ScheduledAt` (DATETIMEOFFSET), `Category` (ChoiceSetSingle), `Tags` (ChoiceSetMultiple) | All CRUD, batch, filter, sort, and ChoiceSet scenarios |
| `CodingAgentsEvalFileEntity` | `Title` (NVARCHAR, required), `Attachment` (File), `Report` (File), `Contract` (File), `attachmentFile` (File), `Owner` (Relationship → CodingAgentsEvalEntity) | File activity and Relationship filter scenarios |

---

## Scenario Summary

| Category | Count | Cadence |
|----------|-------|---------|
| Negative Skill Activation | 2 | Every PR (CI) |
| Positive Skill Activation | 3 | Every PR (CI) |
| Smoke | 3 | Every PR (CI) |
| Integration | 57 (I1–I57) | Daily / on request |
| Quality | 6 | Daily / on request |
| **Total** | **71** | |

When implemented as coder_eval YAML task files, categories map to tags:

| Category | coder_eval tag |
|----------|---------------|
| Negative Skill Activation | `smoke` |
| Positive Skill Activation | `smoke` |
| Smoke | `smoke` |
| Integration | `integration` |
| Quality | `integration` |

---

## 1. Negative Skill Activation

**Purpose**: Verify the agent does NOT activate the `UiPath.DataService.Activities` skill for tasks that belong elsewhere. The SKILL.md description must be precise enough that superficially similar prompts — queuing, file I/O, in-memory data, REST calls, storage — do not cause the agent to generate DataService XAML.

**Evaluation**: The generated workflow must contain zero DataService activities, no `xmlns:uda` namespace, and no `entitiesStores` dependency.

| ID | Scenario | Agent Prompt | Eval Summary | Must NOT appear in output |
|----|----------|-------------|--------------|--------------------------|
| N1 | **CSV file — not entity query** | "Read the file `'C:\data\employees.csv'` and load its rows into a DataTable variable named `employeeTable`." | "Data" + "Table" + "rows" overlap with entity record terminology; the agent must stay within file and DataTable activities with no DataService dependency. | Any `uda:` activity; `entitiesStores` in `project.json`; DataService namespace declarations |
| N2 | **Orchestrator Storage Bucket — not file field** | "Upload the report file at `'C:\reports\monthly.pdf'` to the Orchestrator Storage Bucket named `ReportsBucket` under the path `2026/april/monthly.pdf`." | "Upload file" action overlaps with `UploadFileToRecordField`; the agent must use Storage Bucket activities with no DataService dependency. | `uda:UploadFileToRecordField`; any `xmlns:uda`; `UiPath.DataService.Activities` in dependencies |

---

## 2. Positive Skill Activation

**Purpose**: Verify the agent correctly activates the DataService activity references across different phrasings of Data Service tasks — explicit package mentions, Data Fabric terminology, and implicit entity operations.

**Evaluation**: Pass condition — `uipath-rpa` skill is loaded in the agent session AND the agent reads from the `references/UiPath.DataService.Activities` reference files within that skill. No inspection of the generated workflow or project files.

| ID | Scenario | Agent Prompt | Eval Summary | Expected Activation Signal |
|----|----------|-------------|--------------|---------------------------|
| P1 | **"Data Service" terminology** | "Create an RPA automation that creates a record in the Data Service entity `CodingAgentsEvalEntity` with field `Title` set to `'Hello'`." | Explicit "Data Service" phrasing must route the agent to the RPA skill and load the DataService activity reference files — not resolve to a generic or integration skill. | `uipath-rpa` skill loaded; `references/UiPath.DataService.Activities` reference files read |
| P2 | **"Data Fabric" terminology** | "Create an RPA automation that stores a new order in the Data Fabric entity `CodingAgentsEvalEntity` with field `Title` set to `'ORD-001'`." | "Data Fabric" phrasing — without naming the package — must still resolve to the RPA skill and load the DataService reference files. | `uipath-rpa` skill loaded; `references/UiPath.DataService.Activities` reference files read |
| P3 | **Implicit — entity name only** | "Create an RPA automation that stores a record in entity `CodingAgentsEvalEntity` with `Title` set to `'Hello'`." | No "Data Service" or "Data Fabric" keyword — only the entity name. The agent must infer from the entity name and the store-a-record intent that this is a DataService task. | `uipath-rpa` skill loaded; `references/UiPath.DataService.Activities` reference files read |

---

## 3. Smoke

**Purpose**: Verify the agent selects the correct activities for a given set of intents. Each test packs multiple independent tasks into a single prompt — no data flow between activities, no complex wiring. The only question: did the agent add the right activity for each task?

Three tests cover all 11 activities.

**Evaluation**: Every expected `uda:` activity element is present in the XAML with the correct `x:TypeArguments`, and `uip rpa get-errors` returns no errors. No property-level assertions.

---

### S1 — Entity Record Activities

**Prompt**:
> Build a workflow that performs these independent tasks on Data Service entity `CodingAgentsEvalEntity`:
> 1. Create a new record with `Title` set to `'New Record'`
> 2. Fetch an existing record by its ID
> 3. Update an existing record, setting `Title` to `'Modified'`
> 4. Delete an existing record
> 5. Query all records in the entity

**Pass condition**: All five activity elements present — `uda:CreateEntityRecord`, `uda:GetEntityRecordById`, `uda:UpdateEntityRecord`, `uda:DeleteEntityRecord`, `uda:QueryEntityRecords` — each with `x:TypeArguments="local:CodingAgentsEvalEntity"`; no other `uda:` activity elements present; build passes.

---

### S2 — Batch Activities

**Prompt**:
> Build a workflow that performs these independent batch operations on Data Service entity `CodingAgentsEvalEntity`:
> 1. Create 3 records in batch with Titles `'A'`, `'B'`, `'C'`
> 2. Update 3 existing records in batch, setting `Title` to `'X'`
> 3. Delete 3 existing records in batch

**Pass condition**: All three activity elements present — `uda:CreateMultipleEntityRecords`, `uda:UpdateMultipleEntityRecords`, `uda:DeleteMultipleEntityRecords` — each with `x:TypeArguments="local:CodingAgentsEvalEntity"`; no other `uda:` activity elements present; build passes.

---

### S3 — File Activities

**Prompt**:
> Build a workflow that performs these independent file operations on Data Service entity `CodingAgentsEvalFileEntity`:
> 1. Upload `'C:\temp\test.txt'` to the `Attachment` field of an existing record
> 2. Download the file from the `Report` field of another existing record
> 3. Delete the file from the `Contract` field of another existing record

**Pass condition**: All three activity elements present — `uda:UploadFileToRecordField`, `uda:DownloadFileFromRecordField`, `uda:DeleteFileFromRecordField` — each with `x:TypeArguments="local:CodingAgentsEvalFileEntity"`; no other `uda:` activity elements present; build passes.

---

## 4. Integration

**Purpose**: Verify that each activity is configured perfectly — every property, every attribute, every edge case — one activity at a time. Scenarios are organized per-activity, with exhaustive coverage of each activity's configuration space. Each scenario gates against regressions in both the agent and the activity reference documentation.

**Anti-pattern scenarios** (marked with "Anti-pattern:" prefix) are a key sub-category: they use adversarial or misleading prompts to verify the agent avoids known mistakes that compile but fail at runtime or cause Studio desync.

**Error-path scenarios** (section 4.12) verify the agent handles activity failures correctly — not just setting `ContinueOnError`, but guarding against null outputs downstream and consuming `FailedRecords` for logging or retry.

**Evaluation**: Full property validation on every attribute of the activity under test. Each activity subsection defines a **configuration baseline** — the set of properties checked on every scenario for that activity. Individual scenarios' **Key Semantic Checks** capture what is unique to that prompt.

Integration prompts pass entity and field names only — no GUIDs. Scenarios that reference pre-existing records use permanently resident records in CodingAgentsEvals.

---

### 4.1 CreateEntityRecord

> **Configuration baseline** (checked on every scenario): `x:TypeArguments="local:CodingAgentsEvalEntity"`, `EntityId` matches EntitiesStore.json, `ScopeValue="Tenant"`, `IsInRecordView="[False]"`, `InputEntityInFieldView` present (not `InputEntity`), `RecordState.SelectedFields` present with correct `DynamicEntityField` entries, `OutputEntity` bound, `VisibleDynamicPropertiesInfo="{x:Null}"`, build passes.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I1 | **Single required field** | "Create a record in Data Service entity `CodingAgentsEvalEntity` with `Title` set to `'OnlyRequired'`." | Verifies the minimal valid Create — only the required field in RecordState, no extraneous optional field entries. | `RecordState` has exactly one `DynamicEntityField` for `Title` with `IsRequired="True"` and `ArgumentValue` set; optional fields absent from both `RecordState` and `InputEntityInFieldView` |
| I2 | **All scalar field types** | "Create a record in Data Service entity `CodingAgentsEvalEntity` with `Title` `'TypeTest'`, `Score` `42`, `Price` `9.99`, `IsActive` `true`, `EventDate` `'2026-04-18'`, and `ScheduledAt` `'2026-04-18T09:00:00+05:30'`." | Verifies the agent maps each SqlType to its correct XAML type — INT → `x:Int32`, DECIMAL → `x:Decimal`, BIT → `x:Boolean`, DATE and DATETIMEOFFSET → `x:String` (ISO 8601). | `InputEntityInFieldView` constructs entity with all 6 fields using correct typed literals; `RecordState` has 6 `DynamicEntityField` entries with matching types; date fields use `x:String` not .NET DateTime |
| I3 | **Required + optional fields** | "Create a record in Data Service entity `CodingAgentsEvalEntity` with `Title` `'WithOptional'` and `Notes` `'Some notes'`." | Verifies the agent correctly distinguishes required vs optional fields in RecordState — both present, with correct `IsRequired` flags. | `RecordState` has two `DynamicEntityField` entries: `Title` with `IsRequired="True"`, `Notes` with `IsRequired="False"`; both have `ArgumentValue` set |
| I4 | **ContinueOnError=True** | "Create a record in Data Service entity `CodingAgentsEvalEntity` with `Title` `'ErrorTest'`. The workflow should continue even if the activity fails." | Verifies `ContinueOnError` is set as a bracketed Boolean expression. | `ContinueOnError="[True]"` on the activity |
| I5 | **Anti-pattern: InputEntity property** | "Create a record in Data Service entity `CodingAgentsEvalEntity` with `Title` `'SafeCreate'` by setting the entity object directly." | Verifies the agent uses `InputEntityInFieldView` + `RecordState` even when the prompt implies direct entity object assignment — `InputEntity` causes Studio desync. | `InputEntityInFieldView` present and set; `InputEntity` property absent from activity element |
| I6 | **Anti-pattern: file field in RecordState** | "Create a record in Data Service entity `CodingAgentsEvalFileEntity` with `Title` `'DocRecord'` and attach a file to the `Attachment` field." | Verifies the agent excludes File-typed fields from `RecordState` — file fields must only be manipulated via file activities. Uses `x:TypeArguments="local:CodingAgentsEvalFileEntity"` (exception to baseline). | `RecordState` contains only `Title` DynamicEntityField; `Attachment` absent from both `RecordState` and `InputEntityInFieldView`; agent either omits the file instruction from CreateEntityRecord or sequences a separate `UploadFileToRecordField` |

---

### 4.2 GetEntityRecordById

> **Configuration baseline**: `x:TypeArguments="local:CodingAgentsEvalEntity"`, `EntityId` matches EntitiesStore.json, `RecordId` bound, `OutputEntity` bound, no `RecordState`, no `IsInRecordView`, no `InputEntityInFieldView`, `ExpansionDepth` at default or as specified, build passes.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I7 | **Basic fetch** | "Fetch a record from Data Service entity `CodingAgentsEvalEntity` by its ID and return it as a workflow output." | Verifies the full default configuration of a read-only activity — no write-mode properties present. | `OutputEntity` bound to out-argument; `ExpansionDepth` absent or at default `"[2]"`; no `RecordState`, `IsInRecordView`, or `InputEntityInFieldView` |
| I8 | **ExpansionDepth override** | "Fetch a record from Data Service entity `CodingAgentsEvalEntity` and expand related entities to depth 1 only." | Verifies the agent sets `ExpansionDepth` to a non-default value. | `ExpansionDepth="[1]"` |
| I9 | **OutputEntity used downstream** | "Fetch a record from Data Service entity `CodingAgentsEvalEntity` by its ID and log its `Title` field value to the output." | Verifies `OutputEntity` is bound to a typed variable whose fields are accessed in a subsequent activity. | `OutputEntity` bound to a typed variable (e.g. `retrievedRecord`); subsequent activity references `retrievedRecord.Title` |
| I10 | **Anti-pattern: IEntity type argument** | "Fetch a record from Data Service entity `CodingAgentsEvalEntity` using the generic entity interface type." | Verifies the agent uses the concrete entity type even when the prompt suggests a generic interface — `udd:IEntity` compiles but fails at runtime. | `x:TypeArguments="local:CodingAgentsEvalEntity"` — NOT `udd:IEntity` |

---

### 4.3 UpdateEntityRecord

> **Configuration baseline**: `x:TypeArguments="local:CodingAgentsEvalEntity"`, `EntityId` matches EntitiesStore.json, `RecordId` bound, `IsInRecordView="[False]"`, `InputEntityInFieldView` present (not `InputEntity`), `RecordState.SelectedFields` present, `OutputEntity` bound, `VisibleDynamicPropertiesInfo="{x:Null}"`, build passes.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I11 | **Partial field update** | "Update only the `Title` field of a pre-existing record in Data Service entity `CodingAgentsEvalEntity`, setting it to `'Revised'`. The entity also has `Score`, `Notes`, and `Price` fields — leave them unchanged." | Verifies the agent includes only the field being updated in `RecordState.SelectedFields`. | `RecordState` has exactly one `DynamicEntityField` for `Title`; `Score`, `Notes`, `Price` absent from both `RecordState` and `InputEntityInFieldView` |
| I12 | **Multi-type field update** | "Update a pre-existing record in Data Service entity `CodingAgentsEvalEntity`: set `Title` to `'Updated'`, `Score` to `99`, `Price` to `19.99`, and `IsActive` to `false`." | Verifies correct XAML types across multiple field updates in a single activity. | `InputEntityInFieldView` sets all 4 fields with correct typed literals; `RecordState` has 4 `DynamicEntityField` entries with matching types |
| I13 | **Empty-string update** | "Update the `Title` field of a pre-existing record in Data Service entity `CodingAgentsEvalEntity` to an empty string." | Verifies the agent represents an intentional empty-string update rather than omitting the field. | `InputEntityInFieldView` sets `Title = ""`; `DynamicEntityField` for Title has `ArgumentValue` set to empty string (not null or absent) |
| I14 | **ContinueOnError=True** | "Update the `Title` of a pre-existing record in Data Service entity `CodingAgentsEvalEntity` to `'SafeUpdate'`. The workflow should continue even if the update fails." | Verifies `ContinueOnError` on an update activity. | `ContinueOnError="[True]"` |
| I15 | **Anti-pattern: InputEntity property** | "Update the `Score` field of a pre-existing record in Data Service entity `CodingAgentsEvalEntity` to `100`." | Verifies the agent uses `InputEntityInFieldView` + `RecordState` by default — `InputEntity` causes Studio desync. | `InputEntityInFieldView` present and set; `InputEntity` property absent from activity element |

---

### 4.4 DeleteEntityRecord

> **Configuration baseline**: `x:TypeArguments="local:CodingAgentsEvalEntity"`, `EntityId` matches EntitiesStore.json, `RecordId` bound, `ScopeValue="Tenant"`, Solution properties nulled, no `RecordState`, no `IsInRecordView`, no `InputEntityInFieldView`, no `OutputEntity`, build passes.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I16 | **Basic delete** | "Delete a pre-existing record from Data Service entity `CodingAgentsEvalEntity`." | Verifies the full default configuration — no write-mode or read-mode properties present. | All baseline properties verified; no extraneous properties |
| I17 | **ContinueOnError=True** | "Delete a pre-existing record from Data Service entity `CodingAgentsEvalEntity`. The workflow should not abort if the deletion fails." | Verifies `ContinueOnError` without introducing any write-mode properties. | `ContinueOnError="[True]"`; still no `RecordState`, `IsInRecordView`, or `OutputEntity` |

---

### 4.5 QueryEntityRecords

> **Configuration baseline** (checked on every scenario): `x:TypeArguments="local:CodingAgentsEvalEntity"` (or `local:CodingAgentsEvalFileEntity` for I35), `EntityId` matches EntitiesStore.json, `OutputRecords` bound, no `RecordState`, no `IsInRecordView`, no `InputEntityInFieldView`, build passes.
>
> Filter scenarios additionally verify: `FilterArguments` contains correct `GroupFilter` / `SimpleFilter` structure, `FilterValues` has correctly typed `InArgument` entries at the right `ValueIndex`, operator strings are XML-escaped where needed.

#### Standard Value Operators

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I18 | **Equals on string** | "Query all records in Data Service entity `CodingAgentsEvalEntity` where `Status` equals `'Active'`." | Baseline equality filter on NVARCHAR. | `FilterArguments`: `Equals` on `Status`; `FilterValues`: `x:String` = `'Active'` |
| I19 | **Contains on string** | "Query all records in Data Service entity `CodingAgentsEvalEntity` where `Title` contains `'Invoice'`." | Verifies `Contains` operator (not `Equals` or `StartsWith`). | `FilterArguments`: `Contains` on `Title`; `FilterValues`: `x:String` = `'Invoice'` |
| I20 | **MoreThan + LessThan on numeric (combined)** | "Query all records in Data Service entity `CodingAgentsEvalEntity` where `Score` is greater than `50` and `Price` is less than `20`." | Verifies both XML-escaped comparison operators in a single AND filter — `MoreThan` (`&gt;`) and `LessThan` (`&lt;`). | `FilterArguments`: AND group with `MoreThan` on `Score` (Operator: `&gt;`) and `LessThan` on `Price` (Operator: `&lt;`); `FilterValues`: `x:Int32` = `50` and `x:Decimal` = `20`; `ValueIndex` globally sequential |

#### Value-less Operators

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I21 | **IsEmpty + IsNull (combined)** | "Query all records in Data Service entity `CodingAgentsEvalEntity` where the `Notes` field is empty and the `Status` field has no value set (is null)." | Verifies both positive value-less operators in a single AND filter — forces the agent to demonstrate it knows empty ≠ null. Both require `<x:Null />` slots in `FilterValues`. | `FilterArguments`: AND group with `is empty` on `Notes` and `is null` on `Status`; `FilterValues` has `<x:Null />` at both corresponding `ValueIndex` slots |
| I22 | **IsNotEmpty + IsNotNull (combined)** | "Query all records in Data Service entity `CodingAgentsEvalEntity` where the `Notes` field is not empty and the `Status` field has a value set (is not null)." | Verifies both negative value-less operators. | `FilterArguments`: AND group with `not empty` on `Notes` and `is not null` on `Status`; `FilterValues` has `<x:Null />` at both corresponding `ValueIndex` slots |

#### Boolean Operators

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I23 | **IsTrue on BIT** | "Query all records in Data Service entity `CodingAgentsEvalEntity` where `IsActive` is true." | Verifies `IsTrue` — requires an `x:Boolean` InArgument with value `True` in `FilterValues` (NOT value-less). | `FilterArguments`: `Equals true` on `IsActive`; `FilterValues`: `x:Boolean` = `True` |
| I24 | **IsFalse on BIT** | "Query all records in Data Service entity `CodingAgentsEvalEntity` where `IsActive` is false." | Verifies `IsFalse`. | `FilterArguments`: `Equals false` on `IsActive`; `FilterValues`: `x:Boolean` = `False` |

#### Array Operators

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I25 | **In + NotIn (combined)** | "Query all records in Data Service entity `CodingAgentsEvalEntity` where `Status` is one of `'Active'`, `'Pending'`, or `'Review'` and `Title` is not one of `'Draft'`, `'Test'`." | Verifies both array operators in a single AND filter — both require `s:String[]` regardless of field SqlType. | `FilterArguments`: AND group with `in` on `Status` and `not in` on `Title`; `FilterValues`: two `s:String[]` entries (3 values and 2 values respectively); `ValueIndex` globally sequential |

#### Date and DateTime

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I26 | **Equals on DATE** | "Query all records in Data Service entity `CodingAgentsEvalEntity` where `EventDate` equals `'2026-04-18'`." | Verifies DATE equality uses `x:String` with ISO 8601, not a .NET DateTime literal. | `FilterArguments`: `Equals` on `EventDate`; `FilterValues`: `x:String` = `'2026-04-18'` |
| I27 | **MoreThan on DATETIMEOFFSET** | "Query all records in Data Service entity `CodingAgentsEvalEntity` where `ScheduledAt` is after `'2026-04-01T00:00:00Z'`." | Verifies DATETIMEOFFSET comparison with XML-escaped `>` and ISO 8601 string value. | `FilterArguments`: `MoreThan` on `ScheduledAt` (Operator: `&gt;`); `FilterValues`: `x:String` = `'2026-04-01T00:00:00Z'` |
| I28 | **Date range (NoLessThan + NoMoreThan)** | "Query all records in Data Service entity `CodingAgentsEvalEntity` where `EventDate` falls between `'2026-01-01'` and `'2026-12-31'` inclusive." | Verifies compound range filter using `NoLessThan` (`&gt;=`) and `NoMoreThan` (`&lt;=`) on a DATE field. | `FilterArguments` has two conditions on `EventDate`: `NoLessThan` and `NoMoreThan`; both `FilterValues` entries are `x:String` with ISO 8601 dates |

#### Compound Filters

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I29 | **AND group** | "Query records in Data Service entity `CodingAgentsEvalEntity` where `Status` equals `'Active'` and `Score` is greater than `10`." | Verifies two conditions in a single AND group with globally sequential `ValueIndex`. | `GroupFilter` with `Operator="AND"`; two `SimpleFilter` entries; `ValueIndex` values are 0 and 1 |
| I30 | **OR group** | "Query records in Data Service entity `CodingAgentsEvalEntity` where `Status` equals `'Active'` or `Status` equals `'Pending'`." | Verifies OR group — the agent must not default to AND. | `GroupFilter` with `Operator="OR"`; two `SimpleFilter` entries on `Status` |
| I31 | **Nested groups (AND root with OR child)** | "Query records in Data Service entity `CodingAgentsEvalEntity` where `IsActive` is true and either `Score` is greater than `50` or `Status` equals `'Priority'`." | Verifies nested group structure: root AND group containing a leaf filter and a child OR group. | Root `GroupFilter` `Operator="AND"` with one `SimpleFilter` (IsActive) and one child `GroupFilter` `Operator="OR"` with two `SimpleFilter` entries; `ValueIndex` globally sequential across all filters |

#### Sort and Pagination

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I32 | **Sort descending + Top + Skip + TotalRecords** | "Query records in Data Service entity `CodingAgentsEvalEntity`, sorted by `Score` from highest to lowest, returning the second page of 10 records. Include the total record count." | Verifies sort, pagination, and TotalRecords output wiring together. | `SortByField="Score"`; `SortAscending="[False]"`; `Top="[10]"`; `Skip="[10]"`; `TotalRecords` bound to a variable or out-argument |

#### ChoiceSet and Relationship

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I33 | **Equals on ChoiceSetSingle** | "Query all records in Data Service entity `CodingAgentsEvalEntity` where `Category` equals `'Urgent'`." | Verifies filter on a ChoiceSetSingle field — same `Equals` operator but on a non-Basic FieldDisplayType. | `FilterArguments`: `Equals` on `Category`; `FilterValues`: `x:String` = `'Urgent'` |
| I34 | **In on ChoiceSetMultiple** | "Query all records in Data Service entity `CodingAgentsEvalEntity` where `Tags` includes any of `'frontend'`, `'backend'`." | Verifies `In` on a multi-value choice field — uses `s:String[]`. | `FilterArguments`: `in` on `Tags`; `FilterValues`: `s:String[]` containing `'frontend'`, `'backend'` |
| I35 | **Relationship dot-notation** | "Query all records in Data Service entity `CodingAgentsEvalFileEntity` where the related `Owner` entity's `Title` contains `'Admin'`." | Verifies the agent uses dot notation (`Owner.Title`) in the filter FieldName for relationship traversal. | `FilterArguments`: `Contains` on `Owner.Title`; `FilterValues`: `x:String` = `'Admin'` |

#### Remaining Operators

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I36 | **StartsWith + EndsWith (combined)** | "Query all records in Data Service entity `CodingAgentsEvalEntity` where `Title` starts with `'INV'` and `Status` ends with `'ed'`." | Verifies `StartsWith` and `EndsWith` in a single AND filter — both are string-match direction operators, aggregated because they are structurally identical. | `FilterArguments`: AND group with `StartsWith` on `Title` and `EndsWith` on `Status`; `FilterValues`: two `x:String` entries; `ValueIndex` globally sequential |
| I37 | **NotEquals + NotContains (combined)** | "Query all records in Data Service entity `CodingAgentsEvalEntity` where `Status` does not equal `'Closed'` and `Title` does not contain `'DRAFT'`." | Verifies `NotEquals` and `NotContains` — negation operators that agents frequently confuse with their positive counterparts, aggregated because they are structurally identical. | `FilterArguments`: AND group with `NotEquals` on `Status` and `NotContains` on `Title`; `FilterValues`: two `x:String` entries; `ValueIndex` globally sequential |

---

### 4.6 CreateMultipleEntityRecords

> **Configuration baseline**: `x:TypeArguments="local:CodingAgentsEvalEntity"`, `EntityId` matches EntitiesStore.json, `InputRecords` as `ICollection<CodingAgentsEvalEntity>` (fully constructed entity objects), `OutputRecords` bound, `FailedRecords` bound and typed `IList(Of Tuple(Of String, CodingAgentsEvalEntity))`, no `RecordState`, no `IsInRecordView`, build passes.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I38 | **Large batch** | "Create 10 records in Data Service entity `CodingAgentsEvalEntity` with Titles `'R01'` through `'R10'`." | Verifies the agent uses a single batch activity (not 10 individual Creates) and constructs a list of 10 entity objects. | Single `uda:CreateMultipleEntityRecords`; `InputRecords` constructs 10 `CodingAgentsEvalEntity` objects |
| I39 | **ContinueBatchOnFailure=False** | "Create 3 records in Data Service entity `CodingAgentsEvalEntity`. Stop the entire batch immediately if any record fails." | Verifies `ContinueBatchOnFailure` is explicitly set to False (default is True). | `ContinueBatchOnFailure="[False]"` |
| I40 | **FailedRecords Tuple type** | "Create 3 records in Data Service entity `CodingAgentsEvalEntity` and capture any failed records with their error messages." | Verifies `FailedRecords` is correctly typed — `Item1` is the error string, `Item2` is the failed entity. | `FailedRecords` bound to variable typed `IList(Of Tuple(Of String, CodingAgentsEvalEntity))` |

---

### 4.7 UpdateMultipleEntityRecords

> **Configuration baseline**: `x:TypeArguments="local:CodingAgentsEvalEntity"`, `EntityId` matches EntitiesStore.json, `InputRecords` as `ICollection<CodingAgentsEvalEntity>` (each entity must have `Id` set), `OutputRecords` bound, `FailedRecords` bound and typed `IList(Of Tuple(Of String, CodingAgentsEvalEntity))`, build passes.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I41 | **Id required on each entity** | "Update the `Title` field of 3 pre-existing records in Data Service entity `CodingAgentsEvalEntity` to `'Updated1'`, `'Updated2'`, `'Updated3'` respectively." | Verifies each entity in `InputRecords` carries its `Id` property — missing `Id` causes silent failure. | `InputRecords` expression constructs entities with both `.Id` and `.Title` set on each object |
| I42 | **ContinueBatchOnFailure=False** | "Update 3 records in Data Service entity `CodingAgentsEvalEntity`. Abort the batch if any update fails." | Verifies `ContinueBatchOnFailure` is set to False. | `ContinueBatchOnFailure="[False]"` |
| I43 | **FailedRecords Tuple type** | "Update 3 records in Data Service entity `CodingAgentsEvalEntity` and capture failed updates with their error messages." | Verifies `FailedRecords` for batch update uses the same Tuple type as batch create. | `FailedRecords` typed `IList(Of Tuple(Of String, CodingAgentsEvalEntity))` |

---

### 4.8 DeleteMultipleEntityRecords

> **Configuration baseline**: `x:TypeArguments="local:CodingAgentsEvalEntity"`, `EntityId` matches EntitiesStore.json, `InputRecords` as `ICollection<Guid>` (**not** entity objects), `FailedRecords` bound and typed `IList(Of Guid)` (**not** Tuple), no `RecordState`, no `IsInRecordView`, build passes.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I44 | **Guid input (not entity objects)** | "Delete 3 pre-existing records from Data Service entity `CodingAgentsEvalEntity` in a single batch operation." | Verifies `InputRecords` is a Guid collection — the most common batch delete type error. | `InputRecords` produces `ICollection(Of Guid)` or `List(Of Guid)`; entity objects not used |
| I45 | **ContinueBatchOnFailure=False** | "Delete 3 records from Data Service entity `CodingAgentsEvalEntity`. Stop immediately if any deletion fails." | Verifies `ContinueBatchOnFailure` is set to False. | `ContinueBatchOnFailure="[False]"` |
| I46 | **FailedRecords Guid type (not Tuple)** | "Delete 3 records from Data Service entity `CodingAgentsEvalEntity` and capture the IDs of any that could not be deleted." | Verifies `FailedRecords` for batch delete is `IList(Of Guid)` — not the Tuple type used by create/update. | `FailedRecords` typed `IList(Of Guid)` |

---

### 4.9 UploadFileToRecordField

> **Configuration baseline**: `x:TypeArguments="local:CodingAgentsEvalFileEntity"`, `EntityId` matches EntitiesStore.json, `RecordId` bound, `Field` set by name (matching a `FieldDisplayType: "File"` entry), `OutputEntity` bound, no `RecordState`, no `IsInRecordView`, build passes.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I47 | **FilePath input** | "Upload `'C:\docs\report.pdf'` to the `Report` field of a pre-existing record in Data Service entity `CodingAgentsEvalFileEntity`." | Verifies the `FilePath` input mode with the correct file field. | `FilePath` set to `"C:\docs\report.pdf"`; `FileResource` absent or null; `Field="Report"` |
| I48 | **FileResource input** | "Upload a file resource to the `Attachment` field of a pre-existing record in Data Service entity `CodingAgentsEvalFileEntity`. The file is available as a resource object in variable `fileRes`." | Verifies the `FileResource` input mode (InArgument<IResource>) — mutually exclusive with `FilePath`. | `FileResource` bound to `fileRes`; `FilePath` absent or null |
| I49 | **Field name case sensitivity** | "Upload `'C:\temp\file.txt'` to the field named `attachmentFile` (camelCase) on a pre-existing record in Data Service entity `CodingAgentsEvalFileEntity`." | Verifies the agent preserves exact field name casing — field names are case-sensitive at runtime. | `Field="attachmentFile"` exactly (not `AttachmentFile` or `attachment_file`) |

---

### 4.10 DownloadFileFromRecordField

> **Configuration baseline**: `x:TypeArguments="local:CodingAgentsEvalFileEntity"`, `EntityId` matches EntitiesStore.json, `RecordId` bound, `Field` set by name, no `RecordState`, no `IsInRecordView`, no `ExpansionDepth`, build passes.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I50 | **With explicit FilePath** | "Download the file from the `Attachment` field of a pre-existing record in Data Service entity `CodingAgentsEvalFileEntity` and save it to `'C:\temp\downloaded.txt'`." | Verifies `FilePath` and `DownloadedFileResource` are both set when a destination path is given. | `FilePath` set; `DownloadedFileResource` bound; `Field="Attachment"` |
| I51 | **Without FilePath (resource only)** | "Download the file from the `Attachment` field of a pre-existing record in Data Service entity `CodingAgentsEvalFileEntity` and make it available for further processing." | Verifies `DownloadedFileResource` is wired when no path is specified. | `DownloadedFileResource` bound to variable; `FilePath` absent or null |
| I52 | **DownloadedFileResource.LocalPath downstream** | "Download the file from the `Report` field of a pre-existing record in Data Service entity `CodingAgentsEvalFileEntity` and log its local file path." | Verifies the agent correctly models the `ILocalResource` type returned by the download. | `DownloadedFileResource` bound to typed variable; subsequent activity references `.LocalPath` on that variable |

---

### 4.11 DeleteFileFromRecordField

> **Configuration baseline**: `x:TypeArguments="local:CodingAgentsEvalFileEntity"`, `EntityId` matches EntitiesStore.json, `RecordId` bound, `Field` set by name, `OutputEntity` bound, no `RecordState`, no `IsInRecordView`, build passes.

| ID | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|--------|--------------|---------------------|
| I53 | **Basic file delete + OutputEntity** | "Delete the file from the `Attachment` field of a pre-existing record in Data Service entity `CodingAgentsEvalFileEntity` and return the updated entity state." | Verifies `OutputEntity` is wired — unlike `DeleteEntityRecord`, this activity returns the entity post-deletion. | `OutputEntity` bound to a variable or out-argument |
| I54 | **ContinueOnError=True** | "Delete the file from the `Report` field of a pre-existing record in Data Service entity `CodingAgentsEvalFileEntity`. The workflow should proceed even if no file is attached." | Verifies `ContinueOnError` on a file delete activity. | `ContinueOnError="[True]"` |

---

### 4.12 Error-Path Scenarios

> These scenarios verify the agent handles activity failures correctly — not just setting `ContinueOnError`, but acting on the failure downstream. Each tests a single activity's error surface.

| ID | Activity | Scenario | Prompt | Eval Summary | Key Semantic Checks |
|----|----------|----------|--------|--------------|---------------------|
| I55 | `CreateEntityRecord` | **ContinueOnError + downstream null guard** | "Create a record in Data Service entity `CodingAgentsEvalEntity` with `Title` `'MayFail'`. The activity should continue on error. After the create, log the record's `Title` — but only if the record was actually created." | Verifies the agent adds a conditional check on `OutputEntity` before accessing its properties downstream when `ContinueOnError` is True — without the guard, a failed create causes a NullReferenceException on the next step. | `ContinueOnError="[True]"`; conditional (`If` or `FlowDecision`) checks `OutputEntity IsNot Nothing` before the downstream activity that accesses `OutputEntity.Title` |
| I56 | `CreateMultipleEntityRecords` | **FailedRecords iteration and logging** | "Create 5 records in Data Service entity `CodingAgentsEvalEntity` with Titles `'F01'` through `'F05'`. After the batch, iterate over any failed records and log each error message alongside the failed record's `Title`." | Verifies the agent consumes `FailedRecords` — iterates the `Tuple(Of String, Entity)` list and accesses both `.Item1` (error string) and `.Item2` (failed entity). | `FailedRecords` bound to typed variable; `ForEach` or equivalent iterates `FailedRecords`; loop body accesses `.Item1` (error message) and `.Item2.Title` (failed entity field) |
| I57 | `UpdateMultipleEntityRecords` | **FailedRecords retry** | "Update 3 pre-existing records in Data Service entity `CodingAgentsEvalEntity`, setting `Status` to `'Processed'`. If any updates fail, retry only the failed records once more." | Verifies the agent extracts failed entities from `FailedRecords`, reconstructs an input collection from `.Item2`, and calls a second `UpdateMultipleEntityRecords` — gated by a count check to avoid an empty retry. | First `UpdateMultipleEntityRecords` has `FailedRecords` bound; conditional checks `FailedRecords.Count > 0`; second `UpdateMultipleEntityRecords` with `InputRecords` sourced from first batch's `FailedRecords` `.Item2` values |

---

## 5. Quality

**Purpose**: Verify the agent can compose multiple activities into a coherent, realistic workflow that resembles what a real customer would ask. Quality scenarios span activity categories — record CRUD, batch operations, file operations, filtered queries — in a single workflow. They test the plumbing between steps, not the configuration of individual activities.

**Evaluation**: Assertions focus on workflow-level correctness:
- Correct activities present in the right sequence
- Output-to-input data flow (variable chaining between steps)
- Type consistency (`x:TypeArguments` shared across all activities for the same entity)
- Structural decisions at activity boundaries (e.g. file fields excluded from RecordState, Guid collection for batch delete)
- Build passes

Per-activity property details (RecordState shape, filter operator encoding, field-level bindings) are intentionally NOT asserted — that is Integration's job.

---

### E1 — Ingest, Filter, and Clean

> "Create 5 records in Data Service entity `CodingAgentsEvalEntity` with Titles `'ORD-001'` through `'ORD-005'` and `Score` values `10`, `20`, `60`, `80`, `30`. Query all records where `Score` is greater than `50`, sorted by `Score` descending. Update the matching records to set `Status` to `'Priority'`. Then delete those same records in batch."

**Eval summary:** Tests the full batch lifecycle with a filter-driven pivot. The key composition challenge is the type switch between batch update (`ICollection<Entity>` with `.Id`) and batch delete (`ICollection<Guid>`) operating on the same result set.

| Step | Activity | Plumbing Assertions |
|------|----------|---------------------|
| 1 | `CreateMultipleEntityRecords` | `OutputRecords` → `createdRecords`; 5 entity objects in `InputRecords` |
| 2 | `QueryEntityRecords` | `OutputRecords` → `highScoreRecords`; filter present on `Score` |
| 3 | `UpdateMultipleEntityRecords` | `InputRecords` sourced from `highScoreRecords` (entity objects with `.Id`); `OutputRecords` or `FailedRecords` wired |
| 4 | `DeleteMultipleEntityRecords` | `InputRecords` is `ICollection<Guid>` — IDs extracted from step 2 or 3 output; NOT entity objects |

**Build condition:** `uip rpa get-errors` exits 0; all activities share `x:TypeArguments="local:CodingAgentsEvalEntity"`.

---

### E2 — Document Lifecycle Across Multiple Records

> "Create 3 records in Data Service entity `CodingAgentsEvalFileEntity` with Titles `'Contract-A'`, `'Contract-B'`, `'Contract-C'`. Upload `'C:\docs\a.pdf'` to the `Contract` field of the first record, `'C:\docs\b.pdf'` to the second, and `'C:\docs\c.pdf'` to the third. Download the file from each record's `Contract` field. Then delete the file attachment from all 3 records."

**Eval summary:** Tests file operations across multiple records. The key plumbing challenge is iterating over batch-created records and maintaining correct `RecordId` binding for each file operation, with consistent `Field` value across upload, download, and delete.

| Step | Activity | Plumbing Assertions |
|------|----------|---------------------|
| 1 | `CreateMultipleEntityRecords` | `OutputRecords` → `createdRecords`; 3 entity objects |
| 2 | `UploadFileToRecordField` (×3) | Each `RecordId` bound to a distinct `createdRecords` item; `Field="Contract"` on all |
| 3 | `DownloadFileFromRecordField` (×3) | Each `RecordId` matches the upload target; `Field="Contract"` on all; `DownloadedFileResource` wired |
| 4 | `DeleteFileFromRecordField` (×3) | Each `RecordId` matches; `Field="Contract"` on all; `OutputEntity` wired |

**Build condition:** `uip rpa get-errors` exits 0; all activities share `x:TypeArguments="local:CodingAgentsEvalFileEntity"`; `Contract` field absent from any `RecordState`.

---

### E3 — Single-Record Full Lifecycle

> "Create a record in Data Service entity `CodingAgentsEvalEntity` with `Title` `'Lifecycle Test'` and `Score` `42`. Read the record back by its ID. Update `Score` to `100`. Read it again to verify the update. Then delete the record."

**Eval summary:** Exercises all 5 individual record activities in a single workflow. The primary plumbing test is consistent `createdRecord.Id` chaining across all steps, and that Read activities carry no write-mode properties while Create/Update do.

| Step | Activity | Plumbing Assertions |
|------|----------|---------------------|
| 1 | `CreateEntityRecord` | `OutputEntity` → `createdRecord` |
| 2 | `GetEntityRecordById` | `RecordId` = `createdRecord.Id`; `OutputEntity` → `fetchedRecord` |
| 3 | `UpdateEntityRecord` | `RecordId` = `createdRecord.Id`; `OutputEntity` wired |
| 4 | `GetEntityRecordById` | `RecordId` = `createdRecord.Id`; `OutputEntity` → `verifiedRecord` |
| 5 | `DeleteEntityRecord` | `RecordId` = `createdRecord.Id`; no `OutputEntity` |

**Build condition:** `uip rpa get-errors` exits 0; all activities share `x:TypeArguments="local:CodingAgentsEvalEntity"`; Get and Delete carry no `RecordState` or `IsInRecordView`.

---

### E4 — Compound Filter with Batch Update and Verification

> "Create 3 records in Data Service entity `CodingAgentsEvalEntity`: (`Title`=`'Alpha'`, `Score`=`5`, `IsActive`=`true`), (`Title`=`'Beta'`, `Score`=`15`, `IsActive`=`true`), (`Title`=`'Gamma'`, `Score`=`25`, `IsActive`=`false`). Query records where `IsActive` is true and `Score` is greater than `10`. Update the matching records to set `Score` to `0`. Then query again where `Score` equals `0` to verify, and return the total count of verified records as a workflow output."

**Eval summary:** Tests compound filter → batch update → verification query. The plumbing challenges are: compound AND filter on two different field types (BIT + INT), ID propagation from query to batch update, and `TotalRecords` wired as a workflow output on the verification query.

| Step | Activity | Plumbing Assertions |
|------|----------|---------------------|
| 1 | `CreateMultipleEntityRecords` | `OutputRecords` → `createdRecords`; 3 entity objects |
| 2 | `QueryEntityRecords` | Compound filter present (2 conditions); `OutputRecords` → `matches` |
| 3 | `UpdateMultipleEntityRecords` | `InputRecords` sourced from `matches` with `.Id` set; `OutputRecords` or `FailedRecords` wired |
| 4 | `QueryEntityRecords` | Verification filter on `Score`; `OutputRecords` wired; `TotalRecords` → workflow out-argument |

**Build condition:** `uip rpa get-errors` exits 0; all activities share `x:TypeArguments="local:CodingAgentsEvalEntity"`; `TotalRecords` bound to a workflow-level out-argument.

---

### E5 — CRUD + File Mixed Workflow

> "Create a record in Data Service entity `CodingAgentsEvalFileEntity` with `Title` set to `'Contract Doc'`. Upload `'C:\contracts\final.pdf'` to the `Contract` field. Update the record's `Title` to `'Signed Contract'`. Read the record back by its ID. Download the `Contract` file. Then delete the file from the `Contract` field."

**Eval summary:** Exercises all three activity categories (record CRUD, file upload/download, file delete) in a single workflow on a file entity. The key plumbing tests are: `Contract` field never appears in any `RecordState` (not on Create, not on Update), consistent `RecordId` chaining across 6 activities, and correct `Field` value on all file operations.

| Step | Activity | Plumbing Assertions |
|------|----------|---------------------|
| 1 | `CreateEntityRecord` | `OutputEntity` → `createdRecord`; `Contract` absent from `RecordState` |
| 2 | `UploadFileToRecordField` | `RecordId` = `createdRecord.Id`; `Field="Contract"` |
| 3 | `UpdateEntityRecord` | `RecordId` = `createdRecord.Id`; `Contract` absent from `RecordState` |
| 4 | `GetEntityRecordById` | `RecordId` = `createdRecord.Id`; `OutputEntity` wired |
| 5 | `DownloadFileFromRecordField` | `RecordId` = `createdRecord.Id`; `Field="Contract"`; `DownloadedFileResource` wired |
| 6 | `DeleteFileFromRecordField` | `RecordId` = `createdRecord.Id`; `Field="Contract"`; `OutputEntity` wired |

**Build condition:** `uip rpa get-errors` exits 0; all 6 activities share `x:TypeArguments="local:CodingAgentsEvalFileEntity"`; `Contract` absent from `RecordState` on steps 1 and 3.

---

### E6 — Error Recovery in Multi-Step Pipeline

> "Create a record in Data Service entity `CodingAgentsEvalEntity` with `Title` `'Risky Op'` and `Score` `50`. Attempt to update the record's `Score` to `999` — wrap this update in error handling so the workflow continues if it fails. If the update succeeded, query all records where `Score` equals `999`. If the update failed, log the error and delete the original record as cleanup."

**Eval summary:** Tests TryCatch-based error handling across a multi-step workflow. The agent must wrap the Update in a `TryCatch`, branch on success vs failure, and execute different activity paths in each branch — while maintaining consistent `RecordId` chaining. This is the only scenario that tests branching control flow around DataService activities.

| Step | Activity | Plumbing Assertions |
|------|----------|---------------------|
| 1 | `CreateEntityRecord` | `OutputEntity` → `createdRecord` |
| 2 | `UpdateEntityRecord` (inside TryCatch Try block) | `RecordId` = `createdRecord.Id`; wrapped in `TryCatch` activity |
| 3a | `QueryEntityRecords` (Try block, after Update) | Filter on `Score`; only executes if update succeeded |
| 3b | `DeleteEntityRecord` (Catch block) | `RecordId` = `createdRecord.Id`; inside a `Catch` block; error logged |

**Build condition:** `uip rpa get-errors` exits 0; `TryCatch` activity present with at least one typed `Catch` entry (e.g., `Catch(Of Exception)`); all DataService activities share `x:TypeArguments="local:CodingAgentsEvalEntity"`.

---

## Action Items

1. **Implement as coder_eval YAML task files**: Translate all 71 scenarios into YAML task definitions in `tests/tasks/uipath-rpa/data-service/`. Follow the format in [tests/README.md](https://github.com/UiPath/skills/blob/main/tests/README.md) and [TASK_DEFINITION_GUIDE.md](https://github.com/UiPath/coder_eval/blob/main/docs/TASK_DEFINITION_GUIDE.md).
2. **Investigate brownfield support**: Determine whether coder_eval supports pre-seeded projects (existing `Main.xaml` with non-DataService activities). If supported, add a brownfield Smoke test (S4) where the agent adds DataService activities to an existing workflow.
