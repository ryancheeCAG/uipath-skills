# Releasing the skills package

The whole skills repo is published as an npm package, **`@uipath/skills`**, versioned in lockstep with **`@uipath/cli`** so a given CLI release always resolves to a compatible skills package.

## Version model

`package.json` `version` is the **single source of truth** for the npm package. `scripts/sync-version.mjs` derives these manifests from it (do not edit by hand):

| File | Field | Purpose |
|------|-------|---------|
| `version-manifest.json` | `skillsVersion`, `targetCli` | CLI↔skills pairing record |
| `.claude-plugin/plugin.json` | `version` | Claude Code plugin version (shared `major.minor`, independent patch) — the canonical plugin version |
| `.claude-plugin/marketplace.json` | `plugins[0].version` | Always equals `plugin.json` `version` |
| `.codex-plugin/plugin.json` | `version` | Codex plugin version — always equals `plugin.json` `version` |

### One `major.minor`, three patch counters

All channels share `major.minor` (the CLI-compatibility signal); the **patch diverges deliberately per channel**:

| Channel | Version | Patch cadence |
|---------|---------|---------------|
| npm `latest` | `M.N.<release>` | per stable release — what the CLI pins |
| npm `alpha` | `M.N.<release>-alpha.<date>.<run>` | per alpha dispatch |
| plugin manifests (`.claude-plugin/plugin.json`, `marketplace.json`, `.codex-plugin/plugin.json`) | `M.N.<daily-counter>` | daily (`daily-version-bump.yml`) — drives Claude Code / Codex plugin auto-update |

`sync-version.mjs` enforces the shared line: if the plugin `major.minor` differs from `package.json`, it resets the plugin version to `M.N.0` (and **refuses to downgrade** if `package.json`'s minor is below the plugin's); if they match, `--bump-patch` advances the daily counter, otherwise the patch is left untouched. The marketplace and Codex versions must always equal the plugin version exactly. `--check` fails on any violation, so a hand-bumped plugin manifest cannot drift the line. The bump rule lives only in `sync-version.mjs` (`daily-version-bump.yml` calls `--bump-patch` rather than reimplementing it).

Run after any version change:

```bash
npm run version:sync      # rewrite derived manifests from package.json
npm run version:check     # CI guard — non-zero exit if drifted
```

### Why lockstep with the CLI

The version line mirrors the CLI's `MAJOR.MINOR` (e.g. CLI `1.197.x` → skills `1.197.x`). `version-manifest.json.targetCli` records the matching line as `^MAJOR.MINOR.0`. The CLI pins this line, so it never pulls a skills package from a different minor.

> **The CLI resolves `@uipath/skills` from npm, matched to its own minor line.** `uip skills install` lists the published versions and picks the one matching the CLI's `MAJOR.MINOR` (`packages/cli/src/commands/skills/contentStore.ts` → `fetchMatchingSkillsPackageInfo` / `pickMatchingSkillsVersion`, registry `registry.npmjs.org`), then fetches that tarball into the content store. So a given CLI release always resolves a compatible skills package and the loop this section describes is closed — for the `uip skills install` **content** path. The Claude Code / Codex plugin marketplace is a **separate** channel (a git ref, not the npm package) and is what the daily plugin-version bump serves.

## Publishing tracks (`.github/workflows/publish.yml`)

| Trigger | Registry | dist-tag | Version |
|---------|----------|----------|---------|
| `workflow_dispatch` (target: `github-alpha`) | GitHub Packages | `alpha` | `<base>-alpha.<YYYYMMDD>.<run_number>` |
| GitHub Release published | npmjs | `latest` | `package.json` version |
| `workflow_dispatch` (target: `npmjs`) | npmjs | `latest` | `package.json` version |

Both tracks are **manually triggered** — there is no auto-publish on push to `main`. Alpha is dispatched on demand; stable runs when a GitHub Release is published. `npm install @uipath/skills` (no tag) always resolves to the last stable npmjs release — alphas live only under the `alpha` tag on GitHub Packages.

### Registry routing

`@uipath/skills` is a **scoped** package, so the publish target is set via the **scoped registry** (`@uipath:registry=<url>`) — not a `--registry` flag (which only sets the *unscoped* default and is ignored for scoped packages). There is **no committed `.npmrc` and no `publishConfig.registry`**: a static scoped-registry line would override the per-job target (and break `npm install` for anyone cloning this public repo).

| Job | registry | Auth |
|-----|----------|------|
| `publish-alpha` | GitHub Packages (`npm.pkg.github.com`) | built-in `GITHUB_TOKEN` |
| `publish-release` | npmjs (`registry.npmjs.org`) | **OIDC trusted publishing** (no token) + signed `--provenance` |

## Cutting a stable release

1. Bump `package.json` to the target version (match the CLI minor line), run `npm run version:sync`, merge.
2. Create a GitHub Release tagged `v<version>` → `publish.yml` publishes to npmjs.

### Automated sprint cut (`sprint-release-cut.yml`)

`sprint-release-cut.yml` runs **Sunday 06:00 UTC**, gated to the **14-day cadence** anchored at `2026-06-14`. The **release line is the version `main` is currently on** (no `+1` — `main` on `1.197.0` cuts `release/v1.197`). On a release Sunday it:

1. **cuts `release/v<current>` from `main`** — a frozen snapshot of `main` at its current `M.N.0` (e.g. `release/v1.197` at `1.197.0`). No extra commit; the branch is just `main`'s pointer;
2. **bumps `main` forward to the next minor** (`1.197.0 → 1.198.0`) via `npm version` + `sync-version.mjs`, **pushed directly to `main`**;
3. **publishes an alpha of the new `main` line to GitHub Packages only** — dispatches `publish.yml target=github-alpha`, which stamps `<base>-alpha.<YYYYMMDD>.<run>` from `main`'s now-`1.198.0` `package.json` and publishes to `npm.pkg.github.com` under the `alpha` dist-tag.

**It never publishes to npmjs.** The stable npmjs release is always **manual** (see *Cutting a stable release* above): create a GitHub Release on the `release/v<minor>` branch, or dispatch `publish.yml target=npmjs --ref release/v<minor>`.

Off-cadence or ad-hoc cut: dispatch manually with `release_override` (e.g. `1.197`) to set the release line and skip the cadence gate, or `dry_run` to print the plan without pushing.

> **Required repo setup (both are hard prerequisites):**
> - Branch protection must allow the Actions identity (`github-actions[bot]` via `GITHUB_TOKEN`) to **push `main` directly** and to push `release/v*` — otherwise the bump push and the cut 403. (Configure a branch-protection/ruleset bypass for the Actions app, or switch the bump to a PAT/GitHub App token.)
> - `actions: write` permission on this workflow (already set) so it can dispatch `publish.yml`.

> **Recovery if a run fails *after* the main bump.** Because the bump pushes straight to `main`, once `main` has advanced a re-run of the whole cut would target the *new* line. So if a run bumps `main` but the alpha dispatch fails, **don't re-run the cut** — re-dispatch just the publisher: `gh workflow run publish.yml --ref main -f target=github-alpha`. (The 14-day cadence gate prevents an accidental scheduled re-run in the meantime.)

## Required setup

- [x] **npmjs Trusted Publishing** — configure a GitHub Actions trusted publisher on the `@uipath/skills` package (npmjs → package → Settings → Trusted Publisher): repository `UiPath/skills`, workflow `publish.yml`. No `NPM_TOKEN` secret is used — the `publish-release` job authenticates via OIDC (`id-token: write`). Do **not** set `NODE_AUTH_TOKEN`; a token makes npm bypass OIDC and (with 2FA) fail `EOTP`.
- [x] Package name/scope confirmed: **`@uipath/skills`** (published).
- [x] Seed version confirmed: **`1.197.0`** (current CLI minor line). The ongoing CLI↔skills lockstep is automated by `sprint-release-cut.yml` (Sunday 06:00 UTC, 6 h before the CLI's own cut, on the same 14-day cadence anchored at `2026-06-14`).

> The alpha track also needs no secret — `publish-alpha` uses the built-in `GITHUB_TOKEN` with `packages: write`.
