// Generates website/docs/ from packaging/docs/*.md + packaging/catalog.json,
// and injects the tool catalogue into index.html between the TOOLS markers.
//
// packaging/docs/ is the source of truth for prose; catalog.json is the
// source of truth for category and description (it already feeds the
// installer picker, so duplicating either into frontmatter would give us
// two answers to the same question). The build joins them on package name
// and refuses to produce a site if they disagree.
//
//   node tools/build-site.mjs      then      npx pagefind --site docs
//
// website/docs/ is disposable: it is wiped and rebuilt every run. Nothing
// hand-authored may live there -- docs.css and docs.js sit at website/.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import matter from 'gray-matter';
import MarkdownIt from 'markdown-it';
import anchor from 'markdown-it-anchor';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB = path.dirname(HERE);
const REPO = path.dirname(WEB);
const SRC = path.join(REPO, 'packaging', 'docs');
const CATALOG = path.join(REPO, 'packaging', 'catalog.json');
const ICONS = path.join(REPO, 'icons');
const OUT = path.join(WEB, 'docs');

const SITE = 'https://tools.functionstore.xyz';
const GH = 'https://github.com/function-store/FunctionStore_tools';
// Rolling pointer published by packaging/publish.py; base_url in manifest.json.
const BUCKET = 'https://pub-8001b4bd92174be7a4544571b53f23da.r2.dev/fnstools';
const EDIT_BASE = `${GH}/blob/main/packaging/docs`;

const problems = [];
const fail = (msg) => problems.push(msg);

/** Anchor slug. Must stay identical to slugify() in docs_seed_from_wiki.py. */
function slugify(text) {
  return String(text)
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/`/g, '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s_-]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/-{2,}/g, '-')
    .replace(/^-+|-+$/g, '');
}

/** URL slug for a package. Must match _helpUrl() in build_manifest.py. */
const packageSlug = (name) => name.toLowerCase().replace(/_/g, '-');

const esc = (s) => String(s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;');

// ---------------------------------------------------------------- load

const catalog = JSON.parse(fs.readFileSync(CATALOG, 'utf8'));
const categories = catalog.categories;
const curated = catalog.packages;

// Presentation per category — the glyph on each tile and the one-line pitch
// above each section. Curated in catalog.json next to the category list, so
// renaming or adding a category in the CMS carries them along; hardcoding
// them here meant a rename silently lost both. The repo's icons/*.png are
// 30x19 UI chrome and unusable at tile size, hence unicode glyphs.
const catMeta = catalog.category_meta || {};
const GLYPH = Object.fromEntries(
  categories.map((c) => [c, (catMeta[c] && catMeta[c].glyph) || '·']));
const CATEGORY_PITCH = Object.fromEntries(
  categories.map((c) => [c, (catMeta[c] && catMeta[c].pitch) || '']));

if (!fs.existsSync(SRC)) {
  console.error(`missing ${path.relative(REPO, SRC)} — run packaging/docs_seed_from_wiki.py first`);
  process.exit(1);
}

const files = fs.readdirSync(SRC).filter((f) => f.endsWith('.md')).sort();
const pages = [];

for (const file of files) {
  const name = file.replace(/\.md$/, '');
  const raw = fs.readFileSync(path.join(SRC, file), 'utf8');
  const { data, content } = matter(raw);
  if (!curated[name]) {
    fail(`packaging/docs/${file} has no entry in catalog.json (name must match a package exactly)`);
    continue;
  }
  if (data.package && data.package !== name) {
    fail(`packaging/docs/${file}: frontmatter package "${data.package}" does not match the filename`);
  }
  pages.push({
    name,
    slug: packageSlug(name),
    file,
    meta: data,
    body: content,
    category: curated[name].category,
    description: curated[name].description || '',
  });
}

for (const name of Object.keys(curated)) {
  if (!pages.some((p) => p.name === name)) {
    fail(`catalog.json has package "${name}" with no packaging/docs/${name}.md`);
  }
}

if (problems.length) {
  console.error('build refused:\n' + problems.map((p) => `  - ${p}`).join('\n'));
  process.exit(1);
}

const unknownCategory = pages.filter((p) => !categories.includes(p.category));
if (unknownCategory.length) {
  console.error('build refused: packages in a category missing from catalog.categories:\n' +
    unknownCategory.map((p) => `  - ${p.name} (${p.category})`).join('\n'));
  process.exit(1);
}

// ------------------------------------------------------------- render

const md = new MarkdownIt({ html: true, linkify: true, breaks: false })
  .use(anchor, {
    slugify,
    permalink: anchor.permalink.linkInsideHeader({
      symbol: '#', placement: 'after', class: 'heading-anchor',
      ariaHidden: true,
    }),
  });

const anchorsOf = new Map();   // slug -> Set of heading anchors

for (const p of pages) {
  const ids = new Set();
  p.html = md.render(p.body);
  for (const m of p.html.matchAll(/<h[2-6][^>]*\sid="([^"]+)"/g)) ids.add(m[1]);
  anchorsOf.set(p.slug, ids);
}

// Internal links must resolve. This is the check that would have caught the
// wiki's own dead anchors (#-custompar-tools, #opmenu-mod, ...), and it also
// covers the hand-written landing page, whose /docs/ links are easy to typo.
function checkLinks(html, where, selfSlug) {
  for (const m of html.matchAll(/href="(\/docs\/[^"#]*)(#[^"]*)?"/g)) {
    const wanted = m[1].replace(/^\/docs\//, '').replace(/\/+$/, '');
    if (wanted && !anchorsOf.has(wanted)) {
      fail(`${where}: link to /docs/${wanted}/ but no such package page`);
      continue;
    }
    const frag = m[2] ? m[2].slice(1) : '';
    const ids = anchorsOf.get(wanted || selfSlug);
    if (frag && ids && !ids.has(frag)) {
      fail(`${where}: link to /docs/${wanted || selfSlug}/#${frag} but that heading does not exist`);
    }
  }
}

for (const p of pages) checkLinks(p.html, p.file, p.slug);

const landingPath = path.join(WEB, 'index.html');
if (fs.existsSync(landingPath)) {
  // Only the hand-written parts. The TOOLS block still holds the PREVIOUS
  // build's output at this point, so checking it would deadlock the build
  // on any package rename: the stale block fails the check, and the check
  // runs before the block is regenerated from the catalog. What the build
  // writes there is correct by construction.
  const landingSrc = fs.readFileSync(landingPath, 'utf8')
    .replace(/<!-- TOOLS:START -->[\s\S]*?<!-- TOOLS:END -->/, '');
  checkLinks(landingSrc, 'index.html', null);
}

if (problems.length) {
  console.error('build refused — unresolved internal links:\n' +
    problems.map((p) => `  - ${p}`).join('\n'));
  process.exit(1);
}

// ------------------------------------------------------------ chrome

const navLinks = [
  ['/#get', 'Install'],
  ['/#tools', 'Tools'],
  ['/docs/', 'Docs'],
  ['/#credits', 'Credits'],
  ['https://patreon.com/function_store', 'Patreon'],
];

function head(title, description, canonical) {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
<link rel="icon" href="/favicon.png" type="image/png" />
<link rel="apple-touch-icon" href="/favicon.png" />
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}" />
<meta property="og:title" content="${esc(title)}" />
<meta property="og:description" content="${esc(description)}" />
<meta property="og:type" content="website" />
<meta property="og:image" content="${SITE}/og-image.png" />
<link rel="canonical" href="${canonical}" />
<meta name="robots" content="index, follow" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/site-nav.css">
<link rel="stylesheet" href="/docs.css">
<link rel="stylesheet" href="/docs/pagefind/pagefind-ui.css" onerror="this.remove()">
</head>
<body>`;
}

function header(current) {
  const links = navLinks.map(([href, label]) => {
    const isCurrent = href === current;
    const ext = href.startsWith('http') ? ' target="_blank" rel="noopener"' : '';
    return `      <a href="${href}"${isCurrent ? ' aria-current="page"' : ''}${ext}>${label}</a>`;
  }).join('\n') +
  `\n      <a class="btn btn-secondary" href="${GH}" target="_blank" rel="noopener">GitHub</a>`;
  return `<header class="site">
  <div class="site-inner">
    <div class="brand">
      <img class="brand-logo" src="/favicon.png" alt="" width="28" height="28" decoding="async" />
      <div class="brand-lockup">
        <a href="/" class="brand-name">FNSTools</a>
        <span class="brand-credit">by <a href="https://functionstore.xyz/link-in-bio" target="_blank" rel="noopener noreferrer">Function Store</a></span>
      </div>
    </div>
    <button type="button" class="nav-toggle" aria-expanded="false" aria-controls="site-nav" aria-label="Open menu">
      <span class="nav-toggle__bar" aria-hidden="true"></span>
      <span class="nav-toggle__bar" aria-hidden="true"></span>
      <span class="nav-toggle__bar" aria-hidden="true"></span>
    </button>
    <nav id="site-nav" class="site-nav">
${links}
      <a class="btn btn-primary" href="/#get">Get FNSTools →</a>
    </nav>
  </div>
</header>`;
}

const FOOT = `<footer class="site">
  <div class="wrap footer-inner">
    <div>© 2026 FNSTools · Built for TouchDesigner</div>
    <div class="footer-links">
      <a href="/docs/">Docs</a>
      <a href="${GH}" target="_blank" rel="noopener">GitHub</a>
      <a href="https://discord.gg/b4CaCP3g3K" target="_blank" rel="noopener">Discord</a>
      <a href="https://derivative.ca" target="_blank" rel="noopener">TouchDesigner</a>
      <a href="https://patreon.com/function_store" target="_blank" rel="noopener">Patreon</a>
      <a href="https://functionstore.xyz" target="_blank" rel="noopener">Function Store</a>
      <a href="mailto:dan%2Bfnstools@functionstore.xyz?subject=FNSTools%20feedback">Feedback</a>
    </div>
  </div>
</footer>
<script src="/site-nav.js" defer></script>
<!-- Pagefind is emitted by the search step that runs after this build.
     Both scripts are deferred so they run in order; if the index has not
     been generated yet this 404s and docs.js just skips the search UI. -->
<script src="/docs/pagefind/pagefind-ui.js" defer onerror="this.remove()"></script>
<script src="/docs.js" defer></script>
<script>
  window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
</script>
<script src="/_vercel/insights/script.js" defer></script>
</body>
</html>`;

function sidebar(currentSlug) {
  const groups = categories.map((cat) => {
    const items = pages
      .filter((p) => p.category === cat)
      .sort((a, b) => a.name.localeCompare(b.name, 'en', { sensitivity: 'base' }))
      .map((p) => `      <li><a href="/docs/${p.slug}/"${p.slug === currentSlug ? ' aria-current="page"' : ''}>${esc(p.name)}</a></li>`)
      .join('\n');
    if (!items) return '';
    return `  <div class="side-group">
    <h3><span class="side-glyph" aria-hidden="true">${GLYPH[cat] || '·'}</span>${esc(cat)}</h3>
    <ul>
${items}
    </ul>
  </div>`;
  }).filter(Boolean).join('\n');
  return `<aside class="docs-side" id="docs-side">
  <div class="docs-search"><div id="search"></div></div>
${groups}
</aside>`;
}

// ------------------------------------------------------------- write

// Rebuild from scratch, but keep docs/pagefind/ — that is the search index,
// written by the separate pagefind step. Wiping it here would silently drop
// search from the site whenever this script is run on its own (the markup
// degrades quietly, so the loss is invisible until someone tries to search).
if (fs.existsSync(OUT)) {
  for (const entry of fs.readdirSync(OUT)) {
    if (entry === 'pagefind') continue;
    fs.rmSync(path.join(OUT, entry), { recursive: true, force: true });
  }
}
fs.mkdirSync(path.join(OUT, 'assets', 'icons'), { recursive: true });
let copied = 0;
for (const f of fs.readdirSync(ICONS)) {
  fs.copyFileSync(path.join(ICONS, f), path.join(OUT, 'assets', 'icons', f));
  copied++;
}

for (const p of pages) {
  const dir = path.join(OUT, p.slug);
  fs.mkdirSync(dir, { recursive: true });

  const badges = [
    `<span class="badge badge-cat">${GLYPH[p.category] || '·'} ${esc(p.category)}</span>`,
  ];
  const plats = p.meta.platforms;
  if (Array.isArray(plats) && plats.length && plats.length < 2) {
    badges.push(`<span class="badge badge-warn">${esc(plats.join(', '))} only</span>`);
  }
  if (p.meta.credit && p.meta.credit.name) {
    const c = p.meta.credit;
    badges.push(c.url
      ? `<span class="badge">by <a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.name)}</a></span>`
      : `<span class="badge">by ${esc(c.name)}</span>`);
  }

  const video = p.meta.video
    ? `<div class="embed-video"><iframe src="https://www.youtube.com/embed/${esc(String(p.meta.video).split(/[/=]/).pop())}" title="${esc(p.name)} walkthrough" loading="lazy" allowfullscreen></iframe></div>`
    : '';

  const onThisPage = (p.meta.features || []).length > 1
    ? `<nav class="toc"><span>On this page</span><ul>${(p.meta.features || [])
        .map((f) => `<li><a href="#${esc(f.anchor)}">${esc(f.name)}</a></li>`).join('')}</ul></nav>`
    : '';

  const html = `${head(`${p.name} — FNSTools docs`, p.description || `${p.name} documentation.`, `${SITE}/docs/${p.slug}/`)}
${header('/docs/')}
<div class="docs-layout wrap">
${sidebar(p.slug)}
<main class="docs-main" data-pagefind-body>
  <p class="crumbs"><a href="/docs/">Docs</a> <span aria-hidden="true">/</span> ${esc(p.category)}</p>
  <h1>${esc(p.name)}</h1>
  ${p.description ? `<p class="lede">${esc(p.description)}</p>` : ''}
  <p class="badges">${badges.join(' ')}</p>
  ${video}
  ${onThisPage}
  <div class="docs-body">
${p.html}
  </div>
  <p class="edit-page"><a href="${EDIT_BASE}/${p.file}" target="_blank" rel="noopener">Edit this page on GitHub →</a></p>
</main>
</div>
${FOOT}`;
  fs.writeFileSync(path.join(dir, 'index.html'), html);
}

// docs index
const indexGroups = categories.map((cat) => {
  const items = pages
    .filter((p) => p.category === cat)
    .sort((a, b) => a.name.localeCompare(b.name, 'en', { sensitivity: 'base' }))
    .map((p) => `      <a class="doc-card" href="/docs/${p.slug}/">
        <strong>${esc(p.name)}</strong>
        <span>${esc(p.description || p.meta.summary)}</span>
      </a>`).join('\n');
  if (!items) return '';
  return `  <section class="doc-cat">
    <h2 id="${slugify(cat)}"><span class="side-glyph" aria-hidden="true">${GLYPH[cat] || '·'}</span>${esc(cat)}</h2>
    <div class="doc-cards">
${items}
    </div>
  </section>`;
}).filter(Boolean).join('\n');

fs.writeFileSync(path.join(OUT, 'index.html'), `${head(
  'FNSTools docs — every tool in the toolkit',
  `Documentation for all ${pages.length} FNSTools packages: templates, parameter tools, network shortcuts, MIDI/OSC mapping and extension helpers for TouchDesigner.`,
  `${SITE}/docs/`)}
${header('/docs/')}
<div class="docs-layout wrap">
${sidebar(null)}
<main class="docs-main docs-index" data-pagefind-body>
  <h1>Documentation</h1>
  <p class="lede">Every package that ships with FNSTools. Each tool installs on its own, so each one is documented on its own.</p>
${indexGroups}
</main>
</div>
${FOOT}`);

// ------------------------------- tool catalogue injected into index.html

const grid = categories.map((cat) => {
  const items = pages
    .filter((p) => p.category === cat)
    .sort((a, b) => a.name.localeCompare(b.name, 'en', { sensitivity: 'base' }))
    .map((p) => `        <div class="feat">
          <div class="feat-icon" aria-hidden="true">${GLYPH[cat] || '·'}</div>
          <div class="feat-text"><strong><a href="/docs/${p.slug}/">${esc(p.name)}</a></strong><span>${esc(p.description || p.meta.summary)}</span></div>
        </div>`).join('\n');
  if (!items) return '';
  return `      <div class="feature-cat">
        <div class="feature-cat-head">
          <h3>${esc(cat)}</h3>
          <p>${esc(CATEGORY_PITCH[cat] || '')}</p>
        </div>
        <div class="feature-cat-list">
${items}
        </div>
      </div>`;
}).filter(Boolean).join('\n');

// The published release, stamped into the static hrefs at build time.
//
// The page also refreshes these at runtime, but that fetch cannot be relied
// on: the r2.dev bucket serves no Access-Control-Allow-Origin header, so the
// browser blocks it (TDMap's site has the same silent failure). Stamping here
// is what actually keeps the download links current — the runtime fetch only
// helps if CORS is enabled on the bucket later.
async function publishedRelease() {
  // CI sets this. Without it the stamped release depends on what is published
  // at the moment the build runs, so a release cut between commit and CI would
  // make index.html differ from the committed copy and fail the drift check
  // for reasons nobody changed.
  if (process.env.FNSTOOLS_NO_RELEASE_FETCH) return null;
  const url = `${BUCKET}/manifest.json`;
  try {
    const res = await fetch(url, {
      cache: 'no-store',
      signal: AbortSignal.timeout(8000),
      headers: { 'user-agent': 'Mozilla/5.0 (fnstools-site-build)' },
    });
    if (!res.ok) return null;
    const m = await res.json();
    return m && m.release ? m : null;
  } catch {
    return null;
  }
}

const landing = path.join(WEB, 'index.html');
if (fs.existsSync(landing)) {
  const src = fs.readFileSync(landing, 'utf8');
  const re = /(<!-- TOOLS:START -->)[\s\S]*?(<!-- TOOLS:END -->)/;
  if (!re.test(src)) {
    console.error('index.html is missing the <!-- TOOLS:START --> / <!-- TOOLS:END --> markers');
    process.exit(1);
  }
  let out = src.replace(re, `$1\n${grid}\n      $2`);

  // "N tools" always matches the catalogue this build actually rendered.
  out = out.replace(/(<span class="js-fns-count">)[^<]*(<\/span>)/g,
    `$1${pages.length}$2`);

  const live = await publishedRelease();
  if (live) {
    out = out.replace(/(r2\.dev\/fnstools\/)v[^/"]+\//g, `$1${live.release}/`);
    // No leading space: the span sits inside a .btn, which is inline-flex
    // with its own 8px gap, so one would render as a double space.
    out = out.replace(/(<span class="js-fns-ver">)[^<]*(<\/span>)/g,
      `$1${live.release}$2`);
    console.log(`stamped release ${live.release} (${live.packages?.length ?? '?'} packages published)`);
    if (live.packages && live.packages.length !== pages.length) {
      console.log(`note: catalog has ${pages.length} packages but ${live.release} publishes ` +
        `${live.packages.length} — the site lists the catalog, so these align at the next publish`);
    }
  } else if (process.env.FNSTOOLS_NO_RELEASE_FETCH) {
    console.log('release fetch skipped — download links keep the release already in index.html');
  } else {
    console.log('note: could not reach the release manifest — download links keep the release already in index.html');
  }
  fs.writeFileSync(landing, out);
} else {
  console.warn('note: website/index.html does not exist yet — tool catalogue not injected');
}

console.log(`built ${pages.length} package pages + index, ${copied} icons copied`);
const stubs = pages.filter((p) => /TODO: no wiki content/.test(p.body));
if (stubs.length) {
  console.log(`${stubs.length} pages are still stubs: ${stubs.map((p) => p.name).join(', ')}`);
}
