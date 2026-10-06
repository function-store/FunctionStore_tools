"""Place once (docs/PlaceOnce.md): the catalog flag, its projection, the
installer's record and plan rules, the root's last_install filter, and the
picker page. Plain script: python tests/test_placeonce.py

The behaviour itself (ResolvePlan keeping placed tools when a selection does
not say `place`, forgetting them when it does, spawning a placed family
member, RecordInstalled growing the column) needs TouchDesigner and was run
there on 2026-09-24; this file pins the source so none of it regresses
silently.
"""
import io
import os
import re
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []


def check(label, ok, detail=''):
    print(('  PASS  ' if ok else '  FAIL  ') + label + ('' if ok else '   ' + str(detail)[:200]))
    if not ok:
        FAILS.append(label)


def read(*parts):
    return io.open(os.path.join(ROOT, *parts), encoding='utf-8').read()


# build_manifest outside TD: exec into a stub module, the way test_nopick does
bm = types.ModuleType('build_manifest')
bm.__file__ = os.path.join(ROOT, 'packaging', 'build_manifest.py')
for name in ('op', 'project', 'debug', 'ui', 'app', 'mod', 'tdu', 'me', 'parent', 'ParMode',
             'textTOP', 'tableDAT', 'baseCOMP', 'COMP', 'OP', 'DAT'):
    setattr(bm, name, None)
sys.modules['build_manifest'] = bm
exec(compile(read('packaging', 'build_manifest.py'), bm.__file__, 'exec'), bm.__dict__)

print('1. the catalog flag is presence-style')


def problems(meta):
    cat = {'categories': ['Media & Output'], 'packages': {'X': dict({'category': 'Media & Output',
                                                                       'description': 'x'}, **meta)}}
    try:
        return [p for p in bm.CatalogProblems(cat) if 'placeonce' in p]
    except TypeError:
        return [p for p in bm.CatalogProblems(cat, None) if 'placeonce' in p]


check('true is accepted', problems({'placeonce': True}) == [], problems({'placeonce': True}))
check('false is refused', len(problems({'placeonce': False})) == 1)
check('a string is refused', len(problems({'placeonce': 'yes'})) == 1)
check('placeonce with nopick is fine', problems({'placeonce': True, 'nopick': True}) == [])

print('2. projected into the manifest, only as true')
src = read('packaging', 'build_manifest.py')
check('projected twice (live and foreign)', src.count("entry['placeonce'] = True") == 2)
check('never projected as false', "entry['placeonce'] = False" not in src)

print('3. the installer record and plan')
inst = read('packaging', 'InstallerExt.py')
check("INSTALLED_COLS ends with 'remember'",
      re.search(r"INSTALLED_COLS = \['package', 'sha256', 'release', 'when', 'remember'\]", inst) is not None)
check('RecordInstalled takes remember', 'def RecordInstalled(parent_comp, name, sha256, release=\'\', remember=None)' in inst)
check('an old table grows the column', 'while t.numCols < len(INSTALLED_COLS)' in inst)
check('ResolvePlan reads `place`', "sel.get('place')" in inst and "'place' in sel" in inst)
check('a selection without `place` keeps placed tools', 'keep_placed = set() if place_said else placed_before' in inst)
check('a placed family member spawns', "if place and placement == 'none':" in inst)
check('the plan reports placing', "'placing': [s['name'] for s in steps if s['place']]" in inst)
check('record-only removals run', "plan.get('to_remove') or plan.get('to_unrecord')" in inst)
check('the picker feed separates placed tools', 'window.FNS_PLACED = %s' in inst)

print('4. last_install skips placed tools')
bi = read('packaging', 'build_installer.py')
check('the root save filters remember == "0"', 't[i, 4].val == "0"' in bi)

print('5. the picker page')
page = read('packaging', 'configurator', 'index.html')
check('reads FNS_PLACED', 'window.FNS_PLACED' in page)
check('Place for placeonce packages and family members, served only',
      'return served && !!(p && (p.placeonce || p.family))' in page)
check('the selection always says `place` when served', 'sel.place = Array.from(placing)' in page)
check('ticking a placed tool drops it from placing', 'picked.add(p.name); placing.delete(p.name);' in page)
check('the Place press does not tick the card', "e.preventDefault(); e.stopPropagation();" in page)
check('a Placeable filter beside Selected and New', 'id="placeonly"' in page
      and '>Placeable <span class="k">' in page
      and "&& (!view.once || isPlaceable(p))" in page and "po.hidden = !once;" in page)
check('placeable = placeonce, a family member, or a pane/root spawn',
      "return !!(p && (p.placeonce || p.family || p.placement === 'pane' || p.placement === 'root'));" in page)

print('6. CMS and documentation')
check('CMS checkbox', 'id="placeonce"' in read('website', 'tools', 'cms.html'))
check('CMS stores it', "typeof body.placeonce === 'boolean'" in read('website', 'tools', 'cms.mjs'))
check('CREATING.md documents it', '**`placeonce`**' in read('packaging', 'CREATING.md'))
check('the design doc exists', os.path.exists(os.path.join(ROOT, 'docs', 'PlaceOnce.md')))
import json
cat = json.loads(read('packaging', 'catalog.json'))
check('catalog comment explains it', any('placeonce' in l for l in cat['_comment']))
check('TDXMap and ParHoverMIDI_VSN1 are placeonce',
      all(cat['packages'][n].get('placeonce') is True for n in ('TDXMap', 'ParHoverMIDI_VSN1')))

if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all place-once checks pass')
