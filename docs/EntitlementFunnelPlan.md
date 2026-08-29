---
status: open
summary: The plan that closes the entitlement funnel — three-slice review verdict (TD client, picker/installer, gate worker) and the phased work: stop the funnel-breaking bugs, make degraded states honest, add the missing conversion rungs. Companion to EntitlementPathReview.md, which it re-checked.
since: 2026-08-29
skill: fns-packaging
---

# Closing the entitlement funnel

**Goal:** every user state, on every surface, gets (a) correct behavior,
(b) the true reason when refused, (c) a next step that moves them toward
entitled-and-installed.

This plan follows a full three-slice review of the paid path (TD client,
picker/installer/website, Cloudflare Worker gate) conducted 2026-08-29
against `EntitlementPathReview.md`. The review's verdict, condensed:

- **Every claim in the review doc held up.** Both test suites pass in
  full (`python tests/test_picker_flavors.py`, `node
  worker/test/gate.test.mjs`); the live wiring for defect #1 was
  confirmed in TD (`FNS_Updater.extensions` contains `ExtAuth`,
  `_auth()` returns it, no promoted-name collisions).
- **The happy path is closed** for the four canonical states: anonymous,
  signed out, signed-in-unentitled, entitled. Partial entitlement (Base
  holder, Pro tool) resolves correctly per package at every layer — the
  tier ladder is tested, the chip and `MissingFor()` are per-package.
- **Every *degraded* state leaks**, and always in the same way the
  original work fixed: the wrong refusal reason, or a checksum-flavored
  failure, while the honest cause sits in a return value no surface
  shows. The phases below are ordered by how badly each hole bleeds.
- **The Gumroad lane is gate-solid but surface-absent.** The worker
  treats a licence key as a first-class entitlement source — `productsFor`
  merges Patreon tiers and Gumroad products into one claim, mixed
  accounts work, a key-holding session is exempt from the 30-day
  stale-trust cutoff, and re-checking a held key spends no activation
  (all tested, `gate.test.mjs` section 8). The client rail exists
  (`ExtAuth.RedeemKey` via the `Licensekey`/`Licenseproduct` pars). But
  the PICKER — where the funnel lands people — has no redeem control at
  all, and every refusal sentence assumes Patreon. The amendments below
  (1.1, 1.3, 2.1, 2.5) carry the key-buyer persona through.

The findings live inline with their fixes; where a finding is recorded
but not scheduled, it says so.

## Phase 0 — Stop the bleeding (funnel-breaking bugs)

Each item lands with its own pinning test.

### 0.1 In-TD picker: a gated pick must not stall the install

The website fix (`08b690f`) was never mirrored on the served rail. The
served picker's `selection()` (`packaging/configurator/index.html`,
`selection()` near the `plusPicks` split used only by `installScript`)
puts unentitled Plus picks straight into `install`; the updater skips
them into `job['gated']`; the page's `/status` poll then reports
*"Download failed: unknown — see UPDATER status"* while UPDATER status
reads as success. Net: **nothing installs at all**, wrong cause, status
contradicts it, retry loops. This is the surface the website's own
closing message funnels users toward ("hit Pick Tools and click Sign
in").

Fix, both halves:

- `selection()` splits Plus picks the account is not entitled to out of
  `install` (the page has `access` and `FNS_ACCOUNT.products`; it can
  compute `entitled(p)` locally) — this also fixes the website's
  "Download selection.json" path, which shares the function.
- `/status` (`packaging/InstallerExt.py`) reads `job['gated']` and
  answers with `MissingFor()` wording; `ready` means "all *non-gated*
  picks arrived" so free picks still install.

Tests: extend `tests/test_picker_flavors.py` — lift `selection()` into
node across all four account states, assert gated picks never enter
`install` and free picks do. Also pin the `installScript()` SEL/PLUS
split, which is currently untested (it was verified once with an ad-hoc
node + `ast.parse` one-liner and never again).

*Field-confirmed 2026-08-29, first real walk: picking
FNS_TimelineTools produced a refusal visible only in the Textport —
exactly this defect. No longer theoretical.*

Live check: signed-out mixed pick in TD → free tools install, Plus tool
named with the sign-in sentence.

### 0.2 Worker: never discard a rotated refresh token

`refreshEntitlement` (`worker/src/index.js`, token-exchange block): when
the exchange succeeds but the identity call fails, the rotated
`ex.tok.refresh_token` is never saved. Patreon rotates refresh tokens on
use, so the kept old token can be dead — and its next use returns
`invalid_grant`, which the code correctly treats as *permanent*
revocation. A transient Patreon blip launders a paying supporter into
the revoked path.

Fix: persist `ex.tok.refresh_token` whenever the exchange succeeds,
regardless of identity outcome.

Test: the missing `gate.test.mjs` case — exchange ok + identity 5xx →
token saved, entitlement kept, next refresh succeeds.

### 0.3 ExtUpdater: report the real drop reason, stop double-reporting

`modules/suspects/FNSTools/FNS_Updater/ExtUpdater.py`, two localized
fixes:

- `_onGateDenied` also fires for transport failure ("could not reach
  the gate") and gate 401 ("Sign in again"), but `_report()` recomputes
  the reason from local state via `MissingFor()` — so an offline or
  session-expired supporter is told *"Your current tier does not include
  X."*, the exact inversion `auth_client_callbacks.py` warns must never
  happen. Stamp the actual reason per dropped package in
  `_onGateDenied`; `_report()` uses it.
- `_needed()` sets `plan_names` before the gated filter, so gated skips
  still flow into `_apply`, which fails them with "no artifact in the
  store" and flips `ok:False` — a contradictory double report the code's
  own comment forbids. Exclude gated skips from the apply plan.

Verify: stub the three deny causes, read `_report()` output for each.

### 0.4 The picker's display surface must know when it is visible

Found on the first real walk (2026-08-29): FNS_Hub / FNS_Console show
nothing — the picker page never renders — until the browser's
render-gating is switched off by hand. Mechanism
(`/FNSTools/webBrowser/watch_rules`): `Active` follows
`(Watchwindow AND panel.winopen) OR (Watchviewer AND activeViewer)`.
Embedded in a Hub/Console PANE, neither is ever true, so the sign-in
surface — the funnel's front door in TD — is dark by default and only
an operator who knows the toggles can open it. The component
anticipated half the fix: `Windowowner` exists so an embedder points
the watcher at ITS window — the Hub must set it. The pane case needs a
visibility signal the watcher does not have yet; verify the right one
against the TD wiki (panel values / pane state) rather than guessing,
then add it as a third opt-in watcher. Interim: rail instances keep
the watchers ON only where a window/viewer actually hosts them; a
Hub-embedded instance must not ship dark. Fix belongs to the vendored
webBrowser master + `_ensureBrowserPolicy` in `build_installer.py`
(rails rebuild follows, per 0-milestone mechanics).

*Status 2026-08-29: LANDED. Third watcher `Watchpane` ("Render Only
While Shown In Pane") + `Paneowner` on the master; the rule counts
only open `PaneType.PANEL` panes (a network editor's owner is a plain
COMP — often `/` — and counting those would mean always-on) and
matches owner by path prefix either direction. The Hub case is wired
by pointing the master's `Paneowner` at `FNS_Hub`, because the Select
COMP mirror means the browser is not in the Hub's hierarchy. Verified
live: dark with no pane, lit by a floating PANEL pane owning FNS_Hub,
dark one frame after close (the existing per-frame poll's cadence);
ColorUI's clone gained the pars and kept its own all-off values. Root
suspect PI-saved, vendored tox re-exported, `_ensureBrowserPolicy`
ships `Watchpane` on, rails rebuilt clean. The pane signal is
wiki-verified (`Pane.open`, `Pane.owner`, `PaneType.PANEL`).*

After 0.1–0.3: run `wrangler deploy` (source `TIERS` is already real —
`8323905`/`8291595`/`9796651` in `worker/wrangler.toml`; only the
*deployed* state is unverified), then walk the paid path with the
creator account — what the creator short-circuit (`5917c0e`) exists to
enable. Success = sign in, see "unlocked", watch a gated `.tox` arrive
and install.

**Coordinate first:** the ledger's in-flight domain-migration task
(functionstr.com → functionstore.tools) holds scopes over `worker/`,
`website/`, and `packaging/`. Land after it, or rebase onto it.

*Status 2026-08-29, end of day: the release is REAL. v3.0.4 staged
complete (49 packages, TimelineTools on the plus rail, rails rebuilt),
uploaded — the bucket serves the v3.0.4 rolling manifest with
TimelineTools' gated URL (verified live). Getting there burned through
three Windows layers in the upload chain (see the CMS section) and
surfaced the version-persistence gap (Phase 3, PI dirt). The walk
itself is PART-DONE: the signed-out lanes were exercised for real and
paid immediately — three field defects found, two fixed same-day (0.4
the dark front door; the stranded download window: `Showprogress` now
defaults off, `AbortAll` closes it, late disconnects guarded —
`3d1b97c`) and one confirmed (0.1's Textport-only refusal). Still
open to close the milestone: `wrangler deploy` (the live worker
predates `/session/recheck`), then the ENTITLED walk — sign in as
creator, watch the gated tox arrive and install.*

*Phase 0 status, night of 2026-08-29 (branch `dev25-entitlement-funnel`):
ALL LANDED. 0.1 `e2a9a84` — selection() splits gated picks in every
flavor, /status reports gated + gated_why and `ready` stops waiting,
the page speaks the sentence; pinned across all four account states,
and the paste script's SEL/PLUS split is pinned for the first time.
0.2 `0abf563` — the rotated refresh token persists on exchange
success; tested through the full half-outage round trip. 0.3
`9bf0908` — stamped drop reasons speak verbatim, gated names filtered
from the apply plan at consumption; verified live. 0.4 was landed
earlier (`ed6a37b`). Still open in this section: the milestone walk
(deploy + entitled sign-in — the user's morning).*

## Phase 1 — Honest degraded states (no more dead ends)

- **1.1 Session death resurfaces Sign in.** On gate 401 `signed_out`,
  `OnTokenResponse`/`OnRecheckResponse` (`FNSTools/FNS_Updater/ExtAuth.py`)
  mark the local record signed out, so `FNS_ACCOUNT` goes `null` and the
  picker's existing rail re-offers Sign in. Today the stale keystore
  keeps claiming "N unlocked" and the Sign in button stays hidden; the
  only escape is discovering the Signout pulse. **Origin-aware:** the
  remedy must match how the account was made — "sign in" for a Patreon
  half, "redeem your key again" for a key-only holder (free by design:
  re-checking a held key spends no activation). If the local record
  does not carry its origin, add it when storing.
- **1.2 Lapsed entitlement corrects the local record.** The 403
  `no_entitlement` body deliberately carries `products: []`;
  `OnTokenResponse` currently discards non-200 bodies. Pass it through
  `_rememberProducts` so the picker stops claiming "unlocked" forever.
  Safe for key holders: worker responses always carry the MERGED
  products list (Patreon + Gumroad), so this cannot wipe purchased
  products.
- **1.3 A dead grant gets a distinct signal.** After permanent
  `invalid_grant` the worker strips the refresh token; recheck then
  returns `products: []` forever — indistinguishable from "never
  pledged". Add `connected:false` (or similar) to session/recheck
  responses so the client can say "your Patreon link is broken — sign in
  again". This is the original commercial dead end, one layer down.
  Only fire the wording for sessions that HAVE a Patreon half; a
  key-only session has no grant to be dead.
- **1.4 No unauthenticated gated fetches.** `_download` with an empty
  `_gatedToken()` sends the request bare; the 401 JSON body then fails
  the sha check and reports as "hash mismatch" — website defect #4's
  class, still alive on this rail (reachable when the 15-minute token
  expires mid-pass). Refuse the item with an auth message, or re-request
  a token.
- **1.5 The refresh-kind report speaks too.** `_report()`'s refresh
  branch drops `job['gated']` entirely, and `StoreStatus()` counts
  deliberately-skipped gated packages as store-broken "missing"
  (`ok:False`). Emit `gated`/`gated_why` from the refresh branch; give
  gated skips their own bucket in `StoreStatus`.
- **1.6 Recheck honesty.** Worker: when a recheck serves cached data
  during a Patreon outage, say so (`stale:true` / `verified_at`) —
  today it burns a throttle slot to return a silent stale "no". Picker:
  surface the real recheck outcome (throttle included) instead of the
  unconditional "Checking with Patreon…", and stop the success dialog
  unhiding a spurious Install button (`showDialog(res.text, false)`).

*Phase 1 status, same night: ALL LANDED. 1.1+1.2 `9b670e9` — a gate
refusal is data: the 403 body's merged products list corrects the
local record, a 401 clears the dead session locally and re-offers
both ways back in. 1.3+1.6(worker+client) `8574a64` — recheck answers
carry `connected` / `stale` / `verified_at`, the client picks the
sentence by structure, and recheck persists the response's own tiers.
1.4 `0b2e17b` — a gated item with no valid token is dropped with an
auth sentence before it can go out bare. 1.5 `e55e225` — the
refresh-kind report speaks gated reasons via the shared `_gatedWhy`,
and StoreStatus gives gated-not-entitled absences their own bucket.
1.6(picker) `fc41e05` — `/auth/status` serves the outcome, the page
polls it and reloads itself on product changes, and the spurious
Install button is gone. Every worker change is tested in
`gate.test.mjs`; every client change verified live in TD.*

## Phase 2 — Conversion polish (the funnel's missing rungs)

- **2.1 Name the routes, not just the tier.** The data exists — `access`
  names a tier id in the manifest — but no surface renders it: the
  picker collapses it to `isPlus()`, `MissingFor()` doesn't name the
  needed tier, the gate's 403 returns the tiers you *have*. Ship tier
  labels in the manifest's `toolkit` block (from the gate's
  `TIER_LADDER`, alongside the already-planned `support_url`), and stamp
  per-package purchasability at publish time (`publish.py` already reads
  `GUMROAD_PRODUCTS` to validate reachability — reuse that to emit a
  `buy_url`/flag). Then: chip tooltip and `MissingFor()` say *"X unlocks
  at the Pro tier"* — *"or buy a lifetime key"* when a Gumroad row
  exists — and the button reads **Upgrade** (not "Become a supporter")
  for a user already holding a lower tier. Wording must reflect the
  ladder ("this tier or higher").
- **2.2 Wanted-Plus picks survive.** A website user's Plus picks live
  one Textport line, then vanish from every later surface.
  `selection.json` already records them in `tools`; the served picker
  pre-checks locked wanted tools from it (alongside `FNS_INSTALLED`), so
  after sign-in the original intent is waiting.
- **2.3 `checked_at` end-to-end or out.** Emitted but always 0 (storage
  writes `stored_at`; nothing writes `checked_at`) and never rendered.
  Either store it in `_rememberProducts` and render freshness in the
  picker, or delete the field from the emission.
- **2.4 Truthful 403 tiers.** Return trusted tiers (or a distinct
  stale-trust code) instead of raw stored tiers, so the 30-day
  stale-trust case stops reading as "tier not mapped". And don't stamp
  `verified_at` at sign-in when the identity call actually failed.
- **2.5 Redeem key on the picker rail.** The picker offers Sign in /
  Become a supporter / Check again — a lifetime buyer has no door at
  all; `/plus/` even promises keys are "redeemed in the same place as
  the Patreon connection", but that place is the updater's parameter
  page, which the funnel never points at. Add a Redeem key control to
  the picker's account rail (a new `/auth/redeem` route in
  `InstallerExt.ServeRequest` calling `ExtAuth.RedeemKey`, same shape
  as `/auth/signin` and `/auth/recheck`), hidden on the public build by
  the same `hasAuthRail` guard the other remedy controls use — extend
  the flavors test's hidden-on-site checks to cover it. Keys are
  per-tool: the control should pre-fill `product` from the locked pick
  where possible instead of asking the user to type a product id.
- **2.6 The storefront must deploy when the mirror publishes.** Found
  live: `functionstore.tools/get/` served a months-old build — no Plus
  chips, download buttons pinned to a release the bucket never held —
  while every push and CLI deploy landed as a Vercel PREVIEW, because
  the project's production branch is `main` and the mirror pushes
  `dev25`. "Push didn't do anything" must be impossible to repeat: set
  the Vercel production branch to `dev25` (Settings → Git) so every
  `publish_public.py --push` IS a production deploy, built from the
  full checkout — which also lets `build-site.mjs` regenerate `/get/`
  from `packaging/configurator/` instead of warning "/get/ not built"
  and shipping the committed copy (the CLI-deploy payload cannot see
  `packaging/`). `vercel --prod` from `website/` is the interim
  lever only. Bonus riding on any deploy: pin 2 comes alive
  (`vercel.json` rewrites `/.well-known/fnstools.json` to the
  bucket's). Pin 3 still needs its `fnstools-links` repo pushed.

*Phase 2 status, same night: CODE-COMPLETE except 2.6's dashboard
half. 2.1 `718743c` — the manifest's toolkit block carries the routes
projection (SUPPORT_URL owned here; the tier ladder's labels from
gate_package; per-package `key_available` from GUMROAD_PRODUCTS),
MissingFor and the locked chip name the entry tier ("or higher") and
the key where one exists, and a tier-holding unentitled account is
offered Upgrade, not Become a supporter. 2.2 `5aaf5aa` — FNS_WANTED
resurfaces wanted-but-locked picks. 2.3 `7832228` — checked_at is
written on every gate answer and rendered as an age. 2.4 `14a2f7e` —
refusals show TRUSTED tiers; a half-failed sign-in stamps no
verification and retries soon (tested through recovery). 2.5
`128e3af` — Redeem key on the picker rail: inline DOM form, buyer
names the tool, the gate resolves the product id through its own
one-to-one map; dormant until GUMROAD_PRODUCTS gains rows. 2.6
remains: flip the Vercel production branch to dev25 (dashboard) —
plus one wording fix here: the committed-copy claim below predates
learning that generated pages are untracked; the CLI payload ships
the on-disk BUILD output, not a committed copy. All nine test suites
pass; every hot-synced client edit verified live in TD.*

## The trial lane (settle before the first trial tool ships)

A third acquisition route exists that the phases above do not name:
**tools that govern their own trial** — TDXMap is the live example
(`website/content/family.json`: "14-day Pro trial · Base and Pro with a
membership or a licence key"), currently a family product with its own
site, its own licensing, entirely outside the store, manifest and gate.
Nothing in `catalog.json` carries a trial today, so this is vocabulary
and contract work, not a bug fix — but it must be settled before the
first trial-bearing tool ships through the store, because every one of
its decisions touches surfaces the phases above are already changing.

The model, as decided today: **the tool governs the trial; the gate
stays out of it.** That fixes what each layer means:

- **The artifact is not the paywall — the runtime is.** A trial tool's
  bytes must be downloadable without entitlement (else there is no
  trial), so its manifest entry is NOT `access: <tier>` in the current
  sense: the gated-skip logic (`_needed`), the picker's locked chip and
  the website's Plus-pick deferral must all let it through. It needs
  its own marker — e.g. `access: <tier>` plus `trial: <days>`, read as
  "install freely, the tool enforces" — so `isPlus()`/`_isGated()`
  don't misclassify it. Decide the exact vocabulary WITH 2.1, which is
  already touching how `access` renders.
- **"Try free for N days" is a chip state and a funnel rung.** The
  strongest conversion copy the picker and website can show; today the
  vocabulary cannot express it. Chip: "Pro · 14-day trial" instead of
  "Plus · locked"; the pick installs immediately, signed in or not.
- **The handoff back is the part that must not dead-end.** A trial
  expiring inside the tool is the same moment as the picker's "locked"
  state, one surface deeper. The tool needs a runtime entitlement
  contract to ask "is this account entitled to X, and if not, what are
  the routes?" — i.e. a promoted, documented API on the auth extension
  (products lookup + `MissingFor`-style routed refusal + the 2.1 route
  data), so an expired trial shows the SAME funnel (upgrade tier / buy
  key / sign in) instead of each tool inventing its own. Design the
  surface per `/parameter-design` + extension conventions when it
  lands; the enforcement stance is honesty-box (same as the rest of
  the toolkit — the gate protects bytes, not runtime).
- **Explicitly deferred:** gate-minted trial entitlements (time-boxed
  products issued per account, one per user, server-enforced). More
  honest than tool-side clocks but real worker surface (trial claims,
  expiry, one-shot issuance, abuse throttles). Do not build it
  implicitly through any of the above; if wanted, it is its own
  research doc.

TDXMap itself stays outside the store either way; this section exists
so that when a store tool (or a store-distributed TDXMap) wants the
same funnel shape, the toolkit's surfaces already have the words for
it.

## Placement is a per-package contract (settle with the trial lane)

Today both placement axes have exactly one hardcoded answer: every
package lands inside THE toolkit container (`InstallerExt` resolves the
container that ships the installer, else the project's, else a new one
beside Embody), and every artifact lives in the flat machine store at
`<palette>/FNStools_ext/store` — by contract a MIRROR of the bucket,
where "nothing in it is anyone's work." Products are coming that break
both assumptions, TDXMap first among them. Two independent axes to make
explicit:

- **Network destination.** Three policies: *inside* the toolkit
  container (today's only mode, stays the default); *beside* it — a
  sibling at the container's parent, for products that are their own
  top-level thing (TDXMap next to FNSTools, not inside it); and *at the
  cursor* — wherever the user's network editor's owner is at install
  time (`ui.panes.current.owner`), for drop-anywhere tools. The third
  is really a per-INSTALL choice a package can declare it wants, not a
  fixed path — and it needs a fallback for headless installs (the
  paste rail has no pane).
- **Disk destination.** TDXMap.tox wants `<palette>/TDXMap/`, not the
  FNStools_ext store. Keep the invariant rather than bending it: the
  store stays the flat, sacred bucket mirror (download, verify, one
  copy of each package — `_inStore` and "stale cache, never a
  modification" depend on this), and a new INSTALL-time placement step
  copies the verified artifact to the package's declared palette
  folder. Per-package store paths would break the mirror contract for
  the worst possible reason; a placement step breaks nothing.

What carrying these two axes touches:

- **Manifest vocabulary**: a per-package `placement` block (network
  policy + palette folder), decided together with 2.1 and the trial
  marker — three vocabulary changes to the same catalog rows should
  land as one schema, one migration, one CMS authoring pass (picker
  discipline; placement is packaging authoring, so it lives on the
  FNS_CMS side of the split).
- **Update tracking**: `UpdateProject` compares what THIS project
  recorded at install time against the store — that record must carry
  WHERE the package landed (network path and disk path), or updates
  will never find a sibling-landed or cursor-landed install. Same for
  palette-shared installs whose `externaltox` points at the store
  artifact: a TDXMap pointing at `<palette>/TDXMap/` is a second
  externaltox convention the reload path must honour.
- **The gated lane composes with placement, unchanged**: a gated
  outside-lander still downloads through the token rail into the store
  first; placement is a local copy after verification. No new gate
  surface.
- **Preflight coherence** (the same Stage-time gate the CMS section
  extends): refuse placement declarations that cannot work — a
  cursor-landing package that stamps a registry host expecting the
  toolkit container, a palette folder that collides with another
  package's, a beside-lander with no container to be beside.
- **Conformance**: `/fns-packaging` and the registry rules assume the
  container in places (parent shortcuts, `/sys` stamping, Packages()
  enumeration explicitly EXCLUDES things outside `/FNSTools` — which
  is the point for FNS_CMS, and exactly why a beside-lander needs its
  own answer for "am I installed / current"). Walk those contracts
  once with a beside-lander before declaring the vocabulary done.

**TDXMap is the composite proof.** It is gated (Base/Pro), trial-
bearing (14 days, tool-governed), key-purchasable, beside-landing, and
palette-foldered — one product exercising every section of this plan
at once. When it ships through the store, that shipment is the
integration milestone for the trial lane, the Gumroad lane, and
placement together; do not certify any of the three vocabularies as
done before that walk.

## CMS considerations (the authoring half of the funnel)

The funnel has two halves: what the customer sees (the phases above)
and where the operator authors it — and the second half already has an
owner. FNS_CMS is the entitlement-authoring surface (`gate_package`
wrapped as pickers: package roster from `catalog.json`, tiers from
`TIER_LADDER`, names not ids — `f1f0ea0`), while `cms.mjs` owns content
and *deliberately declined* entitlement ("does not offer to invent a
tier id"). Every plan item that adds funnel vocabulary must land on the
right side of that split, with these specifics:

- **2.1's new manifest fields need authoring homes.** Tier labels come
  from `TIER_LADDER` (already CMS-rendered); per-package purchasability
  is derived from `GUMROAD_PRODUCTS` at publish (no new authoring);
  but `support_url` in the toolkit block needs an owner — either a CMS
  field or a declared constant, not an unowned key someone hand-edits
  into a manifest.
- **The CMS entitlement table should preview the CUSTOMER sentence.**
  It already shows the operator's view ("Unlocks from: Base"; "Tiers
  that grant it: …"). Once 2.1 ships routed refusals, show the same
  line the picker/`MissingFor` will render ("X unlocks at the Pro tier
  — or buy a lifetime key") so gating mistakes are caught at authoring
  time, before a customer reads the wrong sentence. Single-source
  rule applies (the DOCS_SITE drift in `CmsExt._docsSite` is the
  cautionary tale): the preview must read the same published fields
  the picker reads, never a parallel copy of the ladder.
- **The trial marker is entitlement, not content.** When the trial
  vocabulary lands (`trial: <days>` beside `access`), it is authored
  in FNS_CMS's entitlement tab with the same picker discipline — no
  typed-from-memory fields — and NOT in `cms.mjs`, per the declared
  split. `cms.mjs` keeps descriptions, categories, docs prose.
- **Preflight/Stage is the funnel's last gate.** `publish.py` already
  refuses a gated package no tier and no Gumroad row grants; as 2.1
  and the trial marker add fields, extend the same preflight to refuse
  incoherent combinations (a `trial` marker on a free package, a
  `buy_url` with no Gumroad row) so the CMS surfaces the refusal at
  Stage time, in the operator's face, not in a customer's picker.
- **The CMS must name its motions truthfully.** Its release action is
  labelled "Publish selected" while `_apiRelease` hard-codes
  `upload=False` and deliberately does not offer upload — so the CMS
  can do everything EXCEPT ship, and its button claims the one verb it
  cannot perform. Observed cost, both directions: the operator stages
  and believes the last step is done, or presses "Publish" and
  believes it shipped when nothing reached the bucket. Fix per the
  naming doctrine (name the effect): reserve *publish/ship* for
  motions that reach the bucket, rename the CMS action to what it does
  (release & stage), state on the page where the motion ENDS
  (`packaging/publish/`, nothing uploaded) and where shipping lives
  (PI's Publish-to-Bucket, or `upload.py` in a shell) — ideally with a
  read-only view of the upload log so the CMS can at least REPORT ship
  state it refuses to own. *Status 2026-08-29: the copy is fixed in
  `website/tools/cms.html` (button "Release & stage selected", hint
  says where the motion ends and where shipping lives, dialog/toast
  verbs match) — riding uncommitted with the CMS session's in-flight
  work on that file. The upload-log view remains open.*
- **The CMS MAY ship — honestly.** Decided: the objection to upload in
  the CMS was watchability, not capability, and PI already ships via
  `StartUpload()` — a DETACHED subprocess logging to
  `packaging/publish/.upload.log`, not in-process network I/O. So the
  CMS gains a separate, truthfully-named **Upload to bucket** action
  that kicks the same `StartUpload` and tails the log into the page —
  the read-only log view above, made load-bearing. Release & stage
  and Upload stay two buttons, never one: the two-step is the honesty.
  Prerequisite fix for BOTH surfaces: `StartUpload` spawns `python3`,
  which does not reliably resolve on Windows — PI's
  Publish-to-Bucket has the same latent failure; fix the interpreter
  discovery once in `release_one.py`. (`packaging/` is inside the
  domain-migration task's claimed scopes — land through or after it.)
  `check_pins.py` stays a shell step. *Status 2026-08-29: LANDED —
  `/api/upload` + `/api/uploadlog` on FNS_CMS, Upload-to-bucket +
  log-tail + PI-Save-unsaved on the release view, endpoint verified
  live. The release also now PI-saves the packages it bumps
  (`release_one.py`), closing the where-are-my-tox-diffs gap. The
  first REAL upload then peeled three Windows layers off the chain,
  each found only by running it: `which()` trusted the App-Store stub
  aliases, so candidates are now validated by execution — a python is
  real only if it prints 1 (`f789b4c`); bare `npx` is `npx.cmd`,
  which the shell resolves and CreateProcess does not (`a790066`);
  and `text=True` decoded wrangler's UTF-8 with cp1252, shredding a
  healthy run — encoding pinned end to end (`17b2f78`). UI edits ride
  uncommitted with the CMS session's in-flight work.*
- **Coordination:** the CMS is under active development in a parallel
  session (uncommitted `CmsExt.py` / `cms.html` / `cms.mjs` work in
  the tree at the time of writing) — land CMS-side amendments through
  or after that work, not blind beside it.

## Phase 3 — Pinning, errata, cosmetics

- **Tests:** the Phase 0/1 pins above; the flavors test's guard-ordering
  check gains the signin unhide; broaden the "token never leaves the
  updater" grep beyond two literal strings.
- **Doc corrections** to `EntitlementPathReview.md` (written to be
  re-checked, so keep it checkable): `_makeQueue` → `_needed`; "same
  counter as redeem" → same limit/mechanism, separate bucket; note the
  Gumroad redeem as a third products-write path.
- **PI dirt is blind to script-written pars** (paid for on v3.0.4):
  a `p.val` write from the release rail bumped 49 live versions and PI
  marked 13 dirty — "Save unsaved" honestly saved what PI saw and the
  other 36 tracked toxes kept the old version, FNS_Updater included.
  The release self-saving its bumps (landed) closes the release case;
  the residual hazard is any OTHER scripted par write trusted to PI
  dirt. Either teach PI's dirt to see par writes, or teach the CMS
  release view to flag rows whose live version disagrees with the
  committed suspect (it has both numbers).
- **The dev installer does not hot-sync, and testing forgets it** (paid
  for on the walk, twice-shaped like 0.4's dark door): the live
  FNS_Installer's `InstallerExt` and `configurator_html` are embedded
  SNAPSHOTS by design — what ships is what they hold — so editing
  `packaging/InstallerExt.py` or the configurator changes nothing live
  until `EnsureDevRails()` re-embeds them, and the browser panel
  additionally holds the old DOM until reloaded. The walk hit a server
  without `/auth/*` answering an empty dialog. Candidate fix: the
  preflight (or a test) compares the LIVE installer's snapshot against
  the repo file the way `_staleRails` compares the rails, so a stale
  dev installer blocks a release instead of confusing a walk.
- **A browser address outlives its server** (third walk finding, same
  family as the dark front door): the shared webBrowser keeps whatever
  `Address` the last serving flow wrote — the walk found it holding a
  long-dead Console port (36710) with the picker's server not running
  at all, every click landing in the void as an empty dialog. The
  ports themselves are fine (installer 36760 + bind-walk, console
  36710–59, CMS 36770–79 — multiple open projects are designed for).
  Landed: the page's `post()` failure now names the remedy ("press
  Pick Tools") instead of showing a raw or empty error. Still open:
  the Hub's tabs could pulse their flow's serve on tab focus, so a
  stale address self-heals instead of relying on the user knowing
  the front door.
- **Cosmetics:** the "page reloads itself" comment in
  `InstallerExt.py` (made TRUE by 1.6 rather than deleted);
  `slow_down` vs `rate_limited` unification; the
  three `/session/*` routes missing from `worker/README.md`'s route
  table; the stray `NoneType` third entry in `FNS_Updater.extensions`;
  recheck's redundant double-hash and double-save; recheck persisting
  stale local tiers instead of the fresh payload's.

## Out of scope, tracked elsewhere

- Artifacts for FNS_TimelineTools and the seven other catalogued-but-
  unexported packages — release track.
- Populating `GUMROAD_PRODUCTS` (ships empty `{}` in
  `worker/wrangler.toml`, so nothing is key-purchasable today) — same
  bucket as the tier-map deploy; `gate_package.py --gumroad` is the
  tool. Note 2.1's manifest stamping reads this map at publish time, so
  it only lights up once rows exist.
- Real-customer end-to-end (needs a real pledged account; unlocked by
  the Phase 0 milestone).
- Patreon-latency tuning of the recheck throttle — revisit with real
  supporter data.

## Execution notes

- `ExtUpdater.py` / `ExtAuth.py` are hot-synced into the live TD
  session: land file-by-file, `get_op_errors` after each, per
  `worktree-td-safety`. `worker/` and `website/` are inert on disk and
  safe to batch.
- Sequence everything behind (or rebase onto) the in-flight domain
  migration; its ledger scopes overlap every directory this plan
  touches.
- Success criteria per phase are the named tests plus the live checks;
  the plan is done when the Phase 0 milestone walk succeeds and every
  degraded state in the review's funnel matrix shows its true reason
  and a next step.
