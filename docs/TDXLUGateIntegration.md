---
status: open
summary: Assessment of the TDXLU Gate Contract (artifact 06da3418, written at fe5f4d4) against the gate as it stands after the 2026-08-29 walk — who accommodates whom, which of its premises the weekend dissolved, the four pieces of gate surface we accept building, and the conditions attached.
since: 2026-08-29
skill: fns-packaging
---

# TDXLU on the gate: who accommodates whom

Reviewed: the "TDXLU Gate Contract" artifact (rendered from the
launcher repo's `docs/fns-gate.md` at `fe5f4d4`). Verdict up front,
because it is the question that was asked:

**Both sides move, and the asymmetry is exactly right.** The contract
is architected to CONSUME the gate rather than fork it — one Worker,
one keypair, one Patreon client, their own KV namespace — which means
most of the accommodation is theirs by design and consists of using
what exists unchanged. We accept **four bounded pieces of new gate
surface** (§3 below), each of which is generically useful rather than
TDXLU-shaped. And their document needs a **facts refresh**: it was
written before the weekend the gate went to production, and several of
its premises — including its own blocker — are now stale in TDXLU's
favor.

## 1. Their blocker is gone, and their precondition is met

The contract says *"blocked-on: the gate is BUILT, NOT DEPLOYED …
deploy it for FNSTools alone first; TDXLU comes after it has run in
production"* and repeats it as Open #1. As of 2026-08-29 evening:

- The gate is **deployed** (worker version `3730cc04`+) with the real
  tier map, and serves production traffic.
- The paid path has been **walked end to end** on a customer-shaped
  install: `/get/` → paste rail → bootstrap → sign-in → entitlement →
  gated artifact `sha`-true through the token rail → installed.
- v3.0.5/v3.0.6 are live in the bucket; the `plus/` prefix is
  canary-verified private on every upload.

"Let it prove itself" has begun. The remaining maturity gate on OUR
side is `EntitlementFunnelPlan.md` **0.5** (the bootstrap instance's
in-pass download wedge — observed, uncaptured, launch-blocking for
strangers). TDXLU integration work on the Worker can start before 0.5
closes (different code paths), but TDXLU should not LAUNCH on the gate
until 0.5 is dead — same spirit as their own deploy-order rule.

## 2. Corrections their document needs (they accommodate)

Stale facts, each one line to fix on their side:

- **Host.** Every URL says `gate.functionstr.com`. The domain migrated:
  the gate lives at `gate.functionstore.tools`, storage at
  `storage.functionstore.tools`. Their §5 Patreon-client redirect
  addition must register the NEW callback host (it already is —
  sign-ins ran through it on 2026-08-29).
- **Redeem shape.** Their route table shows `{key, product}`. The API
  is `{license_key, product_id}` — and since `128e3af` also
  `{license_key, package}`: the gate resolves Gumroad's product id
  from the package name through its own one-to-one map. The launcher
  should send the package name; a buyer knows the tool, not the id.
  (Response carries `{ok, device_token, products}` — no `uses` field.)
- **`/session/recheck` exists** and is absent from their table. It
  forces past the 6-hour cache (throttled), and since `8574a64` its
  answer carries structure their `LicenseStatus` should consume
  verbatim: `connected: false` = the Patreon grant is dead and only a
  re-sign-in helps (do NOT keep offering "check again");
  `stale: true` + `verified_at` = this is the last known answer served
  during a Patreon outage, not a real "no". This is also the natural
  trigger for their §3.1 "renewed on any successful re-check" claim
  renewal.
- **The manifest carries a routes projection** (`718743c`): the
  toolkit block ships the tier ladder WITH labels
  (Base/Pro/Coaching), `support_url`, and per-package
  `key_available`. Their UI copy ("unlocks at the Pro tier") can read
  the same projection instead of hardcoding labels.
- **The creator short-circuit is their test rail too.** The ladder
  grants upward and the creator holds the top tier, so the moment
  `TDXLU_Pro` enters the `TIERS` lists, the creator account is
  entitled to it — the launcher's whole flow can be walked by its
  builder before any customer. Their Open list should claim this
  explicitly.
- **A methodology warning they have earned the right to skip, once.**
  The first real walk of OUR client flow found three
  measured-not-assumed platform bugs (query parsing, response
  routing, auth headers) — every one in a leg that had never executed.
  Their `licensing.rs` rework is a new client against the same gate:
  its legs have also never executed. Their §8 should add "walk every
  leg against the deployed gate with the creator account before
  shipping" as a numbered step, not an assumption.

## 3. What we accept building (we accommodate)

Four pieces, all on OUR worker, all generically useful. Conditions
apply to each (see §4).

1. **`POST /entitlement`** — the signed long-lived claim
   (`/token/download` generalized: same session load, same
   `refreshEntitlement`, EdDSA JWT with per-kind `exp`). Accepted, and
   noted: their blockquote is right that this answers OUR open
   `EntitlementLifecycle.md §2.2` (how literal is offline) and
   dissolves the Gumroad KV-durability worry — the signed claim
   becomes a second copy of the licence that the client holds.
2. **`POST /trial/start`** — Turnstile-gated, `trial:<fingerprint>`
   KV anchor written once and never rewritten, minting an ordinary
   `kind:'trial'` session. Accepted. This is the "gate-minted trial"
   our funnel plan's trial-lane section explicitly deferred "to its
   own research doc if ever wanted" — this contract is that request,
   and their abuse analysis (Turnstile makes minting uneconomic; it is
   a 14-day trial, not a vault) matches our honesty-box doctrine.
3. **Config + namespace**: `TDXLU_Pro` added to the three `TIERS`
   lists, a `GUMROAD_PRODUCTS` row when the product exists, and a
   SECOND KV namespace bound for launcher sessions/trials. Verified
   on our side: `publish.py`'s entitlement preflight checks only the
   package→grant direction, so foreign product names in `TIERS` pass
   clean — no toolkit release breakage.
4. **A second gated prefix** (`utility/plus/…`) served by the same
   worker with the same fail-closed rule — ONLY if their §4 (gated
   companion modules) is ever decided for. Their own document keeps it
   separable; we keep it conditional.

## 4. Conditions attached

- **Tests before deploy, every route.** `gate.test.mjs` is the gate's
  spine (70+ offline checks, grown four times this weekend). New
  surface lands with its sections: trial anchor never rewrites,
  Turnstile refusals, per-kind `exp` on `/entitlement`, the second
  prefix failing closed. No exceptions — this weekend demonstrated
  exactly what untested legs cost.
- **Name the irrevocability.** A signed claim with a 10-year (Gumroad)
  or 180-day (Patreon) `exp` is IRREVOCABLE by construction once
  minted — revoking the session stops new claims, never outstanding
  ones. For Gumroad that matches the perpetual-licence decision; for
  a refunded purchase it means the refunded buyer keeps the claim
  window. That is consistent with "purchase gate, not DRM", but it
  must be a sentence in the contract, not a surprise: their §7 list
  should gain "an issued claim outlives revocation until its exp".
- **The machine binding is honesty-box.** `machine` in the claim is a
  hash of a CLIENT-computed fingerprint; the gate cannot verify it.
  Fine — same tier of protection as the HMAC scheme it replaces —
  but their Open #2 (fingerprint derivation) should note the gate
  treats it as opaque and unverifiable by design.
- **Secret rotation becomes production discipline.** Their §5.1 point
  stands and we co-sign it: with two products on one gate, a botched
  `PATREON_CLIENT_SECRET` rotation silently freezes BOTH. Before
  TDXLU lands, the rotation procedure gets a runbook entry on our
  side (EntitlementLifecycle §5.1 is the source).
- **Sequencing.** Worker-side routes may be built and tested any time;
  TDXLU goes live on the gate only after funnel plan 0.5 is closed
  and v3.0.x has survived its first strangers.

## 5. Frictions worth naming now

- **The trial lane forks, deliberately.** The funnel plan's trial
  section documents TDXMap as tool-governed (the tool holds the
  clock); TDXLU commits to gate-minted trials. Both models now exist
  in the family. That is acceptable — different products, different
  offline promises — but the funnel plan's trial section should note
  the fork and that `/trial/start`, once built, is available to any
  family product that prefers the gate-minted model (TDXMap could
  converge later; its choice stays its own).
- **CMS observability gap.** The CMS entitlement table renders
  per-toolkit-package from `catalog.json`; `TDXLU_Pro` in `TIERS`
  will be invisible there. The one place that grants it would have no
  authoring surface showing it. Small, but exactly the drift channel
  `gate_package.py` exists to close — its `--status` and the CMS
  table should learn to show foreign (non-package) grants as their
  own rows before TDXLU's row lands.
- **One Patreon client, three consumers.** Their §5 confirms TDMap
  shares the client and its loopback redirect must not be removed.
  With the gate's callback added, the client has three registered
  redirect URIs and a leak in ANY consumer compromises all — their
  §1 already says this about the shipped secret; retiring the
  launcher's embedded copy makes the gate the only secret holder,
  which is the point.

## 6. Action plan — gate side (this repo)

In order; each lands as its own commit with its tests. G1–G4 can be
built and merged any time; nothing DEPLOYS for TDXLU until the gate
precondition (funnel plan 0.5 closed, v3.0.x survived strangers) is
met.

- **G1 — `POST /entitlement`** *(LANDED `b9025b1`, deployed
  `9ea13ff8` 2026-08-30, live-verified; `GET /pubkey` added alongside
  so clients pin `GATE_PUBLIC_KEY` from one authoritative endpoint;
  G3's TIERS rows rode the same deploy — the launcher's L5 walk and
  the joint G7 legs are UNBLOCKED, their L3+L4 being already live
  per tdxlpp-a9. G7 itself was refined on tdxlpp-2f's review,
  `04da4b9`: the shared file lives at the machine-DEFAULT palette
  path always, never the Storefolder override, and Sign in adopts
  before it browses.)*: `worker/src/index.js`: session load +
  `refreshEntitlement` as in `/token/download`, but returns the EdDSA
  claim (`iss`, `sub`, `machine` passthrough, `kind`, `products`,
  `trial_expires_at`, per-kind `exp`: gumroad +10y, patreon +180d,
  trial = window end) and does NOT require non-empty products.
  Tests: per-kind `exp`; a lapsed session gets its lapse; `machine`
  is opaque passthrough; a claim verifies against `JWT_PUBLIC_KEY`.
- **G2 — `POST /trial/start`** *(PENDING DECISION 2026-08-30: the
  owner is leaning toward dropping the TDXLU trial entirely. Dropping
  it deletes this item, the Turnstile secret and its desktop-UX
  question, the fingerprint question, and the one route that mints
  entitlement from nothing — the audit's trial finding then closes by
  deleting Firebase rather than replacing it, and the funnel plan's
  trial-lane fork un-forks. Reversible later: the route is separable
  by construction. Do not build until decided.)* Turnstile verify (new
  `TURNSTILE_SECRET` wrangler secret), `trial:<fingerprint>` KV row
  written once and NEVER rewritten, second start returns the same
  anchor and remaining time, mints an ordinary `kind:'trial'`
  session. Throttled like redeem. Tests: anchor immutability, same
  window on re-start, Turnstile refusal, throttle, `/entitlement`
  over a trial session, expiry refusing new claims.
- **G3 — config + namespace.** `wrangler.toml`: `TDXLU_Pro` in all
  three `TIERS` lists; `GUMROAD_PRODUCTS` row when the product id
  exists; second KV namespace bound (e.g. `TDXLU_SESSIONS`) with the
  trial/session code parameterized over the binding. Tests: FNSTools
  sessions never land in the launcher namespace and vice versa.
- **G4 — rotation runbook.** `EntitlementLifecycle.md §5.1` becomes a
  numbered procedure (stage new secret, verify with a live sign-in,
  retire old) in `worker/README.md` — required before a second
  product shares the blast radius.
- **G5 — CMS shows foreign grants.** `gate_package.py --status` and
  the CMS entitlement table gain rows for grants that are not toolkit
  packages, so `TDXLU_Pro` is visible where it is authored.
- **G7 — the shared machine session** *(LANDED `1f9fec5`, 2026-08-30;
  acceptance recorded here per the §5 sequencing bullet — drafted this
  side on the launcher session's green light, no formal acceptance
  round per the amended contract)*: `gate-session.json` at
  `<palette>/FNStools_ext/config/`
  (beside the config, never under `store/`), schema
  `{schema:1, device_token, written_by, written_at}`, per the
  launcher contract's amended §5: atomic write on every successful
  sign-in and redeem; adopt when holding no session (once per
  extension lifetime, entitlements filled by a deferred token
  request); delete on gate `signed_out` and on sign-out — in both
  cases only while the file still holds the token in question, so a
  newer sign-in by another product survives; sign-out revokes first
  and signs the machine out of every product. Drafted this side under
  the contract's either-side clause, landed as `1f9fec5`, sandbox-
  verified (schema round-trip, guarded deletes, adoption). Two design
  points flagged to the launcher side for their §5 to mirror: a
  REDEEM also publishes the machine token (a licence key mints or
  extends the session too), and adoption stores a placeholder label
  until the first token response corrects it. Named
  cost, accepted pre-release: the opaque revocable token sits in
  plaintext JSON beside the config — weaker at rest than the DPAPI
  keystore that remains our own copy. Launcher-side worklist note
  (2026-08-30, via tdxlpp-a9): their dependency is G1 + TIERS-only G3
  (no Gumroad row yet); their L5 walk waits on those two, not on G7.
  **Ship lag (first L5 walk finding, 2026-08-30, via tdxlpp-2f):** G7
  reaches customers only through a FNSTools RELEASE — a sign-in
  running through a shipped pre-G7 updater tox writes no shared file,
  and that walk leg reads as failed when it is merely early. First
  release carrying it: v3.0.7 (updater 3.0.4); installed projects
  gain it via a normal update. **Backfill (adopted from the same
  finding):** a session signed in before G7 never published — publish
  only fired on sign-in/redeem. `Account()` now backfills once per
  extension lifetime: token held + shared file absent → publish the
  held token. Idempotent; makes G7 retroactive for every existing
  session the moment the new ExtAuth loads. Launcher mirrors in
  `licensing.rs` for symmetry.
- **G6 (conditional, only if their §4 is decided FOR) — second gated
  prefix.** Route `storage.functionstore.tools/utility/plus/*` through
  the worker; generalize the prefix check; fail-closed tests against
  a claim that names no launcher module.

## 7. Action plan — launcher side (their repo)

Handed to the TDXLU session as their worklist; L1–L2 are edits to
their `docs/fns-gate.md`, the rest is `licensing.rs` work from their
own §6, amended by the weekend.

- **L1 — facts refresh** in `fns-gate.md`: host →
  `gate.functionstore.tools`; blocker paragraph → "deployed and
  walked 2026-08-29, precondition met, launch gated on funnel plan
  0.5"; redeem → `{license_key, package}` (response has no `uses`);
  route table gains `/session/recheck`.
- **L2 — two sentences added**: an issued claim outlives revocation
  until its `exp` (purchase gate, not DRM — say it); and the machine
  binding is client-computed and unverifiable by the gate, by design.
- **L3 — client flow** per their §6, unchanged: loopback answers
  `/fns-auth`, verify `cn`, claim → device token, `/entitlement` →
  cached claim, atomic auth-file write, `SignOut` revokes first.
- **L4 — consume recheck structure**: `connected:false` → the
  re-sign-in path, never "check again"; `stale:true` + `verified_at`
  → surfaced as staleness, not a refusal; successful recheck renews
  the cached claim via `/entitlement`.
- **L5 — walk every leg before ship**: with the creator account
  (entitled to `TDXLU_Pro` via the ladder the moment G3 lands), run
  sign-in, claim, entitlement, trial-start (second machine or reset
  fingerprint), recheck, revoke — against the deployed gate, before
  any customer does. Budget for finding bugs: our equivalent walk
  found six.
- **L6 — trial UX decision** (their Open #3): Turnstile surface
  (loopback page vs webview) — their call, no gate dependency.

## 8. State as of 2026-08-30: staged for the human

Both sides are done up to the interactive leg. Gate: G1 + `/pubkey` +
G3 TIERS rows deployed (`9ea13ff8`), G7 landed and refined. Launcher
(per tdxlpp-a9): `GATE_PUBLIC_KEY` filled from `/pubkey` and committed
(TDXLPP `d9a3573`), 136 tests passing, their contract updated —
`/pubkey` in its route table, G1+G3 recorded live, the §5 path caveat
RESOLVED. The **joint walk needs Dan** — the sign-in leg is an
interactive browser flow with the creator account. The staged ladder:
sign-in → claim → `/entitlement` → recheck → revoke, plus the G7
legs (adopt both directions, machine-wide sign-out). After a green
walk, TDXLU's go-live gate remains: funnel plan 0.5 closed, v3.0.x
soaked, then the Patreon secret rotation per the runbook (G4, still
to write).

Coordination note (2026-08-30, TDXLPP `a198b33`): the launcher's
contract mirror is reciprocal — their §8.3 names TD-adopts-a-
launcher-written-file as the cross-test leg to watch, and the
closing-entry-in-both-docs agreement is written down on both sides.
Launcher-side routing: `fns-gate.md` and `licensing.rs` edits go
through session **tdxlpp-2f** (or whichever session Dan points at);
tdxlpp-a9 remains a relay. Address contract-mirror requests
accordingly.

Symmetry closure (2026-08-30, first live walk night, via tdxlpp-2f):
backfill mirrored in `licensing.rs` (TDXLPP `4b16cca`) with the
dead-token caveat; sign-out semantics sharpened in their §5 — a
sign-out revokes only the token it holds, divergent own-sessions
survive and sign out separately; their background refresh now honors
a definitive `signed_out` immediately (clears local record + shared
file, typed errors keep outages separate), matching our `_sessionDied`
on 401 — machine-wide sign-out reaches the launcher at its next
refresh/launch. Launcher download rails were audited against the
byte-eating trap fixed this side (`70f5403`) and already stage +
verify before rename; their store rail is free-only today. Launcher
open item, on record: `fns_store.rs` has no notion of `access`, so a
gated row in their store panel would surface as a digest-ish error —
FNSTools-Plus work-order territory.

## 9. Answer, restated

They built their side to accommodate us — correctly, and the document
shows real fluency in the gate's paid-for decisions (fail-closed,
product lists not booleans, one-time grant codes, the two ExtAuth
traps). We accommodate them with two routes, one config change, one
namespace, and conditionally one prefix — each with tests, each
generically useful, none TDXLU-shaped. Their document owes a facts
refresh (host, redeem shape, recheck, the dissolved blocker) and two
added sentences (claim irrevocability, walk-before-ship). Neither
side bends its architecture; that is what makes this the cheap
version of the integration.
