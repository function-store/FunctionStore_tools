---
status: landed
summary: Spec and verification record for the configurator layout-persistence defects across Toolbar, Navbar and MainMenu.
since: 61748d9 2026-08-21
verified: 2026-08-21 — all three surfaces live via MCP, cold-boot checked; §5.3 dormant-group regression still manual
---

# Configurator Layout Persistence Fixes (Toolbar / Navbar / MainMenu)

> **STATUS (2026-08-21): LANDED + VERIFIED.** All three surfaces, live-tree via
> MCP, project saved. Fix A as spec'd (anchor refresh in `PushSequence`, empty-span
> guard in `_writeMarkerState`); Fix B via promoted `SnapshotState()` that
> `_writeState`s every LIVE group row from `GroupVisible()` (also creates rows for
> groups only ever toggled bar-side); Fix C annotated on `_retireDroppedDividers`.
> Verified live: Navbar anchor re-derivation on member move-out, bar-side toggle
> roams through snapshot, Toolbar `SnapshotState→RestoreState` round-trip
> byte-identical, all 3 `onConfigSave` paths run. Still manual: cold-boot pass and
> the uninstall/reinstall dormant-group regression (§5.3).

Spec for fixing the two real defects in configurator layout persistence, plus
one decision point and one documentation item. Grounded in a full read of the
live `ToolbarConfigurator/ConfiguratorExt`, the surface `config_callbacks`
DATs, and `scripts/shared/RegistryBase.py` (2026-08-20).

## 0. Revised problem statement

The original hypothesis — "uninstalling a tool erodes the roamed layout on the
next SaveAll" — is **mostly wrong**, and this spec does not fix it:

- `onConfigSave` snapshots the **state table**, not the live registry, so what
  roams is the authored layout.
- `_republishGroupMarkers` retains rows whose anchor entry isn't registered
  (`pending = True; continue`, retried 6×60f, rows never deleted) — an
  uninstalled anchor makes a group *dormant*, not lost. Reinstall revives it.

The two genuine defects are narrower:

**A — stale anchors (real bug, affects plain boots too).** Bracket positions
restore by anchor entry *name* (`_writeMarkerState`: anchor = first/last
non-marker member). But `_writeMarkerState` is called **only from
`GroupSelected`** (group creation). Every subsequent drag-reorder goes
`TreeMoveRows → PushSequence`, which persists only `order` for owned rows and
never re-derives anchors. So after any reorder that moves entries into/out of
a bracket's span, the next boot or restore re-inserts the brackets beside the
*original* anchors and the group wraps the wrong run of entries. This corrupts
layout on the same machine — no roaming required.

**B — group-visibility dual record (real bug).** Two write paths exist:

- Configurator eye (`ToggleShow` on a groupstart row): calls
  `api.ToggleGroup(gid)` **and** `_writeState('group', gid, display=…)` —
  both records updated.
- Bar-side eye button (`GROUP_TOGGLE_CALLBACK_TEMPLATE`,
  RegistryBase.py:1515): calls `op.<SHORTCUT>.ToggleGroup(gid)` directly →
  writes only RegistryBase `GroupVisibility` storage + `_syncSurface()`. The
  configurator's `kind='group'` state row goes stale.

Result: toggle from the bar → SaveAll roams the stale value → next
boot/restore (which applies visibility *from the state rows*) resurrects the
pre-toggle state, even on the same machine.

**C — restore retirement asymmetry (minor).** `RestoreState` retires only
dividers (`_retireDroppedDividers`). Builtins absent from an incoming table
keep their current overrides rather than resetting to TD defaults. Low
impact; fix or explicitly accept (see §3).

**D — scope semantics (document, don't fix).** `RestoreState` is a wholesale
REPLACE, and the config JSON is machine-global: last writer wins per surface
across projects. This is by design; it belongs in the Scope & Persistence
doc, not in code.

## 1. Fix A — re-derive anchors on every sequence change

**Where:** `PushSequence(names)` in each ConfiguratorExt.

**Change:** after `SetWidgetSequence` succeeds and the per-row `order`
write-back completes, iterate the live groups and call
`_writeMarkerState(api, gid)` for each — re-deriving `anchor` (and `order`
for the marker rows) from the *new* live sequence. `_writeMarkerState`
already contains the exact derivation logic; the fix is calling it at the
right time, not new logic.

**Edge cases:**

- A group whose members were all dragged out: `_writeMarkerState` should
  degrade gracefully (skip the write, leave the existing spec so the
  dormant-group contract holds) rather than writing empty anchors. Verify
  current behavior with an empty span; guard if needed.
- Dormant groups (anchor not currently registered) must be **skipped**, not
  rewritten — they're not in the live sequence, so re-derivation would
  destroy the spec that lets them revive.
- `TreeMoveRows` regroup-on-drop already rewrites membership positionally
  before calling `PushSequence`, so ordering the anchor refresh *after* the
  sequence push covers both plain reorders and drop-regroups with one call
  site.

## 2. Fix B — single source of truth for group visibility at snapshot time

Rather than making the bar-side callback reach into the configurator (adds
coupling, and the registry shouldn't know the configurator exists), invert
it: **derive the `kind='group'` rows from the live registry at save time.**

**Where:** `onConfigSave` in each surface's `config_callbacks` DAT — via a
promoted method on the ConfiguratorExt (e.g. `SnapshotState()`) that
`onConfigSave` calls, so the logic lands in the extension (3 copies) and the
callbacks stay thin.

**Change:** before dumping the table, refresh every `kind='group'` row's
`display` from `api.GroupVisible(gid)` (RegistryBase storage is the live
truth — both toggle paths write it). Dormant groups keep their stored row
untouched (registry has no live record for them).

No refresh at `_writeState` time is needed — snapshot-time derivation makes
the state row eventually-consistent at exactly the moments that matter
(SaveAll, project pre-save, UPDATER-guarded save). `ToggleShow`'s existing
dual write becomes harmless redundancy; keep it so the configurator UI
reflects immediately.

## 3. C — decision point

Either extend `RestoreState` to reset builtins absent from the incoming table
to TD defaults (symmetric with divider retirement), or annotate
`_retireDroppedDividers` with a one-line comment accepting the asymmetry.
**Recommendation: the annotation** — builtin overrides are cheap to re-clear
manually and a reset pass risks fighting `_applyBuiltinOverrides` ordering.

## 4. Landing plan

- **Three sibling copies**: ToolbarConfigurator, NavbarConfigurator,
  MainMenuConfigurator ConfiguratorExts — every change lands 3×, adapted for
  the navbar/mainmenu `side` column and `_decorateRestoredMarker`. Neither
  fix touches the `side` mechanics, so the ports should be near-verbatim.
- **`config_callbacks` contract unchanged** with Fix B as a promoted
  `SnapshotState()` — `onConfigSave` swaps its table-dump line for the call
  (3 thin DAT edits). Schema stays 1; header row still travels.
- **RegistryBase untouched.** `GroupVisible()` already exists as the read API
  (verify exact promoted name before coding).
- Land live-tree file-by-file per worktree-td-safety: sole-writer check
  first (`get_sessions`), claim `file:` scopes on the three ConfiguratorExt
  files before editing.

## 5. Verification plan

1. **Anchor refresh:** create a group → drag entries so the group's
   first/last member changes → restart TD (or `RestoreState` round-trip) →
   brackets must wrap the post-drag run. Repeat with a drop-regroup via
   `TreeMoveRows`.
2. **Bar-side visibility roams:** toggle a group from the bar eye-button →
   `SaveAll` → inspect `FNStools_config.json` group row `display` → matches →
   restart → visibility persists.
3. **Dormant-group regression:** uninstall a tool holding a group anchor →
   SaveAll → reinstall → group revives with correct span and visibility
   (proves Fix A's skip-dormant guard and Fix B's leave-dormant-rows-alone).
4. **Divider retirement regression:** `RestoreState` with a table missing a
   divider still retires it.
5. All three surfaces, since the exts are copies — at minimum a full pass on
   Toolbar, spot-check anchor+visibility on Navbar (has a live `group` row:
   `G1`) and MainMenu.
6. Known test trap from the config port: sequence-wrecking tests write back
   `Menuorder` to tool host pars — restore the baseline sequence after each
   test or the bars stay shuffled.

## Size estimate

~30–40 lines of extension changes ×3 copies + 3 one-line callback edits.
