# Product Adoption Audit — Findings & Backlog

Audit of FNSTools product design, adoption, installation, updates, and
config/tool scoping. Conducted 2026-08-20 on branch `audit/product-adoption`
against the live project (`FunctionStore_tools_2025_DEV`, live root
`/FNSTools`) and the packaging/docs tree. This document is the actionable
backlog for a follow-up agent; each item carries its evidence anchors.

**Already resolved (do not redo):** the registry ordering/visibility
persistence defects found during this audit were spec'd, landed, and
verified live on 2026-08-21 — see `docs/ConfiguratorPersistenceFixes.md`.
The first landing (`33b955d`) was silently reverted by stale externaltox
reloads on TD restart; commit `61748d9` re-landed all edits, re-exported
every carrying tox (incl. the NESTED `ToolbarConfigurator.tox` inside
`FNS_Toolbar`), and passed a cold-boot check. Re-verified live 2026-08-21:
`SnapshotState`, `PushSequence` anchor refresh, and the callback swap are
present in all three surfaces. Only the §5.3 uninstall/reinstall
dormant-group manual pass remains.

## 1. Verified-healthy baseline (context, no action)

- 46 packages: 7 core (FNS_ConfigRegistry, FNS_MainMenuRegistry,
  FNS_NavbarRegistry, FNS_OpMenuRegistry, FNS_PaneTypeRegistry,
  FNS_ToolbarRegistry, FNS_Updater) + 39 tools. Stable v3.0.1, live bucket
  `https://storage.functionstr.com/fnstools`.
- Update decisions are governed by the `Pkgversion` custom par (read live
  off the installed COMP); sha256 verifies downloads only. `.tox` export is
  not byte-reproducible, so hash-based update detection was tried and
  reversed — do not reintroduce it.
- Three working install rails: one-drop `FNSTools.tox` bootstrap
  ("castrated root"), `FNS_Installer.tox`, and the Textport paste rail.
- Updater `Compare()` states: `update` / `current` / `unversioned` /
  `locked` / `missing`. The `locked` guard refuses to touch Embody-authored
  dev checkouts (discriminator: root `externaltox` set = dev master).
- Dependencies are DERIVED from registry hosting, never declared
  (`packaging/build_manifest.py`); `packaging/catalog.json` is the only
  hand-written data (category + description).
- Config scope: one machine-global JSON at
  `<palette>/FNStools_ext/config/FNStools_config.json` (schema 1, atomic
  write, last-writer-wins). Per-tool `pars` (host Registration pars are bind
  masters) + `state` via `config_callbacks`. Applies ~30 frames after
  registration; config beats `.toe` values. Verified live: 48 tools
  registered, bar layouts roam via `configurator_state` tables.
- §1.1 of `docs/ConfiguratorDistribution.md`: zero core→tool dependency
  edges remain.

## 2. Backlog (priority order)

### P1 — README rewrite (adoption-critical)

`README.md` (repo root) describes the **2023 monolith**: old install flow,
GitHub-release badges, "requires TD 2023.11880", no link to the website or
the bucket-based installer. It is the first thing every prospective user
sees and it contradicts the actual v3 product. The website content itself is
correct — the README just predates the redesign.

**Action:** execute `docs/ReadmeRewritePlan.md` (decisions locked
2026-08-21: README defers to website + bucket; one release badge for the
`FNSTools.tox` bootstrapper; no wiki links — wiki is being retired).

### P2 — OpTemplates not self-contained (the one real install defect)

A fresh install of `OpTemplates` gets an **empty template library**: its
`OPTemplates1` child is an external tox living in the user palette, and the
portable export does not materialize it.

Evidence:
- `packaging/build_manifest.py:335` — comment: "OPTemplates artifact still
  expects OPTemplates1.tox to exist in [palette]".
- `packaging/build_manifest.py:501` — `entry['portability'] = warn` is
  **write-only**: no consumer (installer or configurator) reads it or
  materializes palette files.

**Action (pick one):** (a) inline `OPTemplates1` into the shipped artifact
at build time, or (b) teach `InstallerExt.py` to consume `portability` and
fetch/place the palette file. (a) is simpler if the tox is not huge; verify
against the general finding that nested `externaltox` survives the portable
export (root-only clearing) — this class of defect could recur for other
tools, so a build-time scan for surviving nested `externaltox` would catch
future instances.

### P3 — Updater self-update never live-verified

`FNS_Updater` is `kind: core` and self-update is implemented, but it has
**never been exercised against the live bucket**. The riskiest untested
path in the product (the updater replacing itself mid-run).

**Action:** execute `docs/UpdaterSelfUpdateVerification.md` (scratch-toe
harness, localhost store, self-update-ordered-last check, downloader
traps).

### P4 — First-run nudge (adoption)

After a successful install nothing points the user at the configurator or
the toolbar. **Action:** execute `docs/FirstRunNudgePlan.md` (dialog form
approved 2026-08-21; machine-global seen-flag; boot-window trigger; root
ext home).

### P5 — Scope & Persistence doc

The scope model is coherent but **undocumented**, and it has sharp edges a
user will hit:
- The config JSON is machine-global; `state` restore is whole-table REPLACE
  → last-writer-wins per surface **across projects** (by design — see
  `docs/ConfiguratorPersistenceFixes.md` §0.D).
- `FNS_persist` tag: SaveAll sweep must precede snapshot; foreign-project
  sections can be adopted by a freshly tagged COMP.
- Schema-mismatch sections are silently discarded on load.
- Project-local exceptions: QuickMarks, oscMapper stay project-local.

**Action:** write `docs/ScopeAndPersistence.md` covering: what roams
(machine-global) vs. what stays in the `.toe`, per-tool `pars` vs. `state`
rails, the REPLACE semantics, `FNS_persist`, and the exceptions list.

### P6 — Native installer decision

**DECIDED 2026-08-21: defer** (Option B). **Action:** execute the doc
edits in `docs/NativeInstallerDecision.md` — strike the `.exe`/`.dmg`
promise from `ConfiguratorDistribution.md` + website, pip-rail stale-spot
cleanup, tombstone on `UvPackagingResearch.md`.

### P7 — Minor items

- `packaging/catalog.json` descriptions were seeded by inspection; need an
  owner pass for accuracy/voice.
- Remove or mark the dead pip rail references in
  `docs/ConfiguratorDistribution.md`.

## 3. Corrections on record (do not re-report these)

Two claims from an earlier exploration sub-agent were **hallucinations**,
disproved by direct verification — a future agent should not resurrect
them:

1. "No settings server exists" — FALSE. It exists at
   `FNSTools/FNS_ConfigRegistry/settings_server_callbacks.py` (GET `/`,
   GET `/api/state`, POST `/api/set`).
2. "OpTemplates self-containment is fixed/intentional" — FALSE. Still open
   (see P2 evidence).

## 4. Traps for the acting agent

- **Three sibling-copy ConfiguratorExts** (Toolbar/Navbar/MainMenu) — not
  subclasses; any configurator change lands three times. Navbar/MainMenu
  carry `side` columns + `_decorateRestoredMarker`.
- **NO RECURRING SCANS** — hard user constraint. Nothing discovery-shaped
  on a timer; boot window and SaveAll only. Live-show toolkit.
- **Install tests MUST use a cooking-disabled container**
  (`allowCooking = False` before load) — a live registry-master copy
  promotes itself to `/sys` and destroys the running one. `/sys/quiet` is
  the staging home.
- `pi_suspect` survives into shipped artifacts; `externaltox` on the root
  is the dev/installed discriminator. Never replace a package COMP whose
  `externaltox` is set.
- Live root is `/FNSTools` (not `/FunctionStore_tools_2025`). Multiple AI
  sessions are typically active — check `get_sessions`, claim scopes before
  editing shared files.
