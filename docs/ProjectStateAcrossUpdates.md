---
status: open
summary: An in-place update keeps a tool's custom pars (reloadcustom off) but rebuilds its children, so internal readers come back blank. Fix is split: retire the tool's duplicate streaming readers in favour of FNS_MEDIA's, and self-heal the two analysis readers that must stay.
since: 2026-08-26 (branch dev25-private)
skill: fns-packaging
---

# Project state across a package update

## Correction

An earlier draft of this doc claimed per-project state had no rail surviving a
package update, and proposed an installer-side snapshot/restore. **That was
wrong on the facts.** Updates do not destroy the COMP, and custom parameter
values already survive. What follows is the corrected, much narrower problem.

## How updating actually works

`ExtUpdater._rewriteBound` is the update path, and its own docstring states the
design:

> A plain `externaltox` binding is NOT a refusal -- it is the BETTER update
> path: the file takes the new bytes and the COMP reloads, with no
> copy/destroy of an extension-bearing COMP.

So an update is **a file write plus an external-tox reload pulse**, in place.
`InstallerExt.InstallPlan`'s `existing.destroy()` + `loadTox()` is the *install*
and explicit *Replace* path, not the update path.

Two consequences:

- **Custom par values survive**, because `reloadcustom` is off on the packages
  that hold state nothing else carries. Fleet split, measured: **41 of 50 have
  `reloadcustom = True`, 9 have it off** -- FNS_Hub, FNS_Console, FNS_Installer,
  FNS_CommandKit, FNS_ConfigHost, FNS_HubRegistry, FNS_TimelineTools,
  FNS_PaletteRegistry, FNS_TimelineRegistry. The 41 can afford to be reset
  because the config registry re-applies them; the 9 are configured in place.
- **Children are rebuilt from the artifact.** A reload replaces the COMP's
  contents. Anything held on a *child* operator's built-in par comes back as
  the artifact shipped it.

## The actual discrepancy

For `FNS_TimelineTools`:

| After an in-place update | |
|---|---|
| `Moviefile`, `Audiofile`, `Movieop`, `Audioop` | **survive** (`reloadcustom` off) |
| `moviefilein.file`, `audiofilein.file`, `FNS_Waveform/render_chain/filein1.file` | **blank** -- rebuilt from the artifact |

The tool then shows media as configured while playing nothing, until the user
re-triggers `Loadmedia` by hand.

`TimelineToolsExt.__init__` does not close this: it schedules `AnimationUI()`
and stamps `ext_ready_frame`, and there is no `postInit`. Nothing re-derives the
readers from the surviving pars.

Note this shape is **created by the pre_release scrub** added in the same pass.
Before it, the artifact shipped carrying the author's own media paths in those
readers -- which happened to leave a working tool for the author and was a
private-path leak for everyone else. Blanking them is right; it just exposes
that the readers were never re-derived.

## Proposal

Two readers, two different answers, because they are two different jobs.

### 1. The streaming readers already exist outside the package -- LANDED

`/FNS_MEDIA` -- the durable host at the root, reached by `op.FNS_MEDIA` -- already
contains `moviefilein`, `audiofilein`, `audiomovie`, `switch_video`/`switch_audio`,
`select_video`/`select_audio` and `null_video`/`null_audio`. The tool carries its
OWN `moviefilein` and `audiofilein` holding the same paths.

That duplication decodes the same media twice, which was flagged when FNS_MEDIA
was designed ("having an internal one as well will be duplicating resources").
It is also exactly the update problem: the tool's copies live inside the package
and are rebuilt blank by a reload, while FNS_MEDIA's are outside it and are not
touched at all.

Landed. The tool's `moviefilein`/`audiofilein` are gone; `null_video`/`null_audio`
now take a Select on `op.FNS_MEDIA.op('null_video'/'null_audio')` -- by shortcut,
not path, so it survives FNS_MEDIA being renamed or moved. `_ownMovie`/
`_ownAudio` resolve to the host's readers, and the release path hands the switch
back to slot 0 (the host's own reader) instead of pointing the host's Select at
this tool's null -- the arrangement the code itself described as lasting only
"until the readers migrate into it".

**Not a cook saving, and the earlier draft implying one was wrong.** Measured
before the change: the host's unselected readers cooked 0 times in 557 frames,
because TD does not pull an unselected switch branch. The wins are a single
source of truth -- the same media had been recorded in three places and had
already drifted, the host's copies pointing at an unrelated phone video and demo
mp3 -- and update resilience, since nothing outside the package is rebuilt by a
reload.

**There is no "FNS_MEDIA is present" guarantee, and nothing claims to be one.**
(`Ensurelocal` is unrelated -- it is a Pulse labelled "Add Component Time" that
clones `/sys/local/time` into a Scope Comp. Named for the local timeline, not
the media host.) The accessors return `None` when the host is missing and every
caller already guards for a missing reader, so the tool degrades quietly rather
than erroring. Whether a missing host should be recreated on demand, or simply
reported, is open.

### 2. The analysis readers stay, and re-derive -- LANDED

`FNS_Waveform/render_chain/filein1` (whole-signal read for the waveform) and
`FNS_TimelineBackground/moviefilein` (seek-based thumbnail extraction) genuinely
need file access rather than a stream, so they cannot consume FNS_MEDIA's
outputs. They stay inside the package, come back blank after a reload, and need
re-pointing from the surviving `Moviefile` / `Audiofile` pars.

Landed as `TimelineToolsExt._healReaders`, scheduled from `__init__` at 60
frames. If a media par is set and the ACTIVE reader is blank, it calls
`LoadMedia()` -- which already re-points the readers from the pars and settles
the timeline, so the heal only had to decide when.

Verified in three steps rather than assumed: the external-tox reload pulse DOES
re-initialize the extension (`ext_ready_frame` restamped 458352 -> 1077116);
with the tool in adopted mode the heal correctly no-ops, because the active
reader is the user's own op outside the package; and with adoption cleared and
both readers blanked, it re-pointed both and the timeline re-synced to
`1-11341 @ 60fps (189.02s from the audio)`.

Open: whether re-pointing should also rebuild the strip, or leave it blank until
asked. Rebuilding is friendlier but is real work on project open.

## Still worth deciding separately

- **The other 8 packages with `reloadcustom` off** may have the same shape --
  surviving pars pointing at children that come back default. Unchecked.
  FNS_Console and FNS_Hub are the likely candidates.
- **`reloadcustom = True` on the other 41** means their custom pars ARE reset by
  an update, and they rely entirely on the config registry re-applying them.
  Under **project scope** the config file is never read, so it is worth
  confirming those settings actually survive an update in a project-scoped
  install -- that combination has not been tested.

## Verification this needs

1. Configure media, update the package in place, confirm the readers re-point
   and playback resumes without user action.
2. Same with the media file missing -- should warn, not silently blank.
3. Confirm a project-scoped install keeps `reloadcustom = True` package settings
   across an update (the untested combination above).

## Where the version should live (proposed)

`reloadcustom = True` on 41 of 50 packages is the remaining hazard: an update
resets every custom par on those tools, and they depend entirely on the config
registry re-applying them -- which under **project scope never reads the file at
all**. Untested, and a much worse loss than blank readers if it fails.

The flag is not protecting the version *value*. It is protecting the par's
*existence*: `packaging/migrate_pkgversion_page.py` records that
**"five comps had lost `Pkgversion` entirely (a tox reload reverts page
state)"**. `reloadcustom = True` is the blunt instrument that keeps the About
page in step with the artifact -- and it takes every user setting with it.

> **CORRECTION (2026-08-26, measured).** The existence half of that reasoning
> does not hold for the update path. Probed live on TD 2025.33070 across five
> tox generations ([UpdaterHardening.md](UpdaterHardening.md) §1): an in-place
> external-tox reload with `reloadcustom = OFF` **reconciles the par set by
> itself** -- new pars land, pars the new build retired are removed, pages
> survive, and values are preserved for anything present in both. Nothing has
> to protect a par's existence.
>
> What the flag really protects is only the version VALUE, and it does so
> bluntly: a preserved par keeps its old value **even when the user never
> touched it**, so the build's bumped version never lands. That is the whole
> problem, and it is exactly what moving the version onto a child fixes.
>
> So the proposal below is confirmed necessary and sufficient -- on better
> grounds than it was written on. The five comps that lost `Pkgversion` were
> losing it to some other path (the destroy+loadTox install rail, or
> `reloadcustom = ON`), not to the in-place update reload.
>
> The same probe supersedes verification item 3 below: `reloadcustom = True`
> package settings do NOT survive an update in a project-scoped install --
> the pars are reset and there is no config file to restore them from. It is
> not an open question any more, it is the reason for the flip.

**Proposal: move the version onto a child.** A `FNS_Manifest` base COMP inside
each package holds the real `Pkgversion`. Children are rebuilt from the artifact
by a reload, so the version follows the artifact automatically, with no
`reloadcustom` involved. The tool keeps a visible `Pkgversion` on its About page
as an EXPRESSION referencing it:

```
op('./FNS_Manifest').par.Pkgversion
```

Then `reloadcustom` can be off everywhere, and user settings survive updates on
all 50 packages instead of 9.

### What it costs -- the call sites

Every consumer reads `comp.par.Pkgversion`, and an expression par evaluates
normally, so **the readers need no change**:

| Site | Role |
|---|---|
| `build_manifest._version` | version at Build time |
| `ExtUpdater` (~line 79) | the live update decision |
| `InstallerExt` (~line 562) | `('Pkgversion', 'Version')` probe |
| `ColorUI/ExtColorUI` | a tool displaying its own version |

**One writer changes.** `release_one.ReleaseMany` does `p.val = new_v;
p.default = new_v` on the tool. Writing `.val` to an expression par sets the
constant underneath and leaves the expression in charge, so the bump would
silently do nothing. It has to target the manifest's par instead.

Ordering already works: `ReleaseMany` bumps before it calls `Build`, so the
artifact ships carrying the bumped manifest.

`pre_release_common.py` freezes pars whose expression mentions `parent.FNS`;
this expression is a local `op('./FNS_Manifest')` reference, so it is untouched.

### Open

- Does `FNS_Manifest` carry anything besides the version -- build number, a
  dependency list, the doc slug the site build already requires?
- Migration: 50 packages need the child and the expression. A scripted pass like
  `migrate_pkgversion_page.py` (which did exactly this shape of change once
  already) is the precedent.
- Flip `reloadcustom` to off as part of the same pass, or separately once the
  version no longer depends on it?
