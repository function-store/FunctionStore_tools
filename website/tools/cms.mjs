// Internal CMS for FNSTools package metadata and docs.
//
//   npm run cms      ->  http://127.0.0.1:8787
//
// Authors the two curated sources directly on disk: packaging/catalog.json
// (category + description) and packaging/docs/<Name>.md (frontmatter +
// prose). There is no database and no staging layer — git is the audit
// trail, so review with `git diff` and revert with `git checkout`.
//
// Same shape as packaging/configurator: a static page served from a small
// local server that POSTs back. Deliberately bound to 127.0.0.1 — this
// process writes to the repo, so it must not be reachable from the network.

import { spawn, spawnSync } from 'node:child_process';
import crypto from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import matter from 'gray-matter';
import MarkdownIt from 'markdown-it';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB = path.dirname(HERE);
const REPO = path.dirname(WEB);
const DOCS = path.join(REPO, 'packaging', 'docs');
const GATE_PY = path.join(REPO, 'packaging', 'gate_package.py');
// python for the packaging CLIs; override when it is not on PATH
const PYTHON = process.env.FNS_PYTHON || 'python';
const CATALOG = path.join(REPO, 'packaging', 'catalog.json');
const RECOMMENDS = path.join(REPO, 'packaging', 'recommendations.json');
const ICONS = path.join(REPO, 'icons');

const PORT = Number(process.env.CMS_PORT || 8787);
const HOST = '127.0.0.1';

const md = new MarkdownIt({ html: true, linkify: true });

// ------------------------------------------------------------ helpers

const readCatalog = () => JSON.parse(fs.readFileSync(CATALOG, 'utf8'));

const readRecommends = () => JSON.parse(fs.readFileSync(RECOMMENDS, 'utf8'));

/** Tools by OTHER creators that we link to. Deliberately a separate file
 *  from catalog.json, and separate from anything the manifest carries: a
 *  row here is a link, not a package, and it publishes on its own so that
 *  REMOVING one never waits for a release. */
function writeRecommends(doc) {
  fs.writeFileSync(RECOMMENDS, JSON.stringify(doc, null, 1) + '\n');
}

const REC_FIELDS = ['name', 'author', 'author_url', 'url', 'description',
                    'category', 'note',
                    'tox_url', 'sha256', 'bytes', 'pinned_at'];
const HEX64 = /^[0-9a-f]{64}$/;

/** Mirror of packaging/recommendations.py validate(). Kept in step by the
 *  test, not by hope -- the CMS must refuse the same rows the publisher
 *  would, or a save looks fine and the upload fails hours later. */
function validateRecommends(doc) {
  const bad = [];
  const tools = (doc && doc.tools) || [];
  if (!Array.isArray(tools)) return ['`tools` must be a list'];
  const seen = new Map();
  tools.forEach((row, i) => {
    const where = row && row.name ? `tools[${i}] (${row.name})` : `tools[${i}]`;
    if (!row || typeof row !== 'object') { bad.push(`${where} is not an object`); return; }
    for (const f of ['name', 'author', 'url']) {
      if (!String(row[f] || '').trim()) bad.push(`${where}: ${f} is required`);
    }
    for (const f of Object.keys(row)) {
      if (!REC_FIELDS.includes(f)) bad.push(`${where}: unknown field \`${f}\``);
    }
    for (const f of ['url', 'author_url']) {
      const v = String(row[f] || '').trim();
      if (v && !v.startsWith('https://')) bad.push(`${where}: ${f} must be https`);
    }
    // Placement fields travel together -- a tox_url with no pinned hash
    // would install unverified bytes, and a hash with no url is inert.
    const tox = String(row.tox_url || '').trim();
    const sha = String(row.sha256 || '').trim().toLowerCase();
    if (tox || sha || row.bytes != null) {
      if (!tox) bad.push(`${where}: sha256/bytes given without tox_url`);
      else if (!tox.startsWith('https://')) bad.push(`${where}: tox_url must be https`);
      else if (!tox.toLowerCase().endsWith('.tox')) bad.push(`${where}: tox_url must point at a .tox file`);
      if (!sha) bad.push(`${where}: tox_url needs a pinned sha256 — use Pin`);
      else if (!HEX64.test(sha)) bad.push(`${where}: sha256 must be 64 lowercase hex characters`);
      if (!Number.isInteger(row.bytes) || row.bytes <= 0) bad.push(`${where}: bytes must be a positive integer`);
    }
    if (String(row.description || '').length > 400) {
      bad.push(`${where}: description is over 400 characters`);
    }
    const k = String(row.name || '').toLowerCase();
    if (k) {
      if (seen.has(k)) bad.push(`${where}: duplicate name`);
      else seen.set(k, i);
    }
  });
  return bad;
}

/** Byte-identical to how catalog.json is already formatted, so saving a
 *  description produces a one-line diff rather than reformatting the file. */
function writeCatalog(cat) {
  fs.writeFileSync(CATALOG, JSON.stringify(cat, null, 1) + '\n');
}

const countByCategory = (cat) => {
  const n = {};
  for (const name of Object.keys(cat.packages)) {
    const c = cat.packages[name].category;
    n[c] = (n[c] || 0) + 1;
  }
  return n;
};

/** Apply a whole desired category list: order, renames, additions, removals.
 *
 *  Taken as one transaction rather than per-row edits, because a rename has
 *  to move every package assigned to the old name in the same breath — the
 *  site build refuses to run on a package whose category is not in the list,
 *  so a half-applied rename is a broken repo. */
function applyCategories(cat, incoming) {
  const seen = new Set();
  for (const row of incoming) {
    const name = String(row.name || '').trim();
    if (!name) throw new Error('a category cannot have an empty name');
    if (seen.has(name)) throw new Error(`duplicate category "${name}"`);
    seen.add(name);
  }

  const counts = countByCategory(cat);
  const removed = cat.categories.filter((c) =>
    !incoming.some((r) => (r.from || r.name) === c));
  for (const c of removed) {
    if (counts[c]) {
      throw new Error(
        `"${c}" still has ${counts[c]} package${counts[c] > 1 ? 's' : ''} in it — ` +
        'move them somewhere else before deleting it');
    }
  }

  const meta = {};
  for (const row of incoming) {
    const name = String(row.name).trim();
    const from = row.from && row.from !== name ? row.from : null;
    if (from) {
      if (!cat.categories.includes(from)) throw new Error(`unknown category "${from}"`);
      for (const pkg of Object.values(cat.packages)) {
        if (pkg.category === from) pkg.category = name;
      }
    }
    const prev = (cat.category_meta || {})[from || name] || {};
    meta[name] = {
      glyph: String(row.glyph ?? prev.glyph ?? '·').trim() || '·',
      pitch: String(row.pitch ?? prev.pitch ?? '').trim(),
    };
  }

  cat.categories = incoming.map((r) => String(r.name).trim());
  cat.category_meta = meta;
  return cat;
}

/** A package name is only ever accepted if it is already a catalog key.
 *  Nothing from a request is allowed to build a path on its own. */
function docPath(cat, name) {
  if (!Object.prototype.hasOwnProperty.call(cat.packages, name)) return null;
  if (!/^[A-Za-z0-9_-]+$/.test(name)) return null;
  return path.join(DOCS, `${name}.md`);
}

const mtimeOf = (p) => (fs.existsSync(p) ? fs.statSync(p).mtimeMs : 0);

/** Frontmatter key order, so saved files stay diffable against each other. */
const FM_ORDER = ['package', 'summary', 'features', 'platforms', 'credit', 'video'];
function orderedData(data) {
  const out = {};
  for (const k of FM_ORDER) if (data[k] !== undefined) out[k] = data[k];
  for (const k of Object.keys(data)) if (!(k in out)) out[k] = data[k];
  return out;
}

/** The campaign's tiers, from gate_package -- the one place that knows
 *  them. Cached for the process: they change when the campaign does,
 *  which is not mid-session. */
let LADDER = null;
function tierLadder() {
  if (LADDER) return LADDER;
  try {
    const r = spawnSync(PYTHON, [GATE_PY, '--ladder'], { encoding: 'utf8' });
    LADDER = JSON.parse(r.stdout);
  } catch {
    LADDER = [];
  }
  return LADDER;
}

/** Gate or ungate through gate_package.py, never by editing catalog.json
 *  here: it writes catalog.json AND wrangler.toml together, and a package
 *  gated in one but not the other is a customer paying for a 403. */
function setAccess(name, tier) {
  const args = [GATE_PY, name];
  if (tier) args.push('--tier', tier); else args.push('--free');
  const r = spawnSync(PYTHON, args, { encoding: 'utf8' });
  if (r.status !== 0) {
    throw new Error((r.stderr || r.stdout || 'gate_package failed').trim());
  }
  return (r.stdout || '').trim();
}

function loadPackage(cat, name) {
  const p = docPath(cat, name);
  if (!p || !fs.existsSync(p)) return null;
  const raw = fs.readFileSync(p, 'utf8');
  const { data, content } = matter(raw);
  return {
    name,
    category: cat.packages[name].category,
    description: cat.packages[name].description || '',
    recommended: !!cat.packages[name].recommended,
    // `access` is the ENTRY tier id, or absent for a free package.
    // Editable here now: the ladder supplies real named tiers, so nothing
    // is invented, and gate_package keeps the two files in step.
    access: String(cat.packages[name].access || ''),
    plus: Boolean(cat.packages[name].access) && cat.packages[name].access !== 'free',
    data,
    body: content.replace(/^\n+/, ''),
    mtime: mtimeOf(p),
    stub: /TODO: no wiki content/.test(content),
    todos: (content.match(/TODO/g) || []).length,
    words: content.split(/\s+/).filter(Boolean).length,
  };
}

function state() {
  const cat = readCatalog();
  const ladder = tierLadder();
  const packages = Object.keys(cat.packages)
    .sort((a, b) => a.localeCompare(b, 'en', { sensitivity: 'base' }))
    .map((n) => {
      const p = loadPackage(cat, n);
      return p || {
        name: n, category: cat.packages[n].category,
        description: cat.packages[n].description || '',
        recommended: !!cat.packages[n].recommended,
        access: String(cat.packages[n].access || ''),
        plus: Boolean(cat.packages[n].access) && cat.packages[n].access !== 'free',
        data: {}, body: '', mtime: 0, stub: true, todos: 0, words: 0,
        missing: true,
      };
    });
  const counts = countByCategory(cat);
  const rec = readRecommends();
  return {
    recommendations: { intro: rec.intro || '', tools: rec.tools || [] },
    categories: cat.categories,
    categoryMeta: cat.categories.map((c) => ({
      name: c,
      glyph: (cat.category_meta?.[c] || {}).glyph || '·',
      pitch: (cat.category_meta?.[c] || {}).pitch || '',
      count: counts[c] || 0,
    })),
    icons: fs.readdirSync(ICONS).filter((f) => /\.(png|jpg)$/i.test(f)).sort(),
    // the campaign's tiers, so the UI can offer names while writing ids
    ladder,
    packages,
  };
}

// --- the TouchDesigner release console -------------------------------
// FNS_CMS answers only what a running TD can: PI dirty/save, live
// Pkgversion, Preflight, Stage, the FNS_About.Helpurl override.
const TD_PORTS = Array.from({ length: 10 }, (_, i) => 36770 + i);
const TD_TTL = 10000;
let tdCache = { at: 0, base: null };

/** Base URL of the release console, or null. Identified by its /api/ping
 *  marker rather than by an open port: FNS_CMS walks the range when its
 *  default is taken, and something else answering on a port it might have
 *  used must not be mistaken for it. */
async function tdBase() {
  if (tdCache.base !== null && Date.now() - tdCache.at < TD_TTL) return tdCache.base;
  let found = null;
  for (const port of TD_PORTS) {
    try {
      const r = await fetch(`http://127.0.0.1:${port}/api/ping`,
                            { signal: AbortSignal.timeout(250) });
      if (!r.ok) continue;
      const d = await r.json();
      if (d && d.service === 'fns-release') { found = `http://127.0.0.1:${port}`; break; }
    } catch {
      // nothing listening, or not ours -- keep walking
    }
  }
  tdCache = { at: Date.now(), base: found };
  return found;
}

function runBuild() {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [path.join(HERE, 'build-site.mjs')], {
      cwd: WEB,
    });
    let out = '';
    child.stdout.on('data', (d) => { out += d; });
    child.stderr.on('data', (d) => { out += d; });
    child.on('close', (code) => resolve({ ok: code === 0, code, output: out.trim() }));
    child.on('error', (e) => resolve({ ok: false, code: -1, output: String(e) }));
  });
}

// ---------------------------------------------------------------- http

const MIME = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2', '.ico': 'image/x-icon',
};

const json = (res, code, obj) => {
  const body = JSON.stringify(obj);
  res.writeHead(code, {
    'content-type': 'application/json',
    'content-length': Buffer.byteLength(body),
    'cache-control': 'no-store',
  });
  res.end(body);
};

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', (c) => {
      data += c;
      if (data.length > 4e6) reject(new Error('body too large'));
    });
    req.on('end', () => {
      try { resolve(data ? JSON.parse(data) : {}); } catch (e) { reject(e); }
    });
  });
}

/** Serve website/ so the CMS can preview the built pages on its own origin. */
function serveStatic(req, res, urlPath) {
  let rel = decodeURIComponent(urlPath.split('?')[0]);
  if (rel.endsWith('/')) rel += 'index.html';
  const full = path.join(WEB, rel);
  if (!full.startsWith(WEB + path.sep) || !fs.existsSync(full) || fs.statSync(full).isDirectory()) {
    res.writeHead(404, { 'content-type': 'text/plain' });
    return res.end('not found');
  }
  res.writeHead(200, {
    'content-type': MIME[path.extname(full).toLowerCase()] || 'application/octet-stream',
    'cache-control': 'no-store',
  });
  fs.createReadStream(full).pipe(res);
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${HOST}:${PORT}`);
  const p = url.pathname;

  try {
    if (p === '/' || p === '/cms') {
      const html = fs.readFileSync(path.join(HERE, 'cms.html'));
      res.writeHead(200, { 'content-type': MIME['.html'], 'cache-control': 'no-store' });
      return res.end(html);
    }

    if (p === '/api/state' && req.method === 'GET') {
      return json(res, 200, state());
    }

    if (p === '/api/categories' && req.method === 'PUT') {
      const { categories } = await readBody(req);
      if (!Array.isArray(categories) || !categories.length) {
        return json(res, 400, { error: 'expected a non-empty categories array' });
      }
      const cat = readCatalog();
      try {
        writeCatalog(applyCategories(cat, categories));
      } catch (e) {
        return json(res, 400, { error: e.message });
      }
      return json(res, 200, state());
    }

    if (p === '/api/pin' && req.method === 'POST') {
      // Download a community tool ONCE, here, and record what we got.
      // The pin is the whole safety argument for placing someone else's
      // code: it promises the bytes a user installs are the bytes a
      // curator looked at. If the author republishes, the hash stops
      // matching and the row degrades to a link rather than silently
      // installing something nobody checked.
      const { tox_url: toxUrl } = await readBody(req);
      const u = String(toxUrl || '').trim();
      if (!u.startsWith('https://') || !u.toLowerCase().endsWith('.tox')) {
        return json(res, 400, { error: 'tox_url must be an https link to a .tox file' });
      }
      try {
        const r = await fetch(u, { redirect: 'follow' });
        if (!r.ok) return json(res, 400, { error: `the author's server said ${r.status}` });
        const buf = Buffer.from(await r.arrayBuffer());
        if (!buf.length) return json(res, 400, { error: 'that URL returned an empty file' });
        // A .tox is a container; an HTML error page served with a 200 is
        // the common failure and would otherwise be pinned as if it were
        // the tool.
        if (buf.slice(0, 64).toString('latin1').trim().toLowerCase().startsWith('<')) {
          return json(res, 400, {
            error: 'that URL returned a web page, not a .tox -- link directly to the file',
          });
        }
        const sha = crypto.createHash('sha256').update(buf).digest('hex');
        return json(res, 200, {
          sha256: sha, bytes: buf.length,
          pinned_at: new Date().toISOString().slice(0, 10),
        });
      } catch (e) {
        return json(res, 400, { error: `could not fetch it: ${e.message}` });
      }
    }

    if (p === '/api/recommendations' && req.method === 'PUT') {
      const body = await readBody(req);
      const doc = readRecommends();
      const next = {
        ...doc,
        intro: String(body.intro ?? doc.intro ?? ''),
        tools: Array.isArray(body.tools) ? body.tools : doc.tools,
      };
      const bad = validateRecommends(next);
      if (bad.length) return json(res, 400, { error: bad.join('; ') });
      writeRecommends(next);
      return json(res, 200, state());
    }

    if (p === '/api/render' && req.method === 'POST') {
      const { markdown } = await readBody(req);
      return json(res, 200, { html: md.render(String(markdown || '')) });
    }

    if (p === '/api/build' && req.method === 'POST') {
      return json(res, 200, await runBuild());
    }

    // Everything under /api/td/ belongs to the live project, and is
    // forwarded verbatim. Deliberately a dumb pipe: the release logic
    // lives in TD, where the project is, and duplicating any of it here
    // is how the two surfaces drifted apart in the first place.
    if (p.startsWith('/api/td/')) {
      const base = await tdBase();
      if (!base) {
        return json(res, 503, {
          error: 'TouchDesigner is not running, or its release console is '
               + 'closed (pulse Open on /FNS_CMS).',
        });
      }
      const init = { method: req.method };
      if (req.method === 'POST') {
        init.headers = { 'content-type': 'application/json' };
        init.body = JSON.stringify(await readBody(req));
      }
      const r = await fetch(base + '/api/' + p.slice('/api/td/'.length), init);
      const text = await r.text();
      res.writeHead(r.status, { 'content-type': 'application/json' });
      return res.end(text);
    }

    if (p.startsWith('/api/package/')) {
      let cat = readCatalog();
      const name = decodeURIComponent(p.slice('/api/package/'.length));
      const file = docPath(cat, name);
      if (!file) return json(res, 404, { error: `unknown package "${name}"` });

      if (req.method === 'GET') {
        return json(res, 200, loadPackage(cat, name) || { error: 'no docs file' });
      }

      if (req.method === 'PUT') {
        const body = await readBody(req);

        // Refuse to clobber a file that changed underneath the editor —
        // most likely the seeder or a git operation ran since it loaded.
        const onDisk = mtimeOf(file);
        if (body.mtime && onDisk && Math.abs(onDisk - body.mtime) > 1) {
          return json(res, 409, {
            error: 'This file changed on disk since you opened it. Reload before saving.',
          });
        }

        // Gating goes through gate_package -- it writes catalog.json AND
        // wrangler.toml together, and a package gated in one but not the
        // other is a customer paying for a 403. It runs FIRST and the
        // catalogue is re-read after, because that call rewrites the file
        // this handler is holding in memory.
        if (typeof body.access === 'string') {
          try {
            setAccess(name, body.access.trim());
          } catch (e) {
            return json(res, 400, { error: String(e.message || e) });
          }
          cat = readCatalog();
        }

        if (typeof body.category === 'string' || typeof body.description === 'string'
            || typeof body.recommended === 'boolean') {
          const entry = cat.packages[name];
          if (typeof body.category === 'string') {
            if (!cat.categories.includes(body.category)) {
              return json(res, 400, { error: `unknown category "${body.category}"` });
            }
            entry.category = body.category;
          }
          if (typeof body.description === 'string') {
            entry.description = body.description.trim();
          }
          // The picker's Recommended preset (the first-run welcome). Stored
          // as presence, not as `false`: an unflagged package stays a
          // two-line entry, and the diff of toggling one is one line.
          if (typeof body.recommended === 'boolean') {
            if (body.recommended) entry.recommended = true;
            else delete entry.recommended;
          }
          writeCatalog(cat);
        }

        const data = orderedData({ ...(body.data || {}), package: name });
        // Trim blank lines off the ends only. A plain .trim() would also eat
        // the two trailing spaces on the final line, which are a markdown
        // hard line break — the CMS must not silently rewrite prose.
        const prose = String(body.body || '').replace(/^\n+/, '').replace(/\n+$/, '');
        const text = matter.stringify(`\n${prose}\n`, data, { lineWidth: -1 });
        fs.writeFileSync(file, text);

        return json(res, 200, loadPackage(readCatalog(), name));
      }
    }

    return serveStatic(req, res, p);
  } catch (err) {
    return json(res, 500, { error: String(err && err.message || err) });
  }
});

server.listen(PORT, HOST, () => {
  console.log(`FNSTools CMS  ->  http://${HOST}:${PORT}`);
  console.log('editing packaging/catalog.json and packaging/docs/*.md directly.');
  console.log('review with `git diff`, undo with `git checkout -- packaging/`.');
});
