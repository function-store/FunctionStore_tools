---
status: in-force
summary: The design system shared by functionstore.tools, the docs, /get/ and the web pages served from inside TouchDesigner. Tokens, type, shape, components, chrome, copy rules and the build contracts, with the file that owns each one, plus recipes for adding a site page, a guide or a tool web UI, and the drifts still open.
since: 2026-09-15 (written from the site as of 241849a8)
verified: 2026-09-15: values read from website/index.html, website/docs.css, website/site-nav.css, packaging/configurator/base.css, website/tools/build-site.mjs and packaging/configurator/sync_base.py
---

# Site design system: how a new page or tool UI should look and read

This is the reference for anyone adding a surface that should feel like
part of FNSTools: a new page on functionstore.tools, a docs guide, a tool's
own web UI served from TouchDesigner, or a sibling site in the Function
Store family. Each rule names the file that owns it. When this document and
a source file disagree, the source file wins and this document is the one
to fix.

Related records: [InstallSurfaceDesign.md](InstallSurfaceDesign.md) (why
there is one UI base under two shells), [PublicToolNames.md](PublicToolNames.md)
(what name a reader sees), [ParameterReference.md](ParameterReference.md)
(tooltips as documentation), [DocsEvidenceDerivation.md](DocsEvidenceDerivation.md)
(what the docs read off the live project), and the operational guide
[website/README.md](../website/README.md).

## 1. Pick the kind of surface first

Almost every new surface is one of five kinds, and each kind already has a
pipeline. Start from the existing example; do not invent a sixth pipeline.

| You are adding | Source you write | Wrapped / styled by | Closest example |
|---|---|---|---|
| A page about one package | `packaging/docs/<Package>.md` (+ entry in `packaging/catalog.json`) | `website/tools/build-site.mjs` into `/docs/<slug>/` | [packaging/docs/FNS_OpenExt.md](../packaging/docs/FNS_OpenExt.md) |
| A guide about the toolkit as a whole | `website/content/guides/<slug>.md` | same build, docs chrome | [getting-started.md](../website/content/guides/getting-started.md) |
| A standalone site page (prose, cards, tiers) | `website/content/<slug>.html`, a fragment | build wraps it in `head()`, `header()`, `FOOT` inside `<main class="plus-page">` | [privacy.html](../website/content/privacy.html), [patreon.html](../website/content/patreon.html) |
| A web UI served from TouchDesigner | a single self-contained `.html` that inlines the UI base | `packaging/configurator/sync_base.py` | [console_page.html](../modules/suspects/FNSTools/FNS_Console/console_page.html), [ColorUI/webui.html](../modules/suspects/FNSTools/ColorUI/webui.html) |
| A hand-built marketing page | an `.html` with its own inline `<style>` | nothing; you carry the chrome yourself | [website/index.html](../website/index.html) (the only one; avoid a second) |

The first three get the header, footer, fonts, search, analytics and link
validation for free. The fifth gets none of that and every rule below has
to be kept by hand, which is why the landing page is the only one.

## 2. Tokens

The palette is dark, near-black and neutral, with one warm accent. The
names are shared with the Function Store family sites; per the header of
[docs.css](../website/docs.css), only `--accent` is expected to differ per
site.

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0a0a0a` | page ground |
| `--bg-1` | `#111111` | raised surface: fold, card, callout |
| `--bg-2` | `#161616` | hover fill, table header |
| `--bg-3` | `#1c1c1c` | inline `code`, `kbd`, counts |
| `--bg-deep` | `#050505` | code blocks, the picker preview |
| `--border` | `#262626` | default hairline |
| `--border-strong` | `#3a3a3a` | section rules, secondary button outline |
| `--text` | `#f5f5f5` | headings, strong, body |
| `--text-dim` | `#a3a3a3` | ledes, descriptions, nav links |
| `--text-faint` | `#737373` (see drift D1) | meta lines, counts, captions |
| `--accent` | `#fbbf24` | links, primary button, glyphs, markers |
| `--accent-dim` | `#2a1f08` | tinted fill behind accent text |
| `--accent-bright` | `#fcd34d` | link hover, inline code text |
| `--green` | `#4ade80` | "live / ok" dot, free tier ticks, strings in code |
| `--max-w` | `1140px` | content width |

The UI base ([base.css](../packaging/configurator/base.css)) adds the app
tokens a site page does not need: `--accent-ink`, `--warn`/`--warn-dim`,
`--err`/`--err-dim`, `--radius` and `--stick`, plus an opt-in light theme
under `:root[data-theme="light"]`. The site and TouchDesigner are dark
everywhere, so only a page that is the whole window may offer the light
toggle.

Rules:

- **Use the token names, never raw hex,** in anything new. The accent at
  lower opacity is the one sanctioned literal: `rgba(251,191,36,0.22..0.32)`
  for accent borders and `0.07..0.09` for accent washes.
- **Amber means "you can act on this".** It is the link, button, badge and
  glyph colour. The code highlighter keeps amber off keywords for exactly
  that reason (comment in docs.css, "Code highlighting").
- **Token values change in every copy at once or not at all.** The copies
  are `website/index.html` (inline), `website/docs.css`, and
  `packaging/configurator/base.css` (itself synced into three shells). The
  `/get/` page loads both docs.css and the base, and the inline base wins
  the cascade, so a drifted value restyles the site header.

## 3. Typography

| Role | Setting | Where |
|---|---|---|
| Body | Inter 400, 16px, line-height 1.55 (landing) / 1.6 (docs) / 1.7 (docs reading body) | index.html, docs.css |
| Mono | JetBrains Mono 500, 0.9em | `code, kbd` |
| Hero title | `clamp(38px, 4.6vw, 58px)`, 600, letter-spacing -0.035em, line-height 1.08 | `h1.hero-title` |
| Page title | `clamp(30px, 4vw, 40px)`, 700, -0.025em | `.docs-main h1`, `.plus-page h1` (`clamp(32px, 4.4vw, 44px)`) |
| Section heading | `clamp(28px, 3.6vw, 36px)` landing, 24px in docs, 700, -0.02em | `.section-head h2`, `.docs-body h2` |
| Eyebrow / group label | 11px, 600-700, letter-spacing 0.08em, uppercase | `.eyebrow`, `.cfg-band__eyebrow`, `.side-group > summary` |
| Lede | 17px (18px on `.plus-page`), `--text-dim`, max 62-70ch | `.lede`, `.hero-sub` |
| Meta | 12-13px, `--text-faint` | `.hero-meta`, `.crumbs`, captions |

Load fonts with the same Google Fonts line the build uses (`head()` in
build-site.mjs): `Inter:wght@400;500;600;700` and `JetBrains+Mono:wght@500`,
with `system-ui` and `ui-monospace` fallbacks. A web UI served from
TouchDesigner may be offline, so it must look right on the fallbacks alone.

Headings get tighter tracking the bigger they are; body copy never does.
Keep reading columns to 62-74ch.

## 4. Shape: flat and editorial

The current direction, set by the 2026-09-13/14 passes (`4b96a754`,
`6a5ecc57`, `241849a8`), is flat: **hairline rules and whitespace separate
content.** The trailing override blocks at the end of index.html's `<style>`
and docs.css ("Documentation reading layout") show the intent:

- Cards on the landing page (`.path`, `.tier`, `.prod`, `.docs-callout`,
  `.try-band`) are transparent with a single `border-top: 1px solid
  var(--border-strong)` and no radius.
- Docs index cards are the same: transparent, `border-top`, zero radius.
- The on-page TOC is a 2px left rule.
- Where a box remains (category folds, buttons, badges, code blocks), the
  radius is **2-3px**.
- Tables drop their vertical cell borders in the reading layout.

For a new page: default to rules and whitespace, reach for a filled
`--bg-1` box only for something the reader must see as one unit (a fold, a
callout that carries an action), and keep radii at 2-3px. Round pills
(`999px`) stay reserved for filter chips.

This conflicts with older rules still in the tree (drift D2): `/patreon/`,
`/privacy/`, `/terms/` render through `.plus-page` styles with 12-16px
radii and filled cards, and base.css uses 8-12px. The flat pass is the more
recent decision, so it wins for new work.

## 5. Components

Reuse these by class name. If a page needs a variant, add a modifier beside
the original in the same file and say why in a comment, the way the
existing rules do.

| Component | Classes | Defined in | Notes |
|---|---|---|---|
| Buttons | `.btn` + `.btn-primary` / `.btn-secondary`, `.btn-lg` | index.html, docs.css, base.css | Primary is amber with `#0a0a0a` text; secondary is an outline that turns amber on hover. Arrow `→` at the end of an action label. |
| Fold (progressive disclosure) | `details.fold > summary` + `.fold-body` | index.html, docs.css | `+` / `−` marker in mono amber. Native `<details>`: works with JS off, focusable, found by Ctrl+F. |
| Category fold | `details.cat` with `.cat-glyph`, `.cat-name`, `.cat-pitch`, `.cat-count` | index.html | Glyph and pitch come from `catalog.json` `category_meta`. |
| Feature row | `.feat` with `.feat-icon`, `.feat-text` | index.html | 28px glyph column, name, one-line description. |
| Patreon marker | `.plus-mark` | index.html, docs.css | Class name kept from "Plus"; the visible text says **Patreon** ([PatreonNaming.md](PatreonNaming.md)). |
| Unlock callout | `.plus-note`, `.plus-note-actions` | docs.css | Top of a gated package's page. |
| Tiers | `.tiers > .tier` (+ `.tier--plus`), `.tier-tag`, `.tier-actions` | index.html, docs.css | Free ticks `✓` in green; Patreon items `◆` in amber. |
| Fact list | `ul.plus-facts` | docs.css | `◆` bullets with a bold lead-in; the pattern privacy.html uses. |
| Steps and alternatives | `ol.plus-steps`, `.paths > .path` + `.path-tag` | docs.css, index.html | A number in an accent-dim tag for a step; a word (Either / Or / Then) for paths that are alternatives, since a numbered row reads as a sequence. |
| Product cards | `.prod-grid > .prod` | index.html, docs.css | Injected from `content/family.json`; never typed by hand. |
| Badges | `.badges > .badge` (+ `.badge-cat`, `.badge-warn`, `.badge-surface`) | docs.css | Docs page header row. |
| Filter chips | `.surf-filter > .surf-chip` (`.on`) | docs.css | The one place pills are round. |
| Docs layout | `.docs-layout`, `.docs-side`, `.side-group`, `.docs-main`, `.crumbs`, `.lede`, `.toc`, `.docs-body` | docs.css | 244px sticky sidebar, collapses to accordions under 900px ([docs.js](../website/docs.js)). |
| Keys | `kbd` inside `.feat-keys` / `.parameters` | docs.css | 2px bottom border to read as a key. |
| Parameter table | `.par-wrap > .par-table` | docs.css | Generated from `packaging/parameters.json`; do not hand-write one. |
| Honest gap | `.page-todo`, `.par-todo` | docs.css | A missing piece is shown as missing. |
| Placeholder media | `.demo-placeholder`, `.embed-video` | index.html, docs.css | Dashed box with a plain label until the real recording exists. |

## 6. Layout and responsive behaviour

- **Width and gutter:** `.wrap { max-width: var(--max-w); padding: 0 24px }`,
  16px under 600px ([site-nav.css](../website/site-nav.css)).
- **Sticky header offset:** the header is sticky, so every page sets
  `scroll-padding-top: 84px` and `:target { scroll-margin-top: 84px }`.
  A new sticky element under it uses the same 84px.
- **Breakpoints in use:** 900px (nav drawer, docs sidebar, two-column bands
  stack), 860px (tiers, product grid, category lists go single column),
  760 / 700 / 600 / 560px for local tweaks. Reuse 900 and 600 before adding
  a new one.
- **Grids stack to one column** on narrow screens and use
  `minmax(0, 1fr)` so long names cannot push the page wide.
- **Motion** is limited to 0.15-0.2s colour, border and small translate
  transitions. Every page carries
  `@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }`.
- **Focus** is always visible: `outline: 2px solid var(--accent)` with a
  2-4px offset on links, summaries and controls.
- **Touch targets** in the mobile drawer and sidebar are padded to at least
  40px tall (`.nav-toggle` is 40x40).

## 7. Chrome: header, footer, head

Every generated page gets these from build-site.mjs, so a site page never
copies them:

- `head(title, description, canonical)`: meta, Open Graph, canonical,
  favicon, fonts, Pagefind CSS first then `site-nav.css` then `docs.css`
  (order matters, see the comment in `head()`).
- `header(current)`: brand lockup (logo, **FNSTools**, "by Function Store"),
  the `navLinks` array, GitHub and **Get FNSTools →** buttons, the
  `.nav-toggle` drawer driven by [site-nav.js](../website/site-nav.js).
  Pass the page's own path so its link gets `aria-current="page"`.
- `FOOT`: `FOOTER` links, `site-nav.js`, Pagefind, `docs.js`, Vercel
  analytics.

Rules:

- **The nav exists twice**: hand-written in index.html and `navLinks` in
  build-site.mjs. Change both, or a reader sees the links move between
  pages.
- **Adding a top-level page to the nav** means both copies plus the footer
  links, if it belongs there.
- A web UI served from TouchDesigner carries no site chrome. The one
  exception is the configurator, which leaves `<!-- FNS:HEADER -->` and
  `<!-- FNS:FOOTER -->` markers that the build fills for `/get/`.
- Titles follow `Topic | FNSTools` for utility pages and a plain sentence
  for pages that sell something (`FNSTools on Patreon: supporter tools, and
  what stays free`). Descriptions are one or two plain sentences that
  answer what the reader gets.

## 8. Interaction principles

1. **Progressive disclosure.** Answer the common question in the open and
   keep the precise answer one `<details>` away. Nothing is deleted to make
   a page shorter; caveats move into the fold under the step they belong
   to (website/README.md, "Free and Patreon").
2. **Works without JavaScript.** Content and navigation are HTML. Scripts
   only enhance: docs.js closes sidebar groups on mobile, Pagefind adds
   search and removes itself when its index is missing.
3. **Depictions are generated from the real source.** The picker preview on
   the landing page is built from the same catalogue `/get/` lists, so it
   cannot advertise a tool that does not ship. Any preview, count or list
   of tools on a new page should be generated the same way.
4. **Gated things stay visible.** Patreon packages are listed and tickable
   everywhere, marked with `.plus-mark`; the lock lives on the server.
5. **Show gaps.** An undocumented page, an empty parameter tooltip or a
   missing recording renders a visible placeholder (`.page-todo`,
   `.par-todo`, `.demo-placeholder`).

## 9. Voice and copy

These apply to site copy, docs markdown, generated strings and parameter
tooltips (which the docs render verbatim).

- **No em-dashes and no ` -- ` asides.** Use a colon, comma, semicolon or a
  new sentence. The build prints a note listing every page and tooltip that
  still has one (build-site.mjs, "House style").
- **No contrastive trope.** State what a thing does. Avoid "it is not X, it
  is Y", "not A but B" and "rather than".
- **Plain and specific.** Short sentences, concrete verbs, the real key
  combo or menu name. Headline form: `FNSTools - Enhance your TouchDesigner workflow`.
- **Public names in prose.** Readers see `BeatMod` where the package is `FNS_BeatMod`;
  identity keys, file names and shortcuts keep the prefix
  ([PublicToolNames.md](PublicToolNames.md)).
- **No version numbers on marketing pages.** Buttons say "Get FNSTools",
  downloads point at the `latest/` aliases, so a release needs no site
  rebuild.
- **Say Patreon.** The old name Plus survives only in class names. The tier name comes from the manifest's
  `toolkit.tiers`; never hard-code a tier-to-package map.
- **Keep claims true to the code in both directions.** A pitch that
  overstates hands a sibling's feature to the wrong product; one that
  understates drops a real feature (the comment at the top of
  [family.json](../website/content/family.json)). Privacy and terms claims
  live beside the code they describe for the same reason.
- **Honest labels on placeholders**: a placeholder says what is missing
  ("Recording coming soon").

## 10. Build contracts

A new page inherits these; a new pipeline has to provide its own.

- **Generated output is gitignored.** `website/docs/`, `get/`, `patreon/`,
  `privacy/`, `terms/` exist only locally and on the deploy. Edit the
  source, never the output.
- **Markers fail loud.** Injected blocks sit between
  `<!-- NAME:START -->` / `<!-- NAME:END -->` (`TOOLS`, `CONFIGURATOR`,
  `FAMILY`, `PLUSPKGS`, `FNS:HEADER`, `FNS:FOOTER`, `FNS:UIBASE`). A missing
  pair exits the build, because the alternative is a page that silently
  lists nothing.
- **Internal links are validated.** Every `/docs/...` link and `#heading`
  must resolve; `checkLinks()` refuses the build otherwise. Run it on any
  new fragment.
- **Slugs agree in three places**: `packageSlug()` in build-site.mjs,
  `package_slug()` in the wiki seeder, `_docsSlug()` in `build_manifest.py`.
  Lowercase, `_` becomes `-`. Guide filenames are the URL.
- **The UI base is inlined by generation.** Edit
  `packaging/configurator/base.css`, then
  `python packaging/configurator/sync_base.py --write`;
  `tests/test_ui_base_sync.py` fails on a stale copy.

## 11. Recipes

### A new site page (for example `/changelog/`)

1. Write `website/content/changelog.html` as a fragment: an HTML comment
   saying what the page is and what must stay true, then `<h1>`,
   `<p class="lede">`, and `<h2>` sections using the components in §5.
   Copy the shape of [privacy.html](../website/content/privacy.html).
2. In build-site.mjs, add the page to the `/privacy/` and `/terms/` loop
   (`[slug, 'Title | FNSTools', 'description']`), or give it its own block
   modelled on `/patreon/` if it needs injected data. Anything listed from
   `catalog.json` or `family.json` gets a marker pair and a refusal when the
   marker is missing.
3. If it belongs in the nav, add it to `navLinks` **and** the hand-written
   nav in index.html; add it to `FOOTER` if it belongs there.
4. If `website/.vercelignore` or `vercel.json` needs a redirect or header,
   add it there (no comments; Vercel's schema rejects them).
5. `cd website && npm run build && npm run serve`, check the page at
   1140px, 900px and 400px, keyboard-tab through it, and read the build
   output for dash notes and link refusals.

### A new docs guide

1. `website/content/guides/<slug>.md` with frontmatter `title`, `summary`,
   `section` (`guides` or `reference`) and an explicit `order`.
2. Use `##` headings; they become the "On this page" list. Tag every code
   fence with a language.
3. Link to the next guide down the ladder and back up.
4. `npm run build`.

### A new package page

Use the CMS (`npm run cms`) or edit `packaging/docs/<Package>.md`. Only
`package` is required in frontmatter; `category`, `description` and
`author` belong to `catalog.json`. Parameters come from `par.help` in
TouchDesigner, so fix tooltips there.

### A tool web UI served from TouchDesigner

1. One self-contained `.html` file (it may be served from a Text DAT with
   no site next to it).
2. Put a `/* FNS:UIBASE:START */ ... /* FNS:UIBASE:END */` block in its
   `<style>`, add the file's repo path to `TARGETS` in
   [sync_base.py](../packaging/configurator/sync_base.py), and run it with
   `--write`. Style the page with the base's tokens and components
   (`.btn`, chips, cards, dialogs, toast, `body.app` for panel density).
3. If it is framed inside the console, detect `window.self !== window.top`
   and drop page-level chrome, the way the picker's embedded mode does.
4. Ship no light-theme toggle unless the page is the whole window.
5. If the tool shows up as a console or hub tab, follow
   [ConsoleTabContract.md](ConsoleTabContract.md) or
   [HubContract.md](HubContract.md) for the registration side.

### A sibling site in the Function Store family

Keep the token names, `site-nav.css` and `site-nav.js` (they are already
the merged family version), the brand lockup markup, and the flat shape.
Change `--accent` and its `-dim`/`-bright` pair only. Add the product to
`website/content/family.json` so both FNSTools pages that list the family
pick it up.

## 12. Checklist before merging a new surface

- [ ] Uses an existing pipeline from §1.
- [ ] Only token names; no new raw colours except accent-alpha borders.
- [ ] Flat shape: rules over boxes, radii 2-3px, pills only for chips.
- [ ] Reuses §5 components; any new component is commented at its rule.
- [ ] Readable at 400px with no horizontal page scroll; grids stack.
- [ ] Visible focus, reduced-motion rule, works with JavaScript off.
- [ ] Nav changed in both copies, if at all.
- [ ] No em-dashes, no ` -- `, no contrastive phrasing, public tool names,
      no version numbers, Patreon wording.
- [ ] Every list of tools, tiers or products is generated from
      `catalog.json`, the manifest or `family.json`.
- [ ] `npm run build` passes with no new dash notes; for a TD web UI,
      `python packaging/configurator/sync_base.py` reports all copies current.

## 13. Open drifts

Found while writing this document. Each is a place where two sources
disagree today; none is fixed here.

- **D1. `--text-faint` has two values.** index.html sets `#929292`; docs.css,
  base.css and its synced copies set `#737373`. The landing value is the
  lighter, more legible one and reads like a contrast fix that reached only
  one copy. Decide on one value and change every copy together (§2).
- **D2. Two shape languages.** The flat pass (§4) overrides the landing page
  and the docs layout, but `.plus-page` (Patreon, Privacy, Terms), the
  `.plus-note` callout, `.embed-video` in docs.css and the whole UI base
  still use 8-16px radii and filled cards. New work follows the flat pass;
  the older rules should be brought in line or given a stated reason to
  differ (the in-TD base plausibly has one: panel density).
- **D3. Duplicated component rules differ.** index.html and docs.css both
  define `.tier`, `.prod`, `details.fold`, `.plus-mark` and `.btn`, and the
  values have already split (`.btn` radius 3px on the landing page, 8px in
  docs.css; fold summary colour `--text-dim` versus `--text`).
- **D4. FNS_Remote has its own palette.**
  [remote_page.html](../modules/suspects/FNSTools/FNS_Remote/remote_page.html)
  uses `--bg:#15171a`, green `--acc:#78d64b` and short token names, outside
  the UI base. A phone remote may want a distinct look; if so, record why,
  otherwise add it to `TARGETS`.
- **D5. Stale paths in the records.** [InstallSurfaceDesign.md](InstallSurfaceDesign.md)
  and the header comment of base.css point at
  `FNSTools/FNS_Console/console_page.html`; the file lives at
  `modules/suspects/FNSTools/FNS_Console/console_page.html`, and the base
  comment still says "both shells" while `TARGETS` lists three.
- **D6. Placeholder brand assets.** `favicon.png` and `og-image.png` are
  generated placeholders (website/README.md, "Brand assets"); the brand
  lockup on every page uses them.
