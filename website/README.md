# tools.functionstore.xyz

The FNSTools site: a hand-written landing page plus generated docs.
Static files, no framework, deployed on Vercel with **root directory =
`website`**.

## Where the content actually lives

```
packaging/catalog.json     category + description per package  (curated)
packaging/docs/<Name>.md   prose + frontmatter per package     (curated)
website/index.html         landing page                        (hand-written)
website/docs/              GENERATED — wiped and rebuilt every run
website/get/               GENERATED — the online configurator
```

`/get/` is emitted from `packaging/configurator/index.html` with the
manifest baked in (the bucket serves no CORS header, so the page's live
refresh is best-effort) and `window.FNS_SITE` set, which promotes the
**Copy install script** button — the paste rail described in
`packaging/README.md`. Edit the configurator, not the emitted page.

`packaging/docs/` is the source of truth for documentation. It is *not*
generated from the GitHub wiki — the wiki seeded it once
(`packaging/docs_seed_from_wiki.py`) and is now frozen. Edit the markdown.

One file per shipping package, filename matching the `catalog.json` key
exactly. That is what lets the same markdown be embedded into each tool
later, and what makes `help_url` in `manifest.json` point at a page that
exists.

`catalog.json` keeps owning `category` and `description`; frontmatter must
not duplicate them. The build joins the two on package name and **refuses
to build** if they disagree — a `.md` with no catalog entry, a catalog
package with no `.md`, a frontmatter `package` that does not match its
filename, or an internal `/docs/` link pointing at a page or heading that
does not exist.

## Build

```bash
cd website
npm install
npm run build     # generate pages, then index them for search
npm run serve     # http://localhost:3000
```

| script | does |
| --- | --- |
| `npm run build` | pages + search index (use this one) |
| `npm run pages` | pages only — leaves the existing search index alone |
| `npm run search` | re-index only |

Commit the generated `website/docs/` — Vercel serves these files directly
and runs no build step.

## The CMS

```bash
npm run cms       # http://127.0.0.1:8787
```

An internal editor for the two curated sources. Left: every package,
grouped by category, with `STUB` and `TODO` badges and a filter. Middle:
the metadata fields and the markdown. Right: live preview, the built page,
and build output.

It writes **straight to `packaging/catalog.json` and
`packaging/docs/*.md`** — there is no database and no staging step. Review
with `git diff`, undo with `git checkout -- packaging/`.

- **Save** is `⌘S`. The window warns before you navigate away dirty.
- **Build site** runs `build-site.mjs` and shows its output, including the
  validation failures — so a link to a heading that does not exist surfaces
  here rather than at deploy time.
- **Features are derived, not typed.** The list re-syncs from the `##`
  headings in the body as you write, keeping the icon and hotkeys attached
  to each surviving anchor. That is what keeps `features[]` anchors and the
  real heading slugs from drifting apart.
- Hotkeys are one per line, `KEYS = what it does`.

### Categories

**Categories** in the top bar edits the category list itself — add, rename,
reorder, delete, and set each one's glyph and one-line pitch.

Order is meaningful: it is the order sections appear on the landing page,
in the docs sidebar, and in the installer picker. Move rows with ▲▼.

Renaming moves every package in that category with it, in a single write.
That is deliberate — the site build refuses to run on a package whose
category is not in the list, so a half-applied rename would leave the repo
unbuildable. Deleting is only allowed once a category is empty; the button
stays disabled while anything is still in it.

The glyph and pitch live in `catalog.json` under `category_meta`, beside
the category list. `build_manifest.py` reads only `categories` and
`packages`, so that key is invisible to packaging and to the manifest —
it is website presentation. It used to be hardcoded in `build-site.mjs`,
which meant renaming a category silently dropped its glyph and pitch.

Bound to `127.0.0.1` on purpose: this process writes to the repo, so it
must not be reachable from the network. There is no auth because there is
no remote access.

Saving a file rewrites its frontmatter through the same YAML serializer,
so quoting is normalised. Every file has been run through it once already,
which means a `git diff` after editing shows only what you actually
changed. Prose is never touched — including trailing double-spaces, which
are markdown hard line breaks.

If a file changed on disk after the editor loaded it, saving returns a
conflict instead of clobbering it. Reload and redo the edit.

## Adding or changing a tool's docs

1. `npm run cms`, edit, Save. (Or edit `packaging/docs/<Name>.md` by hand —
   the CMS is a convenience, not a gate.)
2. **Build site** in the CMS, or `npm run build` in a terminal.
3. Commit both the markdown and the regenerated `website/docs/`.

A package must exist in `catalog.json` before it can have docs — that file
is derived from the TouchDesigner project, so new packages appear by
adding the tool the normal way and re-running `build_manifest.py`. The CMS
edits packages; it does not invent them.

The landing page's tool catalogue is generated too, between the
`<!-- TOOLS:START -->` / `<!-- TOOLS:END -->` markers in `index.html`.
Everything outside those markers is hand-written — edit it freely.

## Frontmatter

Only `package` is required. Everything else is optional.

```yaml
---
package: CustomParTools           # must equal the filename and a catalog key
summary: One line, used if the catalog description is empty.
features:                         # drives the "On this page" list
  - name: QuickExt
    anchor: quickext              # must match the generated heading slug
    icon: CustomParTools.png      # from repo icons/, copied to /docs/assets/
    hotkeys:
      - {keys: "Ctrl+Alt+Drag", does: "Promote as iop"}
platforms: [windows]              # omit when it runs everywhere
credit: {name: AlphaMoonbase.berlin, url: "https://alphamoonbase.de/"}
video: "https://youtu.be/j43gZ0MB2xo"
---
```

## Deploying

Vercel project **`fnstools`**, root directory **`website`**.

`vercel.json` declares `buildCommand` and `installCommand` as empty on
purpose: `website/docs/` is generated and committed, so a deploy is a pure
static upload. Without those, Vercel auto-detects the `build` script in
`package.json` and runs pagefind at deploy time for nothing. (The file
cannot carry comments — Vercel's schema rejects unknown keys, `//`
included.)

`.vercelignore` keeps `node_modules/` out of the upload: the repo
`.gitignore` covers it, but it lives at the repo root while the deploy root
is `website/`, so the CLI never reads it. That is the difference between a
1.8 MB upload and a 61 MB one. It also excludes `tools/` (build and CMS
scripts, never served) and `.env.local`, which the CLI writes on link with a
`VERCEL_OIDC_TOKEN` in it.

To stand it up before this branch is merged, point the project at this branch
as its production branch, then switch it to the real one after the merge.
Every other branch gets a preview URL automatically.

Also turn on **Web Analytics** in the project — the page already ships the
stub and the `/_vercel/insights/script.js` tag the platform serves once it is
enabled. It is cookieless, which is why there is no consent banner.

## CI

`.github/workflows/website.yml` runs on any change to `website/`,
`packaging/docs/` or `packaging/catalog.json`.

It builds, and then asserts that the committed `website/docs/` and
`index.html` match what the build produces. That check is the point of the
job: the generated output is committed so Vercel needs no build step, which
means it can go stale silently — edit a `.md`, forget to rebuild, and the
site would show something other than the source. CI makes that a failed
build instead.

The build is reproducible, so the comparison is exact. CI sets
`FNSTOOLS_NO_RELEASE_FETCH=1`; otherwise a release published between the
commit and the run would restamp `index.html` and fail the check for reasons
nobody changed.

Two non-blocking reports land in the job summary: which packages are still
documented only by their catalog line, and whether a newer release has been
published than the one the download links point at.

## Release links

Download buttons point at the **mutable `latest/` aliases**
(`latest/FNSTools.tox`, `latest/FNS_Installer.tox`) that `upload.py`
publishes beside each release. That is deliberate: a release cannot leave
the buttons serving bytes that are no longer current, so **a version bump
needs no site rebuild**. `latest/` is for humans only — installs still
resolve pinned URLs from the manifest, because reproducible installs are
what make bug reports correlatable (`publish.py`, "Never publish a mutable
`latest/<Package>.tox`").

Only the visible version **label** is stamped at build time, read from the
rolling manifest at
`https://pub-8001b4bd92174be7a4544571b53f23da.r2.dev/fnstools/manifest.json`.
A stale label is cosmetic: it sits next to a download that is still
correct. Rebuild after a release if you want the number to match.

The page also tries to refresh label and hrefs at runtime, but **that fetch
is currently blocked**: neither the r2.dev bucket nor
`storage.functionstr.com` sends an `Access-Control-Allow-Origin` header.
Enabling CORS on the bucket would make the label self-correcting and would
upgrade the hrefs from `latest/` to the pinned release in the browser.

The bootstrap artifact is `FNSTools.tox`, renamed from
`FunctionStore_tools_2025.tox` in the v3.0.0 redesign. The filename is a
constant in `index.html`; do not assume it tracks the brand.

## Brand assets

`favicon.png` and `og-image.png` are **placeholders** generated by
`tools/make-brand-assets.py`. There is no real square FNSTools mark in the
repo. Replace both and delete the script.

## Three slug functions must agree

`packageSlug()` here, `package_slug()` in `docs_seed_from_wiki.py`, and
`_docsSlug()` in `build_manifest.py` all lowercase the name and turn `_`
into `-`. If one changes, `help_url` starts pointing at 404s. The heading
slugifier is duplicated the same way (`slugify` in this build script and
in the seeder).
