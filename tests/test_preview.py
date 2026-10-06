"""Preview packages: shipped for the owner's testing, hidden from everyone else.

docs/PreviewPackages.md. Catalog `preview: true` gates the package to the
pseudo tier `preview`, which the Worker grants the creator account alone
(worker/test/gate.test.mjs pins that half). The catalog `access` keeps the
tier it will ship at. The picker, the site, the questionnaire, the bundles
and the new-tools notice leave it out for everyone not entitled to it.

    python tests/test_preview.py
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []


def check(label, ok, detail=''):
    print(('  PASS  ' if ok else '  FAIL  ') + label + ('' if ok else '   ' + str(detail)[:200]))
    if not ok:
        FAILS.append(label)


def read(*parts):
    return io.open(os.path.join(ROOT, *parts), encoding='utf-8').read()


# build_manifest outside TD, the way test_placeonce does
bm = types.ModuleType('build_manifest')
bm.__file__ = os.path.join(ROOT, 'packaging', 'build_manifest.py')
for name in ('op', 'project', 'debug', 'ui', 'app', 'mod', 'tdu', 'me', 'parent', 'ParMode',
             'textTOP', 'tableDAT', 'baseCOMP', 'COMP', 'OP', 'DAT'):
    setattr(bm, name, None)
sys.modules['build_manifest'] = bm
exec(compile(read('packaging', 'build_manifest.py'), bm.__file__, 'exec'), bm.__dict__)

print('1. the catalog flag')


def problems(meta):
    cat = {'categories': ['Visual'], 'packages': {'X': dict({'category': 'Visual', 'description': 'x'}, **meta)}}
    try:
        return [p for p in bm.CatalogProblems(cat) if 'preview' in p]
    except TypeError:
        return [p for p in bm.CatalogProblems(cat, None) if 'preview' in p]


check('true is accepted', problems({'preview': True}) == [])
check('anything else is refused', len(problems({'preview': 'yes'})) == 1)
check('a preview may keep Recommended (it overrides it)', problems({'preview': True, 'recommended': True}) == [])

print('2. the manifest')
check('a preview ships at the preview tier', bm.EffectiveAccess({'preview': True, 'access': '8323905'}) == 'preview')
check('otherwise the catalog access', bm.EffectiveAccess({'access': '8323905'}) == '8323905'
      and bm.EffectiveAccess({}) == 'free')
src = read('packaging', 'build_manifest.py')
check('both entries (live and foreign) use it', src.count("'access': EffectiveAccess(meta),") == 2)
check('projected twice, only as true', src.count("entry['preview'] = True") == 2)
check('a variant build of a preview is preview too', "PREVIEW_TIER if meta.get('preview') is True" in src)
check('never in the Recommended starter set', "and not p.get('preview')" in src)
bundles, bprob = bm._presets({'presets': [{'name': 'Mix', 'packages': ['A', 'W']}]},
                             [{'name': 'A', 'kind': 'tool'}, {'name': 'W', 'kind': 'tool', 'preview': True}])
check('a bundle drops a preview package and says so',
      bundles == [{'name': 'Mix', 'blurb': '', 'packages': ['A']}] and any('preview' in p for p in bprob), (bundles, bprob))

print('3. gate_package: preview and release keep the two files in step')
d = tempfile.mkdtemp()
shutil.copy(os.path.join(ROOT, 'packaging', 'catalog.json'), d + '/catalog.json')
shutil.copy(os.path.join(ROOT, 'worker', 'wrangler.toml'), d + '/wrangler.toml')
spec = importlib.util.spec_from_file_location('gp', os.path.join(ROOT, 'packaging', 'gate_package.py'))
gp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gp)
gp.CATALOG, gp.WRANGLER = d + '/catalog.json', d + '/wrangler.toml'


def grants(n):
    _, t, _, _, _ = gp._maps()
    return sorted(k for k, v in t.items() if n in v)


cat0 = json.load(io.open(d + '/catalog.json', encoding='utf-8'))
# packages that are not previews already: the owner flags real ones in the catalog
paid = next(n for n, m in cat0['packages'].items() if str(m.get('access', '')).isdigit()
            and not m.get('recommended') and not m.get('preview'))
free = next(n for n, m in cat0['packages'].items() if not m.get('access') and not m.get('recommended')
            and m.get('category') != 'Core' and not m.get('preview'))
before = {n: grants(n) for n in (paid, free)}
with contextlib.redirect_stdout(io.StringIO()):
    gp.Preview(paid, True)
    gp.Preview(free, True)
cat1 = json.load(io.open(d + '/catalog.json', encoding='utf-8'))
check('a preview is granted to the preview tier alone', grants(paid) == ['preview'] and grants(free) == ['preview'],
      (grants(paid), grants(free)))
check('its access is kept for the release', cat1['packages'][paid].get('access') == cat0['packages'][paid].get('access')
      and cat1['packages'][paid].get('preview') is True)
with contextlib.redirect_stdout(io.StringIO()):
    gp.Gate(paid, tier='8291595')
check('re-gating a preview records the access but grants nothing public', grants(paid) == ['preview']
      and json.load(io.open(d + '/catalog.json', encoding='utf-8'))['packages'][paid]['access'] == '8291595')
with contextlib.redirect_stdout(io.StringIO()):
    gp.Gate(paid, tier=cat0['packages'][paid]['access'])
    gp.Preview(paid, False)
    gp.Preview(free, False)
check('release restores exactly the grants it had', {n: grants(n) for n in (paid, free)} == before)
check('and clears the flag', 'preview' not in json.load(io.open(d + '/catalog.json', encoding='utf-8'))['packages'][paid])
rec = next(n for n, m in cat0['packages'].items() if m.get('recommended') and not m.get('preview'))
with contextlib.redirect_stdout(io.StringIO()):
    gp.Preview(rec, True)
cat2 = json.load(io.open(d + '/catalog.json', encoding='utf-8'))
check('a Recommended package can become a preview and keeps the flag',
      cat2['packages'][rec].get('preview') is True and cat2['packages'][rec].get('recommended') is True)

print('4. nobody else sees it')
page = read('packaging', 'configurator', 'index.html')
check('the picker drops it unless the account is entitled',
      'M.packages = M.packages.filter(function (p) { return !p.preview || entitled(p); });' in page
      and page.index('M.packages = M.packages.filter(function (p) { return !p.preview') < page.index('var tools = M.packages.filter(pickable);'))
check('the owner sees it marked', "chip('preview · only you see this', 'hint')" in page)
ins = read('packaging', 'InstallerExt.py')
check('the new-tools notice never announces or records it', "and not p.get('preview')]" in ins)
site = read('website', 'tools', 'build-site.mjs')
check('the site builds no page, card or count for it',
      "if (curated[pages[i].name].preview === true) pages.splice(i, 1);" in site)
check('and the site\'s baked manifest leaves it out', "return !(row && row.preview === true) && !pkg.preview;" in site)
check('the worker grants the preview tier to the creator only',
      "if (creator && me === creator && !tiers.includes(PREVIEW_TIER)) {" in read('worker', 'src', 'index.js'))
check('its sources are withheld from the public mirror like a gated tool',
      "or (meta or {}).get('preview') is True:" in read('scripts', 'publish_public.py'))
check('and the release\'s leak check counts it as gated',
      "or (m or {}).get('preview') is True}" in read('packaging', 'release_one.py'))

print('5. the CMS')
mjs = read('website', 'tools', 'cms.mjs')
check('the server flips it through gate_package', "[GATE_PY, name, on ? '--preview' : '--release']" in mjs
      and 'setPreview(name, body.preview);' in mjs)
check('and lets it sit beside Recommended', 'a preview cannot be Recommended' not in mjs)
html = read('website', 'tools', 'cms.html')
check('the editor offers it and saves it', 'id="preview"' in html and 'preview: !!draft.preview,' in html)
check('documented', os.path.exists(os.path.join(ROOT, 'docs', 'PreviewPackages.md'))
      and '**`preview`**' in read('packaging', 'CREATING.md'))

if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all preview checks pass')
