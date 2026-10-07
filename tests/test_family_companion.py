"""The FNS operator family appears only when a family operator is installed.

Owner decision 2026-09-17: the FNS family, its TDFam registry and the FNS
tab should not appear unless needed. FNS_OpFamily is a `companion: family`
package: the picker never offers it, the installer adds it exactly when the
selection holds a family member (a package whose manifest row has a
`family` block) and treats an installed family with no member left as an
ordinary removal candidate, and the updater keeps no family folder in a
project without the family (the family asks for a sync when it arrives).

Verified live 2026-09-17 against a manifest built from the live project:
AutoRes alone plans no family; SwitchTools plans it; the family ticked alone
plans nothing; a minimal RandomCHOP request plans it; an installed family is
removed when no member is selected and kept while one is. The static picker
showed no family card and Select all picked 53 tools without it. The
updater synced where the family is installed and skipped (no folder) where
it is not.

    python tests/test_family_companion.py
"""
import io
import json
import os
import re
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(_ROOT, 'packaging')
CAT = os.path.join(PKG, 'catalog.json')
BM = os.path.join(PKG, 'build_manifest.py')
INS = os.path.join(PKG, 'InstallerExt.py')
IDX = os.path.join(PKG, 'configurator', 'index.html')
UPD = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'FNS_Updater', 'ExtUpdater.py')
FCE = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'FNS_OpFamily', 'FamilyCommandsExt.py')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


def read(p):
    return io.open(p, encoding='utf-8').read()


cat = json.load(io.open(CAT, encoding='utf-8'))
bm_src, ins, idx, upd, fce = read(BM), read(INS), read(IDX), read(UPD), read(FCE)

print('1. the catalog and the manifest')
fam = cat['packages']['FNS_OpFamily']
check('FNS_OpFamily is a family companion', fam.get('companion') == 'family')
check('the questionnaire cannot pick it (no fits)', 'fits' not in fam)
check('it is not recommended (the starter set cannot carry it)', not fam.get('recommended'))
check('the manifest carries companion presence-style',
      "if str(meta.get('companion', '')) == 'family':\n            entry['companion'] = 'family'" in bm_src)

mod = types.ModuleType('bm')
mod.__dict__.update(project=types.SimpleNamespace(folder=_ROOT, name='t'),
                    app=types.SimpleNamespace(build='2025.33070'),
                    op=lambda *a, **k: None, debug=lambda *a, **k: None)
exec(compile(bm_src, BM, 'exec'), mod.__dict__)
live = {n for n, e in cat['packages'].items() if 'source' not in e}
check('the shipped catalog has no companion problems', not mod.CatalogProblems(cat, live))
p = mod.CatalogProblems({'packages': {
    'A': {'category': 'X', 'companion': 'launcher'},
    'B': {'category': 'X', 'companion': 'family', 'family': {'op_type': 'b'}},
}}, {'A', 'B'})
check('an unknown companion kind is refused', any(x.startswith('A:') for x in p), p)
check('a companion that is itself a member is refused', any(x.startswith('B:') for x in p), p)

print('2. the installer decides from the selection')
check('companions are dropped from what a selection asks, then added only with a member',
      re.search(r"has_member = any\(index\[n\]\.get\('family'\) for n in wanted if n in index\)\n"
                r"\s*wanted = \[n for n in wanted if n not in companions\]\n"
                r"\s*if has_member and FamilyWanted\(sel, index, companions, root_comp\):\n"
                r"\s*wanted\.extend\(companions\)", ins) is not None)
check('the rule runs before the core force and the removal candidates',
      ins.index("companions = [p['name'] for p in manifest['packages']")
      < ins.index("for c in manifest.get('core', []):")
      < ins.index("to_remove = [] if minimal else ("))

print('3. the picker never offers it')
check('one pickable() test excludes companions',
      "function pickable(p) { return !!p && p.kind === 'tool' && !p.companion; }" in idx)
check('the tool list, installed, last setup, wanted, starter, bundles and stored picks all use it',
      "var tools = M.packages.filter(pickable);" in idx
      # starter and bundles go through bulkPickable(), which is pickable()
      # minus `nopick` (tests/test_nopick.py) -- still companion-safe
      # (+1 since place-once: the placed-here list, docs/PlaceOnce.md;
      # +1 since the unseen list, docs/NewToolsAndFamilyFreshness.md)
      and idx.count('return pickable(byName[n]);') + idx.count('return bulkPickable(byName[n]);') == 8
      and 'function bulkPickable(p) { return pickable(p) && !p.nopick; }' in idx)
check('no pick list still filters on kind alone',
      "return byName[n] && byName[n].kind === 'tool';" not in idx)

print('4. no family folder without the family')
check('SyncFamilyFolder skips, creating nothing, when the family is not installed',
      re.search(r"if self\._familyOwner\(\) is None:\n\s*return \{'ok': True, 'skipped':", upd) is not None
      and (lambda s: s.index("if self._familyOwner() is None:") < s.index("os.makedirs(folder, exist_ok=True)"))(
          upd[upd.index('def SyncFamilyFolder('):]))
check('the family owner is found by shortcut',
      "reg = getattr(op, 'FAMREGISTRY', None)" in upd and "reg.GetFamilyOwner(self._FAMILY_NAME)" in upd)
check('the family asks for its folder when it initialises',
      "run('args[0]._syncOnArrival()', self, delayFrames=120, delayRef=op.TDResources)" in fce
      and "upd.SyncFamilyFolder()" in fce)

print()
if FAILS:
    print('%d check(s) failed:' % len(FAILS))
    for f in FAILS:
        print('  - ' + f)
    raise SystemExit(1)
print('all family-companion checks pass')
