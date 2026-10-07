/**
 * Offline tests for the public-JSON passthrough (the website's CORS header).
 *
 * The site on https://functionstore.tools reads fnstools/manifest.json and
 * fnstools/recommendations.json in the browser; the bucket sends no CORS
 * header. Every install fetches the same two URLs, so what is asserted here
 * is mostly what must NOT change: status, body, cache-control, etag, 304 and
 * HEAD pass through from the origin untouched, the header goes to the site
 * origin only, and nothing else is routed through this handler.
 *
 * The origin is a stub for the global fetch (a route's fetch(request) goes
 * to the origin, never back into the Worker).
 *
 *   node worker/test/public_json.test.mjs
 */
import worker, { PUBLIC_JSON_PATHS, SITE_ORIGIN, STORAGE_HOST } from '../src/index.js';

const FAILS = [];
function check(label, cond, detail = '') {
  if (cond) console.log('  PASS  ' + label);
  else { FAILS.push(label); console.log('  FAIL  ' + label + '   ' + detail); }
}

const ORIGIN_CALLS = [];
let originImpl = null;
globalThis.fetch = async (req) => {
  ORIGIN_CALLS.push(req);
  return originImpl(req);
};

function origin200(body = '{"release":"v3.2.27"}') {
  return () => new Response(body, {
    status: 200,
    headers: { 'content-type': 'application/json', 'cache-control': 'no-cache', etag: '"abc"' },
  });
}

const env = {};   // the passthrough needs no bindings
const call = (path, { method = 'GET', originHeader = null, host = STORAGE_HOST, headers = {} } = {}) => {
  const h = new Headers(headers);
  if (originHeader) h.set('origin', originHeader);
  return worker.fetch(new Request(`https://${host}${path}`, { method, headers: h }), env);
};

console.log('1. the site origin gets the header, nothing else changes');
originImpl = origin200();
ORIGIN_CALLS.length = 0;
let r = await call('/fnstools/manifest.json', { originHeader: SITE_ORIGIN });
check('the request went to the origin, once', ORIGIN_CALLS.length === 1, String(ORIGIN_CALLS.length));
check('status and body pass through', r.status === 200 && (await r.text()) === '{"release":"v3.2.27"}');
check('Access-Control-Allow-Origin is the site, never *',
  r.headers.get('access-control-allow-origin') === SITE_ORIGIN);
check('cache-control no-cache is kept', r.headers.get('cache-control') === 'no-cache');
check('etag and content-type are kept',
  r.headers.get('etag') === '"abc"' && r.headers.get('content-type') === 'application/json');
check('Vary: Origin is added', /origin/i.test(r.headers.get('vary') || ''));

r = await call('/fnstools/recommendations.json', { originHeader: SITE_ORIGIN });
check('recommendations.json gets the header too',
  r.headers.get('access-control-allow-origin') === SITE_ORIGIN);

console.log('2. other origins and installs get exactly the origin response');
r = await call('/fnstools/manifest.json', { originHeader: 'https://evil.example' });
check('another origin gets no CORS header', r.headers.get('access-control-allow-origin') === null);
check('and still gets the manifest', r.status === 200);
r = await call('/fnstools/manifest.json');
check('no Origin header (an install, curl) gets no CORS header',
  r.headers.get('access-control-allow-origin') === null && r.status === 200);
check('an install still gets no-cache', r.headers.get('cache-control') === 'no-cache');
r = await call('/fnstools/manifest.json', { originHeader: 'http://127.0.0.1:36760' });
check('the local picker origin is not allowed (it reads through the installer)',
  r.headers.get('access-control-allow-origin') === null);

console.log('3. origin statuses pass through');
originImpl = () => new Response(null, { status: 304, headers: { etag: '"abc"' } });
r = await call('/fnstools/manifest.json', { originHeader: SITE_ORIGIN, headers: { 'if-none-match': '"abc"' } });
check('a 304 passes through, with the header for the site', r.status === 304
  && r.headers.get('access-control-allow-origin') === SITE_ORIGIN);
check('the conditional header reached the origin',
  ORIGIN_CALLS[ORIGIN_CALLS.length - 1].headers.get('if-none-match') === '"abc"');
originImpl = () => new Response('<html>Not Found</html>', { status: 404, headers: { 'content-type': 'text/html' } });
r = await call('/fnstools/recommendations.json', { originHeader: SITE_ORIGIN });
check('a 404 passes through, readable by the site (no console CORS error)',
  r.status === 404 && r.headers.get('access-control-allow-origin') === SITE_ORIGIN);
originImpl = () => new Response(null, { status: 200, headers: { 'cache-control': 'no-cache' } });
r = await call('/fnstools/manifest.json', { method: 'HEAD', originHeader: SITE_ORIGIN });
check('HEAD passes through', r.status === 200 && r.headers.get('cache-control') === 'no-cache');

console.log('4. anything else goes to the origin untouched, or is not routed here');
originImpl = () => new Response('forbidden', { status: 403 });
ORIGIN_CALLS.length = 0;
r = await call('/fnstools/manifest.json', { method: 'OPTIONS', originHeader: SITE_ORIGIN });
check('OPTIONS is the origin\'s own answer, no header added',
  ORIGIN_CALLS.length === 1 && r.status === 403 && r.headers.get('access-control-allow-origin') === null);
originImpl = () => { throw new Error('origin unreachable'); };
let threw = false;
try { await call('/fnstools/manifest.json', { originHeader: SITE_ORIGIN }); } catch (e) { threw = true; }
check('an origin failure is not turned into a Worker error page (it surfaces as the origin fetch would)', threw);
originImpl = origin200();
let calledTwice = 0;
originImpl = (req) => {
  calledTwice++;
  if (calledTwice === 1) return { get body() { throw new Error('boom'); } };   // a broken first response
  return new Response('{"ok":1}', { status: 200, headers: { 'cache-control': 'no-cache' } });
};
r = await call('/fnstools/manifest.json', { originHeader: SITE_ORIGIN });
check('a failure inside the handler falls back to a plain origin fetch',
  calledTwice === 2 && r.status === 200 && r.headers.get('access-control-allow-origin') === null);

ORIGIN_CALLS.length = 0;
originImpl = origin200();
r = await call('/fnstools/latest/manifest.json', { originHeader: SITE_ORIGIN });
check('latest/manifest.json is not handled here (not in the set)', !PUBLIC_JSON_PATHS.has('/fnstools/latest/manifest.json')
  && ORIGIN_CALLS.length === 0 && r.status === 404);
r = await call('/fnstools/v3.2.27/FNS_AutoRes.tox', { originHeader: SITE_ORIGIN });
check('artifacts are not handled here', ORIGIN_CALLS.length === 0 && r.headers.get('access-control-allow-origin') === null);
r = await call('/fnstools/manifest.json', { host: 'gate.functionstore.tools', originHeader: SITE_ORIGIN });
check('the gate host never passes these paths through (no bucket behind it)',
  ORIGIN_CALLS.length === 0 && r.status === 404);
check('exactly two paths are handled', PUBLIC_JSON_PATHS.size === 2
  && PUBLIC_JSON_PATHS.has('/fnstools/manifest.json') && PUBLIC_JSON_PATHS.has('/fnstools/recommendations.json'));

if (FAILS.length) {
  console.log(FAILS.length + ' FAILED: ' + FAILS.join(', '));
  process.exit(1);
}
console.log('all public-json checks passed');
