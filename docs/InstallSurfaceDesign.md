---
status: in-force
summary: The install-surface makeover — one shared UI base (base.css, marker-synced) under two shells (web storefront picker, in-TD console manager), the always-available guided setup, the understated Plus rail, and the console's Updates tab over new /api/updates* routes fronting FNS_Updater. Records why the framed picker stayed a frame and became invisible instead.
since: 2026-08-30
skill: fns-packaging
---

# The install surfaces: one base, two shells

Before this work the toolkit had three token families across its web
surfaces: the website/picker look (`#0a0a0a`, amber, marketing density),
the console look (`#191b1e`, `#e8a33d`, TD-panel density), and ColorUI's
own near-copy of the console's. The most visible cost was the console's
Install & remove tab: family-B chrome wrapping a family-A page in an
iframe — a website inside a box. The least visible cost was the worst
one: **updates had a complete backend and no surface at all.**
`FNS_Updater` has carried `CheckUpdates()` / `Compare()` /
`UpdateProject()` from the start; nothing served them to a page.

## The shape

**One base.** `packaging/configurator/base.css` is the single source for
the family's tokens and shared components (buttons, chips, cards, grid,
category headings, dialogs, steps, presets, toast — plus a `body.app`
density switch). Both shells must stay single self-contained files (one
is embedded into the installer and served from a Text DAT; one doubles
as a double-clickable standalone), so the base is **inlined by
generation, not linked**: `python packaging/configurator/sync_base.py
--write` pushes the block between `/* FNS:UIBASE:START */` markers into

- `packaging/configurator/index.html` — the web storefront shell
- `FNSTools/FNS_Console/console_page.html` — the in-TD manager shell

and `tests/test_ui_base_sync.py` (a bare `sync_base.py` run) fails the
suite on drift. This is the mechanized version of the "token-for-token
with website/docs.css" hand-contract the picker already carried — which
still holds one level up: **token VALUES stay in lockstep with
docs.css**, because the /get/ flavor loads both and the inline block
wins the cascade. Change a value in both places or in neither.

**Shell 1 — the storefront** (`index.html`, still built into /get/, the
standalone, and the installer's served page by the untouched build
seams). Gains: a category quick-nav (`#catnav` jump chips built from
`category_meta`), the Plus rail (`#plusrail` — one understated line:
the free tools are the toolkit, N extras are a thank-you for
supporters; the per-tool state stays on the cards' chips), **Guided
setup as a permanent mode** (the first-run welcome + step strip,
re-enterable from the bar in every flavor; step 3 names the flavor's
real finish — Review & install where the page can install, Copy the
install script where it cannot), and an **embedded mode**: framed
inside the console (`window.self !== window.top`), it drops the hero,
sets `body.app` density, and hides the theme toggle, so the framed
picker reads as a native panel.

**Shell 2 — the manager** (`console_page.html`). The console is the
in-app home for everything after the first install: Settings (config
registry views, restyled; scope/export/import moved from the top bar
into the Settings view's own toolbar), Install & remove (the framed
picker, now seamless), contributed tabs — and the new **Updates tab**:
a count badge on the tab (painted from the store manifest already on
disk, no network), per-package rows (installed → available, state
chip, the release's `whatsnew` prose), Check for updates, update one
or all with a confirm dialog, and live narration of the pass (the
updater's own Status par, so a wedge names its hop). Failure keeps its
sentence and a next step, per the funnel doctrine.

**Routes.** The console server grew `/api/updates` (GET — `Compare()`
rows joined with `whatsnew`, plus `checking`/`applying`/`detail`),
`/api/updates/check` (POST — deferred `CheckUpdates()`),
`/api/updates/apply` (POST `{names}` — deferred `UpdateProject()`), and
`/api/updates/status` (GET — the live job's stage/results/failed), all
implemented as `Ui*` methods on `ConsoleRegistryExt`. Job kicks are
deferred out of the web-server callback with `run(..., delayFrames=1,
delayRef=op.TDResources)` — the same marshaling cure
`InstallerExt._refreshStore` applies, for the same measured reason.
`PICKER_URIS` now also forwards `/auth/*` and `/settings`, so the
framed picker's account rail (sign in / recheck / redeem / the done
step's Open Settings) answers when the console serves it; before this
those posts 404ed in the frame while the same page served by the
installer answered. The frozen paths (`/api/state`, `/api/set` —
TDXLPP reads them) are untouched.

## Why the framed picker stayed a frame

The chosen direction was "shared base, two shells, no iframe" — and the
iframe survives **as plumbing only**, deliberately. The picker's install
logic (selection/plan/install polling, the entitlement rail, gated-pick
splitting, auto-resume) is the most behavior-pinned code in the project
(`tests/test_picker_flavors.py` lifts its real source lines), and every
one of those behaviors exists once, in one file, served by one
`ServeRequest`. Re-implementing it natively in the console page would
have reintroduced exactly the two-answers drift the single-source
design exists to prevent. With the shared base + embedded mode the
frame is visually indistinguishable from native — same tokens, same
density, `--bg` on both sides of the seam — which is what the "no
iframe" choice was actually buying. If a future need genuinely requires
the catalog UI outside a frame, the extraction path is a shared
`base.js` catalog module, not a rewrite.

## The guided setup's preset bundles

The wizard's first step offers starting points. Four are fixed behavior
(*Set up like last time* / *Recommended* / *Everything* / *Pick my own*);
anything beyond them is **curation, not code**: `catalog.json` may carry

```json
"presets": [
  {"name": "VJ essentials",
   "blurb": "the live-set core: resolution, timeline, media.",
   "packages": ["AutoRes", "FNS_TimelineTools"]}
]
```

`build_manifest._presets()` validates each bundle against the very
package list that manifest ships — an unknown name is dropped and
reported (`preset_problems` on `Build()`'s return), a bundle emptied by
the filter is dropped whole, and a catalog with no curation emits no
key, so older manifests stay byte-identical. The page filters again on
boot (the same discipline as `starter`) and renders surviving bundles
between Recommended and Everything; a bundle pick routes through the
same `choose()` as every fixed preset, so a Plus item in a bundle
composes with the wanted/locked machinery for free.
`tests/test_wizard_presets.py` pins the page's filter from its real
source lines and mirrors the build guard against `catalog.json` (the
build-side guard runs only in TD, so the test is what CI sees).

**Authoring home, deliberately deferred:** presets are content (curation,
no entitlement), so per the CMS split they belong in `cms.mjs` — but
that file is mid-flight in the parameter-reference-rail session, so the
CMS field lands through or after that work, not beside it. Until then
`catalog.json` is hand-edited; the validators above make a typo loud
rather than shipped. The wizard's *flow* (steps, guards, flavor labels)
stays in the page on purpose — it is behavior, pinned by tests, and a
CMS-authored flow would be a second place the funnel is defined.

## Density pass (2026-09-10): overview first

Owner finding: /get is hard to get an overview of. Fifty-nine packages
in eight always-open sections, each card carrying a description, a
byline, three link-outs and up to five chips, under a hero, a meta
line, a chip row, a five-line core note and the Plus rail. Too much at
first glance; /get is the funnel and has to be friendly, the installer
surface may stay raw. Desktop first: this page is not a phone surface,
so a side menu is fair game.

The list, corrected in place as it lands:

1. **Collapsible category sections.** Each category renders as a
   section with a header row (glyph, name, pitch, "N tools, k
   selected", chevron). Header click toggles; open state persists per
   browser (`fns.fold`). Default on the site and the standalone:
   everything collapsed, so the first screen is the eight category rows
   and their pitches, which is the overview. Default when the installer
   serves the page (served or framed): everything open, the raw view.
   A filter query force-opens every section with a match; a preset from
   the guided setup opens the sections it selected into.
   *Landed.*
2. **Core folds away.** The core section collapses by default
   everywhere with a one-line header ("13 packages, always installed")
   and the long persistence note moves inside it. Nothing actionable
   was on the first screen there.
   *Landed.*
3. **A side rail on wide screens.** At 1000px and up the category
   quick-nav becomes a sticky left rail: glyph, name, count, selected
   count, plus Expand all / Collapse all. Clicking a rail entry opens
   that section and jumps to it. Below 1000px it stays the chip row
   above the list (the framed installer picker is narrow).
   *Landed.*
4. **Quieter cards.** Surface chips ("Toolbar button", "Pane bar
   button") leave the card; the surfaces stay searchable and ride the
   card's tooltip. Descriptions clamp to two lines (the full text is the
   tooltip). Plus, placement and integration chips stay: those change
   what happens on install. Doc links stay; site and changelog links
   render only for foreign packages, as before.
   *Landed.*
5. **Shorter hero.** Two sentences and a trimmed meta line. The steps
   strip and the guided setup are unchanged.
   *Landed.*

6. **Core is de-prioritized, same as on the website.** Owner: people do
   not need to know about it. The picker now honours the catalog's
   `deprioritized` flag: Core renders last as a quiet dashed footnote
   ("10 packages, installed with any selection"), never opens by
   default in any flavor, is off the rail, and is gone from the meta
   line; its note is one sentence. Item 2 above is superseded by this.
   *Landed.*

7. **Plus, filterable and said plainly where it surprises.** Owner
   (2026-09-11): people need a Plus-only view, and a reminder of what
   Plus is at the moments they would otherwise learn it at install
   time. A "Plus only" toggle sits in the bar (and as a link on the
   Plus rail); it narrows the list like a search, opening every section
   with a Plus tool. One sentence, `plusReality()`, says what happens to
   a Plus pick in the current flavor (sign in inside TouchDesigner /
   sign in / covered by the membership or waiting for an upgrade), and
   it appears on the rail, on the questionnaire's result (with the count
   of Plus tools in the set and a "Leave Plus out" button), and in the
   paste-script dialog (the script installs the free picks and opens the
   picker for the Plus ones). The count on the result is of what is not
   installable here, so an entitled account's own tools raise no flag.
   *Landed.*

Not in this pass: card art or per-tool screenshots (no assets), a
search-first landing (search is one keystroke away and the overview is
the point), and any change to the install/entitlement logic, which the
flavor pins keep untouched.

## The questionnaire: "Find my set"

The guided setup's first card runs a short questionnaire and ends in a
recommended selection. Questions and their options' tags live in
`catalog.json` under `quiz`; each package carries `fits`, the tags it
answers. The score is a count: how many chosen tags a tool fits, a tag
chosen by two answers counting twice. Every tool with a score is
recommended, best first, each with the answers that brought it as the
reason. The set is what several answers pointed at (score two or more,
ticked); a single-answer match is offered below it unticked under "Also
fits", so six generous answers do not turn most of the catalog into the
selection, and a thin result keeps its single matches in the set. The
reader edits the list before "Use this selection", which routes through
the same `choose()` as every preset. `build_manifest._quiz()` validates the block (an option tag no
shipped package fits is reported; a question with no options is
dropped) and emits `quiz` only when authored, so an unauthored catalog
stays byte-identical; `fits` rides each package entry presence-style.
`tests/test_wizard_quiz.py` lifts `quizScore` from the page and mirrors
the tag validation against the catalog.

Tags over direct option-to-package lists on purpose: a direct list rots
the day a tool is added and nobody remembers the four answers it belongs
to; a tag is declared once on the package and every question asking for
it picks it up. The first `fits` draft (2026-09-10) came from
descriptions, categories and surfaces and is the owner's to review in
the CMS; the questionnaire is content, so its authoring home is the
`cms.mjs` side with presets. Reachable only from Guided setup for now;
a bigger door on the site waits on seeing whether people use it.

## Classification pass (2026-09-11): categories and fits from the content

Owner: re-evaluate the installer categories and the questionnaire's
fits from the actual content, not from memory. Three readers read every
non-core package's doc, its parameters with tooltips, its manifest
surfaces and, where the doc was thin, its extension source; 46 packages,
35 with changes, applied with these judgment calls on top.

**Category moves (5, one withdrawn).** FNS_CommandKit Core to Developer (an SDK piece
you adopt while writing an extension; it was also invisible in the
picker, see below). FNS_HydroHomie Media & Output to Workflow (a water
reminder; nothing to do with media). FNS_OpToClipboard Network to
Parameters (its whole payoff is an operator reference in a parameter
expression). FNS_SetSmoothness Control to Parameters (bulk-sets one
built-in parameter; no hardware anywhere). FNS_PreviewPanel Network to
Surfaces (a pane type you look at, not a way to build or navigate).
FNS_ParentHierarchy Network to Developer was proposed (copies paste-ready
references and lists extension APIs; it reads the path bar, it does not
navigate) and withdrawn the same day: the owner disagreed, and the
counter-argument already stood here, that it lives on the pane bar
beside iopBrowser and the pair is what people meet. It stays in Network;
its `dev` fit stays, so the questionnaire still surfaces it for
component authors.

**Fits.** Twenty-four packages had tags added or removed to match the
doc; the largest corrections were FNS_AutoRes (its tags were an output
tool's; it is an Alt-placement hook), FNS_QuickTime (a toolbar clock of
time references for parameters, nothing about media or the timeline)
and FNS_TimelineTools (media, audio, keyframing and markers; the doc
says nothing about performing live). One rule was set and recorded in
the catalog comment: `visual` means the working surface is something you
look at or work in, not that a button exists; the readers had added it
to nearly every tool with a toolbar button, which would have made the
"Visual" answer match most of the catalog and inflate every set.
FNS_HydroHomie stays untagged on purpose.

**The Core gap.** FNS_CommandRegistry, FNS_PaletteRegistry and
FNS_TimelineRegistry were catalog category Core but manifest kind
tool, because `build_manifest.CORE` was never extended when they were
added. The picker draws Core by kind and skips the Core category, so
these three were never rendered and installed only as a dependency.
They are now in CORE; the change lands at the next `Build()`.

**Descriptions corrected (6)**, where the catalog contradicted the doc:
AutoRes, QuickTime, SwitchOPs, PasteFromClipboard (images only, Windows
only), Output (NDI and Spout/Syphon are half the tool), OpMenuMods
("script injection" was an implementation detail; acronym search is the
feature).

**Found, not fixed here** (content work for the docs and CMS side):
docs whose frontmatter summary is literally "YouTube breakdown"
(ResetPLS, ExprHotStrings, VSCodeTools) or a truncated sentence
(HotkeyManager, AutoRes); stub docs under 20 lines (AutoCombine,
AutoRes, SwapOps, oscMapper, GlobalOutSelect); parameters.json entries
missing or stale (FNS_Misc and FNS_CommandKit have none, ConfigHost
stops at Register while the doc lists five more, BackupCleaner has
empty help on every parameter, PreviewPanel exposes two author-side
"Stub T3D" pulses with no help); BorderlessTD doc says its features ship
on while the parameter defaults are off; ExprHotStrings doc and
parameters disagree on the promote abbreviation (#@~ vs #!~);
SetSmoothness filter-menu labels look shifted by one; ParOPDrop's Key
help describes the reverse of the doc; SearchPalette registers no
surface although it injects UI into the palette; QuickMarks ships
inactive (the questionnaire cannot promise it works out of the box).

## What update announcing deliberately is NOT

- The web/get flavor has no updates surface — updates are meaningless
  off-machine, and the shell split is what makes that free.
- The Updates tab never invents a decision: `Compare()` is the single
  decision point (update / current / locked / incompatible /
  unversioned / missing), and the tab renders its states verbatim,
  release notes attached.
- Install and update stay separate motions (the plan dialog may say an
  update exists; applying it lives here).

## Landing notes

- `index.html` is an embedded snapshot in the installer rails: after
  landing, run `EnsureDevRails()` and rebuild the rails per
  `packaging/RELEASING.md`, or the live picker keeps serving the old
  page (Phase-3 errata in `EntitlementFunnelPlan.md` documents this
  trap).
- `console_page.html`, `ConsoleRegistryExt.py` and
  `console_server_callbacks.py` are externalized with `syncfile` — they
  hot-reload on landing; the /sys console global runs a COPY of the ext
  DAT, so push + reinit (or re-promote) before testing, per
  `/fns-registry`.
- ~~ColorUI's `webui.html` still carries the third token family~~ DONE
  (2026-08-30): ColorUI inlines the synced base with its legacy var names
  mapped onto the tokens, and the console serves `/base.css` (sliced from
  the page's own synced block) so future contributed tabs link it instead
  of re-declaring a palette — the styling section of
  `docs/ConsoleTabContract.md` is now the contract. The three token
  families are one.
