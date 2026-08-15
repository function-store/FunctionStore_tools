# Packaging

Machinery for shipping the toolkit as **pickable packages** instead of one
monolith — step 2 of `docs/ConfiguratorDistribution.md` §4. The dependency
audit that gates all of this is §1.1 of that document.

```
catalog.json        curated: category + description (the only hand-written data)
build_manifest.py   runs inside TD; derives everything else, writes manifest.json
manifest.json       generated catalog the configurator and UPDATER both read
configurator/       static picker over manifest.json -> selection.json
dist/               exported .tox artifacts (gitignored; rebuild on demand)
```

## Regenerating the manifest

From a session with TD running:

```python
exec(open('packaging/build_manifest.py').read()); result = Build()
```

Add artifacts (slower — each package is staged and exported through its own
`pre_release` hook):

```python
result = Build(export=True)                     # everything
result = Build(export=['AutoRes', 'ColorUI'])   # named subset
```

Artifact hashes for packages you did not re-export are carried over from the
previous `manifest.json`, so partial rebuilds do not lose data.

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
tool requires `ConfigRegistry` (settings persistence); a tool with a toolbar
button also requires `ToolbarRegistry`, and so on. The FNS_* surface shells
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

`packaging/dist/FunctionStore_tools_2025.tox` (~150 KB) is the **one-drop
bootstrap**: the (empty) toolkit root itself, carrying the installer COMP,
a copy of the UPDATER package, and the vendored palette webBrowser
(`packaging/webBrowser.tox`). The container you drop IS the install
target, so a bare project goes from nothing to installed without leaving
TD. Its UPDATER copy needs no special adoption: updates compare
`Pkgversion` read live off the component, so the first update pass treats
it like any installed package (self-update path included). Deliberately a
plain container — the dev root's Active/UI parameter surface belongs to a
populated toolkit, not to the shell the installer fills.

**The configurator is served, not downloaded.** The installer carries the
picker page (embedded at build time) and a Web Server DAT, dormant until
the **Pick Tools** pulse: it serves `http://127.0.0.1:<Port>/` and opens
it in the sibling webBrowser panel (system browser as fallback). The page
gets its catalog from `/manifest.js` — the store's manifest, and when the
store is empty the server kicks the sibling UPDATER's **Refresh Store**
while the page shows "downloading" and polls. The selection comes back as
a POST: plan shown in the page, **Install** run from it. No file leaves
the browser; the same page still works as a plain double-clicked HTML
(static mode = download `selection.json`).

`packaging/dist/FNS_Installer.tox` (~14 KB) is the bare installer, for a
project that already has a toolkit container. Same served picker, minus
the webBrowser panel — Pick Tools opens the system browser.

Both are BUILD ARTIFACTS, not hand-made components — they embed snapshots
of `InstallerExt.py` and `configurator/index.html`, so editing either
means rebuilding. The bootstrap also embeds `dist/UPDATER.tox`, so
re-export UPDATER first when it changed (`Build(export=['UPDATER'])`):

```python
exec(open('packaging/build_installer.py').read())
result = BuildInstaller()
result = BuildBootstrap()
```

`InstallerExt.py` is the single implementation; `install.py` is a thin
script wrapper over the same code, so the droppable rails and the headless
rail cannot drift apart.

## End to end

1. Drop `dist/FunctionStore_tools_2025.tox` (from the bucket) into the
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

**Install tests must target a cooking-disabled container.** A live copy of a
registry master will otherwise try to promote itself to the `/sys` global and
destroy the running one:

```python
t = op('/sys/quiet').create(baseCOMP, 'trial'); t.allowCooking = False
Install('packaging/example-selection.json', target=t.path)
```

## Publishing a release

Distribution is **buckets and manifests only** — native `.exe`/`.dmg`
installers are the bootstrap, and there is no GitHub-based update flow.
The bucket is the single source of truth for what exists and what the
bytes are; `base_url` in the manifest says where to fetch.

```python
exec(open('packaging/build_manifest.py').read()); Build(export=True)
exec(open('packaging/publish.py').read()); result = Stage()
```

`Stage()` lays out `packaging/publish/` to mirror the bucket exactly, then
**re-hashes every staged file against the manifest** and refuses to report
`ok` on any mismatch — publishing bytes that disagree with the hashes an
installer verifies is worse than not publishing. Upload is one sync:

```bash
python3 packaging/upload.py
```

```
<release>/manifest.json      immutable snapshot
<release>/<Package>.tox      immutable artifacts
<release>/FNS_Installer.tox               bare installer (root already exists)
<release>/FunctionStore_tools_2025.tox    one-drop bootstrap root
manifest.json                ROLLING pointer to the newest release
```

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

The UPDATER package consumes what this directory publishes. Two motions,
deliberately separate (design record: `ConfiguratorDistribution.md` §4.2):

- **Refresh Store** — fetch `<Base URL>/manifest.json` and every artifact
  whose bytes differ into `<user palette>/FNStools_ext/store/`.
  Machine-wide; touches no project.
- **Check for Updates** / **Update This Project** — compare the open
  project's `installed` table (package → the sha256 it was installed from)
  against the store, and replace only what differs. Per project, explicit.

`installed` is written by both rails — `InstallerExt.RecordInstalled` on
install and the updater on every replacement — so the two must keep the
same four columns. It lives in the project because it is project state.

**Point `Base URL` at a local directory to test without a bucket.** The
staged `publish/` tree is laid out exactly like the bucket, so
`Base URL = <repo>/packaging/publish` (or a `file://` URL, or a localhost
static server over that folder) exercises the real code path:

```bash
python -m http.server 8899 --bind 127.0.0.1 --directory packaging/publish
```

Artifacts are fetched *relative to the configured Base URL*, not to the
manifest's own `base_url` — identical against the real bucket, and the only
reason a mirror or a local tree can serve the whole flow.

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
