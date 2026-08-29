---
status: in-force
summary: The packaging and update scheme in one page -- buckets and manifests, Pkgversion as the governed version, derived dependencies, and the traps already paid for.
since: 2026-08-13 (consolidated from three sessions)
skill: fns-packaging
---

# Packaging and the update scheme

> Graduated 2026-08-22 from `briefs/2026-08-13-packaging-handover.md`, which was
> gitignored despite being scheme-of-record ("nothing above section 6 is
> historical --- it is current"). One claim was corrected on the way in; the rest
> is as written. The step-by-step runbook is
> [packaging/RELEASING.md](../packaging/RELEASING.md); the distribution model and
> its history are in [ConfiguratorDistribution.md](ConfiguratorDistribution.md).

Consolidated 2026-08-13 after three sessions. **This describes the scheme
as it now stands.** Earlier revisions of this file described two update
models that were built and then reversed; §6 keeps the closed paths so
nobody re-treads them, but nothing above §6 is historical — it is current.

---

## 1. The scheme in one page

Distribution is **buckets and manifests**. The one-drop `FNSTools.tox`
bootstrapper is the install rail, and there is no GitHub-based update flow.
(This section originally named native `.exe`/`.dmg` installers as the
bootstrap; that was **reversed** on 2026-08-21 --- see
[NativeInstallerDecision.md](NativeInstallerDecision.md). Nothing else in the
scheme depended on it.) The bucket is the
single source of truth for what exists; `base_url` says where to fetch.

Four questions, four different answers — keeping them separate is the
whole design:

| Question | Answered by |
|---|---|
| What packages exist, and what do they need? | `manifest.json`, derived from the live project |
| Is a newer build available? | **`Pkgversion`** — a custom par we govern, on every package |
| Where do I fetch it? | the manifest's pinned per-release `url` |
| Did the download arrive intact? | **`sha256`** — integrity, and nothing else |

**`Pkgversion` is read LIVE off the installed component**, not from a
record of what was installed. That is the only thing that works for a
package embedded in a `.toe`: there is no file to hash and no artifact to
consult, but the component still declares what it is. It also means no
side table can drift out of truth — the component *is* the truth.

**Dependencies are DERIVED, never declared.** Registry masters live in
core and tools ship stamped *hosts*, so a package's `requires` is exactly
the core packages owning the registries it hosts. Every tool needs
`FNS_Config`; a toolbar button also needs `FNS_Toolbar`. Nothing
hand-maintains it, so it cannot drift. Package identity = a depth-1 COMP
that is a tracked `pi_suspect` with its own tox.

**The one hand-maintained field is `Pkgversion`.** Bump it whenever you
change a package. Forgetting is silent — no install learns anything is
new — so `publish.py` refuses to stage a *new release* that bumps nothing
and reports what did move. It cannot catch forgetting one package among
several; nothing can, without a content fingerprint (see §6).

## 2. The three motions

| Pulse | Cost | Does |
|---|---|---|
| **Refresh Store** | whole store | fetch manifest + every artifact whose bytes differ → `<palette>/FNStools_ext/store/`. Machine-wide; touches no project |
| **Check for Updates** | one small JSON | fetch the manifest only, then compare. Asking "anything new?" must not cost 6 MB |
| **Update This Project** | only what differs | fetch just the packages this project needs, then apply them |

`Compare()` is the single decision point and reports:
`update` · `current` · `unversioned` (declares no version — shown, never
touched) · `locked` (newer, but this copy must not be written) · `missing`
(recorded installed, component gone).

**An update pass is not an install pass** — a package the user never chose
stays uninstalled.

Applying runs **one package per frame** (`_drain`): each replacement
reinitialises extensions, so batching them into one frame is both a long
main-thread block and the crash-prone case.

## 3. Where package files live

Chosen on the installer (**Package Files**). The updater tracks **no
mode** — it follows whatever binding each package actually has, so there
is nothing to drift:

| Mode | Files | Update path |
|---|---|---|
| `embedded` (default) | inside the `.toe` | `replaceOp` from the store artifact |
| `shared` | bound to the palette store | rewrite + reload (often just a reload) |
| `project` | `<project>/FNStools/` or **Package Folder** | rewrite + reload |

**A bound package updates by rewriting its file and reloading** — no
copy/destroy of an extension-bearing COMP, no docked-op juggling, and the
change is a file the user can version-control.

`project` is what delivers isolated local component state: each project
owns its copies, so one can hold a modified package without touching any
other install. `shared` knowingly reintroduces machine-wide coupling — a
store refresh reaches every project sharing it — because some users want
exactly that. It is not the default.

**Settings are safe by construction**, not by care: they live in
`<palette>/FNStools_ext/config/FNStools_config.json`, never in a `.tox`,
and `RegisterTool(autoload=True)` re-applies each tool's section when its
host re-registers after a reload. `SaveAll()` still runs before any pass.

## 4. What is verified — and the one gap

Verified live this session:

- **Store refresh, local/file path** — 39 artifacts staged, all hashes verified.
- **Store refresh, real HTTP** (`python -m http.server` over `packaging/publish/`) — 39/39 fetched and verified, 0 failed, 41 GETs in the server log.
- **Full project pull** on a cooking-disabled `/sys/quiet/trial` — installed embedded (nothing on disk), component declared `1.0.0`; bumped the source to `1.1.0`, re-exported, re-staged, refreshed; `Compare` reported exactly that one `update`; the pass applied it; the component then declared `1.1.0` at 123 ops, no errors; re-check reported none.
- **Rewrite-in-place** — wrote deliberately DIFFERENT bytes over a bound `.tox` and confirmed the live COMP reloaded to match (123 → 96 ops, the donor's children), then a full pass restored it.
- **Version ordering** — unit-checked on 10 cases including `1.9` vs `1.10`, which string comparison gets wrong.
- **Guards** — live authored packages refuse; the scratch copy is allowed.
- **Shipped `dist/UPDATER.tox`** loads clean: extensions ready, no errors, `externaltox` empty, `updates` DAT present.
- Live canary after all of it: Toolbar **37** / Navbar **13** / MainMenu **12** / Config **44**, unchanged. (OpMenu/PaneType use accessors I did not find — unverified this session, previously 3 / 2.)

**NOT verified — self-update.** UPDATER updating its own package destroys
the DAT running the loop, so it is ordered LAST and executed from a
detached `run()` string (literals only, owned by TDResources' queue). It
cannot be exercised here: on a source checkout UPDATER is refused by the
authored-here guard, and a scratch target can never be the package that is
actually running. Structurally correct, failure bounded — every other
package has landed by then, worst case is re-dropping the tox by hand —
but treat it as unproven until a real bucket install hits it.

## 5. Traps already paid for — do not rediscover

**The vendored TDFileDownloader** (three separate ways to fail silently):

- **A request issued from inside the Web Client DAT's own callback is silently dropped** — the file lands, the next GET never goes out. Its own `queueNext()` re-issues from exactly there, so the internal queue is unusable too: every post-download stage is deferred a frame (`_later`) and the queue is driven by `_pump`.
- **A stale `stateDict` entry poisons every later request for that file** (keyed url+location; an entry left in `GET`/`WAIT` makes `Download()` return the stale state instead of fetching). Every job starts with `AbortAll()`.
- **A connection that never opens produces NO callback at all** — no success, no abort, just a request sitting in `GET` forever. Hence the 45 s stall watchdog.

**Artifacts and identity:**

- **`.tox` export is NOT reproducible.** One untouched component exported three times: 66198 / 66190 / 66150 bytes, three hashes, diverging at byte 9 — the container header, before any content.
- **`pi_suspect` survives into the shipped artifacts — it is NOT a dev marker.** Neither is `externaltox` a sufficient one. What identifies an authored component is: this project is the source checkout (the packaging generator sits beside it) AND the component lives in the container that generator exports from.
- Artifact URLs in the manifest are pinned to the real bucket, so fetching them verbatim ignores `Baseurl` and dials a host that does not exist yet. Artifacts resolve **relative to the configured base**.
- The portable export **inlines externalized ext DATs and clears the ROOT comp's `externaltox`**, but `file` pars and NESTED `externaltox` survive.

**TouchDesigner mechanics:**

- **Install/update tests MUST target a cooking-disabled container** (`allowCooking = False` BEFORE loading). A live copy of a registry master otherwise promotes itself to the `/sys` global and destroys the running one. `/sys/quiet` is the right staging home.
- `COMP.loadTox()` loads the component INTO the given COMP — it creates the child itself. Pre-creating a container named after the package nests it a level too deep (`AutoRes/AutoRes`).
- **A pulse's effect reads STALE in the same `execute_python` that fired it**, and a COMP reloaded by pulsing its external-tox reload does not report its new state in that call either — results settle on the next tick.
- A fresh `tableDAT` already holds one empty row, so `numRows == 0` is the wrong test for "needs a header".
- Copy+destroy of extension-bearing COMPs is crash-prone: one tool per `execute_python`, ending with `comp.save(externaltox)` in the SAME call.
- Before renaming/destroying a COMP containing stamped registry hosts, grep `externalizations.tsv` for rows under its path — Embody's move detection has re-matched orphaned rows to a different clone and deleted the master `.py` ~20 clones sync from.
- `parameterexecuteDAT`'s pulse toggle is `onpulse`, not `pulse`.
- `inspect.getsource()` on a TD builtin WEDGES the main thread. A responsive Envoy is not proof the main thread is alive — `result = 1+1` is the cheap disambiguator.

**Paid for the hard way:** an artifact was written over the live `AutoRes`,
silently stripping its Embody bindings. Restored from
`modules/suspects/.../AutoRes.tox`, `enableexternaltox`/`externaltox`
re-set by hand, nested `kindergaertner_mymod` reloaded to get back to 123
ops. The authored-here guard exists because of this.

## 6. Paths already closed

Do not re-propose these without new information:

- **Artifact hashes as the update signal** — built, then reversed. `.tox` export is not reproducible, so every release marks every package updated.
- **`vc_data` / the `Vc*` pars** as the version source — rejected on ownership: it is Private Investigator's table, written by tooling outside this repo. Also thin: 1 of 39 had a real version, 1 had no table, and `build` did not move across two project saves.
- **A TDN content fingerprint** — rejected on ownership: TDN is an external package. Worth noting it IS technically sound (two exports of one component differ by exactly one line, `exported_at`, out of 2280), so if that constraint ever changes, this is the mechanism.
- **Refusing every `externaltox`-bound package** — too blunt; a binding is the *better* update path, not a reason to refuse.
- **Per-package palette toxes as the only model** — now available as `shared`, but not the default: it mutates every project on the machine.
- **In-project `replaceOp` only** — now `embedded`, the default; it was never wrong, just insufficient alone.
- **GitHub releases / `Gittag` polling** — dead under buckets+manifests. `github_remote`, `TDAsyncIO`, `PollLatestTag()` and `par.Filename` are deleted.

## 7. What is left

> **Three holes found 2026-08-26** by comparison against a shipping rail
> ([DistributionComparison.md](DistributionComparison.md)); the work plan is
> [RailHardening.md](RailHardening.md). All present in the code today:
> `publish.py` computes `bumped`/`added` but never **`removed`**, so a package
> can silently vanish from a release and the bump guard still passes;
> `upload.py` never re-fetches after upload, so a truncated object is
> discovered by a user; and `Baseurl` is a single value with no fallback and no
> way to reach the field, so a moved bucket strands every install. The last one
> cannot be repaired after the fact.

- Swap `BASE_URL` in `build_manifest.py` and the `Baseurl` par default when the bucket is real. **Nothing else changes** — both rails were built and verified against a local tree precisely so this is a one-constant swap. Assume public-read; a token must never ship inside a distributed tox.
- Set `Cache-Control` on the rolling `manifest.json` at upload time. A CDN-cached root manifest would silently pin users to an old release; deliberately not worked around client-side.
- Exercise self-update once against a real bucket install (§4).
- **`OpTemplates` does not ship self-contained** — its `OPTemplates1` child is an external tox in the user palette, so a fresh install gets an empty template library. Embed it or have the installer fetch it.
- `catalog.json` descriptions were seeded by inspection and need an owner pass — they drive the picker.
- `QuickCollapse/popDialog/PopDialogExt.py` still carries the `recreateall` + init-mutation lines fixed in `f616b09` for CustomParTools. Same latent class, not reported broken.
- Six `OpTemplates` render templates pin TD's own `Samples/Geo` by version.

## 8. Where things live

```
packaging/build_manifest.py   derives manifest.json from the LIVE project
packaging/catalog.json        curated: category + description only
packaging/release.json        release label + channel (NOT from git)
packaging/manifest.json       39 packages, 7 core, versions + hashes + urls
packaging/InstallerExt.py     the single install implementation
packaging/install.py          thin script wrapper over InstallerExt
packaging/build_installer.py  builds dist/FNS_Installer.tox from source
packaging/publish.py          stages the bucket tree, re-hashes, guards bumps
packaging/configurator/       picker + single-file standalone build
packaging/dist/               39 .tox + FNS_Installer.tox (gitignored)
packaging/publish/            staged bucket tree (gitignored)
```

The updater is `UPDATER/ExtUpdater.py`, mirrored at
`scripts/UPDATER/ExtUpdater.py` (the DAT syncs from the `modules/suspects`
copy; keep both in step).

**Branch `packaging`, LOCAL ONLY — nothing pushed.** Update commits:
`079515e` (store refresh + project pull) → `c78e8fa` (bound packages
rewrite in place) → `d746cd4` (governed versions replace hashes).

`docs/ConfiguratorDistribution.md` is the design record and is current —
§4.2 carries the update model including the reversal and its evidence.
`docs/UvPackagingResearch.md` is research only, not the plan.

## 9. Release checklist

```python
# 1. bump Pkgversion on every package you changed (Package page)
# 2. rebuild + re-export those artifacts
exec(open('packaging/build_manifest.py').read()); Build(export=['ChangedPkg'])
# 3. set the release label in packaging/release.json, then stage
exec(open('packaging/publish.py').read()); result = Stage()
#    -> refuses a new release that bumps nothing; reports `bumped` / `added`
```

```bash
aws s3 sync packaging/publish/ s3://<bucket>/fnstools/ --delete
```
