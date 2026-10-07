"""packaging/search_index.py -- the words each package's user-facing doc adds
to the install picker's search (docs/PickerSearch.md).

The picker used to search only what a card shows, so a tool whose doc talks
about "undo" or "timecode" was invisible to someone typing it. Build() now
attaches each doc's word list to the manifest row as `search`; this pins
how the list is made and what it costs the manifest.

    python tests/test_search_index.py
"""
import importlib.util
import io
import json
import os
import re
import subprocess

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(_ROOT, 'packaging')
DOCS = os.path.join(PKG, 'docs')
BM = os.path.join(PKG, 'build_manifest.py')
SITE = os.path.join(_ROOT, 'website', 'tools', 'build-site.mjs')
FAILS = []

# What the index may cost the manifest (docs/PickerSearch.md, size budget).
# Measured 2026-10-03 over 98 docs: 80 KB raw, 26 KB gzipped.
BUDGET_RAW = 100000
BUDGET_GZIP = 35000


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


spec = importlib.util.spec_from_file_location('search_index', os.path.join(PKG, 'search_index.py'))
si = importlib.util.module_from_spec(spec)
spec.loader.exec_module(si)


def manifest_rows():
    """The committed manifest's rows: the index must build from HEAD's shape."""
    with io.open(os.path.join(PKG, 'manifest.json'), encoding='utf-8') as f:
        return json.load(f)['packages']


print('1. words are split and folded the way the picker folds a query')
w = si.Words("ChopBank's zero-below Fader1 in1 CHOPs and TOPs colour randomise it's the")
check('camelCase gives the parts and the compound',
      all(x in w for x in ('chop', 'bank', 'chopbank')), w)
check('a hyphenated word gives its parts and the compound',
      'zero' in w and 'zerobelow' in w, w)
check('trailing digits go (Fader1 -> fader); a short stem goes entirely (in1)',
      'fader' in w and 'fader1' not in w and 'in' not in w and 'in1' not in w, w)
check('an acronym plural is one word (CHOPs -> chops, never cho + ps)',
      'chops' in w and 'tops' in w and 'cho' not in w and 'ps' not in w, w)
check('British spellings fold like FuzzyMatch (colour -> color, randomise -> randomize)',
      'color' in w and 'randomize' in w and 'colour' not in w, w)
check('stopwords and short words go', 'the' not in w and 'and' not in w and 'its' not in w, w)

print('2. a doc splits into head and body; code and link targets never count')
doc = """---
package: Demo
summary: 'Shapes channels with a curve.'
features:
  - name: Snap Input
    anchor: snap-input
---

## Lag and smoothing

Some prose about **timecode** and a [link text](/docs/elsewhere-target/).
`inlinecodeword` and

```python
fencedcodeword = 1
```

<span class="htmltagword">visible</span> https://example.com/urlword
"""
head, body = si.DocTiers(doc)
check('the summary, feature names, ## headings and **bold** go to the head',
      all(x in head for x in ('shapes', 'curve', 'snap', 'input', 'lag', 'smoothing', 'timecode')), head)
check('prose goes to the body', 'prose' in body and 'visible' in body, body)
check('link TEXT counts, its target does not', 'link' in body and 'elsewhere' not in body, body)
check('inline and fenced code, tags and URLs are dropped',
      not any(x in head + body for x in ('inlinecodeword', 'fencedcodeword', 'htmltagword', 'urlword')),
      body)

print('3. the real docs index, against the committed manifest')
rows = manifest_rows()
idx = si.BuildIndex(rows, DOCS)
names = {r['name'] for r in rows}
docs = {f[:-3] for f in os.listdir(DOCS) if f.endswith('.md')}
check('every manifest row with a doc gets an entry', set(idx) == names & docs,
      sorted((names & docs) - set(idx)))
check('the index is deterministic', si.BuildIndex(rows, DOCS) == idx)
check('each tier is sorted, single-spaced, each word once',
      all(v[t].split() == sorted(set(v[t].split())) and '  ' not in v[t]
          for v in idx.values() for t in ('head', 'body')))
check('a word is in the head or the body, never both',
      all(not (set(v['head'].split()) & set(v['body'].split())) for v in idx.values()))
by = {r['name']: r for r in rows}
check('words the card already answers to are left out (ChopBank tags: midi, lag)',
      not ({'midi', 'lag', 'faders', 'chopbank'} & set((idx['ChopBank']['head'] + ' '
                                                       + idx['ChopBank']['body']).split())),
      idx['ChopBank'])
check('a docs-only word is indexed: "undo" for BorderlessTD, nowhere on its card',
      'undo' in (idx['FNS_BorderlessTD']['head'] + ' ' + idx['FNS_BorderlessTD']['body']).split()
      and 'undo' not in (by['FNS_BorderlessTD']['description'] + by['FNS_BorderlessTD']['title']).lower(),
      idx['FNS_BorderlessTD'])
all_words = set(' '.join(v['head'] + ' ' + v['body'] for v in idx.values()).split())
check('corpus-common words are dropped (touchdesigner, parameter, operator)',
      not ({'touchdesigner', 'parameter', 'operator', 'network'} & all_words))
raw, gz = si.Sizes(idx)
print('  ....  index size: %d bytes raw, %d gzipped (%d rows)' % (raw, gz, len(idx)))
check('the index fits its budget (%d raw, %d gzipped)' % (BUDGET_RAW, BUDGET_GZIP),
      raw <= BUDGET_RAW and gz <= BUDGET_GZIP, (raw, gz))
sub = si.BuildIndex([r for r in rows if r['name'] == 'ChopBank'], DOCS)
check('indexing one row gives the same words as indexing all (corpus-wide cut)',
      sub['ChopBank'] == idx['ChopBank'])

print('4. Build() and the site carry it')
bm = io.open(BM, encoding='utf-8').read()
check('Build() loads search_index.py by path (it runs exec\'d inside TD)',
      "spec_from_file_location(" in bm and "'search_index.py'" in bm)
check('Build() attaches `search` presence-style', re.search(
    r"index = _searchIndex\(\)\.BuildIndex\(packages, _repo\(PKG_DIR, 'docs'\)\)", bm)
    and "entry['search'] = words" in bm and "if words and (words['head'] or words['body'])" in bm)
check('Build() reports the index size', "'search_bytes'" in bm)
check('a preview row carries no `search` (the manifest promises a name and one line)',
      re.search(r"if entry\.get\('preview'\):\s*\n\s*continue\s*\n\s*if words and", bm) is not None)
site = io.open(SITE, encoding='utf-8').read()
check('the site back-fills `search` from the repo manifest into /get/',
      'if (repoSearch[pkg.name]) pkg.search = repoSearch[pkg.name];' in site)
check('search_index.py imports nothing from TouchDesigner',
      not re.search(r'^\s*(import td|from td|op\(|parent\()',
                    io.open(os.path.join(PKG, 'search_index.py'), encoding='utf-8').read(), re.M))

print()
if FAILS:
    print('FAILED: %d check(s)' % len(FAILS))
    raise SystemExit(1)
print('all search index checks pass')
