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
