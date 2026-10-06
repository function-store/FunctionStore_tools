---
status: landed
summary: Shipping FOREIGN packages through the store (landed 8a280ae1) — tools whose bytes and version are owned upstream (TDXMap first). One new package kind, a catalog `source` block, a shell-side sync step, a self-managed updater state, and new curated fields for every package (author, homepage, changelog) editable in the content CMS and shown by the picker and website. Nothing changes in the upstream repo.
since: 2026-09-02
skill: fns-packaging
---

# Foreign packages

**Goal:** a tool that is NOT a depth-1 suspect of this project — its bytes,
version and licensing owned by another repo and another release rail — can
be listed in the catalog, picked in the installer, mirrored in the bucket,
authored in FNS_CMS and documented on the website, without pretending it
is one of ours. TDXMap is the first and the composite proof
(`EntitlementFunnelPlan.md`, "TDXMap is the composite proof").

**Non-goal:** replacing the upstream tool's own updater, paywall or trial.
The store installs; the tool governs itself afterwards.

## Why the rail cannot do this today (verified 2026-09-02)

- Identity is the live COMP: `build_manifest.Packages()` enumerates depth-1
  `pi_suspect` COMPs with `externaltox` under `/FNSTools`. Nothing else is
  a package. FNS_CMS `_packages()` is a copy of the same filter, so every
  CMS tab except Entitlement is blind to anything not live here.
- Version is read live off the COMP (`Pkgversion`, FNS_About first);
  artifacts are exported from live TD into `packaging/dist/`; `Stage()`
  refuses a name that vanished from `Packages()` unless declared `retired`;
  `release_one` bumps the live par.
- The store refresh only fetches artifact URLs under the configured
  `base_url` (`ExtUpdater._artifactRel`); a foreign URL is ignored.
- The retire flow treats "not in the live set" as retirable — a catalog
  entry with no live COMP looks retirable at any time.
- TDXMap specifics: dev COMP `/TDXMap` in `C:/VJ/TD/Projects/TDMap`
  (read-only Envoy on port 9123). Shell carries `Version` (1.2.0), not
  `Pkgversion`, no `FNS_About`; shortcut `TDMap`. Its release manager
  exports one locked tox to a PUBLIC R2 bucket with a flat manifest
  `{latest, version, url, sha256, notes_url, published}`. Entitlement
  (Patreon / Gumroad / 14-day demo) is enforced at runtime inside the
  locked tox; its own updater rewrites `externaltox` to
  `<palette>/TDXMap/TDXMap.tox` and reloads in place.

## The design

### 1. A foreign marker on an ordinary tool row

*Corrected while building (2026-09-02): the doc first said "a new package
kind". `kind` is the installer's and picker's STRUCTURAL axis (core vs
tool) and is tested in eight places; a third value would have had to be
threaded through every one of them to behave like a tool. Foreign is a
PROVENANCE axis, so the row keeps `kind: tool` and carries `foreign: true`
plus `updates`; only the release rail and the CMS branch on it.*

A foreign package is declared, not discovered. The declaration is the
catalog entry — the catalog is already "what a machine cannot know":

```json
"TDXMap": {
  "category": "Control",
  "description": "MIDI controller mapping with a web UI: multiple devices, banks, Smart Learn, button actions, 14-bit controls.",
  "placement": "root",
  "source": { "manifest": "https://pub-6d70b11fbdda47e1bbbb33f079ca8a7d.r2.dev/manifest.json", "tox": "TDXMap.tox" },
  "updates": "self",
  "help_url": "https://tdxmap.functionstore.xyz/docs/",
  "min_td_build": "2025.30000"
}
```

Authority rules (preflight-enforced, so authority never forks):

- `source` is what makes an entry foreign. Shape: `{manifest, tox}` for an
  upstream flat manifest (TDXMap's shape); a `{file}` variant for a
  hand-dropped artifact can come later if ever needed.
- `help_url` and `min_td_build` are accepted ONLY on foreign entries. On a
  live package they come from `FNS_About.Helpurl` and the export build;
  preflight refuses the catalog keys there.
- `updates: self | store`. `self` = the tool runs its own updater after
  install; the store only installs. `store` = the FNS updater tracks it
  like a tool (needs a `Pkgversion` par inside the artifact — TDXMap does
  not ship one, so it is `self`).
- `access`, `license`, `seats`, `recommended`, `placement` keep their
  meaning. A foreign entry CAN be gated, but gating TDXMap contradicts its
  public R2 URL and tool-governed trial; leave it `free` until the trial
  vocabulary (funnel plan 2.1) lands.

### 1b. New curated fields — for EVERY package, not just foreign ones

Opening the catalog a little is the point of this work. The fields below
are curated (a machine cannot know them), ride into the manifest, and are
therefore visible to the installer picker, the website and both CMS
surfaces. All of them are editable; none is derived.

| Key | Meaning | Consumers | Allowed on |
|---|---|---|---|
| `author` `{name, url}` | who made it; the link is optional | picker byline ("by …" next to the description, `configurator/index.html`), website badge, FNS_CMS roster | all packages; defaults to Function Store when absent |
| `homepage` | the product's own site, when it has one | picker and website link-outs | all |
| `changelog_url` | release notes when they live upstream | picker "what's new", website; foreign_sync may prefill it from the upstream `notes_url` | all |
| `help_url` | the docs page override | picker docs link, website | foreign only (live packages: `FNS_About.Helpurl`) |
| `min_td_build` | install floor | installer refusal, picker badge | foreign only (live packages: the export build) |
| `source` | upstream artifact pointer | foreign_sync, Build, Stage | foreign only (its presence defines foreign) |
| `updates` | `self` or `store` | updater compare state | foreign only (live packages are always store-tracked) |

**Not the recommendations lane.** `packaging/recommendations.json` already
carries "tools by other creators" — as LINKS: never hosted, never
versioned, its validator refuses every package-shaped field, and it
publishes without a release. A foreign package is the opposite on both
counts: we host a mirror of the bytes (pinned by sha in our bucket) and we
version it from an upstream manifest we poll. The line is whether we poll
a source and keep a copy current. Both lanes stay; neither absorbs the
other.

**Conflict surfaced, not averaged: author/credit has two possible homes.**
Today five docs carry a `credit {name, url}` frontmatter block
(`packaging/docs/TDX_SearchPalette.md` et al.) that only the website reads.
The picker reads the manifest, so a byline in the installer needs the field
in the catalog. Pick the catalog as the ONE home: `build-site.mjs` reads
`p.author` from the manifest, the five `credit` blocks migrate into
`catalog.json` `author` entries, `credit` leaves `FM_ORDER`, and the site
build refuses a doc that still carries it (same discipline as the
package/filename check). Flagged as a cleanup item in the order of work.

### 2. Resolution is a shell step, never in-process

`packaging/foreign_sync.py [names]`: for each foreign entry, fetch the
upstream manifest, download the tox to `packaging/dist/<Name>.tox` when
the sha differs, verify sha256, and write `packaging/foreign.lock.json`:

```json
{ "TDXMap": { "version": "1.2.0", "sha256": "…", "url": "…/TDXMap.tox",
              "notes_url": "…/changelog", "fetched_at": 1787188130 } }
```

`Build()` reads ONLY the lock — no network I/O on TD's main thread, which
is FNS_CMS's standing rule (upload and check_pins are shell commands for
the same reason). `Stage()` refuses a foreign entry with no lock, or whose
dist bytes do not match the lock's sha.

### 3. `build_manifest.ForeignPackages()`

Emits rows from lock + catalog: `kind: foreign`, upstream version,
`help_url` and `min_td_build` from the catalog, `surfaces` / `hotkeys` /
`requires` / `integrates_with` empty, `ops` 0, `tox_carrier: own`,
`updates` carried through, `artifact` from dist like any other row.
`Packages()` is untouched. Stage's vanished-package check and
`release_one`'s bump exclude foreign names. Upload changes nothing: the
artifact sits in dist beside the manifest, so the bucket layout, the
store refresh and `_artifactPath` all work unchanged.

### 4. Installer and updater

- Installer: a foreign row installs like any tool of its `placement`
  (TDXMap: `root`, beside the toolkit container at `/`, where `op.TDXMap`
  expects it). Embedded bind by default; the tool's own updater may repoint
  `externaltox` afterwards — that is its business.
- `Compare()` renders `updates: self` as a new **`self-managed`** state
  (sibling of the existing `component` state for pane placements):
  reported, never offered an update, never touched by `UpdateProject`. The
  installed COMP needs no `Pkgversion`. Removal works normally.
- `_isGated` / `_entitled` unchanged.

### 5. The two CMS surfaces — what is editable where

There are two CMSes and the split already exists; foreign packages add to
both rather than inventing a third place:

- **Content CMS (`website/tools/cms.mjs`)** authors `catalog.json` and the
  docs. Its package editor already writes `category`, `description`,
  `recommended` and `placement`. It gains every field in §1b (`author`,
  `homepage`, `changelog_url`, and for foreign entries `source`, `updates`,
  `help_url`, `min_td_build`), with the allowed-on rules enforced in the
  editor so a live package cannot be handed a `help_url`. Gating stays
  routed through `gate_package.py`, as today.
- **FNS_CMS (`FNS_CMS/CmsExt.py`)** stays the release cockpit. Foreign rows
  come through `_pkgMod('build_manifest.py')['ForeignPackages']` — ONE
  definition shared with the build, never a private list in the CMS.

What is read-only for a foreign row is exactly what comes from upstream or
from live TD: version, sha, artifact URL, the bump, the export, PI save
and dirt. Everything curated is editable, the same as for a live package.

- Release table: foreign rows show lock version vs published, a
  "foreign · updated upstream" badge, and a **Sync foreign** button running
  `foreign_sync.py` as the same detached subprocess pattern `/api/upload`
  uses, watched through the log. Selecting one for a release stages its
  mirrored artifact; it never bumps.
- Packages tab: shows the §1b fields per row (author, homepage, help URL
  effective vs override) and links to the content CMS editor for them;
  Parameters and Hotkeys tabs skip foreign rows (nothing to reflect).
- Retire: a foreign package retires by deleting its catalog entry; the
  retire flow learns that and stops treating "not live" as retirable for
  foreign names.
- Entitlement tab: badge foreign rows so a tier grant is a deliberate act
  (the same observability gap `TDXLUGateIntegration.md` names for
  `TDXLU_Pro`).

### 6. Website and docs

- `packaging/docs/<Name>.md` required as usual (site build hard-fails
  otherwise). Author name and link come from the manifest's `author`
  (§1b), not from doc frontmatter.
- `kind: foreign` may render as a "family product" badge; `help_url` links
  out to the upstream docs instead of the derived toolkit page;
  `homepage` and `changelog_url` become link-outs on the package card.
- The installer picker (`packaging/configurator/index.html`) shows the
  byline next to the description and the same link-outs beside its
  existing "docs ↗" link, for every package that declares them.

### 7. Tests

Next to `tests/test_publish_guards.py` and `tests/test_gate_package.py`:
foreign resolution against a fixture manifest, sha mismatch refusal,
Stage exemption, catalog key validation (`help_url` on a live package
refused), and the `self-managed` compare state.

## What landed (2026-09-02)

- `packaging/build_manifest.py`: `CURATED_LINK_KEYS`, `FOREIGN_ONLY_KEYS`,
  `CuratedLinks`, `ForeignEntries`, `ForeignLock`, `CatalogProblems`,
  `ForeignPackages`; `Build()` appends foreign rows after the live loop
  and returns `foreign` + `catalog_problems`.
- `packaging/foreign_sync.py` (new) + `packaging/foreign.lock.json`
  (committed). Understands the flat upstream shape (TDXMap's) and our own
  manifest shape (`source.package` names the row). Refuses unpinned
  upstreams and sha mismatches, leaving dist untouched.
  - **2026-09-23: a GitHub release is a third upstream shape.** Point
    `source.manifest` at
    `https://api.github.com/repos/<owner>/<repo>/releases/latest` and name
    the asset in `source.tox`. The tag is the version (a leading `v` is
    dropped), the asset's `browser_download_url` is the artifact, and the
    asset's `digest` (`sha256:<hex>`, which GitHub serves for every
    uploaded asset) is the pin; the release page is `notes_url` and the
    release body rides as `notes`. No catalog key was added: the release
    document is the manifest. A release whose asset carries no digest is
    refused exactly like a flat manifest without `sha256`. First entry:
    ParHoverMIDI_VSN1 (`updates: self`, `placement: root`, `nopick: true`),
    whose own repo publishes tagged releases and nothing else.
- `packaging/release_one.py`: Preflight blocks on `CatalogProblems` and
  unmirrored foreign; `ReleaseMany` ships foreign names without bump,
  export or PI save, refusing before the label moves when the mirror is
  broken. `Stage()` needed NO change: a foreign row without an artifact is
  "no artifact in manifest", the same refusal a failed export gets, and the
  removed-guard applies unchanged (retire = delete the catalog entry AND
  declare it, which the CMS retire action does in one motion).
- `FNS_Updater/ExtUpdater.py`: `Compare()` state `self-managed`; the
  console files it under "Up to date" as "updates itself".
- `FNS_CMS/CmsExt.py`: foreign rows in `/api/dirty` (lock vs published,
  mirrored/not, problems), `/api/foreignsync` (detached subprocess, same
  pattern as upload) + `/api/foreignlog`; retire understands a foreign
  name. There is no FNS_CMS page — `website/tools/cms.html` is the one UI
  and proxies `/api/td/*`.
- `website/tools/cms.mjs` + `cms.html`: package editor gains author,
  website, changelog, and a "Foreign package" block (source manifest,
  artifact name, updates, minimum TD build, docs URL) with the allowed-on
  rules enforced server-side (`applyCurated`); release table renders
  foreign rows with Sync + Retire; FOREIGN list tag; `credit` left
  `FM_ORDER` and is stripped on save.
- `website/tools/build-site.mjs`: author from the catalog; a doc still
  carrying `credit` fails the build; family-product / website / changelog
  badges.
- `packaging/configurator/index.html`: byline, site/changelog link-outs,
  "updates itself" chip.
- Catalog: five `credit` blocks migrated to `author`; `TDXMap` entry
  (Control, root placement, `updates: self`, min TD 2023.12120 per its
  README); `packaging/docs/TDXMap.md`.
- `tests/test_foreign_packages.py`: the offline contract across all of the
  above, including a file:// upstream round-trip of the sync.

Still open: the cold test (needs the release uploaded), and the
`min_td_build` of a foreign package is hand-declared — the upstream
manifest carries none.

## Order of work

1. Catalog vocabulary (§1, §1b) + preflight validation of the allowed-on
   rules (`build_manifest`, `pre_release_common`); `author`, `homepage`,
   `changelog_url` pass through to every manifest row.
2. Author migration: the five doc `credit` blocks move into `catalog.json`
   `author`; `build-site.mjs` reads the manifest; `credit` leaves
   `cms.mjs` `FM_ORDER` and the site build refuses it.
3. Content CMS package editor gains the new fields with the allowed-on
   rules; picker byline and link-outs in `configurator/index.html`.
4. `foreign_sync.py` + lock file + `Stage()` guards.
5. `ForeignPackages()` and the manifest row; `release_one` exclusion.
6. Updater `self-managed` state.
7. FNS_CMS rows, Sync button, retire flow, entitlement badge.
8. TDXMap catalog entry + `packaging/docs/TDXMap.md`; `npm run pages`.
9. Cold test: bare project, bootstrapper, pick TDXMap, lands at `/TDXMap`,
   its auth gate opens, its own Check / Install works, FNS updater shows
   `self-managed`, picker shows the byline and link-outs.

Estimate: three to four days on this repo. Nothing changes in the TDMap
repo.

## Deliberately deferred

- Palette-folder disk placement (`<palette>/TDXMap/`) as an installer
  step — TDXMap's own updater does that copy on first update; the
  placement vocabulary in `EntitlementFunnelPlan.md` remains to be
  settled with the trial marker.
- Gating foreign packages through the worker map; gate-minted trials.
- Foreign packages with `updates: store` (needs `Pkgversion` inside the
  upstream artifact — a one-par change upstream when wanted).
