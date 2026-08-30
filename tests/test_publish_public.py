"""Offline test of the public-mirror filter.

The filter's whole claim is that it is DERIVED, not hand-kept: gate a
tool in catalog.json tomorrow and its paths stop publishing with no code
edit. That claim is worth exactly as much as a test that gates a
different package and watches it drop out -- so that is the central case
here, alongside the two rules that protect the mirror (every .toe
withheld, the declared design docs withheld) and the sweep that refuses
a run when a gated tool's files appear somewhere the derivation cannot
see.

    python tests/test_publish_public.py
"""
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


def load():
    path = os.path.join(_ROOT, 'scripts', 'publish_public.py')
    spec = importlib.util.spec_from_file_location('publish_public', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pp = load()
tmp = tempfile.mkdtemp(prefix='fns_pubtest_')

print('1. gated set comes from catalog.json, nowhere else')
real = pp.GatedPackages()
check('the real catalog reports FNS_TimelineTools gated',
      'FNS_TimelineTools' in real, real)
check('a free package is not in it', 'FNS_TimelineRegistry' not in real, real)

print('2. .toe files are withheld, whatever else is true')
for toe in ('FunctionStore_tools_2025_DEV.toe', 'FNS_TDDefault_2023.toe',
            'sub/dir/Anything.TOE'):
    check('withheld: %s' % toe, pp.Rule(toe, real) == 'toe')
check('a .tox is not caught by the toe rule',
      pp.Rule('modules/suspects/FNSTools/ColorUI.tox', real) is None)

print('3. the gated package\'s own paths are withheld by derivation')
for path in ('FNSTools/FNS_TimelineTools/TimelineToolsExt.py',
             'FNSTools/FNS_TimelineTools/FNS_Waveform/WaveformExt.py',
             'modules/suspects/FNSTools/FNS_TimelineTools.tox',
             'modules/suspects/FNSTools/FNS_TimelineTools/FNS_Markers.tox'):
    check('withheld: %s' % path,
          pp.Rule(path, real) == 'gated:FNS_TimelineTools')

print('4. mentioning a gated tool is not being one -- these still publish')
for path in ('packaging/catalog.json',
             'packaging/docs/FNS_TimelineTools.md',
             'docs/GatedDeliveryResearch.md',
             'FNSTools/FNS_TimelineRegistry/TimelineRegistryExt.py'):
    check('published: %s' % path, pp.Rule(path, real) is None)

print('5. THE claim: gate another package, its paths drop out, no code edit')
cat_src = os.path.join(_ROOT, 'packaging', 'catalog.json')
cat_tmp = os.path.join(tmp, 'catalog.json')
cat = json.load(io.open(cat_src, encoding='utf-8'))
cat['packages']['ColorUI']['access'] = '77771'
io.open(cat_tmp, 'w', encoding='utf-8').write(json.dumps(cat))
pp.CATALOG = cat_tmp
gated2 = pp.GatedPackages()
check('ColorUI now reads as gated', 'ColorUI' in gated2, gated2)
check('its source is withheld',
      pp.Rule('FNSTools/ColorUI/ColorUIExt.py', gated2) == 'gated:ColorUI')
check('its tox is withheld',
      pp.Rule('modules/suspects/FNSTools/ColorUI.tox', gated2)
      == 'gated:ColorUI')
check('its user-facing doc still publishes',
      pp.Rule('packaging/docs/ColorUI.md', gated2) is None)
check('the previously gated package is unaffected',
      pp.Rule('FNSTools/FNS_TimelineTools/parexec.py', gated2)
      == 'gated:FNS_TimelineTools')
pp.CATALOG = cat_src

print('6. declared design docs are withheld (derivation cannot see them)')
for path in pp.DECLARED_PRIVATE:
    check('withheld: %s' % path, pp.Rule(path, real) == 'declared')

print('7. the sweep refuses a gated tool\'s file the derivation would miss')
stray = 'scripts/TimelineTools_helper.py'
hits = pp._unclassified([stray, 'packaging/catalog.json'], real)
check('the stray path is flagged', [h[0] for h in hits] == [stray], hits)
clean = pp._unclassified(
    ['packaging/docs/FNS_TimelineTools.md', 'docs/README.md'], real)
check('an allowed mention is not flagged', clean == [], clean)

print('8. sub-component names count as the tool -- they ARE its internals')
toks = pp._tokens('FNS_TimelineTools')
for t in ('FNS_TimelineTools', 'TimelineTools', 'FNS_Waveform', 'Waveform',
          'FNS_Markers', 'Markers'):
    check('token derived: %s' % t, t in toks, toks)

print('9. the sweep is case-insensitive -- a lowercase dir is still the tool')
low = pp._unclassified(['tests/fixtures/markers/resolve_markers.edl'], real)
check('lowercase path matches a CamelCase token', len(low) == 1, low)

print('10. fail closed: a tool in development, not yet in the catalog')
for path in ('FNSTools/FNS_SecretNewTool/SecretExt.py',
             'FNSTools/FNS_SecretNewTool/sub/parexec.py'):
    check('withheld: %s' % path,
          pp.Rule(path, real) == 'undeclared:FNS_SecretNewTool',
          pp.Rule(path, real))
check('a catalogued free package still publishes',
      pp.Rule('FNSTools/ColorUI/ColorUIExt.py', real) is None)
check('a merged sub-component is not mistaken for a package',
      pp.Rule('modules/suspects/FNSTools/QuickExt/ExtQuickExt.py', real)
      is None)
check('a grandfathered legacy name still publishes',
      pp.Rule('modules/suspects/FNSTools/PaneTypeRegistry.tox', real) is None)

print('11. the real tree publishes with nothing unclassified')
plan = pp.Plan()
check('no unclassified paths in HEAD', plan['unclassified'] == [],
      plan['unclassified'])
check('no .toe survives into the published set',
      not [p for p in plan['published'] if p.lower().endswith('.toe')])
check('no gated path survives into the published set',
      not [p for p in plan['published'] if 'FNS_TimelineTools' in p
           and not pp._nameAllowed(p, 'FNS_TimelineTools')])
check('the mirror is not empty', len(plan['published']) > 400,
      len(plan['published']))

print('12. the root-tox embedding guard')
# The path rules cannot withhold modules/suspects/FNSTools.tox, and it
# EMBEDS every child with enableexternaltox off -- so a gated package in
# that state must refuse the whole run.
emb, unk = pp.EmbeddedGated()
check('the real state is publishable (gated packages externally carried)',
      emb == [] and unk == [], (emb, unk))
_man = json.load(io.open(os.path.join(_ROOT, 'packaging', 'manifest.json'),
                         encoding='utf-8'))
_root_carried = [p['name'] for p in _man['packages']
                 if p.get('tox_carrier') == 'root']
_orig_gated = pp.GatedPackages
if _root_carried:
    pp.GatedPackages = lambda: [_root_carried[0]]
    emb2, _ = pp.EmbeddedGated()
    check('gating a root-carried package is caught',
          emb2 == [_root_carried[0]], emb2)
else:
    print('  SKIP  no root-carried package in the manifest to simulate with')
pp.GatedPackages = lambda: ['NotInTheManifest']
_, unk2 = pp.EmbeddedGated()
check('a gated package the manifest does not know is caught (fail closed)',
      unk2 == ['NotInTheManifest'], unk2)
# savebackup (Save Backup of External, TD default ON) embeds a full
# backup on every parent save even with the external binding intact --
# a gated package carrying that flag must refuse too
tmp2 = tempfile.mkdtemp(prefix='fns_pub_sb_')
os.makedirs(os.path.join(tmp2, 'packaging'))
with io.open(os.path.join(tmp2, 'packaging', 'manifest.json'), 'w',
             encoding='utf-8') as f:
    json.dump({'packages': [
        {'name': 'FakeGated', 'tox_carrier': 'own', 'save_backup': True},
        {'name': 'FakeClean', 'tox_carrier': 'own'}]}, f)
_orig_repo = pp.REPO
pp.REPO = tmp2
pp.GatedPackages = lambda: ['FakeGated', 'FakeClean']
emb3, unk3 = pp.EmbeddedGated()
check('a backup-embedding gated package is caught',
      emb3 == ['FakeGated'] and unk3 == [], (emb3, unk3))
pp.REPO = _orig_repo
pp.GatedPackages = _orig_gated
shutil.rmtree(tmp2, ignore_errors=True)
check('release exports are withheld (the 9MB root embeds the gated tool)',
      pp.Rule('modules/release/FNSTools.tox', real) == 'declared'
      and pp.Rule('modules/release/AltSelect.tox', real) == 'declared')
# ... and the flag flips back ON for the USER: a bound install re-enables
# savebackup so their .toe self-heals if the bound file vanishes -- there
# the user owns both files and nothing is being smuggled anywhere
_inst = io.open(os.path.join(_ROOT, 'packaging', 'InstallerExt.py'),
                encoding='utf-8').read()
check('the installer re-enables savebackup on bound installs',
      "getattr(comp.par, 'savebackup', None)" in _inst
      and _inst.find('savebackup') > _inst.find('comp.par.enableexternaltox = True'))

shutil.rmtree(tmp, ignore_errors=True)
print()
if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all checks passed')
