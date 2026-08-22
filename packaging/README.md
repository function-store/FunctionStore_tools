# Packaging

Machinery for shipping the toolkit as **pickable packages** instead of one
monolith — step 2 of `docs/ConfiguratorDistribution.md` §4. The dependency
audit that gates all of this is §1.1 of that document.

```
RELEASING.md        the runbook: how to ship (Guided Release, preflight, rails)
catalog.json        curated: category + description (the only hand-written data)
build_manifest.py   runs inside TD; derives everything else, writes manifest.json
manifest.json       generated catalog the configurator and FNS_Updater both read
configurator/       static picker over manifest.json -> selection.json
                    or a one-line Textport install script (the paste rail)
dist/               exported .tox artifacts (gitignored; rebuild on demand)
```

This file describes the **mechanisms** — what the pieces are and why they
are shaped this way. The dev activity of actually shipping (the Guided
Release wizard, preflight, rebuilding rails, staging, notes) is
[RELEASING.md](RELEASING.md).

## What is derived vs curated vs declared

**Derived live** — package list, surfaces, dependencies, optional
integrations, op counts, help URLs, artifact hashes. Re-running the
generator picks up reality.

**Curated in `catalog.json`** — `category` and `description` only: the two
things the project genuinely cannot tell us. Descriptions were seeded by
inspection and **need owner review**.

**Declared on the component** — `Pkgversion`. The one field a human must
maintain, and the only one the updater compares. It is deliberately not
derived: everything derivable was either untrustworthy (artifact hashes —
`.tox` export is not reproducible) or owned by another tool (`vc_data`
belongs to Private Investigator; a TDN fingerprint would depend on an
external package).

## The dependency model

Tools depend only on **core**, never on each other, so the configurator needs
no solver. That is enforceable rather than merely asserted: core is the RAW
REGISTRIES (each package IS its master -- promoted to `/sys`, cloneable by
anyone extending the toolkit) plus `FNS_Updater`, and tools ship stamped
*hosts*, so a package's `requires` is exactly the registries it hosts. Every
tool requires `FNS_ConfigRegistry` (settings persistence); a tool with a
toolbar button also requires `FNS_ToolbarRegistry`, and so on. The FNS_* surface shells
(Toolbar/Navbar/MainMenu/OpMenu extras) are ordinary optional tools that
require their own registries like everything else.

Anything a package reaches for beyond that is an **optional integration**
(`integrates_with`) and must degrade when the other package is absent — the
guarded-lookup idiom from `ConfiguratorDistribution.md` §1.1. The generator
detects both reference forms, bare `op.X` *and* guarded
`getattr(op, 'X', None)`; missing the guarded form would under-report exactly
the correctly-written integrations.

## Package identity

A shippable package is a depth-1 COMP that is a tracked `pi_suspect` with its
own `.tox`. That is already the project's unit of distribution, so no second
list has to be maintained by hand — add a tool the normal way and it appears.

## The droppable rails

`packaging/dist/FNSTools.tox` (~150 KB) is the **one-drop
bootstrap**: the (empty) toolkit root itself, carrying the installer COMP,
a copy of the FNS_Updater package, and the vendored palette webBrowser
(`packaging/webBrowser.tox`). The container you drop IS the install
target, so a bare project goes from nothing to installed without leaving
TD. Its FNS_Updater copy needs no special adoption: updates compare
`Pkgversion` read live off the component, so the first update pass treats
it like any installed package (self-update path included). Deliberately a
plain container — the dev root's Active/UI parameter surface belongs to a
populated toolkit, not to the shell the installer fills.

**Three root pulses, three roles.** On the toolkit root's `FNSTools` page:
**Pick Tools** installs and removes — once `FNS_ConfigRegistry` is
installed it opens the FNS console on its *Install & remove* tab (in the
webBrowser panel beside the installer when the root has one), and only
the bare bootstrap, before core exists, falls back to the installer's own
served picker; **Open Settings** opens the console on its *Settings* tab
in the same panel (export writes its file server-side as well, so it
never depends on the browser's download handling); **Installer
Parameters** opens the manual rail — `Selection`,
`Plan`, `Install`, package-file mode. `EnsureRootEntryPoints(op.FNS)`
re-applies labels, help and the forwarder DAT after editing them in
`build_installer.py`.

**The configurator is served, not downloaded.** The installer carries the
picker page (embedded at build time) and a Web Server DAT, dormant until
the installer's own **Pick Tools (browser)** pulse: it serves
`http://127.0.0.1:<Port>/` and opens
it in the sibling webBrowser panel (system browser as fallback). The page
gets its catalog from `/manifest.js` — the store's manifest, and when the
store is empty the server kicks the sibling FNS_Updater's **Refresh Store**
while the page shows "downloading" and polls. The selection comes back as
a POST: plan shown in the page, **Install** run from it. No file leaves
the browser; the same page still works as a plain double-clicked HTML
(static mode = download `selection.json`).

`packaging/dist/FNS_Installer.tox` (~14 KB) is the bare installer, for a
project that already has a toolkit container. Same served picker, minus
the webBrowser panel — Pick Tools opens the system browser.

**One file, three flavors.** `configurator/index.html` is served here,
double-clicked as `configurator-standalone.html`, and published as
`/get/` — so every style it needs is inline and every documentation link
it builds is absolute (`https://tools.functionstore.xyz/...`). A
root-relative `/docs/` would point at the installer's own web server.
The site build dresses it in the real site header and footer by replacing
the `<!-- FNS:HEADER -->` and `<!-- FNS:FOOTER -->` markers, and refuses
to build if either goes missing; do not delete them. Category glyphs and
pitches come off `category_meta` on the manifest — curated in
`catalog.json`, edited in the website CMS — so the picker heads its
sections exactly like the site does, with or without a site to ask.

**The rails live in the dev root.** `FNS_Installer` and `webBrowser` are
residents of the live `FNSTools` root, beside `FNS_Updater` — the bootstrap
is that root castrated (tools stripped, rails kept), so what you drop is
what we develop in, rail for rail. `EnsureDevRails()` in
`build_installer.py` creates them when missing and otherwise re-embeds the
installer's two source snapshots (`InstallerExt.py`,
`configurator/index.html`) in place; `BuildBootstrap()` does the same
refresh on the staged copy and blanks the installer's per-project state, so
a shipped installer is never older than the sources. The dev installer is a
Private Investigator suspect like its siblings; `build_manifest.RAILS`
keeps rails out of `Packages()`, and the bootstrap build cuts the shipped
copy's `externaltox` binding. The dist artifacts are
still BUILD ARTIFACTS: editing either source means re-running the rails
refresh and rebuilding (the bootstrap also embeds `dist/FNS_Updater.tox`).
Preflight flags stale rails; how to rebuild — a wizard button or two
Textport lines — is in [RELEASING.md](RELEASING.md).

`InstallerExt.py` is the single implementation; `install.py` is a thin
script wrapper over the same code, so the droppable rails and the headless
rail cannot drift apart.

## The FNS webBrowser

`packaging/webBrowser.tox` is TD's palette webBrowser made ours, and
`/FNSTools/webBrowser` is its master -- the rail instance and ColorUI's
panel browser both **clone** it (guarded `op.FNS.op('webBrowser')`
expression; the shipped rail is cut loose from cloning at build time).
What changed from the palette:

- **Visibility policy inside.** *Render Only While Window Open* follows
  the panel value `winopen`; *Render Only While Viewer Active* polls the
  node's Viewer Active flag once a frame. Either on = `Active` follows
  visibility (`watch_rules`/`watch_window`/`watch_viewer`/`watch_pars`
  inside); both off = `Active` is yours. A Web Render cooks a whole
  browser process otherwise, and this component ships to every user.
- **Source on the component.** `Source` (URL or File / DAT) and `Source
  DAT` mirror the Web Render TOP's own, so an instance that renders a DAT
  (ColorUI: `webui_html`) configures that on its custom parameters --
  which is what lets it stay a clone: clone sync replaces the children,
  and per-instance configuration must not live there.
- **One robustness patch** in the palette's `parexec1`: it tolerates an
  empty Info DAT, which a dormant Web Render has. Re-vendoring from the
  palette loses all three; edit the master instead.

## Console exposure ships dormant

Every artifact ships with **Expose to Console off** on any `FNS_Console`
host it carries (`pre_release_common.py`), and `InstallPlan` flips it on
as the package lands (`ExposeConsoleHosts`). One artifact serves both a
standalone drop (local mode, no console raised) and a toolkit install
(exposed). Updates never touch the flag; the config registry persists the
user's choice. Full reasoning in `docs/FNS_Console.md`.

## End to end

1. Drop `dist/FNSTools.tox` (from the bucket) into the
   project.
2. On its `FNS_Installer`, pulse **Pick Tools**. First run: the page says
   it is downloading the catalog while the store refreshes.
3. Pick tools in the panel, hit **Review install…**, read the plan, hit
   **Install**. Packages land in the dropped container.

The manual rail still exists: **Selection** takes a `selection.json`
(from `configurator/configurator-standalone.html` or the served page's
static mode), **Plan**, **Install**. **Manifest** may stay blank — it
defaults to the palette store's manifest, and artifacts are found beside
whichever manifest is read.

Or headless, no COMP:

```python
exec(open('packaging/install.py').read())
Install('packaging/example-selection.json')
```

**Or the paste rail, no download at all.** `tools.functionstore.xyz/get/`
serves the same picker (emitted by `website/tools/build-site.mjs` from
`configurator/index.html`, manifest baked in at site build). **Copy
install script** turns the selection into ONE Textport line that embeds
only the picked names — release, URLs and hashes are resolved from the
ROLLING manifest at paste time, so a copied script stays valid across
releases. The line fetches core + selection + bootstrap from the pinned
release URLs, verifies every sha256 BEFORE writing anything, stocks the
palette store (where `DefaultManifest()` already looks), loads the
bootstrap into the current network editor and hands its installer the
selection one deferred `run()` later. It needs the `rails` hashes that
`Stage()` stamps, so it refuses a manifest published before those existed.

**Install tests must target a cooking-disabled container.** A live copy of a
registry master will otherwise try to promote itself to the `/sys` global and
destroy the running one:

```python
t = op('/sys/quiet').create(baseCOMP, 'trial'); t.allowCooking = False
Install('packaging/example-selection.json', target=t.path)
```

## The bucket

Distribution is **buckets and manifests only** — native `.exe`/`.dmg`
installers are the bootstrap, and there is no GitHub-based update flow.
The bucket is the single source of truth for what exists and what the
bytes are; `base_url` in the manifest says where to fetch. `Stage()`
(see [RELEASING.md](RELEASING.md)) lays out `packaging/publish/` to
mirror it exactly, then **re-hashes every staged file against the
manifest** and refuses to report `ok` on any mismatch — publishing bytes
that disagree with the hashes an installer verifies is worse than not
publishing.

```
<release>/manifest.json      immutable snapshot
<release>/<Package>.tox      immutable artifacts
<release>/FNS_Installer.tox               bare installer (root already exists)
<release>/FNSTools.tox    one-drop bootstrap root
manifest.json                ROLLING pointer to the newest release
```

The rails are not packages (no `Pkgversion`, never update-compared), but
`Stage()` hashes them into the STAGED manifests under `rails` — bytes,
sha256, pinned URL per rail — so the website's paste script can verify
the bootstrap it downloads. Only the staged copies carry `rails`:
`build_manifest.py` cannot know these hashes because the rails are built
afterwards by `build_installer.py`.

Releases are **pinned**: artifact URLs carry their release, so a manifest
always resolves to the bytes it was built from. The rolling root copy only
answers "what is current?" once. Never publish a mutable
`latest/<Package>.tox`.

## Versioning

**`Pkgversion` drives updates.** Every package carries a `Pkgversion`
parameter on its `About` page — ours, stamped on the component, shipped
inside the artifact. The manifest publishes it and the updater compares it
against the same parameter read live off the installed component, which is
what makes the comparison work for a package embedded in a `.toe` with no
file to consult.

**Bump it whenever you change a package.** It is hand-maintained, and
forgetting is silent — nobody's install learns there is anything new.
`publish.py` refuses to stage a new release that bumps nothing, which
catches the common case.

Hashes are still in the manifest and still matter, for the job hashes are
actually good at: **verifying a download arrived intact.** They cannot
decide updates, because `.tox` export is not reproducible — exporting one
untouched component three times gave 66198 / 66190 / 66150 bytes and three
different hashes, diverging at byte 9 of the container header. Comparing
them would mark all 39 packages updated on every release.

The `release` label (`release.json`) names the drop, for changelogs and
support conversations.

## Updating an install

The FNS_Updater package consumes what this directory publishes. Two
motions, deliberately separate (design record:
`ConfiguratorDistribution.md` §4.2):

- **Refresh Store** — fetch `<Base URL>/manifest.json` and every artifact
  whose bytes differ into `<user palette>/FNStools_ext/store/`.
  Machine-wide; touches no project.
- **Check for Updates** / **Update This Project** — compare the open
  project's `installed` table (package → the sha256 it was installed from)
  against the store, and replace only what differs. Per project, explicit.

**The store is a mirror, and both rails treat it as one.** Nothing in it
is anyone's work, so a store file whose sha256 disagrees with the store's
manifest is stale cache, never a modification to preserve: Refresh Store
re-downloads it, and the installer's plan marks it `stale` and fetches it
before installing — a present-but-lagging cache must not install
yesterday's bytes under today's hashes. Files *outside* the store (a dev
checkout's `dist/`, a hand-pointed manifest) get the opposite treatment:
a hash mismatch there can be deliberately staged local work, so it is
reported as a warning and never overwritten. (Testing without a bucket —
pointing `Base URL` at a local tree — is in
[RELEASING.md](RELEASING.md).)

`installed` is written by both rails — `InstallerExt.RecordInstalled` on
install and the updater on every replacement — so the two must keep the
same four columns. It records the hash of the bytes that actually landed,
not the manifest's promise, and it lives in the project because it is
project state.

### Where the package files live

The installer's **Package Files** menu decides, and the updater follows
whatever binding each package actually has — there is no mode to keep in
sync:

| Mode | Files | Update path |
|---|---|---|
| `embedded` (default) | inside the `.toe` | replace the COMP from the store artifact |
| `shared` | bound to the palette store | rewrite + reload (often just a reload) |
| `project` | copied to `<project>/FNStools/` (or **Package Folder**) | rewrite + reload |

**A bound package updates by rewriting its file and reloading** — no
copy/destroy of an extension-bearing COMP, and the change is a file you can
see and version-control. `shared` means one copy per machine, so refreshing
the store reaches every project that shares it; `project` keeps each
project's copies its own, which is what lets one project hold a modified
package without affecting the others.

Settings are not in the `.tox` — they live in
`<palette>/FNStools_ext/config/FNStools_config.json`, and each tool's
ConfigRegistry host re-applies its section when it re-registers after the
reload. Rewriting a package cannot lose them.

A package whose `.tox` **Embody authors** (tracked in
`externalizations.tsv`) is never touched: it reports as `locked`, because
there the file is generated FROM the live COMP. That is the second line of
defence — the first is that a package with no install record is never a
candidate at all, which is what keeps this dev checkout out of update
passes entirely.
