---
status: open
summary: Follow-ups the FNS_Hub build left open -- retire tools_ui (the last scanner) into hub tabs, an OpMenu configurator tab, a ConfiguratorBase extraction, and two hand tests.
since: 2026-08-23 (FNS_Hub landed; see HubContract.md)
skill: fns-registry
---

# FNS_Hub -- open follow-ups

What the hub build ([HubContract.md](HubContract.md), memory `fns-hub-decision`)
deliberately did not do. None of these are blocked; they are ordered by value.

## 1. Retire `tools_ui` into hub tabs -- DONE 2026-08-23

`tools_ui` (the `Fx` toolbar panel, the toolkit's last scanner) is gone. Its
six tab tools carry `FNS_HubRegistry` hosts (orders 100-150, after the
registry tabs and the console): oscMapper, ExprHotStrings, GlobalOutSelect,
midiMapper and ColorUI as mirrored root panels (sized by `w`/`h` expressions
on the hub's tab area, old tools_ui size as the no-hub fallback), FNS_OpMenu's
`OpSearchWords` as an `opviewer` tab. The `Uitab*` pars, the `Fx` toolbar
button (toolbar canonical `FNS`), the `MY_UI` shortcut and the manifest's
`Uitab` surface derivation went with it. Ported into the hub: right-click a
tab opens the owning tool's parameters (`HubExt.OpenTabParameters`), and a
tool carrying a `Refresh` pulse is pulsed on show. One bar of ten tabs, by
inspection, is fine.

## 2. An OpMenu configurator tab

`RegistryScheme.md` has called it "a natural next step" since the OpMenu port:
enable/disable and reorder contributions (`Contributors`,
`SetContributorOrder`, `SetContributorDisplay` already exist on the manager).
Build it as a fourth configurator inside the hub -- copy NavbarConfigurator
(the closest: side-less, no dividers), strip to Name / Show / Origin, register
as tab `opmenu`, order 40, own PI suspect tox under
`modules/suspects/FNSTools/FNS_Hub/`.

## 3. `ConfiguratorBase` extraction -- DONE 2026-08-23

[FNSTools/FNS_Hub/ConfiguratorBase.py](../FNSTools/FNS_Hub/ConfiguratorBase.py)
is the one implementation (state table, adoption, groups, tree lister,
restore, drop-to-register); each configurator's `ConfiguratorExt` is a thin
subclass next to it (`mod('../ConfiguratorBase')`) -- a surface description
in class attributes (`HAS_SIDES`, `HAS_KINDS`, `HAS_DIVIDERS`, `HAS_WIDTH`,
`HAS_GROUPS`, `SUPPORTS_DROP`, `ADOPTS_BUILTINS`, adoption filter flags,
`STAMP_EXTRA_PARS`, `DEFAULT_STATE`) plus the adoption hooks
(`_adoptCandidates` / `_adoptCall` / `_seedFirstAdoption`; MainMenu overrides
`_adoptBuiltins` for its position snapshot). All four DATs are externalized.
Verified live on all three: tree tables row-identical before/after, reorder
through the tree path, show toggle, Snapshot/Restore round trip. One
deliberate change: the hidden flat `entries` table no longer pre-lists
un-adopted stock items (the tree does, after the managed run).

## 3b. Tab bar: drag-to-reorder in Rows style -- DONE 2026-08-23

Both styles reorder by drag now: the Strip through TD's widget, the Rows bar
through `tabbar/dragdrop_callbacks` (modern Drag/Drop callbacks on every tab
textCOMP -- drag a tab onto another tab to move it there). Both land on
`OnTabReorder(fromIndex, toIndex)` and the roaming `Tab User Order` par.

## 4. Hand tests still outstanding

- Real right-click and real drag-drop on the **FNS** main-menu button (its
  Select mirror). The callback paths are verified through MCP; the physical
  gesture is not.
- `FirstRunNudgePlan.md` (open) points new users at "the Configurator" -- when
  it is built, it should point at the hub.

## 5. Small debts noticed, not taken

- `FNS_Toolbar` still carries legacy root pars (`Install`, `Layoutstart`,
  `Open`, `Resetdefs`) from the monolith era; `Open` is handled by nothing.
- The root `webBrowser`'s *Render Only While Viewer/Window Open* watchers are
  off for the hub's sake; in the pre-core install rail (no hub yet) the
  browser stays Active after its viewer closes until the hub lands.
- Fleet-wide: every ExtUtils clone's `FNSCommand` DAT file-syncs to the
  QuickExt master's `.py`; that file had been deleted on disk by move
  detection (restored from git 2026-08-23). If it vanishes again, that is
  the mechanism in [custompartools-merge memory] -- restore, don't re-tag.
