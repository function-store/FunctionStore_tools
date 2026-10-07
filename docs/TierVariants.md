---
status: open
summary: 'A tool with a Base and a Pro form ships as ONE package whose two builds come from TWO separate .tox masters (option C, refined by the owner the same day). One catalog entry, installed name, version line, settings, docs page and picker row; the masters may diverge and may share code through a clone master. Records what the code already supports (the installer names a landed COMP after the manifest, a dotted variant name needs no worker change), what has to change (Packages() would list the Pro master as its own package, variant masters need source withholding, Pkgvariant joins the update decision), why A and B were not chosen, owner questions, and the build order.'
since: 2026-09-15 (owner chose option C, then made the Pro build a separate .tox)
---

# Tier variants: one package, two masters

## The decision

Owner, 2026-09-15, in two steps.

1. When a tool has a Base form and a Pro form, it ships as **one package
   with two builds**. A Base patron installs the Base build, a Pro patron
   installs the Pro build, and to the user they are the same tool: one
   catalog entry, one installed name, one version line, one set of
   settings. Moving up a tier swaps the build in place.
2. **The Pro build is a separate `.tox`.** That is how the two stay
   separate. The Base and Pro masters may diverge, and they may share
   classes and sources, but each is its own file.

Nothing is built yet. This records the shape, what it changes, and what
still needs an answer.

## What the code already supports

Checked on 2026-09-15.

- **Entitlement is a flat list of names.** The session claim carries
  `products`, and the worker serves a gated artifact only when
  `claims.products.includes(name)` (`worker/src/index.js`,
  `handlePlusDownload`). The tier ladder is the same name repeated in
  every tier from its minimum upward.
- **A Pro-minimum gate is expressible.** `gate_package.py`'s
  `LadderFrom(tier)` writes a name into that tier and every tier above
  it, so gating at Pro lands in Pro and Coaching and leaves Base out. It
  has never been exercised: every gated package is Base, and even
  `TDXLU_Pro` is listed in all three tiers.
- **A dotted variant name needs no worker change.** The download route
  matches names with `[A-Za-z0-9._-]+`, so
  `plus/<release>/FNS_Foo.pro.tox` captures `FNS_Foo.pro` and checks it
  against `products` like any other name.
- **The installer names the landed component after the manifest.**
  `InstallerExt.py` renames whatever `loadTox` produced to the manifest
  name ("the manifest name wins"), except for a pane spawn. So the Pro
  master can carry its own name in the dev project and still land as
  `FNS_Foo`, which is what keeps the command registry, hotkeys and
  settings attached across a swap.
- **Field clients read exactly one `artifact` block.** `InstallerExt.py`,
  `publish.py` and six places in `ExtUpdater.py` read `pkg['artifact']`.
  Keeping that block on the Base build means every updater already
  installed picks Base, the safe answer for a client that predates
  variants.
- **Shared code has an established pattern.** ExtUtils and the registry
  hosts reach many packages as clone masters, policed by
  `extutils_distributor`. CLAUDE.md records the two costs: a clone-driven
  change to children is a blind spot for the dirty flag, and cloning
  forces a component's children, never its own parameters.

## What has to change

### Two masters in the dev project

- The Base master is the package as today: `/FNSTools/FNS_Foo`, suspect
  tox `modules/suspects/FNSTools/FNS_Foo.tox`.
- The Pro master is its own suspect beside it, under a distinct name
  because two siblings cannot share one: `/FNSTools/FNS_FooPro`, tox
  `modules/suspects/FNSTools/FNS_FooPro.tox`.
- **`Packages()` must not treat the Pro master as a package.** Today it
  lists every depth-1 suspect with its own tox, so `FNS_FooPro` would get
  its own manifest entry, and the site build would then demand a catalog
  entry and docs page for it. The catalog names the Pro master as a
  variant source (below), and `Packages()` skips any component a variant
  claims.
- **Anything keyed on the component name reads it live.** The installed
  copy is renamed to `FNS_Foo`, so a name baked in at build time
  (`FNS_FooPro` in a global shortcut, a tag, a config key, a string in a
  callback) breaks after install. Command ids already key on the live
  name.
- **Both masters are live in the dev session.** Each will register its
  commands and hotkeys, so the dev project sees duplicates. Decide per
  tool whether the Pro master is kept dormant while the Base one is
  worked on, or the other way round.

### Shared code

The masters share code through a **clone master**, the pattern ExtUtils
and the registry hosts already use: the shared classes live in one child
component, and the other master's copy clones from it.

- **Shared code lives on the Base side.** It ships to Base patrons in the
  Base build anyway. Placed in the Pro master, it would be withheld from
  the public mirror while the Base source that depends on it publishes,
  and a free Base tool would publish source that cannot run.
- **A shared-code edit dirties both masters without the flag noticing.**
  Save the component that owns the edit, then walk to every master that
  carries a clone of it and save those explicitly, parents after, root
  last, as CLAUDE.md prescribes for clone surgery.
- **Divergence is allowed and expected.** Nothing requires Pro to be Base
  plus extras. What has to hold is listed under Settings across a swap.

### Settings across a swap

A swap replaces one build with the other under the same name, and
settings are keyed to that name. So:

- A parameter that exists in both masters keeps **the same name and
  meaning** in both. Renaming it in one master silently resets it on
  every swap.
- A Pro-only parameter is simply absent from the Base build. Its saved
  value is left in place and returns if the user moves back up.
- Both masters carry the same config host identity, so the settings
  follow the installed name.

### Catalog

`access` stays the minimum tier for the package, the tier that gets the
Base build. A new block names the rest and where each build comes from:

```json
"FNS_Foo": {
  "access": "8323905",
  "variants": {
    "pro": { "access": "8291595", "source": "FNS_FooPro" }
  }
}
```

`gate_package.py` writes `FNS_Foo` from Base upward and `FNS_Foo.pro`
from Pro upward, and `wrangler deploy` follows as for any gating change.

### Identity on the installed copy

Each master's `FNS_About` carries its own constant `Pkgvariant` (`base`
in one, `pro` in the other), mirrored to the component by expression as
`Pkgversion` is. No build step stamps it; the master says what it is. The
severed-mirror preflight check covers it.

`Pkgversion` is still one line for the package. Preflight refuses a
release when the two masters disagree on it.

### Build and publish

- Each master exports through the existing `ExportPackage()` path: the
  Base master to `FNS_Foo.tox`, the Pro master to `FNS_Foo.pro.tox`. A
  gated Base build and every Pro build go under `plus/`; a free Base
  build goes on the public rail.
- The manifest keeps `artifact` as the Base build and adds each variant's
  own:

  ```json
  "artifact": { "path": "...FNS_Foo.tox", "sha256": "..." },
  "variants": {
    "pro": {
      "access": "8291595",
      "artifact": { "path": "...FNS_Foo.pro.tox", "sha256": "..." }
    }
  }
  ```

- Each variant has its own bucket key, so the immutable-release rule holds
  as it is.
- `verify_release.py` enumerates variant artifacts; the Pro build is
  checked through the authenticated read described in `RELEASING.md`.
- `shipped_builds.json` records a build per variant.
- **Guard:** the Base master must not contain the Pro master as a child,
  or the Base artifact carries Pro bytes. Preflight checks that no variant
  source sits inside another master.

### Install and update

- The installer installs the highest variant the account is entitled to,
  asking `IsEntitled('FNS_Foo.pro')`, and lands it under the manifest name
  either way.
- The update decision today is `Pkgversion` alone. With variants an update
  is offered when the release has a newer `Pkgversion`, or when the
  installed `Pkgvariant` is below the best variant the account holds. A
  Base patron who becomes Pro gets a swap at the same version.

### Source withholding

`publish_public.py` derives gated source from catalog names:
`_gatedPrefixes(name)` withholds `FNSTools/<name>/` and the suspect tox
for each gated package. A Pro master lives under its own name,
`FNS_FooPro`, which no catalog entry names directly.

- **Today a Pro master is withheld by fail-closed.** Verified 2026-09-15:
  `FNSTools/FNS_FooPro/FooProExt.py` and
  `modules/suspects/FNSTools/FNS_FooPro.tox` both resolve to
  `undeclared:FNS_FooPro`. `KnownPackages()` reads only the catalog's
  package keys, so naming the master inside `variants.pro.source` leaves
  it unknown and still withheld.
- **The risk is the change that teaches the publisher about variants.**
  The first time `KnownPackages()` learns variant sources, for instance to
  stop a free Base tool's shared paths reading as undeclared, fail-closed
  stops covering the Pro master. The same change must add every
  `variants.*.source` whose variant `access` is not free to
  `GatedPackages()`, with a test that plants a Pro master and expects its
  tree withheld once the publisher knows its name.
- The root-tox guard applies unchanged: each master is carried by its own
  tox, or the published root tox would embed it.

### Site and picker

One card, one docs page. The picker reads `variants` to say what the Pro
build adds and which tier it unlocks at, using the tier labels the
manifest already ships.

## Rules this changes

Both are written into `packaging/RELEASING.md` and the `fns-packaging`
skill when the work lands.

1. **"Pkgversion governs updates"** becomes **"Pkgversion and Pkgvariant
   govern updates"**, both read live off the installed component. Hashes
   still only verify downloads.
2. **One package, one master, one artifact** becomes one package with a
   master and an artifact per variant, in `Packages()`, the installer, the
   updater, `Stage()`, `verify_release.py`, `shipped_builds.json` and
   `publish_public.py`.

## The alternatives that were not chosen

**A. One build, Pro features unlocked inside the tool.** Cheapest, and it
protects nothing: the Pro code reaches every Base patron, the Python is
readable, and `IsEntitled()` reads a `products` list stored on the user's
machine while the updater's Ed25519 check covers only the manifest. It
would also switch Pro features off on a lapse while Base features kept
working, which breaks the rule that installed packages are untouched.

**B. A Base package plus a separately catalogued Pro add-on.** Protects the
code, and costs two picker rows, two catalog entries, two docs pages, two
permanent names, a hook in the base for the add-on to plug into, and a fix
to the installer, which has no guard against removing a package another
one requires.

C with separate masters keeps B's protection (Pro bytes reach only Pro
patrons, from a file of their own) under A's single identity.

## Open questions for the owner

1. **Lapse.** A Pro patron drops to Base. Their installed Pro build stays,
   as every package does today. At the next release the account holds only
   the Base build: offer it (they gain fixes and lose Pro features) or hold
   them on the Pro build they have?
2. **Dev session.** With both masters live, commands and hotkeys register
   twice. Keep the inactive master dormant, or accept duplicates in dev?
3. **Shared code home.** A clone child inside the Base master that the Pro
   master clones from, or a neutral master both clone from? The first is
   simpler; the second keeps either master deletable.
4. **Variant ids.** `pro` as a tier word generalises to `.coaching`.
   Confirm ids are words, since the tier numbers are Patreon's.
5. **Coaching.** Its own build ever, or does the ladder cover it by
   inheriting Pro?
6. **Upgrade prompt.** For a Base patron, does the picker show the Pro build
   as a locked upgrade on the same row?

## Decisions taken (owner, 2026-09-17)

1. **Lapse: hold them on Pro.** A Pro patron who drops to Base keeps the
   installed Pro build and the updater stays silent for that package
   until the account holds Pro again; they miss fixes rather than lose
   features. So the update decision is: a newer `Pkgversion` for the
   variant the account can have, and never a swap downward.
2. **Shared code lives in a clone child of the Base master**, when there
   are two masters at all.
3. **Coaching inherits Pro.** Variant ids are words; only `pro` exists,
   and adding one later is additive.
4. **The picker shows the Pro build as a locked upgrade on the same row**
   for a Base patron, with the same words on the site.

And a refinement from the first real case, SimpleSceneChanger (handover
2026-09-17): its repo keeps ONE master whose release hook builds Base
(stripping the Pro extension, the cue timer and the CHOP chain) or Pro
(adding pages, per-scene block parameters and swapping the extension)
from the export file name. Two live masters are therefore optional: a
variant `source` may name the same master with an export `edition`, and
the artifact side (two files, two bucket keys, `Pkgvariant` on each
build, the gate name `.pro`) is unchanged. Two masters remain the shape
for a tool whose builds diverge in the network itself.

## What the first case chose (owner, 2026-09-17, after v3.2.24)

SimpleSceneChanger shipped once as one row with a Pro build, and the
owner then chose TWO packages after all: a Pro member may prefer the
simple one, or want both in one project (they form a fleet together),
which one name with two builds cannot give. So `FNS_ProSceneChanger` is a
real second master beside `FNS_SimpleSceneChanger`, its own suspect tox,
its own tier, row, page and version line; in development its DATs bind
the Base master's source files (shared code as shared source), and the
shared release hook builds the edition off the master's name. The
variant machinery stays built and tested for a tool where one name with
two builds is the right shape; nothing uses it today.

## Build order

Each step lands and verifies before the next.

1. Source withholding, in the same change that makes the publisher aware
   of variant sources: `GatedPackages()` includes every gated variant
   source, with a test that plants a Pro master listed as a variant and
   expects its tree withheld, for both a gated and a free Base.
2. Catalog `variants` block with `source`, and `gate_package.py` writing
   the `.pro` name from the variant's tier upward.
3. `Packages()` skips variant sources; preflight refuses a release when
   the masters disagree on `Pkgversion` or one master contains another.
4. Export each master under its variant's artifact name; `build_manifest.py`
   emits `variants` with `artifact` left on the Base build.
5. `Stage()`, upload, `shipped_builds.json` and `verify_release.py` per
   variant.
6. `Pkgvariant` on each `FNS_About` with its mirror and preflight check;
   the installer picks the variant; the updater's compare includes it.
7. Picker and site copy.
8. **Walk it with a Base test account and a Pro test account.** The creator
   account holds the top tier, so it is entitled to every name and passes
   every check; a walk on it proves nothing about the gate. The Base
   account must see the Pro build refused with `not_entitled`, and the Pro
   account must receive it. Swap Base to Pro and back, and confirm the
   settings both builds share survive each swap.
