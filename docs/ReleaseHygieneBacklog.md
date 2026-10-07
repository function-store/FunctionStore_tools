---
status: open
summary: Six items raised 2026-09-18 after the first clean-machine install — FNS_Remote ships listening, family packages spawn themselves into the user's network, two CamSequencer defects, six pre_release hooks that never run the common scrub, and a current-page rule. Every claim measured live or read out of the shipped artifact.
since: 2026-09-18 (owner raised six items after testing v3.2.37 on a clean machine)
verified: 2026-09-18 — measured in TD 2025.33070 via Envoy, and against the artifacts in packaging/dist. Probes quoted per item.
---

# Release hygiene backlog

Six items raised by the owner on 2026-09-18, immediately after the first
genuinely clean install worked (v3.2.37). They are grouped by what they are,
not by the order they were raised: three are **shipped defaults that are wrong**,
two are **defects inside FNS_CamSequencer**, and one is a **release-process rule**.

Every claim below was measured rather than reasoned about, because this whole
session established that the dev project cannot reproduce install-time
behaviour: its store holds a discovery document, its config holds the owner's
layout, and its packages carry the author's live session state.

| # | Item | Kind | State |
|---|---|---|---|
| 1 | FNS_Remote ships with `Active` on | shipped default | **fixed**, needs release |
| 2 | Family packages spawn into the user's network at install | install behaviour | **built** -- `placement: none` + palette mirror |
| 3 | CamSequencer lister: blank header in col 26 | defect | **fixed for users** (stripped at release); dev-side writer unidentified |
| 4 | CamJoyExt `run()` strings call `.ext` on the extension | defect | **fixed**, needs release |
| 5 | Six `pre_release` hooks never exec the common scrub | release process | **closed** -- 5 hooks fixed, 4 created |
| 6 | `pre_release` should set the current page to the first custom one | release process | **fixed**, needs release |

---

## 1. FNS_Remote ships listening

The shipped artifact carries the author's live value, not the declared default.
Read out of `packaging/dist/FNS_Remote.tox`:

    Active: val True, default False, mode CONSTANT

Its own help text says *"Bind the server and serve this session. Off = nothing
listens."* So installing FNS_Remote starts a phone-pairing server on that
machine without anyone asking for it. The owner wants pairing off by default.

The value is captured at export because nothing resets it: `pre_release_common.py`
already forces every `webserverDAT` to `127.0.0.1` (the blank-address rule) but
does not touch whether a tool's own switch is on.

**Fix:** FNS_Remote's `pre_release` forces `Active` to its default. The general
lesson belongs beside the existing loopback rule: *an artifact must never ship
the author's live state for anything that listens.*

## 2. Family packages place themselves down at install

All seven family members declare `placement: pane` in `catalog.json`:

    FNS_CamSequencer, FNS_MixSequencer, FNS_OpSequencer, FNS_ProSceneChanger,
    FNS_RandomCHOP, FNS_SimpleSceneChanger, FNS_SwitchTools

`placement: pane` means exactly "spawn a copy into the network the user is
working in, and track presence by the install record" (`InstallerExt` line 403
and the `ResolvePlan` branch at 454). So ticking one of these in the picker
drops an operator into the user's project.

The owner's objection: these are released **as family members**, reachable from
the FNS tab of the OP Create dialog, so the install should make them available,
not place one.

**This needs a decision before it can be built**, because removing `placement`
is not obviously right either:

- **(a) drop `placement` entirely** — the package lands as a child of the
  toolkit root like any other tool. Available, nothing spawned. But a copy then
  sits in `/FNSTools` that the user never interacts with directly.
- **(b) a new placement that places nothing** — recorded as installed, mirrored
  into the family folder, no copy anywhere. Matches "that is why we release them
  as such" most closely, and costs a new value understood by the installer, the
  picker, preflight and the catalog.

Worth noting for whichever is chosen: `FNS_Updater.SyncFamilyFolder` mirrors
members from the STORE into `FNStools_ext/family/FNS/`, so the OP Create tab
does not need an installed copy to offer the operator.

## 3. CamSequencer lister: blank header in col 26

    Exception: Blank header in col 26   (ListerExt line 704, via Refresh, via __init__)

Traced to a stored table inside the tool, not to the lister:

    /FNSTools/FNS_CamSequencer/OpSeq_cam/table_presets
    27 columns, 6 rows; header of col 26 is ''; all six cells in col 26 are ''

The chain is `table_presets` → `select2` → `inputTable` → `inputTableFinal`, and
the lister validates headers when `Inputtablehasheaders` is on, refusing a blank
one by design. So the tool ships a presets table with a stray trailing column.

**Deleting the column is NOT the fix.** Tried live: the column came straight
back on the next cook, so something regenerates it. Two further readings say
where to look:

- the stray column's header is **blank**, and there is no `Lookattarget`
  column in the table at all
- `autoColDefine` registered it under its **index**: its last column's header
  is the literal `26`, row data `['26', '*', '', 'string']`

So a column is being appended with no name, and the lister's column-define
row is then keyed by position instead of a name. The writer is in `CamSeqExt`
-- `_ensureTargetColumn` (line 345, which appends `Lookattarget` via either
`tbl.appendCol` or `inner.AddPar`) and the `eng.appendColDefinePar(c.val)`
loop near line 186, which would append a blank-named column for any blank
`c.val`. This one wants proper work inside a gated tool rather than a quick
patch, so it is left open deliberately.

## 4. CamJoyExt calls `.ext` on the extension instance

    AttributeError: 'CamJoyExt' object has no attribute 'ext'

`CamJoyExt.py` lines 122-123:

```python
run('args[0].ext.CamJoyExt.syncSurfaceRig()', self, fromOP=self.ownerComp, delayFrames=5)
run('args[0].ext.CamJoyExt.syncPickRig()',    self, fromOP=self.ownerComp, delayFrames=5)
```

`self` is the extension instance; `.ext` is an **OP** member. So `args[0].ext`
can never resolve and both deferred calls die every time they fire. It has to be
`self.ownerComp`. While there, both are missing `delayRef=op.TDResources`, which
this project requires so a delay survives a stopped timeline.

## 5. Six pre_release hooks never run the common scrub

`packaging/pre_release_common.py` is the generic strip every package's hook is
supposed to exec. Six packages have a `pre_release` that does **not**:

    FNS_CamSequencer, FNS_MixSequencer, FNS_OpSequencer,
    FNS_ProSceneChanger, FNS_SimpleSceneChanger, FNS_SwitchTools

— the recently added family tools, exactly as the owner guessed. Four more
packages have no `pre_release` at all: `FNS_OpFamily`, `FNS_RandomCHOP`,
`FNS_iopBrowser`, `FNS_ParentHierarchy`.

This is visible in what ships. Read out of `packaging/dist`:

| artifact | `Version Ctrl` page | `vc_data` tables |
|---|---|---|
| FNS_CamSequencer | present | 5 |
| FNS_SwitchTools | present | 7 |
| FNS_ColorUI (execs the scrub) | absent | 0 |

The Version Ctrl page is only the visible half. These artifacts also miss the
loopback web-server rule, the console-ships-dormant rule, the `FNS_About.Owner`
expression and the ExtUtils log scrub.

**Fix:** add the `exec(open('packaging/pre_release_common.py').read())` line to
the six hooks, and create hooks for the four packages that have none. Each
artifact must then be re-exported and re-released for the scrub to reach users.

## 6. pre_release should set the current page

The page a tool opens on is whatever the author last had selected. Measured in
the artifacts: `FNS_CamSequencer` opens on `Seq` and `FNS_SwitchTools` on
`Custom` (both happen to be their first custom page), while `FNS_ColorUI` opens
on `Registry` when its first custom page is `ColorUI`.

**Fix:** in `pre_release_common.py`, set the staged copy's `currentPage` to its
first custom page. One rule, applied to every package that execs the scrub —
which is also why item 5 has to land first or the six family tools will not get
this either.

---

## What this batch has in common

Items 1, 5 and 6 are the same failure in three costumes: **the artifact
inherits the author's live session state**, because the only thing standing
between a dev project and a shipped tox is a hook that each package has to opt
into by hand. A package that forgets the one-line exec ships everything the
scrub exists to remove, and nothing fails — no test, no preflight warning.

Worth considering as a seventh item: make the export refuse, or at least warn
loudly, when a package's `pre_release` does not exec the common scrub. That
would have caught all six of these before they ever shipped.

---

## What landed on 2026-09-18

Items 1, 4 and 6 are fixed, and 5 of the 6 hooks in item 5. Verified by
re-exporting three packages and reading the artifacts back:

| artifact | `Version Ctrl` | `vc_data` | current page | `Active` |
|---|---|---|---|---|
| FNS_SwitchTools | gone (was present) | 0 (was 7) | `Custom` (first) | -- |
| FNS_Remote | gone | 0 | `Remote` (first) | **False** (was True) |
| FNS_ColorUI | gone | 0 | `ColorUI` (was `Registry`) | -- |

Still open: item 2 (needs the owner's decision), item 3 (needs real work
inside CamSequencer), and `pre_release` hooks for the four packages that have
none -- `FNS_OpFamily`, `FNS_RandomCHOP`, `FNS_iopBrowser`,
`FNS_ParentHierarchy`. `FNS_ProSceneChanger` has a hook that is a DAT with no
externalized file, so it was not covered by the file sweep either.

None of it reaches a user until those packages are re-exported and released.

---

## Item 2, decided 2026-09-18: a family member is NOT placed

Owner's call: no placement at all. A family member lives **on disk** -- in the
FNS family folder, or as an OpTemplate -- and nothing is dropped into the
project by installing it. The choice should be an option in the same CMS
dropdown as the existing ones.

### The catalog is not where this is decided

Removing `placement: pane` from the seven catalog entries would not work.
`build_manifest.py` puts it back, in two places:

    entry['family'] = curated_family
    entry.setdefault('placement', 'pane')      # lines 594 and 2263

commented *"a member is placed into the working network by definition"*. That
definition is the thing being changed, so the fix starts there and the catalog
entries follow.

### Scope, in the order it has to land

1. `build_manifest.py` -- stop forcing `pane` for a family block; a member
   defaults to the new value instead.
2. The new value itself. `''` already means "the toolkit container", so this
   needs its own name -- `none` reads clearest against a dropdown label like
   "Not placed (on disk: FNS family / OpTemplates)".
3. `InstallerExt` -- `ResolvePlan` presence (line 454), the spawn branch
   (884-893), the `spawn_names` sets (412, 2354) and RemoveTools' doorstep
   branch all switch on `pane`/`root` and need the third case: install records
   it, places nothing, removes nothing from the project.
4. The picker -- the "lands in your working network" chip and the footer's
   "N spawn into your network" count must not claim a spawn that will not
   happen.
5. `cms.mjs` -- the dropdown gains the option; the validator at line 705
   (`pl !== 'pane' && pl !== 'root'`) and the family rule at 369 both need it.
6. Preflight, and `tests/test_placement.py`.

### The palette question, measured

The family toxes are ALREADY under the TouchDesigner user palette. Measured
2026-09-18:

    app.userPaletteFolder  = C:/Users/Dan/Documents/Derivative/Palette
    family members         = <that>/FNStools_ext/family/FNS/{CHOP,COMP,TOP}/
        CHOP/  FNS_MixSequencer_1.0.1.tox, FNS_RandomCHOP_1.0.0.tox, FNS_SwitchTools_1.1.1.tox
        COMP/  FNS_CamSequencer_3.0.1.tox, FNS_OpSequencer_1.16.1.tox
        TOP/   FNS_ProSceneChanger_1.0.1.tox, FNS_SimpleSceneChanger_1.0.2.tox

and TD's browser roots "My Components" at `$userPaletteFolder`
(`/ui/dialogs/palette/palette/p2/rootfolder`), so they are in scope of the
tree already -- but three folders deep under `FNStools_ext / family / FNS /
CHOP`, and named with a version suffix, which is TDFam's naming and not a
name anyone would want to read in a palette.

So "make sure they land in the user palette" is probably about being FINDABLE
rather than present. That wants a decision of its own before building: a flat,
cleanly-named palette folder alongside the versioned family folder, or leaving
the family folder as the one home and accepting the depth.

### The palette needs its index updated, not just files (owner, 2026-09-18)

Dropping toxes into the palette folder is NOT enough. TD keeps an index at
`<userPaletteFolder>/paletteData.json` (269 KB on the dev machine) and the
browser reads THAT. Its shape, measured:

```json
{ "children": [ ... ], "id": ..., "localRoot": ..., "name": ...,
  "palette": ..., "path": ..., "type": ... }
```

Every node is `{id, name, path, type}` with `children` on a directory;
`type` is `file` or `directory`; `path` is backslash-relative to the palette
root (`\0MY_SHIT\Audio\audio_FFT_process1.tox`); `id` is a dotted
hierarchical key (`2.1.19.3`) whose parent prefix is its folder's id.

Owner's layout call: **`FNStools_ext/FNS/` flat is enough** -- no
`family/FNS/CHOP` depth. Categories belong in the per-tox JSON manifests
(TDFam already writes a sidecar `.json` beside each member), not in folder
structure.

So the work is: write members flat to `FNStools_ext/FNS/<Tool>.tox` with their
sidecar manifests, then insert or refresh that directory node inside
`paletteData.json` with correct ids. TDXLPP was suggested as prior art; a
search there found palette-FOLDER discovery (`TDXLUUtilityExt._findTdPyEnvManagerTox`)
but no writer for this index, so the index editing looks like new code -- worth
a second look in that repo before writing it.

Open question before building: whether TD rewrites `paletteData.json` from
disk on its own (a rescan, a restart) and would therefore clobber or heal an
edit. That decides whether we write the index once at install or re-assert it.

### How it is done, from the owner (2026-09-18) plus our own measurements

The write side lives in TDXLPP's Rust (`src-tauri/src/palette.rs`), the
"make TD notice" side in its utility extension. What matters for us:

- **The index is REGENERATED WHOLESALE from a directory walk**
  (`palette.rs:476`, walk at `:418`, node shape at `:403`). It is never
  patched. So we regenerate too, and **no re-assertion is needed** -- owner
  confirmed. Insert-a-tool is "copy the .tox in, then rebuild"
  (`palette.rs:521` -> `:601`); the inverse is `:634`.
- **Node shape**: `id`, `name`, `path`, `type`, `children`, plus `localRoot`
  and `palette` on the ROOT only. Verified against the live file: the root is
  `name: "My Components"`, `palette: "My Components"`,
  `localRoot: "app.userPaletteFolder"`, 74 children. Paths are Windows-style
  with a leading backslash (`palette.rs:392`).
- **Palette root resolution** differs per platform: `palette.rs:51` Windows,
  `:25` macOS.
- **TD reads the file only at STARTUP**, into the Text DAT
  `/ui/dialogs/palette/palette/cusPalette` (its `file` par IS
  `<palette>/paletteData.json`). To make TD notice, pulse that DAT's load:
  `op('/ui/dialogs/palette/palette/cusPalette').par.loadonstartpulse.pulse()`
  (TDXLU does this as its `palette_refresh` action, `TDXLUPaletteExt.py:228`,
  called from `palette_tabs.rs:527`). It is a COURTESY -- a failure must not
  fail the install.

**Measured end to end on 2026-09-18** (backed up, probed, restored): appending
a `{id, name, path, type, children}` directory node to the root's `children`,
then pulsing `loadonstartpulse`, made the DAT re-read the file and the probe
node appear in it. Restoring the backup and pulsing again removed it cleanly.
So the edit-then-pulse loop is confirmed on our side; only the walk itself is
left to write.

### Also found: a case mismatch that only bites macOS

The palette folder on the dev machine is `FNSTools_ext` (capital T) while the
updater builds its paths as `FNStools_ext` (lowercase t). Windows does not
care; macOS does. Fix it in the same pass.

## 7. The ProSceneChanger binding is DELIBERATE (corrected 2026-09-18)

First reading was wrong, and the correction is the useful part.
`FNS_ProSceneChanger/pre_release` is file-synced to
`FNS_SimpleSceneChanger/pre_release.py`, which looked like the copied-DAT
hazard. It is not. Checked:

- `FNS_ProSceneChanger` has **no source folder of its own**. All ten of its
  top-level DATs point into `FNS_SimpleSceneChanger/`.
- That folder holds `ExtSimpleSceneChangerPro.py` -- Pro's OWN extension,
  deliberately co-located.
- The shared hook is Pro-aware:

      IS_PRO = (_base.startswith('simplescenechangerpro') or '.pro.' in _base
                or 'proscenechanger' in _base)
      PRO_DAT = 'ExtSimpleSceneChangerPro'

So Simple and Pro are one codebase shipped as two packages, and one hook
serves both by branching on the save path. Adding the common-scrub exec to
that file therefore fixes BOTH, and ProSceneChanger's tox should be committed
with the rest rather than held back.

### The sweep found no borrowed bindings

Every file-synced DAT in the toolkit was checked against its owning package
(1997 DATs carry a `file`). Restricted to a package's OWN top-level DATs, 41
point into another package's folder, and all 41 are explained:

- **Retired folder names** -- the v3.0 renames kept their old directories:
  `FNS_AutoRes -> AutoRes/`, `FNS_ColorUI -> ColorUI/`, `FNS_SwapOps ->
  SwapOps/`, `FNS_AltSelect -> AltSelect/`, `PasteFromClipboard ->
  paste_from_clipboard/`, `FNS_OpTemplates -> OpTemplates/`, `FNS_OpMenuMods
  -> FNS_OpMenu/` and the rest. Confirmed those directories still exist. The
  files ARE each tool's own; only the directory name is stale. Cosmetic.
- **Shared infrastructure by design** -- `ExtUtils/FNSCommand.py` and
  `CustomParHelper.py`, and registry hosts syncing to their master's ext
  (`FNS_ConfigHost -> FNS_ConfigRegistry/`). This is the documented mechanism.
- **One shared codebase** -- ProSceneChanger/SimpleSceneChanger, above.

Nothing to fix. Worth keeping the probe though: a package's own top-level DAT
pointing at a LIVE sibling's folder is the shape worth alarming on, and only
the scene-changer pair matches it today.

## 8. FNS_ProSceneChanger has a cook dependency loop

Noticed 2026-09-18 while releasing, on a read-only probe, so it PREDATES this
session's edits (nothing here touched that tool's network):

    /FNSTools/FNS_ProSceneChanger:Warning: Cook dependency loop detected.
    Check for exports, expressions or wiring that are creating this loop:
    # Cook dependency loop starts
    /FNSTools/FNS_ProSceneChanger

Five warnings, zero errors, and the loop is reported ON the package COMP
itself rather than a child, which points at a parameter export or expression
that reads back into the COMP it drives.

It did not block v3.2.38 -- the package has been shipping with it and the
release fixes other real things -- but a cook loop costs a frame every frame
and should not be left in a shipped tool. Not yet diagnosed.

## Item 5 closed 2026-09-18: why the four had no hook at all

**`packaging/CREATING.md` never mentions `pre_release`.** A grep of the
document that tells you how to create a package returns nothing. So a package
made by the book gets no hook, and nothing downstream complains. That is the
whole explanation: FNS_OpFamily and FNS_RandomCHOP (both created 2026-09-17),
FNS_iopBrowser and FNS_ParentHierarchy (2026-09-09) all followed the document.
FNS_SwitchTools was created the SAME DAY as the first two and does have one,
because it was a port of a tool that already carried it.

All four now have a hook running the common scrub, verified in the artifacts:
no Version Ctrl page, zero vc_data tables. Two of them had no source folder
at all, so that was created with the hook.

**One nuance, stated rather than glossed:** the first-page rule reads back as
`None` in the artifacts of the two PANEL comps (FNS_iopBrowser,
FNS_ParentHierarchy) while it takes on the two base comps. Live, setting
`currentPage` on those same comps works and reads back correctly, so it is
about what a panel COMP persists in a tox, not about the rule. Their first
custom page is `Custom` either way, so the shipped outcome is right, but the
rule is not universal and should not be described as such.

**Still worth doing:** make `CREATING.md` require the hook, and have the
export warn when a package's `pre_release` is missing or does not exec the
common scrub. Nothing catches it today.

## Item 3, 2026-09-18: fixed where it matters, honest about the rest

The shipped artifact no longer carries the nameless column: FNS_CamSequencer's
`pre_release` strips any column whose header AND every cell are empty, so an
install cannot hit `Exception: Blank header in col 26`. Verified in the
artifact: 26 columns ending in `ipdshift`. The shared sequencer engine
(`AnySeqExt._dropBlankColumns`, used by OpSequencer, MixSequencer and
CamSequencer) also prunes them, and `CamSeqExt._refreshInner` skips blank
headers so the colDefine table stops keying a row by position.

**The dev-side writer is still unidentified, and that is worth saying.** In
the dev project the column comes back within a frame of being deleted. A DAT
Execute armed on the presets table with BOTH `tableChange` and `sizeChange`,
verified active and correctly pointed, never fired while the count went 26 ->
27. So it is not a script editing that DAT. Remaining suspects are the
`Presets_RepoMaker` / `Campresets` repo sync (CamSeqExt line 43 maps the par
to the table) and `AnySeqExt.RestorePresets`, which assigns `table.text`
wholesale from a stored backup that may itself contain the column.

## 8. FNS_ProSceneChanger cook loop -- DIAGNOSED 2026-09-18

It is a parent/child cycle through two DIFFERENT parameters:

    SceneChanger.par.Autonext   = (1 - me.op('timer_auto')['timer_fraction']) * me.par.Autointerval
    timer_auto.par.length       = max(parent.SceneChanger.par.Autointerval.eval(), 0.1)

The COMP's parameter reads the child; the child's parameter reads the COMP.
TD's cook dependency is per OPERATOR, not per parameter, so COMP -> timer_auto
-> COMP is a cycle even though `Autonext` and `Autointerval` are unrelated.
That is why the warning names the COMP itself with nothing else in the loop.

Two ways out, neither applied yet because this is a gated tool and the change
wants testing rather than a late edit:

- **Break the child's read.** Make `timer_auto.length` a CONSTANT and have the
  extension write it when `Autointerval` changes (`_onAutointervalValueChange`),
  which is the project's parameter-callback convention anyway.
- **Break the parent's read.** Compute `Autonext` without reaching into
  `timer_auto`.

The first is the smaller change and keeps the behaviour identical.

## Item 2 built, 2026-09-18

### `placement: none`

A third value joins `pane` and `root`: nothing is placed anywhere. The
install downloads the package and records it; the user reaches it from the
FNS tab of the OP Create dialog or from disk. It crosses the six surfaces the
scope predicted:

- `build_manifest.py` -- accepts `none`, and a family member now
  `setdefault('placement', 'none')` where it forced `'pane'` (BOTH sites)
- `catalog.json` -- all seven family entries switched from `pane` to `none`
- `InstallerExt` -- presence is the record (`placement in ('pane', 'none')`),
  the install step returns `available (not placed)` without loading anything,
  and both `spawn_names` sets include it so removal forgets rather than
  destroys
- the picker -- a `from the FNS tab, not placed` chip
- `cms.mjs` / `cms.html` -- the option is in the same dropdown, and the family
  rule now REFUSES `pane` as well as `root`
- `tests/test_placement.py` and `tests/test_op_family.py` updated to the new
  contract, with the reason in the docstring

Verified in the regenerated manifest: all seven family packages read
`placement: none`, and nothing reads `pane` any more.

### The palette mirror

(2026-09-18: superseded, the family folder itself is the flat palette copy now, docs/PaletteFolderContract.md.)

`FNS_Updater.SyncPaletteFolder()` mirrors the members flat into
`<userPalette>/FNStools_ext/FNS` under their PUBLIC names -- `SwitchTools.tox`,
not `FNS_SwitchTools_1.1.2.tox` -- with the category in the sidecar JSON
rather than as a subfolder. TDFam's own family folder is untouched: versioned
and grouped, because that one is a machine contract.

`RebuildPaletteIndex()` then regenerates `<userPalette>/paletteData.json` from
a directory walk in TD's node shape and pulses
`/ui/dialogs/palette/palette/cusPalette`'s `loadonstartpulse`, because TD
reads that index only at startup. Wholesale, never patched, which is how the
launcher's writer does it, so the two cannot fight. Both ride the pass that
already syncs the family folder.

Measured live, with the real index backed up first:

| | before | after |
|---|---|---|
| `.tox` indexed | 1155 | **1189** (our seven, plus some TD had missed) |
| `.toe` indexed | 63 | 63 |
| files indexed | 1272 | 1329 |
| dropped | -- | one `.dll`, one `.py` |

**One draft cost 50 `.toe` files** by skipping any folder called `backup`,
`build` or `dist`. A plausible NAME is not a machine folder; the skip list is
now `node_modules`, `__pycache__`, `site-packages` only, plus dotfiles and
build-artefact extensions. That is why the table above is in the record.

**Not done:** a live end-to-end install of a family package into a scratch
target. The plan, the manifest, the code paths and the tests all agree, but
nobody has watched an install of one of these place nothing.

## 9. A stale store installed a whole old release -- FIXED 2026-09-19

The owner installed into a clean project and got seven FNS family COMPs
spawned at the project root, at versions nobody had shipped for days. I read
that as stale leftovers twice and was wrong twice. The owner's correction --
"these came from a fresh install" -- is what broke it open.

The `installed` table settled it. All 67 rows carried today's timestamps
(2026-09-19 00:00:35 to 00:00:40) and `release: v3.2.37`, while the bucket
serves v3.2.42 (fetched and confirmed: `release v3.2.42`, family members at
`placement: none`, CamSequencer 3.0.3). So the install was fresh, correct,
and pointed at a catalog five releases old.

**Cause.** `DefaultManifest()` returns `<store>/manifest.json` whenever that
file exists, with no freshness test, and the store lives in the palette
folder -- machine-wide, outliving every project. The silent "set up like
last time" rail then planned the entire install from it. Its only refresh
was `if full is None`, so a machine that had ever installed never looked
again. In the v3.2.37 catalog the family members still carried
`placement: pane`, which is why seven of them spawned into the network the
owner was looking at, the root. That is the exact behaviour `none` was added
to prevent, reintroduced through a stale catalog.

This is the same defect as the clean-machine hang fixed the day before
(`tests/test_first_run_catalog.py`): I fixed the empty-store case and left
the stale-store case, which fails silently instead of hanging. The picker
has been guarded since v3.2.26 (`_checkManifest`, one throttled manifest-only
refresh behind every served store manifest); the silent rail never was.

**Fixed.** `_lastSetupStep` now refreshes at stage `plan` whenever the
manifest is the store's or absent, then plans on what arrived. A dev
`Manifestfile` outside the store is left alone; a manifest that never
arrives is still the hard stop it was.

Two consequences of `placement: none` were found in the same pass and fixed
with it:

- `Install` skipped `RecordInstalled` for a `none` package. The record is the
  only evidence such an install happened (there is no child to find), so
  `ResolvePlan`'s `present` and `Compare` both read it. Without it the picker
  offers the package forever. It now records the landed sha, and fails
  rather than recording when the artifact never arrived.
- `Compare` tested `placement in ('pane', 'root')` for the `component`
  state, so every not-placed package fell through to `missing` -- "recorded
  as installed but not in this project", which is precisely what a family
  member is supposed to be. `'none'` joined the tuple with its own note.

Pinned by `tests/test_first_run_catalog.py` section 4,
`tests/test_placement.py`, and `tests/test_auto_setup.py`. Full suite: 39
files green.

**Not fixed, and worth deciding:** the seven root COMPs in the owner's
project are a correct v3.2.37 install and no update pass will remove them.
They need deleting by hand, and an install-time notice when a
`placement: none` package is found sitting in the project is still open
(item 2's follow-up).

## 10. Registry hosts that cannot receive a fix -- PARTLY FIXED 2026-09-21

Found while sweeping for leftovers from the v3.2.42 palette rename. The
rename could not reach the `Configfile` tooltip because that help text is
authored ON the parameter, not set by code, so all 45 ConfigRegistry hosts
still named `FNStools_ext`. Healed at init from a class constant
(`_ensureFileParHelp`), the way `Configscope` was.

Chasing the four hosts the heal did not reach turned up the real problem.
**FNS_Remote, FNS_BeatMod, FNS_Autosave and FNS_CommandPalette carried a
1290-line `ConfigRegistryExt` against the master's 1565.** Their ext DAT had
no `file` binding, and their clone never pulled, so they were frozen on
whatever they were stamped with and no file fix could ever have reached
them. This is the hazard `/fns-registry` already names ("a host that cannot
receive base fixes is a silent liability"), at 4 hosts rather than 2.

Toggling `enablecloning` did not move them. Restoring the `file` +
`syncfile` binding did, and that is the channel the other 41 use. Embody
strips the binding on export (read back out of a built artifact:
`file` empty, text baked in), so shipped hosts stay self-contained. All four
released in v3.2.46.

**Still open, two things.**

1. **No audit exists for this.** Nothing reports a host whose ext DAT is
   unbound AND whose text differs from the master. It was found by hand.
   `op.FNS_CONFIGREGISTRY.ScopeAudit()` is the model: a `HostAudit()` on
   RegistryBase that walks every host of every registry and reports the
   frozen ones belongs beside it, run before a release.
2. **A dead `ToolbarRegistryExt` ships inside every NavbarRegistry host and
   the Navbar master** (633 lines, no binding, referenced by no extension
   slot -- slot 1 points at `NavbarRegistryExt`). A leftover from seeding
   NavbarRegistry by copying ToolbarRegistry, which is exactly the copied
   master hazard in `/fns-registry`. Harmless but shipped. Removing it
   dirties and re-releases 5 packages, so it waits for a release those
   packages are in anyway.

A caution for whoever writes the audit: a scan that picks DATs by
`name.endswith('Ext')` takes the LAST match and will read the orphan rather
than the real extension. Resolve the ext DAT from the `extension1` par, not
by name.
