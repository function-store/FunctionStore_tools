"""The install picker's search and its compact view (docs/PickerSearch.md).

Owner feedback, 2026-10-03: "there are just so many tools and features".
The picker's search was a plain substring over what a card shows; it now
ranks with a port of scripts/shared/FuzzyMatch.py over the card fields, the
CMS tags, the operator types a tool stands in for and the words of its
documentation (packaging/search_index.py), and shows one ranked list while
a query is present. A Compact toggle draws title-only tiles.

The block between the FNS:SEARCH markers is evaluated in node, straight
from both picker shells, so nothing here restates the ranking:

  1. both shells carry the same block, and it stays ES5
  2. FNSFuzzy matches FuzzyMatch.py token for token over the palette corpus
  3. the real catalog ranks the way the brief promised
  4. the page wires it: ranked list, Enter, docs hint, Compact

    python tests/test_picker_search.py
"""
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(_ROOT, 'packaging')
FIX = os.path.join(_ROOT, 'tests', 'fixtures')
SHELLS = [os.path.join(PKG, 'configurator', 'index.html'),
          os.path.join(PKG, 'configurator', 'configurator-standalone.html')]
NODE = os.environ.get('NODE', 'node')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fm = load('FuzzyMatch', os.path.join(_ROOT, 'scripts', 'shared', 'FuzzyMatch.py'))
si = load('search_index', os.path.join(PKG, 'search_index.py'))
srcs = [io.open(p, encoding='utf-8').read() for p in SHELLS]
BLOCK_RE = re.compile(r'/\* FNS:SEARCH:START.*?\*/(.*?)/\* FNS:SEARCH:END \*/', re.S)

TMP = tempfile.mkdtemp(prefix='picker_search_')


def node(harness, data):
    """Run the page's search block plus a harness; DATA is the parsed input."""
    data_path = os.path.join(TMP, 'data.json')
    with io.open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    script = os.path.join(TMP, 'run.js')
    with io.open(script, 'w', encoding='utf-8') as f:
        f.write(BLOCK + '\nvar DATA = require(%s);\n' % json.dumps(data_path) + harness)
    got = subprocess.run([NODE, script], capture_output=True, text=True, timeout=120)
    if got.returncode != 0:
        raise RuntimeError(got.stderr.strip()[:800])
    return json.loads(got.stdout)


print('1. both shells carry the same search block, and it stays ES5')
blocks = [BLOCK_RE.search(s) for s in srcs]
check('the block is present in both shells', all(blocks))
BLOCK = blocks[0].group(1) if blocks[0] else ''
check('the standalone carries the same block as index.html',
      blocks[1] is not None and blocks[1].group(1) == BLOCK)
check('no lookbehind (JavaScriptCore)', '(?<' not in BLOCK)
check('no arrow functions, let or const (the page is ES5)',
      not re.search(r'=>|\blet\s|\bconst\s', BLOCK))
check('every field weight stays under 1, so strict hits outrank fuzzy ones',
      all(float(v) < 1 for v in re.findall(r'(?:NAME|TAG|META|DESC|HEAD|BODY) = ([0-9.]+)', BLOCK))
      and len(re.findall(r'(?:NAME|TAG|META|DESC|HEAD|BODY) = ([0-9.]+)', BLOCK)) == 6)

print('2. FNSFuzzy matches scripts/shared/FuzzyMatch.py')
names = io.open(os.path.join(FIX, 'palette_names.txt'), encoding='utf-8').read().split()
cmd_rows = json.load(io.open(os.path.join(FIX, 'command_rows.json'), encoding='utf-8'))
TOKENS = ['blur', 'nosie', 'mfo', 'fbg', 'lur', 'kinnect', 'opneext', 'che', 'movie_file',
          'randomise', 'colour', 'grey', 'centre', 'noise', 'hsv', 'x', 'feedbck', 'tex3d',
          'tmln', 'kr', 'particle', 'lfo', 'Ramp', 'GLSL']


def py_token(t, n):
    m = fm.match_token(t, n)
    return None if m is None else [m[0], round(m[1], 9)]


want = [[py_token(t, n) for n in names] for t in TOKENS]
got = node("""
console.log(JSON.stringify(DATA.tokens.map(function (t) {
  return DATA.names.map(function (n) {
    var m = FNSFuzzy.matchToken(t, n);
    return m ? [m[0], Math.round(m[1] * 1e9) / 1e9] : null;
  });
})));
""", {'tokens': TOKENS, 'names': names})
diff = [(TOKENS[i], names[j], want[i][j], got[i][j])
        for i in range(len(TOKENS)) for j in range(len(names)) if want[i][j] != got[i][j]]
hits = sum(1 for r in want for x in r if x)
tiers = sorted({x[0] for r in want for x in r if x})
check('match_token agrees on %d token x name pairs (%d hits, tiers %s)'
      % (len(TOKENS) * len(names), hits, tiers), not diff, diff[:5])
check('the corpus exercises every tier', tiers == list(range(7)), tiers)

QUERIES = ['blur', 'tmln', 'save proj', 'nosie', 'open ext', 'cmd pal', 'x']
fields = [[[r['title'], 0.0, False], [r['category'] or '', 0.4, False], [r['path'], 0.7, True]]
          for r in cmd_rows]


def py_fields(q, f):
    m = fm.score_fields(q, [tuple(x) for x in f])
    return None if m is None else [round(m[0], 9), round(m[1], 9)]


want = [[py_fields(q, f) for f in fields] for q in QUERIES]
got = node("""
console.log(JSON.stringify(DATA.queries.map(function (q) {
  return DATA.fields.map(function (f) {
    var m = FNSFuzzy.scoreFields(q, f);
    return m ? [Math.round(m[0] * 1e9) / 1e9, Math.round(m[1] * 1e9) / 1e9] : null;
  });
})));
""", {'queries': QUERIES, 'fields': fields})
diff = [(QUERIES[i], cmd_rows[j]['title'], want[i][j], got[i][j])
        for i in range(len(QUERIES)) for j in range(len(fields)) if want[i][j] != got[i][j]]
check('score_fields agrees on %d query x command-row pairs' % (len(QUERIES) * len(fields)),
      not diff, diff[:5])

print('3. the real catalog ranks as promised')
# The committed manifest plus the docs index built here: the ranking claims
# hold before the next release regenerates the manifest with `search`.
manifest = json.load(io.open(os.path.join(PKG, 'manifest.json'), encoding='utf-8'))
index = si.BuildIndex(manifest['packages'], os.path.join(PKG, 'docs'))
tools = [p for p in manifest['packages'] if p.get('kind') == 'tool' and not p.get('companion')]
for p in tools:
    if p['name'] in index:
        p['search'] = index[p['name']]
labels = {k: v.get('label', k) for k, v in (manifest['toolkit'].get('surface_meta') or {}).items()}
RANK = """
function rank(rows, q) {
  var toks = FNSFuzzy.tokens(q), out = [];
  rows.forEach(function (p) {
    var h = FNSSearch.score(toks, FNSSearch.prepare(p, function (s) { return DATA.labels[s] || s; }));
    if (h) out.push({name: p.name, tier: h.tier, quality: h.quality, docs: h.docs, title: p.title});
  });
  out.sort(function (a, b) { return FNSSearch.compare(a, b) || a.title.localeCompare(b.title); });
  return out;
}
"""
TABLE = ['math chop', 'constant chop', 'midi fader', 'controller', 'hotk', 'alt',
         'feedbak', 'kinnect', 'undo', 'ui', 'ab', 'fx', 'lag', 'osc', 'midi', 'toolbar',
         'particle', 'record', 'timecode', 'gpu', 'snap', 'crossfade', 'trial']
res = node(RANK + """
var bare = DATA.tools.map(function (p) {
  var c = JSON.parse(JSON.stringify(p)); delete c.search; return c;
});
var out = {full: {}, bare: {}};
DATA.queries.forEach(function (q) { out.full[q] = rank(DATA.tools, q); out.bare[q] = rank(bare, q); });
console.log(JSON.stringify(out));
""", {'tools': tools, 'labels': labels, 'queries': TABLE})
full, bare = res['full'], res['bare']


def order(q):
    return [r['name'] for r in full[q]]


def row(q, name):
    return next((r for r in full[q] if r['name'] == name), None)


chop = next(p for p in tools if p['name'] == 'ChopBank')
check('"math chop" puts ChopBank in the top two (alternatives_for mathCHOP)',
      'ChopBank' in order('math chop')[:2], order('math chop')[:4])
check('"constant chop" puts ChopBank in the top two (alternatives_for constantCHOP)',
      'ChopBank' in order('constant chop')[:2], order('constant chop')[:4])
check('"midi fader" puts ChopBank first', order('midi fader')[:1] == ['ChopBank'], order('midi fader')[:4])
check('a CMS search_words term finds its tool ("controller" -> ChopBank first)',
      'controller' in chop['family']['search_words'] and order('controller')[:1] == ['ChopBank'],
      order('controller')[:4])
check('"hotk" puts HotkeyManager first', order('hotk')[:1] == ['FNS_HotkeyManager'], order('hotk')[:4])
check('"alt" puts AltSelect first (hotkeys are not searched)',
      order('alt')[:1] == ['FNS_AltSelect'], order('alt')[:4])
check('a one-letter typo in a 5+ letter word still finds the tool (feedbak, kinnect)',
      'FeedbackDisplace' in order('feedbak') and 'KinectSinglePlayer' in order('kinnect'),
      (order('feedbak'), order('kinnect')))
undo = row('undo', 'FNS_BorderlessTD')
check('a docs-only word finds the tool and says so ("undo" -> BorderlessTD, in docs: undo)',
      undo is not None and undo['docs'] == ['undo'], undo)
check('without the docs index that hit is gone, so the docs carried it',
      not any(r['name'] == 'FNS_BorderlessTD' for r in bare['undo']))
check('a priced product answers to "trial" and its pricing summary (TDXMap)',
      'TDXMap' in order('trial'), order('trial'))
variant = node(RANK + """
console.log(JSON.stringify(rank([{name: 'FNS_Demo', title: 'Demo', kind: 'tool',
  variants: {pro: {access: '8291595', summary: 'Adds stereo output'}}}], 'stereo')));
""", {'labels': labels})
check('a tier variant answers to its summary (synthetic row: "stereo")',
      [r['name'] for r in variant] == ['FNS_Demo'], variant)
check('a manifest without `search` still searches every other field (midi -> ChopBank)',
      [r['name'] for r in bare['midi']][:1] == ['ChopBank'], [r['name'] for r in bare['midi']][:3])
for q in ('ui', 'ab', 'fx'):
    check('a two-letter query stays small ("%s": %d of %d)' % (q, len(full[q]), len(tools)),
          len(full[q]) <= 5, order(q))
for q in ('lag', 'osc'):
    check('a three-letter query stays small ("%s": %d of %d)' % (q, len(full[q]), len(tools)),
          len(full[q]) <= 10, order(q))
check('results come out best first (tier never decreases down the list)',
      all(all(a['tier'] <= b['tier'] for a, b in zip(full[q], full[q][1:])) for q in TABLE))

# The FuzzyMatch promise: a row a token hits literally (inside a card field,
# or as the start of a docs word) never lands in the fuzzy tiers.
drift = node(RANK + """
function literal(p, tk) {
  var row = FNSSearch.prepare(p, function (s) { return DATA.labels[s] || s; });
  if (tk.length < 3) {
    return row.fields.some(function (f) { return f.ws.some(function (w) { return w.indexOf(tk) === 0; }); });
  }
  return row.fields.some(function (f) { return f.ws.join('').indexOf(tk) >= 0; })
    || !!FNSSearch.docWord(tk, row.head) || !!FNSSearch.docWord(tk, row.body);
}
var bad = [];
DATA.queries.forEach(function (q) {
  rank(DATA.tools, q).forEach(function (r) {
    var p = DATA.tools.filter(function (t) { return t.name === r.name; })[0];
    var all = FNSFuzzy.tokens(q).every(function (t) { return literal(p, FNSFuzzy.fold(t)); });
    if (all && r.tier >= FNSFuzzy.INITIALS) bad.push([q, r.name, r.tier]);
  });
});
console.log(JSON.stringify(bad));
""", {'tools': tools, 'labels': labels, 'queries': TABLE + ['chop', 'color', 'scene', 'op', 'mid']})
check('a literal hit never leaves the strict tiers', not drift, drift[:5])

print('4. the page wires it, in both shells')
for path, src in zip(SHELLS, srcs):
    tag = os.path.basename(path)
    check('%s: the old substring matcher is gone' % tag, 'shownText(' not in src)
    check('%s: a query renders ONE ranked grid, sections otherwise' % tag,
          "rg.className = 'grid ranked';" in src and "if (cat === 'Core' || q) return;" in src)
    check('%s: ranked cards carry the hit (category tag, docs line)' % tag,
          'card(p, hitOf(p, q))' in src and "ct.className = 'cattag';" in src
          and "dh.className = 'dochit';" in src)
    check('%s: Enter ticks the top hit through its own checkbox' % tag,
          "e.key === 'Enter' && t && t.id === 'q' && queryText()" in src
          and "listEl.querySelector('.grid.ranked .card input[type=checkbox]')" in src
          and 'if (top && !top.checked) top.click();' in src)
    check('%s: the category rail jumps to a hit under a search' % tag,
          "listEl.querySelectorAll('.grid.ranked .card')" in src)
    m = re.search(r'<div class="bar-row bar-filters">(.*?)</div>\s*</div>', src, re.S)
    check('%s: the Compact toggle sits in the filter bar, off by default' % tag,
          m is not None and re.search(r'<button type="button" class="tog" id="compact" aria-pressed="false"',
                                      m.group(1)) is not None)
    check('%s: Compact persists per viewer, storage wrapped' % tag,
          "var COMPACT_KEY = 'fns.compact';" in src
          and "try { localStorage.setItem(COMPACT_KEY, compactOn ? '1' : '0'); } catch (e)" in src
          and "stored(COMPACT_KEY, null) === '1'" in src)
    check('%s: Compact hides the description, byline, hints and where-chips' % tag,
          re.search(r'#list\.dense \.desc, #list\.dense \.name a\.help, #list\.dense \.chip\.where,\s*'
                    r'#list\.dense \.chip\.hint, #list\.dense \.chip\.variant,', src) is not None)
    check('%s: the description stays on the tile hover (data-tip)' % tag,
          "el.setAttribute('data-tip', (p.description || '')" in src)
    check('%s: the site keeps the baked docs index over a live manifest' % tag,
          'if (b.search) p.search = b.search;' in src)
ui_start = srcs[0].find('/* FNS:UIBASE:START')
ui_end = srcs[0].find('/* FNS:UIBASE:END */')
check('the picker-only CSS stays outside the generated UIBASE block',
      '#list.dense' not in srcs[0][ui_start:ui_end] and '.dochit' not in srcs[0][ui_start:ui_end])

shutil.rmtree(TMP, ignore_errors=True)
print()
if FAILS:
    print('FAILED: %d check(s)' % len(FAILS))
    raise SystemExit(1)
print('all picker search checks pass')
