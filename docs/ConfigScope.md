---
status: in-force
summary: 'The Config Scope parameter: whether the toolkit''s persisted settings roam machine-globally or stay pinned to the project.'
since: 33b955d 2026-08-21
verified: 2026-08-21 — live gate tests on save/load both directions; cold-boot pass still manual
skill: fns-config-scope
---

# Config Scope: Global vs Project

> **STATUS (2026-08-21): LANDED + VERIFIED** (live gate tests on save/load both
> directions; cold-boot pass still manual).

One menu parameter — **`Config Scope` (`Configscope`) on the `/FNSTools`
toolkit root** ('FNSTools' page) — decides where the toolkit's persisted
settings AND bar layouts live. The root par is the authored record; the
`FNS_ConfigRegistry` master's and `/sys` global's own `Configscope` pars
BIND to it (`op.FNS.par.Configscope`, two-way — edit any of the three).
The scope choice itself never roams: both hosts that snapshot the root
(`FNS_ConfigHost` → canonical `FNS`, and the master → `FNS_Config`) carry
`Excludepars = 'Configscope'`, so a roamed section can never overwrite a
project's scope declaration. A rootless/standalone registry deploy falls
back to its own constant par (`_scopeIsProject` tries own par, then
`op.FNS`, then defaults global).

- **`global`** (default): current behavior. Everything roams through the one
  aggregated JSON in the user palette
  (`<userPaletteFolder>/FNStools_ext/config/FNStools_config.json`), shared by
  every project on the machine. Last save wins across projects.
- **`project`**: the roaming file is **never read and never written**. The
  .toe is the whole store — and it already is one: host Registration pars
  (order/show/width/side per tool), the configurators' `state` tables
  (dividers, groups, built-ins), and every tool's custom pars all boot from
  the project itself, *before* any config payload would land. Project scope
  simply stops the JSON from overwriting them. The config travels with the
  project file, with no sidecar.

## Design decisions

- **Project scope means no JSON at all**, not a project-local JSON. A sidecar
  file gets orphaned the moment someone copies just the .toe; the .toe route
  is self-contained. (`Configfile` remains as the advanced override for those
  who explicitly want a relocatable/diffable JSON.)
- **Save triggers still run every tool's `onConfigSave` under project scope**
  — only the file I/O is gated. This is load-bearing: the configurators'
  `SnapshotState()` freshens their state-table group rows there (see
  docs/ConfiguratorPersistenceFixes.md Fix B), so a bar-side eye toggle still
  reaches the .toe before TD's pre-save. Verified live.
- **A project that opts out also stops clobbering the shared layout** — the
  cross-project last-writer-wins problem disappears for that project.
- **Missing par reads as global** (`_scopeIsProject` uses getattr), so stale
  promoted copies predating the par behave exactly as before.

## Flip semantics

- **Global → Project**: nothing to migrate. The .toe already holds current
  state; the shared JSON keeps its sections for other projects (read-merge-
  write preserves them).
- **Project → Global**: the next save **overwrites the shared layout with
  this project's state** (normal last-writer-wins) — so an interactive flip
  pops a confirmation dialog (TDResources PopDialog, non-blocking):
  **Push to Global** (write this project's state to the file now),
  **Adopt Global** (`LoadAll` the shared config onto this project instead),
  or **Stay Project** (cancel — the par flips back). Flipping to `project`
  stays silent (nothing is at risk); every flip logs one fnsLog line.
  Programmatic flips use `SetConfigScope('global'|'project', prompt=False)`
  (promoted; callable on any copy, routes to the master) — quiet by
  default so scripts, tests, and the future updater handoff never pop UI.

## Per-tool escape hatches (unchanged)

`Autoload` off (tool ignores the roamed section), `Excludepars` /
`Excludepages` (pars that never roam — e.g. excluding the `Registry` page
keeps a tool's bar position out of the file while its settings still roam).
Under project scope these are moot (nothing loads).

## Updater rework note (IMPORTANT)

The planned UPDATER uses the config file as its save-before-replace /
restore-after-replace handoff. Under project scope **both directions are
gated**, so the tool-replacement flow must carry sections itself: either its
own snapshot/apply around the swap, or temporarily forcing scope global with
a temp `Configfile` for the duration. Flagged in the class docstring of
`ConfigRegistryExt.py` and in the task ledger for the packaging track.

## Implementation

All in `FNSTools/FNS_ConfigRegistry/ConfigRegistryExt.py` (externalized,
hot-synced to both master and `/sys` global): `_scopeIsProject()` helper +
gates in `SaveAll` (snapshot loop still runs, file skipped), `SaveTool`
(same), and `_applyToolConfig` (single choke point for `LoadTool`, `LoadAll`,
and the deferred registration-time apply; logs the skip once per session).
The confirm dialog: `configscope_parexec` (Parameter Execute DAT in the
master, OPs `../..` = the root, filtered to `Configscope`) → thin callback →
`ConfigScopeChanged` / `_onScopeDialog` / `SetConfigScope` in the ext. Its
Active par is an expression arming it only on the in-project master, and the
handler guards again (`_isRootMaster`) — clone hosts and the `/sys` copy
stay inert even if cloning propagates the DAT to them.
