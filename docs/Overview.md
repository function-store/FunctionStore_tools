---
status: in-force
summary: One-page map of the schemes in force — what a package is, how it ships, how it updates, where settings live. Orientation only; every detail is owned by the linked document.
since: 2026-08-26
---

# The schemes in force — one page

**This is a map, not a contract.** Every section is a few lines and a link.
When this page disagrees with the document it links to, **that document
wins** — those are the ones kept current, and they own every number,
parameter name and edge case. Nothing here should exist that is not already
true somewhere else.

Read this to get oriented. Read the linked doc before changing anything.

---

## 1. What a package is

A package is a **depth-1 COMP** that is a tracked `pi_suspect` and has its
own `.tox`. Two kinds: **core** (installed as a unit — the registries and
the machinery around them) and **tool** (optional, pick what you want).

**Dependencies are derived, never declared.** Registry masters live in core
and tools ship stamped *hosts*, so a package's `requires` is exactly the
core packages owning the registries it hosts. Nothing hand-maintains it, so
it cannot drift.

The registry architecture is what makes partial installs possible at all —
a registry discovers contributions, and a missing tool is just missing
entries. Everything on this page is downstream of that.

→ [PackagingScheme.md](PackagingScheme.md) · [RegistryScheme.md](RegistryScheme.md) · `/fns-registry`

## 2. Four questions, four answers

Keeping these apart is the whole design:

| Question | Answered by |
|---|---|
| What packages exist, and what do they need? | `manifest.json`, derived from the live project |
| Is a newer build available? | **`Pkgversion`** — a custom par we govern, on every package |
| Where do I fetch it? | the manifest's pinned per-release `url` |
| Did the download arrive intact? | **`sha256`** — integrity, and nothing else |

`Pkgversion` is read **live off the installed component**, so no side table
can drift out of truth — the component *is* the truth. It is also the one
hand-maintained field in the system: bump it whenever you change a package.

→ [PackagingScheme.md](PackagingScheme.md) §1

## 3. How it ships

**Buckets and manifests**, on R2. The bucket is the single source of truth
for what exists; `base_url` says where to fetch. There is no GitHub-based
update flow.

Each release is pinned and immutable; a rolling `manifest.json` at the root
is the one mutable pointer, and ships `no-cache` so a CDN cannot silently
freeze everyone on an old release. Two rails ride along per release: the
one-drop **`FNSTools.tox`** bootstrap (the official install path) and the
bare **`FNS_Installer.tox`**.

→ [ConfiguratorDistribution.md](ConfiguratorDistribution.md) · [NativeInstallerDecision.md](NativeInstallerDecision.md)
· runbook: [packaging/RELEASING.md](../packaging/RELEASING.md) · `/fns-packaging`

## 4. How it installs

Picker → **machine-wide store** → installer. The store is a mirror of the
bucket; the installer only ever installs from it and never fetches.

Where a package's files end up is chosen at install time, and the updater
tracks no mode — it follows whatever binding each package actually has:

| Mode | Files live | Update path |
|---|---|---|
| `embedded` (default) | inside the `.toe` | replace from the store artifact |
| `shared` | bound to the palette store | rewrite + reload; machine-wide by design |
| `project` | `<project>/FNStools/` | rewrite + reload; isolated per project |

→ [ConfiguratorDistribution.md](ConfiguratorDistribution.md) · [LastInstallRecord.md](LastInstallRecord.md)

## 5. How it updates

Three motions, deliberately different costs:

| Motion | Cost | Does |
|---|---|---|
| **Refresh Store** | whole store | fetch manifest + every artifact whose bytes differ. Machine-wide; touches no project |
| **Check for Updates** | one small JSON | fetch the manifest only, then compare |
| **Update This Project** | only what differs | fetch just what this project needs, then apply |

`Compare()` is the single decision point. **An update pass is not an install
pass** — a package the user never chose stays uninstalled. Applying runs
**one package per frame**: each replacement reinitialises extensions, so
batching them is both a long main-thread block and the crash-prone case.

**The reload semantics are the load-bearing part.** With `reloadcustom` OFF
and `reloadbuiltin` ON, TouchDesigner natively preserves custom parameters
(user settings), re-takes built-in parameters (build-owned wiring), rebuilds
children, and keeps the external-tox binding. New pars arrive and retired
pars leave on their own. This is why the updater does not need a parameter
inventory, and it is measured, not assumed.

→ [UpdaterHardening.md](UpdaterHardening.md) — start here · [PackagingScheme.md](PackagingScheme.md) §2

## 6. Where settings live

**Two stores.**

The **`.toe` is the local store, and it is the default.** Custom pars, the
configurators' state tables, `StorageManager` contents — they live in the
project file and survive every save with no registry involved. Local
identity between saves is not a feature you switch on; it is what happens
when nothing overwrites it.

The **JSON is a machine-global overlay**, one aggregated file in the user
palette, applied **once per session** shortly after each tool registers. So
the only moment local state is at risk is that one deferred apply at boot.

**`Configscope` on `/FNSTools` decides whether the overlay exists at all** —
`global` (default) roams; `project` never reads and never writes the file,
and the `.toe` carries everything. There is no per-tool scope.

Each tool has two rails in the file: **`pars`** (its custom parameters,
filtered conservatively — a par missing from the live tool is never created)
and **`state`** (whatever it returns from `onConfigSave()`, unfiltered).

**Two of the four per-tool hatches do not mean what they sound like.**
`Autoload` off is *publish but never adopt* — the tool ignores the shared
file while still overwriting it for everyone else. `Excludepars` is
snapshot-side only, so previously written values keep being applied. The
hatch that actually stops a sync is **`Persistpars` off**.

→ [ScopeAndPersistence.md](ScopeAndPersistence.md) — the model · [ConfigScope.md](ConfigScope.md) — the switch · `/fns-config-scope`

## 7. What is not proven yet

Kept here so it is not rediscovered as a surprise:

- **Self-update has never been run end-to-end.** UPDATER updating its own
  package destroys the DAT running the loop, so it is ordered last and run
  detached. Structurally correct, failure bounded, unproven.
  → [UpdaterSelfUpdateVerification.md](UpdaterSelfUpdateVerification.md)
- **A real multi-package update pass has not been run** against a real
  bucket. → [UpdaterHardening.md](UpdaterHardening.md)
- **An in-place update rebuilds a tool's children**, so internal readers can
  come back blank. Fix is planned, not landed.
  → [ProjectStateAcrossUpdates.md](ProjectStateAcrossUpdates.md)
- **A package can silently vanish from a release** — `publish.py` guards
  against a release that bumps nothing, but not against one that drops
  something. → [RailHardening.md](RailHardening.md) §3.1
- **Nothing verifies what actually landed in the bucket** after upload.
  → [RailHardening.md](RailHardening.md) §3.2
- **One bucket URL, no fallback, no way to reach the field.** A moved or dead
  host strands every install, and there is no kill switch for a bad updater.
  This is the one that cannot be fixed after the fact.
  → [RailHardening.md](RailHardening.md) §2.1–2.2

## 8. Open research — decided by nobody yet

- **Gated delivery** — Patreon auth and Gumroad license keys in front of some
  packages. → [GatedDeliveryResearch.md](GatedDeliveryResearch.md)
- **The updater as a registry** — whether tools should carry their own update
  capability. → [UpdaterRegistryResearch.md](UpdaterRegistryResearch.md)

These two touch the same code and should be read together before either is
built.

The **work plan** that came out of comparing our rail against a shipping one
is [RailHardening.md](RailHardening.md) — six adopted ideas and three closed
holes, none of which depend on gating anything.
→ [DistributionComparison.md](DistributionComparison.md) for the measurement.

## 9. Where the detail lives

| Owns | Document |
|---|---|
| The packaging and update scheme; traps already paid for | [PackagingScheme.md](PackagingScheme.md) |
| Picking and installing a subset; the distribution model | [ConfiguratorDistribution.md](ConfiguratorDistribution.md) |
| Reload semantics, apply-path hardening, the TD-build floor | [UpdaterHardening.md](UpdaterHardening.md) |
| "Set up like last time" across machines | [LastInstallRecord.md](LastInstallRecord.md) |
| Why the bootstrap `.tox` and not a native installer | [NativeInstallerDecision.md](NativeInstallerDecision.md) |
| What roams, what stays, and every hatch | [ScopeAndPersistence.md](ScopeAndPersistence.md) |
| The global-vs-project scope switch | [ConfigScope.md](ConfigScope.md) |
| Registries, stamped hosts, `/sys` homes | [RegistryScheme.md](RegistryScheme.md) |
| The release runbook (how-to) | [packaging/RELEASING.md](../packaging/RELEASING.md) |
| Every doc, by status | [README.md](README.md) |

Skills carry the how-to: `/fns-packaging`, `/fns-registry`, `/fns-config-scope`.
