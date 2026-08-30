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

## What YOU maintain (three things)

### 1. `Pkgversion` — the one field that governs updates

A string version (`1.2.0`) the updater compares LIVE off the installed
component against the manifest. Hashes only verify downloads; this par
alone decides "is a newer build available". Bump it whenever the package
changes; forgetting is silent, which is why the release flow auto-bumps
what you select and refuses a release that bumps nothing.

**Preferred shape:** an `FNS_About` child COMP holds the authoritative
`Pkgversion` (plus `Touchbuild` and `Helpurl`), and the tool's own
`Pkgversion` par mirrors it by expression (registries: by bind). The
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
  "category": "Media & Output",
  "description": "One sentence, user-facing, ends with a period."
}
```

Optional keys: `access` (a Patreon tier id — anything but `"free"` makes
the package **gated**: published under the `plus/` prefix, served only
through the entitlement worker), `license`/`seats` (Gumroad lifetime-key
lane), `recommended` (rides the starter set), `placement` (below).
Categories and their glyph/pitch live in the same file under
`categories`/`category_meta`.

**`placement`** — where the installer lands the package. Absent (the
default): a child of the toolkit container, update-tracked in place.
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
curated keys. Stored as presence: only `"placement": "pane"` is ever
written.

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
- **Hotkeys** go through the conformance flow — `/fns-hotkey-conformance`.
- **Quick-launch commands** — `/fns-command-registration`.

## Shipping it

Once the COMP passes the identity test and carries its three maintained
pieces, it appears in the CMS release table on its own. From there:
[RELEASING.md](RELEASING.md) — preflight, Release & stage, upload. Cold
test before claiming victory: drop the artifact in a bare project and walk
the full bootstrap.
