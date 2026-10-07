"""`nopick` -- a package that is only ever installed by an explicit pick.

Owner, 2026-09-23, for a hardware-specific MIDI controller integration
(free, optional, root-placed, foreign): it "should not be selected only
explicitly (not even select all)". A `nopick: true` package is still a real
package -- a normal card in the picker and on the site, installable and
updatable -- but every BULK selection leaves it out: Select all, the
Everything preset, Recommended (the manifest's `starter`), the curated
bundles (`presets`) and the guided-setup questionnaire. Lists that are the
reader's own ticks (installed, last setup, wanted, stored picks) keep it:
nothing bulk can put it there, and nothing removes a tick the user made.

Modelled on the presence-style keys `minor` and `companion`. The contract
crosses the catalog, the manifest build, both picker shells and the CMS;
this pins each side.

    python tests/test_nopick.py
"""
import io
import json
import os
import re
import tempfile
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(_ROOT, 'packaging')
CAT = os.path.join(PKG, 'catalog.json')
BM = os.path.join(PKG, 'build_manifest.py')
SHELLS = [os.path.join(PKG, 'configurator', 'index.html'),
          os.path.join(PKG, 'configurator', 'configurator-standalone.html')]
CREATING = os.path.join(PKG, 'CREATING.md')
CMS_MJS = os.path.join(_ROOT, 'website', 'tools', 'cms.mjs')
CMS_HTML = os.path.join(_ROOT, 'website', 'tools', 'cms.html')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


def read(p):
    return io.open(p, encoding='utf-8').read()


def load_build_manifest():
    mod = types.ModuleType('bm_nopick')
    mod.__dict__.update(project=types.SimpleNamespace(folder=_ROOT, name='t'),
                        app=types.SimpleNamespace(build='2025.33070'),
                        op=lambda *a, **k: None, debug=lambda *a, **k: None)
    exec(compile(read(BM), BM, 'exec'), mod.__dict__)
    return mod


cat = json.load(io.open(CAT, encoding='utf-8'))
bm_src = read(BM)
bm = load_build_manifest()

print('1. catalog validation: true or absent, never with recommended')
bad = {n: e['nopick'] for n, e in cat['packages'].items()
       if 'nopick' in e and e['nopick'] is not True}
check('every shipped nopick is the boolean true', not bad, bad)
live = {n for n, e in cat['packages'].items() if 'source' not in e}
check('the shipped catalog has no nopick problems',
      not [p for p in bm.CatalogProblems(cat, live) if 'nopick' in p])
p = bm.CatalogProblems({'packages': {
    'Ok': {'category': 'X', 'nopick': True},
    'False': {'category': 'X', 'nopick': False},
    'Str': {'category': 'X', 'nopick': 'true'},
    'One': {'category': 'X', 'nopick': 1},
    'Rec': {'category': 'X', 'nopick': True, 'recommended': True},
}}, {'Ok', 'False', 'Str', 'One', 'Rec'})
check('nopick: true alone is accepted', not any(x.startswith('Ok:') for x in p), p)
check('nopick: false is refused (presence-style)', any(x.startswith('False:') for x in p), p)
check('a string "true" is refused', any(x.startswith('Str:') for x in p), p)
check('the integer 1 is refused', any(x.startswith('One:') for x in p), p)
check('nopick together with recommended is refused',
      any(x.startswith('Rec:') and 'recommended' in x for x in p), p)

print('2. manifest projection: presence-style, only true is written')
check('the live projection copies only the boolean true',
      "if meta.get('nopick') is True:\n            entry['nopick'] = True" in bm_src)
check('both projections (live and foreign) carry it',
      bm_src.count("entry['nopick'] = True") == 2)
check('no projection ever writes false',
      "entry['nopick'] = False" not in bm_src)
tmp = tempfile.mkdtemp(prefix='fns_nopick_')
src = {'manifest': 'https://example.invalid/m.json'}
rows, _ = bm.ForeignPackages({'packages': {
    'Hw': {'category': 'X', 'source': src, 'nopick': True},
    'Plain': {'category': 'X', 'source': src},
    'Junk': {'category': 'X', 'source': src, 'nopick': 'yes'},
}}, lock={}, dist_dir=tmp)
by = {r['name']: r for r in rows}
check('a foreign nopick row carries nopick: true', by['Hw'].get('nopick') is True, by['Hw'])
check('an unflagged row has no nopick key (byte-identical)', 'nopick' not in by['Plain'])
check('a non-boolean value never reaches the manifest', 'nopick' not in by['Junk'])
check('the starter set leaves nopick packages out',
      re.search(r"'starter': \[p\['name'\] for p in packages\s*\n\s*"
                r"if p\['kind'\] == 'tool' and not p\.get\('nopick'\)", bm_src) is not None)
bundles, bprob = bm._presets(
    {'presets': [{'name': 'Mix', 'packages': ['A', 'Hw']},
                 {'name': 'OnlyHw', 'packages': ['Hw']}]},
    [{'name': 'A', 'kind': 'tool'}, {'name': 'Hw', 'kind': 'tool', 'nopick': True}])
check('a bundle drops a nopick package', bundles == [{'name': 'Mix', 'blurb': '', 'packages': ['A']}],
      bundles)
check('and reports it', any('nopick' in x and 'Hw' in x for x in bprob), bprob)
check('a bundle emptied by it is dropped whole', not any(b['name'] == 'OnlyHw' for b in bundles))

print('3. the picker: every bulk selection draws from bulkPickable()')
for path in SHELLS:
    s = read(path).replace('\r\n', '\n')
    tag = os.path.basename(path)
    check('%s: bulkPickable is pickable minus nopick' % tag,
          'function bulkPickable(p) { return pickable(p) && !p.nopick; }' in s
          and 'var bulkTools = tools.filter(bulkPickable);' in s)
    check('%s: the tool list still shows nopick cards (pickable, not bulk)' % tag,
          'var tools = M.packages.filter(pickable);' in s)
    # Select all acts on what the list SHOWS (the 2026-09-24 picker rehaul:
    # narrowed to the free tools it ticks those), but still only ever
    # draws from bulkTools
    check('%s: Select all ticks only bulkTools' % tag,
          re.search(r"getElementById\('all'\)\.addEventListener\('click', function \(\) \{\s*\n"
                    r"(?:\s*//[^\n]*\n)*"
                    r"(?:\s*var inView = \{\};\s*\n\s*shownTools\.forEach\([^\n]*\n\s*)?"
                    r"\s*bulkTools(?:\.filter\(function \(p\) \{ return inView\[p\.name\]; \}\)\s*)?"
                    r"\.forEach\(function \(p\) \{ picked\.add\(p\.name\);", s)
          is not None)
    check('%s: the Everything preset chooses bulkTools' % tag,
          re.search(r"getElementById\('pre-all'\)\.onclick = function \(\) \{\s*\n"
                    r"\s*choose\(bulkTools\.map\(", s) is not None
          and 'var allReady = autoPick(bulkTools.map(' in s)
    check('%s: the starter set filters through bulkPickable' % tag,
          re.search(r"var starter = \(M\.starter \|\| \[\]\)\.filter\(function \(n\) \{\s*\n"
                    r"\s*return bulkPickable\(byName\[n\]\);", s) is not None)
    check('%s: bundles filter through bulkPickable' % tag,
          re.search(r"packages: \(\(b && b\.packages\) \|\| \[\]\)\.filter\(function \(n\) \{\s*\n"
                    r"\s*return bulkPickable\(byName\[n\]\);", s) is not None)
    check('%s: the questionnaire scores bulkTools only' % tag,
          'quizScore(quizAnswers, quiz, bulkTools)' in s
          and 'quizScore(quizAnswers, quiz, tools)' not in s)
    check('%s: no bulk path still walks the full tool list' % tag,
          'tools.forEach(function (p) { picked.add(p.name); })' not in s.replace('bulkTools.forEach', '')
          and 'choose(tools.map(' not in s)
    check('%s: own-tick lists (installed, last, wanted) keep pickable()' % tag,
          re.search(r"var installedNow = \(window\.FNS_INSTALLED \|\| \[\]\)\.filter\(function \(n\) \{\s*\n"
                    r"\s*return pickable\(byName\[n\]\);", s) is not None
          and re.search(r"var lastNames = last \? last\.packages\.filter\(function \(n\) \{\s*\n"
                        r"\s*return pickable\(byName\[n\]\);", s) is not None)

print('4. documented and authorable')
check('catalog _comment documents nopick once',
      sum('`nopick: true`' in c for c in cat['_comment']) == 1)
check('CREATING.md documents it beside placement',
      '**`nopick`**' in read(CREATING)
      and read(CREATING).index('**`placement`**') < read(CREATING).index('**`nopick`**'))
mjs = read(CMS_MJS)
check('the CMS server exposes and stores it presence-style',
      "nopick: cat.packages[name].nopick === true" in mjs
      and re.search(r"if \(body\.nopick\) entry\.nopick = true;\s*\n\s*else delete entry\.nopick;",
                    mjs) is not None)
check('the CMS server refuses it with recommended',
      'if (entry.nopick && entry.recommended)' in mjs)
html = read(CMS_HTML)
check('the CMS editor offers the checkbox and saves it',
      'id="nopick"' in html and 'nopick: !!draft.nopick' in html)

print()
if FAILS:
    print('FAILED: %d check(s)' % len(FAILS))
    raise SystemExit(1)
print('all nopick checks pass')
