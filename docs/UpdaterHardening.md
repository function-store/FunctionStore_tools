---
status: in-force
summary: 'Measured semantics of an in-place external-tox reload, the two apply-path holes it closed, and why most of Embody''s updater port turned out to be unnecessary.'
since: 09cbc80 2026-08-26 (branch dev25-updater-hardening)
verified: 2026-08-26 — reload semantics probed live on TD 2025.33070 (5 tox generations); flip verified on one real package; state machine unit-tested; a real multi-package update pass is NOT yet run
skill: fns-packaging
---

# Updater hardening

Started as a port of the learnings in Embody's `UpdaterExt` (its self-updater,
GitHub-releases based) into `ExtUpdater` (ours, R2-bucket based). Most of the
port turned out to be unnecessary, and the reason is one measurement: **TD's
in-place external-tox reload already does what Embody re-implements by hand.**

## 1. The measurement (this is the load-bearing part)

Probed live on **TD 2025.33070**, five tox generations through one COMP, each
reload an `enableexternaltoxpulse` on a COMP whose `externaltox` was re-pointed.

| With `reloadcustom = OFF`, `reloadbuiltin = OFF` | Result |
|---|---|
| custom par the user EDITED | **value preserved** |
| custom par the user NEVER touched, whose build value changed | **old value preserved** — the build value does NOT land |
| custom par NEW in this build | **lands**, with the build's value |
| custom par RETIRED in this build | **removed automatically** |
| custom PAGE | survives; no page loss observed |
| built-in par the build set away from its TD default | **not applied** — stays as it was |
| children | **fully rebuilt** from the artifact (ids all renewed) |
| `externaltox` binding, node position | survive |

Flipping one flag changes exactly one row:

| `reloadcustom = OFF`, **`reloadbuiltin = ON`** | Result |
|---|---|
| custom pars | **unchanged from above** — user settings still safe |
| built-in pars | **now take the build's values** |
| `externaltox`, node position, children | unchanged from above |

### What follows from it

- **The par set reconciles itself.** New pars arrive, retired pars leave, and
  values survive for anything present in both. Nothing has to declare a par
  inventory and nothing has to destroy pars.
- **`reloadcustom = OFF` + `reloadbuiltin = ON` is the split we want**: custom
  pars are user settings and are preserved; built-in pars are component wiring
  the build owns and are re-taken. TD does this natively.
- **A preserved value is preserved even when the user never set it.** This is
  the one real casualty: a version stamped on the tool's own custom par reads
  the OLD version after an update. See §4.

## 2. What landed

Both are apply-path holes that could report success while the user lost
something.

**Backup before the point of no return.** `_replacePackage` (the embedded
rail) did `destroy()` then `loadTox()`. An older TD loading a newer-build tox
returns nothing *silently*, so "artifact loaded nothing" is reachable — and it
left the package gone, reported as a row in a table. The live COMP is now
exported first and restored on either failure path. A backup that cannot be
written **refuses** the replace: without one the destroy is unrecoverable, and
an unwritable store is a real signal, not a reason to gamble. Backups live one
deep per package in `<store>/_backup/`, so a failed replace is recoverable by
hand even after TD closes. The bound rail never destroys and is untouched.

**Prove the reload happened.** `_rewriteBound` returned `ok: True` on the pulse
itself, so a pulse that quietly did nothing was indistinguishable from one that
worked and the user could be told they are on a version they are not running.
It now records the child ids (§1: a reload renews all of them) and
`_settleVerifications` judges the renewal on the next tick. A no-op gets **one
extra tick** before being called a failure — a reload that has not landed yet
and one that never will look identical on the first look — and `_drain` waits
for that retry rather than finishing the pass, or the last package's check
would never run.

**A TD-build floor.** `build_manifest.py` now stamps each package entry with
`min_td_build` (the build it was exported from), and `Compare()` reports a
package whose floor is above the running build as **`incompatible`** — a new
state, reported and never updated. This is the same silent failure the backup
catches after the fact, caught before the download instead. The comparison
refuses only on a *known* incompatibility: a missing, malformed or unparseable
floor never blocks an update, or a changed build-string shape would strand
every install at once.

Fixing that turned up a live bug: **`build_manifest.py` was recording
`'td_build': app.version`, and `app.version` is `"099"`** — the version
*series*, not the build. `app.build` is `"2025.33070"`. Every manifest
published before 2026-08-26 carries `"099"` in `toolkit.td_build`; the floor
comparison treats it as unparseable and ignores it, which is the correct
behaviour for old manifests and is covered by a test.

`tests/test_updater_verify.py` exercises both outside TD (TD builtins
stubbed): the verification state machine — real reload, no-op, slow reload
landing on the retry, childless COMP, vanished COMP, errors after reload,
untouched non-bound results, and that every path clears its pending flag
within two ticks so the added drain loop terminates — and the build floor,
including that the legacy `"099"` value never causes a false refusal.
9 scenarios, 34 checks.

Three docstrings were also corrected — the module header and class docstring
still described the sha256-decides-newer scheme that was tried and reversed,
and `_rewriteBound` asserted "user data lives in the palette JSON, not in the
.tox", which holds only for `reloadcustom = ON` packages and only under global
config scope.

## 3. What was dropped from the Embody port, and why

| Embody mechanism | Verdict here |
|---|---|
| `_pruneRetiredPars` + manifest `custom_pars` | **Not needed.** TD removes retired pars itself (§1). This is also Embody's most dangerous mechanism — it destroyed users' sequence blocks twice, because `Par.destroy()` on a sequential par destroys the whole block and renumbers the survivors. Do not port it. |
| `_applyBuildOwnedPars` + manifest `builtin_pars` | **Not needed.** `reloadbuiltin = True` does it natively (§1). |
| `_verified_tls_context()` (certifi) | **Not applicable.** Embody fetches with a urllib worker, and macOS's bundled Python has no default CA path — every HTTPS call from TD failed there. Ours goes through the palette `fileDownloader`, which is a clone of `/sys/TDTox/fileDownloader` and transfers via the **Web Client DAT**; its only `urllib` import is `urlparse`. Python's `ssl` module is never involved. We already follow the house rule (native TD I/O operators for any fetch); Embody's worker is the deviation that needed certifi. |
| The GitHub API layer (`apiLatestUrl`, 302 asset redirects, mandatory User-Agent) | **Not needed.** A static R2 bucket is one GET of a known URL. Strictly less surface. |
| `_stampAboutPars` | **Not adopted as-is** — stamping the version from the manifest is what forces a reload-token check, and gets it wrong by making `par.Version` lie. See §4. |
| Sentinel + rollback across a reload | **Shape does not transfer.** Embody updates one COMP and can afford a sentinel that survives its own reload. We update up to 50 packages a pass, and our reload does not destroy the extension driving it. The backup/restore in §2 is the equivalent at our granularity. |

What DID transfer: the reload token, the backup-before-destroy discipline, and
the failure policy (quiet on CHECK — nobody wants a dialog every launch because
the bucket blipped; loud on INSTALL — once the live component is being touched,
silence leaves the user on a half-broken install).

## 4. `reloadcustom = off` — LANDED 2026-08-26

> **DONE** (`c67c0f4`). `reloadcustom` 40 → 0, `reloadbuiltin` 3 → 49, all 49
> toxes saved, 0 errors. User settings now survive an update in place on every
> package, and the ConfigScope updater gate below is dissolved rather than
> worked around: that handoff existed only to restore what `reloadcustom` wiped.
>
> **`reloadbuiltin` stays ON deliberately.** Every non-default built-in across
> the fleet is build-owned identity, not a user setting:
> `ext0object`/`ext0promote` on 45 packages, `ext0name` on 19 (the extension
> wiring), `opshortcut` on 30, `parentshortcut` on 26, `initextonstart` on 13.
> With it off, a version that adds an extension or changes its shortcut would
> silently never take effect on an existing install — the same hole Embody
> covered with a manifest `builtin_pars` list. TD does it natively.
>
> **Verified before flipping**, on a real package: `AutoRes` with the new flags,
> reloaded from its own tox. A custom string par set to a value the tox does not
> contain came back unchanged, while `opshortcut` and the extension wiring held,
> children rebuilt, the version still resolved through `FNS_About`, and no
> errors appeared.
>
> **A trap in testing this**: the first attempt used `Active`, a Toggle, and
> wrote a string to it. The value coerced on assignment, so the par read `True`
> before and after and the test proved nothing in either direction. Use a `Str`
> par whose value genuinely differs from the artifact.
>
> **The exposure was bigger than "project scope".** This was framed throughout
> as a project-scope problem, because under global scope the config file would
> restore what the reload wiped. That reasoning assumes the tool HAS a config
> host. **Twelve do not** — every registry plus `FNS_Console`, `FNS_ConfigHost`,
> `FNS_HubRegistry`, `FNS_TimelineTools`
> ([ScopeAndPersistence.md](ScopeAndPersistence.md) §7b) — and six of those were
> in the `reloadcustom = True` group. For them an update reset every custom par
> with **no restore path in either scope**: every registry's `Menuorder`,
> `Callback` and `Autoregister` went back to the artifact's values on each
> update, in a global-scope install as much as a project-scoped one. The flip
> closes that too.

### How this interacts with the config layer

Checked live 2026-08-26; no conflicts, and one structural protection worth
knowing about.

- **The version cannot be clobbered by a stale config section.** All 49
  `Pkgversion` pars sit on the `About` page, and `About` is in ConfigRegistry's
  `SKIP_PAGES`, so the config layer never snapshots or applies them. This is
  load-bearing rather than incidental: `_snapshotPars` records par MODE and
  EXPR, so without the exclusion an old section could restore `Pkgversion` as a
  CONSTANT and detach the mirror — the same failure `_versionWritePar` guards
  against in `release_one`, arriving by a second route. **If the version ever
  moves off the About page, it needs an explicit `Excludepars` instead.**
- The only tool par that IS snapshotted and looks version-shaped,
  `TDX_SearchPalette.Version` (`op('./Help').par.Version`, a display string), is
  already covered by that package's `Excludepars`.
- **An update does not trigger a config re-apply.** `_queueApply` early-returns
  on `_applied_this_session`, so a tool re-registering after its reload keeps
  the values the reload preserved instead of having a pre-update snapshot
  applied over them.
- **Under global scope the JSON still wins at boot**, so preservation is
  belt-and-braces there. Under project scope it is the entire mechanism.

Hatches actually in use across the fleet: `Excludepars` on three packages
(`OUTPUT`, `ResetPLS1`, `TDX_SearchPalette`); `Autoload` off, `Persistpars` off
and `Excludepages` on none.

### The original problem, for the record

The fleet split today is **41 of 50 packages with `reloadcustom = True`**, which
resets every custom par on update. Those tools depend on ConfigRegistry
re-applying their section — and under `Configscope = project` the config file is
never read or written ([ConfigScope.md](ConfigScope.md),
[ScopeAndPersistence.md](ScopeAndPersistence.md)), so for those 41 there is
nothing to restore from and the settings are simply lost. That is the worst
remaining exposure in the update path.

§1 says the flip is safe on every count except one: **a custom `Pkgversion` on
the tool would keep its old value after the update**, because preserved means
preserved whether or not the user ever touched it. So the version must not live
on a preserved par.

[ProjectStateAcrossUpdates.md](ProjectStateAcrossUpdates.md) already proposes
the fix — hold the real version on an `FNS_Manifest` child, which the reload
rebuilds like any child, and leave a visible About-page `Pkgversion` as an
expression referencing it. **The probe confirms that proposal is both necessary
and sufficient**, and it removes the reasoning the proposal was resting on:
`reloadcustom` is *not* protecting the par's existence (TD reconciles existence
by itself), it is only protecting the version VALUE.

### Remaining plan

Nothing. Steps 1-6 landed; the version lives on `FNS_About`
(see below) and the flags are flipped. What is left is verification,
not work -- see §5.

### Where the version lives: `FNS_About` — LANDED 2026-08-26

> **DONE.** All six steps landed (`106c42d`, `62793bf`, `73b774a`, `aa8a540`).
> 49/49 packages carry `FNS_About`; every version traces to
> `FNS_About.Pkgversion`; 0 errors; all 49 toxes re-exported. The only thing
> still owed for `reloadcustom = off` is flipping the flag itself and an
> end-to-end update pass (§5).
>
> **What changed against the plan, and why:**
>
> - **Slimming could not be a local edit.** `FNS_About/ExtUtils` clones a master
>   shared by 84 instances, so deletions there get recreated by the next sync.
>   The clone is now SEVERED per instance before anything is deleted — which
>   also drops a cross-package dependency, since `FNS_About` no longer needs
>   `CustomParTools` present to resolve a master. Module updates still
>   propagate: `CustomParHelper` is a file-synced DAT on the unchanged shared
>   `.py`; only structure stopped propagating, and the six-op set is frozen.
>   The master and the other 84 clones were not touched.
> - **No `ExtUtilsLite` master was needed** — severing per instance achieves the
>   same thing without a second master to maintain.
> - **`extStubser` (19 of the 46 ops) was droppable** despite `CustomParHelper`
>   binding it at class scope: it is guarded by `STUBS_ENABLED`, `enable_stubs`
>   defaults False, and `ExtFnsAbout` does not pass it. The load-bearing set is
>   six: `CustomParHelper` plus the four executes `Init()` activates
>   unconditionally, plus `extParameter`.
> - **Measured: 1966 → 409 ops** across 41 existing instances, and the 22 new
>   ones cost 220 instead of 1078. All 63 `ExtUtils` are now structurally
>   identical.
> - **An earlier warning is retracted**: this could not have tripped Embody's
>   move-detection. `externalizations.tsv` tracks only the MASTER's
>   `FNSCommand` and `extutils_distributor`; the clones are PI-tracked.
> - **A latent bug surfaced on the first copy.** The source's `Authorname` and
>   `Openauthor` were BIND-ed to `parent.AutoRes.par.X` — a hardcoded parent
>   shortcut, which resolves in place and breaks the instant the component is
>   copied. All instances are now on portable `parent().par.X`, or frozen to a
>   CONSTANT of the same value where the parent has no such par. **Clearing
>   `bindExpr` is required, not just switching mode** — a stale expression keeps
>   evaluating and keeps erroring — and the resulting error flags are stale
>   until a reinit, so same-frame verification lies here.
> - **The 16 BIND-mode packages** (the registries and three others) were
>   resolved without touching the bind: the tool's own `Version` par became the
>   expression to the child, so `Pkgversion` follows through the bind it already
>   had. One par changed per package, and registry promotion keeps reading a
>   correct `Version`.
> - **The floor moved onto the component**: `FNS_About.Touchbuild`, read-only,
>   stamped with `app.build`. It now travels inside the `.tox`, so an installer
>   handed a raw artifact can refuse an incompatible build with no manifest at
>   all. `build_manifest` reads it and falls back to `app.build`.

Surveyed live 2026-08-26 across the 49 installed packages.

`FNS_About` is already the right thing and mostly already there:

- It is a child `baseCOMP`, so a reload rebuilds it and its pars follow the
  artifact — the entire requirement.
- **27 of 49 carry it, and every one already has an empty `Version` par**;
  7 also carry `Build`, `Date` and `Touchbuild` — the same quartet Embody's
  `_stampAboutPars` writes. Nothing reads `Version` today, so adopting it
  needs no data migration and conflicts with nothing.
- Packaging already treats `FNS_About` as the metadata source:
  `build_manifest._helpUrl` reads its `Helpurl` **before** the tool's own
  pars. Making it the version source continues an existing design instead of
  introducing a parallel one.

**The contract: the version lives on child `FNS_About`, par `Version`.** One
rule, one reader, and `Pkgversion` on the tool becomes
`op('./FNS_About').par.Version`.

Costs, none of them hidden:

- **The 22 without it are almost exactly the core** — every `*Registry`, plus
  `FNS_Console`, `FNS_Hub`, `FNS_CommandKit`, `FNS_ConfigHost`,
  `FNS_HotkeyManager`, `FNS_TimelineTools` — and the legacy tools
  (`QuickMarks`, `midiMapper`, `oscMapper`, `MISC`, `OUTPUT`, `HydroHomie`,
  `paste_from_clipboard`, `TDX_SearchPalette`). So the pass is "deploy
  `FNS_About` to 22", not "add a par to 49".
- **`FNS_About` is not featherweight**: `ExtFnsAbout`, an `ExtUtils` subtree,
  an `execute1` and a LICENSE. Adding that to fourteen registry COMPs is a
  real weight decision given the cook-diet work. OPEN: full `FNS_About`
  everywhere (uniform About/help/license) versus a minimal carrier for the
  core. Leaning uniform unless op count on the registries is a live concern.
- **They are not clones** (`clone` is None on all 27), so nothing propagates
  for free; each package needs its own copy. `Deploy` / `Deployoncreate` pars
  exist and should be checked before hand-rolling a copier.
- **`FNS_PaneTypeRegistry` holds `Pkgversion` in BIND mode**, alone among the
  49. The migration must treat it separately — an expression cannot simply be
  written over a bound par.

### Not on the list

Manifest `custom_pars` / `builtin_pars` and any consumer-side par
reconciliation (§3). If a future change does add manifest fields that drive
destruction, the consumer must re-validate their types before acting: our
manifest is a mutable, unhashed object in a bucket, and Embody's own comment
records what a `custom_pars` arriving as a *string* does — it `set()`-iterates
into single characters, every real par reads as undeclared, and the prune
destroys every setting on the component.

## 5. Verified, and still owed

**Verified live** (TD 2025.33070, the running dev project):

- The reload semantics table in §1, across five tox generations.
- `_backupPackage` → `destroy()` → `_restorePackage` on a throwaway package:
  the component comes back with its custom par VALUE, its child's content, its
  position and its colour. This is the exact sequence a failed replace runs.
- `Compare()` after the changes: 41 rows, no errors, no behaviour change on a
  fleet that is entirely current.
- The extension reinitialises clean on hot-sync (`get_op_errors` recursive: 0/0).

**Still owed:**

- **An end-to-end `UpdateProject()` pass has not been run.** The pieces are
  verified individually, but no real pass has exercised the backup, the token
  check and the drain loop together against an actual store. The cheap way to
  do it without a bucket: `Baseurl` accepts a `file://` path or a bare
  directory (`_localBase`), and `publish.py` already lays `packaging/publish/`
  out exactly like the bucket, so a local publish tree exercises the real code
  path rather than a mock.
- The `incompatible` state has never been hit live — no package currently has
  a floor above the running build. It is unit-tested only.
- **The flip is verified on ONE package, not on a real update.** `AutoRes` with
  `reloadcustom = off` / `reloadbuiltin = on`, reloaded from its own tox,
  preserved a custom string par while build-owned built-ins held. What has not
  been exercised is the flip under an actual version change across the fleet —
  particularly a package whose new version RETIRES a par (§1 says TD prunes it,
  but that was measured on a scratch COMP, not on a shipped package with an
  extension reading that par).
- Whether `reloadbuiltin = True` clobbers any built-in a *user* legitimately
  sets on a package COMP. Position, colour and `externaltox` survive (§1); the
  rest are component wiring, but the fleet flip should spot-check a package
  that carries a Window or Panel built-in.
