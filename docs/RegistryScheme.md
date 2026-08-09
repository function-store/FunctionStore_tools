# The FNS Registry Scheme

A general pattern for **centralized, self-installing service registries** in
TouchDesigner, extracted from PaneTypeRegistry (PreviewPanel25) and reused by
ToolbarRegistry. This is the backbone of the packaging redesign: each tool
ships as a standalone package that *publishes* into central managers instead
of surfaces hardcoding their contents.

Current implementations:

| Registry | Global shortcut | Surface it manages | Master (dev) location |
|---|---|---|---|
| `PaneTypeRegistry` | `op.PANETYPEREGISTRY` | Panebar pane-type menu (rows, recall, right-click) | `PreviewPanel25/PaneTypeRegistry` |
| `ToolbarRegistry` | `op.TOOLBARREGISTRY` | Toolbar widgets (mirrors in `/ui/dialogs/bookmark_bar`) | `FNS_Toolbar/ToolbarRegistry` |
| `NavbarRegistry` | `op.NAVBARREGISTRY` | TD's pane bars (stamped copies in `panebar_default` + every `/ui/panes/panebar/*`) | `FNS_Navbar/NavbarRegistry` |

### NavbarRegistry surface specifics (how it differs from the toolbar)

- **Plural surface.** The navbar is TD's own pane bar: `/ui/dialogs/panebar/panebar_default`
  (the template new panes inherit from) PLUS one live bar per open pane. Sync and the
  healing tick walk ALL of them; a pane split after the last sync is populated by the
  next watch tick.
- **Stamped copies, not selectCOMP mirrors.** Every pane bar needs its OWN instance
  (a breadcrumb shows ITS pane's path; mirrors would show one source everywhere), and
  two entry kinds cannot be mirrored at all. Instances are `nbitem_<canonical>` copies
  tagged `NavbarRegistryItem`, `allowCooking` re-enabled (sources ship parked
  cook-disabled), re-stamped when the registered source changes (`RefreshWidget`).
- **`side` is first-class** (`left` | `right`, the user-visible left/right adjacency).
  TD's stock items are NEVER renumbered: at sync time the registry finds the in-flow
  `hmode=fill` pivot (`panenav`, the path area) and fractionally subdivides the open
  interval between the last stock-left item and the pivot (left side), or the pivot and
  the first stock-right item (right side). Recomputed live, so Derivative inserting
  their own fractional items (e.g. `homeAll` 5.4, `root` 5.5) heals on the next pass.
- **`kind` is first-class**: `widget` (aligned panel; height soft-enforced to the bar's
  inner height via the legacy `me.panelParent()` expression), `overlay` (out-of-flow
  panel, e.g. the click-through path-cell layer -- shown/hidden but never re-ordered),
  `logic` (non-panel COMP that just needs a running copy inside every bar, e.g. the
  drag-drop hijacker).
- **Display expressions survive.** A manager hide writes constant 0, but while an entry
  says "shown", a template's own display EXPRESSION is preserved.
- **Manager API deltas**: `SetWidgetSide`, `SideSequences`, `RefreshWidget`;
  `SetWidgetSequence` reassigns 1..N per side (widgets keep their side). No dividers on
  this surface. `NavbarConfigurator` (gear in the bar, `op.NAVBARCONFIG`) has Name /
  Side / Show / Origin columns -- Side cell click flips the side.
- **The legacy installer is retired**: `FNS_Navbar/execute1` inactive, `install.py`
  frozen on disk; sources stay parked in `FNS_Navbar/containers`.

---

## 1. Core idea: one global manager, many host publishers

Every registry component can play two roles, decided at runtime:

- **Global instance** — lives at `/sys/<RegistryName>`, owns the global OP
  shortcut, and is the **single manager** of its surface: which entries
  exist, which are shown, in what order, and how they are recalled. It is
  pure infrastructure — its host-publisher parameters (the Registration
  page) are neutralized at promotion (kept, reset to inert defaults).
- **Host instance** — an unmodified copy shipped inside a tool. It never
  manages the surface. It does exactly two things: (a) on load, install or
  version-upgrade the global instance; (b) publish its one entry into the
  global (`Autoregister` / `Register` pulse). All its API calls forward to
  the global; with no global ready they no-op with a `debug()` note.

The same COMP is both things — a copy *is* the distribution format. Drop the
component into any tool, set three parameters, done.

## 2. Bootstrap and promotion lifecycle

On extension init (`postInit`), an instance that is NOT the sys-global runs:

1. `_installGlobalRegistry()`:
   - A global exists and is **newer or equal** (semver on the `Version` About
     par) → stand down.
   - A global exists and is **older** → merge its entries, destroy it, copy
     self to `/sys` (`_become_global_registry`), hand data over via the
     `post_update` raw-storage handoff (the copy's extension may not compile
     on the first frames — a 20-attempt `reinitextensions` retry loop
     recovers), promote (set shortcut, neutralize Registration page, sync surface).
   - No global → reconcile any *parked* (shortcut-less) `/sys` copies
     (highest version wins, entries merged additively), then self-promote.
   - **Major**-version mismatch → `ui.messageBox` chooser; minor/patch
     resolve silently, ties favor the incumbent.
2. `_release_shipped_shortcut()` — a host never keeps the global shortcut.
3. `_applyHostRegistration()` — publish if `Autoregister` is on.
4. `_ensureSelectionExecuteRole()` — host disables any surface-handling ops
   and clears its local entry table (no parallel state).

The sys-global branch instead: drains `post_update`, sanitizes stored
entries, re-asserts the shortcut, **neutralizes the Registration page**
(`_neutralizeHostParameters` — pars kept, values reset), syncs the surface,
and arms the healing watch.

## 3. Entry data model and persistence

Entries live in the global's `StorageManager` store (`PaneRegistry` key —
historical name, shared by all registries) as **plain-string dicts**:

- Identity is **dual**: `panel_path` + `panel_id` (session op id first, path
  fallback via `_resolveByIdOrPath`) so renames and moves heal.
- `source_registry` + `source_registry_id` record the publishing host —
  ownership checks stop a copied template from clobbering the original's
  entry, and healing can ask the source to republish.
- Optional: `menu_order`, `display`, `callback_path`/`callback_id`, plus
  surface-specific flags (pane recall flags, etc.).
- **Strings only, never enum members** — TD pickles storage into the `.toe`,
  and enum members defined in a DAT module fail pickle's identity check
  after a reinit.

**Persistence model: the global table is deliberately ephemeral** (`/sys`
is NOT saved with the project). The source of truth is the publishers: on
every open each `Autoregister`ed host republishes, and **manager edits
write BACK to host pars** (`Menuorder`, `Displayed`, `Barwidth` —
compare-before-set so host callbacks don't storm). Entries a UI component
owns (the configurator's dividers, its gear, built-in overrides) persist in
that component's own state table, republished on its boot. **Virtual
entries** (`virtual: '1'`, e.g. dividers) have no backing operator; base
healing skips them, and they exist only as long as some publisher
re-registers them. The global additionally runs a **healing watch** (every
120 frames): re-resolve moved ops, ask live sources to republish missing
targets, drop entries whose host died, and (surface hook) re-inject anything
the surface lost — this is also what makes a late-arriving surface work.

## 4. RegistryBase contract (building a new registry)

`RegistryBase` (a textDAT module inside every registry COMP; subclass
imports it with `RegistryBase = mod('RegistryBase').RegistryBase`) owns
everything above. A new registry supplies:

```python
class MyRegistryExt(RegistryBase):
    SHORTCUT      = 'MYREGISTRY'      # global OP shortcut it claims
    EXT_NAME      = 'MyRegistryExt'   # class AND ext-DAT name (must match)
    REGISTRY_NAME = 'MyRegistry'      # COMP family name for /sys discovery
    # HOST_PAGE_NAME = 'Registration' (inherited default)
```

Surface hooks to override (safe no-op defaults in the base):

| Hook | Called when | Responsibility |
|---|---|---|
| `_preInit()` | start of `__init__` | par plumbing that must exist pre-storage |
| `_syncSurface(attempts=40)` | promotion, sys postInit, registration | idempotent: prune orphans + (re)inject every entry; self-defer with `run(..., delayFrames=30, delayRef=op.TDResources)` until the surface exists |
| `_sanitizeStoredRegistry()` | every postInit | migrate/repair legacy entry shapes |
| `_ensureSelectionExecuteRole()` | every postInit | enable surface handlers on the global, disable + clear local table on hosts |
| `_resyncRegisteredMenuRows()` | after ordered registration | default calls `_syncSurface()` |
| `_normalize_action(value)` | entry merges | coerce legacy values to strings |
| `_healRegistryEntries()` | watch tick (extend via `super()`) | add surface repair to base healing |

Plus the registry's own public API (`RegisterX` / `UnregisterX` + manager
methods). Follow the forwarding guard pattern; base healing calls
`self.UnregisterPanel(name)` — alias it if your verbs differ. Host
`_applyHostRegistration` in the base is pane-flavored; override it when your
Registration page differs (ToolbarRegistry does).

Standard component anatomy (copy an existing registry as the template):

```
MyRegistry (baseCOMP, initextonstart=1, ext: op('./MyRegistryExt').module.MyRegistryExt(me))
├── MyRegistryExt   textDAT  (externalized .py, syncfile)
├── RegistryBase    textDAT  (externalized .py, syncfile — per-package copy)
├── ExtUtils        baseCOMP (CustomParHelper + par-callback plumbing)
├── pre_release     textDAT  (release scrub hook, see §6)
└── custom pages: Registration (host-only; neutralized on the global) + About (Version!)
```

Registration page baseline: `Autoregister` (toggle), `Register` (pulse),
`Regstatus` (read-only str), `Comp` (COMP ref, default `..`),
`Canonicalname` (str), `Menuorder` (int, -1 = append), surface-specific
extras, `Callback` (DAT). About page must carry `Version` — promotion
depends on it.

## 5. The manager principle

The global registry is THE manager of its surface. Order, visibility, and
placement live in its central store and are applied by it — never by side
tables or per-widget expressions. (ToolbarDef is retired for registered
widgets; it lingers only for un-migrated legacy toolbar buttons.)

Manager API conventions (ToolbarRegistry reference):
`SetWidgetOrder(name, order)`, `SetWidgetDisplay(name, visible)`,
`Widgets` (snapshot property). Surface artifacts the registry creates are
**tagged and name-prefixed** (`tbmirror_*` + `ToolbarRegistryMirror` tag) so
pruning touches only what the registry owns. Cross-references resolve
through the registry (`op.TOOLBARREGISTRY.WidgetTarget('Name')` as a
parameter expression) rather than hard paths — entries heal, references
follow.

Surfaces must degrade gracefully: ToolbarRegistry injects into TD's stock
bookmark bar whether or not FNS_Toolbar is present, so a tool tox dropped
into a bare project still self-installs its button.

Surface-specific anchoring matters: bookmark-bar widgets must have their
panel input wired to the bar's `emptypanel` (`_anchorMirror`, mirroring the
original FNS_Toolbar installer) or they drop out of the bar's layout flow.
When adopting a surface, read its original installer for wiring like this —
copy/create alone is rarely the whole contract.

## 6. Packaging and distribution

- **Master vs copies — in-project hosts are CLONES.** Every tool host's
  `clone` par is an EXPRESSION on the stable global shortcut —
  `op.FNS_TOOLBAR.op('ToolbarRegistry') if hasattr(op, 'FNS_TOOLBAR') else None`
  — never a relative path (paths bake in hierarchy assumptions and break on
  re-parenting; note par OP paths resolve from the PARENT network,
  sibling-based). The guard makes cloning vanish silently where the toolbar
  package is absent. Master edits propagate live; host-specific Registration par VALUES are
  untouched by cloning. Two hazards paid for: cloning breaks `me.dock`
  references inside the clone (the ExtUtils `extParameter` Pages expr was
  rewritten dock-free), and a clone re-sync transiently rebuilds children.
  The `/sys` global stays unclonled (it is disposable). **`RegistryBase.py`
  is ONE shared file** (`scripts/shared/RegistryBase.py`): every master's
  `RegistryBase` DAT points at it via plain TD `file`+`syncfile` (NO Embody
  tag or tsv row -- an Embody-tracked DAT identity on a much-copied module
  is how the tracker once adopted a stray copy and dragged files away), and
  host copies + `/sys` copies follow automatically through clone sync /
  promotion. A base fix edits one file and hot-propagates to every registry;
  portable releases still embed the text, so shipped toxes stay standalone.
  PaneTypeRegistry (v0.1.0, on the shared base) distributes via the TD
  Palette: its live instance is file-bound for dev, but palette saves go
  through an unbind-save-rebind step so the palette tox ships with the
  text embedded and NO file bindings (a repo-relative binding would
  dangle in foreign projects).
- **Release scrubbing of clones**: shipped copies must NOT carry the clone
  par. The registry's own `pre_release` scrubs it for standalone releases;
  every HOSTING TOOL's `pre_release` carries an auto-added scrub block for
  nested hosts (nested components' own hooks do NOT run when a parent is
  released — by Embody, and releases also go through Private Investigator,
  which supports the same `pre_release` convention). Belt-and-suspenders:
  the global's healing tick re-asserts host cloning in-project
  (`_healHostClones`), so even a live-comp scrub self-repairs.
- **Release artifact**: `op.Embody.ExportPortableTox(target, save_path)` →
  `modules/release/<Name>.tox`. The component's `pre_release` hook runs on
  the staged copy and scrubs all host state (Registration pars, `PaneRegistry`
  / `HostCanonical` storage, `opshortcut`) so releases ship **inert**:
  first load installs/upgrades the `/sys` global, registers nothing.
  Because masters are Embody-tracked AND hook-bearing, `op.Embody.ReleaseAll`
  rebuilds them automatically.
- **A tool that publishes** ships: its widget/panel + a configured registry
  host copy (`Comp`, `Canonicalname`, `Autoregister=on`). See
  `VSCodeTools/ToolbarRegistry` for the canonical example.
- **Management UI is a SEPARATE package -- and the system's bootstrap
  seed.** The Toolbar Configurator ships ONE ToolbarRegistry host that
  plays three roles: bootstrap (alone in a fresh project it promotes the
  /sys global and self-installs the gear), gear publisher (the gear's
  order/display/width persist on that host's Registration pars like any
  tool), and drop-to-register template. **Drop-to-register:** drop any
  panel COMP onto the gear (modern Drag/Drop callbacks on btn_config:
  `onHoverStartGetAccept` filters to panel COMPs, `onDropGetResults` ->
  `PackageDrop`) and the Configurator copies its shipped host inside the
  dropped COMP (`Comp='..'`, canonical = comp name, order = max+1) and
  registers it -- the COMP becomes a portable self-registering package.
  Stamping is DEFERRED a few frames and the template's `enablecloning`
  is off during the copy: copying a clone-bound COMP inside the
  drop-event stack has crashed TD. Scrub the copy's storage via its
  StorageManager CONTAINER key (`ToolbarRegistryExtStored`) -- the
  per-item keys are not top-level storage entries. Without any registry
  the Configurator still degrades to standalone mode (built-in bar icons
  only). 
- **Entries carry the tool's wiki page (`help_url`, 0.6.0).** On
  registration the host resolves it from its `Helpurl` par when set,
  else auto-discovers from the registered panel or its parent: a
  `docsHelper` COMP (its `Url` par), or a `Url`/`Helpurl`/`Wikipage`
  custom par on the panel itself -- both pre-registry self-reporting
  conventions keep working with zero tool changes. `RegisterWidget`
  accepts `help_url=`; `OpenDocs(canonical)` opens it (`ui.viewFile`).
  Configurator surface: right-click the Name cell.
 With
  host cloning, anything inside the registry replicates into every host and
  every tool's tox — so the registry ships NO widgets at all. The editor
  (`ToolbarConfigurator`, `modules/release/ToolbarConfigurator.tox`) ships
  its own gear button + a standard registry host (`Configure`, order 0) —
  the gear only appears where the UI actually exists, so there is never a
  dead affordance. `op.TOOLBARREGISTRY.OpenConfigurator()` remains as a
  convenience API, resolving the editor via its `TOOLBARCONFIG` global
  shortcut (toolbar-package child fallback, debug note if absent).

## 7. Known hazards (paid for once — do not rediscover)

- **CustomParHelper `EXT_SELF` is class-level** — with a shipped host plus a
  `/sys` copy, callbacks can hit the wrong instance. Always route through
  `_hostExtFromPar(par)` (resolve the ext from the parameter's owner).
- **First-compile fragility**: a copy's extension initializes DURING
  `copy()`, before docked ExtUtils resolves; the CustomParHelper import line
  needs the `me.parent().op('ExtUtils')` fallback, and promotion needs the
  reinit retry loop.
- **Storage pickling**: strings only (see §3).
- **Par callbacks fire a frame late** — never assert their effects in the
  same script that set the parameter.
- **`list.extend()` returns None**; build `panes`-style lists with `+`.
- **Panebar specifics**: TD's `cellselectid` fires on right-click too — the
  pane registry rewrites dropdowns to `celllselectid` (left-only); panelexec
  templates copied into dropdowns lose relative `panels` wiring and must be
  re-pointed after copy.
- **`run()` scheduling**: always `delayRef=op.TDResources` so delays survive
  timeline stops.
- **Externalizing a DAT that carries a foreign file binding** (tags/file par
  from another project) can raise a modal that blocks TD's main thread —
  expect it when adopting components from other projects.
- **Cook-disabled tools cannot host widgets or registries.** A COMP with
  `allowCooking=False` (e.g. midiMapper) can't compile extensions and its
  panels don't render — so its toolbar button must live OUTSIDE it (toolbar
  chrome, or a small always-cooking wrapper). Check `allowCooking` before
  moving a widget into a tool.
- **execute_python rollback restores only ops the script CREATED — not ops
  it destroyed.** A batch that destroys legacy state and then fails leaves
  the destroyed ops gone. Destroy last, or keep a restore source (the
  external .tox) at hand.
- **Widgets sized by their panel parent** (`me.panelParent(1).height - 5`)
  break when moved out of the bar into a non-panel tool COMP — constify
  `w`/`h` on migration.

## 8. Adding a new registry — checklist

1. Copy an existing master (ToolbarRegistry is the smaller template); rename
   COMP + ext DAT to `MyRegistry` / `MyRegistryExt` (names must match
   `REGISTRY_NAME` / `EXT_NAME`).
2. Write the subclass: class constants, surface hooks, public API,
   `_applyHostRegistration` override if the Registration page differs.
3. Adjust the Registration page pars + help text; set About `Version` to
   `0.1.0`.
4. Externalize COMP (tdn) + both `.py` DATs; verify `get_op_errors` clean.
5. Reinit → confirm `/sys/MyRegistry` promotes, shortcut resolves,
   Registration page stripped on the global.
6. Pilot: copy the host into one tool, configure, `Autoregister` on; verify
   the entry + surface artifact + unregister cascade (wait a frame after
   par changes).
7. Add `pre_release` scrub hook; `ExportPortableTox` to `modules/release/`;
   load-test the tox in a scratch COMP.
8. Cold test: restart TD (or drop the tox in a bare project) and verify the
   full bootstrap.

## 9. Migrating a legacy surface to the registry scheme (lessons from the toolbar port)

What the toolbar port replaced: a monolith whose installer copied REAL
button COMPs into `/ui/dialogs/bookmark_bar` on every launch, a
`ToolbarDef` table owning order/visibility, widget-based dividers, a
chrome-publisher script, and per-button self-reported wiki URLs. The
registry scheme replaces all of it with host publishers + `/sys` manager +
mirrors. The order below is the one that worked; the lessons were paid for.

### Migration order that worked

1. **Extract the base from the most mature LIVE registry** (RegistryBase
   came from the working PaneTypeRegistry, not from a blank page), then
   build the new surface registry on it.
2. **Prove the contract on ONE pilot tool** (drop the package into a bare
   project, watch it self-install) before touching the fleet.
3. **Retire the definition table only when the registry owns
   order/visibility** — never run two managers over the same surface.
4. **Fleet rollout, one tool at a time**: copy the master host in, clone
   par as an EXPRESSION (never a relative path), set Registration pars
   (panel = sibling name), `Autoregister` on, deferred force-apply.
   Tools stay standalone packages — do NOT fold them into the surface
   package.
5. **Chrome pieces get real hosts too.** A publisher *script* has no
   pars to write back to — every entry needs a live host or persistence
   breaks for it.
6. **Dividers become virtual entries** owned by the manager UI's state
   table — widgets that exist only to be gaps should not be operators.
7. **Metadata rides discovery, not migration.** For self-reported data
   (help/wiki URLs) teach `_hostHelpUrl`-style discovery to read the
   legacy conventions in place instead of copying values into the new
   scheme — copies go stale the moment the source is edited. Survey
   first: the field had TWO conventions (`docsHelper` child with `Url`
   par, and bare `Url`/`Wikipage` pars on the button itself).
8. **Parity-audit against the legacy artifact before retiring it.** Load
   the old tox in a scratch spot, build the legacy name→value map, diff
   byte-for-byte against the registry entries (toolbar port scored 20/20
   on URLs only because two discovery conventions were implemented).
9. **Only then delete legacy remains**: the bar's installed button
   copies, definition-table relics, and the legacy comp itself.

### Lessons

- **The legacy installer re-installs on EVERY launch.** Loading the old
  tox anywhere — even "just to check" — repopulates the bar with real
  buttons next to the mirrors. After ANY contact with the legacy comp,
  audit `emptypanel`'s output connections, and never let the comp
  survive into a project save.
- **The legacy .toe carries zombie shells** (Embody save-strip leftovers)
  that reinfect the bar after restarts — hunt `*1`-suffixed shells and
  stale externalization tags inside the legacy container too, not just in
  the bar.
- **Mixed-era menu orders drift the sequence.** Legacy 1-based table
  orders meeting normalized sequence indices shift dividers by one on
  every republish. After the whole fleet publishes, renormalize ONCE with
  `SetWidgetSequence` — write-back then stamps consistent contiguous
  orders into every host par and state row, and the drift cannot recur.
- **Never strip user-tooling tags** (`pi_suspect`, `FNS_externalized`) in
  legacy-cleanup sweeps; they belong to Private Investigator and Embody,
  not to the old toolbar.
- **External-tox reload trumps the .toe on boot.** The surface package
  reloads from its suspects `.tox` on start, so a stale tox silently
  reverts live-only migration work after a crash or restart — re-save the
  suspects tox as part of EVERY landing, not just the .toe.
- **Same-frame verification lies.** Connector lists and par-callback
  effects read stale in the frame that mutated them — verify a destroy or
  re-anchor only after real frames pass.
- **Keep the legacy artifact until the parity audit passes.** It is the
  only authoritative record of per-tool metadata (URLs, orders, widths);
  delete it only after the diff comes back clean.
