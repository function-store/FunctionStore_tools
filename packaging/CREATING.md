# Creating a package

What a package IS, what it must carry, and what the machinery derives for
you. The step-by-step *release* runbook is [RELEASING.md](RELEASING.md);
the reasoning behind the scheme is
[docs/PackagingScheme.md](../docs/PackagingScheme.md). This page is for
the moment before either: you have a tool and want it to become a
shippable package.

## What makes a package

**A package is a depth-1 COMP in the `/FNSTools` root that Private
Investigator tracks as a suspect with its own tox.** That is the entire
identity test (`build_manifest.Packages()`):

- `family == 'COMP'`, directly under the toolkit root
- `externaltox` set (PI's suspect binding gives you this)
- the `pi_suspect` tag present

Nothing registers a package anywhere. If it passes the test, every release
pass finds it, exports it, hashes it and publishes it; if it stops
passing, `Stage()` refuses the release until the drop is declared in
`release.json` `retired` (packages must never vanish silently).

The two exceptions: `FNS_Installer` and `webBrowser` are **rails** — build
artifacts published under the manifest's `rails` block, never as
installable packages — even though PI tracks them too.

### The other answer: a FOREIGN package (declared, not discovered)

A tool whose bytes and version are owned **upstream** — another repo,
another release rail (TDXMap is the first) — has no live COMP here, so the
identity test above cannot see it. It is declared instead: a catalog entry
with a `source` block (reasoning: `docs/ForeignPackages.md`).

```json
"TDXMap": {
  "category": "Control & mapping",
  "description": "…",
  "placement": "root",
  "source": { "manifest": "https://…/manifest.json", "tox": "TDXMap.tox" },
  "updates": "self",
  "help_url": "https://tdxmap.functionstore.xyz/docs/",
  "min_td_build": "2023.12120"
}
```

The recipe, in order:

1. **Author the entry** in the content CMS package editor (the "Foreign
   package" block) or by hand. `source.manifest` is what makes it foreign.
   The upstream manifest may be flat (`{version|latest, url, sha256,
   notes_url}`) or our own shape (`packages[]`, with `source.package`
   naming the row). It MUST carry a sha256 — unpinned bytes are refused.
2. **Mirror it**: `python packaging/foreign_sync.py TDXMap` (or the row's
   **Sync** button in the CMS release table, which runs the same script
   detached). It downloads the tox into `packaging/dist/`, verifies the
   sha, and pins `{version, sha256, url, notes_url, fetched_at}` in
   `packaging/foreign.lock.json`. **Commit the lock**: it is what the
   manifest build reads, and git then shows which upstream version each
   release mirrored. The sync is the ONLY thing that talks to the upstream;
   `Build()` never does network I/O.
3. **Write the doc** (`packaging/docs/<Name>.md`) like any package.
4. **Release it** like any package: it appears in the CMS release table
   (lock version vs published, mirrored/not), Preflight blocks until it is
   mirrored, and Release & stage ships the mirrored artifact under the
   normal `base_url/<release>/` path. It is never bumped, exported or
   PI-saved — the lock IS its version, the sync IS its export.

What the entry may declare that a live package may not — because a live
package has a live authority for each (`FNS_About.Helpurl`, the export
build) and authority must not fork; Preflight refuses these on a live row:

- `updates`: `self` (the tool runs its own updater after install; the
  toolkit updater reports it as **self-managed** and never touches it —
  no `Pkgversion` needed inside the artifact) or `store` (tracked like a
  tool; then the artifact must carry `Pkgversion`).
- `help_url`, `min_td_build` — declared, since nothing can be reflected.

Retiring a foreign package = removing its catalog entry AND declaring it
in `release.json` `retired`; the CMS row's **Retire** does both. A foreign
package is not a *recommendation* (`packaging/recommendations.json`): that
lane LINKS to other creators' pages and never hosts or versions anything.
Foreign means we mirror the bytes and poll a source to keep them current.

### Getting a new tool INTO PI — per operator, never per project

The identity test above says PI's suspect binding sets `externaltox`. Two
things about that were paid for on 2026-09-01:

**PI owns tool externalization, not Embody.** `externalizations.tsv` had 15
rows and no tool extension in it; PI's `suspects` table had 468. Embody derives
an externalized path from the op path, so `externalize_op` on a tool DAT lands
in `FNSTools/…` — the tree retired in backlog item 13. Use PI:

```python
pi = op('/private_investigator1').ext.PrivateInvestigator
pi.Add(comp)                    # tags it, creates Vcoriginal, sets externaltox, one suspects row
pi.Add(comp.op('MyToolExt'))    # file/syncfile -> modules/suspects/..., Info Header stamped once
pi.Save(comp)                   # writes the suspect tox (and re-exports the root toolkit tox)
```

Then check the DAT's row landed in `suspects` — on first use `Add(dat)` set the
file binding but its row was missing; append the path if so, which is the only
half `Add` does after Init. PI's `Save` writes `externaltox` with a backslash;
normalize to forward slashes to match every sibling.

**Never pulse `Scan` or `Updatesuspects` to adopt one COMP.** `Scan` only sees
COMPs that already carry `Vcoriginal`, so a fresh COMP is invisible to it; and
`Updatesuspects` re-exports every suspect tox on the main thread — 60+ of them,
long enough to wedge TD and need a restart.

## What YOU maintain (three things)

### 1. `Pkgversion` — the one field that governs updates

A string version (`1.2.0`) the updater compares LIVE off the installed
component against the manifest. Hashes only verify downloads; this par
alone decides "is a newer build available". Bump it whenever the package
changes; forgetting is silent, which is why the release flow auto-bumps
what you select and refuses a release that bumps nothing.

**Preferred shape:** an `FNS_About` child COMP holds the authoritative
`Pkgversion` (plus `Touchbuild` and `Helpurl`), and the tool's own
`Pkgversion` par mirrors it by expression, read-only, on its About page --
registries too (measured live 2026-09-02: every master mirrors by
`op('./FNS_About').par.Pkgversion`; an earlier "registries: by bind" here
described a ported copy, not the masters). **Expression, never bind, is a
rule here, not taste**: a bind is two-way, so code that sets the mirror
writes THROUGH to `FNS_About` and silently rewrites the authority it was
meant to read -- `readOnly` stops the UI, not Python -- whereas an
expression is one-way, so a stray write breaks the mirror locally and
leaves the source of truth intact. "The child owns it" (a computed
readout: status, progress, a bound port) points at bind; "the child is
AUTHORITATIVE for it" points at expression, and `Pkgversion` is the
second kind (credit: the launcher's agent, 2026-09-02, after switching
its utility to the expression mirror). The
version lives on a child so it travels INSIDE the artifact through an
update reload (`docs/UpdaterHardening.md` §4 — the reload that rebuilt
children shipped stale versions fleet-wide when the par lived elsewhere).

**Supported minimum:** a bare `Pkgversion` custom par on the COMP itself,
no `FNS_About` at all. The whole rail honors it — the release bump writes
it (`release_one._versionWritePar` falls back to it), the manifest reads
it, the updater compares it, and the CMS release row shows it. What you
give up without `FNS_About`:

- **`Touchbuild`** — the minimum TD build stamp that travels inside the
  tox; without it the manifest falls back to the build that did the
  export (usually fine, occasionally too strict).
- **`Helpurl`** — the one per-package docs override; without it the docs
  link derives from the package name.

Start with the bare par if `FNS_About` is friction; grow the child when
the package needs a build floor or a docs override.

**Who wins on a mismatch: `FNS_About`, always.** Bumps write the child,
and every reader in the rail — the manifest build, the release bump's own
read, the updater compare, the CMS row — reads the child FIRST, falling
back to the comp par only when there is no child (the bare-`Pkgversion`
shape). The comp-level par is a display mirror (expression on tools, bind
on registries), never the truth, so severing the mirror cannot invert
authority. A severed mirror is still a release-blocking defect
(`version mirror severed` in preflight): the stale constant shows on the
parameter page, exports INSIDE the artifact, and feeds any comp-first
reader still shipped in the field. The usual cause is an assignment to
`.val`, which silently flips the par to constant mode — never hand-edit
the comp-level par on a package that has `FNS_About`; edit the child, or
use the release flow's bump.

### 2. A `catalog.json` entry — how the picker presents it

```json
"MyTool": {
  "category": "Visual",
  "description": "One sentence, user-facing, ends with a period."
}
```

Optional keys: `access` (a Patreon tier id — anything but `"free"` makes
the package **gated**: published under the `plus/` prefix, served only
through the entitlement worker), `license`/`seats` (Gumroad lifetime-key
lane), `recommended` (rides the starter set), `placement`, `nopick` and
`placeonce` (below),
`author {name, url}` / `homepage` / `changelog_url` (presentation links —
the manifest carries them to the picker byline and the website badge;
this is the ONE home for credit, and a doc still carrying a frontmatter
`credit` block fails the site build), and for foreign entries only
`source` / `updates` / `help_url` / `min_td_build` (above).
Categories and their glyph/pitch live in the same file under
`categories`/`category_meta`.

**`placement`** — where the installer lands the package. Absent (the
default): a child of the toolkit container, update-tracked in place.

`"placement": "root"` lands it at the **network root, beside the toolkit
container** — for tools that must live at `/` rather than inside the
container. The address is known, so it behaves like a toolkit tool
otherwise: presence is the live comp, updates apply in place (the
updater's doorstep walk), and unselecting removes it for real.

`"placement": "pane"` declares a **reusable component** — something you
use in normal TouchDesigner work rather than a toolkit tool — and the
installer spawns it into the network the user is working in (the current
network editor pane's owner; the toolkit container is the fallback when
no editor is open or the visible network is protected). The trade, by
design (palette-component semantics):

- "installed" is the **install record** on the toolkit root, not a live
  child — the picker pre-checks it from the record, and unselecting it
  later only clears the record (spawned copies are the user's work and
  are never touched). One exception — the installer's doorstep: a spawn
  sitting in the toolkit container itself, or right beside it at the
  network root (where the no-editor fallback and a `/`-showing pane both
  land), is removed like any tool; copies elsewhere in the network are
  never.
- instances are **frozen at their spawn version** — the updater reports
  the package as `component`, never updates it in place; the newest
  version arrives by reinstalling from the picker. The doorstep applies
  here too: a spawn in the toolkit container or beside it at the network
  root compares and updates in place like any tool.

Set it in the CMS package editor ("Installs into"), like the other
curated keys. Stored as presence: only `"pane"` or `"root"` is ever
written.

**`nopick`** — `"nopick": true` makes a package **explicit-pick only**.
It is still a real package: a normal card in the picker and on the site,
installable and updatable. But no bulk selection ever includes it — not
Select all, not the Everything preset, not Recommended (so it cannot also
be `recommended`; preflight refuses the pair), not a curated bundle in
`presets` (the build drops it and reports it), not the guided-setup
questionnaire. It arrives only when someone ticks its card, and nothing
removes a tick they made; a "Set up like last time" restore keeps it only
because nothing bulk could have put it in that setup. Meant for
hardware-specific integrations and anything else that must never land
because someone asked for everything. Set it in the CMS package editor
("Explicit pick only"). Presence-style: `true` or absent, any other value
is a preflight problem, and only `true` is ever written to the manifest.

**`placeonce`** — `"placeonce": true` gives the package's picker card a
second action beside the tick: **place in this project only**. A placed
tool lands and updates like any other, but its install record says
`remember = 0`, so "Set up like last time" never brings it into the next
project; ticking still makes it part of the setup. An FNS family member is
spawned into the working network when placed. Meant for tools someone wants
in one project rather than in every project (TDXMap, ParHoverMIDI_VSN1).
An FNS family member gets the Place button without the flag.
Set it in the CMS package editor ("Can be placed without joining the setup"). Presence-style like
`nopick`. Reasoning and the data it touches: docs/PlaceOnce.md.

**`preview`** — `"preview": true` ships the package in the release for the
owner's own testing and hides it from everyone else: only the creator's
signed-in account can see or install it, and the site, the picker, the
questionnaire, the bundles and the new-tools notice leave it out. `access`
stays the tier it will ship at. Set and clear it with the CMS checkbox
("Preview: not released yet") or `python packaging/gate_package.py <Name>
--preview` / `--release`, never by hand: it also rewrites the Worker's
grants, so `wrangler deploy` follows. It overrides Recommended: the flag is
kept for the release, and the starter set leaves the tool out until then.
Reasoning and limits: docs/PreviewPackages.md.

### 3. A user-facing doc — `packaging/docs/MyTool.md`

The site build (`npm run pages` in `website/`) **hard-fails** on a
catalogued package with no doc, a doc with no catalog entry, or a doc
whose frontmatter `package:` does not match its filename. A package ships
with its doc or nothing ships. This is deliberate.

## What is DERIVED — do not declare it

- **Dependencies.** Tools depend only on CORE, never on each other.
  Registry masters live in core; your tool ships stamped registry
  *hosts*, and its `requires` is derived from exactly the registries it
  hosts. (Stamping a host: load `/fns-registry` first.)
- **Surfaces** (toolbar, hub, op menu…), **integrations**
  (`integrates_with` degrades gracefully by design — never a hard
  dependency), **op counts**, **artifact hashes and URLs**.
- **Launcher reach** — the manifest's `launcher` block
  (`{surfaces, capabilities, seedable}`, where `seedable` is NESTED
  inside it: `p.launcher.seedable`, never `p.seedable`), derived by
  reflecting over your commands.
  A package earns it by declaring a `surface` token other than `quick`,
  or a `capability`, on any command — see `/fns-command-registration`.
  **Having commands is not enough**: nearly every tool has quick-launch
  commands, and a launcher's bundler needs the few that reach a surface
  beyond it. Absent means "commands only", which is the normal answer.

- **FNS family membership** — the manifest's `family` block, derived from
  the tool's own `FamManifest` (TDFam's manifest base: `OpInfo`, `ParRetain`,
  `StateRetain`, `Shortcuts` DATs of JSON). Add or edit it from the content
  CMS package form, which writes the tool and PI-saves it. `op_type` must be
  a lowercase word (TDFam looks it up verbatim in a lowercased cache, so a
  type with capitals places and never comes back from a stub); `op_name`
  keeps the readable spelling. A member is placed into the working network,
  so it implies `placement: pane`. Only a foreign package curates `family`
  in the catalog. See [docs/OperatorFamilyFromStore.md](../docs/OperatorFamilyFromStore.md).

- **A companion** (catalog `companion: family`) is infrastructure that exists
  only for other packages: the picker never offers it and the installer
  adds it exactly when the selection holds a package that needs it. The FNS
  operator family is the one today. Curate it in `catalog.json`; it is not a
  dependency, since the members work without it.

If you find yourself wanting to hand-declare any of these, the design is
telling you the tool is shaped wrong — usually a tool-to-tool dependency
trying to exist.

## House rules the package must live by

- **No absolute operator paths, anywhere** — parameter values included
  (`.claude/rules/td-python.md`). The package must survive rename,
  relocation and instancing.
- **Settings persist through ConfigRegistry**, scoped correctly — load
  `/fns-config-scope` before making anything persist.
- **Copies of a suspect-bound master must sever `externaltox`**
  (`enableexternaltox=False`, `externaltox=''`, strip `pi_suspect`) or
  boot reloads the wrong tox into them.
  Released artifacts are handled for you: `build_manifest.ExportPackage`
  scrubs the written tox of `pi_suspect`, `FNS_externalized` and
  `Vcoriginal` (`ScrubArtifact`, on the artifact, never the live master).
  Hand stamp recipes inside the project still sever them themselves.
- **Hotkeys** go through the conformance flow — `/fns-hotkey-conformance`.
- **Quick-launch commands** — `/fns-command-registration`.

## Shipping it

Once the COMP passes the identity test and carries its three maintained
pieces, it appears in the CMS release table on its own. From there:
[RELEASING.md](RELEASING.md) — preflight, Release & stage, upload. Cold
test before claiming victory: drop the artifact in a bare project and walk
the full bootstrap.

## Every package needs a `pre_release` hook

A package without one ships the authoring apparatus: the `Version Ctrl` page
and the `vc_data` tables that describe THIS checkout's save history rather
than the tool, plus it misses the loopback web-server rule, the
console-ships-dormant rule, the `FNS_About.Owner` expression and the
first-page rule. Nothing warns you -- which is exactly how four packages
shipped without one until 2026-09-18, all of them created by following this
document while it said nothing about hooks.

Create a Text DAT named `pre_release` as a DIRECT child of the package,
file-synced to `modules/suspects/FNSTools/<Package>/pre_release.py`, tagged
`pi_suspect`. Its first line is the generic strip:

```python
exec(open('packaging/pre_release_common.py').read())
```

Anything package-specific goes BELOW that line, never above it. The hook runs
on a STAGED COPY in `/sys/quiet` with extensions not initialized, so it does
direct par/table edits only and never touches the live component.

Check it landed by exporting and reading the artifact back: no `Version Ctrl`
page, no `vc_data` children.
