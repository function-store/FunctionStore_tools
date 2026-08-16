# tools.functionstore.xyz

The FNSTools site: a hand-written landing page plus generated docs.
Static files, no framework, deployed on Vercel with **root directory =
`website`**.

## Where the content actually lives

```
packaging/catalog.json     category + description per package  (curated)
packaging/docs/<Name>.md   prose + frontmatter per package     (curated)
website/index.html         landing page                        (hand-written)
website/docs/              GENERATED — gitignored, built on every deploy
website/get/               GENERATED — gitignored, the online configurator
```

`/get/` is emitted from `packaging/configurator/index.html` with the
manifest baked in (the bucket now sends CORS, so the page also refreshes
that manifest at runtime) and `window.FNS_SITE` set, which promotes the
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

**Do not commit `website/docs/` or `website/get/`** — both are gitignored.
Vercel runs this same build on every deploy, so the generated tree exists
only on your machine (for preview) and on the deploy. Build output in git
is what used to let the site drift from its sources, and it needed a CI
job to police it; now there is nothing to drift.

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
2. Commit the markdown. That is the whole step — the deploy builds the
   pages from it.
3. Optionally **Build site** in the CMS (or `npm run build`) first, to see
   the result locally and to catch a bad link before the deploy does.

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

Vercel project **`fnstools`**, root directory **`website`**. Vercel builds
the site on every deploy: `vercel.json` sets `installCommand` to `npm ci`
and `buildCommand` to `npm run build`, and serves the result from
`outputDirectory: "."`. (The file cannot carry comments — Vercel's schema
rejects unknown keys, `//` included.)

That is the whole pipeline. Push the markdown; the deploy generates the
pages. Nothing generated is committed, so nothing can go stale, and there
is no CI job policing the gap — there is no gap.

A build failure is the safety net: a broken internal link, a docs file with
no catalog entry, a frontmatter/filename mismatch all fail the build, so
the deploy fails and **production keeps serving the last good build**. Run
`npm run build` locally first if you would rather see it before Vercel does.

`.vercelignore` must not exclude anything the build needs — `package.json`,
`package-lock.json` and `tools/` all have to reach the builder. It keeps out
`node_modules/` (~60 MB of pagefind binaries), the generated `docs/` and
`get/`, and `.env.local`, which the CLI writes on link with a
`VERCEL_OIDC_TOKEN` in it.

**Set the production branch** to whichever branch you deploy from. If it is
not set, a push only produces a Preview and production stays where it is
until someone promotes a deployment by hand — which is exactly how the live
site once sat 30 hours behind the repo.

Also turn on **Web Analytics** in the project — the page already ships the
stub and the `/_vercel/insights/script.js` tag the platform serves once it is
enabled. It is cookieless, which is why there is no consent banner.

## Release links

Download buttons point at the **mutable `latest/` aliases**
(`latest/FNSTools.tox`, `latest/FNS_Installer.tox`) that `upload.py`
publishes beside each release. That is deliberate: a release cannot leave
the buttons serving bytes that are no longer current, so **a version bump
needs no site rebuild**. `latest/` is for humans only — installs still
resolve pinned URLs from the manifest, because reproducible installs are
what make bug reports correlatable (`publish.py`, "Never publish a mutable
`latest/<Package>.tox`").

**The landing page carries no version number at all** — the buttons say
"Get FNSTools", not "Get FNSTools v3.0.1". Nothing release-shaped is
stamped into it, so there is no number that can go stale and no reason to
rebuild the site when a release ships.

`/get/` bakes the published manifest (it carries the `rails` hashes), but
that is display data: the paste script it hands you re-fetches the rolling
manifest *at paste time* from inside TouchDesigner via `requests`, and
resolves every artifact and hash from that. A `/get/` page built months ago
still installs the current release; only the picker's package list can lag.

The page also refreshes hrefs at runtime, and **that fetch now works**: the
bucket sends `Access-Control-Allow-Origin` for `tools.functionstore.xyz`.
The browser upgrades hrefs from `latest/` to the pinned release, so
visitors get reproducible URLs, and `/get/`'s picker list stays current
between deploys. If the fetch ever fails the static `latest/` hrefs still
resolve.

Everything is served from the custom domain `storage.functionstr.com`, not
the `pub-*.r2.dev` development endpoint — the latter is rate-limited, not
intended for production, and can be switched off in the bucket settings.

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
