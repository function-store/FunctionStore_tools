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
// Only the languages the docs actually contain. hljs/lib/core plus explicit
// registration rather than the full bundle: it makes the supported set
// readable here, and an unregistered language falls back to plain text
// instead of silently guessing (autodetection reads two lines of
// TouchDesigner Python as Perl often enough to matter).
import hljs from 'highlight.js/lib/core';
import hljsPython from 'highlight.js/lib/languages/python';
import hljsJavascript from 'highlight.js/lib/languages/javascript';
import hljsBash from 'highlight.js/lib/languages/bash';
import hljsJson from 'highlight.js/lib/languages/json';

hljs.registerLanguage('python', hljsPython);
hljs.registerLanguage('javascript', hljsJavascript);
hljs.registerLanguage('js', hljsJavascript);
hljs.registerLanguage('bash', hljsBash);
hljs.registerLanguage('sh', hljsBash);
hljs.registerLanguage('json', hljsJson);

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB = path.dirname(HERE);
const REPO = path.dirname(WEB);
const SRC = path.join(REPO, 'packaging', 'docs');
const CATALOG = path.join(REPO, 'packaging', 'catalog.json');
const ICONS = path.join(REPO, 'icons');
// Glyphs rendered by build_manifest.RenderSurfaceIcons from the SAME Text
// TOP + font the live bar button uses, so this is the button's own picture
// rather than a lookalike. Missing is fine: the badges fall back to words.
const SURFACE_ICONS = path.join(REPO, 'packaging', 'docs', 'surface-icons');
const OUT = path.join(WEB, 'docs');

const SITE = 'https://functionstore.tools';
const GH = 'https://github.com/function-store/FunctionStore_tools';
const PATREON = 'https://patreon.com/function_store';
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

/** Every package's customization surface, from the REPO's
 *  packaging/parameters.json -- written by build_manifest.BuildParameters()
 *  in the same live pass that writes the manifest, so the two can never
 *  describe different projects.
 *
 *  Deliberately NOT part of manifest.json: that file is the rolling pointer
 *  every installed toolkit re-fetches to ask "is there a newer version",
 *  and this is ~200 KB of help text no client needs to answer it. The docs
 *  build reads the repo, so nothing has to be uploaded for it to work. */
const PARAMS = (() => {
  try {
    return JSON.parse(fs.readFileSync(
      path.join(REPO, 'packaging', 'parameters.json'), 'utf8'));
  } catch {
    return { packages: {} };   // pages build without the tables
  }
})();

/** What a package GIVES you -- a toolbar button, a Hub tab, a pane type --
 *  derived in build_manifest from the registries it hosts, with the words
 *  and the owning registry published alongside so this file keeps no list
 *  of its own. A package with none is a background behaviour: it changes
 *  how TouchDesigner acts without putting anything on screen, and saying
 *  so is as useful as naming a button. */
const SURFACE_META = () => PARAMS.surface_meta || {};
const surfacesOf = (name) => ((PARAMS.surfaces || {})[name] || []);

/** What a package actually puts on each bar: one entry per registry host,
 *  carrying the widget, the name the bar shows, its position, and the icon
 *  glyph read off the live button (build_manifest.SurfaceEntries).
 *
 *  `surfaces` above is the same evidence collapsed to a yes/no, and stays
 *  the thing the badges and the index filter run on -- this adds the detail
 *  a reader with the toolbar open in front of them is actually after. A
 *  build against a parameters.json written before this existed simply has
 *  none, and every page renders as it did. */
const entriesOf = (name) => ((PARAMS.surface_entries || {})[name] || []);

/** The rendered glyph for a package's FIRST contribution to one surface.
 *  Two buttons on one bar (MISC) each keep their own file; the badge shows
 *  the first and the placement list below shows both. */
function surfaceIcon(name, sid) {
  const hit = entriesOf(name).find((e) => e.surface === sid && e.icon);
  return hit ? hit.icon.file : '';
}
const iconImg = (file, cls) => (file
  ? `<img class="${cls}" src="/docs/assets/icons/surface/${esc(file)}" alt=""
      width="18" height="18" loading="lazy" decoding="async" />` : '');
const surfaceLabel = (id) => (SURFACE_META()[id] || {}).label || id;
const surfaceRegistry = (id) => (SURFACE_META()[id] || {}).registry || '';

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

/** Categories that are plumbing rather than a reason to install.
 *
 *  Core is eleven registries: the thing every other tool plugs into, always
 *  installed, never chosen. Listing it FIRST meant the docs sidebar opened
 *  on eleven registry names before a single tool a reader came looking for,
 *  and the landing page's catalogue unfolded on them by default.
 *
 *  Marked in catalog.json's `category_meta`, which its own _comment defines
 *  as the website's presentation layer ("packaging ignores it"). So this
 *  reorders the SITE only -- `categories` stays the canonical ordered list
 *  the installer picker runs on, where Core leading is correct because
 *  those packages are the mandatory ones. */
const isDeprioritized = (c) => Boolean(catMeta[c] && catMeta[c].deprioritized);

/** Reading order: everything else first, in catalog order, then the
 *  plumbing. A stable partition, not a sort -- two de-prioritized
 *  categories would keep their curated order relative to each other. */
const displayCategories = [
  ...categories.filter((c) => !isDeprioritized(c)),
  ...categories.filter(isDeprioritized),
];

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
  // Author has ONE home: catalog.json `author` (the manifest carries it,
  // so the picker byline and this badge agree). The old doc-frontmatter
  // `credit` block is refused so the two can never drift apart again.
  if (data.credit !== undefined) {
    fail(`packaging/docs/${file}: frontmatter \`credit\` moved to catalog.json \`author\` — delete it here and set it in the CMS package editor`);
  }
  const cur = curated[name];
  const author = cur.author && typeof cur.author === 'object' && cur.author.name
    ? { name: String(cur.author.name), url: cur.author.url ? String(cur.author.url) : '' }
    : null;
  pages.push({
    name,
    slug: packageSlug(name),
    file,
    meta: data,
    body: content,
    category: cur.category,
    description: cur.description || '',
    author,
    homepage: cur.homepage ? String(cur.homepage) : '',
    changelogUrl: cur.changelog_url ? String(cur.changelog_url) : '',
    foreign: !!(cur.source && typeof cur.source === 'object'),
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

/** Colour a fenced block at BUILD time.
 *
 *  Returning the inner HTML only, never a whole <pre>: markdown-it then
 *  keeps its own `<pre><code class="language-python">` wrapper, so the
 *  existing .docs-body pre rules still apply and Pagefind still indexes
 *  the text. Returning a full <pre> would take that wrapper away.
 *
 *  Highlighting HERE rather than in the browser is the point -- no
 *  client-side highlighter to ship, nothing to run on load, and a block
 *  that is coloured in the HTML stays coloured with scripts off.
 *
 *  `ignoreIllegals` because these are excerpts: a snippet that starts
 *  mid-class is not valid Python on its own and must still colour rather
 *  than throw the build. */
const fenceLanguages = new Set();
function highlight(code, lang) {
  const name = String(lang || '').trim().toLowerCase();
  if (name) fenceLanguages.add(name);
  if (name && hljs.getLanguage(name)) {
    try {
      return hljs.highlight(code, { language: name, ignoreIllegals: true }).value;
    } catch {
      // fall through to plain, escaped below
    }
  }
  if (name) fail(`a code block is tagged \`${name}\`, which no registered `
    + `highlighter covers -- register it in build-site.mjs or retag the fence`);
  return '';   // '' tells markdown-it to escape and render it plain
}

const md = new MarkdownIt({ html: true, linkify: true, breaks: false, highlight })
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

// The shared parameter reference is generated rather than authored from a
// markdown file, but package pages link to it -- so it has to exist as far
// as checkLinks is concerned.
const PARAMS_SLUG = 'common-parameters';
anchorsOf.set(PARAMS_SLUG, new Set(['registry-sections', 'about']));

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
<!-- Pagefind FIRST, then ours. Its bundle declares the same
     --pagefind-ui-* custom properties on :root that docs.css overrides;
     equal specificity means the LAST sheet wins, so loading it after
     docs.css silently reverted every one of them -- the docs search box
     rendered white-on-white in Arial Bold in a black site, and the bold
     placeholder overran the 244px sidebar and was clipped mid-word. -->
<link rel="stylesheet" href="/docs/pagefind/pagefind-ui.css" onerror="this.remove()">
<link rel="stylesheet" href="/site-nav.css">
<link rel="stylesheet" href="/docs.css">
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

// ----------------------------------------------------------- parameters

/** How a control's value type reads to someone who is not sitting in front
 *  of the TouchDesigner parameter dialog. */
const STYLE_WORD = {
  Toggle: 'on / off', Pulse: 'button', Str: 'text', Int: 'number',
  Float: 'number', Menu: 'menu', StrMenu: 'menu, editable',
  File: 'file path', FileSave: 'file path', Folder: 'folder path',
  RGB: 'colour', RGBA: 'colour', WH: 'width, height', XY: 'x, y',
  XYZ: 'x, y, z', UV: 'u, v', OP: 'operator', COMP: 'operator',
  TOP: 'operator', CHOP: 'operator', DAT: 'operator', SOP: 'operator',
  MAT: 'operator', PanelCOMP: 'operator', Header: 'heading',
};
const styleWord = (s) => STYLE_WORD[s] || String(s).toLowerCase();

/** The value the tool arrives with. An empty string is SAID rather than
 *  left blank: a blank cell reads as missing data, and "empty" is often
 *  the meaningful default (an empty Scope Comp means the root timeline). */
function defaultCell(row) {
  if (row.style === 'Pulse' || row.style === 'Header') return '';
  const d = row.default;
  if (d === undefined || d === null) return '';
  if (typeof d === 'boolean') return d ? 'on' : 'off';
  if (d === '') return 'empty';
  if (row.style === 'Menu' || row.style === 'StrMenu') {
    const hit = (row.menu || []).find((m) => m.name === d);
    return hit ? hit.label : String(d);
  }
  return String(d);
}

/** TD's own separator entries are layout, not choices. */
function menuLine(row) {
  const items = (row.menu || []).filter((m) => m.name !== '_separator_');
  if (!items.length) return '';
  const shown = items.slice(0, 8).map((m) => `<code>${esc(m.label)}</code>`);
  const rest = items.length - shown.length;
  return `<div class="par-menu">Options: ${shown.join(', ')}`
    + `${rest > 0 ? ` and ${rest} more` : ''}</div>`;
}

/** One table per parameter page, in dialog order.
 *
 *  A control with no help text is still listed, for the same reason an
 *  unexplained hotkey is: knowing it exists beats not knowing. Saying so in
 *  the cell is also what keeps the gap visible -- an undocumented control
 *  that quietly renders as a blank cell is indistinguishable from a
 *  documented one, and nobody ever goes back to fill those in. */
/** A Header par is a section label -- unless there is a row of them.
 *
 *  Several Headers in a row are not labelling anything: they are a
 *  paragraph typed into the parameter dialog one line per par, which is
 *  the only way to get multi-line prose in there. ExprHotStrings has a run
 *  of fourteen (`Usage:`, then `L1`..`L12`), and rendered literally that is
 *  fourteen full-width heading rows of instructions sitting under a table
 *  of six real controls -- prose wearing the costume of structure.
 *
 *  So: a Header ADJACENT to another Header is dropped, every member of the
 *  run included. A lone Header keeps its meaning and its row. The text is
 *  not lost -- that is what the tool's page is for, and ExprHotStrings
 *  already says all of it in prose. */
const withoutHeaderRuns = (rows) => rows.filter((row, i) => {
  if (row.style !== 'Header') return true;
  const before = i > 0 && rows[i - 1].style === 'Header';
  const after = i < rows.length - 1 && rows[i + 1].style === 'Header';
  return !before && !after;
});

let headerRunsDropped = 0;

function parTable(allRows) {
  const rows = withoutHeaderRuns(allRows);
  headerRunsDropped += allRows.length - rows.length;
  // A page that was ONLY a header run has nothing left to tabulate, and an
  // empty table with a header row still reads as a table.
  if (!rows.some((r) => r.style !== 'Header')) return '';
  const body = rows.map((row) => {
    if (row.style === 'Header') {
      return `      <tr class="par-head"><th colspan="3">${esc(row.label)}</th></tr>`;
    }
    const def = defaultCell(row);
    const desc = (row.help
      ? md.renderInline(row.help)
      : '<span class="par-todo">Not documented yet.</span>') + menuLine(row);
    return `      <tr>
        <td class="par-name"><strong>${esc(row.label || row.name)}</strong>`
      + `<code>${esc(row.name)}</code>`
      + `${row.readonly ? '<span class="par-flag">read-only</span>' : ''}</td>
        <td class="par-type">${esc(styleWord(row.style))}`
      + `${def ? `<span class="par-def">${esc(def)}</span>` : ''}</td>
        <td>${desc}</td>
      </tr>`;
  }).join('\n');
  return `<div class="par-wrap"><table class="par-table">
    <thead><tr><th>Control</th><th>Type / default</th><th>What it does</th></tr></thead>
    <tbody>
${body}
    </tbody>
  </table></div>`;
}

/** "This tool also registers with X and Y."
 *
 *  A tool's Registry page is NOT listed on its own page: those controls
 *  belong to the registry that stamps them, are identical on every tool
 *  that registers, and are documented once on the registry's page.
 *
 *  Driven by `registry_pages` (which registries put a section on THIS
 *  component) rather than by `surfaces` (what the package gives the user).
 *  They are not the same list: a host nested inside a widget earns the
 *  package a toolbar button while leaving the package root's Registry page
 *  empty, which is true of 5 packages. Using surfaces here would point at
 *  a parameter page that does not exist. */
function registersWithLine(name) {
  const owners = (PARAMS.registry_pages || {})[name] || [];
  if (!owners.length) return '';
  const links = owners.map((o) =>
    `<a href="/docs/${packageSlug(o)}/#registry-section">${esc(o)}</a>`);
  const list = links.length > 1
    ? links.slice(0, -1).join(', ') + ' and ' + links[links.length - 1]
    : links[0];
  return `<p class="hint-line">Its <strong>Registry</strong> page comes from ${list}.</p>`;
}

/** The section a REGISTRY stamps onto every tool that registers with it.
 *
 *  Rendered on the registry's own page, which is where a reader who
 *  followed "documented on its registry's page" lands. Derived from the
 *  sections as actually stamped, not from the registry's template. */
function registrySection(name) {
  const rows = (PARAMS.registry_sections || {})[name] || [];
  if (!rows.length) return '';
  const table = parTable(rows);
  if (!table) return '';
  return `<section class="parameters">
  <h2 id="registry-section">What it adds to a registered tool</h2>
  <p class="hint-line">Every tool that registers gets these on its own <strong>Registry</strong> page.</p>
${table}
</section>`;
}

/** The package's own controls, grouped by parameter page in dialog order.
 *
 *  Derived, never authored here: build_manifest.Parameters() reads the pars
 *  off the live component and the description IS the parameter's tooltip,
 *  so a sentence written in TouchDesigner reaches this page at the next
 *  build with no prose edited anywhere. The controls the toolkit stamps on
 *  every package are not repeated here -- they are described once, on the
 *  shared reference. */
function parametersSection(p) {
  const rows = (PARAMS.packages || {})[p.name] || [];
  if (!rows.length) return '';
  // A doc that already hand-wrote a "Parameters" heading owns that anchor.
  const anchor = (anchorsOf.get(p.slug) || new Set()).has('parameters')
    ? 'parameter-reference' : 'parameters';
  const byPage = [];
  for (const row of rows) {
    const last = byPage[byPage.length - 1];
    if (last && last.page === row.page) last.rows.push(row);
    else byPage.push({ page: row.page, rows: [row] });
  }
  const blocks = byPage.map(({ page, rows: rs }) => {
    const table = parTable(rs);
    // No table, no heading for it.
    return table ? `  <h3 id="${slugify(anchor + '-' + page)}">${esc(page)}</h3>
${table}` : '';
  }).filter(Boolean).join('\n');
  if (!blocks) return '';
  return `<section class="parameters">
  <h2 id="${anchor}">Parameters</h2>
  ${registersWithLine(p.name)}
${blocks}
</section>`;
}

/** One collapsible group in the sidebar.
 *
 *  <details open> rather than a plain <div>: on a phone the flat list was
 *  53 packages tall and pushed the first word of every page 2358px down --
 *  you tapped a tool and landed back on the menu. Collapsed, the same nav
 *  is eight rows.
 *
 *  Authored OPEN and closed by docs.js only under the mobile breakpoint, so
 *  the desktop sidebar is unchanged and a reader with no JavaScript gets
 *  today's fully-expanded list rather than a nav they cannot open. The
 *  count rides in the summary because a collapsed group that does not say
 *  how much it hides is a worse affordance than the list it replaced.
 */
function sideGroup(glyph, label, items, count) {
  return `  <details class="side-group" open>
    <summary>
      <span class="side-glyph" aria-hidden="true">${glyph}</span>
      <span class="side-cat">${esc(label)}</span>
      <span class="side-count">${count}</span>
    </summary>
    <ul>
${items}
    </ul>
  </details>`;
}

/** "Where it appears" -- every on-screen contribution, one row each.
 *
 *  Entirely derived (build_manifest.SurfaceEntries reads the registry
 *  hosts): the icon is the glyph off the live button, the name is the
 *  registry's own Canonicalname, and the position is the order par the
 *  surface configurator writes. Nothing here is authored in a doc, so a
 *  rebound button or a re-ordered bar reaches the site with no prose
 *  edited -- which is the whole point, since the previous answer to
 *  "which icon is this" was a hand-typed PNG filename from the wiki era
 *  that no longer matched the button.
 *
 *  Skipped entirely for a package with no entries: "nothing on screen" is
 *  already said by the badges, and an empty section says it worse. */
function placementSection(p) {
  const entries = entriesOf(p.name);
  if (!entries.length) return '';
  const rows = entries.map((e) => {
    const reg = surfaceRegistry(e.surface);
    const where = reg
      ? `<a href="/docs/${packageSlug(reg)}/">${esc(surfaceLabel(e.surface))}</a>`
      : esc(surfaceLabel(e.surface));
    const bits = [];
    // The name the BAR shows, which is often not the package name.
    if (e.label && e.label !== p.name) bits.push(`as <strong>${esc(e.label)}</strong>`);
    if (e.side) bits.push(`${esc(e.side)} side`);
    if (e.order !== undefined) bits.push(`position ${esc(String(e.order))}`);
    const icon = e.icon
      ? iconImg(e.icon.file, 'place-icon')
      : '<span class="place-icon place-icon--none" aria-hidden="true"></span>';
    return `      <li>${icon}<span class="place-what">${where}</span>`
      + `<span class="place-detail">${bits.join(' \u00b7 ')}</span></li>`;
  }).join('\n');
  return `<section class="placement">
  <h2 id="where-it-appears">Where it appears</h2>
  <p class="hint-line">Read off the registry hosts in the component, so this is
  where the tool puts itself in a default install; every one of these can be
  reordered or hidden from <a href="/docs/fns-hub/">FNS_Hub</a>.</p>
  <ul class="place-list">
${rows}
  </ul>
</section>`;
}

function sidebar(currentSlug) {
  const groups = displayCategories.map((cat) => {
    const inCat = pages
      .filter((p) => p.category === cat)
      .sort((a, b) => a.name.localeCompare(b.name, 'en', { sensitivity: 'base' }));
    const items = inCat
      .map((p) => `      <li><a href="/docs/${p.slug}/"${p.slug === currentSlug ? ' aria-current="page"' : ''}>${esc(p.name)}${isPlus(p.name) ? PLUS_MARK : ''}</a></li>`)
      .join('\n');
    if (!items) return '';
    return sideGroup(GLYPH[cat] || '·', cat, items, inCat.length);
  }).filter(Boolean).join('\n');
  // Last, under the packages: it is a reference, not a destination.
  const reference = sideGroup('§', 'Reference',
    `      <li><a href="/docs/${PARAMS_SLUG}/"${currentSlug === PARAMS_SLUG ? ' aria-current="page"' : ''}>Common parameters</a></li>`,
    1);
  return `<aside class="docs-side" id="docs-side">
  <div class="docs-search"><div id="search"></div></div>
${groups}
${reference}
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
let glyphs = 0;
if (fs.existsSync(SURFACE_ICONS)) {
  const dst = path.join(OUT, 'assets', 'icons', 'surface');
  fs.mkdirSync(dst, { recursive: true });
  for (const f of fs.readdirSync(SURFACE_ICONS).filter((f) => f.endsWith('.png'))) {
    fs.copyFileSync(path.join(SURFACE_ICONS, f), path.join(dst, f));
    glyphs++;
  }
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
  // Where it shows up, before anything else about it: this is the question
  // a reader scanning the docs actually has.
  for (const sid of surfacesOf(p.name)) {
    const reg = surfaceRegistry(sid);
    // The glyph the bar button actually draws, beside the words for it --
    // a reader scanning the toolbar recognises the picture faster than the
    // sentence, and the picture is now derived rather than hand-typed.
    const label = iconImg(surfaceIcon(p.name, sid), 'badge-icon')
      + esc(surfaceLabel(sid));
    badges.push(reg
      ? `<a class="badge badge-surface" href="/docs/${packageSlug(reg)}/">${label}</a>`
      : `<span class="badge badge-surface">${label}</span>`);
  }
  const plats = p.meta.platforms;
  if (Array.isArray(plats) && plats.length && plats.length < 2) {
    badges.push(`<span class="badge badge-warn">${esc(plats.join(', '))} only</span>`);
  }
  if (p.author) {
    const c = p.author;
    badges.push(c.url
      ? `<span class="badge">by <a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.name)}</a></span>`
      : `<span class="badge">by ${esc(c.name)}</span>`);
  }
  // A foreign package (catalog `source`): its own product, mirrored into
  // the store. Say so, and give the reader the way out to its own site.
  if (p.foreign) {
    badges.push(`<span class="badge" title="Its own product with its own updater, installable from the toolkit picker">family product</span>`);
  }
  if (p.homepage) {
    badges.push(`<a class="badge" href="${esc(p.homepage)}" target="_blank" rel="noopener">website ↗</a>`);
  }
  if (p.changelogUrl) {
    badges.push(`<a class="badge" href="${esc(p.changelogUrl)}" target="_blank" rel="noopener">changelog ↗</a>`);
  }

  const video = p.meta.video
    ? `<div class="embed-video"><iframe src="https://www.youtube.com/embed/${esc(String(p.meta.video).split(/[/=]/).pop())}" title="${esc(p.name)} walkthrough" loading="lazy" allowfullscreen></iframe></div>`
    : '';

  // The site is the complete record of the gated tools: a Plus page is as
  // full as a free one, and the note on it is where the reader meets the
  // membership that pays for the free toolkit.
  const plusNote = isPlus(p.name) ? `<div class="plus-note">
    <p><strong>This one is a Plus tool.</strong> It installs through the same picker as
    everything else and unlocks with a Patreon membership or a licence key redeemed inside
    TouchDesigner. Everything else in the toolkit stays free and MIT, and the membership is
    what keeps that work moving.</p>
    <p class="plus-note-actions">
      <a class="btn btn-primary" href="${PATREON}" target="_blank" rel="noopener">Join on Patreon →</a>
      <a class="btn btn-secondary" href="/plus/">How Plus works →</a>
    </p>
  </div>` : '';

  const features = p.meta.features || [];
  const featIcon = (f) => (f.icon
    ? `<img class="feat-icon" src="/docs/assets/icons/${esc(f.icon)}" alt="" `
      + `width="18" height="18" decoding="async" />` : '');

  const parAnchor = (PARAMS.packages || {})[p.name]?.length
    ? ((anchorsOf.get(p.slug) || new Set()).has('parameters')
        ? 'parameter-reference' : 'parameters')
    : '';
  const tocItems = (entriesOf(p.name).length
      ? [`<li><a href="#where-it-appears">Where it appears</a></li>`] : [])
    .concat(features
      .map((f) => `<li><a href="#${esc(f.anchor)}">${featIcon(f)}${esc(f.name)}</a></li>`))
    .concat(parAnchor ? [`<li><a href="#${parAnchor}">Parameters</a></li>`] : []);
  const onThisPage = tocItems.length > 1
    ? `<nav class="toc"><span>On this page</span><ul>${tocItems.join('')}</ul></nav>`
    : '';

  // NO icon is injected into the headings. The CMS lets a feature carry an
  // icons/*.png and this used to stamp it in front of its <h2>; it read as
  // decoration inside the running text and is gone by request. The file is
  // still authored and still rides the table of contents, which is a list
  // of links rather than prose.
  const body = p.html;

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
  // Below the prose: the tables are a reference to come back to, and a
  // 80-row table between the lede and the explanation buries the
  // explanation. The TOC entry is what makes them reachable from the top.
  const parSection = parametersSection(p);
  const shortcuts = bound.length ? `<section class="shortcuts">
    <h2 id="shortcuts">Shortcuts</h2>
    <p class="hint-line">Global: they fire anywhere in TouchDesigner. Shortcuts scoped to a single panel are a local control scheme and stay off this list.</p>
    <ul class="feat-keys">${bound.map((h) => {
      const what = said.get(keyId(h.keys)) || '';
      return `<li><kbd>${esc(prettyKeys(h.keys))}</kbd>${
        what ? md.renderInline(what) : ''}</li>`;
    }).join('')}</ul>
  </section>` : '';

  // An undocumented page has to LOOK undocumented. Rendered empty it is a
  // title, a badge row and generated tables -- indistinguishable from a
  // tool that simply has little to say, which is how AltSelect shipped
  // with a blank page nobody noticed. Same reasoning as .par-todo.
  const undocumented = p.body.trim() ? '' : `<p class="page-todo">This tool
    does not have a written page yet. The generated sections below are read
    straight from the component, so they are accurate. What is missing is
    the prose. <a href="${EDIT_BASE}/${p.file}" target="_blank"
    rel="noopener">Write it →</a></p>`;

  const html = `${head(`${p.name} | FNSTools docs`, p.description || `${p.name} documentation.`, `${SITE}/docs/${p.slug}/`)}
${header('/docs/')}
<div class="docs-layout wrap">
${sidebar(p.slug)}
<main class="docs-main" data-pagefind-body>
  <p class="crumbs"><a href="/docs/">Docs</a> <span aria-hidden="true">/</span> ${esc(p.category)}</p>
  <h1>${esc(p.name)}</h1>
  ${p.description ? `<p class="lede">${esc(p.description)}</p>` : ''}
  <p class="badges">${badges.join(' ')}</p>
  ${plusNote}
  ${undocumented}
  ${video}
  ${onThisPage}
  ${placementSection(p)}
  ${shortcuts}
  <div class="docs-body">
${body}
  </div>
  ${parSection}
  ${registrySection(p.name)}
  <p class="edit-page"><a href="${EDIT_BASE}/${p.file}" target="_blank" rel="noopener">Edit this page on GitHub →</a></p>
</main>
</div>
${FOOT}`;
  fs.writeFileSync(path.join(dir, 'index.html'), html);
}

/** Filter the index by what a package puts on screen.
 *
 *  Built from the surfaces actually in use, so a vocabulary entry nothing
 *  hosts (the pane type, today) never becomes a button that always returns
 *  nothing. "Nothing on screen" is a real answer and gets its own button:
 *  those tools change how TouchDesigner behaves rather than adding to it,
 *  and that is exactly what someone browsing wants to be able to ask for. */
function surfaceFilter() {
  const used = new Map();
  for (const p of pages) {
    const list = surfacesOf(p.name);
    if (!list.length) used.set('none', (used.get('none') || 0) + 1);
    for (const sid of list) used.set(sid, (used.get(sid) || 0) + 1);
  }
  if (used.size < 2) return '';
  const order = [...Object.keys(SURFACE_META()), 'none'].filter((k) => used.has(k));
  const buttons = order.map((sid) => `<button class="surf-chip" data-surf="${esc(sid)}">${
    sid === 'none' ? 'Nothing on screen' : esc(surfaceLabel(sid))
  } <span>${used.get(sid)}</span></button>`).join('');
  return `  <div class="surf-filter" id="surf-filter">
    <button class="surf-chip on" data-surf="all">All <span>${pages.length}</span></button>
    ${buttons}
  </div>
  <script>
  (function () {
    var bar = document.getElementById('surf-filter');
    if (!bar) return;
    bar.addEventListener('click', function (e) {
      var b = e.target.closest('.surf-chip');
      if (!b) return;
      var want = b.dataset.surf;
      bar.querySelectorAll('.surf-chip').forEach(function (x) {
        x.classList.toggle('on', x === b);
      });
      document.querySelectorAll('.doc-card').forEach(function (card) {
        var has = want === 'all'
          || (card.dataset.surfaces || '').split(' ').indexOf(want) !== -1;
        card.hidden = !has;
      });
      // a category whose every card is hidden is noise, not a heading
      document.querySelectorAll('.doc-cat').forEach(function (sec) {
        var any = sec.querySelector('.doc-card:not([hidden])');
        sec.hidden = !any;
      });
    });
  })();
  <\/script>`;
}

// docs index
const indexGroups = displayCategories.map((cat) => {
  const items = pages
    .filter((p) => p.category === cat)
    .sort((a, b) => a.name.localeCompare(b.name, 'en', { sensitivity: 'base' }))
    .map((p) => `      <a class="doc-card" href="/docs/${p.slug}/" data-surfaces="${
        esc(surfacesOf(p.name).join(' ')) || 'none'}">
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
  'FNSTools docs: every tool in the toolkit',
  `Documentation for all ${pages.length} FNSTools packages: templates, parameter tools, network shortcuts, MIDI/OSC mapping and extension helpers for TouchDesigner.`,
  `${SITE}/docs/`)}
${header('/docs/')}
<div class="docs-layout wrap">
${sidebar(null)}
<main class="docs-main docs-index" data-pagefind-body>
  <h1>Documentation</h1>
  <p class="lede">Every package that ships with FNSTools. Each tool installs on its own, so each one is documented on its own.</p>
  <p class="docs-index-note">Each page lists that tool's own controls. The ones every package shares are described once on the <a href="/docs/${PARAMS_SLUG}/">common parameters</a> page.</p>
  <p class="docs-index-note">The Plus tools are here too, marked ${PLUS_MARK}. Every gated package is listed and documented in full, locked or unlocked, so this index is the complete record of what a <a href="${PATREON}" target="_blank" rel="noopener">Patreon membership</a> unlocks. <a href="/plus/">How Plus works →</a></p>
${surfaceFilter()}
${indexGroups}
</main>
</div>
${FOOT}`);

// --------------------------- shared parameter reference (generated page)

// The toolkit stamps the same controls onto every package: one registry
// section per surface a tool publishes into, and the read-only identity
// block on its About page. Repeating those on 49 pages would be 49 copies
// of one explanation to keep in step -- so each package page links here
// instead, and this is the only place they are described.
{
  const aboutRows = PARAMS.about_stamp || [];
  const registries = Object.entries(PARAMS.registry_sections || {});
  const registryList = registries.map(([name, rows]) =>
    `      <li><a href="/docs/${packageSlug(name)}/#registry-section">${esc(name)}</a>`
    + `: ${rows.length} controls</li>`).join('\n');
  const dir = path.join(OUT, PARAMS_SLUG);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'index.html'), `${head(
    'Common parameters | FNSTools docs',
    'The controls every FNSTools package carries: the read-only About block that identifies a version, and the registry sections that decide where a tool appears.',
    `${SITE}/docs/${PARAMS_SLUG}/`)}
${header('/docs/')}
<div class="docs-layout wrap">
${sidebar(PARAMS_SLUG)}
<main class="docs-main" data-pagefind-body>
  <p class="crumbs"><a href="/docs/">Docs</a> <span aria-hidden="true">/</span> Reference</p>
  <h1>Common parameters</h1>
  <p class="lede">The controls every package carries, whatever the tool does.</p>
  <section class="parameters">
  <h2 id="about">About</h2>
  <p class="hint-line">Read-only, on every package. <code>Pkgversion</code> is what the updater compares.</p>
${parTable(aboutRows)}

  <h2 id="registry-sections">Registry sections</h2>
  <p class="hint-line">Registering with a surface adds a section to a tool's <strong>Registry</strong> page. Each registry documents its own:</p>
  <ul class="par-registry-list">
${registryList}
  </ul>
  </section>
</main>
</div>
${FOOT}`);
  console.log(`built /docs/${PARAMS_SLUG}/ (${aboutRows.length} identity fields, ${registries.length} registries linked)`);
}

// ------------------------------- tool catalogue injected into index.html

// One fold per category. 49 packages listed flat is a wall nobody reads, and
// the landing page's job is to say what KIND of thing is in here — so the
// category, its pitch and its count stay in the open and the list opens on
// demand. <details> keeps it working with JS off and findable by Ctrl+F.
//
// Core is open by default: it is the shortest way to answer "what is this
// thing actually made of" for someone who just arrived.
const grid = displayCategories.map((cat) => {
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
  // The first category a reader meets, whichever that now is -- never a
  // hardcoded name, which is how this stayed pinned to Core.
  return `      <details class="cat"${cat === displayCategories[0] ? ' open' : ''}>
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
const previewCats = displayCategories.filter((c) => !isDeprioritized(c)).slice(0, 2);
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
    : `<p class="plus-pkgs-empty">Nothing is gated in the current catalogue; every package on this site installs free.</p>`;

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
    `${head('FNSTools Plus: supporter tools, and what stays free',
      'Nearly all of FNSTools is free and MIT. A few tools unlock with a Patreon membership or a licence key, redeemed inside TouchDesigner. Here is exactly how that works.',
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
  ['privacy', 'Privacy | FNSTools',
    'What FNSTools collects: nothing at all in the free toolkit, and the least the supporter gate can store and still know that a membership is live.'],
  ['terms', 'Terms | FNSTools',
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
    + `<meta name="description" content="Pick your FNSTools packages and copy a one-line install script for the TouchDesigner Textport: sha256-verified, macOS or Windows." />\n`
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

// ------------------------------------------------- doc evidence audit
//
// The generated blocks on a page cannot be wrong -- they are read off the
// live component. The PROSE can, and silently: a sentence naming a shortcut
// that nothing binds looks exactly like one naming a shortcut that works.
//
// Reported, never fatal: each line is a claim to CHECK. The filters below
// exist because the first version of this printed 9 lines of which 7 were
// correct prose, and a report that cries wolf gets ignored -- which is the
// failure mode it was written to prevent.
{
  const MOUSE = /click|drag|drop|scroll|wheel|hover/i;
  const MODS = /^(?:ctrl|cmd|alt|opt|option|shift|meta)$/i;
  const COMBO = /\b((?:(?:ctrl|cmd|alt|opt|option|shift|meta)\s*(?:\([^)]*\))?\s*\+\s*)+[A-Za-z0-9\\[\]{}]+)/gi;

  /** The key a combo actually presses -- its last part. */
  const keyOf = (raw) => {
    const parts = String(raw).replace(/\([^)]*\)/g, '').split('+')
      .map((x) => x.trim()).filter(Boolean);
    return (parts[parts.length - 1] || '').toLowerCase();
  };
  /** TD writes a character class; prose writes {number}. Same shortcut. */
  const normKey = (k) => (/^(\[0-9\]|\{number\}|\{0-9\}|\[n\])$/.test(k) ? '#' : k);

  // Every binding in the toolkit, not just this package's: a registry page
  // legitimately documents the tool it serves (FNS_PaletteRegistry names
  // TDX_SearchPalette's Ctrl+Shift+F), and that is a cross-reference, not
  // a stale claim.
  const allCombos = new Set();
  const allKeys = new Map();       // key -> the package that binds it
  const ownCombos = {};
  for (const [name, list] of Object.entries(HOTKEYS)) {
    ownCombos[name] = new Set();
    for (const h of list) {
      for (const combo of String(h.keys).trim().split(/\s+/)) {
        allCombos.add(keyId(combo));
        ownCombos[name].add(keyId(combo));
        const k = normKey(keyOf(combo.replace(/\./g, '+')));
        if (k && !allKeys.has(k)) allKeys.set(k, name);
      }
    }
  }

  const claims = [];
  for (const p of pages) {
    // Parenthesised combos are the mac restatement of the one beside them
    // ("Ctrl+Tab or (Option+Tab)"). The manifest carries whichever half
    // THIS machine binds, so the other half can never match and is not a
    // finding. Drop them before scanning rather than after.
    const prose = p.body.replace(/\([^)]*\)/g, ' ');
    const said = new Map();
    // Keys a page declares as its own panel's control scheme -- the
    // in-window keys of a palette or an editor -- are no more bindings
    // than a mouse combo is, and the Shortcuts hint-line already says
    // panel-scoped keys are not listed. `local_keys:` in the frontmatter
    // is that declaration, so the exemption is explicit, not guessed.
    const local = new Set((p.meta.local_keys || []).map((k) => keyId(String(k))));
    // Keys a tool binds OUTSIDE FNS_HotkeyManager's reach -- BorderlessTD's
    // Shift+Esc lives in a list expression the conformance contract does not
    // recognise (docs/DocsEvidenceDerivation.md, "What this does not do").
    // They are real and global, so `local_keys` would be a lie; `fixed_keys:`
    // says exactly what they are, and the audit stops crying wolf over a
    // gap that is already on record.
    const fixed = new Set((p.meta.fixed_keys || []).map((k) => keyId(String(k))));
    for (const m of prose.matchAll(COMBO)) {
      const raw = m[1];
      if (MOUSE.test(raw)) continue;
      const parts = raw.split('+').map((x) => x.trim()).filter(Boolean);
      // "Hold Ctrl+Alt while dragging" is an instruction, not a binding --
      // build_manifest drops these from the manifest for the same reason.
      if (parts.every((x) => MODS.test(x))) continue;
      const id = keyId(raw.replace(/opt(ion)?/gi, 'alt').replace(/cmd/gi, 'ctrl'));
      if (!id || allCombos.has(id) || local.has(id) || fixed.has(id)) continue;
      const key = normKey(keyOf(raw));
      // The exact combo is unbound, but the KEY is -- ParOPDrop binds `p`
      // and its doc describes four modifier variants of pressing it. The
      // doc is right and so is the manifest; they differ in granularity.
      if (allKeys.has(key)) continue;
      said.set(raw.replace(/\s+/g, ''), key);
    }
    if (said.size) claims.push({ name: p.name, combos: [...said.keys()] });
  }

  // An UNTAGGED fence renders as grey plain text next to a coloured one,
  // which reads as a rendering bug rather than as missing metadata.
  //
  // Fences must be walked in PAIRS: a closing ``` carries no info string by
  // definition, so a plain regex over every fence line reports every page
  // that has a code block at all -- which it did, naming all four.
  const untagged = new Set();
  for (const p of pages) {
    let open = false;
    for (const line of p.body.split('\n')) {
      const m = /^\s{0,3}```(.*)$/.exec(line);
      if (!m) continue;
      if (open) { open = false; continue; }      // closing fence
      open = true;
      if (!m[1].trim()) untagged.add(p.name);    // opening fence, no language
    }
  }
  if (untagged.size) {
    console.log(`note: ${untagged.size} page(s) open a code fence with no `
      + `language, so it renders unhighlighted: ${[...untagged].join(', ')}`);
  }

  // House style: no em-dashes and no double-hyphen asides in reader-facing
  // prose. Reported per page so the habit cannot creep back in unnoticed.
  const dashy = pages.filter((p) => /—|(?<=\S) -- (?=\S)/.test(
    p.body.replace(/<!--[\s\S]*?-->/g, '') + ' ' + (p.description || '')));
  if (dashy.length) {
    console.log(`note: ${dashy.length} page(s) use an em-dash or " -- " in prose `
      + `(house style is plain punctuation): ${dashy.map((p) => p.name).join(', ')}`);
  }
  // The same rule for tooltips, which reach the tables verbatim. These live
  // on the parameters inside the components, so the fix is in TouchDesigner
  // (par.help), and this is where anyone learns that it is needed.
  const DASH = /—|(?<=\S) -- (?=\S)/;
  const tipDashes = [];
  for (const p of pages) {
    const n = ((PARAMS.packages || {})[p.name] || [])
      .filter((r) => DASH.test(String(r.help || ''))).length;
    if (n) tipDashes.push(`${p.name} (${n})`);
  }
  if (tipDashes.length) {
    console.log(`note: parameter tooltips with an em-dash or " -- ", by package `
      + `(fix par.help in TouchDesigner): ${tipDashes.join(', ')}`);
  }

  const blank = pages.filter((p) => !p.body.trim()).map((p) => p.name);
  if (blank.length) {
    console.log(`note: ${blank.length} page(s) have no prose at all: ${blank.join(', ')}`);
  }
  if (claims.length) {
    console.log(`note: ${claims.length} page(s) name a key nothing in the toolkit binds `
      + `-- either the doc is stale, or the binding is not reaching `
      + `FNS_HotkeyManager (docs/HotkeyManagerConformance.md):`);
    for (const c of claims) console.log(`  - ${c.name}: ${c.combos.join(', ')}`);
  } else {
    console.log('every shortcut named in prose is backed by a real binding');
  }
}

if (headerRunsDropped) {
  console.log(`note: ${headerRunsDropped} Header parameters dropped from the tables `
    + `-- consecutive Headers are prose typed into the parameter dialog, not `
    + `section labels`);
}
console.log(`built ${pages.length} package pages + index, ${copied} icons copied`
  + `, ${glyphs} surface glyphs`
  + `, code fences: ${[...fenceLanguages].sort().join(', ') || 'none'}`);
{
  // Said out loud for the same reason an undocumented parameter is: a
  // surface with no gathered glyph renders as words and looks deliberate.
  const noIcon = pages.filter((p) => entriesOf(p.name).some((e) => !e.icon));
  if (noIcon.length) {
    console.log(`note: ${noIcon.length} packages contribute a surface with no icon `
      + `glyph (panels, sliders and whole-COMP tabs have none): `
      + noIcon.map((p) => p.name).join(', '));
  }
}
const stubs = pages.filter((p) => /TODO: no wiki content/.test(p.body));
if (stubs.length) {
  console.log(`${stubs.length} pages are still stubs: ${stubs.map((p) => p.name).join(', ')}`);
}
