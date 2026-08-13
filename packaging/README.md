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

## What is derived vs curated

**Derived live** — package list, version/build, surfaces, dependencies,
optional integrations, op counts, help URLs, artifact hashes. Re-running the
generator picks up reality.

**Curated in `catalog.json`** — `category` and `description` only: the two
things the project genuinely cannot tell us. Descriptions were seeded by
inspection and **need owner review**.

## The dependency model

Tools depend only on **core**, never on each other, so the configurator needs
no solver. That is enforceable rather than merely asserted: registry masters
live in core and tools ship stamped *hosts*, so a package's `requires` is
exactly the core packages owning the registries it hosts. Every tool requires
`FNS_Config` (settings persistence); a tool with a toolbar button also
requires `FNS_Toolbar`, and so on.

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

## The installer COMP

`packaging/dist/FNS_Installer.tox` (~4 KB) is the droppable rail: put it in
a project that has nothing else installed, point **Selection** at a
`selection.json` from the configurator, pulse **Plan** to see what would
happen, then **Install**.

It is a BUILD ARTIFACT, not a hand-made component — it embeds a snapshot of
`InstallerExt.py`, so editing that file means rebuilding:

```python
exec(open('packaging/build_installer.py').read()); result = BuildInstaller()
```

`InstallerExt.py` is the single implementation; `install.py` is a thin
script wrapper over the same code, so the droppable rail and the headless
rail cannot drift apart.

## End to end

1. Open `configurator/configurator-standalone.html`, pick tools, download
   `selection.json`.
2. Drop `dist/FNS_Installer.tox` into the target project.
3. Point **Selection** at the downloaded file, pulse **Plan**, then **Install**.

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
aws s3 sync packaging/publish/ s3://<bucket>/fnstools/ --delete
```

```
<release>/manifest.json      immutable snapshot
<release>/<Package>.tox      immutable artifacts
<release>/FNS_Installer.tox  so a bare project can bootstrap
manifest.json                ROLLING pointer to the newest release
```

Releases are **pinned**: artifact URLs carry their release, so a manifest
always resolves to the bytes it was built from. The rolling root copy only
answers "what is current?" once. Never publish a mutable
`latest/<Package>.tox`.

## Versioning

**Hashes drive updates, not version numbers.** Each artifact's `sha256`
answers "has this changed since the bytes I installed?" exactly, with zero
maintenance. The `release` label (from the toolkit's `Gittag`) is for
humans and changelogs. Per-package semver is optional.
