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

import { spawn } from 'node:child_process';
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
const CATALOG = path.join(REPO, 'packaging', 'catalog.json');
const ICONS = path.join(REPO, 'icons');

const PORT = Number(process.env.CMS_PORT || 8787);
const HOST = '127.0.0.1';

const md = new MarkdownIt({ html: true, linkify: true });

// ------------------------------------------------------------ helpers

const readCatalog = () => JSON.parse(fs.readFileSync(CATALOG, 'utf8'));

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

function loadPackage(cat, name) {
  const p = docPath(cat, name);
  if (!p || !fs.existsSync(p)) return null;
  const raw = fs.readFileSync(p, 'utf8');
  const { data, content } = matter(raw);
  return {
    name,
    category: cat.packages[name].category,
    description: cat.packages[name].description || '',
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
  const packages = Object.keys(cat.packages)
    .sort((a, b) => a.localeCompare(b, 'en', { sensitivity: 'base' }))
    .map((n) => {
      const p = loadPackage(cat, n);
      return p || {
        name: n, category: cat.packages[n].category,
        description: cat.packages[n].description || '',
        data: {}, body: '', mtime: 0, stub: true, todos: 0, words: 0,
        missing: true,
      };
    });
  const counts = countByCategory(cat);
  return {
    categories: cat.categories,
    categoryMeta: cat.categories.map((c) => ({
      name: c,
      glyph: (cat.category_meta?.[c] || {}).glyph || '·',
      pitch: (cat.category_meta?.[c] || {}).pitch || '',
      count: counts[c] || 0,
    })),
    icons: fs.readdirSync(ICONS).filter((f) => /\.(png|jpg)$/i.test(f)).sort(),
    packages,
  };
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

    if (p === '/api/render' && req.method === 'POST') {
      const { markdown } = await readBody(req);
      return json(res, 200, { html: md.render(String(markdown || '')) });
    }

    if (p === '/api/build' && req.method === 'POST') {
      return json(res, 200, await runBuild());
    }

    if (p.startsWith('/api/package/')) {
      const cat = readCatalog();
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

        if (typeof body.category === 'string' || typeof body.description === 'string') {
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
