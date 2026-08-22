# Releasing — the runbook

How to ship. What the pieces *are* (rails, bootstrap, store, versioning,
binding modes) lives in [README.md](README.md); design rationale in
[`docs/ConfiguratorDistribution.md`](../docs/ConfiguratorDistribution.md).

## The button: Guided Release

PI → **Publish** page → **Guided Release...** — the whole release, one
dialog at a time. This is the recommended path: the steps that get
skipped by hand are precisely the ones with no error to announce them (a
package never landed still publishes, it just publishes yesterday's bytes
under a fresh version).

1. **Scope** — what are you shipping? `[Selected]` the rows picked in
   PI's lister, `[Bumped]` every package whose live `Pkgversion` is
   already ahead of the bucket, `[All]` everything, auto patch-bumped.
2. **Preflight** — blockers and warnings (see below). When the rails are
   stale, a **[Rebuild]** button appears right here and rebuilds the
   installer + bootstrap inline — no Textport. Landing is the one thing
   it cannot do for you: Save the dirty rows in the lister, save the
   project, start the wizard again.
3. **Notes** — refuses to ship unnoted packages silently; write the
   prose into `release_notes.md` (format below), save, resume.
4. **Confirm** — packages, version transitions, release label, first
   line of the notes. Publishing runs bump → build → stage → upload,
   the same rails the ☁ buttons drive.

Nothing publishes before step 4's confirm, so **Stop after step 2** is
also the no-Textport way to just rebuild stale rails.

## Preflight

The wizard runs it for you; from the Textport it changes nothing:

```python
exec(open('packaging/release_one.py').read())
Preflight()                # everything -- the "what am I forgetting" view
Preflight(['AutoRes'])     # a selection
```

It checks what the publish rails cannot refuse: a package edited live but
never landed to its `.tox` (an externalized package reloads from its
file, so that work is not unsaved, it is *gone*), a rail artifact older
than the sources it is built from (`Stage()` hashes rails into the
manifest regardless, so a stale one publishes bytes nobody built),
packages shipping with no release notes, and a dirty repo (step 4 below
is committing what publishing writes).

A note it raises but does not enforce: **registry ripple**. Every package
vendors a copy of the registry hosts it uses, so one propagation pass
makes them all look newer than their toxes. Whether that needs a re-save
depends on whether the tox embeds those bytes or externalizes to them, so
it is a warning, not a blocker.

## The manual motion

The same steps the wizard walks, by hand:

1. **Land what you changed.** Each touched package writes back to its own
   `.tox`. Private Investigator's lister is the surface: dirty rows are
   marked, its **Save** button lands that package. Then save the project.
2. **Write the notes** in `release_notes.md` (format below).
3. **Rebuild the rails if they are stale** (see below) — *before*
   publishing, because `Stage()` hashes them into the manifest as it goes.
4. **Publish** — the ☁ in a package's row in PI's lister; or select rows
   and **Publish Selected to Bucket** on PI's `Publish` page to ship them
   as one drop; or the ☁ on the toolkit **root** for everything already
   ahead of the bucket. Every path shows packages, version transitions,
   label and notes before anything happens. Textport equivalent:

   ```python
   exec(open('packaging/release_one.py').read())
   result = ReleaseMany(['AutoRes', 'QuickPane'])   # bump, build, stage, upload
   result = ReleaseOne('AutoRes')                   # one package
   result = ReleaseMany([...], label='v3.1.0')      # name the drop yourself
   result = ReleaseOne('AutoRes', upload=False)     # stage only, batch the sync
   ```

   `Release()`/`ReleaseMany()` run Preflight first and REFUSE on a
   blocker; `force=True` overrides. `bump='auto'` patch-bumps a package
   whose live `Pkgversion` still equals the published one and leaves a
   hand-set version alone; it clamps against the *published* manifest, so
   a `Pkgversion` reverted by a tox reload can never ship as a downgrade.
   Upload runs detached into `packaging/publish/.upload.log`.

5. **Commit** the re-exported toxes, `manifest.json` and `CHANGELOG.md`.

Two PI buttons sound alike and are not. **Publish** (☁) is the rail
above: bump → build → stage → upload. **Release** is PI's own apparatus —
it runs the component's `pre_release` hook and writes a tox into
`modules/release/`, touching neither `Pkgversion` nor manifest nor bucket.

The publish UI is stamped into PI by
[`scripts/pi_publish_ui.py`](../scripts/pi_publish_ui.py), not authored
inside it. PI reloads from its own `.tox` on every project open, so
anything typed into it live is temporary; if the ☁ column or the wizard
button ever disappears, re-run that script and save PI.

## Rebuilding the rails

The rails go stale when `InstallerExt.py`, `build_installer.py`,
`configurator/index.html`, or the root suspect changed — they embed
snapshots of those at build time. Preflight flags it; the wizard's step-2
**[Rebuild]** fixes it in place. By hand, in the dev project:

```python
exec(open('packaging/build_installer.py').read())
result = BuildInstaller()     # -> packaging/dist/FNS_Installer.tox
result = BuildBootstrap()     # -> packaging/dist/FNSTools.tox
```

The rails are residents of the dev root (`FNSTools/FNS_Installer` +
`FNSTools/webBrowser`), and the bootstrap is the dev root castrated with
those two kept. After editing `InstallerExt.py` or
`configurator/index.html`, refresh the live copies first so the dev
project runs what ships:

```python
exec(open('packaging/build_installer.py').read())
result = EnsureDevRails()     # builds missing rails, re-embeds sources in place
```

`BuildBootstrap()` performs the same refresh on its staged copy regardless,
so a forgotten `EnsureDevRails()` only ever leaves the DEV installer stale,
never a shipped one.

The bootstrap embeds the `FNS_Updater` artifact from `dist/`, so
`Build(export=['FNS_Updater'])` first when the updater itself changed. A
stale embedded copy is self-healing (its live `Pkgversion` is what the
updater compares, so the first update pass replaces it), but there is no
reason to ship one knowingly.

## Regenerating the manifest

```python
exec(open('packaging/build_manifest.py').read()); result = Build()
```

Add artifacts (slower — each package is staged and exported through its
own `pre_release` hook):

```python
result = Build(export=True)                     # everything
result = Build(export=['AutoRes', 'ColorUI'])   # named subset
```

Artifact hashes for packages you did not re-export are carried over from
the previous `manifest.json`, so partial rebuilds do not lose data.
(`ReleaseOne`/`ReleaseMany` and the wizard drive this for you.)

## Staging and uploading by hand

```python
exec(open('packaging/build_manifest.py').read()); Build(export=True)
exec(open('packaging/publish.py').read()); result = Stage()
```

`Stage()` lays out `packaging/publish/` to mirror the bucket exactly,
then **re-hashes every staged file against the manifest** and refuses to
report `ok` on any mismatch. Upload is one sync:

```bash
python3 packaging/upload.py
```

`publish.py` refuses to stage a new release that bumps nothing, which
catches the forgotten-`Pkgversion` case.

## Release notes

Write the prose **before** releasing, in `release_notes.md`. A line that
starts with a package name and a colon rides that package's changelog
bullet *and* ships as its `whatsnew` in the manifest — what the updater
shows next to an available update:

```
AutoRes: Follows the project resolution again when the reference moves.
```

Everything else is release-level prose. Attribution is by exact package
name, so a typo silently demotes a line to general prose. Do not write
version numbers or the release label; those are stamped at publish time.
The file is cleared on a successful publish, its text moving to
`CHANGELOG.md` and the release's own manifest.

## Testing an install without the bucket

Point the updater's `Base URL` at a local directory — the staged
`publish/` tree is laid out exactly like the bucket:

```bash
python -m http.server 8899 --bind 127.0.0.1 --directory packaging/publish
```

Artifacts are fetched relative to the configured Base URL, not the
manifest's own `base_url`, which is the only reason a mirror or a local
tree can serve the whole flow.

**Install tests must target a cooking-disabled container.** A live copy
of a registry master will otherwise try to promote itself to the `/sys`
global and destroy the running one:

```python
t = op('/sys/quiet').create(baseCOMP, 'trial'); t.allowCooking = False
Install('packaging/example-selection.json', target=t.path)
```

Remember the palette store when a test install shows stale content: the
installer plans downloads against the store's manifest and re-fetches any
store file whose sha256 disagrees with it (the store is a mirror — see
README, "Updating an install"), but a test that bypasses the picker flow
can still load whatever file a path points at.
