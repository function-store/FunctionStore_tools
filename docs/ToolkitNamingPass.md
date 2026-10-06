---
status: landed
summary: The 2026-09-09 naming pass -- FNS_ prefix on every package, the Toolbar/MISC consolidation, and Active as the single on/off parameter name.
since: 2026-09-09
---

# Toolkit naming pass

Owner request, 2026-09-09: put every shipped package behind the `FNS_` prefix,
fold what is left of `FNS_Toolbar`, and settle the `Enable` / `Active`
parameter split on `Active`.

## What a package rename actually binds to

Packages are discovered LIVE, by COMP name: `build_manifest.Packages()` returns
depth-1 COMPs that are tracked suspects with their own tox. So the COMP name is
the package name, and four things follow it:

1. the `catalog.json` key,
2. `packaging/docs/<Name>.md`,
3. `release.json` `retired` -- publish refuses to drop a package the previous
   release published unless the OLD name is declared there,
4. the registry hosts' stored `Canonicalname`.

**The fourth is the one that decides risk, and it mostly does not move.**
`Register()` derives the public name by stripping a leading `FNS_`, and
`Canonicalname` already holds that stripped value. So a package that merely
GAINS the prefix keeps its public name: `AltSelect` -> `FNS_AltSelect` is still
`AltSelect` to the command registry, the config store and the launcher. Command
ids and saved settings survive untouched.

Only a changed BASE name is a real identity change, and there are six:

| Old COMP | New COMP | Public name |
|---|---|---|
| `MISC` | `FNS_Misc` | `MISC` -> `Misc` |
| `OUTPUT` | `FNS_Output` | `OUTPUT` -> `Output` |
| `ResetPLS1` | `FNS_ResetPLS` | `ResetPLS1` -> `ResetPLS` |
| `TDX_SearchPalette` | `FNS_SearchPalette` | `TDX_SearchPalette` -> `SearchPalette` |
| `FNS_OpMenu` | `FNS_OpMenuMods` | `OpMenu` -> `OpMenuMods` |
| `paste_from_clipboard` | `PasteFromClipboard` | same, respelled |

Those six need `Canonicalname` updated and their hosts re-registered:
unregister under the OLD name FIRST, rename, then register. Renaming first and
unregistering after would unregister the new name and orphan the old entry.

## Prefix-only renames (public name unchanged)

`AltSelect` `AutoCombine` `AutoRes` `BorderlessTD` `ColorUI` `ExprHotStrings`
`GlobalOutSelect` `GlobalVolControl` `HydroHomie` `OpTemplates` `OpToClipboard`
`OpenExt` `ParOPDrop` `ParRandomizer` `QuickCollapse` `QuickPane` `QuickTime`
`SetSmoothness` `SwapOps` `SwitchOPs` `VSCodeTools`

## Deliberately NOT renamed

`QuickMarks`, `midiMapper`, `oscMapper` -- owner's call. `logger`,
`webBrowser`, `docsHelper*`, `mapTables` are internal, not packages.

## Every install reinstalls

A rename is a retirement plus a new package; there is no auto-migration (the
owner's standing decision, taken for the CustomParTools rename). Every renamed
name goes in `release.json` `retired`, and installs keep the old package until
the user installs the new name.

## What no auto-migration means for a consumer's install plan

Asked by the TDXLU launcher on 2026-09-11, which builds its plan as the
tools a session reports intersected with the manifest's names, and found
that a pre-rename package drops out of that intersection entirely.

Measured against the live installer, on a scratch target holding an
`AltSelect` COMP with a selection asking for `FNS_AltSelect`:

| Rail | What it does with the old COMP |
|---|---|
| `ResolvePlan` removals | Nothing. Candidates come only from manifest package names, so `to_remove` is empty |
| `ResolvePlan` presence | `present` is False for `FNS_AltSelect`, so the new package installs beside the old one |
| `Compare()` | Skips any child the manifest does not name, saying nothing. The old copy gets no update row and no warning |
| `retired` | Never read here. It is consumed by the CMS, `build_manifest` and `publish.py` only |

So a user who upgrades gets BOTH components, and the old one is frozen
and silent from then on. That follows the standing decision above, and it
is worth stating because the outcome is invisible at every point a user
might notice it.

`retired` cannot express the mapping in any case: it is a flat list of
old names, and its job is a publish-time guard, refusing a release that
drops a package the previous release published unless the name is
declared. There is no old-to-new map anywhere in the manifest.

A consumer's plan should therefore say it ADDS the new package, and that
the old one stays behind and has to be removed by hand. Saying it
"replaces" the old one would be false.

**Open for the owner:** whether the manifest should carry an old-to-new
map, so a consumer can say this without hard-coding thirty-one names.
That is a schema decision on top of the no-auto-migration rule, not a
reversal of it.

## Active, not Enable

`Active` already wins 19 tools to 5, and it is TouchDesigner's own name for the
switch, so the outliers move:

| Tool | Old | New |
|---|---|---|
| `HydroHomie` | `Enable` | `Active` |
| `BorderlessTD` | `Enable`, `Enabletimeline` | `Active`, `Activetimeline` |
| `FNS_Updater` | `Enabled` | `Active` |
| `ResetPLS1` | `Enableall` | `Activeall` |
| `FNS_CustomParTools` | 9x `Enable*` | 9x `Active*` |

A parameter rename drops that tool's persisted setting (ConfigRegistry stores
by parameter name), so each one resets to its default once. All fourteen
default to on, which is the pre-existing state for every user who never
touched them.

## Left for a later pass

Externalized FOLDER and FILE names, extension DAT names and Python class names
still carry the old spellings. The owner explicitly scoped these out of this
pass. `externaltox` keeps pointing at the old `<Old>.tox` filename, which is a
path the par carries and not a derived value, so nothing breaks -- it is only
untidy.

## What landed

All of it except one open question.

- Twenty-seven packages renamed, their suspect toxes moved to match, catalog,
  docs and the retired list in step. Only `PasteFromClipboard`, `QuickMarks`,
  `midiMapper` and `oscMapper` are unprefixed.
- `Active` is the on/off parameter everywhere. Sixty other COMPs carry `Enable*`
  parameters and every one of them is a TouchDesigner stock widget parameter
  (`Enablerollover`, `Enableupdatesystem`, `Enableselect`, `Enablecallbacks`) --
  TD's API, left alone.
- `FNS_Toolbar` retired into `FNS_Misc`.

### Three things the rename broke that were not obvious

1. **`FNS_About.Owner` held absolute paths** on five packages and stopped
   resolving. The house convention is a relative `'..'`; all fifty-eight now use
   it, so no future rename can break it.
2. **Clone masters do not follow a rename.** Fourteen ExtUtils clones still
   pointed at the pre-rename `CustomParTools` path, stale since that earlier
   rename rather than from this pass. The extutils distributor's
   `rollout(apply=True)` repaired twelve; the four slim `ExtUtilsMinimal` clones
   in FNS_BeatMod, which it skips, were repointed by hand.
3. **PI's suspects table is a path list** and does not follow a rename either:
   220 entries rewritten. The pattern needed a boundary guard so `FNS_OpMenu`
   could not eat `FNS_OpMenuMods`.

Also found on the way: sixteen toolbar hosts named `../FNS_Toolbar/ToolbarRegistry`
as their clone master. No such operator exists; twelve were resolving to the real
master only by TouchDesigner's loose fallback and four were resolving to nothing.
All sixteen now name `FNS_ToolbarRegistry` explicitly.

**PI's dirty flag does not trip on any of this.** `SaveDirty()` reported nothing
dirty after twenty-seven renames, because a child's NAME lives in the parent's
tox and clone-driven changes do not mark their owners. Every affected suspect
has to be saved explicitly, and the root last.

## Open question for the owner

Whether `mouse` and `hog1` should leave `FNS_Misc` as their own packages. The
owner raised `FNS_Mouse` while weighing it against install-list noise. They stay
in `FNS_Misc` for now: splitting one out would create the noise they were
worried about and leave an even thinner misc package behind.

