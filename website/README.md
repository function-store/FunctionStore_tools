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
```

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

## Release links

Download buttons are stamped with the published release at build time,
read from the rolling manifest at
`https://pub-8001b4bd92174be7a4544571b53f23da.r2.dev/fnstools/manifest.json`.
If that fetch fails the build says so and keeps the release already in
`index.html`, so the links always point at something real.

The page also tries to refresh them at runtime, but **that fetch is
currently blocked**: the r2.dev bucket sends no
`Access-Control-Allow-Origin` header. Enabling CORS on the bucket would
make the page self-update between deploys. Until then, re-run the build
after each release.

Note the artifact is still named `FunctionStore_tools_2025.tox` — the
bucket path is already `fnstools`, but the `.tox` filenames have not been
renamed. The filename is a constant in `index.html` and in
`tools/build-site.mjs`; do not assume it tracks the brand.

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
