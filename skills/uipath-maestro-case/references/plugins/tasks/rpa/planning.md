# rpa task — Planning

An RPA robot task. The sdd.md component type is `RPA`. The task node's `type` field is `"rpa"`, but the cached registry entity typically lives in `process-index.json` — the registry does not separate "process" from "rpa" at storage time.

## When to Use

Pick this plugin when the sdd.md explicitly labels a task as `RPA` (e.g., "RPA robot does X"). The distinction from `process` is **semantic** (sdd.md intent) rather than structural (registry representation).

If sdd.md is ambiguous between `PROCESS` and `RPA`, default to `process` unless the sdd.md mentions UI automation, desktop apps, or robot-specific concerns.

## Required Fields from sdd.md

Same shape as [process/planning.md](../process/planning.md):

| Field | Notes |
|-------|-------|
| `display-name` | from Process Reference |
| `name` | from Process Reference |
| `folder-path` | Resolved registry `folders[0].fullyQualifiedName` — NOT the sdd.md "Folder" (which may be a parent path). Binds to `data.folderPath`; Orchestrator starts the job here at runtime. See [§ Registry Resolution](#registry-resolution). For an RPA process **built inline** as an in-solution sibling, the runtime `folder-path` is **empty `""`** (co-located) while `resourceKey` stays `solution_folder.<name>`; do NOT put the `solution_folder` sentinel in `folder-path` (runtime `folder not exist`). See [§ Creating an RPA process inline](#creating-an-rpa-process-inline). |
| `task-type-id` | from registry (`entityKey` in `process-index.json`) |
| `inputs`, `outputs`, `runOnlyOnce`, `isRequired` | see [bindings-and-expressions.md](../../../bindings-and-expressions.md) |

## Registry Resolution

1. **Primary cache file:** `process-index.json` (yes — RPA tasks share this cache with `process`).
2. **Identifier field:** `entityKey`.
3. Use the sdd.md `RPA` label to set `type: "rpa"` on the task node; the cache `entityKey` is recorded in `registry-resolved.json` (not written to the node — the task references the resource via `data.name` / `data.folderPath` = `=bindings.<id>`).
4. If no match in `process-index.json`, search all other cache files as a fallback.
5. **`folder-path` = the SELECTED entry's `folders[0].fullyQualifiedName`** (not the sdd.md "Folder" — see the field table above). Fall back to the sdd.md folder only when there is no registry match (Unresolved path).
6. Discover inputs/outputs via `tasks describe` — see [bindings-and-expressions.md § Discovering output names](../../../bindings-and-expressions.md).

### No tenant-index match → check in-solution siblings BEFORE the gate

When steps 1–4 find nothing in the tenant index **and** the CLI supports `registry --local`, check for an existing in-solution sibling before treating the task as unresolved:

```bash
uip maestro case registry search "<name>" --type process --local --output json
```

> **Registry token is `process`, not `rpa`.** The local registry has no `rpa` type — an RPA sibling registers and rediscovers as `--type process` (`Resource.Category == "process"`). `rpa` exists only as the task-node `type` / `tasks describe` token.

An exact-name match with `Resource.Source == "local"` means the process **already exists as an in-solution sibling** — built by a prior run, built by the user, or built earlier in this run. **Resolve it directly; do NOT enter the [Rule 17 Create gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback):** bind by name+folder with the `solution_folder` sentinel (`resourceKey="solution_folder.<name>"`), reading I/O from the sibling's on-disk `project.json` `entryPoints` (per [§ Creating an RPA process inline](#creating-an-rpa-process-inline)). Only when **both** the tenant index and the local siblings lack the process does it reach the gate / Create. This makes planning **idempotent** — a re-run (or a pre-existing sibling) resolves here instead of triggering a duplicate build.

## Unresolved Fallback

> **Build it inline first (rpa).** At the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) the user may pick **Create** to build the missing RPA process as an in-solution sibling — see [§ Creating an RPA process inline](#creating-an-rpa-process-inline). This fallback applies only when the user declines/skips Create, the build fails, or the CLI lacks `registry --local`.

Mark `<UNRESOLVED: rpa "<name>" in folder "<folder>" not found in registry>`. Omit `inputs:` and `outputs:`; capture intended wiring in a fenced ```` ```text ```` code block (not `#` prefixed — it renders as markdown H1). Execution creates a placeholder task — see [placeholder-tasks.md](../../../placeholder-tasks.md).

## Creating an RPA process inline

When an RPA process is unresolved at the [Rule 17 empty-lookup gate](../../../registry-discovery.md#must-confirm-before-placeholder-fallback) and the user selects it for **Create**, the skill builds it as an **in-solution sibling**. The cross-cutting orchestration (capability probe, multi-select, parallel build, sequential register, rediscover/verify/bind) lives in [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). This section covers the **RPA-specific** parts: what contract to compute and what brief to hand the builder.

**The skill does not run `uip rpa init` itself.** It spawns a sub-agent that invokes the `uipath-rpa` skill — RPA-build knowledge lives there. Cross-skill invocation is allowed for this path (overrides the `SKILL.md` "never auto-invoke other skills" anti-pattern). The build is a **deterministic scaffold** (no LLM-authored workflow logic): the sibling ships with the pinned argument contract and default-value output assignments; the user implements the real workflow logic in Studio afterward (name it in the completion report). **Only processes the user selected at the gate are built — never from SDD content alone.**

### Step 1 — Compute the pinned I/O contract

Same rule as the agent leg — declare to the builder **only the fields the case wires**:

- **Wired to a typed Case Variable** → **required, type pinned** from the variable's `Type` (SDD Case Variables table).
- **Wired but type not knowable at planning** (cross-task ref, literal, `=metadata.*`) → **required, name only**; the builder picks the type.
- **Unwired** → **omit from the contract**.

Pass the case vocabulary through; mapping it onto .NET argument types is `uipath-rpa`'s concern at build. Reconcile back at verify (§ Step 4) via:

| Case vocab | .NET FQN |
|---|---|
| string | `System.String` |
| integer | `System.Int32` |
| float | `System.Single` |
| double | `System.Double` |
| boolean | `System.Boolean` |
| date / datetime | `System.DateTime` |
| jsonSchema | `System.Collections.Generic.Dictionary<System.String,System.Object>` |
| file | *(no .NET mapping — pass name-only; builder picks; reconcile at verify)* |

Map is proposed-canonical: at verify, treat a differing-but-compatible .NET type in the built `project.json` as authoritative (warn, don't block).

### Step 1b — Build kind

**None.** RPA processes have no kind choice — v1 always scaffolds XAML/VisualBasic (`uip rpa init` defaults). Skip the [registry-discovery.md § 1b](../../../registry-discovery.md#create-on-missing-build-and-rediscovery) kind prompt for `rpa` (it applies to agents only).

### Step 2 — Hand the builder a self-contained brief

```
Build a UiPath RPA process by following the uipath-rpa skill. Non-interactive:
do not ask for approval; do not publish/upload/deploy.
  Solution dir:     <abs path to the solution>
  Process name:     <ProcessName>
  Required inputs:  <Step-1 pinned inputs: [{name, type?}, ...]>   (case vocabulary; map to .NET arguments — honor type when given)
  Required outputs: <Step-1 pinned outputs: [{name, type?}, ...]>
  Scaffold: uip rpa init --name "<ProcessName>" --location "<solution dir>"
    --target-framework Portable --expression-language VisualBasic
    --skip-solution-registration --output json
  (init auto-registers inside a solution dir — the flag opts out; Status:"OptedOut" is
   expected, not an error. Do NOT register — the caller registers via `uip solution project add`.)
  A fresh scaffold has NO I/O contract (project.json entryPoints: null) and an empty
  Main.xaml <Sequence/>. You MUST then:
    1. Declare each pinned input/output as a Main.xaml x:Property
       (InArgument/OutArgument, .NET type).
    2. Mirror them into project.json entryPoints[] — {filePath:"Main.xaml",
       uniqueId:<mint a UUID>, input:[{name,type,required}], output:[{name,type}]},
       .NET FQN types. No CLI keeps XAML args and entryPoints in sync — you do, by hand.
    3. Assign every output a typed default value in the workflow body (an empty Sequence
       returns null outputs at runtime); the user implements real logic later.
  `uip rpa` needs the @uipath/rpa-tool plugin and a reachable .NET 8 runtime (no Robot
  installed → set DOTNET_ROOT, e.g. DOTNET_ROOT=~/.dotnet). If init errors for either
  reason, or you cannot locate/load the uipath-rpa skill, do NOT improvise a build —
  return { built:false, error:"<why>" }.
Return JSON: { built: bool, path, finalInputs:[{name,type}], finalOutputs:[{name,type}], error? }
```

The brief is self-contained — no other case context (do not dump `caseplan.json` or sibling tasks). Building runs in a sub-agent; orchestration/parallelism per [registry-discovery.md § Create-on-Missing](../../../registry-discovery.md#create-on-missing-build-and-rediscovery). The **caller registers** the built sibling (`uip solution project add`, then `resources refresh`) before rediscovery. `--target-framework Portable` is deliberate: a Portable sibling runs serverless (no Robot) and is e2e-verified through deploy+invocation; the user can retarget Windows in Studio if the real logic needs UI automation.

### Step 3 — Binding (drops `resourceSubType`)

After the sibling is built, registered, and verified, bind the task by name+folder: two bindings `resource:"process"`, **NO `resourceSubType` key** (omit entirely — not `""`, not null; contrast agent `"Agent"`), shared `resourceKey="solution_folder.<ProcessName>"`; `name` default `<ProcessName>`, **`folderPath` default `""` (empty string — the `solution_folder` sentinel belongs ONLY in `resourceKey`; a literal `solution_folder` folderPath passes `validate` but fails invocation with `folder not exist`)**. Node `type` stays `"rpa"`. In `bindings_v2.json`, omit `metadata.subType`. The result is byte-identical to a tenant-resolved RPA binding except `folderPath:""` + the sentinel `resourceKey`.

> **Provisioning ≠ debug (runtime-verified).** The sibling ships inside the solution `.uipx` and is provisioned as a runnable Orchestrator process by a full **`uip solution deploy run`** — invocation then succeeds end-to-end (StartJob finds the process; outputs round-trip into case vars; runtime argument-name matching is case-insensitive, so camelCase XAML args match the engine's PascalCase `JobArguments` — do NOT "fix" casing at verify). **`uip maestro case debug` does NOT provision non-agent siblings**: an inline RPA task in debug fails with incident `170007` "The job's associated process could not be found". That is a debug-path limitation, not a binding error — verify invocation via a full deploy, and warn the user when they debug a case with an inline RPA sibling.

### Step 4 — Read-back and verify

Rediscover with `uip maestro case registry search "<ProcessName>" --type process --local --output json` (§ sibling check above — token is `process`). RPA siblings have **no `entry-points.json`**: read the case-preserving argument names + .NET types from the sibling's on-disk **`project.json` `entryPoints[].input/output`** (never from the PascalCased `--local` `Resource.{Inputs,Outputs}`), reconcile against the pinned contract via the Step-1 map → matched / missing-in-sibling / extra-in-sibling. Warn+diff into the completion report; never block. The `--local` `EntityKey` is audit-only — the node binds by name+folder.

### Failure — surface and re-prompt, never stall

Same contract as the agent leg: on `built:false` (or a dead sub-agent), show the `error` verbatim, then AskUserQuestion `Retry create` / `Skip (defer)`. On Skip or repeated failure → Unresolved Fallback above (placeholder + completion-report note) — never halt. Verify-time I/O mismatch = **warning** (rewire matched fields, report the rest). **"Already exists" is NOT a failure:** *"directory exists"* from `init` or *"Project name already exists"* from `project add` means an interrupted prior run built it but never registered it — register it (`uip solution project add`), then rediscover + bind. It's already built.

## tasks.md Entry Format

```markdown
## T<n>: Add rpa task "<display-name>" to "<stage>"
- taskTypeId: <entityKey>
- folder-path: "<folder>"
- inputs:
  - <input_name> = "<value>"
- outputs: <out1>
- runOnlyOnce: true
- isRequired: true
- order: after T<m>
- lane: <n>  # FE layout; increment per task. Within `runs-sequentially` group, parallel members share a lane (semantic).
- verify: Confirm Result: Success, capture TaskId
```
