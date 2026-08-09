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

Planned: `NavbarRegistry` (same scheme, navbar surface).

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

**Persistence model: the global table is deliberately ephemeral.** The
source of truth is the hosts: on every project open each `Autoregister`ed
host republishes. The global additionally runs a **healing watch** (every
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
  The `/sys` global stays unclonled (it is disposable). `RegistryBase.py`
  exists per-package; base fixes are applied to every master, whose `/sys`
  copies file-sync from the SAME `.py` files.
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
- **Management UI is a SEPARATE package, never inside the registry.** With
  host cloning, anything inside the registry replicates into every host and
  every tool's tox — so the registry ships only a tiny launcher (the gear
  `btn_config`, ~2 KB) while the heavyweight editor (`ToolbarConfigurator`,
  its own `modules/release/ToolbarConfigurator.tox`) is discovered at
  runtime via its `TOOLBARCONFIG` global shortcut, with a toolbar-package
  child lookup as fallback. Missing editor = a debug note, nothing breaks.

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
