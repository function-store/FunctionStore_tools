---
status: landed
summary: 'Move the toolkit''s tools off the full ExtUtils clone (NoNode, its 11 exec DATs, Keyboard In, announcer) onto the slim ExtUtilsMinimal clone, each command owner announcing itself. NoNode is wired in none of them. The full master stays for QuickExt users.'
since: 2026-09-14
skill: fns-command-registration
---

# Moving tools to ExtUtilsMinimal

Owner's decision, 2026-09-14: tools get the slim clone
(`FNS_CustomParTools/QuickExt/ExtUtilsMinimal`) and announce their own
commands, the shape FNS_BeatMod and FNS_Remote already have.

## What was measured before deciding

- **57 full ExtUtils instances**, not "a few". 46 are toolkit tools or their
  FNS_About boxes; the rest are `/project1` test components, TDFam, and
  Private Investigator's release manager.
- **NoNode is wired in none of the 33 toolkit roots that carry it**: no
  CHOP, DAT, parameter or keyboard exec is targeted, and no tool source calls
  its API. It is dead weight inside the toolkit.
- The full clone's two live duties are the **announcer** (auto-registers a
  tool's commands 60 frames after init) and **`extAutoInit`** (touches
  `.extensions` so a COMP nothing pulls on still constructs its extension,
  and with it its CustomParHelper callbacks). The slim master has neither.
- Only one tool reaches into a full-only child by path:
  `FNS_Hub/HubExt.py` calls `ExtUtils/FNSCommandAnnouncer`.
- Baseline before any change: **151 commands from 47 owners**
  (`op.FNS_COMMANDREGISTRY.Commands()`).

## Not in scope

- **The full master** `QuickExt/ExtUtils` stays exactly as it is: QuickExt
  ships it as the template for users' own extensions, and NoNode is
  user-facing API there (`CoreToolsBacklog.md` item 2).
- `/project1/*` test components, `/TDFam_create`, `/private_investigator1`.
- `FNS_BackupCleaner` (a non-clone copy with no FNSCommand) is listed
  separately below; it is handled after the fleet, on its own.

## The plan

1. **Give the slim master `extAutoInit`.** Copy the full master's Execute DAT
   into `ExtUtilsMinimal`, so every slim clone keeps the lazy-init guarantee.
   Only the slim master's clones inherit it (five today: FNS_BeatMod's and
   FNS_Remote's).
2. **Pilot one tool end to end** (FNS_QuickCollapse), and record here
   anything it teaches before touching the rest.
3. **Per command owner:** the extension announces itself from a deferred
   `onInitTD` through `FNSCommand.announce(self.ownerComp)` (merged into an
   existing `onInitTD` where there is one). Then the tool's `ExtUtils` is
   pointed at the slim master, children re-synced, docks repaired.
4. **Per FNS_About box:** clone swap only (no commands).
5. **FNS_Hub:** replace its `ExtUtils/FNSCommandAnnouncer` call with the
   extension's own announce.
6. **Verify per tool:** both error kinds (`get_op_errors` and
   `scriptErrors(recurse=True)`), NoNode gone, the tool's command ids equal to
   the baseline, a forced reinit still announces.
7. **Save:** PI `Save()` every owning suspect, nested suspects first
   (HideTimeline, BorderlessWindow, ClearPars, QuickParent, QuickParCustom,
   QuickExt, TDTypings, ScriptSyncFile, MIDIResetPLS), then their parents,
   `/FNSTools` root last. Build the list from owners, not PI's Dirty column
   (clone-driven changes do not trip it).
8. **Fleet check:** distributor `survey()`, total commands back to 151 from
   47 owners.

## Traps to respect (from fns-command-registration)

- Batch text surgery: AST-parse every edited extension and diff its `def`
  names against git HEAD.
- Cloning does not carry docks: repair them after every re-sync.
- Extensions that are not file-backed (FNS_Misc, mapTables, FNS_Output,
  FNS_ResetPLS, FNS_QuickTime, FNS_HydroHomie, FNS_OpMenuMods,
  FNS_VSCodeTools, FNS_GlobalVolControl) are edited in TD and saved through
  their tox.

## Inventory

Command owners (root or nested tool): FNS_Hub, FNS_Misc, mapTables,
FNS_Output, QuickMarks, FNS_AutoRes, FNS_ColorUI, FNS_OpenExt, FNS_SwapOps,
FNS_Updater, FNS_ResetPLS, FNS_AltSelect, FNS_ParOPDrop, FNS_QuickPane,
FNS_QuickTime, FNS_SwitchOPs, FNS_HydroHomie, FNS_OpMenuMods,
FNS_AutoCombine, FNS_OpTemplates, FNS_VSCodeTools,
FNS_BorderlessTD/HideTimeline, FNS_BorderlessTD/BorderlessWindow,
FNS_PreviewPanel, FNS_HotkeyManager, FNS_OpToClipboard, FNS_ParRandomizer,
FNS_QuickCollapse, FNS_SetSmoothness, FNS_CustomParTools,
FNS_CustomParTools/ClearPars, FNS_CustomParTools/QuickParent,
FNS_CustomParTools/QuickParCustom, FNS_ExprHotStrings, PasteFromClipboard,
FNS_GlobalVolControl.

No commands (clone swap only): FNS_CommandPalette,
midiMapper/MIDIResetPLS, and 10 FNS_About boxes (VSCodeTools/TDTypings,
VSCodeTools/ScriptSyncFile, BorderlessTD/HideTimeline,
BorderlessTD/BorderlessWindow, CustomParTools/QuickExt, ClearPars,
QuickParent, iopPromoter, QuickParCustom), plus FNS_BackupCleaner's pair
(not clones; last).

## Progress

| Step | State |
|---|---|
| 1 slim master gets extAutoInit | done: copied into `ExtUtilsMinimal`; its five existing clones picked it up only after an explicit `enablecloningpulse` |
| 2 pilot FNS_QuickCollapse | done: it already announced itself from `onInitTD`, so only the clone swap was new; the swap removed every full-only child, kept the host dock, and after a reinit its two commands came back from its own announce |
| 3 self-announce code | done: 25 file-backed extensions and 9 in-tox extensions got `onInitTD` + `_announceCommands` through one checked transform (AST parse, `def`-name set equal to HEAD plus exactly the two new methods); FNS_Hub's `ExtUtils/FNSCommandAnnouncer` call now calls `FNSCommand.announce` |
| 4-5 clone swap | done: 46 instances (35 tools and nested tools, 10 FNS_About boxes, FNS_CommandPalette) plus the pilot |
| 6 verify | done: every command owner unregistered, extension reinitialised, and the registry compared to the baseline: 151 commands from 47 owners, none missing, none extra; no script errors under `/FNSTools` |
| 7 save | done: 46 owning suspect toxes, nested first, `/FNSTools` root, then `SaveDirty()` empty |
| 8 fleet check | survey: full targets 65 -> 18 (only `/project1`, TDFam, PI and FNS_BackupCleaner remain); still unhealthy for the same four non-clone copies it flagged before this work |
| cold boot | done 2026-09-14: project saved, TouchDesigner restarted. Every migrated tool announced itself at boot and all extensions were ready, with no script errors; the registry held 148 commands from 46 owners. The three missing were the Installer's (`available`, `install`, `installed`), unrelated to this work: the dev rail `/FNSTools/FNS_Installer` reloads from a tox saved 2026-09-10 that embeds an InstallerExt older than its command registration (55 KB against the 92 KB source), and the baseline only listed them because the v3.2.11 release's rail rebuild had re-embedded the source live. `EnsureDevRails()` refreshed it, it registered (151 / 47), and its tox was saved |
| FNS_BackupCleaner | done (owner's call): both non-clone full copies (tool and FNS_About) now clone the slim master; `extStubser` (a legacy stubs COMP nothing referenced) and NoNode went with the swap; no commands, so no announce code; extension reinitialised clean, CustomParHelper properties resolve; tox and root saved. Survey now flags only TDFam's two copies, outside FNSTools |

## What the run taught

- **Adding a child to a clone master does not reach existing clones until a
  clone pulse** (`par.enablecloningpulse.pulse()`).
- **Clone-immune children survive a clone swap.** FNS_HydroHomie's full-only
  exec DATs were `cloneImmune` (left from its cook-diet work) and stayed behind,
  erroring once NoNode was gone. Check every swapped instance against the
  master's child names, not just for errors, and destroy the leftovers.
- **Destroying a host destroys the DATs docked to it.** Removing
  `extKeyboardIn` took `extKeyboardin_callbacks` with it mid-loop; iterate over
  names and re-resolve each op.
- **46 PI saves in one call outlast the 30 s MCP timeout.** The call keeps
  running on the main thread; wait for the tox count in `git status` to settle
  instead of re-running it.
- **`extutils_distributor.rollout(apply=True)` clones anything still carrying
  NoNode to the FULL master.** Every toolkit instance is slim now, so a rollout
  leaves them alone; a new tool built from QuickExt starts on the full clone and
  must be swapped the same way.
