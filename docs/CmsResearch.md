---
status: landed
summary: The two-CMS contract — website/tools/cms.mjs owns CONTENT (docs, descriptions, recommendations); the FNS_CMS component owns what needs the live project (PI publishing, Preflight, Stage, Helpurl override) plus entitlement. v1 landed 2026-08-28.
since: 2026-08-28 (owner idea, sketched in session; decisions NOT taken)
skill: fns-packaging
---

# FNS_CMS — the authoring cockpit (research)

The owner's sketch, 2026-08-28: a component **outside `/FNSTools`** that
helps manage the scattered authoring surfaces — help links, catalog
metadata, gated tiers — "so there is one source of truth or at least not
so many"; it should **interface with Private Investigator for
publishing**; and it gets a **local web UI** ("the CMS website talks to
FNS_CMS").

Every piece of this already exists as a proven pattern here, which is
why it is worth sketching rather than dismissing as scope creep.

## Why it is plausible

* **The local-web-UI pattern is the console/installer picker**: a
  loopback-pinned Web Server DAT (BIND_ADDRESS discipline from day one),
  ephemeral, port pool, page JS calling `/api/*` on the component.
* **The PI interface exists**: `Add / Save / Reload / Get_Dirt` on
  `private_investigator1`, plus `release_one.Preflight()` — everything a
  publish tab needs is already a method call.
* **It FIXES a known fragility instead of adding one.** The current
  release UI is stamped *into* PI's lister and silently reverts on
  project open because PI cannot track itself
  ([ExternalizationOwnership.md](ExternalizationOwnership.md));
  `scripts/pi_publish_ui.py` exists solely to re-stamp it. A CMS that is
  its own tracked component *calling* PI's API makes that whole class of
  loss impossible.
* **The file-authoring layer is already CLI-shaped**:
  `packaging/gate_package.py` (entitlement, both files, no drift),
  `sign_release.py`, `check_pins.py`, `rebaseline_pkgversion.py` — a CMS
  tab is a thin front-end over functions that already exist and are
  already tested.

## The three commitments (without these, do not build it)

1. **Zero owned state.** The CMS is a *pen*, never a *store*: it edits
   the repo's files (`catalog.json`, `release.json`, `wrangler.toml`,
   `packaging/docs/`, notes) and calls PI's live API. The files remain
   the sources of truth — version-controlled and diffable, which is this
   project's stated DNA (the TIERS map is in `wrangler.toml` *because* a
   KV entry changes with no record). A CMS that caches content in
   `storage` or custom pars becomes the drift source it exists to kill.
2. **It lives outside `/FNSTools`, like PI.** Dev tooling, its own
   suspect tox, never in `Packages()`, never in the manifest, never
   shipped. The public website never talks to it — the site stays a
   static build (`build-site.mjs`) that *reads the same files* the CMS
   writes. One source of truth means: the repo is the truth, the CMS is
   how you write it, the site is how the world reads it.
3. **The web UI is the console pattern, loopback-pinned, ephemeral.**
   No auth story needed beyond what the console already has, because it
   never listens beyond 127.0.0.1 and only while open.

## Scope sketch (tabs)

| Tab | Over | Does |
|---|---|---|
| Packages | `catalog.json`, `packaging/docs/` | descriptions, categories, help links, doc-stub creation (site build hard-fails without a doc — the CMS can create the stub the moment a package is catalogued) |
| Entitlement | `gate_package.py` | tier/Gumroad authoring with the same authorizability verdict `Stage()` enforces |
| Publish | PI API + `release_one` | dirty lister (`Get_Dirt`), per-package `Save`, `Preflight()` report, `Stage()` button, the upload command + `check_pins` verdict |
| Notes | release notes source | per-release notes authoring, the thing Preflight currently warns 48 times about |

## The help-links prerequisite — LANDED 2026-08-28, differently and better

This document's first draft proposed a `catalog.json` `help` field
pushed onto tools at pre-release. **That idea is superseded** — surfacing
the conflict rather than averaging it: `build_manifest._helpUrl()` had
already landed the real design (2026-08-26, measured), and it is
stronger because it needs **no field at all**:

* **Derivation IS the source of truth**: `DOCS_SITE/<name lowercased,
  `_`→`-`>/`. Measured fleet-wide, derivation did 100% of the work —
  every hand-set override tier was empty, so the old self-reporting
  ladder (host `Helpurl` → `docsHelper` `Url` → `Url`/`Helpurl`/
  `Wikipage` pars) was speculative generality that never once fired.
* **`FNS_About.Helpurl` is the ONE override**, for a slug that isn't the
  package name or docs hosted elsewhere.

What was actually missing — and landed today — was the **live half**:
the manifest and website derived perfect URLs while the in-TD consumers
still walked the dead ladder and registered `help_url = None/''` on
every entry. `RegistryBase._packageHelpUrl` now mirrors the manifest
rule (`HELP_SITE` must match `build_manifest.DOCS_SITE`; the two worlds
cannot import each other — change both or neither), and both consumers
derive registrant's-package-first: gear menus and hub tabs resolve real
docs URLs, verified live at exact parity with the manifest.

**Consequence for the CMS**: the Packages tab's help-links job shrinks
to authoring the *rare* `FNS_About.Helpurl` override (a live par,
PI-saved) and creating doc stubs — there is no file field to manage,
because the rule replaced the data.

## Open questions (decide before building)

* Does `upload.py` run from the CMS (subprocess + background job
  pattern, like `save_project`) or stay a shell step the CMS merely
  prints? The main-thread and wrangler-auth implications differ.
* Where do release notes live as a source? (Preflight wants per-package
  notes; today's source is ad hoc.)
* Does the CMS absorb `scripts/pi_publish_ui.py`'s role entirely
  (retiring the re-stamp script), and if so, does the PI lister keep any
  release affordances at all?

Per the project's own rule: if this graduates from idea to build, it
starts as a `/brief`, and its contracts land back here as an in-force
doc.

## v1 LANDED — 2026-08-28, and a correction

**This document's founding premise was wrong**: a CMS already existed.
`website/tools/cms.mjs` (`npm run cms` → 127.0.0.1:8787) is the CONTENT
cms — docs prose with stub/TODO tracking, catalog descriptions and
categories, recommendations with publisher-mirroring validation, icons —
loopback-bound, zero-owned-state, git as the audit trail: the same
philosophy this document "proposed". It also *deliberately* shows
`access` read-only ("does not offer to invent a tier id").

So the landed contract is ONE FRONT DOOR over TWO backends, same
files: FNS_CMS's page embeds cms.mjs in its Content tab (iframe; it can
also spawn it, walking ports 8787-8791 with a content-marker probe --
a port merely being OPEN proved to mean nothing when a foreign process
was found squatting 8787). cms.mjs stays independently runnable:

| | `website/tools/cms.mjs` | `/FNS_CMS` (TD, port 36770+) |
|---|---|---|
| Owns | content: docs prose, descriptions, categories, recommendations, icons | what needs the LIVE project: PI dirty/save, Preflight, Stage, `FNS_About.Helpurl` (par + PI-save in one action) — plus entitlement authoring (`gate_package`), which cms.mjs declined |
| Runs | node, `npm run cms` | inside TD, `Open` pulse |
| Never | invents tier ids, touches the live project | authors docs or descriptions |

`/FNS_CMS` shipped per `briefs/2026-08-28-fns-cms.md` (root-level beside
PI, PI-tracked itself — the pi_publish_ui reversion class is dead), all
criteria verified via curl against the served API. Upload and check_pins
remain shell commands by design. Two hazards found and fixed during the
build are recorded in the brief's Deviations: the exec-without-__name__
CLI-block hazard (TD-specific), and the in-process-HTTP main-thread
deadlock. Still open: the Notes tab (release-notes source undecided),
and retiring `scripts/pi_publish_ui.py` after one real release cycle
through the CMS.
