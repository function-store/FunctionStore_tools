# fnstools-gate

The entitlement gate for paid packages. Turns a Patreon membership or a
Gumroad licence key into a short-lived download token, and serves the
private `fnstools/plus/` prefix to holders of one.

**Free packages never come through here.** They stay on the public prefix
and are served straight off the CDN, so the free rail keeps working with no
compute hop in front of it. Design and reasoning:
[docs/GatedDeliveryResearch.md](../docs/GatedDeliveryResearch.md).

Nothing here is deployed yet.

---

## What you have to do (none of it can be done for you)

Each of these needs an account only you hold.

1. **Register a Patreon client** at the Patreon developer portal. Set the
   redirect URI to `https://gate.functionstore.tools/patreon/callback` — *the
   Worker's own address, not localhost.* The Worker holds the client secret
   because Patreon's token exchange requires one and offers no PKCE; that
   single fact is why this service exists rather than TouchDesigner talking
   to Patreon directly.

2. **Create the KV namespace** and put its id in `wrangler.toml`:
   ```bash
   npx wrangler kv namespace create SESSIONS
   ```

3. **Generate the signing pair** and set the four secrets:
   ```bash
   openssl genpkey -algorithm ed25519 -out fns.pem
   npx wrangler secret put JWT_PRIVATE_KEY   # openssl pkey -in fns.pem -outform DER | base64 -w0
   npx wrangler secret put JWT_PUBLIC_KEY    # openssl pkey -in fns.pem -pubout -outform DER | base64 -w0
   npx wrangler secret put PATREON_CLIENT_ID
   npx wrangler secret put PATREON_CLIENT_SECRET
   ```
   Keep `fns.pem` out of this repo. Signing is asymmetric so that verifying
   never needs the private key — splitting the issuer out later then costs
   nothing, and reading the verifying environment mints nothing.

4. **Fill in `TIERS`** in `wrangler.toml` with your real Patreon tier ids.
   They are numeric strings from the API, *not* display names — a display
   name can be renamed at any time and is not unique. Sign in once through
   `/patreon/start`; a refusal returns the `tiers` array it saw.

5. **Make the gated path private.** Public reads of
   `storage.functionstore.tools/fnstools/plus/*` must be blocked (a Cloudflare
   rule on the zone until the Worker route owns the path), or the gate is
   decorative. `packaging/upload.py` plants a canary there and FAILS the
   upload run if the public rail serves it, so this is enforced, not just
   a checklist item.

6. **Point `gate.functionstore.tools`** at the Worker: the zone needs a
   PROXIED DNS record for that hostname (any target -- the route
   intercepts before the origin), and the route in `wrangler.toml`
   does the rest. `custom_domain = true` is NOT usable here: it
   refuses a hostname that already has a DNS record (code 100117).

## Routes

| Route | Auth | Does |
|---|---|---|
| `GET /health` | none | liveness |
| `GET /patreon/start?port=N` | none | 302 to Patreon; loopback port + CSRF nonce ride in `state` |
| `GET /patreon/callback` | none | exchange, read tiers, mint a device token, 302 back to `127.0.0.1:N` |
| `POST /gumroad/redeem` | none | verify a key, **extend** an existing session rather than replace it |
| `POST /token/download` | device token | re-check entitlement (cached), mint a 15-minute signed token |
| `GET /fnstools/plus/<release>/<Pkg>.tox` | download token | check the product, stream from R2 |

## The rules this encodes

Each was paid for by an outage, mostly someone else's
([docs/DistributionComparison.md](../docs/DistributionComparison.md)).

- **The claim is a product list, never a boolean.** DOTsimulate shipped one
  `subscription_valid` field, later had to split it, and in the gap refused
  $5 patrons their own product for four months.
- **Entitlement is tier-based, never "has a membership."** A free follower
  has an empty `currently_entitled_tiers`; a lapsed supporter is a
  `former_patron`. Both correctly get nothing new — and keep everything
  already installed, because the store is theirs.
- **A failed lookup is not a revocation.** Patreon being down keeps the
  last known answer rather than stripping a paying supporter mid-show.
- **Tokens are short and revocable.** Delete the KV entry to cut off a
  device; the download token expires on its own within minutes.
- **Fail closed on an unknown package**, and leave failing *open* to the
  client — which reads its claim only to name the missing tier in a
  refusal, never to decide.
- **The tier map lives here and only here.** A client-side copy would ship,
  and would then be the second place the answer lives.
- **Refusals name what is missing.** "Not entitled" tells a paying customer
  nothing and generates a support ticket every time.

## What this does not solve

A `.tox` that has been downloaded is a file someone can re-post. This
controls distribution, not redistribution; the goal is friction plus an
update channel only supporters get, not DRM. Do **not** try to close it
with per-user watermarked artifacts: per-user bytes mean a per-user hash,
and the whole update scheme rests on the manifest pinning one `sha256`.
