/**
 * FNSTools entitlement gate.
 *
 * One Worker, three jobs:
 *   1. turn a Patreon membership or a Gumroad licence key into an FNS
 *      device token  (/patreon/*, /gumroad/redeem)
 *   2. turn a device token into a short-lived download token, re-checking
 *      entitlement as it goes                              (/token/download)
 *   3. serve gated artifacts from the private `fnstools/plus/` prefix,
 *      and refuse everything else            (/fnstools/plus/...)
 *
 * WHAT THIS IS NOT. Free artifacts never come through here. They sit under
 * the public prefix and are served straight off the CDN, so the free rail
 * keeps working with no compute hop and no failure mode we would have to
 * debug. See docs/RailHardening.md 2.4.
 *
 * DESIGN RULES, each paid for by someone else's outage
 * (docs/DistributionComparison.md):
 *
 *   * The claim is a PRODUCT LIST, never a boolean. DOTsimulate shipped one
 *     `subscription_valid` field, later had to split it, and in the gap
 *     refused $5 patrons their own product for four months.
 *   * Signing is ASYMMETRIC (Ed25519). Verification never needs the private
 *     key, so splitting the issuer out later costs nothing and a read of
 *     the verifying environment mints nothing.
 *   * Tokens are SHORT and revocable. A download token lives minutes; the
 *     device token behind it is an opaque KV key that can be deleted. A
 *     long-lived unrevocable token cannot be withdrawn once leaked.
 *   * FAIL CLOSED on an unknown package: a manifest row we cannot map to a
 *     tier is treated as gated, not as free.
 *   * FAIL OPEN is the CLIENT's job, not ours -- it reads its claim only to
 *     name the missing tier in a refusal. We always decide.
 *   * The tier -> packages map lives HERE and only here. A client-side copy
 *     would ship, and would then be the second place the answer lives.
 */

const TEXT = { 'content-type': 'text/plain; charset=utf-8' };
const JSON_H = { 'content-type': 'application/json; charset=utf-8' };

// A download token is deliberately short. Long enough for a slow update
// pass over many packages, short enough that a leaked one is worthless by
// the time it is noticed.
const DOWNLOAD_TOKEN_TTL = 15 * 60;
// How long an entitlement answer may be reused before Patreon is asked
// again. Their limits are 100 req/2s per client and 100/min per token, and
// 2000 4xx in 10 minutes triggers a 30 minute block -- so a retry loop
// must never reach them. It never can: only this Worker talks to Patreon.
const ENTITLEMENT_TTL = 6 * 60 * 60;
// After a TRANSIENT refresh failure (Patreon down, network), retry sooner
// than the full cache window -- an outage should cost minutes of staleness,
// not a quarter of a day per attempt. See docs/EntitlementLifecycle.md 5.1.
const TRANSIENT_RETRY = 30 * 60;
// A Patreon session that has not been successfully verified for this long
// stops being trusted, whatever its cached tiers say. This is the backstop
// that makes "keep the last answer on a transient failure" safe: an outage
// is forgiven for days, not forever. Gumroad claims are exempt by decision
// (docs/EntitlementLifecycle.md 2 -- perpetual, never re-checked).
const STALE_TRUST_TTL = 30 * 24 * 60 * 60;
// Per-kind KV row lifetime (docs/EntitlementLifecycle.md 3): a Patreon
// session in use renews itself (refreshEntitlement writes whenever the 6 h
// cache is stale) and an abandoned one ages out. A Gumroad-flavoured
// session IS the licence and never expires. Revoked rows are kept long
// enough that a replayed token stays dead, then age out entirely.
const PATREON_SESSION_TTL = 180 * 24 * 60 * 60;
const REVOKED_ROW_TTL = 30 * 24 * 60 * 60;
// /gumroad/redeem is unauthenticated and proxies to Gumroad, so it is both
// a brute-force oracle and (because verification can spend an activation)
// a way to inflate a customer's uses count. Cheap KV counters close both:
// per source address AND per key -- one key tried from many addresses is
// exactly the signal worth refusing on.
const REDEEM_WINDOW = 60 * 60;
const REDEEM_LIMIT = 10;
// The sign-in redirect hands the loopback listener a ONE-TIME grant code,
// never the device token itself: a URL query string lands in browser
// history, and a long-lived credential must not sit where a history sync
// or a shared machine can read it back. The code is worthless once
// claimed and worthless within minutes regardless.
const GRANT_TTL = 120;

const PATREON_AUTH = 'https://www.patreon.com/oauth2/authorize';
const PATREON_TOKEN = 'https://www.patreon.com/api/oauth2/token';
const PATREON_IDENTITY =
  'https://www.patreon.com/api/oauth2/v2/identity' +
  '?include=memberships.currently_entitled_tiers' +
  '&fields%5Bmember%5D=patron_status';
const GUMROAD_VERIFY = 'https://api.gumroad.com/v2/licenses/verify';

// ---------------------------------------------------------------------------
// small helpers
// ---------------------------------------------------------------------------

const b64url = (buf) =>
  btoa(String.fromCharCode(...new Uint8Array(buf)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

const b64urlDecode = (s) => {
  const pad = s.replace(/-/g, '+').replace(/_/g, '/');
  const bin = atob(pad + '='.repeat((4 - (pad.length % 4)) % 4));
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
};

const enc = new TextEncoder();

function json(obj, status = 200, extra = {}) {
  return new Response(JSON.stringify(obj), {
    status, headers: { ...JSON_H, ...extra },
  });
}

/** A refusal that NAMES what is missing. "not entitled" tells a paying
 *  customer nothing and generates a support ticket every time. */
function refuse(status, code, message, extra = {}) {
  return json({ ok: false, error: code, message, ...extra }, status);
}

function randomToken() {
  const b = new Uint8Array(32);
  crypto.getRandomValues(b);
  return b64url(b.buffer);
}

async function sha256hex(s) {
  const d = await crypto.subtle.digest('SHA-256', enc.encode(s));
  return [...new Uint8Array(d)].map((x) => x.toString(16).padStart(2, '0')).join('');
}

// ---------------------------------------------------------------------------
// Ed25519 JWT -- sign here, verify anywhere with the public key alone
// ---------------------------------------------------------------------------

async function signingKey(env) {
  // PKCS#8, base64 (no PEM header), stored as a Worker secret.
  const raw = b64urlDecode(env.JWT_PRIVATE_KEY.replace(/\s+/g, ''));
  return crypto.subtle.importKey('pkcs8', raw, { name: 'Ed25519' }, false, ['sign']);
}

async function verifyingKey(env) {
  const raw = b64urlDecode(env.JWT_PUBLIC_KEY.replace(/\s+/g, ''));
  return crypto.subtle.importKey('spki', raw, { name: 'Ed25519' }, false, ['verify']);
}

async function mintJWT(env, claims, ttl) {
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: 'EdDSA', typ: 'JWT' };
  const payload = { ...claims, iss: 'fnstools', iat: now, exp: now + ttl };
  const body =
    b64url(enc.encode(JSON.stringify(header))) + '.' +
    b64url(enc.encode(JSON.stringify(payload)));
  const sig = await crypto.subtle.sign('Ed25519', await signingKey(env), enc.encode(body));
  return body + '.' + b64url(sig);
}

/** Returns the payload, or null. Never throws on malformed input: a
 *  garbage Authorization header is a 401, not a 500. */
async function readJWT(env, token) {
  try {
    const [h, p, s] = String(token).split('.');
    if (!h || !p || !s) return null;
    const ok = await crypto.subtle.verify(
      'Ed25519', await verifyingKey(env), b64urlDecode(s), enc.encode(h + '.' + p));
    if (!ok) return null;
    const payload = JSON.parse(new TextDecoder().decode(b64urlDecode(p)));
    if (typeof payload.exp !== 'number' || payload.exp < Math.floor(Date.now() / 1000)) {
      return null;
    }
    return payload;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// the tier -> packages map
// ---------------------------------------------------------------------------

/** A JSON [vars] entry, or {} when it is absent or malformed.
 *
 *  Malformed must DEGRADE, never throw. GUMROAD_PRODUCTS used to be parsed
 *  inline with no guard while TIERS had one, so a typo in the Gumroad map
 *  500'd /token/download for EVERYONE -- including patrons whose
 *  entitlement has nothing to do with Gumroad. One broken variable must
 *  only cost the thing it configures.
 *
 *  Logged rather than swallowed: from the outside "entitles nothing" and
 *  "misconfigured" look identical, and only one of them is our fault. */
function jsonVar(env, name) {
  try {
    return JSON.parse(env[name] || '{}');
  } catch (err) {
    console.error('malformed [vars] entry', name, err && err.message);
    return {};
  }
}

/** TIERS is JSON in wrangler.toml [vars] so it is version-controlled and
 *  reviewable in a diff -- unlike a KV entry, which changes with no record
 *  of who changed it or why. */
function tierMap(env) {
  return jsonVar(env, 'TIERS');
}

/** Every package id this set of Patreon tier ids and Gumroad products
 *  entitles, as a flat list. This IS the `products` claim. */
function productsFor(env, { patreonTiers = [], gumroadProducts = [] }) {
  const map = tierMap(env);
  const out = new Set();
  for (const t of patreonTiers) for (const p of map[t] || []) out.add(p);
  // A Gumroad key is per-tool by decision, so the product id maps to
  // exactly the package it was bought for.
  const byLicence = jsonVar(env, 'GUMROAD_PRODUCTS');
  for (const g of gumroadProducts) if (byLicence[g]) out.add(byLicence[g]);
  return [...out].sort();
}

// ---------------------------------------------------------------------------
// sessions (KV) -- the device token is an opaque key, so it is revocable
// ---------------------------------------------------------------------------

const sessionKey = (token) => 'session:' + token;

async function loadSession(env, token) {
  if (!token) return null;
  const raw = await env.SESSIONS.get(sessionKey(token));
  if (!raw) return null;
  const s = JSON.parse(raw);
  return s.revoked ? null : s;
}

/** Per-kind row lifetime -- see docs/EntitlementLifecycle.md 3. A blanket
 *  TTL here would silently revoke a perpetual Gumroad licence from anyone
 *  who did not open TouchDesigner for the window; branching on the
 *  products list (not just `kind`) also covers the mixed account that
 *  started as Patreon and later redeemed a key. */
function sessionTtl(session) {
  if (session.revoked) return REVOKED_ROW_TTL;
  if ((session.gumroad_products || []).length) return null;   // perpetual
  return PATREON_SESSION_TTL;
}

async function saveSession(env, token, session) {
  const ttl = sessionTtl(session);
  await env.SESSIONS.put(sessionKey(token), JSON.stringify(session),
    ttl ? { expirationTtl: ttl } : undefined);
}

/** Small KV rate counter. Not atomic -- concurrent racers may each land a
 *  request or two past the line, which is fine: this exists to stop
 *  brute-force loops and counter inflation, not to bill anyone. */
async function overLimit(env, bucket, id) {
  if (!id) return false;
  const key = 'rl:' + bucket + ':' + await sha256hex(id);
  const n = parseInt(await env.SESSIONS.get(key) || '0', 10);
  if (n >= REDEEM_LIMIT) return true;
  await env.SESSIONS.put(key, String(n + 1), { expirationTtl: REDEEM_WINDOW });
  return false;
}

// ---------------------------------------------------------------------------
// Patreon
// ---------------------------------------------------------------------------

/** Currently-entitled tier ids for an access token. Empty for a free
 *  follower and for a former patron -- entitlement is TIER-BASED, never
 *  "has a membership", which is how a lapsed supporter keeps access. */
async function patreonTiers(env, accessToken) {
  const r = await fetch(PATREON_IDENTITY, {
    headers: { authorization: 'Bearer ' + accessToken },
  });
  if (!r.ok) return { ok: false, tiers: [], status: r.status };
  const doc = await r.json();
  const included = doc.included || [];
  const tiers = [];
  for (const item of included) {
    if (item.type !== 'member') continue;
    if ((item.attributes || {}).patron_status !== 'active_patron') continue;
    const rel = ((item.relationships || {}).currently_entitled_tiers || {}).data || [];
    for (const t of rel) tiers.push(String(t.id));
  }
  // The creator cannot pledge to their own campaign, so without this they
  // could never exercise their own gate end to end -- and an untested gate
  // is discovered by the first paying customer. Granting the TOP tier
  // rather than a bypass keeps them on the ordinary mapping: every gated
  // package is granted from its entry tier upward, so the top tier is in
  // every grant list by construction.
  const me = String(((doc.data || {}).id) || '');
  const creator = String(env.PATREON_CREATOR_USER_ID || '');
  const topTier = String(env.CREATOR_TIER || '');
  if (creator && topTier && me === creator && !tiers.includes(topTier)) {
    tiers.push(topTier);
  }
  return { ok: true, tiers: [...new Set(tiers)] };
}

/** {ok, tok} on success; {ok:false, permanent} on failure.
 *
 *  The DISTINCTION is the point (docs/EntitlementLifecycle.md 5.1): Patreon
 *  answers 4xx (invalid_grant) for a refresh token that was revoked or
 *  expired -- a fact about the grant, true tomorrow too -- and 5xx/timeout
 *  for an outage. Collapsing both to one "failed" made entitlement immortal:
 *  a supporter who revoked us in their Patreon settings kept access forever,
 *  and a botched client-secret rotation looked exactly like health. */
async function patreonExchange(env, params) {
  const body = new URLSearchParams({
    client_id: env.PATREON_CLIENT_ID,
    client_secret: env.PATREON_CLIENT_SECRET,
    ...params,
  });
  let r;
  try {
    r = await fetch(PATREON_TOKEN, {
      method: 'POST',
      headers: { 'content-type': 'application/x-www-form-urlencoded' },
      body,
    });
  } catch {
    return { ok: false, permanent: false };      // network: transient
  }
  if (!r.ok) return { ok: false, permanent: r.status >= 400 && r.status < 500 };
  return { ok: true, tok: await r.json() };
}

/** The tiers this session may be TRUSTED with right now. Cached tiers are
 *  honoured only while the session has actually been verified within
 *  STALE_TRUST_TTL -- the backstop that keeps "a failed lookup is not a
 *  revocation" from quietly becoming "entitlement never ends". Older rows
 *  predate verified_at; their checked_at meant "last success" then. */
function trustedTiers(session, now) {
  const lastGood = session.verified_at || session.checked_at || session.created_at || 0;
  if (lastGood && now - lastGood > STALE_TRUST_TTL) return [];
  return session.patreon_tiers || [];
}

/** Re-resolve what this session is entitled to, cached. The cache is what
 *  keeps a fleet of updaters from ever becoming a Patreon rate-limit
 *  problem, and it is why a retry loop in TD is harmless. */
async function refreshEntitlement(env, token, session) {
  const now = Math.floor(Date.now() / 1000);
  const fresh = session.checked_at && now - session.checked_at < ENTITLEMENT_TTL;
  // Only the PATREON CALL is cached. Mapping tiers -> packages is local,
  // free, and must always be redone: it is what changes when a package is
  // added to a tier, and gating it behind the cache would mean a launch
  // silently not reaching signed-in supporters for hours.
  if (fresh) {
    session.products = productsFor(env, {
      patreonTiers: trustedTiers(session, now),
      gumroadProducts: session.gumroad_products || [],
    });
    return session;
  }
  if (session.patreon_refresh_token) {
    const ex = await patreonExchange(env, {
      grant_type: 'refresh_token',
      refresh_token: session.patreon_refresh_token,
    });
    if (ex.ok && ex.tok.access_token) {
      const res = await patreonTiers(env, ex.tok.access_token);
      if (res.ok) {
        session.patreon_tiers = res.tiers;
        session.verified_at = now;
        if (ex.tok.refresh_token) session.patreon_refresh_token = ex.tok.refresh_token;
      }
      // An identity lookup that fails with a good grant is transient --
      // fall through to the transient handling below via checked_at.
    } else if (ex.permanent) {
      // The GRANT is dead -- revoked in the supporter's Patreon settings,
      // expired, or rotated away. That is a revocation, not an outage:
      // the tiers go, and the dead token goes with them so we stop
      // presenting it every window.
      session.patreon_tiers = [];
      session.patreon_refresh_token = '';
      session.verified_at = now;      // verified to be nothing
    }
    // A failed LOOKUP is not a revocation -- but only a TRANSIENT one.
    // Patreon being down must not strip a paying supporter of access:
    // keep the last known answer, and retry sooner than the full window
    // so an outage costs minutes of staleness, not six hours per try.
  }
  const attempted = session.patreon_refresh_token || session.verified_at === now;
  const succeeded = session.verified_at === now;
  session.checked_at = (attempted && !succeeded)
    ? now - ENTITLEMENT_TTL + TRANSIENT_RETRY
    : now;
  session.products = productsFor(env, {
    patreonTiers: trustedTiers(session, now),
    gumroadProducts: session.gumroad_products || [],
  });
  await saveSession(env, token, session);
  return session;
}

// ---------------------------------------------------------------------------
// routes
// ---------------------------------------------------------------------------

async function handlePatreonStart(env, url) {
  const port = url.searchParams.get('port') || '';
  if (!/^\d{4,5}$/.test(port)) {
    return refuse(400, 'bad_port', 'A loopback port is required.');
  }
  // `cn` is the CLIENT's nonce: TouchDesigner mints it when it opens the
  // browser, we carry it through the exchange, and the loopback listener
  // accepts a token only when the nonce comes back matching. Without it,
  // anything that can reach the listener can hand it a token to store --
  // OUR `state` nonce protects the gate, not the listener.
  const cn = url.searchParams.get('cn') || '';
  if (cn && !/^[A-Za-z0-9_-]{8,64}$/.test(cn)) {
    return refuse(400, 'bad_nonce', 'Malformed client nonce.');
  }
  // The loopback port and a CSRF nonce ride in `state`; the redirect_uri
  // registered with Patreon is OURS, because only we may hold the secret.
  const nonce = randomToken();
  await env.SESSIONS.put('nonce:' + nonce, JSON.stringify({ port, cn }),
    { expirationTtl: 600 });
  const q = new URLSearchParams({
    response_type: 'code',
    client_id: env.PATREON_CLIENT_ID,
    redirect_uri: env.PATREON_REDIRECT_URI,
    scope: 'identity identity.memberships',
    state: nonce,
  });
  return Response.redirect(PATREON_AUTH + '?' + q, 302);
}

async function handlePatreonCallback(env, url) {
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state') || '';
  const raw = await env.SESSIONS.get('nonce:' + state);
  if (!code || !raw) {
    return new Response('Sign-in link expired or invalid. Start again from TouchDesigner.',
      { status: 400, headers: TEXT });
  }
  await env.SESSIONS.delete('nonce:' + state);
  let port = '', cn = '';
  try {
    ({ port = '', cn = '' } = JSON.parse(raw));
  } catch {
    port = raw;      // a row written before cn existed holds the bare port
  }
  if (!port) {
    return new Response('Sign-in link expired or invalid. Start again from TouchDesigner.',
      { status: 400, headers: TEXT });
  }

  const ex = await patreonExchange(env, {
    grant_type: 'authorization_code',
    code,
    redirect_uri: env.PATREON_REDIRECT_URI,
  });
  if (!ex.ok || !ex.tok.access_token) {
    return new Response('Patreon rejected the sign-in. Please try again.',
      { status: 502, headers: TEXT });
  }
  const now = Math.floor(Date.now() / 1000);
  const res = await patreonTiers(env, ex.tok.access_token);
  const device = randomToken();
  const session = {
    kind: 'patreon',
    patreon_refresh_token: ex.tok.refresh_token || '',
    patreon_tiers: res.tiers,
    gumroad_products: [],
    checked_at: now,
    verified_at: now,
    created_at: now,
  };
  session.products = productsFor(env, { patreonTiers: res.tiers });
  await saveSession(env, device, session);

  // Hand the loopback listener a one-time grant code (see GRANT_TTL --
  // the device token itself must never ride a URL), with the client nonce
  // so the listener can tell OUR redirect from anything else that found
  // its port. TouchDesigner exchanges the code via POST /session/claim.
  const grant = randomToken();
  await env.SESSIONS.put('grant:' + grant, device, { expirationTtl: GRANT_TTL });
  const back = new URL('http://127.0.0.1:' + port + '/fns-auth');
  back.searchParams.set('code', grant);
  if (cn) back.searchParams.set('cn', cn);
  return Response.redirect(back.toString(), 302);
}

/** POST /session/claim {code} -- exchange a sign-in grant code for the
 *  device token, exactly once. The delete-before-answer order makes a
 *  raced double-claim fail on the second claimer rather than mint twice. */
async function handleSessionClaim(env, request) {
  let body;
  try {
    body = await request.json();
  } catch {
    return refuse(400, 'bad_request', 'Expected a JSON body.');
  }
  const code = String(body.code || '').trim();
  if (!code) {
    return refuse(400, 'bad_request', 'A sign-in code is required.');
  }
  const device = await env.SESSIONS.get('grant:' + code);
  if (!device) {
    return refuse(401, 'expired_code',
      'That sign-in expired or was already used. Start again from TouchDesigner.');
  }
  await env.SESSIONS.delete('grant:' + code);
  return json({ ok: true, device_token: device });
}

/** POST /session/revoke -- signing out actually signs you out.
 *
 *  Bearer = the device token revoking ITSELF: the only credential needed
 *  to kill a session is holding it, which is exactly the "laptop stolen at
 *  a festival" case -- sign out from any machine that still has it.
 *  Idempotent, and deliberately the same answer whether the token existed
 *  or not: a revoke endpoint must not double as a token oracle. The row is
 *  KEPT (with a bounded TTL) rather than deleted, so a copy of the token
 *  presented later still reads as revoked instead of merely unknown. */
async function handleSessionRevoke(env, request) {
  const device = bearer(request);
  if (!device) {
    return refuse(401, 'signed_out', 'No device token supplied.');
  }
  const raw = await env.SESSIONS.get(sessionKey(device));
  if (raw) {
    let session;
    try {
      session = JSON.parse(raw);
    } catch {
      session = {};
    }
    session.revoked = true;
    session.revoked_at = Math.floor(Date.now() / 1000);
    await saveSession(env, device, session);
  }
  return json({ ok: true });
}

async function handleGumroadRedeem(env, request) {
  let body;
  try {
    body = await request.json();
  } catch {
    return refuse(400, 'bad_request', 'Expected a JSON body.');
  }
  const key = String(body.license_key || '').trim();
  const product = String(body.product_id || '').trim();
  if (!key || !product) {
    return refuse(400, 'bad_request', 'license_key and product_id are required.');
  }
  // Throttle BEFORE touching Gumroad: this endpoint is otherwise a free
  // brute-force proxy against our account, and every guess it forwards is
  // traffic Gumroad attributes to us. Per-IP catches a loop; per-key
  // catches one key sprayed from many addresses -- which would otherwise
  // inflate the customer's own activation counter until THEY look like
  // the key-sharer. docs/EntitlementLifecycle.md 5.2.
  const ip = request.headers.get('cf-connecting-ip') || '';
  if (await overLimit(env, 'ip', ip) || await overLimit(env, 'key', key)) {
    return refuse(429, 'slow_down',
      'Too many licence checks. Wait an hour and try again.');
  }

  // The SESSION comes first, because it decides what this call is: a key
  // this session already holds is a RE-CHECK, and a re-check must verify
  // with increment_uses_count 'false' -- the uses count is the activation
  // counter for a perpetual licence, and spending it on retries and
  // recoveries walks a paying customer toward their own ceiling. Only a
  // genuine first activation on this install increments.
  let device = String(body.device_token || '').trim();
  let session = await loadSession(env, device);
  const firstActivation = !session || !session.gumroad_products.includes(product);
  const r = await fetch(GUMROAD_VERIFY, {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      product_id: product,
      license_key: key,
      increment_uses_count: firstActivation ? 'true' : 'false',
    }),
  });
  const doc = r.ok ? await r.json() : null;
  if (!doc || !doc.success) {
    return refuse(403, 'bad_licence', 'That licence key was not recognised for this product.');
  }
  const purchase = doc.purchase || {};
  if (purchase.refunded || purchase.disputed || purchase.chargebacked) {
    return refuse(403, 'licence_void', 'That purchase was refunded or disputed.');
  }
  if (purchase.subscription_cancelled_at || purchase.subscription_failed_at) {
    return refuse(403, 'licence_lapsed', 'That subscription is no longer active.');
  }

  // Keys are per tool, so redeeming a second one EXTENDS the session
  // rather than replacing it -- five tools means five keys on one install.
  if (!session) {
    device = randomToken();
    session = {
      kind: 'gumroad', patreon_tiers: [], gumroad_products: [],
      created_at: Math.floor(Date.now() / 1000),
    };
  }
  if (!session.gumroad_products.includes(product)) {
    session.gumroad_products.push(product);
  }
  session.checked_at = Math.floor(Date.now() / 1000);
  session.products = productsFor(env, {
    patreonTiers: session.patreon_tiers || [],
    gumroadProducts: session.gumroad_products,
  });
  await saveSession(env, device, session);
  return json({
    ok: true, device_token: device, products: session.products,
    uses: doc.uses || null,
  });
}

/** device token -> a short-lived, signed download token. */
/** POST /session/recheck -- forced entitlement re-check, throttled.
 *
 *  Same refresh the automatic path uses; only the cache is skipped. The
 *  answer is deliberately the WHOLE picture (products and tiers), because
 *  the caller is a human asking "did my pledge land?" and an empty
 *  products list with a populated tiers list is a different story from
 *  both lists being empty -- the first means the tier is not mapped, the
 *  second means Patreon reports no membership at all.
 */
async function handleSessionRecheck(env, request) {
  const device = bearer(request);
  let session = await loadSession(env, device);
  if (!session) {
    return refuse(401, 'signed_out', 'This install is not signed in. Sign in again.');
  }
  if (await overLimit(env, 'recheck', await sha256hex(device))) {
    return refuse(429, 'rate_limited',
      'Too many checks. Give Patreon a minute, then try again.');
  }
  session.checked_at = 0;          // the only thing refreshEntitlement caches on
  session = await refreshEntitlement(env, device, session);
  await saveSession(env, device, session);
  return json({
    ok: true,
    products: session.products || [],
    tiers: session.patreon_tiers || [],
  });
}

async function handleTokenDownload(env, request) {
  const device = bearer(request);
  let session = await loadSession(env, device);
  if (!session) {
    return refuse(401, 'signed_out', 'This install is not signed in. Sign in again.');
  }
  session = await refreshEntitlement(env, device, session);
  if (!session.products.length) {
    return refuse(403, 'no_entitlement',
      'This account does not currently include any paid packages.',
      { products: [], tiers: session.patreon_tiers || [] });
  }
  const token = await mintJWT(env,
    { sub: await sha256hex(device), products: session.products },
    DOWNLOAD_TOKEN_TTL);
  return json({
    ok: true, token, expires_in: DOWNLOAD_TOKEN_TTL, products: session.products,
  });
}

function bearer(request) {
  const h = request.headers.get('authorization') || '';
  return h.toLowerCase().startsWith('bearer ') ? h.slice(7).trim() : '';
}

/** GET /fnstools/plus/<release>/<Package>.tox
 *
 *  The path carries the bucket prefix because gated URLs are written
 *  UNDER the manifest's base_url (see wrangler.toml) -- the pathname IS
 *  the bucket key, same rule as the public rail. */
async function handlePlusDownload(env, request, url) {
  const m = url.pathname.match(
    /^\/fnstools\/plus\/([A-Za-z0-9._-]+)\/([A-Za-z0-9._-]+)\.tox$/);
  if (!m) return refuse(404, 'not_found', 'No such artifact.');
  const [, release, name] = m;

  const claims = await readJWT(env, bearer(request));
  if (!claims) {
    return refuse(401, 'bad_token', 'Expired or invalid download token.');
  }
  // FAIL CLOSED: a package nobody has claimed is gated, not free.
  if (!Array.isArray(claims.products) || !claims.products.includes(name)) {
    return refuse(403, 'not_entitled',
      `Your current tier does not include ${name}.`,
      { package: name, products: claims.products || [] });
  }

  const key = `fnstools/plus/${release}/${name}.tox`;
  const obj = await env.BUCKET.get(key);
  if (!obj) return refuse(404, 'not_found', 'No such artifact.');

  return new Response(obj.body, {
    headers: {
      'content-type': 'application/octet-stream',
      // Release-pinned, so immutable -- but PRIVATE: a shared cache must
      // never hold a gated artifact where an unauthenticated request
      // could be served it.
      'cache-control': 'private, max-age=31536000, immutable',
      'content-disposition': `attachment; filename="${name}.tox"`,
      etag: obj.httpEtag,
    },
  });
}

// ---------------------------------------------------------------------------

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const { pathname } = url;

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: { allow: 'GET, POST, OPTIONS' } });
    }
    if (request.method !== 'GET' && request.method !== 'POST') {
      return refuse(405, 'method_not_allowed', 'GET or POST only.');
    }

    try {
      if (pathname === '/health') return json({ ok: true });
      if (request.method === 'POST' && pathname === '/session/recheck') {
        return handleSessionRecheck(env, request);
      }
      if (pathname === '/patreon/start') return handlePatreonStart(env, url);
      if (pathname === '/patreon/callback') return handlePatreonCallback(env, url);
      if (pathname === '/gumroad/redeem' && request.method === 'POST') {
        return handleGumroadRedeem(env, request);
      }
      if (pathname === '/token/download' && request.method === 'POST') {
        return handleTokenDownload(env, request);
      }
      if (pathname === '/session/revoke' && request.method === 'POST') {
        return handleSessionRevoke(env, request);
      }
      if (pathname === '/session/claim' && request.method === 'POST') {
        return handleSessionClaim(env, request);
      }
      if (pathname.startsWith('/fnstools/plus/')) return handlePlusDownload(env, request, url);
      return refuse(404, 'not_found', 'No such endpoint.');
    } catch (err) {
      // Never leak internals to a client, but do not swallow it either.
      console.error('unhandled', pathname, err && err.stack);
      return refuse(500, 'internal', 'Something went wrong. Please try again.');
    }
  },
};
