# Configurator Distribution — Design Notes

How a user picks and chooses which FunctionStore tools to install, instead
of taking the whole toolkit. Companion to
[RegistryScheme.md](RegistryScheme.md), which owns the **in-project
runtime** relationship between tools and registries.

**Distribution model (decided 2026-08-13): buckets and manifests.** A
bucket holds `manifest.json` and the per-release artifacts; native
`.exe`/`.dmg` installers are the bootstrap. Everything downstream —
picking, installing, updating — is manifest-driven. Update decisions are
made on a **version parameter we govern** (`Pkgversion`), read live off
the installed component; artifact hashes verify downloads only. See §4.2.

[UvPackagingResearch.md](UvPackagingResearch.md) remains as research
only: the pip/uv rail it explores is **not** the plan (§3).

Started as design notes 2026-08-10; §1.1–1.3 and §4.1 record what has
since been built and verified.

## 1. Why this is feasible now

The redesign25 registry architecture already did the hard part. Tools are
self-contained COMPs carrying **stamped registry contribution DATs**
(Toolbar/Navbar/OpMenu/MainMenu/PaneType registries, HotkeyManager
entries). Registries discover contributions; a missing tool just means
missing entries. That is exactly the property "install any subset"
requires. The pre-redesign monolith could not do partial installs — the
registry scheme is the enabler, and this document is downstream of it.

Remaining coupling to audit before any of this works: `/sys` globals,
`RegistryBase.py`, the registry hosts themselves, `tools_ui`, and any
`op.X` global-shortcut references *between tools*.

### 1.1 Dependency audit — RESULTS (2026-08-13)

Swept all 59 depth-1 tool COMPs: every descendant DAT's text plus every
custom/expression parameter, for `op.<SHORTCUT>` references resolving to a
DIFFERENT tool. Stamped registry hosts (`*/ToolbarRegistry/*`,
`*/ConfigRegistry/*`, …) were excluded — those reference core by design and
are what the clone rail updates.

**Verdict: the "tools depend only on core" rule is already ~true.** Fourteen
cross-tool edges across 59 tools — **35 live reference lines** — plus three
dead ones. Nothing here is deep logic entanglement; it is almost entirely *a
widget living in the wrong package*. No blocker to the core/tool split.

| Source → Target | Lines | Site(s) | Shape |
|---|---|---|---|
| CustomParPromoter → QuickExt, QuickParent, ClearPars, QuickCollapse, iopPromoter | 7 | `button_custompar_tools/panelexec_lcick`, `panelexec_mclick`, `dragdrop` | **hub button** — one widget dispatching to 5 optional tools |
| **FNS_Navbar** (core) → CustomParPromoter, iopPromoter | 8 | `containers/hijack_dragdrop/dragdrop` | core → optional (backwards) |
| **FNS_Toolbar** (core) → midiMapper | 7 | `widgets/button_midi_learn/dragdrop`, `panelexec2`, `panelexec3`, `panelexec4` | core → optional (backwards) |
| **tools_ui** (core) → GlobalOutSelect | 1 | `valueParExec` | core → optional (backwards) |
| OpTemplates → AutoRes | 8 | `OPTemplates1/{noiseTOP/noise1, noiseTOP/noise2_highp, circleTOP/circle1, displaceTOP/base1/noise1}` `.resolutionw/h` | par expressions inside template assets |
| ExprHotStrings → CustomParPromoter | 1 | `extExprHotString` | real logic dep |
| MY_HOTKEYS → ResetPLS1 | 1 | `keyboardin14_callbacks` | the only guarded one |
| SearchWords → FNS_OpMenu | 1 | `.opviewer` (expr) | target is core — fine |
| openOp1 → ColorUI | 1 | `.Op` (expr) | helper COMP, not a packaged tool |

**Two findings that shape the work:**

1. **34 of the 35 lines are unguarded** — bare
   `op.FNS_QUICKEXT.CreateExtension(...)`, `op.FNS_CPP.Reference = ...`. With
   the target uninstalled these raise `AttributeError` inside a panel/drag
   callback: a partial install fails at click time, not at load time. The one
   exception is `MY_HOTKEYS/keyboardin14_callbacks`, and it is a bare
   `try: … except: pass` — it survives a missing tool but swallows every
   other error too, so it is a pattern to replace, not to copy.

   **Watch the OpTemplates block — it only looks guarded.**
   `tdu.tryExcept(lambda: parent.Project.width, op.AUTO_RES.par.Resolutionw)`
   protects the *first* argument, but the fallback is an ordinary argument
   evaluated eagerly, so a missing `op.AUTO_RES` raises before `tryExcept`
   ever runs. Eight parameter expressions, and being parameters they would
   error on every cook rather than only on interaction — the most visible
   failure of the set, and the least obvious in a code read.
2. **Three edges point the wrong way** — core surfaces (Toolbar, Navbar,
   `tools_ui`) reaching into optional tools. Core must never depend on a
   feature package, and the registry scheme already removes the need: a tool
   ships its own button as a contribution. `button_midi_learn` belongs in
   midiMapper; `hijack_dragdrop`'s CPP/iop branches belong in those tools.

**Dead edges (delete, don't port):** three commented-out
`#op.FNS_RPLS.par.Reset.pulse()` lines in `CustomParPromoter/.../parexec1`,
`FNS_Toolbar/widgets/button_midi_learn/parexec1` and
`ParOPDrop/button_ParOpPlace/parexec1` — copy-paste residue inflating
ResetPLS1's apparent fan-in from 1 to 4.

**Recommended resolution** (in order, each independently landable):

1. Delete the three dead references — free, and removes ResetPLS1's only
   apparent fan-in beyond MY_HOTKEYS.
2. Relocate the three backwards widgets into the tools they drive, as
   registry contributions. This is the only structural work, and it is
   exactly the packaging move anyway.
3. Give the rest one guarded-optional idiom instead of eleven bare
   attribute accesses. The global shortcut IS the feature-detect —
   `getattr(op, 'FNS_CPP', None)`, return quietly (or log once) when absent.
   Worth one core helper so all sites read the same and the "not installed"
   message is uniform. No dependency solver, no manifest edges — keeps
   §2.1's rule intact.
4. Merge the custom-par family — **decided 2026-08-13, see §1.2**.

**Unrelated bug found in passing:** `ExprHotStrings/extExprHotString` does
`self.customParPromoter = op.FNS_CPP` — a cached extension reference, which
goes stale on reinit (see `.claude/rules/td-python.md`). Fix independently of
packaging.

### 1.2 Package granularity — DECIDED and MERGED (2026-08-13)

**Per-tool packages, with exactly one deliberate bundle.** This closes the
granularity open question in §5 for the custom-par family; groups like MISC
and OUTPUT are still open.

**Merged: the `CustomParTools` package** (~934 ops): CustomParPromoter
(renamed to CustomParTools, keeps shortcut `FNS_CPP` and the
Toolbar/Navbar hosts, which already published canonical `CustomParTools`)
now contains QuickExt + QuickParent + ClearPars + iopPromoter as children.
Hub-button callbacks call them sibling-relative (`op('../QuickExt')`);
`FNS_QUICKEXT` / `FNS_QUICKPARENT` / `FNS_ClearPars` / `FNS_IOP` retired.
Each child keeps its own ConfigRegistry host (canonical unchanged, so
saved config sections carried over); nested suspect toxes live under
`modules/suspects/FunctionStore_tools_2025/CustomParTools/`.

**Hazard paid for during the merge — Embody move-detection vs shared
clone files.** The tsv carried rows for the OLD CustomParPromoter host's
DATs whose `file_path` was the MASTER's shared
`FNS_Toolbar/ToolbarRegistry/*.py` (many host clones share that file).
Renaming the package orphaned those op paths; Embody's move-detection
re-matched them to a DIFFERENT clone (`MISC/button_hog`), "moved" the
shared file to a per-clone path — deleting the master file that ~20
clones sync from. Repair: restore master files from git, remove the
retargeted rows + stray files (`remove_externalization_tag`), re-bind the
hijacked clone's `file` par to the master. **Before renaming/destroying
any COMP that contains stamped registry hosts, grep `externalizations.tsv`
for rows under its path first.**

The evidence is entry points, not vibes. Only CustomParPromoter carries
Toolbar and Navbar hosts; the other four have a ConfigRegistry host and
nothing else — no toolbar button, no navbar item, no op-menu contribution,
and their keyboardins hold only `esc`/`enter` (dialog dismiss inside their
own popups, not invocation shortcuts). **They have no independent entry
point**: `CustomParPromoter/button_custompar_tools` is their entire
user-facing surface. They are method libraries that were packaged as tools.

**Stay separate** — both have real global invocation hotkeys, so they stand
alone:
- **QuickCollapse** (`ctrl+w`, `ctrl+shift+w`) — also on the hub's
  middle-click, so that one branch becomes an optional feature-detect.
- **QuickParCustom** (`alt+x`, `shift+alt+x`, `alt+\`, `ctrl+alt+\`) — no
  cross-tool edges at all; already clean.

Effect on §1.1's graph: **14 edges → 8.** Four CustomParPromoter edges become
internal calls, and `FNS_Navbar → CustomParPromoter` + `→ iopPromoter`
collapse into one. Remaining after this plus the MY_HOTKEYS move and the dead
-line deletion: the three backwards core→tool widgets, `OpTemplates →
AutoRes`, `ExprHotStrings → CustomParTools`, `CustomParTools →
QuickCollapse`.

Merging retires the `FNS_QUICKEXT` / `FNS_QUICKPARENT` / `FNS_ClearPars` /
`FNS_IOP` global shortcuts. No alias shim: redesign25 is a major version with
no back-compat obligation (same call as the FNS_Config v2 rewrite).

### 1.2b The three core→tool widgets — one is BLOCKED (2026-08-13)

Assessed all three before touching them; they do not resolve the same way.

- **`tools_ui → GlobalOutSelect`: done.** Never a widget relocation at all --
  just `if tab == op.GLOBAL_OUT_SEL` inside the tab switcher. Replaced with
  a capability test (`hasattr(tab.par, 'Refresh')`), which REMOVES the edge
  instead of guarding it. GlobalOutSelect is the only one of the seven app
  tabs with a Refresh par, so it is equivalent today, and a future tab opts
  in by adding the par.
- **`FNS_Navbar → CustomParPromoter` + `→ iopPromoter`: RESOLVED by
  guarding, not moving (revised during the merge).** `hijack_dragdrop`
  stays a navbar citizen: it is a navbar-surface behavior (hijacks navbar
  drag-drop, probes a `../panenav` pane-context service — a constant-mode
  par reference the text/expression audit missed), and its CustomParTools
  calls are optional-feature delegation. Its `dragdrop` now resolves the
  package once via `getattr(op, 'FNS_CPP', None)`, bails with a `debug()`
  when absent, and reaches iopPromoter THROUGH the package
  (`cpt.op('iopPromoter')`) so `FNS_IOP` could still be retired. Note the
  audit lesson: constant-mode par VALUES can carry op references too —
  sweep those, not just DAT text and expressions.
- **`FNS_Toolbar → midiMapper`: RESOLVED (2026-08-13).** The blocker was
  `allowCooking = False` on midiMapper — a live panel widget cannot move
  into a COMP that does not cook. The owner re-enabled cooking, which took
  option 3, and `widgets/button_midi_learn` moved into midiMapper carrying
  its own ToolbarRegistry host. Its calls are now local (`parent().`), the
  entry re-registered from the new path keeping order 28, and the toolbar
  still reports 37 widgets. **No core→tool edges remain.**

  midiMapper also joined the fleet properly: it was the only tool with no
  ConfigRegistry host (it could not have one while cook-disabled), so its
  settings never roamed. Stamped via `StampHost`, canonical `midiMapper`.

  Fixed in passing: `panelexec4` called `op.FNS_MULTIMIDI.Resetall()`, but
  `Resetall` is a pulse PAR, not a method — it raised `tdAttributeError`.
  Now `.par.Resetall.pulse()`. Invisible until now because the button
  could not reach a non-cooking tool at all.

### 1.2c tools_ui tabs — discovered, not hardcoded (2026-08-16)

The tab panel was the last structural coupling: a static six-name list
(`switch_hack` DAT + `Menunames`) naming sibling COMPs, sibling panels
hand-WIRED into tools_ui as panel children, a startup timer working around
a 2023 folderTabs bug, and two tabs (`SearchWords`, `OpColor`) that were
unpackaged root glue no `.tox` carried — dead tabs even on a full install,
and a `None.family` crash in the switcher on any partial one.

Resolved by a **capability sweep**, same philosophy as the `Refresh` par
(§1.2b): a tool contributes a tab by carrying a `UI Tab` section on its
`Registry` par page (`Uitabsection` header +
`Uitab`/`Uitablabel`/`Uitaborder`/`Uitabpanel` — same page as the stamped
`Cf*`/`Tb*` sections, one prefixed section per surface); tools_ui's
`build_tabs` sweeps depth-1 siblings on startup/create/open and rebuilds
the folderTabs menu. Missing tool = missing tab, zero tabs = an empty-state hint. Tab
order and active tab roam via tools_ui's ConfigRegistry host
(`Tabuserorder`/`Activetab`); a tab's ✕ simply flips the tool's `Uitab`
off, which roams too.

**The rendering lesson (hard-won):** TD builds panels lazily and ONLY as
real panel children — opviewerCOMP and selectCOMP render a panel that is
already built somewhere, but neither force-builds an offscreen one
(selectCOMP mirrors already-rendering panels; opviewerCOMP force-renders
only non-panel viewers like DATs). So the old wiring was load-bearing, and
the sweep now reproduces it: root-panel tabs get WIRED
(`tools_ui.output → tool.input`) by `Rebuild()` itself; non-panel content
gets a local shim child inside tools_ui (opviewer for DATs, parameterCOMP
for `params:<pagescope>` tabs). Interior panel COMPs are rejected with a
log line — only the tool root can be a panel tab.

The orphan glue died: root `SearchWords` (opviewer onto
`FNS_OpMenu/OpSearchWords` — now FNS_OpMenu's own `./OpSearchWords` tab),
root `OpColor` + `openOp1` (a par-window springboard at ColorUI — now
`params:Families Colors Search` on ColorUI, a strictly better tab: the
full palette editor inline). Node-viewer redirects (`opviewer` par) on the
four root-panel tab tools were cleared — they pointed at mapping-table
DATs and would have hijacked any viewer-based rendering.

`build_manifest.py` derives a `tools_ui` surface from the presence of the
`Uitab` par (capability, not toggle state). Effect on §1.1's graph: the
`tools_ui → GlobalOutSelect` guard stays capability-based, `openOp1 →
ColorUI` is gone with its comp, and tab membership is no longer an edge
of any kind. Pkgversions bumped: tools_ui 1.1.0 (rework), the six tab
tools patch (+`UI Tab` pars, redirects cleared).

### 1.3 MY_HOTKEYS → zero dependencies (2026-08-13)

Six active hotkeys, and only ONE touches a tool:

| Shortcut | Action |
|---|---|
| `ctrl+0` / `cmd+0` | `op.FNS_RPLS.par.Reset.pulse()` — **the only tool reference** |
| `shift+alt+q` | `…selectedChildren[0].openParameters()` |
| `ctrl+alt+q` | `ui.panes.current.owner.openParameters()` |
| `shift+alt+w` | `ui.openCOMPEditor(selectedChildren[0])` |
| `ctrl+alt+w` | `ui.openCOMPEditor(owner)` |
| `ctrl+shift+f` | focus TD's palette search field |

Move `keyboardin_resetpls` + its callback into ResetPLS1 (where the call
becomes local — `parent().par.Reset.pulse()`, no global shortcut at all) and
MY_HOTKEYS becomes a dependency-free "TD conveniences" package. HotkeyManager
already discovers per-tool hotkeys, so no new mechanism is needed. This also
deletes the audit's only `try: … except: pass`.

## 2. The layers

### 2.1 Core + feature split

- **Core package** (always installed): registries + RegistryBase + `/sys`
  bootstrap + shared UI shells (toolbar/navbar/mainmenu hosts).
- **One package per tool** (or per small coherent group): self-registers
  on load via its stamped contributions.
- **Design rule worth committing to early: tools depend only on core,
  never on each other.** Then the manifest needs no dependency solver,
  the configurator needs no constraint logic, and partial installs can
  never half-break. Cheapest architectural rule available while the
  redesign is still in flight. (If cross-tool deps must exist, they
  become real pip dependencies — see §3 — and uv resolves them; but
  every such edge makes the configurator and the failure modes worse.)
- **Corollary (decided 2026-08-12): registry MASTERS live in core; tools
  ship scrubbed hosts.** Host cloning is not just a dev convenience — the
  globals' healing tick re-asserts clone exprs in USER projects too, so
  cloning is the core→fleet update rail: updating core rolls every
  in-project host (even ones inside tool toxes the user never updated)
  forward to the new master, while host Registration par VALUES survive.
  The catch it papers over: clone sync is NOT version-aware — with a
  newer master anywhere but core, an old in-project master would
  structurally DOWNGRADE a newer tool's host (the /sys global arbitrates
  by Version; clones don't). Masters-in-core makes "the in-project
  master" and "the newest registry version" the same thing by
  construction, so the downgrade case cannot arise. Revisit (version-
  aware _healHostClones) only if mixed-age installs ship before the
  core/tool split does.

### 2.2 Build pipeline

Headless TD or a live session driven via Envoy walks the tool list,
exports each COMP (`ExportPortableTox`, same artifact as today's
`modules/release/` output — see UvPackagingResearch §6 wrinkle), computes
hash + version, and writes a `manifest.json`: name, description,
category, icon, version, sha256, deps, artifact URL. The existing UPDATER
tool should consume the *same* manifest for updates — one catalog, two
consumers.

### 2.3 Install rails

> **Revised 2026-08-13** — see §4.2. Rail 3 (pip/uv) is dead; delivery is
> a bucket plus native `.exe`/`.dmg` installers. Rails 1 and 2 stand,
> and both consume the same manifest.

1. **Installer COMP** — a single small `.tox`, no launcher required.
   Reads a selection (JSON) + manifest and loads core then tools. **Built**
   (`packaging/dist/FNS_Installer.tox`, ~4 KB), currently installing from
   local artifacts; the bucket fetch is the remaining piece and should
   reuse the vendored `UPDATER/fileDownloader` rather than hand-rolled
   HTTP.
2. **TDXLU sidecar** — the launcher utility bus already exposes
   `load_tox` with `persist`, `parent`, `externaltox`, `toxfile_module`
   (see `TDXLUUtilityExt._handleCmdLine`, action `load_tox`). A
   "store" panel in TDXLU renders the manifest with checkboxes and
   pushes `load_tox` commands into live sessions; `persist` survives
   restarts. Best UX: already installed, already knows which TD
   sessions are alive, and browsers can't speak raw TCP to the bus
   anyway. Still open.
3. ~~pip/uv skeleton~~ — **dead**, see §3.

### 2.4 Configurator front-end

A static site (GitHub Pages) over the same `manifest.json`: pick
features, dependencies auto-check, output one of:

- a downloadable `selection.json` + installer-COMP bundle;
- a client-side-assembled zip of the chosen toxes;
- a deep link (`tdxlpp://install?tools=...`) handled by TDXLU, which
  performs the install over its bus — website as storefront, launcher as
  installer;
- a `pip install fns-tool-a fns-tool-b` line (§3 route).

A browser POSTing directly to a Web Server DAT on `127.0.0.1` is
possible but the fiddliest option (CORS, port discovery) — noted, not
recommended.

## 3. The pip-skeleton pattern (marker packages) — SUPERSEDED

> **Dead as of 2026-08-13.** Distribution is buckets + manifests, with
> native `.exe`/`.dmg` installers as the bootstrap (see §4.2). pip was
> only ever a delivery rail, and it argued mostly against itself even
> then. Kept for the reasoning, not as a plan.

Refines UvPackagingResearch with the *selection* mechanism. If pip is
the rail, feature selection must live in pip's world or the resolver
contributes nothing:

- Each feature is a tiny **marker package** (`fns-tool-quickop`, …):
  no real code, just metadata — tox artifact URL, version, sha256, and
  pip deps on `fns-tools-core` (+ any cross-tool deps, if allowed).
  Extras form also works: `fns-tools[quickop,swapops]`.
- The **bootstrap COMP** enumerates installed `fns-tool-*`
  distributions and loads their toxes in dependency order. This is the
  "skeleton on pip, bootstrapper collects toxes" model.
- **Pin, never "latest"**: package version N points at an immutable
  artifact (GitHub Release asset / versioned bucket key) with its hash
  in the metadata. Mutable `latest/` paths → unreproducible installs,
  uncorrelatable bug reports.
- **Embed vs fetch**: if toxes are pinned per package version anyway,
  embedding them in the wheel as package data (tdp-MVP's model,
  UvPackagingResearch §2.1) is simpler and atomic — `pip install` *is*
  the collection step, offline installs work, no runtime HTTP in TD.
  Remote-fetch only earns its complexity when payloads are large or
  binaries must update without republishing packages.

### Honest case against pip as the primary rail

(From the same discussion; UvPackagingResearch is neutral on this.)

1. It doesn't install anything *into TD* — the bootstrap COMP and all
   the hard work (core/tool split, audit, manifest) exist regardless;
   pip only replaces the download step.
2. Scope mismatch: `TDPyEnvManagerContext` is per-project; the toolkit
   is session-level UI tooling wanted in *every* project. (Unverified
   whether a shared/global env mode exists — check docs before leaning
   on it.)
3. Two sources of truth: pip's ledger is the venv, the user's reality
   is the network. Dissolves only under fully ephemeral loading (toxes
   loaded fresh every startup, never saved into the .toe) — a strong
   commitment made mostly to accommodate the transport.
4. Audience friction: TD users drag toxes; "set up a Python
   environment first" is an adoption tax. TD 2025.31310+ only.
5. Lifecycle: partially mitigated — the env manager Helper runs during
   TD core startup *before* any COMP cooks (UvPackagingResearch §4.1),
   so `sys.path` is ready before the bootstrap COMP inits. Failure
   modes still surface as a silently missing toolkit rather than an
   installer error.

Verdict from the discussion: with TDXLPP existing, pip mostly
duplicates the delivery layer while adding per-project ceremony. Without
TDXLPP it would rate considerably higher. The steel-man is the
ephemeral-bootstrap model — one universal bootstrap tox that never
changes, pip as the sync mechanism behind it.

**Correction worth recording**: TDPyEnvManager manages pip
packages/venvs — it does not "install toxes." Any tox materialization
is our own bootstrap's job, whichever rail delivers the bytes.

## 4. Recommended order

1. ~~**Dependency audit + core/tool boundary definition**~~ — **DONE**, §1.1.
2. ~~Manifest + per-tool tox export automation~~ — **DONE**, `packaging/`.
3. ~~Installer consuming manifest + selection JSON~~ — **DONE as a script**
   (`packaging/install.py`). The droppable *COMP* wrapper is still open.
4. ~~TDXLU store panel over the `load_tox` bus~~ — **DONE (2026-08-19),
   launcher-side** (TDXLPP `docs/fns-integration.md`): an **FNS Tools**
   tab in TDX Launcher Ultra renders this manifest by category, stocks
   the palette store (sha256-verified), writes a `selection.json` and
   drives `FNS_Installer` in a running session via new companion verbs
   (`fns_install` / `fns_status`, utility ≥ 0.9.0) — plus a live
   configurator over the ConfigRegistry settings server
   (`fns_settings_url` + `/api/state`//`/api/set` proxy), an offline
   editor over `FNStools_config.json`, a per-component palette shelf
   (standalone drops), and the §2.4 paste rail as fallback. Nothing on
   this repo's side had to change — the bucket, store, installer and
   settings-server contracts were consumed as published.
5. ~~Static configurator~~ — **DONE**, `packaging/configurator/`.
6. Optional: pip marker-package rail on top (§3), sharing the same
   artifacts and manifest. **Open.**

### 4.1 What exists now (2026-08-13)

```
packaging/build_manifest.py   derives manifest.json from the live project
packaging/catalog.json        the only hand-written data: category + description
packaging/manifest.json       41 packages, 6 core, artifacts + hashes
packaging/install.py          Plan() / Install() over a selection.json
packaging/configurator/       the picker; also emits a single-file build
packaging/dist/               41 exported .tox (6.5 MB, gitignored)
```

**Pick-and-choose works end to end today, with no web presence**: open
`configurator/configurator-standalone.html`, pick, download
`selection.json`, then `exec(open('packaging/install.py').read())` and
`Install('path/to/selection.json')`.

Verified: all 41 artifacts export, and all 41 install into a scratch
container (11,066 ops) with zero failures and op counts matching their live
originals. Install tests MUST use a cooking-disabled container — a live copy
of a registry master will otherwise try to promote itself to the `/sys`
global and destroy the running one.

**Dependencies are derived, not declared.** A package's `requires` is
exactly the core packages owning the registries it hosts, because masters
live in core and tools ship stamped hosts (§2.1). Every tool requires
`FNS_Config`; a tool with a toolbar button also requires `FNS_Toolbar`.
Nothing hand-maintains this, so it cannot drift from reality.

**Two findings the packaging work surfaced**, both pre-existing:

- `ExternalTables` could not be exported at all — its own `pre_release`
  hook resolved `par.Root` (a *sibling* reference) against the staged copy
  in `/sys/quiet`, where siblings do not exist. Fixed.
- The manifest carries a `portability` field, because Embody's
  absolute-path warnings scroll past during export and a package whose
  files point at THIS machine arrives subtly broken. Checked against the
  artifacts rather than assumed: the export strips the ROOT comp's
  `externaltox`, but **`file` pars and NESTED `externaltox` survive**, so
  the scan skips the former and reports the latter.

  The one that matters: **`OpTemplates` ships expecting
  `OPTemplates1.tox` to already exist in the installing user's palette**
  (`<palette>/FNStools_ext/OpTemplates/OPTemplates1.tox`). On a fresh
  machine that file is absent and the template library comes up empty.
  Six of its render templates also pin TD's own `Samples/Geo` by version.
  The other palette references (ExprHotStrings, FNS_HotkeyManager,
  FNS_OpMenu, ResetPLS1) are per-user data files those tools recreate, so
  they are benign.

## 4.2 Updates — REWORKED onto buckets + manifests + governed versions (2026-08-13)

> **Status: built and verified.** The rework described at the end of this
> section is implemented in `UPDATER/ExtUpdater.py`. The rest of the
> section is kept as the record of what was replaced and why.

**How updates worked before** (`UPDATER/ExtUpdater.py`): one version for the
whole toolkit — `Gittag` on the root COMP, currently `v2.11.2` — polled
against the latest GitHub tag. `Update()` snapshots every tool's settings
through `op.CONFIGREGISTRY.SaveAll()`, downloads ONE tox, and calls
`TDF.replaceOp(parent.FNS, newComp)`: the entire
`FunctionStore_tools_2025` COMP is swapped wholesale. Settings survive
because each tool's ConfigRegistry host re-loads its own section after the
replacement. Docked ops are undocked and restored around the swap.

**So there is no per-tool update mechanism at all** — one artifact, one
version, all or nothing.

**This is incompatible with subset installs.** A user who picks five tools
and later updates gets `replaceOp`'d with whatever the release tox
contains — the whole toolkit back, their selection erased. Per-package
installs without per-package updates is half a system.

**Is UPDATER therefore core?** In effect yes: it is the only update path.
It stayed `tool` only until the mechanism was decided — with the rework
landed it is now `core` (`CORE` in `build_manifest.py`), because the one
package that can fetch updates is the one a user must not be able to
accidentally decline.

### Versioning — REVERSED: a version we govern, not hashes

> This section originally read *"hashes drive updates, not version
> numbers"*. That was **wrong**, and the correction is the more useful
> record.

The reasoning was: per-package versions do not exist (38 of 39 empty,
`build` is a counter), but the manifest already carries a `sha256` per
artifact, so let the hash answer *"has this changed since the bytes I
installed?"* — exact, zero maintenance, no way to drift.

**It cannot answer that, because `.tox` export is not reproducible.**
Exporting one untouched component three times:

| Export | Bytes | sha256 |
|---|---|---|
| a | 66198 | `061982f7…` |
| b | 66190 | `8c41e46b…` |
| dist | 66150 | `116ae877…` |

They diverge at **byte offset 9** — the container header, before any
content. So a hash comparison marks *every* package updated on *every*
release: publish a drop that touched two tools and all 39 installs
re-download. The property the design was chosen for never existed.

Two replacements were considered and rejected:

- **`vc_data` / the `Vc*` pars** — the table already on 38 of 39
  components. Rejected: it belongs to Private Investigator, is written by
  tooling outside this repo, and nothing in packaging governs it. (Also
  thin: one package had a real version, one had no table, and `build` did
  not move across two project saves — so even "save counter" was wrong.)
- **A TDN content fingerprint** — genuinely stable (two exports of one
  component differ by a single line, `exported_at`, out of 2280).
  Rejected: TDN is an external package, and identity cannot depend on one.

**What we do instead: `Pkgversion`, a custom parameter on every package,
governed by us** — the `FunctionStore_tools_2023.tox` `Gittag` idea made
per-package. The manifest publishes it; the updater compares it against
the same parameter read live off the installed component.

Reading it live is what makes the embedded case work at all: a package
loaded into a `.toe` has no file to hash and no artifact to consult, but
it still declares what it is. It also means no side record can drift out
of truth — the component is the truth.

So: `sha256` verifies **downloads** (its real job), `Pkgversion` decides
**updates**, and the release label names the **drop**. The cost is that
bumping is manual and forgetting is silent, which is why `publish.py`
refuses a new release that bumps nothing.

### Distribution — DECIDED: buckets and manifests only

**Supersedes every GitHub-based flow in this document** (§2.3 rail 3, §3's
pip rail, and the old "GitHub keeps the tag" wording). The owner's
direction, 2026-08-13:

> in the future we will only serve an .exe and .dmg installer so don't
> worry about github-based update workflows. simply think in buckets and
> manifests from now on

So there are exactly two moving parts:

- **A bucket** holding `manifest.json` and the per-release artifacts. It
  is the single source of truth for what exists and what the bytes are.
- **Native installers** (`.exe` / `.dmg`) as the bootstrap that gets a
  first copy onto a machine. Everything after that — picking, installing
  into a project, updating — is manifest-driven.

Consequences, all of them simplifications:

- **The release label is ours, not git's.** It lives in
  `packaging/release.json` (with a `channel`, so `beta` is just another
  bucket prefix) and is stamped into the manifest and every artifact URL.
  The root COMP's `Gittag` par survives only as a fallback.
- **`UPDATER/github_remote` and `PollLatestTag()` become legacy.** Update
  checks stop being "poll the newest git tag and compare strings" and
  become "fetch `<base_url>/manifest.json`, compare artifact hashes". The
  `Gittag` string comparison in `OnPolledLatestTag` — including its
  major-version gate — has no role in that.
- **`UPDATER` becomes core** once reworked: reading the manifest and
  replacing changed packages is infrastructure, not an optional tool.
  (It stays `tool` in the manifest only until that rework lands.)
- **Distribution size stops mattering.** 39 artifacts is a directory
  listing in a bucket, not 39 release assets.

`packaging/publish.py` stages the exact bucket tree and re-hashes every
staged file against the manifest before reporting success — publishing
bytes that disagree with the hashes an installer will check is worse than
not publishing:

```
<release>/manifest.json                   immutable snapshot
<release>/<Package>.tox                   immutable artifacts
<release>/FNS_Installer.tox               bare installer (root already exists)
<release>/FunctionStore_tools_2025.tox    one-drop bootstrap: the toolkit
                                          root carrying installer + UPDATER
manifest.json                ROLLING pointer to the newest release
```

Releases are **pinned**: every artifact URL inside a manifest carries its
release, so a manifest always resolves to the bytes it was built from. The
rolling root copy exists only to answer "what is current?" once. No
mutable `latest/<Package>.tox` (§3).

### Where installed packages live — DECIDED: hybrid store + per-project pull

The palette is a **store**; projects embed self-contained copies. Two
deliberately separate motions:

1. **Refresh the store** — fetch the bucket manifest, download changed
   artifacts into `<palette>/FNStools_ext/store/`. Machine-wide,
   project-independent.
2. **Update this project from the store** — compare the open project's
   embedded packages against the store and `replaceOp` only what differs.
   Explicit, per project, never automatic.

Two records, and they are not interchangeable: the store's own
`manifest.json` (what the palette holds), and an `installed` table DAT
**inside the toolkit root COMP**. That table was originally the identity
source; since the Versioning reversal above it is an **audit trail only**
(release, when, the sha of the artifact fetched). Identity is the
component's own `Pkgversion`, read live.

Rejected: per-package palette toxes with `externaltox` bindings (updates
land machine-wide, but shipped packages stop being self-contained and
every project mutates under the user), and in-project `replaceOp` alone
(clean artifacts, but every project becomes its own frozen fork).

The accepted cost is that a project can sit behind the store, so the UI
must say so plainly rather than pretend everything is current.

**Never hash the live COMP to decide staleness** — a `.tox` re-saved
inside a project no longer hashes to what was published. (This instinct
was right and the conclusion drawn from it was not: the fix is not to
compare a *recorded* hash, it is to not compare hashes at all. See the
Versioning reversal above.)

### The mechanism — per-package, version-driven

With buckets-and-manifests settled there is no longer a choice to make.
Selection-aware whole-replace and reinstall-only both existed to work
around "one artifact, one version"; the bucket removes that constraint.

**UPDATER, reworked:**

1. Fetch `<base_url>/manifest.json` (rolling) via the vendored
   `UPDATER/fileDownloader` — a TDFileDownloader wrapping a Web Client
   DAT, with callbacks, progress UI, auth and a concurrency cap. Do not
   hand-roll HTTP; `requests` blocks the frame.
2. For each package present, compare the `Pkgversion` it declares against
   the version the manifest publishes. Newer = update available. Nothing
   else is consulted — not hashes, not `build`, not `Gittag`.
3. Download only those artifacts (pinned URLs), verify each **hash** after
   download — that is what hashes are for — then apply per package.
4. Settings survive as they do today: each tool's ConfigRegistry host
   reloads its own section after replacement.

One detail worth getting right the first time: a package the user never
installed must stay uninstalled — an update pass is not an install pass.

`UPDATER.par.Filename` (`FunctionStore_tools_2023.tox` on a 2025 toolkit)
was stale naming, not a broken download. Under the store model there is no
monolith artifact at all, so the parameter is gone.

### What was actually built (2026-08-13)

Three pulses on UPDATER, one for each motion, plus `Baseurl` /
`Storefolder` / `Showprogress` / `Status`:

| Pulse | Cost | What it does |
|---|---|---|
| **Refresh Store** | whole store | manifest + every artifact whose bytes differ → `<palette>/FNStools_ext/store/` |
| **Check for Updates** | one small JSON | manifest only, then compare — answering "anything new?" must not cost 6 MB |
| **Update This Project** | only what differs | fetches just the packages this project needs, then replaces them |

`Compare()` is the whole decision in one place, and reports five states:
`update`, `current`, `untracked` (in the project with no install record —
shown, never auto-updated), `missing`, `gone`. The project's side of the
comparison is an `installed` table DAT in the toolkit root, written per
package as it lands by BOTH rails (`InstallerExt.RecordInstalled` and the
updater), which is also what makes an interrupted pass safe to re-run.

`Baseurl` accepts a bucket URL, a `file://` URL, or a plain directory, and
artifacts resolve *relative to it* rather than to the manifest's own
`base_url` — same string against the real bucket, but it is what lets a
mirror, a local `packaging/publish/` tree or a localhost server serve the
whole flow. Both rails were verified end to end before the bucket exists.

**Three traps paid for, all in the vendored TDFileDownloader:**

- **A request issued from inside the Web Client DAT's own callback is
  silently dropped.** The file lands, the next GET never goes out — and the
  downloader's own `queueNext()` re-issues from exactly there, so its
  internal queue cannot be relied on either. Every stage after a download
  is deferred one frame (`_later`) and the queue is driven here.
- **A stale `stateDict` entry poisons every later request for that file.**
  It keys on url+location; an entry left in `GET`/`WAIT` makes `Download()`
  return the stale state instead of fetching. Each job starts with
  `AbortAll()`.
- **A connection that never opens produces no callback at all** — no
  success, no abort, just a request sitting in `GET` forever. Hence the
  stall watchdog: 45 s without progress fails the pass with a message
  naming the stuck files.

### Where package files live — and the two update paths (2026-08-13)

An install can put its package `.tox` files in one of three places, chosen
on the installer (`Package Files`), and **the updater does not track the
choice — it follows whatever binding each package actually has**, so there
is no mode flag to drift out of sync:

| Mode | Files | Update path | Trade |
|---|---|---|---|
| `embedded` (default) | inside the `.toe` | `replaceOp` from the store | one file to move; nothing to lose track of |
| `shared` | bound to the palette store | rewrite + reload (usually just reload) | one copy per machine — a store refresh reaches every project sharing it |
| `project` | copied to the project's own folder | rewrite + reload | each project owns its files, so one can hold a modified package without touching any other |

**Updating a bound package is a file write plus a reload, not COMP
surgery** — no copy/destroy of an extension-bearing COMP, no docked-op
juggling, and the change is a file the user can see and version-control.
Verified by rewriting a bound `.tox` with different bytes and confirming
the live COMP reloaded to match. A COMP reloaded this way does not report
its new state in the call that fired the pulse, so the pass records what to
check and settles it on the next tick.

Settings are safe by construction, not by care: they live in
`<palette>/FNStools_ext/config/FNStools_config.json`, never in the `.tox`,
and each tool's ConfigRegistry host re-registers on reload with
`autoload`, which re-applies its section. `SaveAll()` still runs before any
pass.

`shared` deliberately reintroduces the machine-wide coupling §4a rejected
as a default — a store refresh changes bytes every sharing project will
pick up on its next reload. It is offered because some users want exactly
that; `project` is the isolation-preserving choice, and `embedded` is the
default.

**What is still refused** (state `locked`): a COMP whose `.tox` Embody
*authors* — tracked rows in `externalizations.tsv` — because there the file
is generated FROM the live COMP, so writing over it destroys work. Note
this is the second line of defence: the first is that a package with no
install record is never a candidate at all, which is what actually keeps a
dev checkout out of every update pass. Learned the hard way by replacing
the live `AutoRes` with an artifact and losing its Embody bindings — and
note that `pi_suspect` is no help as a marker, since it survives into the
shipped artifacts.

## 4.3 The console: one landing page over settings + install (2026-08-21)

The ConfigRegistry settings server is now the toolkit's single in-project
landing ("FNS tools — Console", `FNSTools/FNS_ConfigRegistry/
settings_page.html` + `settings_server_callbacks.py` + Ui* methods on the
ext). One page, two tabs plus document actions:

- **Settings** — the scrollable all-tools sections view (nav = scrollspy
  jump list), unchanged `UiState`/`UiSet` contract.
- **Install & remove** — the FNS_Installer picker, NOT reimplemented: the
  settings server serves `/tools` and forwards `/manifest.js`,
  `/selection`, `/status`, `/install` straight to
  `InstallerExt.ServeRequest` in-process — one origin, one port, zero
  duplicated picker logic. Without an installer COMP the tab shows a
  plain explanation. **Verified live (2026-08-22)** once the rails became
  dev-root residents: `/tools` serves the picker, `/manifest.js` comes
  back `FNS_SERVED` with the root's children pre-checked, `/status`
  forwards. Unchecking an installed tool = removal, and the
  tab's banner states the precedence rule: install decides WHAT is in
  the project; the config layer always re-applies on top, and removed
  tools keep their settings for the next install. The same sentence now
  ships in the picker's core note (all three flavors).
- **Export / Import** — `/api/export` snapshots every registered tool
  LIVE into a schema-1 config document (correct under project scope,
  where the file is stale by design); `/api/import` applies a document
  onto installed tools now and merges sections of not-installed tools
  into the roaming file for their next install (verified end to end,
  including the deferred merge surviving a later SaveAll). Schema-gated.
- **Scope** — `/api/scope` reads/flips `Configscope`. `project` flips
  quietly; `global` REQUIRES `mode: push|adopt` (the page shows the same
  three-way choice as the in-TD dialog — no popup, an explicit decision).

## 4.4 The rails live in the dev root (2026-08-22)

`FNS_Installer` and `webBrowser` are now residents of the live `FNSTools`
root beside `FNS_Updater`, and the bootstrap is that root **castrated with
the rails kept** (`BOOTSTRAP_KEEP` in `build_installer.py`) rather than
emptied and re-injected. The reason is the one that motivated castration
in the first place: a build-only copy of anything is a second source that
drifts. `EnsureDevRails()` builds missing rails and re-embeds the
installer's two source snapshots in place; `BuildBootstrap()` runs the
same refresh on its staged copy and blanks per-project installer state
(selection, status, server). `FNS_Updater` stays a build-time injection
from the dist artifact on purpose — the dev copy is an Embody-tracked
master with file bindings.

**Tracked like everything else, shipped unbound.** `FNS_Installer` is a
Private Investigator suspect like every other dev-root component (tox
under `modules/suspects/FNSTools/`, version history in the lister). Two
guards make that safe: `build_manifest.RAILS` keeps it (and `webBrowser`)
out of `Packages()` — rails publish under the manifest's `rails`, never as
installable packages — and `_resetInstallerState` cuts the shipped copy's
`externaltox` binding, because a NESTED binding survives export and would
point a user's bootstrap at a dev-only path. Its DATs are deliberately
NOT Embody-externalized: `packaging/InstallerExt.py` and
`configurator/index.html` stay the single sources, re-embedded by
`EnsureDevRails()`.

**Root entry points, revised (2026-08-22).** Three pulses on the root's
`FNSTools` page, three roles: **Pick Tools** → the console's Install &
remove tab (`#tools`, in the in-TD webBrowser panel when the root has
one; the installer's own picker only while core is not installed yet);
**Open Settings** → the console's Settings tab, same panel; **Installer
Parameters** → the manual rail. `OpenSettingsUI(tab=, panel=)` grew the
two knobs (panel defaults on; a root without the panel opens the system
browser); the console reads its tab from the URL fragment. Correction
recorded: Open Settings first shipped to the system browser on the
unverified assumption that the in-TD panel could not do file dialogs —
the owner tested it, it can. Export now also writes
`<config dir>/exports/FNStools_config_<stamp>.json` server-side and the
page reports the path, so the export never rests on the browser honouring
a download in the first place.

**The source-checkout lock.** A resident installer's default target is
the dev root itself, and the picker pre-checks every live child — an
Apply there would remove authored masters. `SourceLock(target)` in
`InstallerExt.py` mirrors the updater's `_refuseReason` layer for layer:
the target is the container `build_manifest.py`'s `TOOLKIT` exports from
(source checkout + exporting root, both required), or Embody tracks rows
under it. `ResolvePlan` carries the reason as `plan['locked']`;
`InstallPlan` and `RemoveTools` refuse, the Plan/Install pulses report it,
the served `/selection` and `/install` answer REFUSED, and `/manifest.js`
hands the picker `FNS_LOCKED` so Apply is disabled up front with the
reason shown. A scratch container elsewhere in the source project stays
installable — that is still how installs are tested. Known gap surfaced
while doing this: the
published `v2.11.2` has no `rails` (no bootstrap was ever built after the
castration rework), so the website's paste-script rail asserts against it
until the next publish.

## 4.5 FNS_Console: the web front as its own /sys service (2026-08-22)

Owner decision, same day: "the console stopped being a ConfigRegistry
feature the moment it grew an install tab." Extracted on branch
`fns-console` (brief: `briefs/2026-08-22-fns-console.md`).

`FNS_Console` is a RegistryBase registry (`ConsoleRegistryExt`, shortcut
`FNS_CONSOLE`, master `/FNSTools/FNS_Console`, global
`/sys/FNS_Registries/FNS_Console`). Its **surface is the server**: the
global owns the ephemeral Web Server DAT (ports 36710-36759, idle-stop),
serves `console_page`, and routes — `/api/*` to `FNS_CONFIGREGISTRY`'s
Ui* (paths unchanged on purpose; TDXLPP reads `/api/state` + `/api/set`),
`/tools` + picker URIs to `FNS_Installer.ServeRequest`, `/t/<tab>/` to a
contributed tab. Its **hosts are tab contributors**: a stamped host's
Registration pars name a page DAT and an optional api DAT
(`onConsoleRequest(action, method, body)`), and `RegisterTab` publishes
them; Settings and Install & remove are built in. See
`packaging/docs/FNS_Console.md` for the contract.

`FNS_ConfigRegistry` keeps its Ui* API and nothing else of the UI: the
page, callbacks and server lifecycle are gone; `OpenSettingsUI(tab, panel)`
is a thin forward to `op.FNS_CONSOLE.Open` so the root pulses and the
launcher keep working. The root pulses prefer the console and fall back to
the forward. `FNS_Console` is core in the manifest (`CORE`,
`REGISTRY_OWNER`) and a PI suspect like its siblings.

**Paid for on the way:** a TD crash + relaunch reverted `/FNSTools` to its
last PI-saved tox (02:11) — every live structural change made since
(rails, pulse revision, installer PI row) vanished while files and commits
stayed intact. `save_project` writes the `.toe`; the root reloads from
`modules/suspects/FNSTools.tox`, which only `pi.Save(op.FNS)` rewrites.
Rule: after structural changes under the root, `pi.Add` new comps,
`pi.Save` changed suspects, `pi.Save(op.FNS)` LAST, then `save_project`.

## 5. Open questions

- [ ] Does TDPyEnvManager offer any shared/global (non-per-project)
      environment mode? (Affects §3 objection 2.)
- [ ] `tdxlpp://` protocol-handler registration in TDXLU — feasible on
      all target OSes?
- [ ] Ephemeral vs persisted installs as the default: `load_tox
      persist=True` semantics vs load-fresh-every-start (affects update
      story and §3 objection 3).
- [x] Package granularity — **per-tool, one deliberate bundle** (§1.2).
      MISC and OUTPUT already ship as single COMPs, so they are one
      package each by construction; no further grouping needed.
- [x] **Update mechanism vs subset installs — DONE (§4.2).** Per-package,
      store + per-project pull, driven by a `Pkgversion` parameter we
      govern. Hashes were tried first and cannot work: `.tox` export is not
      reproducible, so they verify downloads and nothing more.
- [ ] Descriptions in `packaging/catalog.json` were seeded by inspection
      and need an owner pass.
- [ ] **`OpTemplates` does not ship self-contained** — its `OPTemplates1`
      child is an external tox in the user palette, so a fresh install
      gets an empty template library. Either embed the child in the
      artifact or have the installer fetch it alongside.
- [ ] Where does the manifest live — GitHub Releases per-version, plus
      a rolling `manifest.json` index?
