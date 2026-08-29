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

const SITE = 'https://functionstore.tools';
const GH = 'https://github.com/function-store/FunctionStore_tools';
// Rolling pointer published by packaging/publish.py; base_url in manifest.json.
const BUCKET = 'https://storage.functionstore.tools/fnstools';
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

/** A binding's identity, for matching a hand-written sentence to the key
 *  the manager actually reports. The two spellings drift by nature --
 *  'alt.F7' from TD, 'Alt+F7 (Opt+F7 on Mac)' from a human -- so compare
 *  the modifier set, not the text: lowercase, drop any parenthetical, and
 *  treat . + - and space as the same separator. */
function keyId(raw) {
  return String(raw).toLowerCase().replace(/\([^)]*\)/g, '')
    .split(/[.+\-\s]+/).filter(Boolean).sort().join('+');
}

/** TouchDesigner stores a binding as `ctrl.alt.q`, and one par can hold
 *  several separated by spaces. Readers know it as Ctrl+Alt+Q. */
function prettyKeys(raw) {
  return String(raw).trim().split(/\s+/).map((combo) => combo.split('.')
    .map((k) => (k.length === 1 ? k.toUpperCase()
      : k.charAt(0).toUpperCase() + k.slice(1)))
    .join('+')).join('  /  ');
}

/** Hotkeys per package, from the REPO manifest -- the one
 *  build_manifest just wrote from FNS_HotkeyManager. Not the published
 *  manifest fetched later for /get/: that one is a release behind by
 *  definition, and a docs page should describe the toolkit as it is. */
const HOTKEYS = (() => {
  try {
    const doc = JSON.parse(fs.readFileSync(
      path.join(REPO, 'packaging', 'manifest.json'), 'utf8'));
    const out = {};
    for (const pkg of doc.packages || []) {
      if ((pkg.hotkeys || []).length) out[pkg.name] = pkg.hotkeys;
    }
    return out;
  } catch {
    return {};   // no manifest yet: pages build without a shortcuts block
  }
})();

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

// Entitlement. `access` in catalog.json NAMES A TIER (docs/GatedDeliveryResearch
// §9.3), so anything that is not the literal 'free' is gated. The site says
// "Plus" and stops there on purpose: which tier covers which package is a
// SERVER-side map, and a copy of it here would be the second place that
// answer lives. Absent means free, so a catalog written before gating
// existed reads correctly.
const isPlus = (name) => {
  const a = curated[name] && curated[name].access;
  return Boolean(a) && a !== 'free';
};
const PLUS_MARK = '<span class="plus-mark">Plus</span>';

// Curated site content: the other Function Store products. Site-only —
// packaging/ never reads it. One source, injected into both the landing page
// and /plus/, because two hand-kept copies of the same two cards drift.
const FAMILY = path.join(WEB, 'content', 'family.json');
const family = fs.existsSync(FAMILY)
  ? (JSON.parse(fs.readFileSync(FAMILY, 'utf8')).products || [])
  : [];
if (!family.length) {
  console.warn('note: website/content/family.json missing or empty — the "More from Function Store" blocks will be empty');
}

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

// Kept in step with the hand-written nav in index.html — the header markup
// is duplicated the same way the tokens are, and a visitor moving between
// the landing page and a docs page should not see the links change.
const navLinks = [
  ['/#get', 'Install'],
  ['/#tools', 'Tools'],
  ['/plus/', 'Plus'],
  ['/docs/', 'Docs'],
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

// Shared by the docs pages and by /get/ — every page below the landing page
// ends the same way, so the footer markup has one definition.
const FOOTER = `<footer class="site">
  <div class="wrap footer-inner">
    <div>© 2026 FNSTools · Built for TouchDesigner</div>
    <div class="footer-links">
      <a href="/docs/">Docs</a>
      <a href="/plus/">Plus</a>
      <a href="/privacy/">Privacy</a>
      <a href="/terms/">Terms</a>
      <a href="${GH}" target="_blank" rel="noopener">GitHub</a>
      <a href="https://discord.gg/b4CaCP3g3K" target="_blank" rel="noopener">Discord</a>
      <a href="https://derivative.ca" target="_blank" rel="noopener">TouchDesigner</a>
      <a href="https://patreon.com/function_store" target="_blank" rel="noopener">Patreon</a>
      <a href="https://functionstore.xyz" target="_blank" rel="noopener">Function Store</a>
      <a href="mailto:dan%2Bfnstools@functionstore.xyz?subject=FNSTools%20feedback">Feedback</a>
    </div>
  </div>
</footer>`;

const ANALYTICS = `<script>
  window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
</script>
<script src="/_vercel/insights/script.js" defer></script>`;

const FOOT = `${FOOTER}
<script src="/site-nav.js" defer></script>
<!-- Pagefind is emitted by the search step that runs after this build.
     Both scripts are deferred so they run in order; if the index has not
     been generated yet this 404s and docs.js just skips the search UI. -->
<script src="/docs/pagefind/pagefind-ui.js" defer onerror="this.remove()"></script>
<script src="/docs.js" defer></script>
${ANALYTICS}
</body>
</html>`;

function sidebar(currentSlug) {
  const groups = categories.map((cat) => {
    const items = pages
      .filter((p) => p.category === cat)
      .sort((a, b) => a.name.localeCompare(b.name, 'en', { sensitivity: 'base' }))
      .map((p) => `      <li><a href="/docs/${p.slug}/"${p.slug === currentSlug ? ' aria-current="page"' : ''}>${esc(p.name)}${isPlus(p.name) ? PLUS_MARK : ''}</a></li>`)
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
  // A Plus package is documented exactly like a free one — the decision was
  // "visible and locked", so the page is public and complete. What differs is
  // one badge and one callout saying how to get it.
  if (isPlus(p.name)) badges.push(`<a class="badge badge-cat" href="/plus/">◆ Plus</a>`);
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

  const plusNote = isPlus(p.name) ? `<div class="plus-note">
    <p><strong>This one is a Plus tool.</strong> It installs through the same picker as
    everything else, and unlocks with a Patreon membership or a licence key redeemed inside
    TouchDesigner. Everything else in the toolkit stays free and MIT.</p>
    <p><a href="/plus/">How Plus works →</a></p>
  </div>` : '';

  const features = p.meta.features || [];
  const featIcon = (f) => (f.icon
    ? `<img class="feat-icon" src="/docs/assets/icons/${esc(f.icon)}" alt="" `
      + `width="18" height="18" decoding="async" />` : '');

  const onThisPage = features.length > 1
    ? `<nav class="toc"><span>On this page</span><ul>${features
        .map((f) => `<li><a href="#${esc(f.anchor)}">${featIcon(f)}${esc(f.name)}</a></li>`).join('')}</ul></nav>`
    : '';

  // The icon and the hotkeys are authored per feature in the CMS and used
  // to reach nothing. Inject them into the rendered body by anchor, so the
  // markdown stays plain markdown and no doc has to be re-authored.
  let body = p.html;
  for (const f of features) {
    if (!f.icon) continue;
    // markdown-it-anchor emits <h2 id="anchor">Name</h2>
    const re = new RegExp(`(<h2 id="${f.anchor}"[^>]*>)([\\s\\S]*?)(</h2>)`);
    body = body.replace(re, (m, open, text, close) =>
      `${open}${featIcon(f)}${text}${close}`);
  }

  // Shortcuts: the KEYS come from the manifest, which build_manifest
  // fills from FNS_HotkeyManager on every build, so a rebound key
  // reaches the site with no prose edited. The sentence comes from the
  // doc, because nothing in the project knows what a shortcut MEANS.
  // A key with no sentence is still listed: knowing one exists beats
  // not knowing.
  const said = new Map();
  // Top-level `hotkeys:` is where the CMS writes now -- the keys belong to
  // the PACKAGE, not to whichever heading someone once attached them to.
  for (const h of (p.meta.hotkeys || [])) {
    if (h && h.keys && h.does) said.set(keyId(h.keys), h.does);
  }
  for (const f of features) {
    for (const h of (f.hotkeys || [])) {
      const k = typeof h === 'string' ? h.split('=')[0] : (h.keys || '');
      const v = typeof h === 'string'
        ? h.split('=').slice(1).join('=').trim() : (h.does || '');
      if (String(k).trim() && v) said.set(keyId(k), v);
    }
  }
  const bound = HOTKEYS[p.name] || [];
  const shortcuts = bound.length ? `<section class="shortcuts">
    <h2 id="shortcuts">Shortcuts</h2>
    <p class="hint-line">Global — they fire anywhere in TouchDesigner. Shortcuts scoped to a single panel are a local control scheme and are not listed here.</p>
    <ul class="feat-keys">${bound.map((h) => {
      const what = said.get(keyId(h.keys)) || '';
      return `<li><kbd>${esc(prettyKeys(h.keys))}</kbd>${
        what ? md.renderInline(what) : ''}</li>`;
    }).join('')}</ul>
  </section>` : '';

  const html = `${head(`${p.name} — FNSTools docs`, p.description || `${p.name} documentation.`, `${SITE}/docs/${p.slug}/`)}
${header('/docs/')}
<div class="docs-layout wrap">
${sidebar(p.slug)}
<main class="docs-main" data-pagefind-body>
  <p class="crumbs"><a href="/docs/">Docs</a> <span aria-hidden="true">/</span> ${esc(p.category)}</p>
  <h1>${esc(p.name)}</h1>
  ${p.description ? `<p class="lede">${esc(p.description)}</p>` : ''}
  <p class="badges">${badges.join(' ')}</p>
  ${plusNote}
  ${video}
  ${onThisPage}
  ${shortcuts}
  <div class="docs-body">
${body}
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
        <strong>${esc(p.name)}${isPlus(p.name) ? PLUS_MARK : ''}</strong>
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

// One fold per category. 49 packages listed flat is a wall nobody reads, and
// the landing page's job is to say what KIND of thing is in here — so the
// category, its pitch and its count stay in the open and the list opens on
// demand. <details> keeps it working with JS off and findable by Ctrl+F.
//
// Core is open by default: it is the shortest way to answer "what is this
// thing actually made of" for someone who just arrived.
const grid = categories.map((cat) => {
  const inCat = pages
    .filter((p) => p.category === cat)
    .sort((a, b) => a.name.localeCompare(b.name, 'en', { sensitivity: 'base' }));
  const items = inCat.map((p) => `          <div class="feat">
            <div class="feat-icon" aria-hidden="true">${GLYPH[cat] || '·'}</div>
            <div class="feat-text"><strong><a href="/docs/${p.slug}/">${esc(p.name)}</a>${isPlus(p.name) ? PLUS_MARK : ''}</strong><span>${esc(p.description || p.meta.summary)}</span></div>
          </div>`).join('\n');
  if (!items) return '';
  const plusHere = inCat.filter((p) => isPlus(p.name)).length;
  const count = `${inCat.length} tool${inCat.length === 1 ? '' : 's'}`
    + (plusHere ? ` · ${plusHere} Plus` : '');
  return `      <details class="cat"${cat === 'Core' ? ' open' : ''}>
        <summary>
          <span class="cat-glyph" aria-hidden="true">${GLYPH[cat] || '·'}</span>
          <span>
            <span class="cat-name">${esc(cat)}</span>
            <span class="cat-pitch">${esc(CATEGORY_PITCH[cat] || '')}</span>
          </span>
          <span class="cat-count">${count}</span>
        </summary>
        <div class="cat-list">
${items}
        </div>
      </details>`;
}).filter(Boolean).join('\n');

// ------------------------------- the rest of the family, from family.json
const familyBlock = family.map((p) => `      <a class="prod" href="${esc(p.url)}" target="_blank" rel="noopener">
        <span class="prod-kind">${esc(p.kind || '')}</span>
        <span class="prod-name">${esc(p.name)} ↗</span>
        <span class="prod-pitch">${esc(p.pitch || '')}</span>
        <span class="prod-access">${esc(p.access || '')}</span>
      </a>`).join('\n');

// ------------------------------- picker preview injected into index.html
//
// A depiction of /get/ on the landing page, built from the same catalogue
// the picker lists — so it can never show a tool that no longer ships, and
// the categories it shows are simply the first two the CMS puts after Core.
// Static markup inside one link: the real thing is one click away, and a
// second copy of the picker's logic here would be a second thing to keep
// true.
const previewCats = categories.filter((c) => c !== 'Core').slice(0, 2);
const previewBlock = previewCats.map((cat) => {
  const items = pages
    .filter((p) => p.category === cat)
    .sort((a, b) => a.name.localeCompare(b.name, 'en', { sensitivity: 'base' }));
  const cards = items.slice(0, 2).map((p, i) => `          <span class="picker__card${i === 0 ? ' is-on' : ''}">
            <span class="picker__box" aria-hidden="true">${i === 0 ? '✓' : ''}</span>
            <span class="picker__card-body">
              <b>${esc(p.name)}</b>
              <span>${esc(p.description || p.meta.summary || '')}</span>
            </span>
            <span class="picker__card-docs">docs ↗</span>
          </span>`).join('\n');
  return `          <span class="picker__cat">
            <span class="picker__cat-glyph" aria-hidden="true">${GLYPH[cat] || '·'}</span>
            ${esc(cat)}
            <span class="picker__cat-count">1 of ${items.length} selected</span>
          </span>
${cards}`;
}).join('\n');

const preview = `        <span class="picker__bar" aria-hidden="true">
          <span class="picker__search">Filter by name, description or category…</span>
          <span class="picker__chip">Select all</span>
          <span class="picker__chip">Clear</span>
        </span>
        <span class="picker__body" aria-hidden="true">
${previewBlock}
        </span>
        <span class="picker__sum" aria-hidden="true">
          <span class="picker__sum-text"><b>${previewCats.length}</b> tools selected · + the core packages they need (already included)</span>
          <span class="picker__sum-cta">Copy install script</span>
        </span>`;

// The published release. NOTHING release-shaped is stamped into the landing
// page any more: the download hrefs point at the mutable latest/ aliases,
// and the version text next to them is gone. A release therefore cannot
// leave this page stale, and does not need a rebuild to stay correct.
//
// Still fetched because /get/ bakes the published manifest (it carries the
// `rails` hashes the paste script shows), and because the count note below
// compares the catalogue against what the release actually publishes.
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

const live = await publishedRelease();

const landing = path.join(WEB, 'index.html');
if (fs.existsSync(landing)) {
  const src = fs.readFileSync(landing, 'utf8');
  const re = /(<!-- TOOLS:START -->)[\s\S]*?(<!-- TOOLS:END -->)/;
  if (!re.test(src)) {
    console.error('index.html is missing the <!-- TOOLS:START --> / <!-- TOOLS:END --> markers');
    process.exit(1);
  }
  // Function replacements throughout: these bodies are built from catalog
  // prose, and `$1` or `$&` inside a replacement STRING is a capture-group
  // reference. One description with a dollar sign in it would otherwise
  // rewrite the page in a way nobody would think to look for.
  let out = src.replace(re, (_m, a, b) => `${a}\n${grid}\n      ${b}`);

  const previewRe = /(<!-- CONFIGURATOR:START -->)[\s\S]*?(<!-- CONFIGURATOR:END -->)/;
  if (!previewRe.test(out)) {
    console.error('index.html is missing the <!-- CONFIGURATOR:START --> / <!-- CONFIGURATOR:END --> markers');
    process.exit(1);
  }
  out = out.replace(previewRe, (_m, a, b) => `${a}\n${preview}\n        ${b}`);

  const familyRe = /(<!-- FAMILY:START -->)[\s\S]*?(<!-- FAMILY:END -->)/;
  if (!familyRe.test(out)) {
    console.error('index.html is missing the <!-- FAMILY:START --> / <!-- FAMILY:END --> markers');
    process.exit(1);
  }
  out = out.replace(familyRe, (_m, a, b) =>
    `${a}\n    <div class="prod-grid">\n${familyBlock}\n    </div>\n    ${b}`);

  // "N tools" always matches the catalogue this build actually rendered.
  out = out.replace(/(<span class="js-fns-count">)[^<]*(<\/span>)/g,
    `$1${pages.length}$2`);

  if (live) {
    console.log(`release ${live.release} published (${live.packages?.length ?? '?'} packages)`);
    if (live.packages && live.packages.length !== pages.length) {
      console.log(`note: catalog has ${pages.length} packages but ${live.release} publishes ` +
        `${live.packages.length} — the site lists the catalog, so these align at the next publish`);
    }
  } else if (process.env.FNSTOOLS_NO_RELEASE_FETCH) {
    console.log('release fetch skipped — landing page carries no release, so nothing to keep');
  } else {
    console.log('note: could not reach the release manifest — /get/ falls back to the repo manifest');
  }
  fs.writeFileSync(landing, out);
} else {
  console.warn('note: website/index.html does not exist yet — tool catalogue not injected');
}

// ------------------------------------------------------ /plus/ — the gate
//
// Prose is hand-written in website/content/plus.html and is only a fragment:
// this wraps it in the same head, header and footer every other generated
// page gets, so the Plus page cannot drift out of the site's chrome. The
// output is generated and gitignored, exactly like docs/ and get/.
//
// Two blocks are injected. The package list comes from catalog.json, so the
// page cannot advertise a Plus tool that does not ship (or miss one that
// does); the family cards come from content/family.json, the same source the
// landing page uses.
const plusSrc = path.join(WEB, 'content', 'plus.html');
if (fs.existsSync(plusSrc)) {
  let body = fs.readFileSync(plusSrc, 'utf8');

  const plusPages = pages
    .filter((p) => isPlus(p.name))
    .sort((a, b) => a.name.localeCompare(b.name, 'en', { sensitivity: 'base' }));

  const plusList = plusPages.length
    ? `<div class="plus-pkgs">\n` + plusPages.map((p) => `  <a class="plus-pkg" href="/docs/${p.slug}/">
    <span>
      <b>${esc(p.name)}</b>
      <span>${esc(p.description || p.meta.summary || '')}</span>
      <span class="cat-of">${GLYPH[p.category] || '·'} ${esc(p.category)}</span>
    </span>
    <span class="btn btn-secondary">Read the docs →</span>
  </a>`).join('\n') + `\n</div>`
    // Not an error: a catalog with nothing gated is a legitimate state, and
    // the page still has to explain what Plus is for when the first one lands.
    : `<p class="plus-pkgs-empty">Nothing is gated in the current catalogue — every package on this site installs free.</p>`;

  for (const [marker, markup] of [
    ['PLUSPKGS', plusList],
    ['FAMILY', `<div class="prod-grid">\n${familyBlock}\n</div>`],
  ]) {
    const re = new RegExp(`(<!-- ${marker}:START -->)[\\s\\S]*?(<!-- ${marker}:END -->)`);
    if (!re.test(body)) {
      console.error(`website/content/plus.html is missing its <!-- ${marker}:START --> / `
        + `<!-- ${marker}:END --> markers — /plus/ would ship without that block`);
      process.exit(1);
    }
    body = body.replace(re, (_m, a, b) => `${a}\n${markup}\n${b}`);
  }

  checkLinks(body, 'content/plus.html', null);
  if (problems.length) {
    console.error('build refused — unresolved internal links:\n' +
      problems.map((p) => `  - ${p}`).join('\n'));
    process.exit(1);
  }

  fs.mkdirSync(path.join(WEB, 'plus'), { recursive: true });
  fs.writeFileSync(path.join(WEB, 'plus', 'index.html'),
    `${head('FNSTools Plus — supporter tools, and what stays free',
      'Nearly all of FNSTools is free and MIT. A few tools unlock with a Patreon membership or a licence key, redeemed inside TouchDesigner — here is exactly how that works.',
      `${SITE}/plus/`)}
<!-- GENERATED by tools/build-site.mjs from website/content/plus.html — do not edit here -->
${header('/plus/')}
<main class="plus-page">
${body}
</main>
${FOOT}`);
  console.log(`built /plus/ (${plusPages.length} Plus package${plusPages.length === 1 ? '' : 's'}, ${family.length} family cards)`);
} else {
  console.warn('note: website/content/plus.html missing — /plus/ not built, and every link to it 404s');
}

// ------------------------------------------- /privacy/ and /terms/ — legal
//
// Two hand-written fragments in website/content/, wrapped in the same chrome
// as every other page. They exist because registering an OAuth client (the
// Patreon one the gate depends on) requires public policy URLs -- and because
// keeping the privacy claims HERE means they change in the same commit as
// worker/src/index.js, the code they describe. A policy hosted anywhere else
// is one that silently stops being true.
for (const [slug, title, desc] of [
  ['privacy', 'Privacy — FNSTools',
    'What FNSTools collects: nothing at all in the free toolkit, and the least the supporter gate can store and still know that a membership is live.'],
  ['terms', 'Terms — FNSTools',
    'The free packages are MIT and stay that way; Plus packages are licensed to you while your membership or licence key is live. Everything ships as-is.'],
]) {
  const src = path.join(WEB, 'content', `${slug}.html`);
  if (!fs.existsSync(src)) {
    console.warn(`note: website/content/${slug}.html missing — /${slug}/ not built, and every link to it 404s`);
    continue;
  }
  const body = fs.readFileSync(src, 'utf8');
  checkLinks(body, `content/${slug}.html`, null);
  if (problems.length) {
    console.error('build refused — unresolved internal links:\n' +
      problems.map((x) => `  - ${x}`).join('\n'));
    process.exit(1);
  }
  fs.mkdirSync(path.join(WEB, slug), { recursive: true });
  fs.writeFileSync(path.join(WEB, slug, 'index.html'),
    `${head(title, desc, `${SITE}/${slug}/`)}
<!-- GENERATED by tools/build-site.mjs from website/content/${slug}.html — do not edit here -->
${header(`/${slug}/`)}
<main class="plus-page">
${body}
</main>
${FOOT}`);
  console.log(`built /${slug}/`);
}

// ------------------------------------------------- /get/ — online picker
//
// The same configurator the installer serves from inside TD, published as
// a page: pick tools, copy a one-line Textport install script (or a
// selection.json for the manual rail). The manifest is BAKED in at build
// time; the page also refreshes it at runtime, which works because the
// bucket sends Access-Control-Allow-Origin for this host. Prefer the
// published rolling manifest (it carries the `rails` hashes publish.py
// stamps, and it is what a paste actually installs); fall back to the
// repo's, which lists the same catalogue minus rails.
//
// Everything site-shaped is added HERE rather than in the configurator:
// that file is also read verbatim into a Text DAT and served from inside
// TouchDesigner, where /docs.css and /site-nav.js do not exist. The source
// stays self-contained and this build dresses it in the site's chrome.
const cfgSrc = path.join(REPO, 'packaging', 'configurator', 'index.html');
if (fs.existsSync(cfgSrc)) {
  const manifest = live
    || JSON.parse(fs.readFileSync(path.join(REPO, 'packaging', 'manifest.json'), 'utf8'));
  let page = fs.readFileSync(cfgSrc, 'utf8');
  const tag = '<script src="manifest.js"></script>';
  if (!page.includes(tag)) {
    console.error('packaging/configurator/index.html lost its manifest.js script tag');
    process.exit(1);
  }
  // catMeta is the curated presentation from catalog.json — the same glyph
  // and pitch the landing page and the docs sidebar use, so a category
  // renamed in the CMS reads the same in all three places. build_manifest.py
  // now carries it on the manifest too (for the picker served inside TD);
  // baking it here means /get/ has it even against a release published
  // before that key existed.
  const baked = '<script>\nwindow.FNS_SITE = true;\n'
    + 'window.FNS_CATEGORY_META = ' + JSON.stringify(catMeta) + ';\n'
    + 'window.FNS_MANIFEST = ' + JSON.stringify(manifest, null, 1) + ';\n</script>';
  page = page.replace(tag, () => baked);
  page = page.replace('<title>',
    `<link rel="icon" href="/favicon.png" type="image/png" />\n`
    + `<link rel="apple-touch-icon" href="/favicon.png" />\n`
    + `<link rel="canonical" href="${SITE}/get/" />\n`
    + `<meta name="description" content="Pick your FNSTools packages and copy a one-line install script for the TouchDesigner Textport — sha256-verified, macOS or Windows." />\n`
    + `<meta property="og:title" content="Build your FNSTools install" />\n`
    + `<meta property="og:description" content="Pick the TouchDesigner tools you want and get a single sha256-verified line to paste into the Textport." />\n`
    + `<meta property="og:type" content="website" />\n`
    + `<meta property="og:image" content="${SITE}/og-image.png" />\n`
    + `<link rel="preconnect" href="https://fonts.googleapis.com">\n`
    + `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n`
    + `<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">\n`
    + `<link rel="stylesheet" href="/site-nav.css">\n`
    + `<link rel="stylesheet" href="/docs.css">\n`
    + `<title>`);

  for (const [marker, markup] of [
    ['<!-- FNS:HEADER -->', header('/get/')],
    ['<!-- FNS:FOOTER -->', `${FOOTER}\n<script src="/site-nav.js" defer></script>\n${ANALYTICS}`],
  ]) {
    if (!page.includes(marker)) {
      console.error(`packaging/configurator/index.html lost its ${marker} marker — `
        + '/get/ would ship without the site header or footer');
      process.exit(1);
    }
    page = page.replace(marker, () => markup);
  }

  fs.mkdirSync(path.join(WEB, 'get'), { recursive: true });
  fs.writeFileSync(path.join(WEB, 'get', 'index.html'),
    '<!-- GENERATED by tools/build-site.mjs from packaging/configurator/index.html — do not edit here -->\n' + page);
  console.log(`built /get/ (release ${manifest.release}, ${live ? 'published' : 'repo'} manifest`
    + `${manifest.rails ? '' : ', no rails hashes yet — paste script needs the next publish'}`
    + `${manifest.category_meta ? '' : ', category_meta baked from catalog.json'})`);
} else {
  console.warn('note: packaging/configurator/index.html missing — /get/ not built');
}

console.log(`built ${pages.length} package pages + index, ${copied} icons copied`);
const stubs = pages.filter((p) => /TODO: no wiki content/.test(p.body));
if (stubs.length) {
  console.log(`${stubs.length} pages are still stubs: ${stubs.map((p) => p.name).join(', ')}`);
}
