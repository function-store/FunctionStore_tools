"""'Changed since ship' -- the CMS signal for bytes without a bump.

release_one records each package's PI build counter into
packaging/shipped_builds.json as it ships; the CMS compares the live
counter against it, so a tox saved after its last release reads
'changed' in the release table even while the version still equals the
published one. This pins the three sides of that contract.

    python tests/test_shipped_builds.py
"""
import io
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELEASE = os.path.join(_ROOT, 'packaging', 'release_one.py')
CMSEXT = os.path.join(_ROOT, 'FNS_CMS', 'CmsExt.py')
CMSHTML = os.path.join(_ROOT, 'website', 'tools', 'cms.html')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


print('1. the release records what shipped')
rel = io.open(RELEASE, encoding='utf-8').read()
check('the sidecar is defined',
      "SHIPPED_BUILDS = ('packaging', 'shipped_builds.json')" in rel)
check('recorded AFTER the release\'s own PI saves',
      rel.find('_recordShippedBuilds(todo') > rel.find('pi_saved.append'))
check('a selected dirty/unlanded package is saved too, not only the bump',
      re.search(r"to_save = list\(bumped_live\).*?_unlandedPackages\(todo\)"
                r".*?Get_Dirt", rel, re.S) is not None)
check('a bookkeeping failure never fails the release',
      re.search(r"try:\s*\n\s*_recordShippedBuilds.*?except Exception",
                rel, re.S) is not None)
check('ShippedBuilds() reads back and degrades to {}',
      re.search(r"def ShippedBuilds.*?return \{\}", rel, re.S) is not None)

print('2. the CMS compares live build against it')
ext = io.open(CMSEXT, encoding='utf-8').read()
check('_apiDirty reads the sidecar',
      "'shipped_builds.json'" in ext)
check('rows carry shipped_build and build_changed',
      "'shipped_build': sb" in ext and "'build_changed': changed" in ext)
check('unknown is never reported as changed',
      re.search(r"changed = None\s*\n\s*if sb is not None and live_b is not "
                r"None", ext) is not None)

print('2b. the third signal: sources newer than the suspect tox')
check('_newestSource covers the DATs beside the suspect tox',
      re.search(r"_repo\('modules', 'suspects', 'FNSTools', name\)", rel)
      is not None)
check('_apiDirty annotates unlanded/rippled from _unlandedPackages',
      "_unlandedPackages" in ext and "r['unlanded']" in ext)

print('3. the release table shows and selects it')
html = io.open(CMSHTML, encoding='utf-8').read()
check('the changed badge renders', 'tag-chg' in html
      and 'changed since ship' in html)
check('the select button includes changed rows',
      re.search(r"r\.unshipped \|\| r\.build_changed", html) is not None)
check('the PI column shows unlanded and the save button covers it',
      "'unlanded'" in html
      and re.search(r"r\.dirty \|\| r\.unlanded", html) is not None)

print('4. the prune rail')
check('the retire endpoint is routed',
      "('POST', '/api/retire')" in ext and '_apiRetire' in ext)
check('_apiDirty exposes the three prune lists',
      all(k in ext for k in ("'vanished'", "'stale_retired'",
                             "'prunable_retired'")))
check('a live package cannot be retired',
      'still a live package' in ext)
check('the doc is archived, never deleted',
      re.search(r"os\.replace\(doc_path", ext) is not None
      and "'retired'" in ext)
check('the catalog entry and shipped-builds record are pruned',
      re.search(r"\.pop\(name", ext) is not None
      and 'shipped-builds record dropped' in ext)
check('a gated package warns about the worker tier map',
      'wrangler.toml' in ext)
check('the page renders the three verbs',
      'relretire' in html and 'Retire' in html
      and 'Clear entry' in html and 'Prune entry' in html)

print("4b. the Published column says where it comes from")
check('_apiDirty ships both release labels',
      "'published_release'" in ext and "'staged_release'" in ext)
check('a started refresh is not reported as an error',
      "r.get('ok') is False" in ext)
check('the page shows the stale-cache banner with a Refresh store button',
      'Published column may be stale' in html and 'relRefreshStore' in html)

print('5. the bucket prune')
up = io.open(os.path.join(_ROOT, 'packaging', 'upload.py'),
             encoding='utf-8').read()
check('upload.py has a prune-only entry',
      "'--prune-only'" in up and '--prune-only needs --prune N' in up)
check('dry mode previews and deletes nothing',
      'would delete' in up and 'DRY RUN -- nothing deleted' in up)
check('the dry return comes before any delete',
      up.find('DRY RUN -- nothing deleted') < up.find('pool.map(_deleteOne'))
check('release_one starts it detached into the shared upload log',
      re.search(r"def StartPrune.*?'--prune-only'", rel, re.S) is not None)
check('the CMS routes it and guards keep < 1',
      "('POST', '/api/prunebucket')" in ext
      and 'keep must be at least 1' in ext)
check('keep=0 is refused, never defaulted (the falsy-or trap deleted '
      'real objects once)',
      "body.get('keep') or" not in ext
      and re.search(r"int\(body\.get\('keep', 3\)\)", ext) is not None)
check('a running upload/prune blocks a second start',
      re.search(r"def _apiPruneBucket.*?log moved\s*'?\s*\n?.*?seconds ago",
                ext, re.S) is not None)
check('the page button previews on Cancel (safe by construction)',
      'relPruneBucket' in html and 'DRY PREVIEW' in html)

print()
if FAILS:
    print('FAILED: %d check(s)' % len(FAILS))
    raise SystemExit(1)
print('all shipped-build checks pass')
