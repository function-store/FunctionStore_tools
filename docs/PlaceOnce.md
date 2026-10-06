---
status: in-force
summary: A `placeonce` package's picker card, and every FNS family member's, offers Place beside the tick. A placed tool lands and updates in this project like any other, but its install record says remember = 0, so "Set up like last time" never carries it into the next project.
since: unreleased 2026-09-24
---

# Place once

**The problem.** Ticking a tool in the picker makes it part of the
project's setup. The toolkit root copies the `installed` table into the
machine's `last_install` record on every save, and a fresh project offers
"Set up like last time" from that record, or applies it unasked when the
root's Always Set Up Like Last Time toggle is on. For most tools that is
the point. For some it is not: a hardware integration (ParHoverMIDI_VSN1),
a tool for one kind of project (TDXMap), an FNS family operator you want
dropped into one network. Ticked once, those arrive in every new project.
`nopick` keeps them out of bulk selections, but a tick the user made still
counts as setup.

**The answer.** A package the catalog flags `placeonce: true` gets a second
action on its picker card: **place in this project only**. The tick keeps
its meaning, so a user who does want the tool every time still ticks it.

## What each action does

| | Ticked | Placed |
|---|---|---|
| Lands in this project | yes | yes |
| Updated by the updater | yes | yes |
| `installed` row, `remember` | `1` | `0` |
| In `last_install`, so in "Set up like last time" | yes | no |
| Card on the next picker open | ticked | "placed here · undo" |

A tool both ticked and placed is simply ticked. Ticking a placed tool
promotes it to part of the setup without reloading it. An FNS family member
(placement `none`, which normally installs as a record only) is spawned into
the network you are working in when placed, the way the OP Create dialog
would drop it.

## The data

- **Catalog**: `placeonce: true` or absent, like `nopick`. Preflight
  (`build_manifest.CatalogProblems`) refuses any other value; the manifest
  carries only `true`. Set it in the CMS package editor ("Place once").
- **Selection** (`selection.json`, posted by the picker): a `place` list
  beside `tools`. The served picker always writes the key, even empty, so
  it is the whole placed set: a placed tool left out of it is removed on
  Apply, the same way an unticked tool is. **A selection without the key**
  (Set up like last time, a pasted setup, the site's static picker, any
  older writer) knows nothing about placed tools, so `ResolvePlan` keeps
  them as they are.
- **Install record**: the root's `installed` table gains a fifth column,
  `remember`. `1` or empty is part of the setup (every row written before
  the column existed reads empty and so stays exactly what it was), `0` is
  placed-only. `RecordInstalled` grows the column on an older table, and an
  update pass (which passes no `remember`) never changes it.
- **Root save** (`build_installer.CONFIG_CALLBACKS_TEXT`): `last_install`
  skips `remember == "0"` rows.
- **Picker feed** (`GET /manifest.js`): `FNS_INSTALLED` excludes placed-only
  tools, and `FNS_PLACED` lists them, so the page never pre-ticks one.

## Decided (owner, 2026-09-24)

1. Place is opt-in per package (the catalog flag), not on every card.
2. A tick made on another machine is honoured: its `last_install` still
   carries the tool, because that tick was deliberate.
3. A placed FNS family member spawns into the current network.
4. Every FNS family member gets the Place button without the flag: a
   family operator is dropped into networks as often as you like, so it
   should never have to join the setup to be used once. The installer
   already places any tool the `place` list names; the page is the only
   gate (`placeable()` in the picker).
5. "Place once" named the action, not the kind of tool. The picker's
   filter is **Placeable**: tools dropped into a network as nodes (a
   family member, a pane or root spawn, or a `placeonce` package), as
   opposed to services living in the toolkit container. The catalog key
   keeps its name; the CMS checkbox reads "Can be placed without joining
   the setup".

## Fixed on the way

`Install()` ran `RemoveTools` only when the plan had a child COMP to remove
(`to_remove`). A removal that is only an un-record (an unticked family
member or pane component, and now an unplaced tool) was silently skipped
and its record stayed, so the picker kept showing it installed. It now runs
for `to_unrecord` too.
