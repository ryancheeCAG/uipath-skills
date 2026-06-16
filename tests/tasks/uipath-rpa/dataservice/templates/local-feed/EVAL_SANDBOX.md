# DS eval sandbox — read this before starting

This file is mounted at the project root by every v2 DataService task. It tells
you how to bootstrap the project against the local NuGet feed and how to
install the two evaluation entities without a live tenant.

## Local NuGet feed (already in place)

- `./NuGet.Config` declares `./local-feed/` as a NuGet source.
- `./local-feed/` hosts `UiPath.DataService.Activities` version `23.1.4-dev`.

This version is **not** available on any public feed. After `uip rpa init`, pin
this exact version in `project.json`:

```
"UiPath.DataService.Activities": "23.1.4-dev"
```

## Entities (pre-resolvable on the tenant)

Both `CodingAgentsEvalEntity` and `CodingAgentsEvalFileEntity` are defined on
the connected Data Service tenant. Install **both** (plus `SystemUser`) into
the project.

The canonical CLI verb is `uip rpa data-fabric-entities install` (see the
DataService skill docs). In this eval sandbox the dev `rpa-tool` source is run
directly via `bun` — it accepts the same arguments:

```
bun C:\Users\suphalathlur\Studio\RpaTool\rpa-tool\src\index.ts install-data-fabric-entities --add SystemUser,CodingAgentsEvalEntity,CodingAgentsEvalFileEntity --project-dir "<PROJECT_DIR>" --verbose --format json
```

The compiled `DataService.<ProjectName>.dll` lands under
`.local/.entities/<hash>/` after install.

## Standard agent steps

1. `uip rpa init` with the project name the task gives you.
2. Pin `UiPath.DataService.Activities@23.1.4-dev` in `project.json`.
3. Run the `bun ... install-data-fabric-entities ...` command above.
4. Author `Main.xaml`.
5. `uip rpa validate --output json` in the project directory — must report
   zero errors before you consider the task complete.

All other `uip rpa` verbs work exactly as documented in the skill.
