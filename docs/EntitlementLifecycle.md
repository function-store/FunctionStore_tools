---
status: open
summary: How an entitlement begins, is re-checked and ends — the Gumroad perpetual-licence decision, revocation, session lifetime, and the failure-kind split. The §4–§5 work is built and offline-tested; §2.2 and §3.1 stay open.
since: 2026-08-27 (audit of the undeployed gate); §4–§5 built 2026-08-28
skill: fns-packaging
---

# Entitlement lifecycle

[GatedDeliveryResearch.md](GatedDeliveryResearch.md) covers how entitlement is
*granted* — Patreon OAuth, Gumroad keys, the Worker that holds the client
secret. This document covers what happens **afterwards**: what gets re-checked,
how often, and how an entitlement is supposed to end.

> **BUILT, NOT DEPLOYED.** The gate is written and tested offline
> (`worker/`, 62 checks) and is not deployed. The decisions in §1 and §2 are
> taken; the §4 and §5 work was built 2026-08-28 (see the *Built* notes in
> each section). All 48 packages in the current manifest are `access: free`,
> so no user is affected by any of it yet. §2.2 and §3.1 remain open.

## 1. Two kinds of entitlement, deliberately different

The gate issues one device token, but what sits behind it comes in two
flavours and they do **not** age the same way.

| | Patreon | Gumroad |
|---|---|---|
| Nature | **Subscription** — a live claim | **Perpetual licence** — a completed purchase |
| Ends when | the supporter lapses or changes tier | never |
| Re-checked | every 6 h, via the gate | **never, by decision** (§2) |
| Session may expire | yes | **no** (§3) |

Conflating them is the mistake this table exists to prevent. DOTsimulate
shipped one `subscription_valid` boolean, later had to split it, and refused
$5 patrons their own product for four months in the gap
([DistributionComparison.md](DistributionComparison.md)). The same class of
error here would be a single session-expiry policy applied to both.

## 2. Gumroad is a perpetual offline licence — decision, 2026-08-27

**A Gumroad key is bought once and owned forever.** Verification happens at
redemption and never again. A refund after redemption keeps working.

That last sentence is the cost, and it is **accepted**: Gumroad's refund
window is short, the loss is a rounding error against the machinery required
to police it, and every mechanism that would close it charges an honest
customer something (see §2.1). The purchase is theirs.

### 2.1 Considered and closed: re-verifying Gumroad on a cycle

The audit proposed re-verifying each `gumroad_products` entry on the same 6-hour
cycle as Patreon, dropping refunded or cancelled ones. **Rejected**, and
recorded here so it is not re-raised:

* It contradicts §2. A perpetual licence that phones home is not perpetual.
* Under `licenses/verify` the uses count is the **activation counter**.
  Re-verifying four times a day with `increment_uses_count: 'true'` would
  inflate every paying customer's counter into their own activation ceiling —
  the entitlement check itself becoming the thing that makes customers look
  like key-sharers.
* It would need a network round trip on a rail whose whole point is not
  needing one.

**Do not re-open this without also changing §2.**

### 2.2 Open question: how literal is "offline"?

Today "offline" means *no recurring check*, not *works with no network*. A
Gumroad customer still needs the gate for `POST /token/download` on every
update pass and for every `GET /plus/` artifact.

If it is ever meant literally, the shape is different and better: the gate
issues a **signed perpetual entitlement** at redemption, the client verifies it
against the pinned Ed25519 public key with no round trip, and no KV row is
load-bearing (which also answers §3.1). Not decided.

## 3. What this forbids

Constraints for whoever implements the session lifecycle. Each one exists
because the obvious implementation gets it wrong.

* **Session expiry must be per-kind.** A blanket TTL — the obvious fix for an
  unbounded KV namespace — would silently revoke a perpetual licence from any
  customer who did not open TouchDesigner for the length of the window. `kind`
  is already stored on the session (`'patreon'` / `'gumroad'`); branch on it,
  or on a non-empty `gumroad_products`.
* **A Patreon session may expire; the artifacts it already fetched may not.**
  A lapsed supporter correctly gets nothing new and correctly keeps everything
  installed. The store is theirs.
* **The client never decides a subscription claim.** It reads its own
  entitlement list only to name the missing tier in a refusal. This is
  unchanged. A *perpetual* claim under §2.2 would be the one exception, and
  only because a signed claim that never changes cannot go stale.

### 3.1 Durability is now the question that matters

Under §2 the KV row **is** the licence. It is a single unreplicated entry with
no backup and no recovery path: lose it to eviction, a migration or a
mis-click, and the customer's only remedy is to re-redeem — which burns
another activation (§5.2). Either back the rows up, or move the licence onto
the customer's machine as a signed claim (§2.2).

## 4. Revocation — found open, closed 2026-08-28

As found by the audit: `loadSession` honours a `revoked` flag and the test
suite exercises it, so it read as a working feature. **Nothing in the
codebase ever set it.**
There is no route that could — the gate answers exactly six paths, none of
them a revoke.

`ExtAuth.SignOut()` compounds it: it clears the local keystore and never
contacts the gate. The device token stays valid forever. **Signing out does
not sign you out**, which is a promise the button's label makes and the code
does not keep.

What that costs a user: a laptop stolen at a festival, a machine sold, a
studio's house rig signed into once — in every case the honest answer today is
"that install can still download your paid packages, and neither you nor we
can stop it." Not because it is hard, but because there is no path at all;
even with dashboard access it means hand-hunting a KV key.

**Approved shape:** a `POST /session/revoke` that `SignOut()` calls before
clearing the local copy, plus a per-kind TTL on session writes (§3) that
renews itself — `refreshEntitlement` already writes whenever the 6-hour cache
is stale, so an install in use never expires and an abandoned one ages out.
Optionally a device list, so "I lost my laptop" is something a customer can
act on themselves.

> **Built 2026-08-28.** `POST /session/revoke` revokes the bearer's own
> session — holding the token is the only credential needed, which is
> exactly the stolen-laptop case; the answer is the same whether the token
> existed or not, so the route is not a token oracle. The revoked row is
> kept 30 days (a replayed token reads *revoked*, not *unknown*), then ages
> out. `SignOut()` fires the revoke best-effort before clearing the
> keystore. Session writes now carry the per-kind TTL: Patreon-only rows
> live 180 days and self-renew in use; any row with `gumroad_products` never
> expires (§2). The device list is still unbuilt.

## 5. Two lifecycle holes — found open, closed 2026-08-28

Both descriptions below record the code **as the audit found it**; the
*Built* note under each records what replaced it.

### 5.1 A dead Patreon grant is indistinguishable from an outage

`patreonExchange` discards the failure reason:

```js
if (!r.ok) return null;
```

Patreon returns **400 `invalid_grant`** for a refresh token that has been
revoked or has expired, and **5xx / timeout** for an outage. Both collapse to
`null`. `refreshEntitlement` then keeps the last known tiers *and* resets
`checked_at`, so six hours later it does the same thing again — indefinitely.

The rule it is applying — *a failed lookup is not a revocation* — is correct.
It is applied to **all** failures when it should only cover transient ones.

Consequences:

* A supporter who revokes FNSTools in their Patreon account settings keeps
  full entitlement permanently. That is the one escape hatch a user has, and
  it does not work.
* A refresh token that expires or is rotated away has the same effect.
* **The operationally dangerous one:** rotate `PATREON_CLIENT_SECRET` and get
  it wrong, and every session in the fleet silently freezes at its last known
  entitlement. The misconfiguration presents as "everything is fine."

**Fix:** keep the status. `4xx invalid_grant` is permanent — clear the tiers.
`5xx` / network is transient — keep the last answer and back off *shorter*
than the full window. And split `checked_at`, which currently means both "last
attempt" and "last success", so a session can express "not actually verified
in 30 days, stop trusting it."

> **Built 2026-08-28.** `patreonExchange` keeps the failure kind: 4xx clears
> the tiers *and drops the dead refresh token*; 5xx/network keeps the last
> answer and retries after 30 minutes instead of six hours. `verified_at`
> (last success) now sits beside `checked_at` (last attempt), and a session
> unverified for 30 days stops being trusted — the backstop that makes the
> transient forgiveness safe. Gumroad claims are exempt from the backstop by
> §2. Rows that predate `verified_at` fall back to `checked_at`, which meant
> "last success" under the old code.

### 5.2 The uses count is spent on checks, not activations

`handleGumroadRedeem` sends `increment_uses_count: 'true'` on **every**
verification, including pure re-checks. Under §2 that counter is the
activation counter for a perpetual licence, so every retry after a dropped
connection, every re-redeem to extend a session, and every recovery from a
lost KV row (§3.1) spends one. A customer who reinstalls a few times over two
years can hit their own ceiling on a licence they own outright, and the remedy
is an email to us.

The code already computes the right test — `!session.gumroad_products.includes(product)`
— it just runs **after** the increment. Load the session first, verify with
`'false'` for a re-check, and pass `'true'` only for a genuine first
activation.

The endpoint is also unauthenticated and unthrottled, which makes the counter
inflatable by anyone holding a customer's key — and the customer is then the
one who looks like the abuser. Rate-limit on `cf-connecting-ip` plus a
separate per-key cap; a key tried from many addresses is the signal worth
having.

The gate already returns `uses` in the redeem response and the client discards
it. Under §2 it is the one number a customer would want to see.

> **Built 2026-08-28.** The session is loaded *before* Gumroad is called: a
> key the session already holds verifies with `increment_uses_count:
> 'false'`, and only a genuine first activation on the install increments.
> The endpoint is throttled before it proxies anything — per source address
> *and* per key (10 per hour each), so a key sprayed from many addresses is
> refused rather than counted against the customer. Surfacing `uses` in the
> client UI is still unbuilt.

## 6. Sources

* [GatedDeliveryResearch.md](GatedDeliveryResearch.md) — how entitlement is granted
* [DistributionComparison.md](DistributionComparison.md) — the outages these rules were bought with
* `worker/src/index.js`, `FNSTools/FNS_Updater/ExtAuth.py` — the code described here
