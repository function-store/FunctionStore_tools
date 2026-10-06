---
status: in-force
summary: The install picker's search ranks with a FuzzyMatch port over the card fields, the CMS tags, the operator types a tool stands in for and a docs word index each manifest row carries as `search`; a query shows one ranked list, and a Compact toggle draws title-only tiles.
since: v3.2.63 (2026-10-05)
verified: 2026-10-03
skill: fns-packaging
---

# Install picker search and compact view

Owner feedback on the install picker (/get/, the installer's served page,
the console's Install tab), 2026-10-03: "there are just so many tools and
features". The search was a plain substring over what a card shows (name,
description, category, surfaces), so someone typing "midi" or "undo" never
found a tool whose card did not happen to say it, and every hit sat in its
category section, so a search scattered its answers down the page.

Two changes, both in `packaging/configurator/index.html`:

- **Search goes deeper and ranks.** It matches the card fields, the CMS
  tags, the operator types a tool is an alternative for, and the words of
  the tool's documentation. While a query is present the list is ONE ranked
  grid, best match first.
- **Compact view.** A toggle in the filter bar draws title-only tiles.

## What a package answers to

`FNSSearch.prepare(p, labelOf)` turns a manifest row into fields; each field
has a weight that is ADDED to the FuzzyMatch tier of a hit in it, so a title
hit outranks the same hit in a description:

| Field | Weight | Fuzzy? |
|---|---|---|
| title, name (minus `FNS_`), family `op_label` | 0 | yes |
| each family `search_words` tag (the CMS tags), each `alternatives_for` type | 0.3 | yes |
| category, family `op_group`, each surface's label, author name | 0.4 | strict |
| description, family `summary`, `trial` + pricing summary, each variant id + summary | 0.5 | strict |
| docs head words (`search.head`) | 0.6 | word start only |
| docs body words (`search.body`) | 0.8 | word start only |

Ranking is `scripts/shared/FuzzyMatch.py`'s, ported line for line into the
page as `FNSFuzzy` (EXACT, PREFIX, WORD, SUBSTRING, then the fuzzy INITIALS,
TYPO, SUBSEQUENCE). A token takes its best field; a row's tier is its worst
token's weighted tier; ties go to the tighter hit, then the title.

The rules that keep it honest:

- **Every weight is under 1**, so a strict hit anywhere (a docs word
  included, at most 2.8; a strict substring, at most 3.5) still ranks above
  any fuzzy one (4 and up). This is the FuzzyMatch promise that the fuzzy
  tiers only ever fill BELOW the literal hits.
- **Only short name fields take fuzzy hits.** A typo or a subsequence over a
  description or a docs page matches almost anything.
- **A token under three letters matches word starts only**: no substring,
  no docs. "ui" inside "quick" put every Quick* tool on the list, and "ab"
  matched 26 tools through table, label and absolute.
- **A subsequence needs four letters.** "lag" was a subsequence of
  SimpleSceneChanger.
- **Hotkeys are not searched.** Nearly every binding carries alt or ctrl,
  so "alt" listed 41 tools with CustomParTools above AltSelect.

## The docs index: `search` on each manifest row

`packaging/search_index.py` (pure Python, no TD imports) reads
`packaging/docs/<Package>.md` and returns `{"head": "...", "body": "..."}`:
two strings of space-joined, sorted, deduplicated words.

- **head**: the frontmatter `summary` and feature names, the `##` headings,
  the `**bold**` terms. What the doc says the tool is about.
- **body**: every other prose word, minus the head.
- **Folded like a query.** Words come from `FuzzyMatch.words`, so the page
  compares like with like: ChopBank gives chop, bank and the compound
  chopbank; zero-below gives zero and zerobelow; colour folds to color. An
  acronym plural is one word (CHOPs -> chops, never cho + ps), trailing
  digits go (Fader1 -> fader).
- **Dropped**: words under three letters, stopwords, fenced and inline
  code, link targets, HTML tags, URLs, every word the card already answers
  to (title, name, description, family tags and summary; those fields score
  higher anyway), and any word in more than 30% of all docs ("parameter",
  "network", "touchdesigner": they say nothing about one tool).
- **Matched by word start only.** A token hits a docs word it starts,
  never one it merely sits inside, and never fuzzily. The card shows
  `in docs: undo` when a docs word carried a token no card field did, so a
  deep hit explains itself.

`build_manifest.Build()` loads the module by path (the build is exec'd into
TD's namespace, so there is no package to import from), builds the index
over every row once, and writes `search` **presence-style**: a row whose
doc adds nothing carries no key. A **preview** row carries none either:
the published manifest names a preview and describes it in one line
(docs/PreviewPackages.md, Limits), and only the creator's picker shows it.
`Build()` reports the cost as `search_bytes`.

### Size budget

Measured 2026-10-03 over 98 docs: **80 KB raw, 26 KB gzipped**, against a
153 KB manifest. `tests/test_search_index.py` fails above 100 KB raw or
35 KB gzipped. The cheapest further cut, if it is ever needed, is the
common-word share (20% saves about 5 KB); CamSequencer's doc alone is a
tenth of the index.

## Where the field travels

- `Build()` writes it into `manifest.json`, `configurator/manifest.js` and
  the standalone, so it rides the store manifest the updater downloads and
  the installer serves to the in-TD picker (`/manifest.js`) without a
  route of its own.
- The updater reads package rows with `.get()` and indexes them by name;
  nothing validates manifest keys strictly (checked 2026-10-03), so an
  unknown key is ignored.
- /get/: `website/tools/build-site.mjs` back-fills `search` from the repo
  manifest into the baked page (the docs are newer than any published
  release, the same reason the catalog's description wins), and the page's
  runtime merge keeps the baked `search` over a live manifest that lacks it.
- A manifest without `search` still searches every other field.

## The results

- A query with at least one token renders one ranked grid (`.grid.ranked`).
  Each card names its category, since there are no section headings. The
  sections and their fold state come back when the field is cleared.
- **Enter in the search ticks the top hit**, through the card's own
  checkbox so a Patreon tool still asks; it never unticks.
- The category rail, under a search, scrolls to that category's best hit
  instead of a section that is not drawn.
- The results line, the filter pills, the access counts and Select/Clear
  shown act on exactly what is listed (`shownTools`), as before.

## Compact view

A **Compact** toggle in `.bar-filters`, off by default, remembered per
viewer in localStorage (`fns.compact`, wrapped in try/catch like every key
on the page). It is a view, not a filter: every card stays, only the words
go. It toggles the `dense` class on `#list`; nothing re-renders.

- **Kept**: the checkbox, the title, New, installed / will install / will
  be removed, the Patreon chip, a trial chip, a placed tool's undo, and
  under a search the category and the `in docs:` line.
- **Hidden**: the description, the byline, the docs and site links, the
  hint chips, the where-it-lands chips, the variant chips, and Place on a
  card that is not placed.
- **The description is the tile's hover**: the card's `data-tip` already
  carries it.

The picker-only CSS sits outside the `FNS:UIBASE` markers, which
`sync_base.py` regenerates from `base.css`.

## Rejected

- **Fetching the docs at runtime.** The page served from inside
  TouchDesigner has no site to fetch from, and the standalone works offline.
- **A separate index file.** One more fetch per flavor, and the bucket
  sends no CORS headers, so a 127.0.0.1 page would need its own installer
  relay. On the manifest row it rides every existing path for free.
- **Substring over the docs text.** Folding joins the words, so a
  substring matches across word boundaries ("lag" in "dial agent"), and a
  long text holds nearly every short string.
- **Fuzzy over the docs.** A subsequence of a few hundred words matches
  anything.

## Rolling it out

The page change works the day it lands: the ranked list and Compact need
no new data. The docs words reach a picker with the next release's
`Build()`. The repo manifest was **not** regenerated when this landed: a
mid-cycle `Build()` is release-shaped. On 2026-10-03 it added the two
unreleased packages (PaneSearchRegistry, SearchFix), whose `whatsnew` the
version-carry rule would then freeze from that day's notes. It also rewrote
twenty rows with live drift (portability, hotkeys, cooking) and re-rendered
the surface icons. The served picker inside TouchDesigner is a snapshot
`build_installer` embeds into `FNS_Installer/configurator_html`;
`BuildBootstrap()` refreshes it at release, and `EnsureDevRails()` refreshes
the dev root's copy on demand.

## Tests

- `tests/test_search_index.py`: word folding and drops, head and body, the
  real index against the committed manifest, the size budget, and that
  `Build()` and the site carry the field.
- `tests/test_picker_search.py`: evaluates the page's own `FNS:SEARCH`
  block in node from both shells. FNSFuzzy against FuzzyMatch.py over the
  palette corpus (every tier), the ranking table on the real catalog (math
  chop, midi fader, a CMS tag, typos, a docs-only word, short queries), the
  strict-above-fuzzy invariant, and the page wiring.
- `tests/test_foreign_packages.py` and `tests/test_tier_variants.py` pin
  that a trial and a variant summary stay searchable.
