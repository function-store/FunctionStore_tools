---
status: research
summary: FNSTools' distribution rail compared against DOTsimulate's shipping LOPs rail — what converges, what they have that we lack, and three unguarded holes the comparison exposed in our own code.
since: 2026-08-26
skill: fns-packaging
---

# Ours vs LOPs: two TouchDesigner distribution rails

Compared against **"LOPs Distribution — full architecture map"** (DOTsimulate,
2026-08-26), a map of a *shipping, gated* TouchDesigner distribution system.

Why it is worth the read: LOPs is an independent implementation of almost
exactly the architecture [GatedDeliveryResearch.md](GatedDeliveryResearch.md)
proposed from first principles a few hours earlier — Patreon → a backend that
mints a claim → a Cloudflare Worker in front of a private R2 bucket → a client
inside TD that never decides access. **They built it, shipped it, and broke it
in production several times.** Their scar tissue is the cheapest available
information about our own plan.

Their doc points at files for every claim. Ours below points at ours.

---

## 1. Where the two designs converge

Independently, and closely enough to treat the research as validated:

| Both do this |
|---|
| Bucket is the source of truth; a JSON catalog describes what exists |
| The client **never decides access** — it only reads the claim to name what is missing |
| A Cloudflare Worker with a bucket binding is the only reader of the private objects |
| Release-pinned artifacts are immutable; the rolling pointer is the one mutable thing |
| Loopback OAuth: a Web Server DAT inside TD catches the callback, `webbrowser.open` for the real browser |
| A **content receipt** (`sha256`, and for them `size_bytes` too) gates whether bytes may be installed |
| No secret ships in the `.tox` — the broker holds it |
| Gate the bytes, not the UI |

Two details worth copying verbatim because they are more careful than what I
wrote:

- **They check size, then hash** (`verify_content()`), and the Worker also
  compares the *actual R2 object size* against the catalog's `size_bytes`
  before serving. We check hash only, and only client-side.
- **Fail-open on unreadable claims, fail-closed on unknown products.** A client
  that cannot parse its entitlement lets the user through rather than inventing
  a lockout the backend never decided; a catalog row with no product annotation
  is gated as the paid product, not left open. That asymmetry is right and my
  research doc does not state it.

## 2. What they have that we do not

Ranked by what it would cost us to be without it.

### 2.1 A discovery document, pinned to three hosts — the big one

Every LOPs client has exactly **three URLs** compiled into it, at three
different companies (Netlify, Cloudflare, GitHub raw), and *nothing else*.
Everything else — which endpoints exist, what version is newest, which builds
may still run, what message reaches every install — is JSON in a bucket.
**"Change the data, never the file."**

We have `Baseurl`, one par, one value, and the manifest that would tell us
where to go is only reachable *through* that value. If
`storage.functionstore.tools` moves, changes hands, or goes down, **every install
in the field is dead until a human edits a parameter.** PackagingScheme §7
treats the bucket URL as a one-constant swap at build time; it is not a
one-constant swap in the field.

Their pin 1 is a **200-proxy** to pin 2, not a hand-maintained copy — so the
fallback only ever fires for a dead host, never for stale content. A
hand-copied pin that someone forgot to redeploy would serve a wrong `latest`
forever and look perfectly healthy. That detail is the whole reason the design
works, and it cost them: an `@sveltejs/adapter-netlify` quirk (it throws if
`netlify.toml` declares any redirect beside a publish directory) failed the
build silently and left pin 1 a 404 for the rail's entire early life.

### 2.2 A kill switch and a notices channel

`minimum_installer` in the discovery document: a client below the floor
**refuses to run and says why**. `notices` reaches every install.

We have the opposite direction only — `min_td_build` per package, added in
[UpdaterHardening.md](UpdaterHardening.md), which stops a package landing on
too old a TD. We have **no way to stop a known-bad shipped updater**, and no
channel to tell the field anything. Given §7 of
[Overview.md](Overview.md) — self-update has never been run end-to-end — a
kill switch is the cheapest insurance we could buy before it is.

### 2.3 A toolkit-version floor on packages

Their `requires.lops_version` (`>=x.y.z`), plus **immutable compatibility
catalogs**: a frozen projection per installed base version, so an operator
update can never be offered to a base that cannot run it.

Our `requires` is a **name list only** — derived from stamped registry hosts,
which is a genuinely better mechanism for *which* core packages, but it says
nothing about *which version* of them. A tool that starts depending on a new
`FNS_ConfigRegistry` API has no way to say so. Verified:
`build_manifest.py:488-509` emits names; `min_td_build` (`:519`) is a TD build
floor, not a toolkit one.

### 2.4 Add-only publishing, and read-back verification

On 2026-08-19 their live `registry.json` was replaced by a projection missing
one product's row. **Every shipped updater for that product silently broke for
a week.** The fix: `publish-tox-row` patches exactly one row and *asserts every
other row byte-identical* before uploading, and every live publish re-fetches,
compares SHA-256, and prints its own `wrangler ... put` rollback line on
mismatch.

**We have their exact failure mode, unguarded — see §4.1.**

### 2.5 A protected set

Never overwrite a released artifact, the published registry, any R2 object a
user's updater can already reach, or any `.tox` a paying user already holds.
A fix reaches a shipped artifact as a *distinct new artifact*, never by editing
the one out there.

Our `_remoteHas()` skip-existing gets us most of this by accident on the normal
path, but `upload.py --force` and `--prune N` both reach published objects with
no ceremony. We have the *inverse* guard — the authored-here guard, which
protects the dev source from being overwritten by an artifact (paid for the
hard way, PackagingScheme §5). We do not have this one.

### 2.6 Smaller, still worth taking

- **A sealed plan ID** — `batch_release` computes a canonical SHA-256 of the
  dry-run schedule and refuses a live save unless it still matches the approved
  one. Our Guided Release confirms a plan but does not seal it.
- **Content-addressed object keys** (`objects/<op>/<ver>/<sha256>.tox`) so two
  builds of one version cannot collide. Our release label in the path covers
  the normal case; a *re-publish of the same release* would overwrite.
- **A freeze instrument** that logs any frame over 60 ms using `absTime.seconds`
  — deliberately not `absTime.frame`, which is wall-clock derived and reports a
  healthy frame rate straight through a stall.

## 3. Where we are ahead, or deliberately different

**Native TD I/O instead of worker threads.** Their auth stack runs `urllib` on
worker threads with deadlines, a queue the main thread polls, a `prime()` call
to resolve a `mod()` lookup before any worker touches it, and a hard line in
the file below which nothing may touch a TD API. All of that exists because Get
TOX 0.2.0 ran a blocking token exchange inline in `onHTTPRequest` and froze TD.
We fetch through the Web Client DAT — the house rule in
`.claude/rules/td-python.md` — so that entire class of bug is unreachable, and
[UpdaterHardening.md](UpdaterHardening.md) §3 already recorded the same
conclusion when declining Embody's certifi machinery. **Do not port their
threading model along with their ideas.**

**`Pkgversion` read live off the installed component.** They reconcile
`par.Version`, `manifest_ver`, `latest_tag` and on-disk releases — their
release Gate 1 is an audit that exists to make four sources agree. Ours has one
source and it cannot drift, because the component *is* the record. This is our
best invariant and it is worth defending.

**Derived dependencies.** `requires` falls out of which registry hosts a tool
stamps. Nothing hand-maintains it, so it cannot rot.

**No drift gate needed.** Their §10 exists because baked DAT text inside a
master and the repo `.py` diverge silently — the LANE A resolver was committed
and absent from all 91 baked copies of a shared module in a shipped release.
Embody's `syncfile=True` externalization makes the file the source and TD
reloads on change, so the drift cannot open in the first place. (One place to
stay honest: the portable export *does* inline externalized ext DATs. It
inlines from the live, synced DAT, so it should be sound — but nothing asserts
it, and their lesson was that a spot-check on one filename read 91/91 clean
while other files were stale.)

**A far more developed settings model.** They persist a venv path and a
`runtime.json` breadcrumb. We have two stores, `Configscope`, two rails per
tool, four hatches, and a measured account of what an in-place reload preserves
([ScopeAndPersistence.md](ScopeAndPersistence.md),
[UpdaterHardening.md](UpdaterHardening.md) §1). They install `.tox` files into
folders; we replace and reload COMPs inside a live project, which is the harder
problem, and we have actually measured it.

**A public manifest.** Their `/registry` requires a paid tier, so a free user
cannot see the catalog at all — and they had to *not* product-gate it to avoid
a patron being unable to see the thing they had paid for. Our proposed fully
public manifest with locked rows sidesteps both problems.

## 4. Three holes this comparison found in our own code

All three verified, all three independent of whether we ever gate anything.

### 4.1 A package can silently vanish from a release

`publish.py:98-100` computes `bumped` and `added` and refuses a release that
moves neither. It never computes **`removed`**. `Stage()` then `rmtree`s the
staged tree and rebuilds it wholesale from whatever `build_manifest.py` derived
from the live project.

So if a package is not loaded, or its `pi_suspect` tracking lapses, or the
generator simply does not see it, it disappears from the rolling manifest —
and the guard passes, because other packages did bump. Every install stops
being offered it, silently. **This is precisely the 2026-08-19 LOPs incident,
in our code, today.**

Fix is small: compute `removed` and refuse unless the removal is explicitly
declared. Cheap, and it closes the one failure mode their scar tissue says
costs a week.

### 4.2 Nothing verifies what actually landed in the bucket

`publish.py` re-hashes what it *staged* — good. `upload.py` checks wrangler's
exit code and, before uploading, whether the key exists. **Nothing re-fetches
after upload and compares.** A truncated or half-written object passes.

Their rule is read-back-and-compare on every live publish, with the rollback
command printed on mismatch.

### 4.3 One URL, no failover, no way to reach the field

Covered in §2.1 and §2.2. This is the one I would fix first, because unlike the
other two it cannot be repaired after the fact — a client that cannot find a
manifest cannot be told where the new one is.

## 5. Corrections to GatedDeliveryResearch.md

- **Model the entitlement claim as a product list from day one, never a
  boolean.** They shipped one field, later split it into `subscription_valid` +
  `products`, and in between raised the boolean's threshold — refusing $5
  patrons *their own product* for four months. My §3.1 says "device token" and
  is vague about its shape. It should carry a products claim.
- **Keep a compatibility fallback for old tokens.** Theirs falls back to the
  legacy claim so higher tiers never have to re-login; only the tier the bug
  actually broke has to sign in again.
- **Add the fail-open / fail-closed asymmetry** (§1) to the design.
- **Verify size then hash**, and have the Worker check the real object size
  before serving.
- Unchanged and reinforced: **do not watermark artifacts per user.** Their
  content-addressed keys make one canonical byte-set per version the whole
  basis of safe republishing — the same reason our `sha256` pinning cannot
  tolerate per-user bytes.

## 6. What I would actually do with this

In order, and none of it requires deciding anything about Patreon:

1. **`removed` guard in `publish.py`** — hours, closes a live hole (§4.1).
2. **Read-back verification in `upload.py`** — hours (§4.2). Pairs with the
   authenticated existence check that gated delivery needs anyway.
3. **A discovery document with pinned fallbacks, plus `minimum_installer` and
   `notices`** — the largest of the three and the only one that must exist
   *before* the thing it protects against (§2.1, §2.2).
4. Then gated delivery, if it is still wanted, with §5's corrections folded in.

Items 1–3 make the **free** rail more survivable and are worth doing on their
own merits. Nothing in them is contingent on selling anything.
