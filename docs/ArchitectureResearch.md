---
status: landed
summary: Deep research over the toolkit's bootstrapping, versioning and updates, dependency handling, launcher ecosystem and gated releases, measured against the code and the live session on 2026-09-08. Produced the website guide "How FNSTools is built" (a new guides route on the site), corrected twenty stale claims in place, and lists what is still flagged, with the ideas worth explaining and their code anchors.
since: 2026-09-08 (owner ask: explain how the toolkit is built, Launcher included, and put it on the website)
verified: 2026-09-08 (live session FNSTools_PRIV on TD 2025.33070; four code traces; read-only probes of the gate and bucket)
---

# Architecture research: what the guide says, and what was stale

The owner asked for a deep pass over the architecture (bootstrapping, version
and update management, dependency handling including externals, tooling, the
Launcher, gated releases) that ends up as a dedicated section of the website
documentation. This is the record of that pass. The deliverable itself is the
guide; this document says how it was made, what it measured, which documents
disagreed with the code, and what was done about each.

## What shipped

- **The guide.** `website/content/guides/how-fnstools-is-built.md`, served at
  `/docs/guides/how-fnstools-is-built/` (renamed 2026-09-10 so the slug matches
  the title; `/docs/guides/architecture/` is now the one-page overview that
  links to it). Sections: the shape
  in one paragraph; what a package is; registries; derived dependencies;
  bootstrapping (first drop, served picker, the store as a mirror, plan then
  install, the other rails, set up like last time); versioning and updates
  (four questions, versions decide and hashes verify, pinned releases and the
  rolling pointer, discovery and signing, three motions, applying, what a
  reload keeps); where settings live; shared code; the release pipeline and
  foreign packages; the launcher and the ecosystem; gated releases; what is
  deliberately absent or unproven; ideas worth borrowing.
- **A guides route in the site generator** (`website/tools/build-site.mjs`).
  Any `website/content/guides/<slug>.md` with `title` and `summary` renders
  through the package-page markdown pipeline into the docs chrome, is indexed
  by Pagefind with the rest of `/docs/`, and takes part in the internal-link
  check both ways and in the house-style dash note. A `section` key places
  it: `guides` leads the sidebar and the index, `reference` closes both
  beside the common-parameters page. Documented in `website/README.md`.
- **Placement, per the owner's review the same day:** the architecture page
  is long-form and sits at the end of the docs under Reference. The Guides
  group up front holds `getting-started.md`, a short set of instructions
  (install, pick, update, settings, Plus, help) whose first line links to the
  architecture page for readers who want the machinery.
- **The landing page's "How updates work" button** now points at the
  getting-started guide's Updating section instead of the wiki-era Updater
  page.
- **A one-page overview, added 2026-09-10** on the owner's follow-up ask for
  "a much simpler version too": `architecture.md` at
  `/docs/guides/architecture/`, around 650 words in the Guides group. One tool
  one package; the nine registries and the surface each owns; dependencies
  derived from hosted registries; one bucket, versions decide and checksums
  verify; settings that roam; and the reach past the toolkit (commands, the
  launcher, Plus). It links down to the long version and the long version
  links back up. The deep page moved to `/docs/guides/how-fnstools-is-built/`
  in the same pass so each slug matches its title and the guessable URL lands
  on the short page. Guides also gained an explicit `order` frontmatter key,
  since their position in the sidebar had been an accident of the filename.
- **Twenty dated corrections in place**, listed below, and a status refresh of
  `website/README.md`.

## How it was done

Every in-force and open design document under `docs/` that touches the
subject was read (Overview, PackagingScheme, ConfiguratorDistribution,
RegistryScheme, RegistryHomeContract, UpdaterHardening, RailHardening,
ReleaseSigning, ScopeAndPersistence, ConfigScope, LastInstallRecord,
InstallSurfaceDesign, NativeInstallerDecision, FNSToolsRedesign,
ExternalizationOwnership, CmsResearch, ForeignPackages, PlusCapabilityPackaging,
CommandCuration, LauncherToolkitBoundary, TDXLUGateIntegration,
GatedDeliveryResearch, EntitlementLifecycle, the head of EntitlementFunnelPlan,
DistributionComparison), plus `packaging/README.md`, `RELEASING.md`,
`CREATING.md`, `CHANGELOG.md`, the `fns-packaging` and `fns-registry` skills,
and the launcher repo's own `README.md`, `docs/fns-integration.md`,
`docs/fns-gate.md`, `docs/fns-command-registry.md`, `docs/licensing.md`,
`docs/releases-r2.md` and `docs/fns-plus-capabilities.md`.

Four code traces were run against the files as they are on disk: the
install and update machinery (`InstallerExt.py`, `build_installer.py`,
`ExtUpdater.py`, `ExtAuth.py`, the secure-storage modules, the picker page,
the tests that pin them); the dependency derivation and the release rail
(`build_manifest.py`, `publish.py`, `upload.py`, `release_one.py`,
`sign_release.py`, `gate_package.py`, `foreign_sync.py`, `RegistryBase.py`,
the ExtUtils masters and distributor); the launcher, the gate worker and the
family (`worker/src`, the tests, the mirror check, the four capability
packages); and the site generator. Where a document and the code disagreed,
the code won, and the document got a dated note.

## Measured on the live session (2026-09-08, v3.1.4)

| Measurement | Value |
|---|---|
| Children of `/sys/FNS_Registries` | 11: ten `RegistryBase` registries at 3.0.4 or 3.0.5, plus `FNS_CommandRegistry` |
| Live packages under `/FNSTools` (depth-1 suspects with `externaltox`) | 58, of which `FNS_Installer` is a rail; 57 carry `FNS_About` |
| Manifest | 58 packages (48 tool, 10 core), 6 gated, 1 foreign (TDXMap, self-managed), 13 starter packages |
| Config-registry family under the root | 48 COMPs; `ScopeAudit()` empty; root `Configscope` is `global` |
| Registered commands | 152 |
| Gate | `/health` answers; unauthenticated GET of `plus/v3.1.4/FNS_Collect.tox` returns 401; the plus canary 404s; `/trial/start` is `not_found` |
| Discovery pins | pins 1 and 2 answer with v3.1.4; pin 3 (`raw.githubusercontent.com/function-store/fnstools-links`) is 404 |
| Launcher mirror record | `packaging/launcher_mirror.json` records v3.1.3 builds (0.1.3 / 3.0.4) while the bucket serves v3.1.4 (0.1.4 / 3.0.5) |

## Stale claims corrected in place

Each got a dated note beside the original text; nothing was deleted.

| Where | It said | The code and the live state |
|---|---|---|
| `docs/Overview.md` §7 | three holes open: silent package removal, no upload read-back, one bucket URL with no fallback | all three closed 2026-08-27 (`publish.py` `removed`, `upload.py` read-back, discovery document); pin 3 and the server-side kill switch remain open |
| `docs/Overview.md` §8 | gated delivery "decided by nobody yet" | deployed 2026-08-29, six packages gated |
| `docs/PackagingScheme.md` §1, §7, §8, §9 | pre-3.0 core names; the three holes "present in the code today"; updater at `UPDATER/ExtUpdater.py` mirrored in `scripts/`; a local-only branch note; `aws s3 sync` as the upload | owners are `FNS_ConfigRegistry` and `FNS_ToolbarRegistry`; holes closed; the updater is `modules/suspects/FNSTools/FNS_Updater/ExtUpdater.py` and `scripts/UpdaterExt.py` is Embody's self-updater; the upload is `upload.py` behind Guided Release |
| `docs/ConfiguratorDistribution.md` intro | native `.exe`/`.dmg` installers are the bootstrap | the one-drop `FNSTools.tox`; native installers deferred 2026-08-21 (the edit `NativeInstallerDecision.md` listed and nobody applied) |
| `packaging/README.md`, The bucket | same native-installer line | same correction |
| `docs/GatedDeliveryResearch.md` frontmatter, banner, §10 | research, "not deployed, TD client side not started", `PLACEHOLDER_TIER` in the catalog | status landed; deployed and walked; real tier ids on six packages; the placeholder survives only as a test fixture |
| `docs/EntitlementLifecycle.md` banner | "BUILT, NOT DEPLOYED", 62 checks, 48 packages all free | deployed; 91 checks; 58 packages, 6 gated |
| `worker/README.md` | "Nothing here is deployed yet"; route table without claim, revoke, recheck, entitlement, pubkey | deployed since 2026-08-29; `src/index.js` dispatch is the truth |
| `docs/RailHardening.md` §2.2 and the landed banner | kill switch "enforced both ends"; pin 3's repo "does not exist yet" | client-only today (`ExtUpdater._belowFloor`); pin 3 still 404 on 2026-09-08 |
| `docs/RegistryScheme.md` table, §3, §5, §6 | nine registries; a healing watch every 120 frames and a 2 s tick; `op.FNS_TOOLBAR.op('ToolbarRegistry')`; the command registry has no master here and is promoted from the launcher | ten registries (Timeline missing from the table); `REGISTRY_WATCH_ENABLED = False`, healing runs at project save; the clone expression is `op.FNS.op('FNS_ToolbarRegistry')`; the command registry has a master and source here since v3.1.1 and ships as a store package the launcher mirrors |
| `docs/RegistryHomeContract.md`, family members | the command registry's source lives in TDXLPP | it lives here; the launcher mirrors the released artifact |
| `docs/CommandRegistration.md` pieces table | "We NEVER ship it" | shipped since v3.1.1 |
| `packaging/RELEASING.md` step 4 | `Release()`/`ReleaseMany()` run Preflight and refuse on a blocker | only `Release()` does; `ReleaseMany()`, the PI and CMS buttons and the wizard's Continue do not refuse |
| `website/README.md` | Worker undeployed, `PLACEHOLDER_TIER`, `Gateurl` unresolvable; a frontmatter example with `credit:` | all three false since 2026-08-29; `credit` is refused by the build and lives in `catalog.json` |

## Flagged, not changed

Found by the traces and left for the owner or for the next release, because
each needs a decision or a code change the research pass should not make:

- `packaging/release.json` `_comment` and `publish.py` (around line 192) still
  mention native installers; `build_installer.py` titles the bootstrap README
  "FunctionStore_tools"; `InstallerExt.py:27` names `UPDATER/ExtUpdater.py`.
- `ExtUpdater._rewriteBound` docstring still describes the pre-flip
  `reloadcustom` split (9 off / 41 on); the fleet flipped 2026-08-31.
- `packaging/parameters.json`: the `Gateurl` help says "Placeholder until the
  gate is deployed"; the par default is blank and `ExtAuth.DEFAULT_GATE` is the
  live host. Fix is `par.help` in TouchDesigner.
- `scripts/UpdaterExt.py` is a byte-identical duplicate of Embody's
  `modules/suspects/Embody/updater/UpdaterExt.py`; stale location.
- `packaging/launcher_mirror.json` is one release behind the bucket
  (v3.1.3 record, v3.1.4 published); the mirror check passes against the old
  record, so the launcher carries a registry one version behind ours.
- The third discovery pin's repository (`function-store/fnstools-links`) does
  not exist; the pin is compiled into the shipped updater.
- `CHANGELOG.md` has no v3.1.0 entry and an empty v3.0.9: `_setReleaseLabel`
  runs before Build and Stage and a refused stage does not restore the label,
  so a refusal burns a label. `upload.py --prune` enumerates CHANGELOG labels
  only.
- `packaging/docs/FNS_Updater.md` is wiki-era (the `?` toolbar icon) and says
  nothing about Refresh Store, Check for Updates, Update This Project,
  discovery or signing. The landing button now bypasses it; the page itself
  wants a rewrite through the CMS.
- Core membership is stated three ways: `packaging/docs/FNS_ConfigRegistry.md`
  (six surface registries plus Console and Updater), `build-site.mjs:198`
  ("eleven registries"), and the manifest (ten core: eight registries plus Hub
  and Updater, with Timeline, Palette and Command registries shipping as
  tools).
- `docs/CustomParHelperContract.md` (exec DATs resolve via `mod(me.dock.name)`)
  and `docs/RegistryScheme.md` (rewritten dock-free) disagree; the on-disk
  templates side with dock-based; live DAT text not verified.
- `docs/ExternalizationOwnership.md` names `scripts/QuickExt/templates/` as the
  shared CustomParHelper source; the live master syncs from
  `modules/suspects/FNSTools/QuickExt/ExtUtils/CustomParHelper.py` and the
  templates copy is the 2024 version.
- `docs/CmsResearch.md` and `EntitlementFunnelPlan.md` say FNS_CMS owns
  entitlement authoring; today the content CMS (`cms.mjs`) writes `access`
  through `gate_package.py` and FNS_CMS's Entitlement tab is empty, so the
  launcher's `TDXLU_Pro` grant has no authoring surface (G5 in
  `TDXLUGateIntegration.md`, still open with G3 and G4).
- `docs/PaletteTabContract.md` says the launcher's palette tabs still come from
  a pre-registry injector; the launcher's README says the strip belongs to
  `FNS_PaletteRegistry`. One is stale; not verified which.
- `docs/LauncherToolkitBoundary.md` proposes an `external` Compare row "when A
  lands"; A landed, the row does not exist.
- `website/index.html` lines near 1144 and 1180 still say the command palette
  is "the launcher palette today, an in-TouchDesigner palette next";
  `FNS_CommandPalette` shipped 2026-09-01. Landing copy; left for the owner.
- `README.md` at the repo root links its download badge to GitHub releases
  while the rail publishes `latest/FNSTools.tox` on the bucket; not verified
  whether a GitHub release mirror exists.
- `docs/UpdaterSelfUpdateVerification.md` (open) asks whether self-update is
  ordered last; the code answers yes (`_apply`, `_selfUpdate`), and the
  end-to-end run it plans has still not been done.

## Ideas worth explaining, with anchors

The guide's closing list is the reader-facing version. This is the longer
one, for anyone explaining the toolkit or borrowing from it.

- Versions decide, hashes verify: `.tox` export is not reproducible (three
  exports, three hashes, diverging at byte 9), so `Pkgversion` read live off
  the component is the update signal (`build_manifest._version`,
  `ExtUpdater.Compare`).
- The version lives on `FNS_About`, a child the reload rebuilds, so it travels
  inside the artifact; child-first readers and a severed-mirror preflight
  block keep authority from inverting (`release_one._versionWritePar`).
- Dependencies derived from stamped hosts (`build_manifest.py` `requires`),
  so the installer needs a topological walk and no solver
  (`InstallerExt._order`).
- One COMP, two roles: a registry copy is both the shipped host and the `/sys`
  global (`RegistryBase._become_global_registry`), and promotion never prompts
  (`_compare_versions`, newest wins, ties to the incumbent).
- Tool-page parameters as bind masters: registration settings persist with the
  tool and roam through ConfigRegistry (`RegistryBase._ensureToolRegistryPage`).
- Healing at project save, never per frame, because the toolkit runs inside
  live shows (`registry_presave_exec.healAllRegistries`).
- `StampHost` as the one blessed copy recipe, so the paid-for copy hazards stay
  fixed in one place.
- A master plus an init-time heal plus a pre-release audit for anything that
  must reach every clone host (`ConfigRegistryExt._ensureScopePar`,
  `ScopeAudit`).
- The bootstrap is the live dev root castrated (`build_installer._bootstrapRoot`),
  and the first run is a storage flag the shipped root does not carry.
- The store is a mirror; `.part` staging and sha promotion mean a refused
  download can never overwrite good bytes (`ExtUpdater._verifyFetched`).
- The install record is written per package as it lands
  (`InstallerExt.RecordInstalled`), so an interrupted pass re-runs.
- Pinned immutable releases, one rolling `no-cache` pointer, `latest/` aliases
  for humans only (`publish.py`, `upload.py`).
- A signed discovery document at pinned URLs with `minimum_updater` and
  `notices`; the last good copy cached apart from the fetch target; a local
  base URL outranks it (`ExtUpdater.DISCOVERY_PINS`, `BaseUrl`, `_belowFloor`).
- Fail closed on a bad signature, fail open on a missing one during the
  transition (`REQUIRE_SIGNED`), and refuse a floor only when it parsed.
- One package per drain tick, self-update last and detached, backup before
  destroy, and a reload proven by renewed child ids (`_drain`, `_selfUpdate`,
  `_replacePackage`, `_settleVerifications`).
- `reloadcustom` off with `reloadbuiltin` on, measured across five tox
  generations, so TouchDesigner reconciles the parameter set itself.
- Two settings stores with the `.toe` as the default and the JSON as a
  once-per-boot overlay; one scope switch; credentials in the keystore.
- Read-back verification with a printed rollback command, gated objects
  verified through the authenticated path, a privacy canary every upload
  (`upload.py`).
- `removed` versus a declared `retired` list, so a package cannot vanish
  silently (`publish.Stage`).
- Release notes accumulate per commit and become both the changelog bullet and
  the in-tool `whatsnew` (`build_manifest.AttributedNotes`).
- Foreign packages declared by `source`, mirrored on the shell, pinned by a
  committed lock, `self-managed` in the updater (`foreign_sync.py`).
- Gate the bytes: same host, `plus/` prefix, the Worker fails closed on a
  claim that does not name the package; the client names the missing tier and
  never decides access; the tier map lives once, in `wrangler.toml`, written
  together with the catalog by `gate_package.py` and cross-checked at stage.
- A one-time grant code on the loopback redirect, a product list as the claim,
  per-kind session lifetimes, a 30-day stale-trust backstop, and a revoke
  that is not an oracle (`worker/src/index.js`).
- Tag-based command discovery and `announce()`: a consumer that arrives later
  rediscovers every tool; `surface` and `capability` as progressive
  enhancement that is never a gate (`FNSCommand.py`, registry 1.7.0).
- The launcher installs through the toolkit's installer, `fns.install` is dry
  run by default and minimal never removes, and the launcher seeds the store
  only on a cold start (`InstallerExt.FnsCommands`, `ResolvePlan(minimal=)`).
- One ownerless curation file with per-entry merge, tombstones and an in-file
  `seeded` stamp (`CommandCuration.py`).
- A generated public mirror that withholds gated sources and refuses a root
  tox that embeds one (`scripts/publish_public.py`).
- The `FNS_` prefix is identity; every listing shows the public name
  (`PublicToolNames.md`).

## Sources

The four trace reports live only in this session's transcript; every claim
they made that reached the guide or a correction was re-checked against the
file it cites before being used. The live measurements above were taken with
one read-only `execute_python` on the running dev project. The gate and pin
probes were read-only GETs.
