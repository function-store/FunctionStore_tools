/**
 * Offline tests for the entitlement gate.
 *
 * No Cloudflare, no network: the R2 bucket and the KV namespace are
 * in-memory stubs and Patreon/Gumroad are never called. What is exercised
 * is the part that decides who gets bytes -- token integrity, the product
 * check, and the failure directions.
 *
 * The failure DIRECTIONS are the point. A gate that wrongly refuses a
 * paying customer and a gate that wrongly serves a stranger are both
 * bugs, but only one of them shows up in normal use, so both are asserted
 * explicitly here.
 *
 *   node worker/test/gate.test.mjs
 */
import { generateKeyPairSync } from 'node:crypto';
import worker from '../src/index.js';

const kp = generateKeyPairSync('ed25519');
const B64 = (b) => Buffer.from(b).toString('base64');

const TIERS = {
  '111': ['FNS_TimelineTools'],
  '222': ['FNS_TimelineTools', 'FutureTool'],
  '333': ['SomeOtherTool'],
};

function makeEnv(objects = { 'fnstools/plus/v3.0.1/FNS_TimelineTools.tox': 'TOXBYTES' }) {
  const kv = new Map();
  const puts = [];      // [key, options] per put, so TTL choices are assertable
  return {
    JWT_PRIVATE_KEY: B64(kp.privateKey.export({ type: 'pkcs8', format: 'der' })),
    JWT_PUBLIC_KEY: B64(kp.publicKey.export({ type: 'spki', format: 'der' })),
    PATREON_CLIENT_ID: 'cid',
    PATREON_CLIENT_SECRET: 'csecret',
    PATREON_REDIRECT_URI: 'https://gate.example/patreon/callback',
    TIERS: JSON.stringify(TIERS),
    GUMROAD_PRODUCTS: JSON.stringify({ gum_tl: 'FNS_TimelineTools' }),
    SESSIONS: {
      get: async (k) => (kv.has(k) ? kv.get(k) : null),
      put: async (k, v, opts) => { kv.set(k, v); puts.push([k, opts || null]); },
      delete: async (k) => void kv.delete(k),
      _kv: kv,
      _puts: puts,
    },
    BUCKET: {
      get: async (k) => (objects[k] === undefined ? null : {
        body: objects[k], httpEtag: '"etag"',
      }),
    },
  };
}

/** Route outbound fetches to canned upstream answers. Returns the calls it
 *  saw so a test can assert WHAT was sent, not just what came back. */
function stubFetch(handlers) {
  const calls = [];
  globalThis.fetch = async (url, init = {}) => {
    const u = String(url);
    calls.push({ url: u, body: String(init.body || '') });
    for (const [match, make] of handlers) {
      if (u.startsWith(match)) return make(calls[calls.length - 1]);
    }
    throw new Error('unstubbed fetch: ' + u);
  };
  return calls;
}
const realFetch = globalThis.fetch;
const jsonRes = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json' } });
const lastSession = (env, device) =>
  JSON.parse(env.SESSIONS._kv.get('session:' + device));

const call = (env, path, init = {}) =>
  worker.fetch(new Request('https://gate.example' + path, init), env);

let FAILS = [];
const check = (label, cond, detail = '') => {
  if (cond) console.log('  PASS  ' + label);
  else { console.log('  FAIL  ' + label + '  ' + detail); FAILS.push(label); }
};

/** Mint a download token the way /token/download does, via a real session.
 *
 * Takes TIERS, not a product list: `products` is DERIVED from the tier map
 * on every call by design, so a test that injected a product list directly
 * would be asserting against a field the Worker overwrites. */
async function tokenFor(env, tiers) {
  const device = 'dev_' + tiers.join('_');
  await env.SESSIONS.put('session:' + device, JSON.stringify({
    kind: 'patreon', patreon_tiers: tiers, gumroad_products: [],
    products: [], checked_at: Math.floor(Date.now() / 1000),
  }));
  const r = await call(env, '/token/download', {
    method: 'POST', headers: { authorization: 'Bearer ' + device },
  });
  return { res: r, body: await r.json(), device };
}

console.log('fnstools-gate');

// --- basics ---------------------------------------------------------------
console.log('\n1. surface');
{
  const env = makeEnv();
  check('health is open', (await call(env, '/health')).status === 200);
  check('unknown route 404s', (await call(env, '/nope')).status === 404);
  const del = await call(env, '/health', { method: 'DELETE' });
  check('DELETE is refused', del.status === 405, String(del.status));
}

// --- the download token ---------------------------------------------------
console.log('\n2. download token');
{
  const env = makeEnv();
  const anon = await call(env, '/token/download', { method: 'POST' });
  check('no device token -> 401', anon.status === 401, String(anon.status));

  const unknown = await call(env, '/token/download', {
    method: 'POST', headers: { authorization: 'Bearer not-a-real-token' },
  });
  check('unknown device token -> 401', unknown.status === 401, String(unknown.status));

  const { res, body } = await tokenFor(env, ['111']);
  check('valid session -> a token', res.status === 200 && !!body.token, JSON.stringify(body));
  check('  token carries the product list',
    JSON.stringify(body.products) === JSON.stringify(['FNS_TimelineTools']));
  check('  token is short-lived', body.expires_in > 0 && body.expires_in <= 900,
    String(body.expires_in));

  // A revoked device is cut off even though its session row still exists.
  await env.SESSIONS.put('session:dev_x', JSON.stringify({ products: ['X'], revoked: true }));
  const rev = await call(env, '/token/download', {
    method: 'POST', headers: { authorization: 'Bearer dev_x' },
  });
  check('revoked session -> 401', rev.status === 401, String(rev.status));

  // Entitled to nothing is a NAMED refusal, not a token with an empty list.
  await env.SESSIONS.put('session:dev_empty', JSON.stringify({
    products: [], patreon_tiers: [], gumroad_products: [],
    checked_at: Math.floor(Date.now() / 1000),
  }));
  const none = await call(env, '/token/download', {
    method: 'POST', headers: { authorization: 'Bearer dev_empty' },
  });
  const nb = await none.json();
  check('no entitlement -> 403 named', none.status === 403 && nb.error === 'no_entitlement',
    JSON.stringify(nb));
}

// --- serving the bytes ----------------------------------------------------
console.log('\n3. /plus -- who gets bytes');
{
  const env = makeEnv();
  const P = '/fnstools/plus/v3.0.1/FNS_TimelineTools.tox';

  check('no token -> 401', (await call(env, P)).status === 401);

  const bad = await call(env, P, { headers: { authorization: 'Bearer garbage.token.here' } });
  check('malformed token -> 401 (not 500)', bad.status === 401, String(bad.status));

  const { body: ok } = await tokenFor(env, ['111']);
  const good = await call(env, P, { headers: { authorization: 'Bearer ' + ok.token } });
  check('entitled -> 200 with the bytes', good.status === 200, String(good.status));
  check('  body is the artifact', (await good.text()) === 'TOXBYTES');
  check('  never publicly cacheable',
    (good.headers.get('cache-control') || '').startsWith('private'),
    good.headers.get('cache-control'));

  // Entitled to something ELSE must not open this door.
  const { body: other } = await tokenFor(env, ['333']);
  const wrong = await call(env, P, { headers: { authorization: 'Bearer ' + other.token } });
  const wb = await wrong.json();
  check('entitled to another package -> 403', wrong.status === 403, String(wrong.status));
  check('  refusal NAMES the package', String(wb.message).includes('FNS_TimelineTools'),
    JSON.stringify(wb));

  // Fail closed: a package in no tier is gated, never open.
  const unlisted = await call(env, '/fnstools/plus/v3.0.1/NotInAnyTier.tox',
    { headers: { authorization: 'Bearer ' + ok.token } });
  check('unlisted package -> 403 (fails CLOSED)', unlisted.status === 403,
    String(unlisted.status));

  // A token signed by someone else's key must not verify.
  const other_kp = generateKeyPairSync('ed25519');
  const forged = makeEnv();
  forged.JWT_PRIVATE_KEY = B64(other_kp.privateKey.export({ type: 'pkcs8', format: 'der' }));
  forged.JWT_PUBLIC_KEY = B64(other_kp.publicKey.export({ type: 'spki', format: 'der' }));
  const { body: fb } = await tokenFor(forged, ['111']);
  const rejected = await call(env, P, { headers: { authorization: 'Bearer ' + fb.token } });
  check('token from a foreign key -> 401', rejected.status === 401, String(rejected.status));

  // Tampering with the payload must break the signature.
  const [h, p] = ok.token.split('.');
  const evil = JSON.parse(Buffer.from(p, 'base64url').toString());
  evil.products = ['FNS_TimelineTools', 'Everything'];
  const tampered = h + '.' +
    Buffer.from(JSON.stringify(evil)).toString('base64url') + '.' + ok.token.split('.')[2];
  const t = await call(env, P, { headers: { authorization: 'Bearer ' + tampered } });
  check('tampered payload -> 401', t.status === 401, String(t.status));

  // A missing object is 404 even for an entitled holder.
  const gone = await call(env, '/fnstools/plus/v9.9.9/FNS_TimelineTools.tox',
    { headers: { authorization: 'Bearer ' + ok.token } });
  check('entitled but absent object -> 404', gone.status === 404, String(gone.status));

  // Path traversal must not reach outside the prefix.
  const trav = await call(env, '/fnstools/plus/..%2F..%2Fmanifest.json',
    { headers: { authorization: 'Bearer ' + ok.token } });
  check('traversal attempt -> 404', trav.status === 404, String(trav.status));
}

// --- the tier map ---------------------------------------------------------
console.log('\n4. tier -> products');
{
  const env = makeEnv();
  await env.SESSIONS.put('session:dev_t', JSON.stringify({
    kind: 'patreon', patreon_tiers: ['222'], gumroad_products: [],
    products: [], checked_at: Math.floor(Date.now() / 1000),
  }));
  const r = await call(env, '/token/download', {
    method: 'POST', headers: { authorization: 'Bearer dev_t' },
  });
  const b = await r.json();
  check('a higher tier grants its whole list',
    JSON.stringify(b.products) === JSON.stringify(['FNS_TimelineTools', 'FutureTool']),
    JSON.stringify(b.products));
}

// --- patreon start --------------------------------------------------------
console.log('\n5. sign-in start');
{
  const env = makeEnv();
  const bad = await call(env, '/patreon/start');
  check('missing loopback port -> 400', bad.status === 400, String(bad.status));
  const r = await call(env, '/patreon/start?port=9871');
  const loc = r.headers.get('location') || '';
  check('redirects to Patreon', r.status === 302 && loc.startsWith('https://www.patreon.com/'),
    loc.slice(0, 60));
  check('  asks for membership scope', loc.includes('identity.memberships'));
  check('  never leaks the client secret', !loc.includes('csecret'));
  check('  redirect_uri is OURS, not localhost',
    decodeURIComponent(loc).includes('https://gate.example/patreon/callback'));
}

// --- malformed configuration ----------------------------------------------
console.log('\n6. a broken [vars] entry degrades, it does not 500');
{
  // The guard logs deliberately; silence it so the test output stays readable.
  const realError = console.error;
  console.error = () => {};

  // The regression: GUMROAD_PRODUCTS was parsed inline with no guard while
  // TIERS had one, so a typo in the Gumroad map threw on EVERY entitlement
  // check -- including Patreon sessions that never touch Gumroad. One broken
  // variable must only cost the thing it configures.
  const gum = makeEnv();
  gum.GUMROAD_PRODUCTS = '{not json';
  const { res, body } = await tokenFor(gum, ['111']);
  check('broken GUMROAD_PRODUCTS still serves a patron',
    res.status === 200 && !!body.token, String(res.status));
  check('  and their tier list is intact',
    JSON.stringify(body.products) === JSON.stringify(['FNS_TimelineTools']),
    JSON.stringify(body.products));

  // The same in the other direction: a broken tier map entitles nothing,
  // which is a NAMED refusal the client can act on -- never a 500.
  const tiers = makeEnv();
  tiers.TIERS = '{also not json';
  await tiers.SESSIONS.put('session:dev_t2', JSON.stringify({
    kind: 'patreon', patreon_tiers: ['111'], gumroad_products: [],
    products: [], checked_at: Math.floor(Date.now() / 1000),
  }));
  const t = await call(tiers, '/token/download', {
    method: 'POST', headers: { authorization: 'Bearer dev_t2' },
  });
  check('broken TIERS -> a named 403, not a 500', t.status === 403, String(t.status));

  console.error = realError;
}

// --- the sign-in loop, end to end -----------------------------------------
console.log('\n7. sign-in callback: the client nonce rides the whole loop');
{
  const env = makeEnv();
  const bad = await call(env, '/patreon/start?port=9871&cn=not*valid');
  check('malformed client nonce -> 400', bad.status === 400, String(bad.status));

  const CN = 'client_nonce_12345';
  const r = await call(env, '/patreon/start?port=9871&cn=' + CN);
  const state = new URL(r.headers.get('location')).searchParams.get('state');
  check('start still redirects with a state nonce', r.status === 302 && !!state);

  stubFetch([
    ['https://www.patreon.com/api/oauth2/token',
      () => jsonRes({ access_token: 'at', refresh_token: 'rt' })],
    ['https://www.patreon.com/api/oauth2/v2/identity',
      () => jsonRes({ included: [{ type: 'member',
        attributes: { patron_status: 'active_patron' },
        relationships: { currently_entitled_tiers: { data: [{ id: '111' }] } } }] })],
  ]);
  const cb = await call(env, `/patreon/callback?code=abc&state=${state}`);
  globalThis.fetch = realFetch;
  const back = new URL(cb.headers.get('location'));
  check('callback lands on the loopback listener',
    cb.status === 302 && back.hostname === '127.0.0.1' && back.port === '9871');
  const grant = back.searchParams.get('code');
  check('  with a one-time code, NEVER the device token',
    !!grant && !back.searchParams.get('token'), String(back));
  check('  and the client nonce echoed back', back.searchParams.get('cn') === CN,
    String(back));

  const claim = await call(env, '/session/claim', {
    method: 'POST', body: JSON.stringify({ code: grant }),
  });
  const cbody = await claim.json();
  const device = cbody.device_token;
  check('  code exchanges for the device token',
    claim.status === 200 && !!device, JSON.stringify(cbody));
  const again2 = await call(env, '/session/claim', {
    method: 'POST', body: JSON.stringify({ code: grant }),
  });
  check('  code is single-use', again2.status === 401, String(again2.status));
  const gput = env.SESSIONS._puts.find(([k]) => k === 'grant:' + grant);
  check('  unclaimed codes age out fast',
    !!(gput && gput[1]) && gput[1].expirationTtl === 120,
    JSON.stringify(gput && gput[1]));

  const s = lastSession(env, device);
  check('  session is verified at creation', typeof s.verified_at === 'number');
  const put = env.SESSIONS._puts.find(([k]) => k === 'session:' + device);
  check('  patreon-only session ages out if abandoned',
    !!(put && put[1]) && put[1].expirationTtl === 180 * 24 * 3600,
    JSON.stringify(put && put[1]));

  const replay = await call(env, `/patreon/callback?code=abc&state=${state}`);
  check('  state nonce is single-use', replay.status === 400, String(replay.status));
}

// --- gumroad lifecycle ------------------------------------------------------
console.log('\n8. gumroad redeem: an activation is spent once, then never again');
{
  const env = makeEnv();
  const H = { 'content-type': 'application/json', 'cf-connecting-ip': '1.1.1.1' };
  const calls = stubFetch([
    ['https://api.gumroad.com', () => jsonRes({ success: true, purchase: {}, uses: 1 })],
  ]);
  const r1 = await call(env, '/gumroad/redeem', {
    method: 'POST', headers: H,
    body: JSON.stringify({ license_key: 'K-1', product_id: 'gum_tl' }),
  });
  const b1 = await r1.json();
  check('first redeem mints a session', r1.status === 200 && !!b1.device_token,
    JSON.stringify(b1));
  check('  and spends ONE activation', calls[0].body.includes('increment_uses_count=true'),
    calls[0].body);
  const r2 = await call(env, '/gumroad/redeem', {
    method: 'POST', headers: H,
    body: JSON.stringify({ license_key: 'K-1', product_id: 'gum_tl',
      device_token: b1.device_token }),
  });
  check('re-check of a held key succeeds', r2.status === 200, String(r2.status));
  check('  without spending another activation',
    calls[1].body.includes('increment_uses_count=false'), calls[1].body);
  const put = env.SESSIONS._puts.find(([k]) => k === 'session:' + b1.device_token);
  check('  gumroad session never expires (a perpetual licence)',
    !!put && put[1] === null, JSON.stringify(put && put[1]));
  globalThis.fetch = realFetch;
}

console.log('\n9. redeem throttle');
{
  const redeem = (env, ip, key) => call(env, '/gumroad/redeem', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'cf-connecting-ip': ip },
    body: JSON.stringify({ license_key: key, product_id: 'gum_tl' }),
  });
  const env = makeEnv();
  stubFetch([['https://api.gumroad.com', () => jsonRes({ success: false })]]);
  let last;
  for (let i = 0; i < 10; i++) last = await redeem(env, '9.9.9.9', 'GUESS-' + i);
  check('a wrong key is refused, not served', last.status === 403, String(last.status));
  const eleventh = await redeem(env, '9.9.9.9', 'GUESS-x');
  check('11th try from one address -> 429', eleventh.status === 429, String(eleventh.status));

  const env2 = makeEnv();
  for (let i = 0; i < 10; i++) await redeem(env2, '10.0.0.' + i, 'SAME-KEY');
  const spray = await redeem(env2, '10.0.0.99', 'SAME-KEY');
  check('one key sprayed across addresses -> 429', spray.status === 429,
    String(spray.status));
  globalThis.fetch = realFetch;
}

// --- revocation -------------------------------------------------------------
console.log('\n10. revoke: signing out actually signs you out');
{
  const env = makeEnv();
  const { body, device } = await tokenFor(env, ['111']);
  check('entitled before revoke', !!body.token);
  const rv = await call(env, '/session/revoke', {
    method: 'POST', headers: { authorization: 'Bearer ' + device },
  });
  check('revoke acknowledges', rv.status === 200, String(rv.status));
  const after = await call(env, '/token/download', {
    method: 'POST', headers: { authorization: 'Bearer ' + device },
  });
  check('the device token is dead afterwards', after.status === 401, String(after.status));
  const again = await call(env, '/session/revoke', {
    method: 'POST', headers: { authorization: 'Bearer ' + device },
  });
  check('revoking twice is fine', again.status === 200);
  const ghost = await call(env, '/session/revoke', {
    method: 'POST', headers: { authorization: 'Bearer never-existed' },
  });
  check('unknown token gets the SAME answer (no oracle)', ghost.status === 200,
    String(ghost.status));
  const anon = await call(env, '/session/revoke', { method: 'POST' });
  check('no token -> 401', anon.status === 401, String(anon.status));
  const put = env.SESSIONS._puts.filter(([k]) => k === 'session:' + device).pop();
  check('revoked row is kept, bounded', !!put[1] && put[1].expirationTtl === 30 * 24 * 3600,
    JSON.stringify(put[1]));
}

// --- dead grant vs outage ---------------------------------------------------
console.log('\n11. a dead grant is not an outage');
{
  const HOUR = 3600, DAY = 24 * 3600;
  const now = Math.floor(Date.now() / 1000);
  const staleSession = (extra) => JSON.stringify({
    kind: 'patreon', patreon_tiers: ['111'], gumroad_products: [], products: [],
    patreon_refresh_token: 'rt', checked_at: now - 7 * HOUR,
    verified_at: now - 7 * HOUR, ...extra,
  });
  const download = (env, dev) => call(env, '/token/download', {
    method: 'POST', headers: { authorization: 'Bearer ' + dev },
  });

  // PERMANENT: invalid_grant means the supporter (or Patreon) killed the
  // grant -- entitlement must actually end.
  const env = makeEnv();
  await env.SESSIONS.put('session:dev_p', staleSession());
  stubFetch([['https://www.patreon.com/api/oauth2/token',
    () => jsonRes({ error: 'invalid_grant' }, 400)]]);
  const p = await download(env, 'dev_p');
  check('revoked grant -> named 403', p.status === 403, String(p.status));
  const sp = lastSession(env, 'dev_p');
  check('  tiers cleared', sp.patreon_tiers.length === 0, JSON.stringify(sp.patreon_tiers));
  check('  dead refresh token dropped', sp.patreon_refresh_token === '');

  // TRANSIENT: an outage keeps the last answer -- a paying supporter is
  // never stripped because Patreon had a bad day.
  const env2 = makeEnv();
  await env2.SESSIONS.put('session:dev_t', staleSession());
  stubFetch([['https://www.patreon.com/api/oauth2/token', () => jsonRes({}, 500)]]);
  const t = await download(env2, 'dev_t');
  const tb = await t.json();
  check('outage keeps the supporter entitled', t.status === 200 && !!tb.token,
    String(t.status));
  const st = lastSession(env2, 'dev_t');
  check('  but the retry comes sooner than the full window',
    now - st.checked_at > 4 * HOUR, String(now - st.checked_at));

  // BACKSTOP: transient forgiveness is not forever. A session that has
  // not actually verified in 30 days stops being trusted.
  const env3 = makeEnv();
  await env3.SESSIONS.put('session:dev_s', JSON.stringify({
    kind: 'patreon', patreon_tiers: ['111'], gumroad_products: [], products: [],
    checked_at: now - HOUR, verified_at: now - 31 * DAY,
  }));
  const s = await download(env3, 'dev_s');
  check('31 days unverified -> no longer trusted', s.status === 403, String(s.status));
  globalThis.fetch = realFetch;
}

console.log();
if (FAILS.length) {
  console.log(FAILS.length + ' FAILED: ' + FAILS.join(', '));
  process.exit(1);
}
console.log('all checks passed');
