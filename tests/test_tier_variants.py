"""Tier variants (docs/TierVariants.md): one package, one build per tier.

Pins the offline half of the machinery: the catalog block and its
validation, the gate tool granting FNS_Foo.pro from its own tier, the
publisher withholding a variant master and the files only a variant
build may hold, the manifest builder's per-variant export and URL, the
staging under plus/, and the preflight checks.

    python tests/test_tier_variants.py
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(_ROOT, 'packaging')
FAILS = []
BASE, PRO, COACH = '8323905', '8291595', '9796651'


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


def read(p):
    return io.open(p, encoding='utf-8').read()


def load_build_manifest(repo):
    mod = types.ModuleType('build_manifest_under_test')
    mod.__dict__['project'] = types.SimpleNamespace(folder=repo, name='t')
    mod.__dict__['app'] = types.SimpleNamespace(build='2025.33070')
    mod.__dict__['op'] = lambda *a, **k: None
    mod.__dict__['debug'] = lambda *a, **k: None
    src = read(os.path.join(PKG, 'build_manifest.py'))
    exec(compile(src, 'build_manifest.py', 'exec'), mod.__dict__)
    return mod


print('1. the catalog block is validated')
bm = load_build_manifest(_ROOT)
good = {'packages': {'FNS_Foo': {'category': 'X', 'description': 'd', 'access': BASE,
                                 'variants': {'pro': {'access': PRO, 'summary': 'adds cues'}}}}}
check('a good variants block passes', bm.CatalogProblems(good, {'FNS_Foo'}) == [])
bad = {'packages': {
    'FNS_Foo': {'category': 'X', 'description': 'd', 'access': BASE,
                'variants': {'Pro Edition': {'access': 'Pro'}, 'plus': 'nope',
                             'coaching': {'access': COACH, 'source': 'FNS_Bar',
                                          'withhold': 'ExtPro.py'}}},
    'FNS_Bar': {'category': 'X', 'description': 'd'},
}}
p = bm.CatalogProblems(bad, {'FNS_Foo', 'FNS_Bar'})
check('a variant id must be a lowercase word', any('must be a lowercase word' in x for x in p), p)
check('a variant access must be a numeric tier id', any('numeric Patreon tier id' in x for x in p), p)
check('a variant block must be an object', any('must be an object' in x for x in p), p)
check('a variant source must not be a catalog package of its own',
      any('catalog package of its own' in x for x in p), p)
check('withhold must be a list', any('withhold must be a list' in x for x in p), p)
check('Variants() reads only well-formed blocks',
      set(bm.Variants(bad['packages']['FNS_Foo'])) == {'Pro Edition', 'coaching'})
check('VariantSources() names the second masters',
      bm.VariantSources(bad['packages']) == {'FNS_Bar'})
bm_src = read(os.path.join(PKG, 'build_manifest.py'))
check('Packages() skips a variant master (no row, no catalog entry, no doc)',
      re.search(r"sources = VariantSources\(\)\n(.*?\n)*?\s*if c\.name in sources:\n\s*continue", bm_src)
      is not None)

print('2. the manifest builder: one artifact per variant, under plus/')
check('ExportPackage takes a suffix and names the file <name><suffix>.tox',
      "def ExportPackage(comp, suffix=''):" in bm_src
      and "dest = _repo(DIST_DIR, comp.name + suffix + '.tox')" in bm_src)
check('a variant exports from its source master or from the package master',
      "src_comp = _root().op(src_name) if src_name else comp" in bm_src
      and "vart = ExportPackage(src_comp, suffix='.' + vid)" in bm_src)
check('a non-exporting build carries the variant artifact from disk or the previous manifest',
      "built = _repo(DIST_DIR, '%s.%s.tox' % (name, vid))" in bm_src
      and "elif (prev_vars.get(vid) or {}).get('artifact'):" in bm_src)
check('the variant URL sits under the plus prefix with its own key',
      "vart['url'] = '%s/%s/%s/%s.%s.tox' % (base_url.rstrip('/'), PLUS_PREFIX," in bm_src)
# 1470088d (2026-09-25) lets a preview package's row carry the preview tier
# as its access; the row still records access and summary for the picker.
check('the row records the variant' + chr(39) + 's access and summary for the picker',
      "vrow = {'access': (PREVIEW_TIER if meta.get('preview') is True" in bm_src
      and "else str(block.get('access', '') or ''))" in bm_src
      and "'summary': str(block.get('summary', '') or '')}" in bm_src)

print('3. the gate tool grants FNS_Foo.pro from its own tier')
tmp = tempfile.mkdtemp(prefix='fns_variants_')
try:
    os.makedirs(os.path.join(tmp, 'packaging'))
    os.makedirs(os.path.join(tmp, 'worker'))
    cat = json.load(io.open(os.path.join(PKG, 'catalog.json'), encoding='utf-8'))
    cat['packages']['FNS_Fake'] = {'category': 'Parameters', 'description': 'd'}
    json.dump(cat, io.open(os.path.join(tmp, 'packaging', 'catalog.json'), 'w', encoding='utf-8'), indent=1)
    shutil.copy2(os.path.join(_ROOT, 'worker', 'wrangler.toml'), os.path.join(tmp, 'worker', 'wrangler.toml'))
    # the tool resolves catalog.json and wrangler.toml relative to ITSELF,
    # so a copy inside the temp repo is what edits the temp files
    gate = os.path.join(tmp, 'packaging', 'gate_package.py')
    shutil.copy2(os.path.join(PKG, 'gate_package.py'), gate)

    def run(*args):
        return subprocess.run([sys.executable, gate] + list(args), cwd=tmp,
                              capture_output=True, text=True)

    def maps():
        src = read(os.path.join(tmp, 'worker', 'wrangler.toml'))
        m = re.search(r'^TIERS\s*=\s*"""(.*?)"""', src, re.M | re.S)
        return json.loads(m.group(1))

    def catalog():
        return json.load(io.open(os.path.join(tmp, 'packaging', 'catalog.json'), encoding='utf-8'))

    r = run('FNS_Fake', '--tier', BASE)
    check('the base gates as before', r.returncode == 0 and 'FNS_Fake' in maps()[BASE], r.stdout[-300:] + r.stderr[-300:])
    r = run('FNS_Fake', '--variant', 'pro', '--tier', PRO)
    t = maps()
    check('--variant pro --tier PRO records variants.pro.access',
          catalog()['packages']['FNS_Fake'].get('variants', {}).get('pro', {}).get('access') == PRO, r.stdout[-300:] + r.stderr[-300:])
    check('FNS_Fake.pro is granted from Pro up, never at Base',
          'FNS_Fake.pro' in t.get(PRO, []) and 'FNS_Fake.pro' in t.get(COACH, [])
          and 'FNS_Fake.pro' not in t.get(BASE, []), t)
    check('the base grant is untouched by the variant gate',
          'FNS_Fake' in t[BASE] and 'FNS_Fake' in t[PRO] and 'FNS_Fake' in t[COACH])
    r = run('FNS_Fake', '--tier', BASE)
    t = maps()
    check('regating the base re-derives the variant grants (no drift)',
          'FNS_Fake.pro' in t.get(PRO, []) and 'FNS_Fake.pro' not in t.get(BASE, []))
    r = run('FNS_Fake', '--free')
    t = maps()
    check('--free drops the package, its variants and every grant',
          all('FNS_Fake' not in v and 'FNS_Fake.pro' not in v for v in t.values())
          and 'variants' not in catalog()['packages']['FNS_Fake']
          and 'access' not in catalog()['packages']['FNS_Fake'], r.stderr[-300:])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print('4. the publisher withholds a variant master and the variant-only files')
pp = types.ModuleType('publish_public_under_test')
pp.__dict__['__file__'] = os.path.join(_ROOT, 'scripts', 'publish_public.py')
exec(compile(read(os.path.join(_ROOT, 'scripts', 'publish_public.py')),
             'publish_public.py', 'exec'), pp.__dict__)
tmp2 = tempfile.mkdtemp(prefix='fns_variants_pp_')
try:
    cat_path = os.path.join(tmp2, 'catalog.json')
    json.dump({'packages': {
        'FNS_Free': {'category': 'X', 'description': 'd',
                     'variants': {'pro': {'access': PRO, 'withhold': ['ExtFreePro.py']}}},
        'FNS_Two': {'category': 'X', 'description': 'd', 'access': BASE,
                    'variants': {'pro': {'access': PRO, 'source': 'FNS_TwoPro'}}},
    }}, io.open(cat_path, 'w', encoding='utf-8'))
    pp.CATALOG = cat_path
    gated = pp.GatedPackages()
    check('GatedPackages() names the variant master beside the gated package',
          gated == ['FNS_Two', 'FNS_TwoPro'], gated)
    check('a free Base package is not gated by having a variant', 'FNS_Free' not in gated)
    check('the variant master\'s tree and tox are withheld under its own name',
          pp.Rule('modules/suspects/FNSTools/FNS_TwoPro/TwoProExt.py', gated) == 'gated:FNS_TwoPro'
          and pp.Rule('modules/suspects/FNSTools/FNS_TwoPro.tox', gated) == 'gated:FNS_TwoPro')
    check('a withheld variant file inside a FREE Base tree is withheld by name',
          pp.Rule('modules/suspects/FNSTools/FNS_Free/ExtFreePro.py', gated) == 'gated-file:ExtFreePro.py'
          and pp.Rule('FNSTools/FNS_Free/ExtFreePro.py', gated) == 'gated-file:ExtFreePro.py')
    check('the free Base\'s own files still publish',
          pp.Rule('modules/suspects/FNSTools/FNS_Free/ExtFree.py', gated) is None)
finally:
    shutil.rmtree(tmp2, ignore_errors=True)

print('5. staging, entitlement and preflight (source contracts)')
pub = read(os.path.join(PKG, 'publish.py'))
check('Stage() stages every variant under plus/ as <name>.<vid>.tox and re-hashes it',
      "vdst = os.path.join(plus_dir, vname + '.tox')" in pub
      and "if _sha256(vdst) != vart.get('sha256'):" in pub
      and "gated_staged.append(vname)" in pub)
check('a variant row must be authorizable like the Base (its own product, its own tier)',
      "rows.append(('%s.%s' % (p['name'], vid), str((v or {}).get('access', ''))))" in pub
      and "or p.get('variants')]" in pub)
ro = read(os.path.join(PKG, 'release_one.py'))
check('preflight refuses a missing source master, one nested in another, or a version disagreement',
      'def _variantProblems():' in ro and 'is not a live depth-1 COMP' in ro
      and 'artifact would carry its bytes' in ro and 'package, one version line' in ro
      and "blockers.append('tier variants: '" in ro)
check('the root-tox leak check covers variant masters too',
      "for c in list(Packages()) + list(VariantSourceComps()):" in ro
      and "gated.add(src)" in ro)

print('6. the install and update half (source contracts)')
upd = read(os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'FNS_Updater', 'ExtUpdater.py'))
ins = read(os.path.join(PKG, 'InstallerExt.py'))
check('Pkgvariant is read live off the component, FNS_About first, base when absent',
      "def _variantOf(comp):" in upd and "for host in (comp.op('FNS_About'), comp):" in upd
      and "return 'base'" in upd)
check('a variant build has its own store file: FNS_Foo.pro.tox',
      "def _storePath(self, name, vid='base'):" in upd
      and "stem = name if not vid or vid == 'base' else '%s.%s' % (name, vid)" in upd)
check('BestVariant ranks entitled variants by the ladder, base when none',
      "def BestVariant(self, name, manifest=None):" in upd
      and "if rank > best_rank and self._entitled('%s.%s' % (name, vid)):" in upd)
check('every build is a fetch row of its own; a scoped fetch takes only the build that lands',
      "def _allRows(self, man, scoped=False, plan_variants=None):" in upd
      and "rows = [r for r in rows if r['_variant'] == want]" in upd
      and "for pkg in self._allRows(man, scoped=names is not None," in upd)
check('the store status counts every build', "for pkg in self._allRows(man):" in upd)
check('hold on Pro: an installed build the account no longer holds is kept and never offered',
      "'state': 'held'" in upd and "'-- kept as it is' % target_vid" in upd)
check('the account growing is an upgrade: a swap upward, refused like any update when locked',
      "'state': 'locked' if refuse else 'upgrade'" in upd
      and "'your account now holds the %s build' % best" in upd)
check('an update compares the version of the INSTALLED build',
      "avail = str((vs.get(target_vid) or {}).get('version') or avail)" in upd)
check('the update pass fetches and applies the planned build',
      "job['plan_variants'] = {r['package']: r.get('variant', 'base')" in upd
      and "steps.append({'name': name, 'path': self._storePath(name, vid)," in upd
      and "art = _artifactFor(pkg, vid) or {}" in upd)
check('the installer asks the updater which build lands, once per plan',
      "def VariantPicks(manifest, target):" in ins and "picks = VariantPicks(manifest, tgt)" in ins
      and "vid = str(upd.BestVariant(pkg['name'], manifest) or 'base')" in ins)
check('the plan step carries the build and its own artifact path',
      "art = _artifactFor(pkg, vid)" in ins
      and "stem = name if vid == 'base' else '%s.%s' % (name, vid)" in ins
      and "'variant': vid," in ins)
check('the plan text names a non-base build', "state += ' (%s build)' % s['variant']" in ins)

print('7. the copy: one row, one page, the build above shown on it')
page = read(os.path.join(PKG, 'configurator', 'index.html'))
check('the card shows each variant build as a chip: an upgrade below its tier, yours above',
      "Object.keys(p.variants || {}).sort().forEach(function (vid) {" in page
      and "var vlabel = vtier + ' build' + (!account ? '' : (vown ? ' · yours' : ' · upgrade'));" in page)
check('the chip says what it adds and that it installs in place of the Base build',
      "it installs in place of the '" in page and "(tierLabel(p.access) || 'Base') + ' build.'" in page)
# the search moved into FNSSearch.prepare (docs/PickerSearch.md, 2026-10-03)
check('a variant summary is searchable',
      "add(vid + ' ' + ((p.variants[vid] || {}).summary || ''), DESC, true);" in page)
site = read(os.path.join(_ROOT, 'website', 'tools', 'build-site.mjs'))
# 0272bb46 (2026-09-24) moved the docs SIDEBAR's access marks into a quiet
# column (sidebarAccess), so the inline marks appear twice, on the index
# row and the feature card, and the sidebar still shows access its own way.
check('the site marks a variant build beside the Patreon mark everywhere that mark appears',
      site.count("${isPlus(p.name) ? plusMark(p.name) : ''}${variantMark(p.name)}${trialMark(p.name)}") == 2
      and 'sidebarAccess(p.name)' in site)
check('the package page carries a badge and a note per variant, never a second page',
      "for (const v of variantsOf(p.name)) {" in site and "const variantNote = variantsOf(p.name).length ?" in site
      and "${plusNote}${variantNote}${trialNote}" in site)

print()
if FAILS:
    print('FAILED: %d check(s)' % len(FAILS))
    raise SystemExit(1)
print('all tier-variant checks pass')
