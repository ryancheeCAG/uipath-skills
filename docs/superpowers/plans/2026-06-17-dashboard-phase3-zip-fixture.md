# Dashboard Phase 3 — Packaged Starter-Kit Fixture (zip) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline) or superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Package the dashboard scaffold as a single committed, versioned archive (`governance-dashboard-starter-kit.zip`) that the build extracts, replacing the loose-directory `copyDir`. The loose source stays the editable truth; the zip is a generated artifact. Everything works on any coding agent (no Claude-specific tools, no system `unzip`/`tar`).

**Architecture:** A dependency-free pure-Node zip reader/writer (`assets/scripts/lib/zip.mjs`) packs `templates/dashboard/scaffold/` into `assets/fixtures/governance-dashboard-starter-kit.zip` plus a `*.manifest.json` (version + sha256 + file count). `SCAFFOLD_VERSION` is read from the manifest (so versioning has a real source, superseding Phase 2's constant). Fresh build and `runUpgrade` extract the zip instead of copying the loose dir. A drift guard (test) keeps the committed zip in sync with the loose source.

**Tech Stack:** Node ESM (`zlib` only — no npm deps), the existing Phase 1/2 pipeline.

**Spec:** `docs/superpowers/specs/2026-06-15-dashboard-compiler-architecture-design.md` §5 (this is the final phase).

**Branch:** `feat/dashboard-compiler-arch`.

---

## Scope decisions

- **The archive = the scaffold only** (the project skeleton extracted into each dashboard). The widget *templates* (`templates/dashboard/widgets/*.tsx`) are build-time resources the script reads in place via `applyTemplate`; they are not extracted into the project, so they stay loose. Bump the version (re-pack) when **either** the scaffold or the widget templates change.
- **Fixed zip filename** `governance-dashboard-starter-kit.zip`; version + sha256 live in `governance-dashboard-starter-kit.manifest.json`. The build reads the manifest for the version and extracts the fixed-name zip.
- **Binary in git is intentional here** (user-requested). Add `.gitattributes` marking `*.zip binary` so git never applies CRLF normalization (which would corrupt the archive on Windows). This is a deliberate exception to the repo's "no binary files" guidance, scoped to `assets/fixtures/`.
- **Determinism:** the packer uses a fixed timestamp for every entry so the zip bytes (and sha256) are reproducible — the drift guard depends on this.

---

## File Structure

**New:**
- `assets/scripts/lib/zip.mjs` — `crc32`, `zipDir(srcDir) → Buffer`, `unzipTo(buffer, destDir)`. Pure Node, no deps.
- `assets/scripts/pack-scaffold.mjs` — maintainer tool: zip the scaffold → `assets/fixtures/governance-dashboard-starter-kit.zip` + manifest; `--check` mode verifies the committed zip matches the loose source.
- `assets/fixtures/governance-dashboard-starter-kit.zip` — committed archive (binary).
- `assets/fixtures/governance-dashboard-starter-kit.manifest.json` — `{ name, version, sha256, fileCount, builtFrom }`.
- `.gitattributes` (repo root or skill dir) — `*.zip binary`.

**Modified:**
- `build-dashboard.mjs` — `SCAFFOLD_VERSION` reads the manifest; `extractFixture(P)` replaces both `copyDir(SCAFFOLD_DIR, P)` calls (fresh build + `runUpgrade`).
- `references/dashboards/plugins/build/impl.md` (or a primitive) — short note on the packaged fixture + re-pack discipline.
- `tests/resolution.test.mjs` — zip round-trip + drift-guard tests.

---

## Task 1 — Pure-Node zip library + round-trip test

**Files:** Create `assets/scripts/lib/zip.mjs`; Test `assets/scripts/tests/resolution.test.mjs`.

- [ ] **Step 1 — Write `zip.mjs`** with `crc32(buf)`, `zipDir(srcDir)` (recurse files, deflateRaw each, fixed mtime, assemble local headers + central directory + EOCD → Buffer), and `unzipTo(buffer, destDir)` (parse EOCD → central dir → inflateRaw each entry, mkdir parents, write files; skip `/`-terminated dir entries). Compression method 8 (deflate) for files; tolerate method 0 (stored) on read.

- [ ] **Step 2 — Failing round-trip test:**
```js
import { zipDir, unzipTo } from '../lib/zip.mjs'
test('zip round-trip preserves files and bytes', () => {
  const src = mkdtempSync(join(tmpdir(), 'zsrc-'))
  const dst = mkdtempSync(join(tmpdir(), 'zdst-'))
  writeFileSync(join(src, 'a.txt'), 'hello')
  mkdirSync(join(src, 'sub'), { recursive: true })
  writeFileSync(join(src, 'sub', 'b.ts'), 'export const x = 1\n')
  try {
    const buf = zipDir(src)
    unzipTo(buf, dst)
    assert.equal(readFileSync(join(dst, 'a.txt'), 'utf8'), 'hello')
    assert.equal(readFileSync(join(dst, 'sub', 'b.ts'), 'utf8'), 'export const x = 1\n')
  } finally { rmSync(src, { recursive: true, force: true }); rmSync(dst, { recursive: true, force: true }) }
})

test('zipDir is deterministic (stable bytes for same input)', () => {
  const src = mkdtempSync(join(tmpdir(), 'zdet-'))
  writeFileSync(join(src, 'a.txt'), 'hello')
  try { assert.ok(zipDir(src).equals(zipDir(src))) }
  finally { rmSync(src, { recursive: true, force: true }) }
})
```
Add `mkdirSync` to the test's `node:fs` import.

- [ ] **Step 3 — Run, expect fail; implement; run, expect pass.** `node --test skills/uipath-coded-apps/assets/scripts/tests/`

- [ ] **Step 4 — Commit:** `feat(dashboards): dependency-free pure-Node zip library`

---

## Task 2 — `pack-scaffold.mjs`, produce the committed archive, `.gitattributes`

**Files:** Create `pack-scaffold.mjs`, `.gitattributes`; produce `assets/fixtures/*.zip` + `*.manifest.json`.

- [ ] **Step 1 — `.gitattributes`** (skill dir or repo root): `*.zip binary`

- [ ] **Step 2 — `pack-scaffold.mjs`:** zip `templates/dashboard/scaffold/` via `zipDir`; compute `sha256`; write the zip + manifest `{ name: "governance-dashboard-starter-kit", version, sha256, fileCount, builtFrom: "templates/dashboard/scaffold" }`. `--version X.Y.Z` sets the version (default: reuse the existing manifest's version, else `1.0.0`). `--check` re-packs in memory and exits non-zero if sha256 differs from the committed manifest (drift guard for CI).

- [ ] **Step 3 — Run it** to create the committed artifacts: `node skills/uipath-coded-apps/assets/scripts/pack-scaffold.mjs --version 1.0.0`. Confirm the zip + manifest exist and `--check` passes.

- [ ] **Step 4 — Commit:** `feat(dashboards): pack-scaffold tool + committed starter-kit archive + manifest` (includes the binary zip; `.gitattributes` keeps it intact).

---

## Task 3 — Build extracts the archive; version from the manifest

**Files:** Modify `build-dashboard.mjs`.

- [ ] **Step 1 — Source `SCAFFOLD_VERSION` from the manifest.** Replace the Phase 2 constant with a read at module load:
```js
const SCAFFOLD_MANIFEST_PATH = resolve(__dirname, '../fixtures/governance-dashboard-starter-kit.manifest.json')
const FIXTURE_ZIP_PATH = resolve(__dirname, '../fixtures/governance-dashboard-starter-kit.zip')
function readScaffoldVersion() {
  try { return JSON.parse(readFileSync(SCAFFOLD_MANIFEST_PATH, 'utf8')).version ?? '1.0.0' } catch { return '1.0.0' }
}
export const SCAFFOLD_VERSION = readScaffoldVersion()
```
(Keeps the `SCAFFOLD_VERSION` export so Phase 2 tests/imports stay valid.)

- [ ] **Step 2 — `extractFixture(P)`:**
```js
function extractFixture(projectPath) {
  if (!existsSync(FIXTURE_ZIP_PATH)) fail(`Starter-kit archive not found at ${FIXTURE_ZIP_PATH} — run pack-scaffold.mjs`)
  unzipTo(readFileSync(FIXTURE_ZIP_PATH), projectPath)
}
```
Import `unzipTo` from `./lib/zip.mjs` at the top.

- [ ] **Step 3 — Replace both `copyDir(SCAFFOLD_DIR, P)` calls** (fresh build Step 1, and `runUpgrade`) with `extractFixture(P)`. Keep the `rmSync(node_modules)` line after it. `SCAFFOLD_DIR` / `copyDir` may remain for the packer’s use but are no longer the build's source.

- [ ] **Step 4 — Parse check + full suite** (no unit regressions; build is exercised in Task 5). Commit: `feat(dashboards): build extracts the packaged starter-kit archive`

---

## Task 4 — Drift-guard test + docs

**Files:** Modify `tests/resolution.test.mjs`, a reference doc.

- [ ] **Step 1 — Drift-guard test:** re-pack the loose scaffold in memory and assert its sha256 equals the committed manifest's `sha256` (fails loudly if someone edits the scaffold without re-packing):
```js
test('committed starter-kit archive matches the loose scaffold (re-pack to refresh)', () => {
  const scaffoldDir = resolve(__dirname, '../../templates/dashboard/scaffold')
  const manifest = JSON.parse(readFileSync(resolve(__dirname, '../../fixtures/governance-dashboard-starter-kit.manifest.json'), 'utf8'))
  const sha = createHash('sha256').update(zipDir(scaffoldDir)).digest('hex')
  assert.equal(sha, manifest.sha256, 'Scaffold changed but archive not re-packed — run pack-scaffold.mjs')
})
```
Add `createHash` from `node:crypto` to the test imports.

- [ ] **Step 2 — Docs:** short note (impl.md or a primitive) — the build extracts a versioned starter-kit archive; the loose `scaffold/` is the editable source; after editing it, **re-pack** (`pack-scaffold.mjs`) and commit the refreshed zip + manifest; CI runs `pack-scaffold.mjs --check`. Keep wording tool-neutral.

- [ ] **Step 3 — Commit:** `test+docs(dashboards): starter-kit drift guard + packaging notes`

---

## Task 5 — Self-test (no regression)

- [ ] **Step 1 — Full unit suite** green.
- [ ] **Step 2 — Fresh build** from a fixture intent → confirm it extracts the archive and still reaches `METRICS_PASS → TSC_PASS → BUILD_RESULT` (the dashboard compiles exactly as before — no regression).
- [ ] **Step 3 — Upgrade** (bump version via `pack-scaffold --version`, run an `UPGRADE` op) → confirm `UPGRADE_DONE`, app still compiles, version re-stamped. Revert the version bump after.
- [ ] **Step 4 — Clean up** the temp project.

---

## Self-Review (plan author)
- §5 coverage: loose-source-of-truth + generated zip (Tasks 1-2), build extracts (Task 3), manifest version + checksum (Tasks 2-4), dependency-free cross-platform extraction (Task 1). 
- Platform-neutral: only `node:zlib`/`node:crypto`; no system tools; build path is `node build-dashboard.mjs`.
- No placeholders; types consistent (`zipDir → Buffer`, `unzipTo(buffer, dir)`, manifest `{name,version,sha256,fileCount,builtFrom}` used identically across tasks).
- Risk: binary in git → mitigated by `.gitattributes *.zip binary` + deterministic packer + drift-guard test.
