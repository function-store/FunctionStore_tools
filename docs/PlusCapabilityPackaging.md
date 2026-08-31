---
status: landed
summary: 'The toolkit half of the launcher''s Plus-capability work: authoring TDXLU collect/media/mobile as gated FNSTools packages, and adopting the 1.7.0 surface/capability fields.'
since: 282dd40 2026-08-31 (FNSCommand 1.7.0 port landed)
skill: fns-packaging
---

# Plus capability packaging — the toolkit half

TDXLPP's `docs/fns-plus-capabilities.md` is the launcher half of this
work: it restructures the launcher's baked-in session controls into
registry capabilities. **Its P3 phase is ours** — "the toolkit half is
authoring the packages" (their §5). This document is the FunctionStore
side: what each package needs, what is already true, and the decisions
that gate the build.

The wire contract stays canonical in TDXLPP
(`docs/fns-command-registry.md`); our implementation guide is
[CommandRegistration.md](CommandRegistration.md); what makes a package is
[packaging/CREATING.md](../packaging/CREATING.md).

## Already landed (2026-08-31)

- **`FNSCommand` carries `surface` + `capability`** (registry 1.7.0),
  ported verbatim from TDXLPP's copy — theirs is gitignored, so this
  repo is now the durable carrier. All 169 copies in the project are on
  it: 161 file-sync the master, 8 unbound ones were synced by hand.
  Verified functionally, including on the gated tool's own copy.
- Their port-notes rows 1 and 2 are therefore both closed.

## What is NOT needed

The rail and the gate already carry everything the launcher consumes —
per-package `access`, the `toolkit.tiers` ladder with labels,
`support_url`, the `fnstools/plus/` prefix, and a storage host that 401s
unauthenticated `plus/` fetches (verified against the live v3.0.9
manifest). The only recurring gate touch is **per-package**: each new
Plus package needs its `TIERS` rows in the worker's `wrangler.toml`, which
the CMS **Access** dropdown writes for you (it runs `gate_package.py`, so
`catalog.json` and `wrangler.toml` can never disagree). That is release
work, not machinery.

## The components are portable by construction

Verified by reading their source (`utility/TDXLauncherUtility/`):

- `TDXLUCollectExt.py` (856 lines) and `TDXLUMediaExt.py` (1222 lines)
  reference **no** `parent.X`, **no** `op.X` global, and reach nothing
  outside `self.ownerComp` — every lookup is internal.
- Both register through a `FnsCommands()` spec list plus a guarded
  deferred announce (`tags.add('fnscommands')` +
  `reg.Register(comp, spec)`), so they need **nothing from our
  ExtUtils** — not even the `FNSCommand` module. The capability travels
  with the component, which is the whole point of the design.
- Their specs already declare `surface` and `capability`
  (`fns.collect`, `fns.media-browser`).

So the migration is packaging, not rewriting.

## Per-package checklist

For each of `collect` and `media` (per-feature packages — owner decision,
their §6.1):

1. **Bring the COMP into `/FNSTools`** as a depth-1 child. Their
   `utility/TDXLUCollect.tox` exists; media needs an export. The
   launcher's TD instance serves Envoy on **port 9879**
   (`switch_instance`), so the export and the import can be driven
   without leaving the tooling.
2. **Sever the source binding** on arrival — `enableexternaltox=False`,
   `externaltox=''`, strip `pi_suspect` — then let PI bind it as a
   suspect here. A copy that inherits a foreign binding reloads the
   wrong tox at boot.
3. **`FNS_About` child with `Pkgversion`** (plus `Touchbuild`,
   `Helpurl`). The comp-level `Pkgversion` mirrors it by expression —
   never by a `.val` write, which severs the mirror and blocks preflight.
4. **`catalog.json` entry** — category, description, and **`access`**
   set through the CMS (writes the worker tier map in the same motion).
5. **`packaging/docs/<Name>.md`** — the site build hard-fails without it.
6. **Gated-tool flags**: `enableexternaltox` ON and `savebackup` OFF, or
   preflight blocks the release — a gated package in either wrong state
   would ride the published root tox into the public mirror.
7. Release through the CMS as usual; the pipeline supplies the pinned
   sha, `min_td_build` and the `plus/` staging.

Once a package version exists on the rail, TDXLPP starts its D7
deprecation window for the bespoke verbs.

## Decisions (owner, 2026-08-31)

1. **Names: the `TDXLU` prefix becomes `FNS_`** — `TDXLUCollect` →
   **`FNS_Collect`**, `TDXLUMedia` → **`FNS_Media`**. This is the
   irreversible one (the registry keys curation, history and presets on
   `tool#id`, where the tool part is the COMP name), but its cost is
   near zero **because the keys are one day old**: the capability
   registration that created `TDXLUCollect#collect` landed in TDXLPP's
   P2 commit `82d9036` on 2026-08-30. Nothing has had time to curate
   against the old owner keys. Renaming later would not have been this
   cheap.
2. **Tier: Base for both** — id `8323905` (the ladder grants upward, so
   Pro and Coaching inherit; this is the `FNS_TimelineTools` pattern
   already in `wrangler.toml`).
3. **Category and catalogue copy: authored by the owner** in the CMS.
   A catalog entry and its `packaging/docs/<Name>.md` must land
   *together* — the site build hard-fails on either half alone.
4. **Config scope: open**, to be decided from what the components
   actually persist once they are in the tree (`/fns-config-scope`).

## The port LANDED 2026-08-31 (`f9d9d4d`)

`FNS_Collect`, `FNS_Media` and `FNS_Remote` are in `/FNSTools` as
PI-registered suspects with their source Embody-externalized (15 files).
Exported live from the launcher project over MCP-on-HTTP (below), staged
cooking-disabled in `/sys/quiet`, then moved in. Zero errors; they
register as packages 50–52.

Four things the port had to fix — worth knowing for the next one:

1. **Foreign file bindings.** All 15 DATs pointed at
   `TDXLauncherUtility/...` paths, which in this project would resolve
   under *our* folder. Severed before the move so Embody could assign
   ours.
2. **A parent-coupled bind.** `FNS_Collect`'s `Collectexpr` was bound to
   `op('..').par.Collectexpr` — a utility-level toggle shared with its
   children there, absent on `/FNSTools`, so it errored on arrival. The
   package now owns the par at the value it had (`False`); the extension
   already read it defensively off its own COMP. A sweep confirmed it was
   the only such coupling in the three.
3. **Package furniture**: `FNS_About` + `Pkgversion` 1.0.0 + comp-level
   expression mirror.
4. **Gated flags set in advance** — `enableexternaltox` on, `savebackup`
   off — so the leak preflight passes the moment a tier is set. Note PI's
   `Add()` leaves `enableexternaltox` OFF and writes a mixed-separator
   `externaltox`; both need correcting after any `Add`.

### Config scope — answered by the code

- **`FNS_Collect`** stores one key (`TDXLUCollectLast`) via
  `ownerComp.store()`: the last run's summary. Run-result cache, not a
  preference — **no ConfigRegistry host needed**.
- **`FNS_Media`** persists nothing. None needed.
- **`FNS_Remote`** needs **no ConfigRegistry host** — corrected
  2026-08-31 after verifying the code. An earlier reading of TDXLPP's D4
  ("machine-local activation via ConfigRegistry") said it did; the
  implementation has zero registry references, and TDXLPP has since
  corrected their doc. It writes one file directly —
  `app.userPaletteFolder/FNStools_ext/config/fns_remote.json`, atomic
  via a `.tmp` — holding only `{schema, token}`.

  **Do not "fix" this into the registry.** Two reasons, both deliberate.
  It is a **credential, not a setting**: the token is minted per machine
  on first use and deliberately kept off a parameter, because parameters
  travel inside the `.toe` and a token that travels is a token you gave
  away. And the component's whole premise is working standalone in a bare
  project, so requiring a toolkit root to hold its own credential would
  defeat it. Sharing the registry's config *directory* (not its
  mechanism) is what keeps everything a user might clear in one place.

  Its user-facing settings (`Port`, `Lan`, `Active`, `Maxtouches`, the
  `Control` sequence…) are ordinary custom pars that travel with the
  `.toe`, which is normal for tool settings. If they should later ROAM
  across projects, that is an additive ConfigRegistry host — a feature
  choice, never a dependency.

  This is the standing exception to the house rule that settings persist
  through ConfigRegistry (`/fns-config-scope`): secrets do not.

### STATUS: shipped in v3.0.13 (2026-08-31), one step left

Steps 1–6 below are **done**. Only the companion release (step 7)
remains, and it is an owner decision rather than a technical block.

**What went live** (verified against the bucket, not staged):

| Package | Version | Access | `seedable` |
|---|---|---|---|
| `FNS_Autosave` | 1.0.0 | free | **true** |
| `FNS_Collect` | 1.0.0 | Base `8323905` | false |
| `FNS_Media` | 1.0.0 | Base `8323905` | false |
| `FNS_Remote` | 1.0.0 | Base `8323905` | false |

Plus `FNS_Updater` 3.0.7 → 3.0.8 and rebuilt rails at installer 3.1.0
carrying the command rail (`fns.install`, `minimal`, `source`). The
worker was deployed so the three gated packages are in the live tier map.

**The entitled path is proven, not assumed.** TDXLPP ran the gated stock
against the live gate with a signed-in supporter account:

```
entitled=true  products=[FNS_Collect, FNS_Media, FNS_Remote,
                         FNS_TimelineTools, TDXLU_Pro]
FNS_Collect    no token  -> 401
               with token -> 200, digest matches the manifest
```

The 401-then-200 order is what makes it evidence: it proves the gate
DISCRIMINATES rather than merely permits. This was the one leg never
exercised entitled — reading `wrangler.toml` only ever proved what we
intended, not what the live worker believed. It is kept re-runnable on
their side as `cargo test gated_stock_check -- --ignored`, so it is the
regression test for any future gate, worker or tier change.

**The offline path is closed**: their build fetches the bootstrap
(0.324 MB) and `FNS_Autosave.tox` (0.015 MB) from the manifest's rails
and package URLs, digest-verified. Bootstrap to install WITH, autosave to
install FROM.

Release mechanics that bit on the way through — a preflight false
positive from sub-second save ordering, and a concurrency race in the
gated upload read-back — are written up in
[packaging/RELEASING.md](../packaging/RELEASING.md), "Two things that
look like breakage and are not".

## Website copy — decided, and deliberately NOT applied yet

TDXLPP's owner settled the positioning (2026-08-31). Recorded verbatim
because the copy is written once, at their ship, and reconstructing the
intent later would produce something weaker.

**The group is named "launcher capabilities", and it describes a property
the packages HAVE, not a category they belong to:**

> A launcher capability is a complete TouchDesigner tool that ALSO lights
> up TDX Launcher Ultra's session view when both are installed.

**The load-bearing rule: it must never read as "launcher add-on."** All
four work standalone, which is both true and commercially better for us —
a visitor who wants media replacement must not be sold an accessory to a
product they do not own. So a page's first job stays "what this does in
TD", and the launcher is an additional sentence, never the premise.
`FNS_Remote` is the one inversion: serving a phone IS the product, and
the launcher merely shows a QR for it.

**No bundle.** Per-feature packages were an owner decision; three of four
being Base-tier is a pricing fact, not a product boundary.

**Today: say nothing about the launcher on the four pages.** TDXLU is
unreleased, so naming the group publicly would market a product nobody
can buy and make four standalone tools look like accessories to something
absent. The name is decided; its APPEARANCE waits for their ship.

**At their ship, append (never rewrite) per page:**

- `FNS_Collect` — "With TDX Launcher Ultra installed, this also appears
  in the launcher's session view, with a per-file confirm before anything
  is copied."
- `FNS_Media` — same, "…as a browsable media list with previews and
  replace."
- `FNS_Remote` — description already whole; add only "The launcher can
  show the pairing QR for any running session, so you do not have to open
  the component to find it." **Explicitly not "requires the launcher".**
- `FNS_Autosave` — "Works in any project with no launcher; the launcher
  renders its settings when present." The framing genuinely improved for
  this one: free, standalone, and now reaching people who never install
  the companion. It is the best evidence the split was not a paywall
  move.
- `/plus/` — name the group and give the two-sentence meaning above, with
  `FNS_Autosave` noted as a launcher capability that is FREE, so the
  section never implies capability == paid. That distinction is the one
  most likely to be lost.

Their FNS tab already badges capability packages, tooltipped with both
halves and styled quieter than the tier badge — information, not upsell.
`FNS_TimelineTools` is their control case: Base-tier but NOT a
capability, which is what proves the badge means capability rather than
paid.

## RELEASE ORDER — a hard precondition, not a preference

**The companion must not ship before these four packages are released.**
TDXLPP companion 0.23.0 has removed Collect, Media, the touch receiver
AND Autosave (their `TDXLUAutosave` is deleted as of 2026-08-31). Our
four exist but are **not released** — no catalogue, no docs, no tier — so
the rolling manifest does not carry them and the launcher's FNS tab
cannot stock them. A companion release ahead of ours would leave users
with all four features gone and no way to install the replacements.

There is no gap today, because nothing is released on either side and
`release/TDXLauncherUtility.tox` still carries 0.21.0. The order that
has to hold:

1. **Toolkit: catalogue + docs + tier** for all four. Nothing downstream
   can start until this lands, and it unlocks four things at once: the
   `launcher` block reaches the bucket, `seedable` turns true for the
   free packages, `FNS_Autosave.tox` becomes fetchable, and
   `install(package='FNS_Autosave')` answers instead of refusing.
2. **Rebuild the rails.** `InstallerExt.py` and `build_installer.py`
   changed on `dev25-launcher-boundary`, so the shipped bootstrap must
   carry the command rail (`fns.install`, `minimal`, `source`) or the
   whole boundary work is absent from what users get.
3. **Release and stage, then upload.**
4. **TDXLPP runs `npm run fns:bootstrap -- --force`.** Their fetch is
   deliberately NOT auto-pickup: a matching local copy is a no-op, so
   without the explicit force their installer ships a bootstrap older
   than what exists. Their build also prints, from this release onward, a
   note naming any free launcher-capable package it is not yet bundling —
   which is how `FNS_Autosave` announces itself.
5. **TDXLPP bundles `FNS_Autosave.tox`**, now that it is released and
   catalogued free. Bootstrap alone gives the installer, not the
   capability; `source` needs the artifact.
6. **Verify stocking against the REAL manifest**, not the demo mock:
   gated rows resolving their tier label from `toolkit.tiers`, a free
   package stocking with no token (watch for the ABSENCE of a
   `/token/download` call, since succeeding for the wrong reason is the
   failure mode), and a gated fetch going through the entitlement
   worker's token rather than the public URL.
7. **Only then, the companion release.**

Steps 4 and 5 are theirs but belong in this list: "which toolkit does a
given installer carry" is a decision made at THEIR build time and
recorded in their tracked `release/FNSTools.json`, so it is answerable
from their git history rather than ours.

**The D7 window is CLOSED (2026-08-31).** It existed only because
companions in the wild lag; with effectively nothing released on either
side — TDXLU included — it was a second implementation nobody exercised,
so TDXLPP retired the bespoke verbs outright rather than carrying them
for a version. `collect_save`, `collect_status`, `media_*`,
`autosave_get`/`set`/`now` and `repoint_assets` are gone.

Consequence, and it cuts both ways. There is now **no fallback path
anywhere**: these four packages are the only implementation of all four
capabilities, so the ordering above is not "preferred", it is the only
sequence that produces a working result. What deflates is the URGENCY,
not the order — the risk it was protecting against was users losing
features, and that population is currently empty.

Verified on our side when the window closed: **no package calls a legacy
verb.** The only external references any of the four make are the guarded
`op.FNS_COMMANDREGISTRY` announce and the guarded `op.TDXLU`
companion-presence checks. `FNS_Autosave`'s `autosave_get`/`set`/`now`
are its own COMMAND ids, which merely share names with the retired verbs
— a coincidence worth knowing before someone greps for them and panics.

### A trap this split invites, paid for once

When a capability moves, **check that the launcher UI's DATA path moved
with it, not just its entry point.** Their autosave modal drove the bus
verb only: blessing `fns.autosave` made the modal OPEN from a registry
command while every read and write still went to the companion, so
deleting the COMP would have broken autosave in the launcher even with
our package installed. Caught before shipping; the modal now prefers the
capability rail and falls back to the legacy verbs. Collect and media did
not have this shape. Check it for anything ported later that the launcher
renders richly.

### Still open

- **Catalogue + docs** (owner): category and description for each, and a
  `packaging/docs/<Name>.md` per package. The entry and its doc must land
  together or the site build fails. Nothing ships until then.
- **Access = Base** through the CMS, which writes `wrangler.toml` in the
  same motion; then `wrangler deploy`.
- **Extension class names** are still `TDXLUCollectExt` / `TDXLUMediaExt`
  inside `FNS_`-named packages. Cosmetic only — command ids key on the
  COMP name, not the class — and deliberately left alone while TDXLPP may
  still iterate, since renaming now would complicate a last sync. Worth
  doing once their D7 window closes.

## From TDXLPP, 2026-08-31: the trap had a second instance

Filed from the launcher side because the session that wrote this doc had
ended. Nothing here changes the release order — it is entirely on our
side of the boundary.

**"A trap this split invites" was right, and it caught the smaller half.**
The desktop autosave modal was one surface. The **in-TD palette page**
(`src/palette-standalone.tsx`, which renders the session bar and the
Session sub-tab) is the other, and nobody checked it.

Its Session bar read autosave through `sessionCall("autosave_get")` — the
companion bus — and D7 retired `autosave_get`/`set`/`now`. The catch block
reads "older companion without the verb", so it failed **silently**: a chip
that never showed state and a toggle that did nothing. Fixed in TDXLPP
`8bc6de3`: it resolves the `fns.autosave` pair from the session registry and
runs it over `/api/palette/run`, as `App.tsx` already did, and says "install
FNS_Autosave" when the package is absent instead of going quiet.

**Not fixed, and larger.** Auditing all 22 verbs that page may forward
against what `TDXLUUtilityExt.py` still implements: **14 live, 8 dead**. The
dead eight are the three autosave verbs plus `collect_save`,
`collect_status`, `media_list`, `media_pick_replace` and
`media_pick_status` — and the page's **Collect and Media panels still call
all five**. Two full panels (chunked progress polling, dry-run plans,
file-picker status loops) needing the same port to `fns.collect` /
`fns.media-browser`. Left calling the dead verbs rather than half-ported,
since verifying it needs a live session with both packages installed;
documented at the allow-list so it fails in one place.

**The generalisation worth keeping**: the check is not "did the modal move"
but *enumerate every UI surface that ever called the retired verb*. There
were two here, and the second had no owner — the palette page is served by
the launcher but lives inside TD, so it reads as neither side's problem.

### Three corrections to this document

1. **It contradicts itself, and the stale half reads last.** "STATUS:
   shipped in v3.0.13" says the four packages are live with tiers set and
   the worker deployed — which the gated-stock test independently confirms
   (`FNS_Collect`: 401 without a token, 200 with, digest matching the
   manifest). "Still open" further down says catalogue + docs + Access are
   outstanding and "nothing ships until then". Reading top-down lands on the
   stale half.
2. **"The modal now prefers the capability rail and falls back to the legacy
   verbs" is stale.** It is capability-only; no fallback exists anywhere,
   because the verbs are gone. Absent package -> a moved-to-package message.
   Worth stating plainly: the absence of a fallback is what makes the release
   ordering load-bearing rather than merely preferred.
3. **The `TDXLUCollectExt` / `TDXLUMediaExt` renames are unblocked.** They
   are marked "worth doing once their D7 window closes"; it closed
   2026-08-31, per this same document.

### Website, launcher side

TDXLU's own site now names the four packages, links them to its FNSTools
section, and leads with the agreed rule — a complete TouchDesigner tool that
ALSO lights up the session view. The four toolkit pages stay untouched per
the decision to wait for the launcher's ship; nothing done there depends on
this repo's site changing.

That audit turned up a launcher-side bug of the same class as the one above:
`tiers.ts` had moved the heartbeat watchdog into the free list during the
gating flip while the code still gates it. Windows and the perf readout did
go free with the session surface; the watchdog rode along by mistake. Same
lesson — when a boundary moves, the copy describing it drifts as easily as
the data path under it.

## How the export was done (no second session needed)

This session's MCP bridge is pinned to `FNSTools_PRIV` (port 9899) and
`switch_instance` only lists instances that bridge knows, so the launcher
project was unreachable that way. Envoy serves **MCP over HTTP inside
TD**, so the launcher's own server (port 9879) can be driven directly
with a small JSON-RPC client — initialize, then `tools/call
execute_python` — with no MCP reconfiguration and no switching. That is
the general recipe for any two-project operation here.

## Superseded: the manual export ask

No on-disk artifact carries the current components. Both candidates
predate the capability work of 2026-08-30:
`release/TDXLauncherUtility.tox` is from 08-28, `utility/TDXLUCollect.tox`
from 08-14, and `TDXLUMedia` has no tox at all. The extensions are
externalized and current, but a `.py` is not a component — the COMP
structure (panels, `body/list_media`, `info_sync`, the parexecs, custom
pars) lives only in the launcher project.

The launcher's Envoy (port 9879) is not in this bridge's instance
registry, so this session cannot reach it. Two lines in that project
produce what is needed:

```python
op('/TDXLauncherUtility/TDXLUCollect').save('C:/VJ/TD/Projects/TDXLPP/utility/FNS_Collect_port.tox')
op('/TDXLauncherUtility/TDXLUMedia').save('C:/VJ/TD/Projects/TDXLPP/utility/FNS_Media_port.tox')
```

Loading them here happens in a cooking-disabled container first
(`/sys/quiet`) — the established rule for staging foreign components, so
nothing self-promotes into `/sys` or injects a palette tab on arrival.

## Surface adoption — DECIDED: ported capabilities only (owner,
2026-08-31)

**The existing tool fleet does not get `surface=`.** Only what comes
across from TDXLU carries it — and those specs already declare their own
surfaces, so nothing needs adding by hand.

This was proposed the other way (promote the 14 state-bearing toggles —
`AltSelect`, `AutoRes`, `AutoCombine`, borderless/fullscreen, timeline,
`OpToClipboard`, `ParOPDrop`, `ParRandomizer`, `QuickCollapse`,
`QuickMarks`, `QuickPane`, `QuickParCustom`, `SwitchOPs`) and declined.
The reasoning to keep: the launcher's Current bar is a **session
capability** surface, not a mirror of the tool fleet. Filling it with
every toolkit toggle would cost 14 decorator edits, 13 PI saves and a
release to make the bar noisier and less about the session in front of
you. The tools remain fully reachable where they belong — quick-launch.

A corollary worth remembering if this is ever revisited: a session-bar
click happens in the LAUNCHER, not in TouchDesigner, so any command
scoped to the current selection or TD focus (`Clear custom pars of
selected`) is ambiguous when driven from another window and should never
carry `session` regardless.
