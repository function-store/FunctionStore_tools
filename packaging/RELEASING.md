# Releasing — the runbook

How to ship. What the pieces *are* (rails, bootstrap, store, versioning,
binding modes) lives in [README.md](README.md); design rationale in
[`docs/ConfiguratorDistribution.md`](../docs/ConfiguratorDistribution.md).
Making a NEW package — what one consists of, what it must carry —
is [CREATING.md](CREATING.md).

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

   `Release()` runs Preflight first and REFUSES on a blocker (`force=True`
   overrides); `ReleaseMany()`/`ReleaseOne()` and the PI and CMS buttons that
   call them do not run it, and the wizard's step 2 shows it without
   refusing (corrected 2026-09-08: this line used to say both refuse). `bump='auto'` patch-bumps a package
   whose live `Pkgversion` still equals the published one and leaves a
   hand-set version alone; it clamps against the *published* manifest, so
   a `Pkgversion` reverted by a tox reload can never ship as a downgrade.
   Upload runs detached into `packaging/publish/.upload.log`.

5. **Commit** the re-exported toxes, `manifest.json` and `CHANGELOG.md`.
   The publish PI-saves the packages whose version it bumped (`pi_saved`
   in the result; `pi_unsaved` when PI is missing or a save fails), so
   the version bump reaches the tracked suspect toxes without a manual
   pass. Work you edited yourself still lands in step 1, and the project
   (`.toe`) save stays yours.

Two PI buttons sound alike and are not. **Publish** (☁) is the rail
above: bump → build → stage → upload. **Release** is PI's own apparatus —
it runs the component's `pre_release` hook and writes a tox into
`modules/release/`, touching neither `Pkgversion` nor manifest nor bucket.

The publish UI is stamped into PI by
[`scripts/pi_publish_ui.py`](../scripts/pi_publish_ui.py), not authored
inside it. PI reloads from its own `.tox` on every project open, so
anything typed into it live is temporary; if the ☁ column or the wizard
button ever disappears, re-run that script and save PI.

## Foreign packages ride the same release

A foreign package (catalog `source` block — `CREATING.md`, "The other
answer") has no live COMP: nothing to land, bump or export. Its one extra
step is the mirror:

```bash
python packaging/foreign_sync.py
```

(or the row's **Sync** button in the CMS release table, which runs it
detached and tails `packaging/.foreign_sync.log`). It fetches each
upstream manifest, downloads and sha-verifies the tox into
`packaging/dist/`, and pins `packaging/foreign.lock.json`. Preflight
blocks with `foreign package(s) not mirrored` until the lock and the dist
bytes agree; then Release & stage ships it like any package, at the lock's
version, and step 5's commit must include the lock. Nothing in the rail
polls the upstream on its own — a foreign package only moves when someone
syncs it, which is the point: the lock in git says exactly which upstream
build each release mirrored.

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

**Rebuild them only when one of those four actually changed.** A rails
rebuild is not byte-reproducible: rebuilding with no source change at all
produces different bytes every time (measured across v3.2.44 and v3.2.45).
So a reflexive rebuild each release leaves you choosing between shipping
different bytes under one rail version and bumping the version for churn,
and both are wrong. Preflight calls the rails stale whenever the ROOT
suspect is newer than the artifact, which a PI save makes true every
release, so treat that particular staleness as a question rather than an
instruction. When nothing in their sources moved, copy the previous
release's rails back into `dist/` from `packaging/publish/<label>/` and ship
them unchanged.

Order matters when the updater is in the release: `BuildBootstrap()` embeds
`dist/FNS_Updater.tox`, so it has to run AFTER the bump and export, or the
bootstrap ships the previous updater. Build the installer first, release,
then rebuild the bootstrap and stage again. The label is unpublished at that
point, so the second `Stage()` is free.

The bootstrap embeds the `FNS_Updater` artifact from `dist/`, so
`Build(export=['FNS_Updater'])` first when the updater itself changed. A
stale embedded copy is self-healing (its live `Pkgversion` is what the
updater compares, so the first update pass replaces it), but there is no
reason to ship one knowingly.

## One artifact, two lives

There is deliberately **no standalone release profile**. Every artifact
ships with console exposure off (`pre_release_common.py` scrubs it on any
`FNS_Console` host), and the toolkit's install rail flips it on as the
package lands (`InstallerExt.ExposeConsoleHosts`). The same `.tox` is the
standalone plugin download (local mode, no console raised) and the
toolkit package (exposed). Do not hand-edit an artifact for either case;
`docs/FNS_Console.md` has the rule and the reasoning.

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

**Signing happens inside `Stage()`** and needs no extra step: the
manifest and the discovery document (every staged copy) get sidecar
`.sig` files from the Ed25519 key at
`%USERPROFILE%/.fnstools-release/signing.key`. A machine without that
key **cannot stage a release** (`FNS_ALLOW_UNSIGNED=1` is the
offline-test hatch, never the release path). First-time setup and the
full contract — key custody, what clients verify, the transition flag —
live in [docs/ReleaseSigning.md](../docs/ReleaseSigning.md).

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

**Accumulate the notes as the work lands, not at release time.** The
commit that changes what a shipped package does appends that package's
line to `release_notes.md` in the same commit; a later commit to the same
package edits the line rather than adding a second one. Between two
publishes the file is the running answer to "what has changed since the
last release", which is what the first v3.1.0 notes cost a session to
reconstruct from 186 commits. Commits that ship no behaviour change (a
PI re-save, a doc, a test harness) write nothing. The pre-commit hook in
`scripts/hooks/` warns when a commit touches a package's files and the
file carries no line for it (`git config core.hooksPath scripts/hooks`
installs the hooks; the warning never blocks).

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

---

## Two things that look like breakage and are not

Both cost real time on the v3.0.13 release. Both are fixed; this is so
the *symptoms* are recognisable if they resurface.

### "not landed, own code newer than the .tox" on packages you just saved

Preflight reported 18 packages as unlanded immediately after a clean
save. One PI save writes the suspect `.tox` **and** re-exports the
externalized `.py` files beside it, microseconds apart and in no
guaranteed order — measured **0.5 ms** apart here, with the `.py`
identical to git HEAD. A strict "source newer than tox" comparison reads
that ordering as unlanded work, producing a blocker nobody can clear by
saving again (each save recreates it).

`_unlandedPackages` now allows `_SAVE_SLACK_S = 2.0` seconds. A genuine
unlanded edit is seconds-to-minutes newer, never sub-second.

**If you see it anyway**, check whether the source really differs:

```bash
git status --short modules/suspects/FNSTools/<Name>/
```

Empty output plus a sub-second mtime gap means it is this. A real hit
looks different — on v3.0.13 exactly one package survived the slack
(`CustomParTools`, which owns the `FNSCommand` master edited that day),
and that one genuinely needed the save.

### "uploaded but could not be read back for verification" on gated artifacts

Every `plus/` artifact failed upload verification while the bytes were
perfectly correct in the bucket. Gated objects cannot be read back over
the public rail — that is the privacy working — so `upload.py` verifies
them through an authenticated `wrangler r2 object get`. That read-back
wrote to a **fixed** temp filename while uploads run concurrently across
`WORKERS` processes, so every gated object in a release raced one path:
one deleted it in its `finally` while another was still hashing.

The temp file is now unique per key. **Never trust that message from an
older uploader without checking serially:**

```bash
npx wrangler r2 object get "fnstools/fnstools/plus/<release>/<Name>.tox" --file /tmp/rb.tox --remote
sha256sum /tmp/rb.tox   # compare against packaging/publish/plus/<release>/<Name>.tox
```

A re-upload cannot fix a read path, so the uploader deliberately refuses
to retry — the failure is loud precisely so nobody ships on an unverified
claim.

### And one that IS breakage: restaging a label without `--force`

Objects under `v<release>/` are **release-pinned and immutable**: the
uploader decides by a public HEAD that an existing key is already done and
skips it (`upload.py`, "Immutable (release-pinned) objects already in the
bucket are skipped"). Only `latest/` and the manifest are rewritten.

So a restage of an already-published label lands HALF: the manifest ships
new digests, the versioned path keeps the old bytes, and every install
fails its digest check with `download rejected`. It is the worst shape of
breakage, because staging, upload and the privacy probe all report success
and the `latest/` alias serves the correct bytes, so a spot check on
`latest/` passes while users cannot install.

Restaging a published label therefore needs:

```bash
python packaging/upload.py --force          # overwrite the pinned objects
python packaging/verify_release.py v3.2.0   # then PROVE both paths agree
```

The verifier is the point. It fetches every free artifact from BOTH the
versioned path and the `latest/` alias and compares each against the staged
bytes; gated ones need the authenticated read in the section above. Run it
after any restage, and after any upload that reported a skip.

Note the release pipeline tries to stop you first: `bump='auto'` patch-bumps
a package whose live version equals the published one, precisely so a
republish becomes a NEW version instead of a mutation of a shipped one.
Reaching for `bump=False` to hold a label steady is the moment to remember
this section. Shipping the fix as the next version is the boring, safe path;
restage only when the release is minutes old and you accept that already
installed copies will never pull it, since `Pkgversion` governs updates.

### And one that IS breakage: skipping `wrangler deploy`

`gate_package.py` writes the tier map into `worker/wrangler.toml`, but
`TIERS` is an environment variable **baked into the deployed worker**.
Until you deploy, the live gate runs the previous map, so a paying
supporter requesting a newly-gated package gets **403 not_entitled** on
bytes they own — while the picker advertises it happily. Gating a package
is not finished until:

```bash
cd worker && npx wrangler deploy
```

### A refused release retried is a double bump

Cost v3.2.1 three attempts (2026-09-11). `ReleaseMany()` bumps and
regenerates the manifest, then stages, then uploads; when `Stage()` or
`StartUpload()` refuses, everything before it has already happened. The
retry then reads `packaging/publish/` (the tree the refused attempt laid
out) as a published source, sees every package "already published" at
the version it was about to ship, and patch-bumps again: 3.2.1 became
3.2.2, then 3.2.3, under a label that still said v3.2.1.

Before retrying a release that refused **after** the bump: restore
`manifest.json`, `CHANGELOG.md`, `release_notes.md`, `release.json` and
`shipped_builds.json` from git, delete `packaging/publish/`, put the live
`Pkgversion` values back (on the `FNS_About` child, and re-save), and
retry with `bump=None` and an explicit `label=`.

### The upload cannot start from a TouchDesigner that Envoy launched

`StartUpload()` probes for a shell python with `subprocess.run`; in a TD
instance started through Envoy's `launch_td` every process creation
fails with `OSError(22, 'The request is not supported')`, so the release
reports "no working python for the upload subprocess" although the
python it names runs fine. `Build()` and `Stage()` are unaffected (no
subprocess). Release with `upload=False` and run the sync from a shell:

```bash
PYTHONIOENCODING=utf-8 python packaging/upload.py
python packaging/verify_release.py v3.2.1
```

Two smaller things from the same day: `Stage()` needs `sign_release`
importable, so a Textport release that `exec()`s `release_one.py` should
put `packaging/` on `sys.path` first (the wizard does), and a scripted
`Pkgversion` write must land on the `FNS_About` child, never the
component's own parameter, or Preflight reports the mirror severed.

## Tier variants: one package, one build per tier

`docs/TierVariants.md` (decided 2026-09-15, built 2026-09-17). A tool
with a Base and a Pro form is ONE package: one catalog entry, one docs
page, one picker row, one installed name, one version line, and one
artifact per tier above the entry tier.

- Declare it in `catalog.json`: `"variants": {"pro": {"access": "<tier id>",
  "summary": "adds ...", "source": "FNS_FooPro"?, "withhold": ["ExtFooPro.py"]?}}`.
  `source` names a second live master; without it the package's own
  master exports under the variant's file name (`FNS_Foo.pro.tox`) and its
  `pre_release` hook builds that edition off the save path. `withhold`
  names source files only that build may publish (a free Base with a paid
  variant in one master).
- Gate it: `python packaging/gate_package.py FNS_Foo --tier <base id>` as
  before, then `--variant pro --tier <pro id>`; the Worker product is
  `FNS_Foo.pro`, granted from that tier up; `wrangler deploy` follows.
- Each master's `FNS_About` carries `Pkgvariant` (`base` / `pro`); a
  single master's hook sets it per edition. **`Pkgversion` and
  `Pkgvariant` govern updates**, both read live off the installed copy:
  a newer version of the installed build updates it, an account that
  grew swaps upward at the shipping version, and an installed build the
  account no longer holds is held as it is (never offered anything).
- The release exports every variant (`dist/FNS_Foo.pro.tox`), stages
  each under `plus/<release>/`, and `Stage()` refuses a variant that is
  not authorizable. Preflight refuses a missing source master, one
  nested in another master, or masters disagreeing on `Pkgversion`.
- Walk every variant package with a Base test account AND a Pro test
  account before release: the creator account holds every tier and
  proves nothing about the gate.

