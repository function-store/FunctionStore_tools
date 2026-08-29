---
status: open
summary: Six adopted ideas and three closed holes for the public distribution rail — a discovery document with pinned fallbacks, a kill switch, publish-time guards. None of it depends on gating anything.
since: 2026-08-26
skill: fns-packaging
---

# Rail hardening — what we adopt, and in what order

Work plan arising from [DistributionComparison.md](DistributionComparison.md),
which measured our rail against DOTsimulate's shipping LOPs rail. Everything
here improves the **public, un-gated** rail and is worth doing whether or not
[GatedDeliveryResearch.md](GatedDeliveryResearch.md) is ever built.

Three of these close holes that exist in our code today. The rest are ideas
worth taking because someone else already paid for them.

---

## 1. Order of work

Ranked by cost-of-not-having, not by effort.

| # | Item | Size | Why this position |
|---|---|---|---|
| 1 | **Discovery document + pinned fallbacks** | large | The only one that *cannot* be fixed after the fact — a client that cannot find a manifest cannot be told where the new one is |
| 2 | **`minimum_updater` kill switch + `notices`** | small, once §1 exists | Self-update has never been run end-to-end. This is the insurance for that |
| 3 | **`removed` guard in `publish.py`** | hours | Closes a live hole (§3.1) |
| 4 | **Read-back verification in `upload.py`** | hours | Closes a live hole (§3.2) |
| 5 | **A protected set** | rule + a flag | Cheap, prevents a category of irreversible mistake |
| 6 | **Toolkit-version floor on `requires`** | medium | A real expressiveness gap, no incident yet |

Items 3 and 4 are the cheapest and land first in practice; items 1 and 2 are
the ones that matter most.

## 2. The adopted ideas

### 2.1 A discovery document, pinned to several hosts

**The principle, adopted verbatim: change the data, never the file.**

Today `Baseurl` is a single parameter with a single value, and the manifest
that would say where to go is only reachable *through* that value. If
`storage.functionstore.tools` moves, changes hands, or goes down, **every install
in the field is dead until a human edits a parameter** — and we have no way to
tell them to.

The fix is a small JSON that clients read *before* the manifest, reachable at
**two or three URLs compiled into the shipped component and never changed**:

```json
{
  "schema": 1,
  "endpoints": { "manifest": "https://storage.functionstore.tools/fnstools" },
  "minimum_updater": "3.0.0",
  "notices": []
}
```

**Pins decided 2026-08-27 — three names, two independent origins:**

| # | URL | Host | Form |
|---|---|---|---|
| 1 | `storage.functionstore.tools/fnstools/.well-known/fnstools.json` | Cloudflare R2 | the document itself |
| 2 | `functionstore.tools/.well-known/fnstools.json` | Vercel | **200-proxy** to pin 1, via a `vercel.json` rewrite |
| 3 | `raw.githubusercontent.com/…/fnstools.json` | GitHub | static copy, **published by the release step, never by hand** |

Pin 2 is a proxy rather than a copy for the reason below; pin 3 is the only
genuinely independent origin, so it is the one that must never go stale — which
is why publishing it belongs to the release step and not to a human.

**Correction, 2026-08-28 — pin 2 was dead and probed as healthy.** As first
written, pin 2 named the apex `functionstore.xyz`. That hostname belongs to a
*different* Vercel project (the Function Store brand site) and 308-redirects to
`www`, so this repo's `vercel.json` rewrite could never fire there: the pin
returned a plain 404, identical in every observable way to "the document is not
published yet" — which is what it was assumed to be. It was caught only by
probing each pin's host individually while migrating domains, before any of it
shipped. Two rules come out of it, and they generalise past this one bug:

- **A pin names a host the project provably serves.** Pin 2 now sits on
  `functionstore.tools`, the site's own primary domain, so the rewrite is
  served by the same deployment the docs are.
- **No pin ships unverified.** `packaging/check_pins.py` must see every pin
  return the real document before a release goes out. An unverified pin is not
  a fallback, it is a fallback-shaped hole, and the whole point of the list is
  that it still works on the day everything else does not.

The cost, stated plainly: pins 1 and 2 now share a registrable domain, where
before they nominally spanned two. That independence was worth less than it
looked — pin 2 was always a *proxy* to pin 1, never a second origin — and it was
worth nothing at all while broken. Pin 3 remains the genuinely independent one.

Design rules, all of them load-bearing:

- **Pinned forever.** Editing the pin list mints a new generation of the
  component; it does not fix copies already in the field. Treat the list as
  permanent from the first release that ships it.
- **Make the extra pins genuinely independent hosts.** LOPs has three pins but
  two of them share one origin, because pin 1 is a proxy to pin 2 — good for
  migration, no help when that origin is the failure.
- **Prefer a 200-proxy over a hand-copied file** wherever a pin can be one. A
  hand-maintained copy someone forgot to redeploy serves a wrong answer forever
  and looks perfectly healthy. Where a pin *must* be a static copy (a git-raw
  fallback), publish it from the same release step that publishes the bucket —
  never by hand.
- **Cache the last good copy on disk**, so an offline machine gets an answer
  rather than a dead updater — with the caveat in §2.2.
- `Baseurl` stays as the manual override. It is the mirror/`file://` escape
  hatch the whole offline test rail depends on.

**What it buys beyond survival:** moving the bucket, adding a mirror, or
changing hosts becomes a data edit that reaches every install, with no
component update and no user action.

### 2.2 A kill switch, and a channel to the field

`minimum_updater` in the discovery document: an updater below the floor
**refuses to run and says why**. `notices` carries a message every install
sees.

We currently have only the opposite direction — `min_td_build` per package
(from [UpdaterHardening.md](UpdaterHardening.md)), which stops a package
landing on too old a TD. There is **no way to stop a known-bad shipped
updater**, and [Overview.md](Overview.md) §7 records that self-update has never
been executed end-to-end. That combination is the argument.

**Do not repeat their hole**: their floor is checked by the client against
itself, and their offline discovery cache means a killed build with a cached
pre-kill document keeps running — weakest exactly where you want it strongest.
Ours should be enforced **both** ends: the client refuses below-floor, *and*
the updater sends its version as a header so the origin can refuse too. A
cached document may satisfy the client; it cannot satisfy the server.

### 2.3 A protected set

Never overwrite in place: a published release's artifacts, a manifest a
client can already reach, or any `.tox` an install already holds. A fix
reaches a shipped artifact as a **new release**, never by editing the one out
there.

We get most of this by accident — `upload.py:_remoteHas()` skips objects the
bucket already has, and release labels are in the path. But `--force` and
`--prune N` both reach published objects with no ceremony beyond a flag. Make
it a stated rule with a deliberate gate, not an accident of the happy path.

Note we already hold the *inverse* guard, and it was paid for the hard way:
the authored-here guard, which stops an artifact being written over the live
development source (PackagingScheme §5). This is the same instinct pointed
outward.

### 2.4 Content-addressed artifact keys — adopt partially

`objects/<name>/<version>/<sha256>.tox` means two builds of one version cannot
collide. Our release label already sits in the path, so the normal case is
covered; the uncovered case is a **re-publish of the same release**, which
silently overwrites.

Given §2.3 makes re-publishing a release a rule violation anyway, this is
belt-and-braces. Worth taking *if* it is free at staging time, not worth a
migration on its own. **It does not change the update signal** — `.tox` export
is not reproducible (PackagingScheme §6), so a hash still cannot tell a change
from a re-export, and `Pkgversion` remains the only thing that decides newness.

### 2.5 A sealed release plan

Their `batch_release` computes a canonical SHA-256 of the dry-run schedule and
refuses a live save unless it still matches the approved one; any drift in
schedule, versions, or output paths invalidates the approval.

Our Guided Release confirms a plan and then executes it, with nothing binding
the two together. Low priority — our pass is shorter and human-supervised —
but it is the right shape if the release ever becomes less interactive.

### 2.6 A toolkit-version floor

`requires` is a **name list only**: derived from stamped registry hosts, which
is a better mechanism than a hand-written list for saying *which* core
packages — but it cannot say *which version*. A tool that starts depending on
a new `FNS_ConfigRegistry` API has no way to declare it, and an update will be
offered to a base that cannot run it.

Two ways to close it:

- **A floor per package** — `requires_version: {FNS_ConfigRegistry: ">=3.1.0"}`,
  derived where possible, declared where not. Simple, fits the existing
  `Compare()` states (it is another `incompatible`).
- **Immutable compatibility catalogs** — a frozen manifest projection per
  installed core version, so an incompatible update is never even listed. More
  powerful, considerably more machinery, and it is the piece of LOPs that most
  visibly grew a second catalog system it can now never retire (§7 of the
  comparison).

**Recommend the floor.** It answers the same question, costs one field, and
does not fork the manifest.

## 3. The three holes to close in our own code

All verified 2026-08-26. None are hypothetical.

> **ALL THREE LANDED 2026-08-27.** §3.1/§3.2 in `packaging/`
> (`tests/test_publish_guards.py`, 14 checks); §3.3 — the discovery document,
> §2.1 and §2.2 — across `packaging/`, `website/vercel.json` and
> `ExtUpdater.py` (`tests/test_updater_discovery.py`, 23 checks). All suites
> pass, including the pre-existing `test_updater_verify.py`.
>
> **Not yet exercised against a real bucket**: nothing has been published, so
> no client has fetched a real discovery document over the wire. Pin 3's repo
> (`function-store/fnstools-links`) does not exist yet — the URL is pinned in
> the shipped component and will 404 until it is created, which the fallback
> chain handles but which must be fixed before it counts as a third origin.
>
> The `removed` guard earned its place immediately: run against the real
> tree it refuses the next stage on **four packages the 3.0 redesign dropped
> and never declared** — `FNS_Config`, `FNS_MainMenu`, `UPDATER` and
> `tools_ui` (renames into `FNS_ConfigRegistry`, `FNS_MainMenuRegistry`,
> `FNS_Updater`, and dissolution into `FNS_Hub`). They are now declared in
> `packaging/release.json`. Nothing was wrong with the 3.0 release — the
> point is that the drop was invisible, and would have been again.

### 3.1 A package can silently vanish from a release

`publish.py:98-100` computes `bumped` and `added`, and refuses a release that
moves neither. It never computes **`removed`** — and `Stage()` `rmtree`s the
staged tree and rebuilds it wholesale from whatever `build_manifest.py` derived
from the live project.

So a package that is not loaded, or whose `pi_suspect` tracking lapses, or that
the generator simply does not see, disappears from the rolling manifest — and
the guard passes, because other packages bumped. Every install silently stops
being offered it.

This is exactly the LOPs 2026-08-19 incident: their live registry was replaced
by a projection missing one product's row, and every shipped updater for that
product broke for a week.

**Fix**: compute `removed`, refuse unless the removal is explicitly declared
(a flag, or a `retired` list in `release.json`). Their stronger form — patch
one row and assert every other row byte-identical — is the right end state if
the manifest ever stops being regenerated wholesale.

### 3.2 Nothing verifies what actually landed in the bucket

`publish.py` re-hashes what it *staged*, which is right. `upload.py` checks
wrangler's exit code, and checks key existence *before* uploading. **Nothing
re-fetches after upload and compares.** A truncated or half-written object
passes and is discovered by a user.

**Fix**: after upload, re-fetch and compare SHA-256; on mismatch, fail loudly
and print the exact `wrangler r2 object put ... --file <staged>` rollback line.
Pairs naturally with making `_remoteHas()` authenticated, which gated delivery
needs anyway and which is more correct for public objects today — an r2.dev
bot-filter 403 or any CDN hiccup currently answers "not there" and re-uploads.

### 3.3 One URL, no failover, no reach into the field

§2.1 and §2.2 are the fix. Listed here too because it is a present hole, not
only a missing feature.

**As built (2026-08-27):**

| Piece | Where |
|---|---|
| `minimum_updater` / `notices` declared | `packaging/release.json` |
| carried into the manifest | `build_manifest.py:_minimumUpdater/_notices` |
| document built + staged (bucket copy, per-release copy, pin-3 copy) | `publish.py:_discoveryDoc`, `Stage()` |
| `no-cache` policy; `pin3-*` never uploaded; pruned per release | `upload.py` |
| pin 2 as a 200-proxy | `website/vercel.json` |
| pins, fetch, fallback, kill switch | `ExtUpdater.py` (`DISCOVERY_PINS`, `_fetchDiscovery`, `BaseUrl`, `_belowFloor`) |

Four decisions worth keeping when this is revisited:

- **`Usediscovery` is a new toggle, not "empty `Baseurl` means discovery".**
  Custom par values are *preserved* across an in-place update, so every
  existing install already holds a non-empty `Baseurl` and would never have
  opted in. A NEW par lands with its build value on every install — measured,
  [UpdaterHardening.md](UpdaterHardening.md) §1.
- **A local or `file://` `Baseurl` outranks discovery**, so the mirror/offline
  test rail is never re-routed by a network lookup.
- **The document is cached only once it parses** (`fnstools.last.json`). The
  fetch target is overwritten in place, so an error page would otherwise
  destroy the only fallback at exactly the moment it is needed.
- **Discovery got its own stall watchdog.** The existing `_watchdog` only
  watches the `artifacts` stage, and a pin that never opens produces no
  callback at all — so a dead first pin would have wedged every pass before it
  started, which is the precise bug that watchdog exists for.

## 4. What we explicitly do not adopt

- **Their threading model.** Worker threads, deadlines, a main-thread queue
  poll, and a `prime()` step to resolve a `mod()` lookup before a worker
  touches it — all of it exists because a blocking token exchange once ran
  inline in `onHTTPRequest` and froze TD. We fetch through the Web Client DAT
  per `.claude/rules/td-python.md`, so the whole class is unreachable.
  [UpdaterHardening.md](UpdaterHardening.md) §3 already reached this conclusion
  once, declining Embody's certifi machinery for the same reason. **Taking
  their ideas must not drag their threading with it.**
- **A drift gate.** Their §10 exists because baked DAT text and the repo `.py`
  diverge silently. Embody's `syncfile=True` externalization makes the file the
  source, so the window does not open. *(One honest caveat: our portable export
  does inline externalized ext DATs. It inlines from the live synced DAT so it
  should be sound — but nothing asserts it, and their lesson was that a
  spot-check on one filename read 91/91 clean while other files were stale. A
  cheap assertion at export time would close the argument.)*
- **A second catalog system.** See §2.6.
- **Gating the manifest.** Theirs requires a paid tier to read the catalog at
  all. Ours stays public with locked rows — it avoids both their problem and
  the one they had to design around.

## 5. What this changes elsewhere

- [PackagingScheme.md](PackagingScheme.md) §7 gains the three holes as known
  gaps; the scheme itself is unchanged until §2.1 lands, which adds a layer
  *above* `base_url` rather than altering it.
- [GatedDeliveryResearch.md](GatedDeliveryResearch.md) was revised the same day
  for the claim shape, credential storage, and size-then-hash.
- Nothing here touches [ScopeAndPersistence.md](ScopeAndPersistence.md) or the
  reload semantics in [UpdaterHardening.md](UpdaterHardening.md).
