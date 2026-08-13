# Configurator Distribution — Design Notes

How a user could pick and choose which FunctionStore tools to install —
via a configurator website/app — instead of taking the whole toolkit.
Companion to [UvPackagingResearch.md](UvPackagingResearch.md) (which owns
the pip/uv **delivery-mechanism** research) and
[RegistryScheme.md](RegistryScheme.md) (which owns the **in-project
runtime** relationship between tools and registries). Nothing here is
implemented — captured from a design discussion 2026-08-10.

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
- **`FNS_Toolbar → midiMapper` (7 lines): BLOCKED — midiMapper has
  `allowCooking = False`.** Moving `widgets/button_midi_learn` (54 ops, a
  live panel widget with four panelexecs) into a non-cooking COMP would
  stop it cooking, rendering, and firing its callbacks. The relocation
  cannot be done as specified. Three ways out, needs a decision:
  1. give midiMapper a cooking wrapper COMP that hosts the widget (the
     brief's own suggestion for reaching its state at all);
  2. leave the button in core and feature-detect midiMapper -- accepts a
     permanent core→optional edge, contradicting §1.1;
  3. revisit WHY midiMapper is cook-disabled and undo it.

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

### 2.3 Install rails (they compose, not compete)

1. **Installer COMP** — a single small `.tox`, no launcher required.
   Reads a selection (JSON) + manifest, fetches artifacts over HTTPS
   (Web Client DAT, non-blocking), loads core then tools. Works for
   users who have nothing else installed.
2. **TDXGL sidecar** — the launcher utility bus already exposes
   `load_tox` with `persist`, `parent`, `externaltox`, `toxfile_module`
   (see `TDXGLUtilityExt._handleCmdLine`, action `load_tox`). A
   "store" panel in TDXGL renders the manifest with checkboxes and
   pushes `load_tox` commands into live sessions; `persist` survives
   restarts. Best UX: already installed, already knows which TD
   sessions are alive, and browsers can't speak raw TCP to the bus
   anyway.
3. **pip/uv skeleton** — see §3. Delivery via package manager; still
   needs a bootstrap COMP in-project to materialize toxes into the
   network (UvPackagingResearch §1: uv can never materialize an
   operator network).

### 2.4 Configurator front-end

A static site (GitHub Pages) over the same `manifest.json`: pick
features, dependencies auto-check, output one of:

- a downloadable `selection.json` + installer-COMP bundle;
- a client-side-assembled zip of the chosen toxes;
- a deep link (`tdxlpp://install?tools=...`) handled by TDXGL, which
  performs the install over its bus — website as storefront, launcher as
  installer;
- a `pip install fns-tool-a fns-tool-b` line (§3 route).

A browser POSTing directly to a Web Server DAT on `127.0.0.1` is
possible but the fiddliest option (CORS, port discovery) — noted, not
recommended.

## 3. The pip-skeleton pattern (marker packages)

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

1. **Dependency audit + core/tool boundary definition** — the gate;
   everything else is mechanical. Decide the "tools depend only on
   core" rule here.
2. Manifest + per-tool tox export automation (Envoy can drive it).
3. Installer COMP consuming manifest + selection JSON — "pick and
   choose" works with zero web presence at this point.
4. TDXGL store panel over the `load_tox` bus.
5. Static configurator site as the public face (selections/deep links).
6. Optional: pip marker-package rail on top (§3), sharing the same
   artifacts and manifest.

## 5. Open questions

- [ ] Does TDPyEnvManager offer any shared/global (non-per-project)
      environment mode? (Affects §3 objection 2.)
- [ ] `tdxlpp://` protocol-handler registration in TDXGL — feasible on
      all target OSes?
- [ ] Ephemeral vs persisted installs as the default: `load_tox
      persist=True` semantics vs load-fresh-every-start (affects update
      story and §3 objection 3).
- [ ] Package granularity for groups (MISC, OUTPUT, SwapOps): per-tool
      or per-group artifacts?
- [ ] Where does the manifest live — GitHub Releases per-version, plus
      a rolling `manifest.json` index?
