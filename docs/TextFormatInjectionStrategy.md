# Injecting FNSTools via TouchDesigner's Text-Based Project Format — Exploration

Future-work exploration, 2026-08-21. Read-only: no code changed, nothing
decided. Companion to [TextFormatProjectFiles.md](TextFormatProjectFiles.md)
(the schema research this builds on), [ConfiguratorDistribution.md](ConfiguratorDistribution.md)
(current distribution model) and [NativeInstallerDecision.md](NativeInstallerDecision.md)
(current bootstrap decision).

## The problem this is aimed at

Named directly in the prompt for this research: **FNSTools isn't part of any
default TouchDesigner startup file.** A new user has to know it exists, find
it, and manually drag a `.tox` into their network before they ever see it.
That's the adoption blocker. Everything below is about whether the new text
format changes what's possible there.

## 1. Where the actual gap is today (confirmed by reading TDXLPP's code)

Every path that gets FNSTools or the TDXLU companion utility into a project
today requires **TouchDesigner to already be open and running Python**:

| Path | Mechanism | Requires |
|---|---|---|
| First-ever install | User manually drags `TDXLauncherUtility.tox` from the Palette panel into their network | A live, open TD window; the user's own action |
| Store install via TDXLU's FNS Tools tab | `LoadTox` verb over TDXLU's TCP companion bus → `TDXLUUtilityExt.LoadTox()` calls TD's live `loadTox()` | An **already-resident** utility COMP with its TCP bus listening — i.e. this can only extend an install that exists, not create the first one |
| One-drop bootstrap (`FNSTools.tox`, current official rail per `NativeInstallerDecision.md`) | User drags one file in; it carries an installer that pulls the rest from the bucket | Still a live, manual drag |
| `toeexpand` (Derivative's own tool, bundled in TDXLPP) | Reads a two-line version/build header only, via `-b` | Nothing structural — confirmed it never touches the OP tree |

There is **no code anywhere in TDXLPP or FNSTools that edits a `.toe` file's
structure while TD is closed.** `toeexpand`/`toecollapse` round-trips
Derivative's older, undocumented ASCII dump of the *binary* format, and
TDXLPP's own code never round-trips it back — it only reads a header. The
text format changes that: it's a real, structural, machine-editable
representation of the whole project, and TextFormatProjectFiles.md §2.5
confirms `externaltox` — the mechanism the whole packaging track already
depends on — carries over unchanged.

**The one new thing worth building toward: statically writing FNSTools into
a project's `.toe` before TD ever launches it**, closing the chicken-and-egg
gap where the very first install always needs a live window.

## 2. Two injection shapes, mapped onto what's actually in the file

Both are additions of one top-level JSON key (a new COMP) to an existing
`.toe`'s root object — see TextFormatProjectFiles.md §2.1. They differ only
in what that COMP's subtree contains.

### 2a. External reference (`externaltox` pointing at a launcher-fetched local copy)

The smallest possible patch — a handful of lines:

```json
"FNSTools": {
  ".node": { "type": "COMP:base", "tile": [0, 0, 160, 60] },
  ".parm": {
    "externaltox": "C:/Users/<user>/Documents/Derivative/Palette/FNSTools_ext/store/FNSTools.tox",
    "enableexternaltox": true
  }
}
```

**Confirmed**, not assumed: `externaltox` is documented as *"Path to a
`.tox` file on disk"* ([COMP Common Page / Base COMP](https://docs.derivative.ca/Base_COMP))
— a local filesystem path only. TD does not fetch it over HTTP(S); there is
no URL form. So "an online vault" can only ever be the *source*, never the
value written into `externaltox` itself.

**The launcher is the middleman, not TD.** The sequence has to be:
1. TDXLPP (already the thing writing the `.toe` in this scenario — see §3)
   fetches `FNSTools.tox` from the bucket down to a local path, same as
   `UPDATER`'s vendored `TDFileDownloader` already does for the `shared`
   binding mode today (`ConfiguratorDistribution.md` §4.2, §"Where
   installed packages live").
2. *Then* it writes the `externaltox` parameter pointing at that now-local
   path, and only then hands the file to TD.

This is **exactly the `shared` binding mode the packaging track already
ships**, just applied one layer earlier — instead of the installer setting
`externaltox` at runtime after a manual drag, the file arrives with it
already set to a path the launcher guaranteed exists. TD still does the
lazy-load itself once the project opens (same behavior externaltox has
always had); TD just never sees the vault, only the launcher does. Cheap to
generate, cheap to diff, and it inherits every trap already documented for
`shared` mode (machine-wide coupling — one store folder shared by every
project on the machine — plus the three `TDFileDownloader` traps in
`packaging-track` memory, since the launcher is now the one driving that
same downloader).

### 2b. Full inline splice (the whole bootstrap, embedded)

The heavier version: the entire `FNSTools` root subtree — every child COMP,
DAT, parameter, exactly as it appears in a real save — spliced wholesale
into the target `.toe`'s JSON tree as that same top-level key. This is what
"the bootstrapper's text form, exposed via the installer or an online
vault" most literally means: a **pre-rendered JSON fragment**, produced once
from a real dev build (a new export target — call it `ExportPortableJSON`,
sibling to today's `ExportPortableTox`), that an injector script drops in
verbatim.

Trade-off against 2a: bigger diff, and needs care around anything
`ExportPortableTox` already has to handle (nested `externaltox` survives,
`file` pars survive, absolute-path warnings — see `packaging-track` memory)
plus one thing that's new here: **ID/name collisions** with whatever else is
already in the target project. `loadTox()` in the live API handles renaming
on collision automatically (`InstallerExt.py` already relies on this: *"TD
numbers on collision; the manifest name wins"*); a raw JSON splice would
have to reimplement that collision handling itself, or simply refuse when
`/FNSTools` (or the shortcut `FNS`) already exists in the target file.

Zero network dependency after the initial fetch of the fragment itself,
which is the real advantage over 2a — once the fragment is in hand, the
resulting project is self-contained the same way `embedded` binding mode is
today.

## 3. Where this could plug into TDXLPP specifically

TDXLPP already owns exactly the moment where this would matter: **project
creation and project opening**, both already mediated by its own code
(`td_manager.rs`), not TD's. Two integration points, in order of how
disruptive they are to existing behavior:

1. **"New Project" flow gains an FNSTools-enabled starting point.**
   Simplest possible version needs *none* of this research — a pre-made
   template `.toe` (any format, even today's binary one) with FNSTools
   already embedded, offered from TDXLPP's existing Templates tab. This is
   buildable today, is not blocked on the text format at all, and is worth
   calling out precisely because it's cheap and shouldn't wait.

2. **Patch an *existing, arbitrary* project the user already has** — the
   genuinely new capability, and the one that actually matches "inject...
   at root" from the original ask. A user opens some project of their own
   in TDXLPP that has never seen FNSTools; TDXLPP (a) confirms the file is
   text-format (reads `header.settings["td.settings.project.file-format"]`
   — trivial), (b) confirms `/FNSTools` isn't already present, (c) splices
   in 2a or 2b **before** handing the file to TD, all while TD is closed.
   This is the one that closes the chicken-and-egg gap in §1 — no live
   session, no manual drag, no companion bus required for the *first*
   install. It only works on projects already saved in text format, which
   today means: none of them, until the feature ships for real (§4).

`toeexpand`'s presence in TDXLPP (TextFormatProjectFiles.md's sibling
research confirms it's Derivative's own signed binary, vendored only for a
version-header read) is a red herring for this — it's unrelated machinery
solving a different problem (which TD build a project needs) and shouldn't
be extended for this; a plain JSON parse of a text-format `.toe` needs
nothing TDXLPP doesn't already have.

## 4. Why this is not actionable yet, and what would change that

Three separate blockers stack here, and none of them are about our own
engineering effort:

1. **No schema, no stability guarantee.** Everything in
   TextFormatProjectFiles.md was reverse-engineered from one 469 KB sample
   on one experimental build. Derivative's own forum status (~Oct 2025) is
   "still a very active project" with **planned but not-yet-published**
   external schema files. Building an injector against this now means
   rebuilding it on every experimental build bump.
2. **Experimental-only, and possibly one-directional.** Derivative's own
   changelog states Experimental-saved `.toe` files could not load back into
   Official builds (as of 2023.11170; unconfirmed whether this restriction
   specifically covers text-format saves or is a general Experimental
   caveat). If it still holds, injecting into a text-format `.toe` today
   would produce a file **most of our actual user base's TD installs can't
   open at all** — the opposite of solving the adoption problem.
3. **No confirmed multi-file mode.** If `file-structure: "multi"` turns out
   to split a project into one-file-per-component, that would be a
   materially better target for 2b (splice in a whole *file*, not a JSON
   subtree inside one) — worth knowing before committing to a splicing
   strategy built around the single-file shape.

**Revisit trigger, explicitly**: this is adjacent to but distinct from the
trigger already recorded in `NativeInstallerDecision.md` ("Derivative ships
a native packaging system, in which case adopt that rail"). A text-based
project format is not itself a packaging system — it's a file format that
would let *our own* injector work without a live TD session. Both
should be watched, but don't conflate them: the native-installer decision
stays deferred on its own terms regardless of what happens here.

## 5. Recommended posture

Not a plan to execute now — a sequencing note for when the blockers in §4
lift.

1. **Now: watch, don't build.** Re-run the schema research
   (TextFormatProjectFiles.md) against each new experimental build that
   changes `header.build`, specifically checking whether `header.versions`
   integers bump — that's the signal the format is still moving under us.
2. **When schema stabilizes (even if still experimental-only):** build the
   §3.1 template-based flow first — it's low-risk, needs no injection logic,
   and ships value immediately regardless of file format.
3. **When Experimental→Official loading is confirmed fixed (or the text
   format ships as default):** prototype the §3.2 injector against 2a
   (external reference) first — it's the smaller patch, and it's the same
   `shared`-binding model the packaging track already trusts. Only reach
   for 2b (full inline splice) if the network dependency in 2a proves to be
   a real adoption blocker in practice, or once a `ExportPortableJSON`
   export path exists to produce clean fragments cheaply.
4. Throughout: treat any hand-authored JSON patch as **provisional and
   disposable** — no schema means no forward-compatibility promise, so this
   should stay a thin, easily-rewritten layer, not load-bearing
   infrastructure, until Derivative documents the format.
