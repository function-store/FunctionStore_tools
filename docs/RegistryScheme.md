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
| `OpMenuRegistry` | `op.OPMENUREGISTRY` | TD's Insert Operator dialog (`/ui/dialogs/menu_op`) -- search words, row decorations, right-click items | `FNS_OpMenu/OpMenuRegistry` |

### OpMenuRegistry surface specifics (how it differs again)

- **Entries are BEHAVIOUR, not operators.** The other two registries publish
  a thing to place on a surface (a widget, a bar item). This one publishes
  *contributions to a dialog TD already owns*, in five kinds: extra fuzzy
  **search words**, node-table **row decorations**, **right-click menu
  items**, filter-**chain stages**, and dialog **panels**. The first three
  create nothing in `/ui` at all; the last two are injected copies, tagged
  `OpMenuRegistryChain` / `OpMenuRegistryPanel` so pruning only ever touches
  what the registry owns.
- **Appearance is NOT a registry concern -- see `FNS_UISkin`.** Skinning
  (panel background TOPs, and whatever customization comes next) briefly
  lived here as host parameters, then as an `onPanelTops()` hook. Both were
  retired: skinning contributes nothing to a surface's *behaviour*, it just
  overwrites a parameter on a dialog TD already owns, so routing it through
  the registry made every skinnable panel a registry concept for no gain.
  `FNS_UISkin` is a standalone tool -- no host, no callbacks DAT -- covering
  **every** registry surface's background panels, one page each: Op Menu
  (`emptypanel`/`nodepanel`/`familypanel`/`searchpanel`), Toolbar
  (`bookmark_bar/emptypanel`), Main Menu (`mainmenu/emptypanel`) and Pane Bar
  (TD's `panebar_default` template plus every live `/ui/panes/panebar/*` --
  one parameter, 11+ panels). `UISkinExt.SKIN_TARGETS` is the single source
  of truth: it GENERATES the pages and parameters (`EnsurePars`) and drives
  `Apply()`, so adding a knob is one row and nothing else. Targets resolve
  through `ops()` patterns on every apply, and a healing tick re-asserts
  while anything is claimed, so a pane split later still matches. Values are
  captured once per panel and restored on blank. **The rule this settled:
  the registry is for contributions a surface must aggregate, order, and
  arbitrate between; a tool that only writes a parameter should just write
  it.**
- **Chain stages and panels are what the legacy installer hardcoded.** The
  I/O filter used to be a special case inside `install.py` (splice
  `script_IOFilter` after the injected node; inject `radioExpose` into
  `searchpanel`; both gated on a `parent.FNS.par.Activeopmenuiofilter`
  check). IOFilter now declares both for itself via `onChainNodes()` /
  `onPanels()`, and reads the toggle in its OWN callbacks -- so whether it
  contributes is IOFilter's decision, not a branch in the installer. A
  `parexec_active` inside IOFilter calls `op.OPMENUREGISTRY.Resync()` when
  the toggle flips. Chain order follows contributor order and the chain
  heals around a removed stage, so install order stops mattering.
  `install.py` is down to ONE executable line (the compat-table patch).
- **The contribution's CODE lives in the publishing tool.** Each tool ships
  ONE `opmenu_callbacks` DAT of its own; the entry carries only
  `callback_path`/`callback_id`, and the registry probes which hooks that
  module defines (`onSearchWords`, `onDecorateLabel`, `onMenuItems`,
  `onMenuItem` -- all optional). This is the rule that keeps the surface
  component free of tool names: FNS_OpMenu used to call
  `op.FNS_OPTEMPLATES.Templates` and `op.FNS_OPTEMPLATES.OpenTemplateBase()`
  from its own callback DATs; that code now lives inside OpTemplates and
  travels in OpTemplates' tox. **One host per tool** -- capabilities are
  discovered, not declared, so a tool contributing three different things
  still ships one host.
- **The registry owns NO chain stage of its own** (corrected 2026-08-09).
  It owns the *mechanism* — aggregation, injection, ordering, healing,
  menu dispatch (`popmenu_dispatch`) — and nothing that knows TD's
  node-table schema. The stage that APPLIES the aggregated search words and
  decorators (`script_inject` + its callbacks) belongs to **FNS_OpMenu**,
  published through `onChainNodes` exactly like IOFilter's. It was already
  written against the registry's public API (`SearchWords`, `Decorators`),
  so it was a contributor in everything but location. Moving it kept the
  schema-fragile part (column names, the `score <= 3` heuristic,
  `layouts/{family}/{opType}` strings) inside a tool, where a TD version
  change breaks one tool instead of the registry.
  Consequence, and it is the honest trade: `onSearchWords` /
  `onDecorateLabel` only take effect when some tool supplies an applier
  stage. The registry still aggregates them regardless.
- **Chain wiring is re-asserted every sync, not just on injection**
  (`_relinkChain`). A stage that is merely "not stale" is still wired to
  whatever neighbour it had when injected, so adding, removing or
  re-ordering ANY other stage silently leaves it mis-linked — the bug that
  produced a stage with two inputs and no outputs while TD's own downstream
  ops sat on the wrong stage. Each sync enforces
  `families -> stage1 -> ... -> stageN -> (whatever consumed the chain)`,
  remembering each consumer's exact input index so multi-input consumers
  reconnect faithfully.
- **The right-click menu is rebuilt, not appended to.** TD's own three items
  (Help / Python Help / Snippets, `BUILTIN_MENU_ITEMS = 3`) always lead;
  registered labels follow. `popmenu_dispatch` routes any click past the
  builtins to `InvokeMenuItem(index - 3, optype)`, which calls back into the
  publishing tool. Rebuilding from the live par's first 3 entries keeps it
  idempotent across heals.
- **Hot path**: the injected node cooks over every operator type in the
  dialog, so it resolves `SearchWords` and `Decorators` ONCE per cook and
  calls the functions per row -- never re-resolve contributors per row.
#### Making a tool a publisher (the whole flow)

1. Copy an `OpMenuRegistry` host into your tool; set `Comp` = `..` and
   `Canonicalname`.
2. **Pulse `Create Callbacks`.** It spawns `opmenu_callbacks` into your
   tool from the registry's `callbacks_template` and wires the host's
   `Callback` par to it. Idempotent: an existing DAT is adopted, never
   overwritten, so pulsing again just repairs an unset `Callback`.
3. Fill in the hooks you want. Turn `Autoregister` on.

The pulse is promoted onto the tool itself (`Omcreatecallbacks`) alongside
the other Registry-page pars, so the whole setup happens without opening
the host. Two things the spawner does that matter: it **strips the file
binding** off the copy (the template is a synced repo file -- an inherited
binding would make every tool's callbacks read from, and save over, the one
shared template), and it strips tracker tags so the copy does not get
adopted as a tracked identity.

#### The `opmenu_callbacks` protocol (what a tool author writes)

**Every hook is optional** -- the registry probes the module and uses what
it finds, so one host covers a tool that defines one hook or all six. The
spawned template defines all six but returns empty from each, so a fresh
publisher contributes NOTHING until you fill something in. `me.parent()` is
your tool; resolve everything from there, never by absolute path or global
shortcut.

| Hook | Returns | When |
|---|---|---|
| `onSearchWords()` | `{opType: [word, ...]}` | merged into the dialog's fuzzy search |
| `onDecorateLabel(opType, label)` | replacement `str`, or `None` | once per visible row, per cook -- keep it cheap |
| `onMenuItems()` | `[label, ...]` | appended after TD's own three items |
| `onMenuItem(label, opType)` | -- | one of YOUR items was clicked |
| `onChainNodes()` | `[scriptDAT, ...]` | stages spliced into the node-table chain, in order |
| `onPanels()` | `[(comp, anchor_name), ...]` | panels injected into the dialog, wired to `anchor_name` |

Returning `[]` / `{}` WITHDRAWS a contribution -- the registry prunes what
it injected. That is how a live toggle works: decide it in your callbacks
(it is your tool's decision, not the registry's) and call
`op.OPMENUREGISTRY.Resync()` when the condition changes, or let the ~2s
healing tick pick it up. `FNS_OpMenu/IOFilter` is the worked example.
A hook that raises is contained: debug()'d, skipped, dialog keeps working.

- **Manager API deltas**: `RegisterContributor` / `UnregisterContributor`,
  `SetContributorOrder`, `SetContributorDisplay`, `Contributors`,
  `SearchWords`, `Decorators`, `DecorateLabel`, `MenuItems`,
  `InvokeMenuItem`, `Resync`. Tool page prefix `Om`. No
  configurator yet (a natural next step: enable/disable and reorder
  contributions).
- **The global re-asks hosts to publish during the boot window** -- and this
  is the fix the other two registries still lack. `/sys` does NOT save with
  the project, so on every open (and after ANY extension reinit wave,
  including the one every `project.save()` triggers) the global comes up
  empty while hosts believe they are registered: their `Autoregister` ran at
  extension init, which can predate the global being ready. Symptom: hosts
  report `Regstatus: Registered` while `Contributors` is empty.
  `_reapplyAutoregisterHosts()` runs on the first `BOOT_SWEEPS` (6) healing
  ticks, finds live `Autoregister` hosts the global has no entry for, and
  asks them to republish; then it stops, because it is a project-wide
  search. Verified: wiping the global's entries entirely and running ONE
  heal tick restores every contributor and the whole surface.
  **`findChildren` gotcha paid for here: TD's `depth` argument is an EXACT
  depth, not a maximum** -- `findChildren(name=X, depth=6)` silently matched
  nothing while the bare `findChildren(name=X)` found all three hosts. Never
  pass `depth` when you mean "anywhere below".
- **The legacy installer is NOT fully retired here** -- unlike the navbar.
  `FNS_OpMenu/install` still runs (from `execute2`, 60 frames after start)
  for FNS_OpMenu's OWN chrome: the optional IOFilter injection and the
  family-compat patch. Only the parts the registry took over were removed.

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
  frozen on disk. Sources live UN-parked (cooking on) in `FNS_Navbar/containers`,
  because **each source carries its own registry host INSIDE it**
  (`containers/parent_hierarchy/NavbarRegistry`, `Comp='..'`) -- every
  component is a standalone self-registering unit, same shape drop-to-register
  stamps. A host inside a cook-disabled subtree cannot compile, hence no
  parking. `_injectItem` strips the embedded host from bar copies (the
  /sys-or-/ui guard would neutralize it anyway; bars stay lean).

### MainMenuRegistry surface specifics (the toolbar/navbar hybrid)

- **Surface**: TD's main menu bar `/ui/dialogs/mainmenu` (File/Edit strip on the far
  left, wiki/forum/tutorials/fps cluster left of center, OpFamUI/update in the right
  corner). ONE bar, like the bookmark bar -- so entries render as **selectCOMP
  mirrors** (`mmitem_<canonical>`, tag `MainMenuRegistryItem`), never stamped copies.
  Mirror height is soft-enforced to 19 px (`BAR_ICON_HEIGHT`, the same height every
  stock main-menu item uses); width live-follows the source unless the entry carries
  an override.
- **Anchoring contract**: every stock item wires its COMP input 0 to the bar's
  `emptypanel` output -- mirrors get exactly that wire (`_anchorMirror`); an unwired
  panel drops out of the bar's layout flow.
- **`side` is first-class, navbar-style** (`left` | `right`), but the pivot is
  **`stringfield`** (alignorder 4.0, the bar's only in-flow `hmode=fill` item -- the
  stretchy status-message area). Left entries subdivide (last-stock-left ~3.4, 4.0);
  right entries subdivide (4.0, first-stock-right ~4.9). TD stock alignorders are
  never touched. The File/Edit `menu` strip and `emptypanel` sit at alignorder 0 and
  are excluded from the scan, same as the pane bar's alignorder-0 cluster.
- **No `kind`, no dividers** (v0.1.0): every entry is an aligned panel widget. Groups
  (bracket pairs) come from RegistryBase and work unchanged.
- **Built-ins ARE auto-adopted -- seeded by pixels, not alignorder.** The whole left
  cluster (`wiki` .. `realtime`) is adopted into the managed sequence so entries can
  be ordered BETWEEN TD's items (user decision 2026-08-10). Two deltas from the pane
  bar's recipe: the duplicate-alignorder pair (`gpuUsage`/`realtime` both 3.4) is
  adoptable anyway because first adoption seeds the sequence from LIVE X positions
  (pixels resolve the tie the way the user sees it), and the `layer == 0` adoption
  filter is dropped (`gpuUsage` rides layer 5 yet aligns like any fixed item).
  CRITICAL: snapshot the x positions BEFORE the first `AdoptBarWidget` call -- every
  adoption re-flows the bar, so positions read mid-loop are churn, not truth (paid
  for once: entries jumped ahead of `wiki`). Original alignorders persist as
  `td_order` in the Configurator `state` table; right-click the TD topbar button
  restores TD's original order. `menu` (ao 0), the `stringfield` pivot, and the
  `OpFamUI`/`update` right corner stay unmanaged landmarks. Adopted order/display
  persist in the `state` table (adopted entries have no host publisher).
- **`Anchor` par (Registration page, `Mmanchor` on the tool)**: pins an entry into
  the gap directly after a NAMED stock item, overriding the side band -- the escape
  hatch for placing next to something unmanaged (e.g. the right corner,
  `Anchor=OpFamUI`). Name-based and re-resolved live, so it heals across TD builds;
  a vanished anchor falls back to the side band. With the left cluster adopted,
  ordinary sequence order covers most cases (projname sits between `tutorials` and
  `startstop` by plain order now).
- **Manager API deltas**: `SetWidgetSide`, `SideSequences`; `SetWidgetSequence`
  reassigns 1..N per side. `MainMenuConfigurator` (gear in the bar,
  `op.MAINMENUCONFIG`) is the NavbarConfigurator adapted; tool page prefix is `Mm`.
- **Callbacks DAT (optional): lifecycle hooks, not interaction.** The panel handles
  its own clicks (the mirror forwards them); the callbacks DAT is for REACTING to the
  manager -- the registry probes it for `onRegistered(canonical, info)` (fires on
  EVERY publish incl. boot/healing re-applies; keep idempotent), `onUnregistered`,
  `onDisplayChanged(canonical, visible)` (manager show/hide only, NOT group
  collapse), `onSideChanged(canonical, side)`. All optional, raise-contained. The
  host's `Create Callbacks` pulse (`Createcallbacks`, promoted as
  `Mmcreatecallbacks`) spawns `mainmenu_callbacks` from the registry's
  `callbacks_template` INTO THE HOST'S PARENT TOOL -- not `_hostComp()`, which on
  this surface is the registered widget panel itself (the OpMenu recipe copied
  verbatim spawns the DAT inside a bare textCOMP; paid for once) -- and wires the
  `Callback` par to it. Idempotent: an existing DAT is adopted, never overwritten.
- **First registrant**: BorderlessWindow publishes its `projname` (canonical
  `ProjName`, side left) through an embedded host; its legacy `install.py` direct-copy
  injection ships nothing, and `displayProjName` drives the mirror through
  `SetWidgetDisplay` (dynamic-visibility pattern, like HydroHomie on the toolbar).

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

**Page ORDER is standardized across every registry** (fleet-wide as of
2026-08-09) — five `startSection` groups reading as the setup flow a tool
author actually follows, rather than the order pars happened to be added:

| Group | Pars |
|---|---|
| What is registered | `Comp`, `Canonicalname` |
| How it behaves | `Callback` (+ `Createcallbacks` where the registry spawns one) |
| Turn it on | `Autoregister`, `Register`, `Regstatus` |
| How it appears | `Menuorder`, `Displayed`, + surface extras (`Barwidth`, `Align`, `Kind`) |
| Meta / shipping | `Helpurl`, `Promotepars` |

`Regstatus` sits under the pars that produce it; a "create" pulse sits
directly under the par it populates. A new registry copied from any master
inherits this. `TOOL_PAGE_PARS` follows the same flow in its own terms
(on the tool, the "create" pulse comes first — it is the first thing you
do). Re-ordering is par `.order` + `.startSection` on the MASTER only,
then `enablecloningpulse` on every host: no `.py` edit, so it costs no
extension reinit wave. Verify entry counts against a pre-change baseline
afterwards — the clone churn is the risk, not the ordering.

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
  is ONE shared dev file** (`scripts/shared/RegistryBase.py`): every master's
  `RegistryBase` DAT points at it via plain TD `file`+`syncfile`, and hosts +
  `/sys` copies follow automatically through clone sync / promotion -- a base
  fix edits one file and hot-propagates to every registry. Releases stay
  standalone because release flows strip external file references and ship
  the text embedded. The base DATs carry NO Embody tag or tsv row (an
  Embody-tracked DAT identity on a much-copied module is how the tracker
  once adopted a stray copy and dragged files away). PaneTypeRegistry
  additionally distributes via the TD Palette, and is tracked exactly like
  the others: a `pi_suspect` with its own
  `modules/suspects/PreviewPanel25/PaneTypeRegistry.tox` plus a
  `pre_release` hook. **No unbind-save-rebind dance** (the older rule) —
  the dev copy KEEPS its file bindings so edits hot-reload, and
  `pre_release` strips file/syncfile + tracker tags off every bound DAT at
  release time, so only the shipped artifact is standalone. That is exactly
  what the hook is for; a save is just `comp.save(externaltox)`.
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
- **The host lives INSIDE the component it registers** (`Comp='..'`), for
  chrome exactly like for tools: `widgets/gridshow/ToolbarRegistry`,
  `containers/parent_hierarchy/NavbarRegistry`, drop-to-register stamps --
  one shape everywhere, and any single widget dragged into a foreign
  project self-registers. Requires the component to COOK (a host inside a
  cook-disabled subtree cannot compile its extension -- un-park sources,
  guard any `panelParent()` sizing exprs with `... if me.panelParent()
  else N`).
- **Every registered tool gets a standardized `Registry` custom page,
  created PROGRAMMATICALLY by the host** on each successful registration
  (`RegistryBase._ensureToolRegistryPage`): key Registration pars mirrored
  on the parent tool (Auto-Register, Register, Status, Order, Displayed +
  per-surface extras like the navbar's Side or the toolbar's Bar Width).
  **The TOOL pars are the bind MASTERS** -- they hold and persist the
  values with the tool -- and the host's Registration pars BIND to them
  (new tool pars are seeded from the host's current values before the host
  is bound, so nothing snaps to defaults). Par names carry a per-registry
  prefix (`Tb`/`Nb`/`Pt`) so a tool with multiple registries
  (CustomParPromoter has toolbar + navbar) shares the one page without
  collisions. The page is kept ORDERED ahead of the meta pages
  (`sortCustomPages`: tool pages first, then Registry, then About / Common /
  Version Ctrl). Promotion is OPT-OUT per host: the Registration page's
  `Promotepars` toggle (default on) -- turn it off before shipping a tool
  that should not expose registry controls; the section withdraws and the
  host pars fall back to constants with their values intact. The fleet
  self-standardizes -- no per-tool work, and drop-to-register packages
  inherit the page automatically. Two framework hazards paid for here:
  clone sync initializes a NEWLY-added master par to the TYPE default (not
  the master's value) -- sweep the fleet after appending pars to a master;
  and ExtUtils' callback exec DATs resolved CustomParHelper via
  `mod(me.dock.name)`, which cloning breaks -- par callbacks were silently
  dead on every clone host until all ExtUtils exprs AND DAT texts were
  rewritten dock-free (`mod('CustomParHelper')`). Hardening paid
  for once: `onDestroyTD` ALSO fires on extension REINIT, so the page is
  only removed when the host COMP is genuinely being destroyed
  (`not ownerComp.valid`); and `_repairDanglingHostBinds` runs BEFORE
  CustomParHelper touches the pars at init, falling dangling BINDs back to
  CONSTANT (detected via `bindMaster is None` -- a dangling PULSE bind does
  not raise on eval).
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
- **Copying ANY COMP whose subtree contains an enabled clone host crashes
  TD** — not just clone copies inside drop-event stacks. Copying
  NavbarConfigurator (which ships its clone-bound gear host) via a plain
  MCP copy hard-crashed TD 2025.33070 (mainmenu port, 2026-08-10). Before
  copying a configurator or any host-carrying package: set the inner
  host's `enablecloning=False` (and the source's `initextonstart=False` so
  the copy's extensions stay quiet), copy, then restore — wrapped in
  try/finally.

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
- **ENUMERATE nested suspects before saving — never assume you know them.**
  A `pi_suspect` at ANY depth is stored in its parent's tox as a REFERENCE
  STUB, so the parent's tox cannot carry that child's content. Saving the
  tool and forgetting a nested one loses everything added inside it at the
  next boot. Proven the hard way: an unplanned restart reverted
  `FNS_OpMenu/IOFilter` (its own suspect, tox 20 hours stale) and took its
  registry host, callbacks DAT and parexec with it — while the sibling
  `OpMenuRegistry.tox`, which HAD been saved, survived intact. The
  FNS_OpMenu + OpTemplates scope has SEVEN nested suspects; a "save the
  toxes I edited" habit covered four. Walk them and save DEEPEST-FIRST:

  ```python
  def nested_suspects(root_path):
      r = op(root_path)
      found = [o for o in [r] + r.findChildren()
               if getattr(o.par, 'externaltox', None) and o.par.externaltox.eval()
               and 'pi_suspect' in o.tags]
      return sorted(found, key=lambda o: o.path.count('/'), reverse=True)
  ```

  Only the `.tox` reverts — externalized `.py` files have their own file
  bindings and survive, which is what makes recovery cheap: recreate the
  operators, rebind them to the surviving files, re-register.
- **Same-frame verification lies.** Connector lists and par-callback
  effects read stale in the frame that mutated them — verify a destroy or
  re-anchor only after real frames pass.
- **Keep the legacy artifact until the parity audit passes.** It is the
  only authoritative record of per-tool metadata (URLs, orders, widths);
  delete it only after the diff comes back clean.
