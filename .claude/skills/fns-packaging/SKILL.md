---
name: fns-packaging
description: "MUST READ before releasing, versioning, or changing how an FNS tool ships -- manifests, buckets, Pkgversion, the installer, the updater, or exporting a portable tox. Routes to the runbook and carries the invariants a release must not break."
---

# Shipping an FNS package

**The step-by-step runbook is [packaging/RELEASING.md](../../../packaging/RELEASING.md)**
— Guided Release, preflight, the manual motion, rebuilding the rails,
regenerating the manifest, staging/uploading, release notes, and testing an
install without the bucket. Follow it; do not improvise a release.

**Creating a NEW package is [packaging/CREATING.md](../../../packaging/CREATING.md)**
— the identity test (depth-1 suspect-tracked COMP with its own tox), the three
author-maintained pieces (`Pkgversion`, catalog entry, user-facing doc), what is
derived and must not be declared, and the FNS_About-vs-bare-Pkgversion shapes
(bare par is the supported minimum; the child adds `Touchbuild` + `Helpurl`).

The distribution *model* — why buckets and manifests, what the layers are, what
was superseded — is in
[docs/ConfiguratorDistribution.md](../../../docs/ConfiguratorDistribution.md).
`docs/UvPackagingResearch.md` describes a pip/uv rail that is **explicitly not
the plan**; do not build toward it.

## Invariants a release must not break

- **`Pkgversion` governs updates; hashes only verify.** The update decision is
  made on the version parameter we govern, read live off the installed
  component. Artifact hashes confirm a download arrived intact — they are not
  the version signal. Never invert these roles.
- **Native installers are deferred** ([docs/NativeInstallerDecision.md](../../../docs/NativeInstallerDecision.md)).
  The one-drop `FNSTools.tox` bootstrapper is the official install rail. Do not
  promise `.exe`/`.dmg` in docs, README, or the website.
- **`externaltox` marks a dev master.** A copy of a suspect-bound master
  inherits its `externaltox` binding, and boot then reloads the *wrong* tox into
  it. Every stamp recipe must sever it: `enableexternaltox=False`,
  `externaltox=''`, strip `pi_suspect`.
- **Tools with `enableexternaltox=False` are carried by the ROOT toolkit tox**,
  not their own. Their own `.tox` saves are dead files at boot. Landing
  discipline: save the ROOT tox too, never only the per-tool suspects.
- **Save order is leaves first, `/FNSTools` root last** (PI `Save()` per owner).
  PreviewPanel25 and private_investigator1 persist via their OWN `externaltox`
  pars, not PI's table.
- **PI's Dirty column under-reports.** After clone-driven child changes, build
  the save list from every suspect that OWNS an affected instance — not from
  Dirty.
- **The user-facing doc is part of the package.** `website/tools/build-site.mjs`
  hard-fails if a `packaging/docs/<Package>.md` has no `catalog.json` entry, if
  its frontmatter `package` does not match the filename, or if a catalogued
  package has no doc. A new package ships with its doc or the site build breaks.
- **The updater's config handoff is gated under project scope** — see
  `/fns-config-scope`. Replacement logic that assumes the roaming JSON exists
  will lose user state in every project-scoped install.

## Before you claim a release is done

Run the site build (`npm run pages` in `website/`) if anything under
`packaging/docs/` or `catalog.json` changed, and cold-test the artifact: drop the
tox in a bare project and verify the full bootstrap, not just that the file exists.
