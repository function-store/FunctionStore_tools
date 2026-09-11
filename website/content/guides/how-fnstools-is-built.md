---
title: How FNSTools is built
section: reference
order: 10
summary: The machinery under the toolkit, explained once. How one dropped file becomes a picked install, how a version decides an update while a hash only verifies it, how tools plug into shared surfaces without knowing each other, how the launcher reads the same registry, and how the supporter gate locks bytes.
---

[Architecture](/docs/guides/architecture/) is the same story in one page. This one is for the curious: people who want to know why the toolkit behaves the way it does, tool authors who want to ship something through the same rail, and anyone building their own TouchDesigner distribution who would like to borrow the parts that worked. Each tool has its own page for the everyday questions. This one is about the ideas the tools share.

Everything here describes the toolkit as released on 2026-09-08 (v3.1.4). Counts change with every release; the shape does not.

## The shape in one paragraph

FNSTools is a catalog of packages, each a single `.tox`, published to one bucket with one manifest. A small core carries the registries every tool plugs into, plus the updater, the hub and the console; everything else is optional and picked one by one. Every package declares its own version on the component itself, so an update is decided by comparing a live parameter against the published manifest, and the hash on each artifact only proves that a download arrived intact. Tools depend on core and on nothing else: what a tool needs is derived from the registries it hosts. Settings live in the project file, with an optional machine-wide overlay that follows you between projects. A separate desktop launcher reads the same command registry and installs through the same installer, and a handful of packages sit behind a supporter gate that refuses to serve their bytes to anyone without an entitlement. The rest of this page takes those sentences one at a time.

## What a package is

A package is a component directly under the toolkit root that the project's release tracker (Private Investigator) follows as a suspect, with its own `.tox` on disk. That is the entire identity test. Nothing registers a package anywhere: add a tool the normal way and every release pass finds it, exports it, hashes it and publishes it. If a package stops passing the test, the release refuses to proceed until the drop is declared in the release file, so a tool cannot vanish from the catalog by accident.

Two kinds exist. Core is installed as a unit: seven registries ([ConfigRegistry](/docs/fns-configregistry/), [ToolbarRegistry](/docs/fns-toolbarregistry/), [NavbarRegistry](/docs/fns-navbarregistry/), [MainMenuRegistry](/docs/fns-mainmenuregistry/), [OpMenuRegistry](/docs/fns-opmenuregistry/), [PaneTypeRegistry](/docs/fns-panetyperegistry/), [HubRegistry](/docs/fns-hubregistry/)) plus [Updater](/docs/fns-updater/), [Hub](/docs/fns-hub/) and [Console](/docs/fns-console/). Tools are everything else, including two more registries ([PaletteRegistry](/docs/fns-paletteregistry/), [TimelineRegistry](/docs/fns-timelineregistry/)) and the [CommandRegistry](/docs/fns-commandregistry/), which install when a picked tool needs them or when you pick them yourself.

A package author maintains exactly three things:

- `Pkgversion`, the version the updater compares. It lives on a child component named `FNS_About`, and the tool's own About page mirrors it. The reason for the child is explained under updates.
- A catalog entry: category, description, and a few presentation fields (author, homepage, a changelog link, where it installs, and `access` for a gated package).
- A documentation page, a sibling of the one you are reading. The site build refuses to run on a catalogued package with no page, so a package ships with its docs or it does not ship.

Everything else is derived from the live project when the manifest is built: dependencies, the surfaces a tool appears on, its hotkeys, its op count, its artifact hash and URL, and the launcher block described later. Wanting to hand-declare any of these usually means the tool is shaped wrong.

One naming convention runs through the whole site. The `FNS_` prefix on a component name is an operator-name convention, and every listing a person reads drops it: the package `FNS_BeatMod` displays as BeatMod. Its shortcut, its file name and its COMP name keep the prefix, because those are identities that code looks up.

### Where a package lands

By default a package installs inside the toolkit container you dropped. Two other placements exist, set in the catalog. `root` puts the package beside the container at the network root, for tools that need to live at `/` (the family product [TDXMap](/docs/tdxmap/) is one). `pane` spawns a reusable component into the network you are working in, with palette-component semantics: the install record on the toolkit root is what counts as installed, and spawned copies are your work, untouched by any update.

## Registries: how tools plug in without knowing each other

The pattern under everything is a registry: one global manager per TouchDesigner surface, and many host publishers inside tools. A tool that wants a toolbar button carries a small host component, a clone of the ToolbarRegistry master, with a Registration page naming what to publish. On load the host publishes its one entry into the global; the global owns the surface and decides what exists, in what order, and what is shown.

The same component plays both roles. A registry master is a package in the catalog; a copy of it inside any tool is a host. At extension init a host looks for its global. If none exists it promotes a copy of itself into `/sys/FNS_Registries` and claims the global shortcut; if an older global exists it merges the entries, replaces it and hands the data over; if the global is newer or equal it stands down. Newest wins, ties keep the incumbent, and nothing in that path ever prompts. That last rule was paid for: a version-mismatch dialog once fired during project load for every host of every registry at once, and TouchDesigner wedged before it could be inspected.

`/sys` never saves with the project, so the globals are rebuilt on every open. That is deliberate. The publishers are the source of truth: every host republishes on init, and a heal that runs at every project save re-resolves moved operators, drops entries whose host has died, re-injects anything the surface lost and republishes any host the global has no entry for. A periodic version of that heal exists in the code and is switched off, because re-applying every host on a timer showed up as load, and this toolkit runs inside live shows. Edits you make in the manager (order, visibility, bar width) are written back to parameters on the tool itself, so they persist in the `.toe` with the tool, and a tool replaced by an update comes back where you left it.

| Registry | Surface it manages |
|---|---|
| [ToolbarRegistry](/docs/fns-toolbarregistry/) | TD's bookmark bar, as mirrors of the tools' widgets |
| [NavbarRegistry](/docs/fns-navbarregistry/) | every pane bar, as stamped copies, since each pane needs its own breadcrumb |
| [MainMenuRegistry](/docs/fns-mainmenuregistry/) | the main menu bar, with TD's own items adopted so entries can sit between them |
| [OpMenuRegistry](/docs/fns-opmenuregistry/) | the OP Create dialog: search words, row decorations, right-click items, filter stages, panels, op alternatives |
| [PaneTypeRegistry](/docs/fns-panetyperegistry/) | the pane-type menu on every pane bar |
| [PaletteRegistry](/docs/fns-paletteregistry/) | tabs in TD's Palette Browser |
| [TimelineRegistry](/docs/fns-timelineregistry/) | panels in the timeline dialog, beside the native transport |
| [HubRegistry](/docs/fns-hubregistry/) | the tabs of the Hub window |
| [ConfigRegistry](/docs/fns-configregistry/) | the settings file; its surface is a JSON document, described below |
| [Console](/docs/fns-console/) | the toolkit's web front, one tab per contributing tool |

The [CommandRegistry](/docs/fns-commandregistry/) is the deliberate exception to the shape: it holds no entries and stamps no hosts. It discovers tools by a TD-native tag and harvests their commands live, which is what lets a consumer that arrives later find every tool that announced itself earlier.

Three consequences fall out of the pattern:

- Partial installs are possible at all. A registry discovers contributions, so a missing tool is just missing entries. The pre-3.0 toolkit was a monolith whose installer copied real buttons into the bar on every launch, and it could only be installed whole.
- Surfaces degrade gracefully. The ToolbarRegistry injects into TD's stock bookmark bar whether or not any FNS tool has contributed a widget to it, so a single tool dropped into a bare project still shows its button.
- The toolkit can be extended with the machinery it is built on. The registry masters ship raw and cloneable; your own component can carry a host and appear on the toolbar, the nav bar or the OP menu like any FNS tool. [Hub](/docs/fns-hub/) is the management surface: drop a panel component on the FNS button and it is stamped with a host and registered.

## Dependencies are derived

Registry masters live in core and tools carry stamped hosts, so a tool's requirements are exactly the core packages owning the registries it hosts. Every tool needs the ConfigRegistry; a tool with a toolbar button also needs the ToolbarRegistry; and so on. The manifest builder reads the hosts off the live components and writes the list. Nothing hand-maintains it, so it cannot drift.

Tools depend only on core. That rule is what lets the picker resolve a selection with no solver: core plus your picks, installed in an order that walks the requirement list. When two tools cooperate, the link is an optional integration that must degrade when the other side is absent. The idiom is a guarded lookup on the global shortcut, which doubles as the feature detect:

```python
cpp = getattr(op, 'FNS_CPP', None)
if cpp is not None and hasattr(cpp, 'Reference'):
    cpp.Reference = target
```

The manifest builder recognises both this guarded form and a bare `op.X` reference, and lists them as `integrates_with` so the picker can mention the pairing without enforcing it. The one thing the list cannot express is a minimum version of a core package. A tool that starts needing a newer ConfigRegistry API has no way to declare it yet, and that gap is on record.

## Bootstrapping: from one dropped file to a picked install

`FNSTools.tox` is the toolkit root itself with the tools removed. The build copies the live development root, destroys every child except the installer, the vendored browser panel and the root's own config host, strips the authoring pages and all storage, freezes the root's parameters to constants, and loads a copy of the Updater package in. What you drop is what the toolkit is developed in, rail for rail, so the shipped root cannot drift from the real one.

### The first drop

The root carries an Execute DAT whose `onCreate` fires for every way a DAT can come into being: dropped from the `.tox`, loaded with a project, copied, pasted. Only the drop is a first run, and a storage flag on the root tells them apart. The shipped root has no storage at all; the flag is written the moment the DAT first fires, and ninety frames later, once the installer's extension and the browser panel are up, it pulses the root's Pick Tools. If you dropped the file into a nested network, the root moves itself to `/` first, because the toolkit's global shortcuts and the network-level tools expect to live there. The development master never welcomes: its root is bound to an external tox, and the welcome checks that first.

### The picker is served

The installer carries the picker page and a Web Server DAT, dormant until asked. Pick Tools binds it to `127.0.0.1` on the first free port from a default upward, serves `http://127.0.0.1:<port>/`, and opens that in the sibling browser panel inside TouchDesigner, with your system browser as the fallback. The page gets its catalog from a `/manifest.js` route on the same server: the store's manifest, what this project already has installed, and your account state. When the store is empty it kicks a manifest-only refresh, and the page says it is fetching while it polls.

The page is one file with three lives. The installer serves it; the same file works double-clicked as a standalone page that downloads a `selection.json`; and the site publishes it as [the online picker](/get/), dressed in the site's header and footer, where the button becomes "Copy install script". A first run gets a guided setup: Set up like last time (when this machine remembers an install), Recommended (the tools flagged in the catalog), Everything, or Pick my own, with a step strip through choose, adjust and review, and a done step whose Open Settings hands the panel to the Console.

### The store is a mirror

Downloads land in a machine-wide store, `FNStools_ext/store` inside your user palette folder. Nothing in it is anyone's work: a file whose hash disagrees with the store's manifest is stale cache, so a refresh re-downloads it and the installer refuses to load it. Artifacts arrive in a staging file and replace the store copy only after their checksum passes, so a failed or refused fetch leaves the previous good bytes untouched. A connection that never opens produces no callback at all in TouchDesigner's downloader, so a stall watchdog closes that hole.

Because the store is machine-wide and the installer only ever installs from it, a machine that has synced once installs with no network. The launcher's offline path is built on that property (below).

### Plan, then install

The selection becomes a plan before anything is written. Core is added unless the caller asked for a minimal install, every requirement is walked, and each package is marked present, to download, stale, locked (a development checkout is refused), removal (a tool this project has that you unticked), or missing an artifact. Install loads each artifact into the target, verifies it with one forced recook, records a row in an `installed` table on the toolkit root (package, the sha256 of the bytes that actually landed, release, when), and flips on console exposure for tools that carry a Console host. The record is written per package as it lands, so an interrupted pass can simply be re-run.

Where the files end up is your choice at install time, and the updater follows whatever binding each package has:

| Mode | Files live | Update path |
|---|---|---|
| embedded (default) | inside the `.toe` | replace the component from the store artifact |
| shared | bound to the palette store | rewrite the file and reload; machine-wide by design |
| project | copied into `<project>/FNStools/` or a folder you name | rewrite and reload; isolated per project |

### The other ways in

The bare `FNS_Installer.tox` is the same installer without the browser panel, for a project that already has a toolkit container. The install script from the online picker is one Textport line that embeds only the picked names: it fetches the rolling manifest at paste time, downloads core, your picks and the bootstrap from the pinned release URLs, verifies every hash before writing anything, stocks the store, loads the bootstrap into the current network, marks it welcomed so no picker appears over a scripted drop, and hands the installer the selection one deferred call later. A copied script stays valid across releases because it resolves everything at paste time. There is a headless rail as well (`install.py`, a thin wrapper over the same implementation, so the two cannot drift), and the launcher's FNSTools tab, which asks this same installer to do the placing.

Native `.exe` and `.dmg` installers were considered and deferred. The audience already runs TouchDesigner, dragging a `.tox` into a network is a gesture they know, and unsigned installers throw operating-system warnings that hurt adoption more than having none.

### Set up like last time

When a project saves, the toolkit root's own config host writes one entry into the roaming settings: the list of installed tools, the project name, the time and the file mode. Dropping the bootstrap into a new project on the same machine offers that list as the first card of the guided setup, pre-checked. It is an offer: the card lands on the ordinary review-then-install path, because a download into your project on the strength of a different project's history is exactly the surprise a live-show toolkit must avoid.

## Versioning and updates

Keeping four questions apart is the whole design:

| Question | Answered by |
|---|---|
| What packages exist, and what do they need? | the manifest, derived from the live project at release time |
| Is a newer build available? | `Pkgversion`, a parameter on every package, read live off the installed component |
| Where do I fetch it? | the manifest's pinned per-release URL |
| Did the download arrive intact? | the artifact's sha256, and nothing else |

### Versions decide, hashes verify

The version is read live off the installed component. That is the only thing that works for a package embedded in a `.toe`: there is no file to hash and no record to consult, but the component still declares what it is. No side table can drift out of truth, because the component is the truth.

Hashes were tried as the update signal and reversed. Exporting one untouched component three times gave three different files (66198, 66190 and 66150 bytes), diverging at byte nine of the container header, before any content. Comparing hashes would have marked every package updated on every release. The hash keeps the job it is good at: proving that what you downloaded is what was published.

The version lives on a child component, `FNS_About`, and the tool's own About page mirrors it. The reason is the reload described below. An in-place update rebuilds a component's children from the artifact while preserving the component's own custom parameter values, so a version stamped on the tool itself would keep reading the old number after an update. A child is rebuilt with the artifact, so the version travels inside it. The same child carries the TouchDesigner build the package was exported from, which becomes the package's install floor, and a docs-page override.

### One bucket, pinned releases, one rolling pointer

Distribution is buckets and manifests, on Cloudflare R2 behind `storage.functionstore.tools`. Each release is a pinned, immutable directory: its manifest and its artifacts never change once published, so a manifest always resolves to the bytes it was built from, and a bug report can be correlated with an exact install. One rolling `manifest.json` at the root is the only mutable pointer, shipped with `no-cache` so a CDN cannot silently freeze everyone on an old release. The `latest/` aliases the site's download buttons use exist for humans; installs resolve pinned URLs from the manifest.

A moved or dead bucket host was the one failure that could not be fixed after the fact, so a discovery document sits above the manifest: a small JSON at three pinned URLs on two independent origins, compiled into the shipped updater and never changed. It says where the manifest is, and it carries `minimum_updater` (an updater below that floor refuses to run and says why, which is the recall lever for a bad shipped updater) and `notices` (a message every install sees). The last good copy is cached on disk separately from the fetch target, so an error page cannot destroy the offline fallback. A local or `file://` base URL outranks discovery, which is what keeps the mirror and offline test rails working.

The manifest and the discovery document are signed with a dedicated Ed25519 key at staging time, and every install verifies the signature against a public key pinned in the updater. A well-formed signature that fails is tamper evidence and refuses, always. A missing signature is allowed and logged loudly during the transition, so documents published before signing existed cannot strand the fleet; the transition ends by flipping one constant in a normal update.

### Three motions

| Motion | Cost | Does |
|---|---|---|
| Refresh Store | whole store | fetch the manifest and every artifact whose bytes differ; machine-wide, touches no project |
| Check for Updates | one small JSON | fetch the manifest only, then compare |
| Update This Project | only what differs | fetch just what this project needs, then apply |

`Compare()` is the single decision point. It walks the toolkit root and reports each package as `update`, `current`, `unversioned` (declares no version; shown, never touched), `incompatible` (its TouchDesigner build floor is above the running build; reported, never updated), `locked` (a development checkout that must not be written), `missing` (recorded as installed, component gone), `component` (a pane spawn, frozen at its spawn version), or `self-managed` (a family product that updates itself). An update pass installs nothing new: a package you never chose stays uninstalled.

The Console's Updates tab renders those states verbatim, with each release's notes beside the row, and drives the same check and update calls.

### Applying an update

The pass snapshots settings first, orders the updater's own package last, and applies one package at a time, a few frames apart: each replacement reinitialises extensions, so batching them into one frame was both a long main-thread block and the crash-prone case. A package bound to a file updates by rewriting the file and pulsing the reload, with no copy or destroy of an extension-bearing component. An embedded package is exported to a backup first, then destroyed and reloaded from the store artifact, and restored from the backup on either failure path; a backup that cannot be written refuses the replace, because without one the destroy is unrecoverable. Every reload is proven: the child ids are recorded before the pulse and checked on the next tick, because a reload that quietly did nothing looks identical to one that worked.

The updater's own package goes last and runs from a detached script that references nothing it is about to destroy. That path is structurally correct and its failure is bounded, and it is also the one path the docs record as never exercised end to end on a real install.

### What an update keeps

This was measured on TouchDesigner 2025.33070 across five generations of one component, and it is the load-bearing part. With the flags the fleet now ships (`reloadcustom` off, `reloadbuiltin` on):

| On reload | Result |
|---|---|
| a custom parameter you edited | value preserved |
| a custom parameter new in this build | arrives with the build's value |
| a custom parameter retired in this build | removed by TouchDesigner itself |
| built-in parameters (extension wiring, shortcuts) | take the build's values |
| children | fully rebuilt from the artifact |
| the external-tox binding and node position | survive |

The parameter set reconciles itself: new parameters arrive, retired ones leave, and your values survive for everything present in both. The updater needs no parameter inventory and destroys no parameter, which is the mechanism another toolkit's updater got wrong twice (destroying one sequential parameter renumbers the survivors). TouchDesigner does this natively; the toolkit only had to choose the flags and measure them.

## Where settings live

There are two stores, and the project file is the default one. A tool's custom parameters, the configurators' state tables and stored values live in the `.toe` and survive every save with no registry involved. The [ConfigRegistry](/docs/fns-configregistry/) adds a machine-global overlay: one aggregated JSON in your user palette, `FNStools_ext/config/FNStools_config.json`, applied once per session about thirty frames after each tool registers. That single deferred apply at boot is the only moment local state is at risk; every save and every mid-session edit leaves the project file authoritative.

A menu on the toolkit root, Config Scope, decides whether the overlay exists at all. `global` (the default) roams; `project` never reads and never writes the file, so the project carries everything with no sidecar. Every host carries a guarded copy of that choice, and a tool released on its own, with no toolkit root, reads `project`, because shared roaming without the toolkit would be a surprise.

Each tool has two rails in the file: `pars`, its custom parameters, filtered conservatively (a parameter missing from the live tool is never created, so a stale file cannot resurrect a retired setting), and `state`, whatever the tool returns from its own save callback. Per-tool hatches let a tool keep named parameters or whole pages out of the file, and a tag on any component registers it with defaults, so a micro-tool too small to carry a host still roams. A few things stay local on purpose: bookmarks that are operator paths, MIDI and OSC maps that travel with the show, and anything that is a credential. Credentials never touch this file; the supporter session lives in the operating system's keystore.

## Shared code, and how a fix reaches every tool

Every tool carries a small docked component, ExtUtils, with the helpers the toolkit shares: a parameter helper that turns custom parameters into typed properties and routes their callbacks, the command module described in the launcher section, and callback decorators. Every registry host carries the registry base class. None of these are copied by hand. The masters live in one place and every copy is a file-synced DAT or a clone, so editing one file reaches roughly a hundred live components at once, and a release strips the file bindings so the shipped artifact is self-contained.

Cloning has one edge the toolkit turned into a rule. A clone forces a component's children and leaves the component's own parameters alone, so a parameter added to a master reaches only hosts stamped afterwards. A fix meant for every host therefore goes into the master and into a heal that runs on every init, with an audit that must return empty before a release. The Config Scope parameter is the worked example: forty of forty-six hosts lacked it until the heal landed, and the audit is what proves it cannot recur.

Releases ship inert. A pre-release hook runs on the staged copy of every package and strips authoring bookkeeping, the clone binding, file bindings and host registration state, so the artifact's first load installs or upgrades the global and registers nothing until the tool's own init runs. Console exposure ships off on every artifact and the installer flips it on as the package lands, which is how one artifact serves both a standalone drop and a toolkit install.

## The release pipeline

A release is driven from inside the development project by a guided wizard that walks four steps: scope (what is shipping), preflight, notes, confirm. Publishing runs bump, build, stage, upload, the same rails the per-package buttons drive.

Preflight checks what the publish rails cannot refuse: a package edited live but never landed to its `.tox` (an externalized package reloads from its file, so that work would ship stale), a rail artifact older than the sources it embeds, a severed version mirror, packages with no release notes, catalog fields that belong to a different kind of package, an unmirrored foreign package, and a dirty repository.

Release notes accumulate as work lands, in one file, in the commit that changes a package. A line starting with a package name and a colon rides that package's changelog bullet and ships as `whatsnew` in the manifest, which is what the updater shows beside an available update. The file is cleared on publish; its text moves to the changelog and into the release's own manifest.

Staging lays out a local directory that mirrors the bucket exactly, re-hashes every staged file against the manifest and refuses to report success on any mismatch. It refuses a release that bumps nothing, a package that vanished from the live project unless its retirement is declared, and a gated package that no tier grants. It hashes the two install rails into the manifest and signs. Upload writes pinned objects as immutable and the rolling documents as `no-cache`, re-fetches every object it wrote and compares its hash (a mismatch fails the run and prints the command that rolls it back), and plants a canary under the gated prefix to prove the public rail does not serve it. Three more checks bracket a release: every discovery pin must return the real document, the launcher's copy of the shared registry artifact must match byte for byte, and the site must build, because a package page is part of the package.

Two editors share the job. A content CMS runs on the developer's machine and writes the catalog, the documentation pages and the categories straight into the repository, with git as the audit trail. A second, inside TouchDesigner, owns what needs the live project: the dirty list, per-package saves, preflight, staging, foreign-package sync, and the one docs-URL override that lives on a component. Neither owns state. The files are the truth, and the public site is a static build that reads the same files.

The public GitHub mirror is generated: a filtered copy of one commit that withholds the sources of gated packages and refuses to run if the root artifact embeds one, so the publish that forgets cannot leak paid code.

### Foreign packages

A tool whose bytes and version are owned upstream, by another repository with its own release rail, can still be listed in the catalog and installed from the picker. The catalog entry carries a `source` block naming the upstream manifest and artifact. A shell-side sync fetches it, verifies its hash and pins version, hash and URL in a lock file committed with the release; the manifest builder reads only the lock, so no network request ever runs on TouchDesigner's main thread; and the updater reports the installed copy as self-managed and leaves it to its own updater. [TDXMap](/docs/tdxmap/) is the first: a family product, mirrored into the store at the version its lock names, governed by its own licensing after install.

## The launcher, and how this becomes an ecosystem

[TDX Launcher Ultra](https://launcher.functionstore.xyz) is a desktop application for Windows and macOS: a project launcher that also drives running TouchDesigner sessions through a companion component it injects. It is a separate product with its own release rail, and it shares more with the toolkit every month. What the two share is the answer to how a collection of tools becomes an ecosystem.

**One command registry.** Every FNS tool declares its actions with a decorator on the method and one announce call at init; label, help and typed parameters are derived from the method name, docstring and signature. The announce sets a TD-native tag on the component and registers with the [CommandRegistry](/docs/fns-commandregistry/) if one is present. The registry ships two ways to the same single copy: as a core package for toolkits without the launcher, and inside the launcher's companion, which carries the toolkit's released artifact verbatim, policed by a byte-for-byte mirror check before either side releases. Both loaded together resolve to one global. The tag is what makes the arrangement durable: a registry that arrives later, or replaces itself on a version bump, rediscovers every tagged tool by rescanning. A user who installs Autosave first and the launcher a month later sees it light up in the launcher's session bar with no reinstall. The same registry feeds the in-TouchDesigner [CommandPalette](/docs/fns-commandpalette/), the launcher's quick-launch overlay and its palette tab, and TouchDesigner's own dialogs and session actions are registered as built-in commands beside the tools.

**One curation file.** Favourites, hidden commands and presets are one machine-wide JSON beside the settings file, read and written by the palette and the launcher alike, keyed by tool and command id. Two consumers write at different moments about different commands, so the file merges per entry by timestamp, removals are tombstones so a stale reader cannot resurrect them, and each consumer seeds the file from its private store exactly once per machine, recorded in the file itself so a restored backup cannot re-seed.

**One installer.** The launcher's FNSTools tab is a store, a picker and a settings editor over the toolkit's bucket, and it places no package itself: it syncs the store, writes a selection and asks the installer to do the placing, recording and updating the toolkit already knows how to do. The installer publishes `fns.install` as a command (dry run by default, with a minimal mode that installs one package and its requirements and proposes no removals), so any consumer can ask the same way. The one component the launcher places itself is the bootstrap, fetched from the rolling manifest by hash at the launcher's build time and bundled for machines that have never been online. The bundle seeds the store only when the store is empty, because the store is authoritative and the bundle is the cold-start fallback, and a newer bundle can never advance a partial store: the manifest is an all-or-nothing document.

**Launcher capabilities.** Four packages carry commands that target the launcher's session view and context menu and declare a capability id the launcher recognises, so it can render rich native UI for them: [Autosave](/docs/fns-autosave/) (free), [Collect](/docs/fns-collect/), [MediaBrowser](/docs/fns-mediabrowser/) and [Remote](/docs/fns-remote/). The rule they were written to: a launcher capability is a complete TouchDesigner tool that also lights up the launcher's session view when both are installed. None of them requires the launcher, and the three lookups they make toward the launcher's companion are guarded and degrade to standalone behaviour. The manifest derives a `launcher` block for such packages so a bundler can find the few that reach a surface beyond quick launch; `seedable` inside it is false for anything gated, so a free app can never bundle paid bytes by reading the wrong key.

**One sign-in.** The launcher's Pro tier and the toolkit's Plus packages sit on one tier map, behind the same gate, the same Patreon client and the same signing key. A sign-in on a machine is published to a shared session file that either product adopts, and signing out anywhere revokes the session and signs the machine out everywhere.

**One settings surface.** The launcher edits a running session's settings through the ConfigRegistry's own loopback settings server, so validation and persistence stay TouchDesigner's, and edits the roaming JSON directly when no session is running.

**One family.** The other Function Store products appear on this site from one content file injected into two pages, and TDXMap ships through the store as a foreign package while keeping its own updater and licensing.

The recipe, stated once: TD-native tags that need no registry to exist, guarded lookups that degrade instead of failing, one store that both sides treat as a mirror, one gate, one config folder, and a contract written down on both sides before either side writes a line against it.

## Gated releases: Plus

Six packages are gated today: [BeatMod](/docs/fns-beatmod/), [Collect](/docs/fns-collect/), [MediaBrowser](/docs/fns-mediabrowser/), [PreviewPanel](/docs/fns-previewpanel/), [Remote](/docs/fns-remote/) and [TimelineTools](/docs/fns-timelinetools/). Everything else is free and MIT, and [the Plus page](/plus/) says what a membership buys. This section is about how the gate is built.

**Gate the bytes.** Greying out a card in the picker is cosmetic. The only lock that means anything is the bucket refusing to serve the object, so gated artifacts live under a private `plus/` prefix on the same storage host, served only through a Cloudflare Worker that checks a download token. The prefix stays on the same host on purpose: the updater derives an artifact's path by stripping the manifest's base URL and re-basing it onto the configured one, which is what makes local mirrors and offline tests work, and a second host would have broken that for paid packages only. Every upload plants a canary under the prefix and fails if the public rail serves it.

**Visible and locked, in one manifest.** Gated packages are rows in the same public manifest, with the same release label, changelog and cadence as everything else; their names, descriptions, versions and hashes are public. A picker that hid them would misrepresent what the toolkit is, and a logged-out Check for Updates can still honestly report that two supporter tools have updates.

**A tier is data, and the map is server-side.** In the catalog, `access` names a Patreon tier id. Which tier covers which package is a map in the Worker's configuration, version-controlled with the gate; one script writes the catalog and the map in a single motion, and staging refuses a gated package that no tier grants. The ladder grants upward, so a higher tier holds everything a lower one does, and the creator's own account holds the top rung, which is how the builder walks the paid path before any customer does. A client-side copy of the map would be the second place the answer lives, and that duplication is a failure another toolkit already shipped.

**The broker holds the secret.** Patreon's token exchange requires a client secret and offers no PKCE, and a secret inside a `.tox` is no secret at all. So the Worker is the only holder of the Patreon client secret and of refresh tokens, and TouchDesigner only ever holds an opaque device token that can be revoked. The sign-in flow opens your browser at the gate, which redirects to a loopback listener inside TouchDesigner with a one-time grant code and a nonce; the code is exchanged for the device token in a second request, so a credential never lands in browser history. The token is stored in the operating system's keystore (DPAPI on Windows, the Keychain on macOS), never in a parameter, a `.toe` or the settings file.

**Tokens and lifetimes.** A download needs a second, short-lived token: fifteen minutes, an EdDSA-signed claim carrying the list of products the session is entitled to. The Worker fails closed on a package the claim does not name; the client reads its own claim only to phrase a refusal ("unlocks at the Base tier"), never to decide access. The claim is a product list, because a boolean cannot express partial entitlement, and a competitor's boolean once refused paying supporters their own product for four months. Patreon entitlement is re-checked every six hours: a permanent failure (a revoked grant) clears the tiers, a transient one (an outage) keeps the last answer and retries sooner, and a session unverified for thirty days stops being trusted. A Patreon session lives 180 days and renews itself in use. A Gumroad licence key is a completed purchase: verified once at redemption, never re-checked, never expiring, with its activation counter spent only on a genuine first activation. Sign-out revokes the session at the gate before clearing the local copy, and a replayed revoked token reads as revoked.

**What it does not try to be.** A `.tox` you downloaded is a file you can copy. Gating controls distribution, and the packages you fetched while entitled stay installed and stay yours. Per-user watermarked artifacts were rejected because they would break the one-hash-per-artifact integrity rail to slow a leak they could not stop. Free packages never pass through the Worker; they stay on the CDN with no compute hop in front of them.

The gate went live on 2026-08-29 and the paid path was walked end to end on a customer-shaped install the same day. Seat policy for licence keys, a device list, and showing a key's activation count in the client are on record as open.

## What is deliberately absent, and what is unproven

- Native installers are deferred; the one-drop `.tox` is the rail.
- A pip or uv rail was researched and rejected; the bucket and manifest model won.
- Hash-based update detection was built and reversed; `.tox` export is not reproducible.
- GitHub releases as the update source are gone; the bucket is the single source of truth.
- The requirement list names packages, never versions; a toolkit-version floor is the known gap.
- Config scope is one switch for the whole toolkit; there is no per-tool scope yet.
- The updater's kill switch is enforced by the client; the origin does not yet refuse on a version header.
- The discovery document's third pin, a copy on GitHub, is compiled into the updater, and its repository does not exist yet; the two live pins answer, and the fallback chain tolerates a dead one.
- The updater replacing its own package has never been exercised end to end on a real install; the path is ordered last and bounded, and it is documented as unproven.

## Ideas worth borrowing

- Read the version off the installed component itself.
- Let hashes verify downloads, and let a governed version decide updates.
- Derive dependencies from what a tool hosts; a hand-written list is a list that rots.
- Make the registry the enabler of partial installs: a missing tool is just missing entries.
- Resolve version conflicts silently during a load path and report afterwards.
- Treat the machine-wide store as a mirror, so a stale file is always safe to re-download.
- Pin releases immutably and keep exactly one mutable pointer, shipped uncached.
- Put a discovery document above the manifest, at pinned URLs, with a kill switch and a notices channel.
- Sign the documents, fail closed on a bad signature, and fail open on a missing one during a transition.
- Apply one package at a time, prove each reload happened, and back up before the point of no return.
- Keep the version on a child that the reload rebuilds, so it travels with the artifact.
- Let the project file be the settings store and make roaming an overlay applied once at boot.
- Ship a bootstrap that is the real root with the tools removed, so it cannot drift from what you develop in.
- Announce capabilities with a native tag so a consumer that arrives later still finds them.
- Gate bytes on the server, name the missing tier on the client, and keep the tier map in one place.
- Write the contract down on both sides of a product boundary before either side builds against it.
