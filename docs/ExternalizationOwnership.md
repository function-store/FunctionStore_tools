---
status: in-force
summary: 'The ownership rule for the file-externalization mechanisms: Private Investigator owns externalization and release; Embody is the Envoy/MCP layer, and its file rows are an editing convenience, never a registry of record. Two corrections since: the source trees do not map to the roles (2026-09-01), and 50 committed source files are bound to nothing at all because the binding lives in the package tox (2026-09-03).'
since: 2026-08-28 (owner decision; audits 2026-08-27 surfaced the ambiguity)
verified: 2026-09-03 (unbound-file count and the tox-is-the-carrier test measured against the live session)
skill: externalize-operator
---

# Externalization ownership: PI owns it, Embody is the live layer

Two mechanisms in this project write operators to files, and until now
nothing in the repo said which one *owns* an operator. Both audits tripped
over it, and one of them initially mis-measured the whole project against
the wrong registry. This document is the rule.

## The rule

**Private Investigator owns externalization.** Its suspects table is the
registry of record for what is externalized; `modules/suspects/` is the
canonical export tree (162 `.tox`, 63 `.py` at time of writing, ~438
suspects); the release flow — the Pkg column, the per-package publish —
rides it. A package's shippable identity IS its PI suspect tox.

**Embody owns nothing but the Envoy/MCP layer.** Its real jobs are the MCP
server, TDN snapshots and diffs, the multi-session ledger and claims, and
the logs. It *also* has a file-sync feature, and its
`externalizations.tsv` (47 rows at time of writing, 43 of them `.py` text
DATs synced in place under the tools' own folders) is where that feature
does its bookkeeping — but that table is a **working set, not an ownership
registry**. A row there means "this source DAT is hot-sync-editable on
disk right now", nothing more.

The two are layers, not rivals: PI answers *"what ships, at what version,
from which bytes?"*; Embody's rows answer *"which source files reload live
when edited?"*. A DAT with an Embody row lives inside a COMP whose
shipping is owned by PI. The seam only hurts when someone mistakes one
layer's table for the other's question — which is exactly what the
2026-08-27 audit did on its first pass.

> **Corrected 2026-09-01.** The ownership half of this stands: PI's tag is
> the answer to "is this externalized, and what ships?". What does NOT
> stand is the implied mapping from that pair of *questions* onto the pair
> of source *trees*. Measured against the live session, all three trees
> hot-sync — including PI's. See
> [the correction](#correction-20260901--the-trees-do-not-map-to-the-roles).

## What follows from it

- **Discoverability.** To know whether an operator is externalized, ask
  PI (the `pi_suspect` tag / the suspects table). An `externalizations.tsv`
  row never implies ownership, and its absence never implies "untracked".
- **One file binding per DAT.** A DAT's `file` parameter belongs to at
  most one system. Two systems pointing different paths at the same DAT is
  the FNS_PaletteRegistry bug (PI lists a suspect export that does not
  exist because the live binding is Embody's in-place path) — resolve such
  cases to one binding, never leave both standing.
- **Nothing ships from an Embody row.** Releases read PI's world plus the
  live parameters. The in-place `.py` files are *source*, reaching users
  only as the bytes baked into a PI-owned tox.
- **The split inside one component is legal** — but it is now the *pattern*,
  not an exception: **7** components carry `.py` in both trees (ColorUI,
  FNS_Toolbar, FNS_Updater, OpenExt, ParOPDrop, ResetPLS1, SwapOps).
  FNS_Updater is the standing example: `ExtUpdater` is a PI suspect exporting to
  `modules/suspects/FNSTools/FNS_Updater/ExtUpdater.py`, while `ExtAuth`,
  the auth callbacks and the `secure_storage` modules are Embody-synced in
  place under `FNSTools/FNS_Updater/`. Under this rule that is a layering,
  not a conflict — the component's shipping is PI's either way. What was
  wrong before this document was only that nothing said so.
- **New work registers with PI.** Embody in-place sync is added on top as
  an editing convenience during active development, and a row whose
  development has landed is a candidate for retirement, not a permanent
  fixture. The load-bearing exception is `scripts/shared/RegistryBase.py`
  — the clone-source DAT for every registry syncs from it, so editing that
  file *is* how RegistryBase changes reach the live session; that row
  stays for as long as the mechanism does.

## Copies carry the tag, and PI now knows a copy from a suspect

`copy()` carries every tag, so a DAT copied from a tracked one arrives as
a `pi_suspect` with the SAME `file` binding: every modulator FNS_BeatMod
deploys from its template, every registry host stamped into a scratch
widget, PI's own FNS_About. `Scan()` listed them all, and the suspects
table churned with the owner's project state (38 such rows on
2026-09-04, twenty of them `/beatmod_*/ModulatorExt`). The hazard is not
a PI save (PI writes only COMP toxes; DAT files are written by TD's own
`syncfile`), it is that the table stopped meaning "what ships".

Since 2026-09-04 `Scan()` and `ReinitSuspects()` skip a **stray copy**: a
tagged DAT with no suspect COMP among its ancestors while another tagged
DAT holds the same file. A sole holder of its file is a real suspect
wherever it lives (`/utils/remote/Tweener/extTweener`, `/Embody/updater/UpdaterExt`,
`/PresetManager/__init__` stayed), and a clone inside a suspect COMP (a
tool's ExtUtils) is that tool's business, listed as before. FNS_BeatMod
also strips the tracking tags from what it deploys (`_untrack`), so a
modulator is clean in any project. `ReinitSuspects` mattered most: it
re-`Add`s every listed op, and `Add` derives a fresh `file` from the op's
own path and saves there, so on a copy it would have created a new file
and cut the copy's link to the template.

## Known seams, still open

- **FNS_PaletteRegistry double claim** — its extension DATs are both PI
  suspects and Embody rows, with the live `file` par on the Embody path,
  so PI lists an export it does not own. Resolve to one binding.
- **PI cannot see itself.** PI is not a `pi_suspect`; it reloads from
  `modules/suspects/private_investigator1_withmyhacks.tox` on open, and
  its own lister never shows it dirty — the publish UI silently vanished
  once already (2026-08-14; `scripts/pi_publish_ui.py` exists solely to
  re-stamp it). The tracker is the one thing nothing tracks.
- **One Embody row pointed into PI's tree** (`/PreviewPanel25` →
  `modules/suspects/PreviewPanel25.tox`) — a cross-system binding that
  predated this rule. Folded 2026-09-02: the tool moved under `/FNSTools`
  as the `FNS_PreviewPanel` package, PI owns its root, nested panel and
  extension DATs, and the Embody row is gone (`CoreToolsBacklog.md` §20).

## Correction 2026-09-01 — the trees do not map to the roles

The rule above was written to settle a real confusion and its ownership
half still governs: **ask PI's `pi_suspect` tag** to know whether an
operator is externalized and what ships. Measuring the second half against
the live session, it does not hold.

**Every tree hot-syncs, PI's included.** Counting live DATs whose `file`
par points at a `.py` with `syncfile` on:

    scripts/           1,782 bindings    20 distinct files
    modules/suspects/    474 bindings    56 distinct files
    FNSTools/            464 bindings    70 distinct files

`modules/suspects/FNSTools/QuickExt/ExtUtils/CustomParHelper.py` is the
clearest case: it lives in the tree this document calls PI's canonical
export tree, *and* it is the hot-sync source for 151 hosts — which is
exactly how backlog item 12 delivered a fix to all of them. So the
boundary does not separate "what ships" from "what reloads live". Both
trees do both.

**A row is neither necessary nor sufficient for hot-sync.** 31 of the 91
`.py` files under `FNSTools/` have no `externalizations.tsv` row, and
several of them (the registry `*RegistryExt.py` files) hot-synced fine
during item 12's work. The table is a partial working set, not the
working set.

**What the split does earn.** One axis is real, and this document
undersells it: `scripts/` holds sources shared by *many* components —
`RegistryBase.py`, the QuickExt `ExtUtils/CustomParHelper/*` templates.
Twenty files carrying 1,782 bindings. A file belonging to no single
component genuinely needs a home outside every component's folder, and
editing one is how a fix reaches ~102 hosts at once. The rule names only
`RegistryBase.py` as a "load-bearing exception"; it is a category of
twenty.

`modules/suspects/` versus `FNSTools/` is the pair with no work to do.
Both are per-component, both mirror the network tree, both hot-sync, and a
file's location tells a reader nothing the `pi_suspect` tag does not. No
file exists at the same relative path in both trees, so this is disorder
rather than duplication.

**The revised rule.** Sort by *shared vs per-component*, which is the
distinction that does work — not by which mechanism happened to write the
file first:

    modules/suspects/<component>/…   everything one component owns
    scripts/shared/ + templates/     sources many components share

Retiring `FNSTools/*.py` into the first is tracked as backlog item 13
(~70 files, 464 live `file` pars to rewrite; worktree work, per-component
rather than one sweep).


## Correction 2026-09-03 — the tox is the carrier, and 50 files are bound to nothing

The 2026-09-01 pass counted bindings and found all three trees hot-sync.
It did not count the files with **no** binding. There are 50 of them
under `modules/suspects/FNSTools/`, all committed, all read by humans as
source, and none of them connected to the live session in either
direction. Nothing reloads them into TD when the file changes, and
nothing writes them when the DAT changes.

**Three mechanisms bind a DAT to a file, and these are in none of them:**

| Mechanism | Marker | Example |
|---|---|---|
| PI suspect (`PrivateInvestigator.Add`) | tag `pi_suspect`, `file` + `syncfile` | `FNSCommandRegistryExt` |
| VSCodeTools ScriptSyncFile | tag `FNS_externalized`, `file` + `syncfile` | `HotkeyManagerExt` |
| Embody row (`externalizations.tsv`, 14 rows) | a row, `file` + `syncfile` | `FNS_TimelineTools/FNS_Waveform/WaveformExt` |
| **none** | no tag, `file` empty, `syncfile` off | `ConfigRegistryExt`, `console_page`, 48 more |

**Where the state actually lives: the package tox.** Loading a suspect
tox in isolation settles it. `FNS_CommandRegistry.tox` hands back its ext
DAT with `file = modules/suspects/.../FNSCommandRegistryExt.py` and
`syncfile` on; `FNS_ConfigRegistry.tox` hands back `file = ''`. Every
package root carries `externaltox`, so TD re-imports the tox on project
open and the tox's answer wins. A binding set in a live session survives
only if `PrivateInvestigator.Save` re-exports the tox afterwards. That is
why the 2026-09-01 repoint of 470 pars did not stick for these packages:
their toxes were not re-exported with it.

**It has already cost a shipped feature.** Commit `8a280ae1` added the
`self-managed` update state to
`modules/suspects/FNSTools/FNS_Console/console_page.html` and did not
touch `FNS_Console.tox`. With no binding, the edit never reached the live
DAT and never reached the shipped tox, so for two days the repo showed
code that the product did not run. It was found on 2026-09-03 by
comparing DAT text against disk before an unrelated edit, and pasted in
by hand. `FNS_PaletteRegistry`'s two files are drifted the same way right
now, which is the "known seam" already listed above, measured.

**The fix is the binding, not `PI.Add`.** Adding these as PI suspects
today would do two unwanted things: `dat_externalizer.Init` builds its
path from PI's `Folder` par, still `modules`, so it would write to
`modules/FNSTools/...` beside the real tree; and `dat_versionmanager.Init`
stamps an Info Header, which was retired on 2026-08-31. The correct
operation is the one the retire commit used: set `file`, `loadonstart`
and `syncfile` on the DAT, then `PrivateInvestigator.Save` the package
root so the tox carries it. Binding a shared template DAT is safe: the
registries already clear `file`/`syncfile`/`loadonstart`/`write` on every
stamped host copy, so a copy cannot save over its master.

**Swept 2026-09-03. All 50 are bound, and 18 package toxes carry it.**
FNS_Console (4 DATs) and FNS_ConfigRegistry (3) first, then the other 43
across ColorUI, FNS_Autosave, FNS_Collect, FNS_Hub and its four
configurators, FNS_HubRegistry, FNS_MediaBrowser, FNS_PaletteRegistry,
FNS_Remote, FNS_TimelineRegistry, FNS_TimelineTools and
FNS_TimelineBackground, FNS_ToolbarRegistry, FNS_Updater. Nested toxes
were saved before their parents, since a child with its own `externaltox`
reloads from it and would otherwise overwrite what the parent restored.
Verified by loading three toxes in isolation in `/sys/quiet` (the nested
ToolbarConfigurator, FNS_Updater, and the previously drifted
FNS_PaletteRegistry) and re-measuring the whole project: **2,979 live
file bindings, 0 drifted, 0 unbound.**

Two content questions came out of it. The `FNS_PaletteRegistry` pair
differed from disk only by the frozen `Info Header` block, so the disk
side was loaded into the DATs rather than the reverse: the header is
history and is not edited. And `/FNSTools/CustomParTools/QuickExt/ExtTest`
carried a UTF-8-read-as-cp1252 mojibake in a comment that its file did not,
which would have propagated into every extension made from the template;
the file was reloaded over it.

**A BOM is not drift, and it is not an encoding hazard either.** 61 of
the 288 source files start with a UTF-8 BOM, because that is what TD
writes when it saves a DAT to a file, and it strips the BOM again when
it loads one. Any live-vs-disk comparison has to `lstrip('﻿')`
first, or it reports every one of those files as drifted along with all
their clone copies; a first pass here counted 375 false positives that
way. The follow-on worry, that TD might mis-decode the BOM-less files as
cp1252 and mangle their non-ASCII characters, was measured and is
unfounded: a probe Text DAT pointed at the same content with and without
a BOM, by absolute path and by project-relative path, returned correct
UTF-8 every time. Six BOM-less source files carry non-ASCII, including
`console_page.html` with 101 characters, and all six are clean live.


## Sources

- 2026-08-27 audits (W-02 as corrected; the infrastructure audit's
  "code you can and can't read" section)
- `scripts/pi_publish_ui.py` header — the PI self-tracking incident
- `/externalize-operator` — the how-to for Embody's mechanism (per the
  project rule: how-to in the skill, reasoning here)
