---
status: research
summary: Whether the updater should become the 11th registry, so tools carry their own update capability and hand it to a /sys global when one exists. Research only — nothing here is built.
since: 2026-08-26
skill: fns-packaging
---

# The updater as a registry

Research into turning `ExtUpdater` from a package that *scans the toolkit* into
a registry that *tools publish into* — so a tool can ship, install and update
itself without the toolkit around it.

Nothing here is built. Read §3 first: the delegation this question describes is
already written, which changes what the work actually is.

---

## 1. What the updater is today (measured)

Probed live on TD 2025.33070, `/FNSTools/FNS_Updater`:

| Fact | Value |
|---|---|
| Package size | **195 ops**, 169 KB tox |
| Its own payload | ~60 ops — of which **45 are `fileDownloader`**, a clone of `/sys/TDTox/fileDownloader` |
| The rest | shared furniture every tool already carries: `ExtUtils` (45), `FNS_ConfigRegistry` host (35), `FNS_ToolbarRegistry` host (33), `FNS_About` (10), `wiki` (13) |
| Logic | one DAT, `ExtUpdater.py`, 1295 lines |
| Discovery | `Compare()` walks `self._root().children` and matches names against one manifest index |
| Source | ONE `Baseurl` par, ONE `manifest.json`, ONE store folder |
| Install record | ONE `installed` table on the toolkit root |
| Concurrency | one `self._job` at a time |
| Self-update | special-cased: a detached script string that may reference nothing inside the package |

Two facts from `packaging/manifest.json` that matter more than they look:

- **`FNS_Updater` is `core` but appears in no package's `requires`.** No tool
  declares it needs the updater, because no tool talks to it — the updater
  finds tools, never the other way around. `build_manifest.py` documents why it
  is core anyway: *"leaving it optional means the one package that can fetch
  updates is the one a user can accidentally decline."* That is a workaround for
  the absence of a bootstrap path, not a design.
- **49 of 61 depth-1 COMPs in `/FNSTools` carry `Pkgversion`** (the 12 without
  are annotations, the logger, docsHelpers and the installer rail). Every
  shippable package already declares what it is, on itself, live.

`/sys/TDTox/fileDownloader` is **TD's own** (44 ops, no tags, no `externaltox`)
— present in every TouchDesigner install. Nothing has to ship a downloader to
have one.

## 2. What actually blocks standalone shipping

Less than the framing suggests. Two things, and only two:

1. **Discovery is containment-based.** A package is "a depth-1 COMP of
   `Target`". A tool dropped into `/project1`, nested inside another tool, or
   living in someone else's toolkit is invisible to `Compare()` — not refused,
   not reported, simply absent. **Answered 2026-08-27 — a release-time tag,
   see §5.1.** It is a one-off cost at release and it removes containment from
   the question entirely.
2. **The source is one URL on one package.** A tool from a different publisher
   (or a different bucket, or a gated prefix) has nowhere to say where it comes
   from. `Baseurl` is a property of the *updater*, not of the *package*.

Everything else already travels with the tool: its version (`FNS_About.Pkgversion`,
49/49), its registry hosts (which guard themselves and vanish quietly where a
registry is absent), its settings (ConfigRegistry, keyed by canonical name), and
the refusal logic that protects an authored source checkout — which reads
`project.folder` and `externalizations.tsv`, not the toolkit.

## 3. Does it fit the registry pattern?

Structurally, yes — and three things fall out of the pattern for free, on top of
the standalone shipping that is the point of the exercise.

**The hand-over already exists.** `RegistryBase._registryApi()` is exactly
"sense a `/sys` global and delegate":

```python
def _registryApi(self):
    if self._is_sys_global():
        return self
    global_reg = self._global_registry()
    if global_reg and global_reg.valid and global_reg.extensionsReady:
        if hasattr(global_reg.ext, self.EXT_NAME):
            return getattr(global_reg.ext, self.EXT_NAME)
    return self
```

Ten registries run on it in production. `ExtUpdater` subclassing `RegistryBase`
gets the described behaviour by writing `api = self._registryApi()` at the top
of each public method — it is not new machinery.

**Newest-wins promotion solves version skew for free.** A tool published in 2027
and dropped into a project running a 2025 toolkit promotes *its* updater into
`/sys`, and every other tool's update then runs on the newer code. Today a stale
`FNS_Updater` is stale for everything in the project. (It never prompts —
`RegistryHomeContract` C5, and the modal in that path already cost a wedged cold
boot once.)

**The `/sys` copy is not the package, which dissolves the self-update hack.**
Promotion is `sys_comp.copy(master)`, and the global stays uncloned and
disposable. A global updater replacing the `FNS_Updater` package is not standing
on the branch it is sawing — no `_SELF_UPDATE` script string, no "treat a
failure here as re-drop the tox by hand". This is the single biggest code
simplification on offer.

**Where it does not fit.** Every existing registry manages a *surface TD owns*
and publishes contributions onto it. There is no TD surface here. `FNS_Config`
already broke that (its "surface" is a file), so this would be the second
**service registry** — entries are *facts about packages*, not contributions to
a UI. That is a real widening of the scheme and `RegistryScheme.md` should name
the category rather than let it arrive by accident.

## 4. The shape: every tool carries it, the global takes over when present

The goal is a tool that ships alone, installs alone and **updates alone**, and
that costs nothing extra when it happens to sit inside the toolkit. So the
capability travels with the tool. The thing to avoid is not "the updater is in
every tox" — it is **fifty independently-authored copies of the apply path**.
Those are separable, and the split falls out of what a lone tool actually needs.

### 4.1 The standalone path already exists, and it is small

A tool updating itself is not a small version of the toolkit pass. It is
`_selfUpdate` — the rail already written for "replace the package this extension
lives in", from a detached script that may reference nothing inside the package.
Everything the toolkit pass carries beyond that exists because it updates *up to
fifty other* packages:

| Machinery | Needed by a lone tool? |
|---|---|
| fetch manifest, `Compare` one version, download, verify sha256 | **yes** |
| `min_td_build` floor, backup before destroy, reload-token verification | **yes** — these are the hazards, not the bulk |
| `_selfUpdate` / `_rewriteBound` (one package) | **yes** |
| `_drain` one-package-per-frame, `_settleStaleErrors`, `_report` over N results | no |
| store-wide `RefreshStore`, the `installed` audit table, changelog prompt | no |
| `ConfigRegistry.SaveAll()` before the pass | no (its own section survives a `reloadcustom = off` reload in place) |
| entitlement / auth for gated artifacts | **no — deliberately global-only** (§7) |

So the per-tool half is roughly "fetch, compare, verify, replace myself", and
the global half is "do that for N packages, in order, with a report".

### 4.2 One source, many instances — not fifty forks

The drift objection is real but it is a *sourcing* problem, and this codebase
already solved it: `scripts/shared/RegistryBase.py` is ONE file behind **83
DATs**, file-bound with `syncfile` in dev and embedded at release. The updater
gets the same treatment. Fifty instances of one source is not fifty
implementations — and three things bound the exposure that bit the registry
family before:

- **With the toolkit present the tool's copy never runs at all** — `_registryApi()`
  hands every call to the promoted global (§3), so the fleet's normal path is
  one live implementation, the newest one in the project.
- **Standalone, a stale copy can only mis-update its own tool** — not the other
  49. The blast radius is one package, and the user asked for it explicitly.
- **It heals itself**: the update that lands also lands the newer updater code,
  because it is inside the tox being replaced.

What does NOT get vendored is the downloader. `/sys/TDTox/fileDownloader` is
TD's own (§1) — create or clone it on demand instead of carrying 45 ops in every
tox. That is the difference between ~60 ops per tool and ~15.

**Cost per tool**: ~15 ops and ~50-60 KB of embedded text, against a 66 KB
median tox. Not free — worth saying out loud — and the single biggest lever on
it is how much of `ExtUpdater.py` the per-tool branch actually needs (§4.1
suggests well under half).

### 4.3 What "detached from the toolkit" then means

| Situation | What happens |
|---|---|
| Tool alone in a bare project | its own copy fetches its `Pkgsource` manifest, compares its own `Pkgversion`, replaces itself |
| Tool alone, no network | reports; nothing else changes |
| Tool inside the toolkit | `_registryApi()` delegates; the global updates it as one package in a batch |
| Tool inside SOMEONE ELSE'S toolkit carrying a newer updater | that newer global wins promotion and drives it (§3) |
| Gated/paid tool, standalone | reports "update available — needs FNS_Updater" rather than carrying a credential (§7) |

## 5. Registration is a declaration, not a stamped host

The cheapest registration is the one that already exists: **`Pkgversion` on
`FNS_About` is the registration**. Add one curated par — `Pkgsource`, the
manifest base URL — and a tool is registrable with no host, no extension, and no
cooking.

Precedent is in the family already: ConfigRegistry's **`FNS_persist` tag** —
registration without a host, for micro-tools too small to carry one. The same
sweep rules should apply: never on a timer (finding a tag means walking the
project, and this toolkit runs inside live shows), only in the boot window and
before a save.

Three things this buys over stamping a host into 50 tools:

- **Cook-disabled tools become updatable.** A host must cook to compile its
  extension; midiMapper cannot host today and is skipped by ConfigRegistry for
  that reason. A declared par needs nothing.
- **No derived dependency.** `build_manifest.py` derives `requires` from hosted
  registries, so an updater *host* would add `FNS_Updater` to all ~50 packages'
  `requires` — writing the coupling we are trying to remove into the manifest.
  A declaration adds nothing.
- **Nothing to stamp, so nothing to re-stamp.** No fleet pass, no clone
  expressions, no `pre_release` scrub for a new host type.

### 5.1 The tag is the discovery mechanism — decided 2026-08-27

**Every released package carries an `FNS_package` tag.** Discovery becomes
`findChildren(tags=['FNS_package'])` from the project root instead of walking
`Target.children`, which closes §2's first blocker outright.

**It is a one-off cost, not a per-release one.** Because tags survive into the
artifact and back through a reload (below), one fleet pass over the ~49 live
packages puts the tag in every tox permanently — nothing stamps it again. What
the release regime needs is therefore an **assertion, not a step**: a new
package with no tag should be refused (or warned) where `build_manifest.py`
already tests `pi_suspect` at `:109`, so the one case that can regress —
someone adding a package and forgetting — is caught at the same place package
identity is already decided. No existing release tooling touches tags today
(`pre_release_common.py` only scrubs), so this is additive.

Keep the split clear: **the tag is the index, the pars are the data.** The tag
makes a package cheap to *find*; `Pkgversion` and `Pkgsource` say what it is
and where it updates from.

**Two tags already exist, and both inform this.**

- **`pi_suspect` is already on every shipped package**, and
  `build_manifest.py:109` already uses it as half of package identity —
  `p.eval() and 'pi_suspect' in c.tags`. It is Private Investigator's tag with
  PI's semantics, covering things that are not packages
  ([PackagingScheme.md](PackagingScheme.md) §5 says so explicitly), so it is a
  fine co-signal and the wrong thing to key on. **But it settles the question
  that matters**: §5 also records that `pi_suspect` *survives into the shipped
  artifacts*, and it is sitting on packages that have been through updates.
  **Tags survive an in-place update.** They ride in the tox, and
  `reloadcustom`/`reloadbuiltin` govern parameters, not COMP properties. There
  is nothing here to measure.
- **`FNS_persist` is the working precedent** — ConfigRegistry's
  registration-by-tag for tools too small to carry a host
  (`ConfigRegistryExt.PERSIST_TAG`). Its docstring is already the spec: *"The
  tag IS the registration."*

**Sweep rules, inherited from `FNS_persist` rather than reinvented:**

- **Never on a timer.** A tag sweep is a whole-tree walk and this toolkit runs
  inside live shows. `FNS_persist` runs in the bounded boot window and at every
  `SaveAll`; the updater adds "on user pulse", which is rare and
  user-initiated.
- **No `depth` argument, ever.** TD's `findChildren` depth is an EXACT depth,
  not a maximum — `depth=99` returns an empty list, so a project-wide sweep
  written with it reports zero hits and looks like a clean result. Already cost
  three "nothing found" searches once
  (`.claude/rules/td-python.md`); the `FNS_persist` sweep carries the warning
  inline for the same reason.
- **A real registration beats a tag** where both exist, as with `FNS_persist`.

**One guard, and it is one line:** a tagged COMP that has a tagged *ancestor*
is not an independent package — it is vendored inside another package's tox,
and updating it would both edit a package behind its back and be discarded the
next time that package reloads. `findChildren` will not do this natively;
filter the result by "no tagged ancestor". No current case is known to exercise
it; the guard is cheap enough not to wait for one.

**Two non-problems, recorded so they are not re-raised.** Copies inheriting the
tag is fine — finding two copies of a tool and updating *both* is correct, and
the canonical-name collision belongs to ConfigRegistry, which already answers
it. And tag survival is settled above.

**What the tag unlocks**, beyond the standalone case that motivated it: a tool
in `/project1`, a tool nested inside another COMP, a tool inside someone else's
toolkit, and — with §5's declaration model — cook-disabled tools like
midiMapper, which cannot host a registry because a host must cook to compile
its extension.

### 5.2 TDAsyncIO as the orchestration layer — measured 2026-08-26

Offered by DOTsimulate with permission to reuse (provenance and cautions in
[GatedDeliveryResearch.md](GatedDeliveryResearch.md) §5b). Worth recording
because the obvious reading of it is wrong in both directions.

**It is NOT a threading layer.** `execute1.onFrameEnd` calls `Update()`, which
does `loop.run_until_complete(asyncio.sleep(0))` — one cooperative tick on the
**main thread**. No `threading`, no `Thread`, no `run_in_executor`, no
`call_soon_threadsafe` in the whole 20 KB. So it does not violate
`.claude/rules/td-python.md`, and coroutines under it may touch TD objects —
genuinely unlike LOPs' `auth_manager` worker threads.

**But the loop does not make a blocking call non-blocking.** It ships no HTTP
client of its own; only asyncio-native awaits yield. Our own deleted
`github_remote/githubRemote.py` is the proof — `import requests` /
`requests.get(url)` wrapped in TDAsyncIO, blocking the frame on every GitHub
poll despite the machinery around it.

**The client decides, and that splits by audience.** Measured in TD 2025.33070:
`httpx` and `anyio` import (the project `.venv` is on `sys.path`), `aiohttp`
does not, and TD's bundled Python has only `requests`.

| Path | Works in a bare user project? |
|---|---|
| TDAsyncIO + `httpx.AsyncClient` | **no** — needs a venv the user does not have |
| TDAsyncIO + `asyncio.open_connection` + stdlib `ssl` | yes, hand-rolled |
| Web Client DAT (today) | yes — ships with TD |

`httpx` is in that venv only because Envoy's MCP stack pulled it in
(`mcp` → `httpx2`, `starlette`, `uvicorn`), with **no manifest recording it**
— so it is an accident of the dev environment, not a dependency anyone chose.

**Conclusion for a per-tool updater**: the transport stays the Web Client DAT,
which is the only option that is both non-blocking and present on every
machine. TDAsyncIO's value is **orchestration** — timeouts, cancellation,
completion callbacks, a status table — against the hand-rolled `_job` /
`_later` / `_pump` / `_watchdog` state machine, and that value is independent
of the transport underneath.

**One cost to gate before adopting**: `onFrameEnd` runs `Update()` every frame
including a task-table DAT write, with zero tasks pending. That is exactly the
always-on per-frame cost the Navbar cook-diet work exists to remove, in a
toolkit that runs inside live shows. Gate the Execute DAT on "tasks exist".

**Weigh it against not adopting.** The state machine it would replace was
hardened as recently as [UpdaterHardening.md](UpdaterHardening.md), and the
discovery stage added to it on 2026-08-27 fitted the existing `_later`/`_pump`
idiom without strain. Reach for TDAsyncIO on NEW async work, not to rewrite a
loop that now has measured behaviour.

## 6. What has to change inside `ExtUpdater`

1. **Discovery**: `Compare()` iterates registry entries (`{name, comp path,
   version, source}`) instead of `root.children`. `_root()`/`Target` survives
   only as the default install destination.
2. **Sources**: one `Baseurl` becomes N per-entry sources, with one manifest
   fetched and cached per distinct source. `_artifactRel()` already re-bases
   everything onto the *configured* base rather than the manifest's own, which
   is what makes the `file://` and mirror rails work — that logic becomes
   per-source rather than global.
3. **The install record has nowhere obvious to live, and both obvious answers
   are wrong.** Since `reloadcustom = off` landed, a preserved custom par keeps
   its OLD value through an update ([UpdaterHardening.md](UpdaterHardening.md)
   §4 — the same trap that moved the version onto `FNS_About`), so an
   `Installedsha` par on the tool would lie after every pass. And a table
   *inside* the package is destroyed and rebuilt by the reload. So the record
   must be written **outside the package, after the reload lands** — by the
   global, into project state it owns, or into the store. Worth remembering that
   the audit table answers exactly one question `Compare()` cannot ("installed
   but now missing"), which is meaningless for a standalone tool: it can degrade
   rather than be ported.
4. **`_isSelf` / `_selfUpdate`**: mostly deleted (§3).
5. **`_refuseReason` / `_isAuthoredHere`**: unchanged. Both read `project.folder`
   and `externalizations.tsv` and work identically from `/sys`.

## 7. New risks the registry model introduces

- **Multi-source trust is the big one.** Today the fetch URL is one par on one
  package the user installed deliberately. In a registry, any COMP in the
  project could register a source and have the *shared, trusted* updater fetch
  and install a `.tox` from it. That is a meaningful escalation, and it needs a
  visible source list, per-source consent on first use, and no automatic update
  from a source the user has not accepted. Do not build the fan-out before this.
- **Gated delivery depends on the chokepoint staying single.**
  [GatedDeliveryResearch.md](GatedDeliveryResearch.md) is cheap on the TD side
  precisely because *"there is exactly ONE place in TouchDesigner that touches
  the network"*. Shapes A and C preserve that; shape B destroys it — fifty
  downloaders means fifty places a device token would have to live, in tools
  that ship to everyone. Auth belongs only in the global; a standalone tool
  without it should report "update available — needs FNS_Updater", not carry a
  credential.
- **Serialization improves, but only under delegation.** One global job is
  strictly better than N tools each running a pass into the same store; N
  fallbacks racing on one store folder is a state the current code has never
  been in.
- **`/sys` is per-process.** Nothing durable may live on the global
  ([RegistryHomeContract.md](RegistryHomeContract.md) C5) — which is the same
  constraint §6.3 hits from the other side.

## 8. What is NOT verified

- **A Web Client DAT running under `/sys` is unverified.** The Web *Server* DAT
  is proven there — `ConfigRegistryExt._ensureSettingsServer()` creates one
  inside the promoted global and the settings page is reachable — and `/sys`
  and `/sys/FNS_Registries` both have `allowCooking = True`. But nothing has
  fetched over the network from `/sys` yet, and the whole delegation shape rests
  on it. **First spike, before anything else.**
- Whether promoting a COMP that carries a clone-bound `fileDownloader` copies
  cleanly (the clone target is TD's own `/sys/TDTox/fileDownloader`, so it
  should resolve from anywhere — but "should" is not "measured").
- Whether a running `/sys` global keeps working while its own master package is
  destroyed and reloaded underneath it. Expected yes (the copy is independent
  and uncloned), unmeasured.
- **`_selfUpdate` has never been live-verified** — its own docstring says so, because on a dev checkout the updater package is `externaltox`-bound and therefore refused, and a scratch target can never be the package that is actually running. §4.1 puts that rail on the critical path for every standalone tool, so it stops being an acceptable gap: it needs a real test project with an embedded, unrefused copy.
- No live experiment was run for any of this. It is code reading plus the
  measurements in §1.

## 9. Rough effort

| Piece | Estimate |
|---|---|
| Spike: prove a fetch works from a `/sys` copy | half a day, and it gates everything |
| Split `ExtUpdater.py` into the per-tool core and the global-only batch layer (§4.1) | ~1 day |
| `ExtUpdater` → `RegistryBase` subclass, delegation on every public method | ~1 day |
| Entry model + declaration sweep (`Pkgversion` + `Pkgsource`, `FNS_package` tag) | ~1 day |
| Per-source manifests, cache, install-record relocation (§6.3) | ~1–2 days |
| Source trust/consent surface (§7) | ~1 day |
| Verify `_selfUpdate` for real (§8) + fleet rollout of the shared source | ~1 day |
| Live verification: standalone tool in a bare project, mixed-version promotion, a real multi-package pass | ~1 day |

**≈1.5 weeks**, and it overlaps the gated-delivery work rather than competing
with it: both want the same single chokepoint and the same per-package metadata.

## 10. Decisions needed before any of this is built

1. Where exactly the per-tool / global-only line falls in `ExtUpdater.py` (§4.1)
   — this is the one decision the rest hangs off.
2. ~~Declaration or stamped host?~~ **DECIDED 2026-08-27: declaration, found by
   an `FNS_package` tag — §5.1.** Naming is the only thing still open
   (`FNS_package` matches `FNS_persist`; `FNSTool` was the original proposal).
3. Does the toolkit root keep the `installed` audit table, or does the live
   `Pkgversion` become the whole truth? (§6.3)
4. What is the trust model for a source a tool declares — allowlist, per-source
   consent, or "same origin as an already-trusted package"? (§7)
5. Does `FNS_Updater` stay `core` once every tool can update itself, or become
   optional again? (`build_manifest.CORE`'s stated reason for including it —
   "the one package that can fetch updates is the one a user can accidentally
   decline" — stops being true.)
6. Does a standalone tool get an update UI of its own, or only a pulse + a
   status par? A tool alone has no hub tab and no console to report into.
