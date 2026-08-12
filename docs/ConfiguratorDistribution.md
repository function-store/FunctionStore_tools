# Configurator Distribution — Design Notes

How a user could pick and choose which FunctionStore tools to install —
via a configurator website/app — instead of taking the whole toolkit.
Companion to [UvPackagingResearch.md](UvPackagingResearch.md) (which owns
the pip/uv **delivery-mechanism** research) and
[RegistryScheme.md](RegistryScheme.md) (which owns the **in-project
runtime** relationship between tools and registries). Nothing here is
implemented — captured from a design discussion 2026-08-10.

## 1. Why this is feasible now

The redesign25 registry architecture already did the hard part. Tools are
self-contained COMPs carrying **stamped registry contribution DATs**
(Toolbar/Navbar/OpMenu/MainMenu/PaneType registries, HotkeyManager
entries). Registries discover contributions; a missing tool just means
missing entries. That is exactly the property "install any subset"
requires. The pre-redesign monolith could not do partial installs — the
registry scheme is the enabler, and this document is downstream of it.

Remaining coupling to audit before any of this works: `/sys` globals,
`RegistryBase.py`, the registry hosts themselves, `tools_ui`, and any
`op.X` global-shortcut references *between tools*.

## 2. The layers

### 2.1 Core + feature split

- **Core package** (always installed): registries + RegistryBase + `/sys`
  bootstrap + shared UI shells (toolbar/navbar/mainmenu hosts).
- **One package per tool** (or per small coherent group): self-registers
  on load via its stamped contributions.
- **Design rule worth committing to early: tools depend only on core,
  never on each other.** Then the manifest needs no dependency solver,
  the configurator needs no constraint logic, and partial installs can
  never half-break. Cheapest architectural rule available while the
  redesign is still in flight. (If cross-tool deps must exist, they
  become real pip dependencies — see §3 — and uv resolves them; but
  every such edge makes the configurator and the failure modes worse.)
- **Corollary (decided 2026-08-12): registry MASTERS live in core; tools
  ship scrubbed hosts.** Host cloning is not just a dev convenience — the
  globals' healing tick re-asserts clone exprs in USER projects too, so
  cloning is the core→fleet update rail: updating core rolls every
  in-project host (even ones inside tool toxes the user never updated)
  forward to the new master, while host Registration par VALUES survive.
  The catch it papers over: clone sync is NOT version-aware — with a
  newer master anywhere but core, an old in-project master would
  structurally DOWNGRADE a newer tool's host (the /sys global arbitrates
  by Version; clones don't). Masters-in-core makes "the in-project
  master" and "the newest registry version" the same thing by
  construction, so the downgrade case cannot arise. Revisit (version-
  aware _healHostClones) only if mixed-age installs ship before the
  core/tool split does.

### 2.2 Build pipeline

Headless TD or a live session driven via Envoy walks the tool list,
exports each COMP (`ExportPortableTox`, same artifact as today's
`modules/release/` output — see UvPackagingResearch §6 wrinkle), computes
hash + version, and writes a `manifest.json`: name, description,
category, icon, version, sha256, deps, artifact URL. The existing UPDATER
tool should consume the *same* manifest for updates — one catalog, two
consumers.

### 2.3 Install rails (they compose, not compete)

1. **Installer COMP** — a single small `.tox`, no launcher required.
   Reads a selection (JSON) + manifest, fetches artifacts over HTTPS
   (Web Client DAT, non-blocking), loads core then tools. Works for
   users who have nothing else installed.
2. **TDXGL sidecar** — the launcher utility bus already exposes
   `load_tox` with `persist`, `parent`, `externaltox`, `toxfile_module`
   (see `TDXGLUtilityExt._handleCmdLine`, action `load_tox`). A
   "store" panel in TDXGL renders the manifest with checkboxes and
   pushes `load_tox` commands into live sessions; `persist` survives
   restarts. Best UX: already installed, already knows which TD
   sessions are alive, and browsers can't speak raw TCP to the bus
   anyway.
3. **pip/uv skeleton** — see §3. Delivery via package manager; still
   needs a bootstrap COMP in-project to materialize toxes into the
   network (UvPackagingResearch §1: uv can never materialize an
   operator network).

### 2.4 Configurator front-end

A static site (GitHub Pages) over the same `manifest.json`: pick
features, dependencies auto-check, output one of:

- a downloadable `selection.json` + installer-COMP bundle;
- a client-side-assembled zip of the chosen toxes;
- a deep link (`tdxlpp://install?tools=...`) handled by TDXGL, which
  performs the install over its bus — website as storefront, launcher as
  installer;
- a `pip install fns-tool-a fns-tool-b` line (§3 route).

A browser POSTing directly to a Web Server DAT on `127.0.0.1` is
possible but the fiddliest option (CORS, port discovery) — noted, not
recommended.

## 3. The pip-skeleton pattern (marker packages)

Refines UvPackagingResearch with the *selection* mechanism. If pip is
the rail, feature selection must live in pip's world or the resolver
contributes nothing:

- Each feature is a tiny **marker package** (`fns-tool-quickop`, …):
  no real code, just metadata — tox artifact URL, version, sha256, and
  pip deps on `fns-tools-core` (+ any cross-tool deps, if allowed).
  Extras form also works: `fns-tools[quickop,swapops]`.
- The **bootstrap COMP** enumerates installed `fns-tool-*`
  distributions and loads their toxes in dependency order. This is the
  "skeleton on pip, bootstrapper collects toxes" model.
- **Pin, never "latest"**: package version N points at an immutable
  artifact (GitHub Release asset / versioned bucket key) with its hash
  in the metadata. Mutable `latest/` paths → unreproducible installs,
  uncorrelatable bug reports.
- **Embed vs fetch**: if toxes are pinned per package version anyway,
  embedding them in the wheel as package data (tdp-MVP's model,
  UvPackagingResearch §2.1) is simpler and atomic — `pip install` *is*
  the collection step, offline installs work, no runtime HTTP in TD.
  Remote-fetch only earns its complexity when payloads are large or
  binaries must update without republishing packages.

### Honest case against pip as the primary rail

(From the same discussion; UvPackagingResearch is neutral on this.)

1. It doesn't install anything *into TD* — the bootstrap COMP and all
   the hard work (core/tool split, audit, manifest) exist regardless;
   pip only replaces the download step.
2. Scope mismatch: `TDPyEnvManagerContext` is per-project; the toolkit
   is session-level UI tooling wanted in *every* project. (Unverified
   whether a shared/global env mode exists — check docs before leaning
   on it.)
3. Two sources of truth: pip's ledger is the venv, the user's reality
   is the network. Dissolves only under fully ephemeral loading (toxes
   loaded fresh every startup, never saved into the .toe) — a strong
   commitment made mostly to accommodate the transport.
4. Audience friction: TD users drag toxes; "set up a Python
   environment first" is an adoption tax. TD 2025.31310+ only.
5. Lifecycle: partially mitigated — the env manager Helper runs during
   TD core startup *before* any COMP cooks (UvPackagingResearch §4.1),
   so `sys.path` is ready before the bootstrap COMP inits. Failure
   modes still surface as a silently missing toolkit rather than an
   installer error.

Verdict from the discussion: with TDXLPP existing, pip mostly
duplicates the delivery layer while adding per-project ceremony. Without
TDXLPP it would rate considerably higher. The steel-man is the
ephemeral-bootstrap model — one universal bootstrap tox that never
changes, pip as the sync mechanism behind it.

**Correction worth recording**: TDPyEnvManager manages pip
packages/venvs — it does not "install toxes." Any tox materialization
is our own bootstrap's job, whichever rail delivers the bytes.

## 4. Recommended order

1. **Dependency audit + core/tool boundary definition** — the gate;
   everything else is mechanical. Decide the "tools depend only on
   core" rule here.
2. Manifest + per-tool tox export automation (Envoy can drive it).
3. Installer COMP consuming manifest + selection JSON — "pick and
   choose" works with zero web presence at this point.
4. TDXGL store panel over the `load_tox` bus.
5. Static configurator site as the public face (selections/deep links).
6. Optional: pip marker-package rail on top (§3), sharing the same
   artifacts and manifest.

## 5. Open questions

- [ ] Does TDPyEnvManager offer any shared/global (non-per-project)
      environment mode? (Affects §3 objection 2.)
- [ ] `tdxlpp://` protocol-handler registration in TDXGL — feasible on
      all target OSes?
- [ ] Ephemeral vs persisted installs as the default: `load_tox
      persist=True` semantics vs load-fresh-every-start (affects update
      story and §3 objection 3).
- [ ] Package granularity for groups (MISC, OUTPUT, SwapOps): per-tool
      or per-group artifacts?
- [ ] Where does the manifest live — GitHub Releases per-version, plus
      a rolling `manifest.json` index?
