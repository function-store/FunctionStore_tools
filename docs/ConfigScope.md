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
`FNS_ConfigRegistry` master's, the `/sys` global's and every stamped host's
own `Configscope` par FOLLOWS it through a guarded expression,
`op.FNS.par.Configscope if hasattr(op, 'FNS') else 'project'`. Authoring
happens on the root (the hub's tab, `SetConfigScope`, which writes the
root); the followers read.

**Why an expression and not a bind (corrected 2026-09-08).** They used to
BIND to `op.FNS.par.Configscope`, two-way. The owner caught the failure
mode on a standalone tool release: without the toolkit root the bind
dangles. Measured on a scratch parameter: a dangling bind does not raise,
it errors on the COMP and evaluates to an empty string, so
`_scopeIsProject`'s "try own par, then the root" never fell through and the
tool read `global` and reached for the roaming file. A bind carrying the
guard (`... else 1`) evaluates empty just the same, because its `else`
branch is a number, not a parameter, and a bind needs a parameter. The
guarded EXPRESSION is the form that works: with the root it reads the
root's value, without it `project`, the right default for a tool on its
own (no shared roaming without the toolkit). The master's par is what a
stamp copies, so every future host carries the guard; the eight live ones
were converted in place.

**Every host carries the par (2026-09-08).** The owner expected more than
eight, since every tool carries a config host, and was right: 46 hosts,
of which 40 had no `Configscope` at all. They were stamped before the par
existed, and cloning never fixes that: a clone forces a COMP's CHILDREN
(the ext DATs), never the COMP's own parameters, so the par reached only
hosts stamped or re-stamped after 2026-08-21. A host without it fell
through `_scopeIsProject` to the root, which without a root reads
GLOBAL, the opposite of the guarded default. All 40 got the par (page
`Config`, order -0.5, the guarded expression), so a standalone release of
any tool reads `project`. Safe for the roaming rail: `_snapshotPars`
walks the TOOL's custom pars, never the host's own, and the two hosts
whose tool is the root already exclude it.

**Healed on init, audited before a release (2026-09-08).** The hand sweep
above is the last one: `ConfigRegistryExt._ensureScopePar()` runs from
`onInitTD` on every copy (master, global, host) and adds the par when
missing or rewrites a bind or an unguarded expression into the guarded
one; a CONSTANT is left alone, because `SetConfigScope` writes one on a
standalone tool and that is the user's choice. `ScopeAudit()` on any copy
returns `[(path, 'missing' | 'bind' | 'unguarded')]` over the toolkit
root's tree and the `/sys` home (which `findChildren` from the root never
sees); empty is the invariant. Verified by destroying a host's par and
reinitialising it: the par came back guarded, and the audit read empty.

The scope choice itself never roams: both hosts that snapshot the root
(`FNS_ConfigHost` → canonical `FNS`, and the master → `FNS_Config`) carry
`Excludepars = 'Configscope'`, so a roamed section can never overwrite a
project's scope declaration.

- **`global`** (default): current behavior. Everything roams through the one
  aggregated JSON in the user palette
  (`<userPaletteFolder>/FNSTools/config/FNStools_config.json`), shared by
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

## A separate file for the development checkout

The toolkit's author also uses FNSTools in ordinary projects. Under global
scope the development project and every user project share one file, and
the last save wins, so dev settings roamed into real work and back (owner,
2026-09-30).

The development project therefore points its FNS_ConfigRegistry master's
`Configfile` at `FNStools_config.dev.json`, beside the normal file in
`<palette>/FNSTools/config/`. It is set as an expression on
`app.userPaletteFolder`, so the same value resolves on any machine instead
of baking one computer's path into a tracked tox. Promotion carries it to the
`/sys` global, which is the copy that reads it.

Two things this is careful about:

- **Project scope was the obvious answer and the wrong one.** It stores
  settings in each package's own pars and state tables. In the development
  project those are exactly the bytes that get exported, so the author's
  layout would ship. A separate global file keeps the packages clean.
- **The override must never ship.** In FNS_ConfigRegistry it would move
  every user's settings into a file named for a development setup, and
  `StampHost` copies the master, so a host stamped inside the dev project
  would carry the path into whichever package received it.
  `packaging/pre_release_common.py` resets every `Configfile` to its empty
  default on the staged copy of every package, walking the whole subtree.
  Pinned by `tests/test_config_dev_file.py`.

The dev file was seeded as a byte copy of the shared file on the day it was
introduced, so neither side lost its state; the two diverge from there.

### The template library and the tables, as `_dev` twins

The same separation was extended the same day to the OpTemplates library and
every table in `tables/`. Each keeps a **twin folder** beside the shared one, named
with a `_dev` suffix, and only the development project points at it:

| What | Shared (user projects) | Development project |
|---|---|---|
| Settings JSON | `config/FNStools_config.json` | `config/FNStools_config.dev.json` |
| Template library | `OpTemplates/OPTemplates1.tox` | `OpTemplates_dev/OPTemplates1.tox` |
| Tables (hotkeys, hot strings, op search words, ResetPLS) | `tables/*.tsv` | `tables_dev/*.tsv` |

The template library matters more than it looks. An export embeds whatever
library the development project has loaded, and that becomes every user's
seed: the published `OPTemplates1` carried exactly the same 18 templates as
the dev library. With one shared file, templates saved while merely USING the
toolkit reached the dev project and shipped. The twin ends that.

OpTemplates needed a real override, the `Libraryfolder` par, because
`applyScope` rewires the base whenever its path differs from
`ExternalPathExpr()`, so a hand-set path is reverted on the next pass.
Library Scope `project` looks like the same thing and is not suitable: it
unwires the base and sends edits to a separate project library, which would
freeze the shipped seed. A redirected folder also skips adoption from the
migration's `legacy_<old name>/` keep-aside, since adoption copies the newest
candidate over the target and would replace the dev library with an old user
set.

The tables are wired two ways, and each needed its own lever:

- **Hotkeys** (FNS_HotkeyManager) are plain synced Table DATs with a `file`
  expression and nothing managing them, so the expressions were simply
  pointed at the twin. A synced Table DAT writes to whatever its `file` par
  names once repointed, never to the old file (measured on a throwaway DAT).
- **ExprHotStrings, OpSearchWords and the ResetPLS tables** belong to an
  `ExternalTables` helper vendored into each package. It finds its tables by
  the `FNS_GLOBAL_TABLE` tag and builds every path from `Folderrootexpr` and
  `Foldername`, so repointing those DATs directly would have been undone on
  its next `TableCheck`. The lever is `Foldername` = `FNSTools/tables_dev`.
  `TableCheck` CLEARS a table's `file` par when the computed file is
  missing, so the twin files were copied in before the switch; and
  `TableSave` was measured writing to the twin with the shared file
  untouched. `FNS_ResetPLS/table_except_static_const` is untagged and reads
  the same file statically, so it was repointed directly or it would have
  kept reading the shared copy while its sibling wrote the twin.

Every twin was seeded as a copy before the switch; a synced DAT pointed at a
missing file loads an empty table.

**On export**, `pre_release_common.py` rewrites any `FNSTools/<name>_dev`
back to `FNSTools/<name>` in a `file`, `externaltox`, `folder` or
`Foldername` par, on every operator in the package (the tables are DATs, so
this walks all children, not just COMPs). The match ends at a slash or the
end of the value, because `Foldername` holds a bare `FNSTools/tables_dev`,
and it leaves look-alikes such as `tables_devices` alone. OpTemplates' own
hook also clears `Libraryfolder`. Verified on real exports of all six
packages involved: no `_dev` path anywhere. `ExternalTables.PreRelease()`,
which would clear the table paths, is not called by any package hook, which
is why the rule has to cover them.

The store and the Patreon session stay shared on purpose: one machine, one
account.

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

`Autoload` off (tool ignores the roamed section), `Persistpars` off (its
pars neither roam nor load), `Excludepars` / `Excludepages` (pars that
never roam — e.g. excluding the `Registry` page keeps a tool's bar
position out of the file while its settings still roam). Under project
scope these are moot (nothing loads).

**`Autoload` off is not "do not sync".** `SaveAll` checks no autoload
flag, so an autoload-off tool still writes its section and still clobbers
the shared layout for every other project. The symmetric hatch is
`Persistpars` off. Full matrix of what each hatch gates, in both
directions, and the exceptions list of tools that stay project-local:
[ScopeAndPersistence.md](ScopeAndPersistence.md).

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
