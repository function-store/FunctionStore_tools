---
status: in-force
summary: The site publishes /catalog.json, one JSON document of the published catalogue, so the Function Store portfolio (functionstore.xyz) renders its Tools section from this repo instead of a Notion database. What is in it, why it is derived from the site build and not the bucket manifest, and the additive-fields rule that keeps a consumer we do not deploy from breaking.
since: 2026-09-30
verified: 2026-09-30 -- built locally and parsed by tests/test_catalog_feed.py, 82 tools (58 free, 24 Patreon) across 13 categories, no preview package present, every url under /docs/
---

# The portfolio catalog feed: this repo is the live list of tools

Until 2026-09 the portfolio at functionstore.xyz kept its own tools list in
a Notion database, filled by a Patreon import and curated by hand. It
disagreed with this repo the moment either side moved, and it was the
second time the same 30 descriptions were written. The owner's decision
(2026-09-30): this repo is the live list, and the portfolio reads it.

## What ships

`website/tools/build-site.mjs` writes `website/catalog.json` as its last
generated surface, and Vercel serves it at
`https://functionstore.tools/catalog.json` with
`Access-Control-Allow-Origin: *` and a five-minute cache (`website/vercel.json`).
Gitignored like every other generated file.

```json
{
  "schema": 1,
  "generated": "2026-09-30T00:00:00.000Z",
  "site": "https://functionstore.tools",
  "toolkit": { "name": "FNSTools", "td_build": "2025.33070" },
  "links": { "home", "get", "pick", "docs", "patreon", "community", "github", "support" },
  "counts": { "tools": 82, "free": 58, "patreon": 24, "categories": 13 },
  "categories": [ { "name", "glyph", "pitch", "group", "deprioritized", "count", "free", "patreon" } ],
  "tools": [ {
    "name": "FNS_CustomParTools", "title": "CustomParTools", "slug": "fns-custompartools",
    "url": "https://functionstore.tools/docs/fns-custompartools/",
    "category": "Parameters", "description": "...",
    "access": "free" | "patreon", "tier": "Base" | "", "unlock": "the Patreon Base tier or higher, or a Gumroad licence key" | "",
    "key_available": false, "surfaces": ["Toolbar button"],
    "author": { "name", "url" } | null,
    "recommended": true, "minor": false, "foreign": false,
    "homepage": "", "pricing": "", "variants": ["Pro build"]
  } ],
  "family": [ { "name", "kind", "pitch", "url", "access" } ],
  "guides": [ { "title", "summary", "section", "url" } ]
}
```

`tools` is in display order: the categories as the site lists them (the
`deprioritized` plumbing last), alphabetical by public title inside each.
The consumer sorts as it likes; the order is a sensible default, not a
contract.

## Why the site build, not the bucket manifest

The rolling manifest at `storage.functionstore.tools/fnstools/manifest.json`
already describes every package, so the obvious feed was that one. It is
the wrong one for a web page, for four reasons the site build already
answers:

| The manifest | The site build |
|---|---|
| a release behind by definition: a description edited today reaches it at the next publish | reads `catalog.json` and `packaging/docs/` at deploy, which is every markdown push |
| sends CORS for `functionstore.tools` only (`/get/` refreshes from it) | its own host, `*` on one path |
| carries artifacts, hashes, versions, rails: install data no page needs | only what a listing shows |
| lists previews, which the picker filters per signed-in account | the preview filter has already run; a preview is absent, not flagged |

It also gives the portfolio exactly the presentation the site has settled:
`title` is the public name (`docs/PublicToolNames.md`), `category_meta`
supplies the glyph, pitch and group, `access` is already resolved to the
tier's label through the manifest ladder, and `unlock` is the sentence the
docs page prints.

## The additive-fields rule

The consumer is `myPortfolioWebsite/tools/build-tools-from-fnstools.mjs`
and the `Tools` component in its `components/sections.jsx`. They read
fields by name, they deploy from another repo, and nothing here runs their
tests. So under `schema: 1` a field is only ever **added**. Renaming or
removing one bumps `schema`, and the consumer is changed before the bump
ships; the consumer refuses a document whose `schema` it does not know
and keeps its committed snapshot, so a mismatch degrades to a stale list,
never a broken page.

`python tests/test_catalog_feed.py` pins the wiring: the feed is written
after the last refusal gate, it is gitignored, `vercel.json` sends the CORS
header, the README names it, and a locally built `website/catalog.json`
(when present) parses with the counts consistent and no preview in it.

## What this does not do

It does not push. The portfolio's Vercel build fetches the feed
(falling back to its committed snapshot when the fetch fails), and the
page refreshes it in the browser. Nothing in this repo has to know the
portfolio exists, and a change here reaches functionstore.xyz within a
browser cache window of this site's deploy.
