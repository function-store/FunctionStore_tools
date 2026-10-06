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
      pp.Rule('modules/suspects/FNSTools/FNS_ColorUI.tox', real) is None)

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
cat['packages']['FNS_ColorUI']['access'] = '77771'
io.open(cat_tmp, 'w', encoding='utf-8').write(json.dumps(cat))
pp.CATALOG = cat_tmp
gated2 = pp.GatedPackages()
check('FNS_ColorUI now reads as gated', 'FNS_ColorUI' in gated2, gated2)
check('its source is withheld',
      pp.Rule('FNSTools/FNS_ColorUI/ColorUIExt.py', gated2) == 'gated:FNS_ColorUI')
check('its tox is withheld',
      pp.Rule('modules/suspects/FNSTools/FNS_ColorUI.tox', gated2)
      == 'gated:FNS_ColorUI')
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
# Names prefix each other: ColorGenPro's own page is not ColorGen's file,
# but a page named after no package still reads as one.
pre = pp._unclassified(['packaging/docs/ColorGenPro.md'], ['ColorGen'])
check('a prefixed package\'s own doc page is not flagged', pre == [], pre)
stray = pp._unclassified(['packaging/docs/ColorGenExtra.md'], ['ColorGen'])
check('a doc page named after no package is still flagged', len(stray) == 1, stray)

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
      pp.Rule('FNSTools/FNS_ColorUI/ColorUIExt.py', real) is None)
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
      and pp.Rule('modules/release/FNS_AltSelect.tox', real) == 'declared')
# briefs/ is gitignored, so a tracked brief is always an accident or a
# force-added hand-off; either way it is a private working note
check('a tracked brief is withheld (force-added hand-offs never publish)',
      pp.Rule('briefs/release-handoff-2026-10-05.md', real) == 'declared'
      and pp.Rule('briefs/picker-search-compact.md', real) == 'declared')
# ... and the flag flips back ON for the USER: a bound install re-enables
# savebackup so their .toe self-heals if the bound file vanishes -- there
# the user owns both files and nothing is being smuggled anywhere
_inst = io.open(os.path.join(_ROOT, 'packaging', 'InstallerExt.py'),
                encoding='utf-8').read()
check('the installer re-enables savebackup on bound installs',
      "getattr(comp.par, 'savebackup', None)" in _inst
      and _inst.find('savebackup') > _inst.find('comp.par.enableexternaltox = True'))

print('13. a package authored OUTSIDE FNSTools/ -- the root-resident shape')
# PreviewPanel25 and FNS_CMS are authored this way, and `placement` makes
# installing outside the toolkit a supported request, so root-resident is
# a real layout rather than a hypothetical. Before this arm existed the
# path rules knew only the FNSTools/ shape: a gated package here was
# caught solely by the name sweep, which REFUSES the whole publish instead
# of withholding one file, and an UNCLASSIFIED one was seen by nothing at
# all -- which is how PreviewPanel25 published by accident.
for path in ('modules/suspects/FNS_Remote.tox',
             'modules/suspects/FNS_Remote/ui.tox',
             'FNS_Remote/FNSRemoteExt.py'):
    check('root-resident gated path withheld: %s' % path,
          pp.Rule(path, real) == 'gated:FNS_Remote',
          pp.Rule(path, real))
check('and the toolkit shape still resolves to the same rule',
      pp.Rule('modules/suspects/FNSTools/FNS_Remote.tox', real)
      == 'gated:FNS_Remote')

print('14. fail closed at root too: unclassified means withheld')
check('an uncatalogued root suspect is withheld, not published',
      pp.Rule('modules/suspects/FNS_BrandNew.tox', real)
      == 'undeclared:FNS_BrandNew',
      pp.Rule('modules/suspects/FNS_BrandNew.tox', real))
check('_packageish sees the root shape',
      pp._packageish('modules/suspects/FNS_BrandNew.tox') == 'FNS_BrandNew')
check('a FNSTools sub-component is still NOT a package',
      pp._packageish('modules/suspects/FNSTools/NoSuchSub/x.py') is None)

print('15. the fix changed no published byte -- root scaffolding still ships')
# Without these, the root arm would newly withhold 66 files the mirror
# already carries. A safety fix that silently removes files from the
# public repo is a product change wearing a safety fix's clothes.
for name in ('FNSTools', 'FNS_CMS', 'FunctionStore_tools_2023',
             'project1', 'private_investigator1_withmyhacks'):
    check('grandfathered root suspect still publishes: %s' % name,
          pp.Rule('modules/suspects/%s.tox' % name, real) is None,
          pp.Rule('modules/suspects/%s.tox' % name, real))
check('PreviewPanel25 stays withheld by its explicit declaration',
      pp.Rule('modules/suspects/PreviewPanel25.tox', real) == 'declared')

print('16. --only website: the site inputs publish, nothing else is touched')
scope = pp.ONLY['website']
splan = pp.Plan('HEAD', scope)
spub = set(splan['published'])
check('the landing page is in', 'website/index.html' in spub)
check('a gated tool doc page is in (a doc is not the tool)',
      'packaging/docs/FNS_TimelineTools.md' in spub)
check('catalog and manifest are in',
      {'packaging/catalog.json', 'packaging/manifest.json'} <= spub)
check('nothing under modules/ or FNSTools/ is in',
      not [p for p in spub if p.startswith(('modules/', 'FNSTools/'))])
check('the scope carries no tox or toe, so the embedding guard may stand down',
      not pp._scopeCarriesTox('HEAD', scope))
check('a .toe under website/ would still be withheld by rule',
      pp.Rule('website/scratch.toe', real) == 'toe')
# Diff removes only inside the scope: a mirror file outside it is not "removed"
_real_shas = pp._shas
WANT = {'website/index.html': 'a'}
HAVE = {'website/index.html': 'b', 'website/stale.html': 'c',
        'modules/suspects/X.tox': 'd'}
pp._shas = lambda args, cwd, idx: WANT if args[0] == 'ls-tree' else HAVE
d = pp.Diff({'rev': 'HEAD', 'published': ['website/index.html'], 'scope': scope}, tmp)
pp._shas = _real_shas
check('a stale file inside the scope is removed',
      d['removed'] == ['website/stale.html'], d)
check('a changed file inside the scope is changed',
      d['changed'] == ['website/index.html'], d)

print('16. retired names are grandfathered, but never a gated one')
# RETIRED_IN_MIRROR lets pre-rename files sit in the mirror unclassified so
# a scoped publish is possible at all. That is a name-based allow, so the
# day a gated tool takes one of those names its bytes would publish. The
# guard has to run, not merely be commented.
check('every retired name is free today',
      not (set(pp.RETIRED_IN_MIRROR) & set(real)),
      sorted(set(pp.RETIRED_IN_MIRROR) & set(real)))
check('retired names are reachable through GRANDFATHERED',
      all(n in pp.GRANDFATHERED for n in pp.RETIRED_IN_MIRROR))
_clashed = False
try:
    pp._assertRetiredNotGated(['FNS_Remote', pp.RETIRED_IN_MIRROR[0]])
except SystemExit:
    _clashed = True
check('a gated package sharing a retired name REFUSES the publish', _clashed)
check('and the real catalog does not clash',
      pp._assertRetiredNotGated(real) is None)
# The reason the list exists: an old free path must stop failing closed.
check('a retired package path publishes instead of reading undeclared',
      pp.Rule('modules/suspects/FNSTools/AltSelect.tox', real) is None,
      pp.Rule('modules/suspects/FNSTools/AltSelect.tox', real))
# ...but a name nobody has classified still fails closed.
check('an unknown package name still fails closed',
      pp.Rule('modules/suspects/FNSTools/FNS_NotAThing.tox', real)
      == 'undeclared:FNS_NotAThing')

shutil.rmtree(tmp, ignore_errors=True)
print()
if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all checks passed')
