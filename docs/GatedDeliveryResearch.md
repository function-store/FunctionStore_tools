---
status: research
summary: Gating some R2-bucket packages behind Patreon membership or a Gumroad license key. Worker built and tested; not deployed, TD client side not started.
since: 2026-08-26
skill: fns-packaging
---

# Gated delivery: Patreon auth and Gumroad license keys

Research into delivering *some* packages only to paying supporters, while the
rest of the toolkit stays free and open. Delivery stays on R2 exactly as it is
today ([PackagingScheme.md](PackagingScheme.md)); Patreon and Gumroad are only
ever asked one question — **is this person entitled?**

> **PARTLY BUILT 2026-08-27.** The Worker is written and tested
> (`worker/`, 28 offline checks) and the manifest carries entitlement
> metadata; `FNS_TimelineTools` is the first gated package. **Not deployed**, and nothing has
> been exercised against a live gate. Status and what remains: §10.

Read §2 first: one constraint decides the whole shape.

> **Revised 2026-08-26** against a shipping implementation of this same
> architecture — see [DistributionComparison.md](DistributionComparison.md).
> Four things changed: the claim is a **product list, never a boolean** (§3.1),
> credentials go in the **OS keystore, not a sidecar file** (§5), verification
> checks **size then hash** (§3.3), and §3.1 now records the heavier
> own-IdP option and why it may be worth it.

---

## 1. What already exists (this is cheaper than it looks)

Four facts from the current code, all verified this session:

**There is exactly ONE place in TouchDesigner that touches the network.**
`ExtUpdater._fetchManifest()` and `ExtUpdater._download()` in
`modules/suspects/FNSTools/FNS_Updater/ExtUpdater.py`. `InstallerExt` installs
only from the palette store (`DefaultManifest()`, `_artifactPath()`) — it never
fetches. The configurator picker reads a manifest. So the gate attaches at one
chokepoint, not scattered across the toolkit. (`FNS_Updater/github_remote/` is
the dead GitHub rail from PackagingScheme §6 — ignore it.)

**The vendored downloader already speaks bearer auth, per request.** Probed
live on `/FNSTools/FNS_Updater/fileDownloader` (TD 2025.33070):

```
Download(url, location, loadIntoProj, compPath, discCopy, dwnldCopy, renameTo,
         doneCallback, abortCallback, progressCallback, reqMethod, reqData,
         reqPars, authType, username, password, appKey, appSecret,
         oauth1Token, oauth1Secret, oauth2Token, uploadFile, force, clear,
         showProgress)
```

`authType` + `oauth2Token` are **per-call arguments**, so a gated artifact can
carry an `Authorization: Bearer` header while the manifest and the free
artifacts do not. `webclient1`'s `authtype` menu is
`none/basic/digest/oauth1/oauth2`, and its headers-table input is currently
unwired — we do not need it. **TDFileDownloader needs no modification**; only
`_download()`'s two-line signature does.

**Loopback OAuth is already a solved pattern in this codebase.**
`FNSTools/OpenExt/FNS_ConfigRegistry/ConfigRegistryExt.py` creates a
`webserverDAT` on demand, picks a free port with `_freeUiPort()` over
`UI_PORTS = range(9871, 9881)` bound to `127.0.0.1`, opens the system browser
with `webbrowser.open`, and shuts the server down after `UI_IDLE_SECONDS` of
silence (`_settingsIdleTick`). An OAuth callback listener is the same machine
with a shorter idle. Confirmed against the wiki: Web Server DAT's `onHTTPRequest`
returns the response dict, and **Local Address** binds a single interface.

**Curated per-package metadata already has a home and a rail.**
`packaging/catalog.json` holds what a machine cannot derive (category,
description, `recommended`), and `build_manifest.py` merges it into
`manifest.json` and derives the top-level `starter` list from it. An `access`
field follows an existing pattern rather than inventing one.

## 2. The constraint that decides everything

**Patreon's token exchange requires `client_secret`. There is no PKCE.**
`POST www.patreon.com/api/oauth2/token` takes `code`, `grant_type`,
`client_id`, `client_secret`, `redirect_uri`.

A `.tox` is a file anyone can drop into TouchDesigner and open. A secret inside
one is not a secret. PackagingScheme §7 already states the rule for the bucket
("a token must never ship inside a distributed tox") — the same rule applies
here, and it is fatal to any client-only design.

**Therefore a server-side broker is mandatory.** Not a convenience, not a
phase 2. Every Patreon design that does not have one is wrong.

Gumroad is different — `POST https://api.gumroad.com/v2/licenses/verify` takes
`product_id` + `license_key` + optional `increment_uses_count` and needs no
secret, so it *could* run in TD. It should not: a check that runs on the
client is a check the client can edit out of a text DAT in thirty seconds.
Since the broker exists for Patreon anyway, Gumroad goes through it too.

**The corollary is the important part: entitlement must gate BYTES, not UI.**
Greying out a button in the picker is cosmetic. The only gate that means
anything is R2 refusing to serve the object.

## 3. Proposed shape

Three pieces. Two are new, one is a small edit.

### 3.1 The broker — a Cloudflare Worker

Same platform as the bucket, so the R2 binding is direct and there is no
second vendor.

| Route | Does |
|---|---|
| `GET /patreon/start?port=<loopback>` | 302 → Patreon authorize, `redirect_uri` = the Worker's own callback, loopback port + CSRF nonce carried in `state` |
| `GET /patreon/callback?code&state` | exchange code (secret lives here), `GET /api/oauth2/v2/identity?include=memberships.currently_entitled_tiers`, resolve against the campaign, mint an **FNS device token**, persist `{patreon_user_id, refresh_token, tier, token_hash}` in KV/D1, then 302 → `http://127.0.0.1:<port>/fns-auth?token=…` |
| `POST /gumroad/redeem` | call Gumroad verify with `increment_uses_count`, reject `refunded` / `disputed` / cancelled subscriptions, mint the same device token, record the seat |
| `POST /token/download` | device token → short-lived (≈15 min) download token, re-checking entitlement against a ≤24 h server-side cache |
| `GET /plus/<release>/<pkg>.tox` | verify bearer token + that the tier covers this package, then stream from the R2 binding |

Only the Worker ever holds a Patreon refresh token. **TouchDesigner only ever
holds an opaque FNS token** — which we can revoke, and which is worthless
anywhere else.

**The claim is a product list, never a boolean.** LOPs shipped one
`subscription_valid` field, later had to split it into
`subscription_valid` + `products`, and in the gap raised the boolean's
threshold — refusing $5 patrons *their own product* for four months. Mint
`{products: [...], tier, exp}` from the first token. If a compatibility
fallback for older tokens ever becomes necessary, **give it a sunset date
tied to maximum token lifetime**: theirs has none, so any pre-`products`
token still grants everything.

**Fail open on unreadable claims, fail closed on unknown products.** Two
different defaults, deliberately. A client that cannot parse its own
entitlement lets the user through — it must never invent a lockout the
backend did not decide, and it only reads the claim to *name the missing
tier* in a refusal. The Worker does the opposite: a package with no access
annotation is treated as gated, not open.

**Sign the token asymmetrically (EdDSA or RS256) with a JWKS endpoint.**
LOPs verifies HS256 against a shared `JWT_SECRET`, which means the Worker
holds the *signing* key and a leak at the edge can mint any entitlement.
Asymmetric keeps only a public key at the edge, and it is what makes an
issuer allowlist mean anything.

**Plan revocation before launch, not after.** Short access tokens with a
refresh that re-checks entitlement is the cheapest form and also handles a
lapsed patron for free. A long-lived token with no deny-list cannot be
withdrawn once leaked.

**The heavier option worth considering: our own OAuth 2.1 IdP**, with
Patreon and Gumroad upstream of it rather than brokered per request. Costs
more to build; buys real PKCE (no secret anywhere in the client path),
token lifetimes we control, and **one sign-in across everything** — the
updater, and anything else we ship later that needs identity. LOPs took
this route and it is the part of their design that has aged best. If gating
is ever more than a single yes/no, start here rather than migrating to it.

### 3.2 The bucket — gate a prefix, not a host

Keep one host. Free stays at `fnstools/v*/…` served publicly as today; paid
goes to `fnstools/plus/v*/…`, **not** publicly readable, reachable only
through the Worker route above.

The reason to gate a prefix rather than stand up a second host is
`ExtUpdater._artifactRel()`: it derives an artifact's path by *stripping the
manifest's `base_url` off the pinned URL* and falling back to
`<release>/<name>.tox`. Everything is then re-based onto the **configured**
`Baseurl` — which is what makes the local `file://` and mirror test rails work
at all. A second host breaks that stripping and forces a per-package base
through `_onManifest`, `_needed` and `_copyLocal`. A prefix costs nothing.

Streaming through the Worker beats 302-ing to a presigned S3 URL: no signature
in a query string (which would also fight the cache policy in `upload.py`), one
hop, and no dependency on whether `webclientDAT` follows cross-host redirects —
which is unverified.

### 3.3 TouchDesigner — the small part

1. **`catalog.json`** gains per-package entitlement metadata (curated, like
   `recommended`). **`access` NAMES A TIER, it is not a flag** — see §9.3;
   an earlier draft of this line had a flat `free | patron | license` enum and
   the multi-tier decision invalidated it:

   ```json
   "access":  "free" | "<tier-id>",      // which tier covers this package
   "license": "gumroad:<product_id>",    // optional, per-tool key (§9.4)
   "seats":   null                        // per-package, see §9.5 -- NOT a
                                          // global constant
   ```

   The tier-id → packages map stays **server-side**. A client-side copy would
   have to ship, and would then be the second place the answer lives.
2. **`build_manifest.py`** copies `access` into each package record, points
   gated artifacts' `url` at the `plus/` prefix, and derives a top-level
   `plus: [...]` list the way it already derives `starter`.
3. **`ExtUpdater._download()`** takes the two kwargs the vendored downloader
   already accepts — `authType='oauth2', oauth2Token=<download token>` — and
   passes them **only** for gated artifacts.
4. **`ExtUpdater._needed()`** skips gated packages when no entitlement is held,
   so a refresh does not queue downloads that will 403. (`_verifyFetched` would
   catch an error page on sha256, but not asking is better than catching.)
   While there: **check size, then hash.** The manifest already carries
   `artifact.bytes`; comparing it first turns a truncated download or an error
   page into a cheap, specific failure instead of an opaque hash mismatch. The
   Worker should also compare the real R2 object size against the manifest's
   before streaming a gated artifact — LOPs does both, we do neither.
5. **A new auth surface** — its own `FNS_Auth`, or a page on `FNS_Updater`:
   *Connect Patreon* (pulse), *License Key* + *Redeem*, a status readout
   (tier, expiry), *Sign Out*.
6. **The loopback listener** copies `ConfigRegistryExt`'s pattern verbatim,
   with a ~120 s idle instead of 600 and a shutdown on first good callback.

## 4. How much of this unifies with the public rail

Almost all of it. The gated path is the same pipeline with one extra field,
one path prefix, and two kwargs. Everything expensive stays shared.

### 4.1 Stage by stage

| Stage | Unified? | What differs |
|---|---|---|
| Authoring, `Pkgversion` bump, `pi_suspect` identity | **fully** | nothing — a paid tool is authored and versioned like any other |
| `.tox` export into `packaging/dist/` | **fully** | nothing; same non-reproducible bytes, same `sha256` |
| `build_manifest.py` derive + `catalog.json` merge | **+1 field** | `access` rides along exactly like `recommended`; the artifact `url` gets the gated prefix |
| `manifest.json` | **fully — ONE manifest** | gated packages are rows in the same public file |
| `publish.py Stage()` | **~all** | one path branch when copying into `<release>/`. Hash verify, bump guard, rails, rolling copy all unchanged — and the bump guard covers gated packages for free, because it compares manifests, not bucket state |
| `upload.py` write path | **fully** | wrangler writes through the account API; public-read is a *bucket/route* property, not an upload one |
| `upload.py` read-back (`_remoteHas`, `prune`) | **breaks** | both ask the *public* URL — see §7 |
| Cache policy (immutable / `no-cache`) | **fully** | a gated object is still release-pinned and still immutable |
| `_fetchManifest()` | **fully** | the manifest stays public and unauthenticated |
| `Compare()` | **fully** | it reads `Pkgversion` off installed components; where the bytes came from is irrelevant to it |
| `_needed()` | **+1 filter** | skip gated packages when unentitled |
| `_download()` | **+2 kwargs** | `authType` / `oauth2Token`, conditional on `access` |
| downloader machinery — `AbortAll` reset, `_later` frame-deferral, `_pump` queue, 45 s watchdog, `Maxdownloads` | **fully** | nothing. This is the expensive, trap-laden part (PackagingScheme §5) and it is shared verbatim |
| `_verifyFetched()` sha256 | **fully** | same integrity rail |
| the palette store | **fully** | flat; a gated `.tox` sits beside a free one, indistinguishable |
| **all of `InstallerExt`** — Plan, Install, `embedded`/`shared`/`project` binding, `RemoveTools`, `RecordInstalled` | **fully — zero changes** | it installs from the store and never learns how the bytes arrived |
| `_apply()`, `_replacePackage`, one-package-per-frame `_drain`, external-tox reload semantics | **fully** | nothing |
| self-update ordering (UPDATER last, detached `run()`) | **fully** | nothing; UPDATER is core and can never be gated |
| picker / configurator | **+ a card state** | locked card and an auth CTA; same manifest, same presets |
| website generator | **+ a badge** | "support to unlock" in place of an install line |
| local `file://` / `publish/` test rail | **for everything but auth** | it bypasses the gate by construction — see §7 |

### 4.2 The line that cannot be unified

**Verification and authorisation are different things.** The free rail
verifies bytes (`sha256`) and authorises nobody — deliberately, because
everything is public. Gated bytes need an authorisation decision *before*
they move, and §2 says that decision cannot live in the client.

So the broker is strictly **additive**: a new component standing beside the
pipeline, not a modification of it. That is the entire genuine divergence.

### 4.3 One release, not two

The biggest unification decision is nearly free, and worth making
explicitly: **one manifest, one release label, one changelog, one cadence.**
Gated packages ship inside the same `v3.x` as everything else.

A separate paid release cycle would fork the runbook, the `CHANGELOG.md`
that `upload.py:_changelogReleases()` parses, the bump guard's
previous-manifest comparison, and the prune logic — for no benefit. The
price of staying unified is that paid packages' **names, descriptions,
versions and hashes become public**. That is decision #2 in §9, and the
answer should be yes: the list is marketing, and a picker that hides them
lies about what the toolkit contains.

It also buys one good behaviour for free — a logged-out user's **Check for
Updates** still works, still costs one small JSON, and can honestly report
"2 patron tools have updates" with no second code path.

### 4.4 The obvious "unify harder" option, and why not

Route *everything* through the Worker so there is one delivery path and
free downloads get analytics too. Recommend against it: that puts a compute
hop and a new failure mode in front of the free rail, which today is R2 plus
CDN and has nothing in it we could be called on to debug. Front the gated
prefix only.

### 4.5 Two of the fixes improve the free rail anyway

- `_remoteHas()` becoming an **authenticated** existence check is more
  correct for public objects too. Today an r2.dev bot-filter 403, or any CDN
  hiccup, silently answers "not there" and re-uploads.
- `Compare()` gaining a `gated` state generalises the existing `locked`
  state — "newer exists, but this copy must not be written" and "newer
  exists, but you are not entitled to it" are the same shape of answer.

## 5. Where the token lives — a real hazard

**Not a custom par, and not the ConfigRegistry JSON.** Per
[ConfigScope.md](ConfigScope.md):

- Under **`project` scope** the roaming JSON is never written and *the .toe is
  the whole store*. A credential on a custom par would be **saved into the
  `.toe`** — the file people share, commit, and hand to clients.
- Under **`global` scope** it lands in the shared roaming JSON, where `SaveAll`
  is last-writer-wins across every project on the machine.
- `Excludepars` / `Persistpars` are per-tool opt-outs. **There is no
  "always global, never project" hatch**, so nothing structurally prevents the
  leak — it would rest on remembering to set a flag.

→ **Put the credential in the OS keystore** — Windows DPAPI, macOS Keychain —
so it is machine-locked and user-locked and never exists as readable bytes in
the project tree at all. LOPs does this (`secure_storage_windows.py` /
`_macos.py`, stdlib `ctypes` and `subprocess`, no pip dependency), and it is
strictly better than the plaintext sidecar this section originally proposed.

Non-secret companions — tier label, expiry, last-checked — can sit in a
machine-local JSON beside the store (`<userPaletteFolder>/FNStools_ext/`), so
the UI can render "your tier: X" without touching the keystore on every cook.
Never a Patreon refresh token anywhere on the client. Never in a `.toe`, a
`.tox`, or git.

**One TD-specific trap comes with this**: the keystore call must resolve any
`mod()`/operator lookup on the main thread before a worker touches it. LOPs
hit exactly that and added a `prime()` step. Our fetch path is the Web Client
DAT rather than worker threads (§3.3), so this only applies to the keystore
write itself — but it is the one place the gated path leaves TD's async
operators and touches blocking OS APIs.

## 5b. Code we may reuse — permission granted 2026-08-26

DOTsimulate gave permission to scour and reuse from `tox_updater` 0.4.1 and
`TDAsyncIO`, both loaded into the dev project from outside the repo. Recorded
here because permission and provenance are perishable knowledge, and because
two of these modules are things this document otherwise says we would write.

| Module | ~Size | Verdict |
|---|---|---|
| `secure_storage` + `_windows` + `_macos` | 19 KB | **Lift.** DPAPI via raw `ctypes`, Keychain via `subprocess`, **zero pip deps.** Exactly what §5 specifies. Also ships `get/set_last_update_check` and `save/load_registry_cache` — the manifest-cache pattern [RailHardening.md](RailHardening.md) §2.1 wants |
| `catalog_contract` | 5 KB | **Lift.** Pure, no TD imports, carries `verify_content()` = size then hash (§3.3) |
| `auth_manager` | 19 KB | Reference. The PKCE logic ports; **the threading does not** |
| `webserver_callbacks` | 12 KB | Reference for the loopback shape |
| `ToxUpdaterEXT`, `dot_chat_util`, `dot_lop_utils` | 145 KB | Their model and furniture. Not ours |

**Three cautions that travel with it.**

- **The copy on hand is 0.4.1; the freeze fix is 0.4.2.** Their own map records
  the `_on_oauth_callback` → `_begin_token_exchange` → `_on_token_exchanged`
  fix as *"pushed, never executed"* at 0.4.2. So this copy is the **pre-fix**
  version, where the blocking token exchange ran inline on the main thread.
  That is the bug, not the pattern — do not copy the callback threading.
- **`secure_storage._get_backend()` uses `mod('secure_storage_windows')`**, a
  TD DAT sibling import. That is the `mod()` main-thread trap they added a
  `prime()` step for; resolve it on the main thread before anything else
  touches it.
- **`TDAsyncIO` is a derivative**, headed *"Based on TDAsyncIO by Motoki
  Sonoda"*. Permission from DOTsimulate covers DOTsimulate's work; check the
  upstream licence before it ships in a distributed tox.

## 6. What this does not solve — be honest about it

A `.tox` that has been downloaded is a file the user can copy and re-post.
Gating controls **distribution, not redistribution**. The realistic goal is
friction plus a supported update channel that only supporters get, not DRM.

**Do not solve it with per-user watermarked artifacts.** A Worker could mint
per-user bytes, but per-user bytes means a per-user hash, and the entire update
scheme rests on the manifest pinning one `sha256` that `_verifyFetched` and
`_needed` compare against. Watermarking would break the integrity rail to slow
down a leak it cannot stop. Not worth it.

## 7. Traps waiting in the current code

- **`upload.py:_remoteHas()` decides "already uploaded" with an unauthenticated
  public HEAD.** Against a private prefix that always 404s, so every publish
  re-uploads every gated artifact. Either use an authenticated existence check
  or accept the re-upload for the small paid set — but know which.
- **`upload.py:prune()` enumerates a doomed release's keys from that release's
  own manifest over public HTTP.** Gated keys would never be enumerated and
  would sit in the bucket forever. Gated key lists must come from the local
  staged tree instead.
- **`Baseurl` is a user-editable par and `_localBase()` accepts bare paths and
  `file://`.** Anyone can point the updater at a local tree and bypass the gate
  for artifacts they already have. This is the escape hatch the whole offline
  test rail depends on — do not close it, just know it is there.
- **Patreon rate limits**: 100 req / 2 s per client, 100 req/min per token, and
  2000 4xx responses in 10 minutes triggers a 30-minute edge block. Cache
  entitlement server-side; a retry loop must never reach Patreon.
- **A free follower is not a patron.** `currently_entitled_tiers` is empty for
  them. Entitlement must be tier-id based, never "has a membership". A lapsed
  supporter returns a membership with `patron_status: former_patron`.
- **Testing cannot use the `file://` rail** — it bypasses auth by construction.
  Gated paths need a real staging bucket and a real test patron.
- **Cache policy is already right and must stay that way**: `manifest.json` is
  `no-cache`, release-pinned artifacts are `immutable`. Bearer headers keep it
  that way; URL-embedded tokens would not.

## 8. Rough effort

| Piece | Estimate |
|---|---|
| Worker: Patreon OAuth + Gumroad redeem + KV + gated R2 route | 1–2 days, incl. Patreon client registration and secrets |
| `catalog.json` / `build_manifest.py` / `publish.py` / `upload.py` | ~½ day; the risk is the existence check and prune, not the field |
| TD: `_download` kwargs, `_needed` skip, auth sidecar, loopback callback, par page | 1–2 days, mostly UI and callback lifecycle |
| Picker "locked" state + website messaging | ~½ day |
| Testing against a real bucket and a real test patron | ~1 day |

**≈1 week focused.** The Worker is the piece that has to be right; the
TouchDesigner side is genuinely small because the chokepoint is single and the
downloader already carries auth.

## 9. Decisions needed before any of this is built

**Answered 2026-08-27.** Four of five; the fifth is deliberately open.

1. **DECIDED: one host, gated prefix** (§3.2). Keeps `_artifactRel()`'s
   base-stripping intact and the `file://` mirror rail working.
2. **DECIDED: visible and locked** in the public manifest. The list is
   marketing, and a picker that hides them lies about what the toolkit is.
3. **DECIDED: multiple Patreon tiers, not one gate.** This is a change from
   what §3 assumed, and it has consequences:
   - `access` in `catalog.json` cannot be a yes/no. It names a **tier**, and
     the Worker maps tier → the set of packages that tier covers. Keep the map
     server-side: a client-side map would have to ship, and it would then be
     the second place the answer lives (LOPs' `DEFAULT_PRODUCT` lesson).
   - The `products` claim (§3.1) is what makes this work at all — a boolean
     could not express it. This is the second reason not to ship one.
   - A refusal must name **which** tier is missing, not just "not entitled",
     which is why the client reads (but never enforces) its own claim.
4. **DECIDED: one Gumroad key per tool.** So `/gumroad/redeem` takes a
   `product_id` per tool, the claim accumulates entitlements one key at a
   time, and **the UI is a list, not a single field** — a user with five tools
   holds five keys and must be able to see, add and remove them individually.
   Worth designing the auth surface around that from the start; a single
   "License Key" string par does not survive this decision.
5. **OPEN: seat policy** — and it "might differ per product", so whatever it
   becomes it is **per-package data, not a global constant**. Leave room for it
   in the catalog rather than hard-coding a cap. `increment_uses_count` gives
   the counter; nothing decides what to do at the cap yet.

## 10. Sources

- [Patreon API v2 — OAuth, identity, memberships, rate limits](https://docs.patreon.com/)
- [Gumroad license keys](https://gumroad.com/help/article/76-license-keys) ·
  [Gumroad API](https://gumroad.com/api) ·
  [verify walkthrough](https://dev.to/zsevic/license-key-verification-with-gumroad-api-58f9)
- [Cloudflare R2 presigned URLs](https://developers.cloudflare.com/r2/api/s3/presigned-urls/) ·
  [Securely access assets with R2 + Workers](https://developers.cloudflare.com/workers/tutorials/upload-assets-with-r2/)
- [TD Web Client DAT](https://docs.derivative.ca/Web_Client_DAT) ·
  [TD Web Server DAT](https://docs.derivative.ca/Web_Server_DAT)

## 10. Build status — 2026-08-27

| Piece | State |
|---|---|
| Entitlement metadata (`access` names a tier, `license`, `seats`) | **built** — `catalog.json`, `build_manifest.py` |
| Gated artifacts routed to the `plus/` prefix on the same host | **built** — `build_manifest.py:PLUS_PREFIX` |
| The Worker: Patreon OAuth, Gumroad redeem, token mint, gated R2 read | **built, untested against reality** — `worker/`, 28 offline checks |
| Ed25519 signing, revocable opaque device tokens, 15-min download tokens | **built** |
| TD: keystore (DPAPI + Keychain, dependency-free) | **built** — `FNSTools/FNS_Updater/secure_storage*.py`, DPAPI round-trip verified live |
| TD: sign-in, licence redeem, entitlement (`ExtAuth`) | **built** — second extension on `FNS_Updater`, Web Client DAT transport |
| TD: gated download path | **built** — `_needed` skips unentitled and reports them, one token per pass, bearer only on gated calls |
| The site: Plus marked in the catalogue, docs and picker, plus a `/plus/` page | **built** — `website/`, one `access` field drives all five surfaces |
| Staging/upload of the gated prefix | **not started** |
| Deployment, Patreon client, Gumroad product, tier ids | **needs the owner's accounts** — `worker/README.md` |

**One bug the tests caught, worth remembering.** A cached session did not
recompute its product list, so adding a package to a tier would not have
reached signed-in supporters for up to six hours. Only the *Patreon call*
is rate-limited and therefore cached; mapping tiers to packages is local and
free, and is now always redone. The same shape will recur anywhere a cache
wraps more than the expensive part.

**Still open:** seat policy (§9.5), and `plus/` must be confirmed
non-public before any of this is announced — an unauthenticated GET is the
only proof that the gate is not decorative.

**Placeholder, deliberately:** `Gateurl` defaults to `https://gate.functionstore.tools`
and `catalog.json` carries `PLACEHOLDER_TIER` for `FNS_TimelineTools`. Both
are one-line swaps once the real tier id and hostname exist.

**One design point the client forced.** Gated artifacts stay on the STORAGE
host under `plus/`, not on the gate's hostname, so the Worker takes two
routes. `ExtUpdater._artifactRel()` derives a path by stripping the
manifest's `base_url` and re-bases onto the *configured* base — which is
what makes the `file://` and mirror rails work. A different hostname for
gated rows would break that stripping for paid packages only, which is the
worst place for it to break.

