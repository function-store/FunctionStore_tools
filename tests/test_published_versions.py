"""Offline test of the release's idea of "what the world has".

release_one.py cannot be exec'd outside TouchDesigner (it reaches for
`project` at import), so this test lifts the two functions that decide
published versions and runs them against temp files. That is enough,
because the bug being pinned is purely about WHICH FILES are consulted:

    _publishedVersions() read packaging/manifest.json, which Build()
    regenerates FROM the live Pkgversion pars. So `pub` always equalled
    the live version, auto-bump's `old_v <= pub` was always true, and a
    deliberate 3.0.0 baseline would have shipped as 3.0.1.

    python tests/test_published_versions.py
"""
import io
import json
import os
import re
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


SRC = io.open(os.path.join(_ROOT, 'packaging', 'release_one.py'),
              encoding='utf-8').read()


def lift(*names):
    """Pull named top-level defs out of release_one without exec'ing it."""
    ns = {'json': json, 'os': os}
    for name in names:
        m = re.search(r'^def %s\(.*?(?=^def |\Z)' % name, SRC, re.M | re.S)
        assert m, 'could not find def %s' % name
        exec(compile(m.group(0), name, 'exec'), ns)
    return ns


print('1. the source list is what the fix is about')
check('the repo manifest is NOT consulted',
      "_repo(PKG_DIR, 'manifest.json')" not in
      re.search(r'def _publishedVersions\(.*?(?=^def )', SRC,
                re.M | re.S).group(0),
      'packaging/manifest.json is back in the chain')
check('the store cache IS consulted', '_storeManifest()' in SRC)
check('the staged tree IS consulted',
      "'publish', 'manifest.json'" in SRC)

print('2. reading a manifest')
ns = lift('_versionsIn')
tmp = tempfile.mkdtemp(prefix='fns_pubver_')
good = os.path.join(tmp, 'good.json')
io.open(good, 'w', encoding='utf-8').write(json.dumps({'packages': [
    {'name': 'AltSelect', 'version': '1.0.1'},
    {'name': 'FNS_Updater', 'version': '1.0.10'},
    {'name': 'NoVersion'},
]}))
got = ns['_versionsIn'](good)
check('versions read', got.get('AltSelect') == '1.0.1', got)
check('a missing version reads empty, not absent',
      got.get('NoVersion') == '', got)
check('an unreadable file is empty, never an exception',
      ns['_versionsIn'](os.path.join(tmp, 'nope.json')) == {})

print('3. highest wins across sources')
# the real function needs TD for the store path; the merge rule is what
# matters, so exercise it directly the way _publishedVersions does
def merge(paths, verTuple):
    out = {}
    for path in paths:
        for name, ver in ns['_versionsIn'](path).items():
            if not ver:
                continue
            if name not in out or verTuple(ver) > verTuple(out[name]):
                out[name] = ver
    return out


vt = lift('_verTuple')['_verTuple']
older = os.path.join(tmp, 'older.json')
io.open(older, 'w', encoding='utf-8').write(json.dumps({'packages': [
    {'name': 'AltSelect', 'version': '1.0.0'},
    {'name': 'OnlyHere', 'version': '2.5.0'},
]}))
merged = merge([older, good], vt)
check('the higher version wins regardless of order',
      merged['AltSelect'] == '1.0.1', merged)
check('a package in only one source survives',
      merged['OnlyHere'] == '2.5.0', merged)

print('4. THE regression: a stale published map must not eat the baseline')
def decide(live, pub):
    """ReleaseMany's auto-bump, verbatim in shape."""
    if pub and vt(live) <= vt(pub):
        parts = [int(x) for x in pub.split('.')]
        parts[2] += 1
        return '.'.join(str(x) for x in parts)
    return live


check('world has 1.0.1, live is the 3.0.0 baseline -> ships 3.0.0',
      decide('3.0.0', '1.0.1') == '3.0.0', decide('3.0.0', '1.0.1'))
check('never published -> ships 3.0.0',
      decide('3.0.0', '') == '3.0.0', decide('3.0.0', ''))
check('world already has 3.0.0 -> bumps, as it should',
      decide('3.0.0', '3.0.0') == '3.0.1', decide('3.0.0', '3.0.0'))
check('the old bug reproduced: self-referential pub bumps the baseline',
      decide('3.0.0', '3.0.0') != '3.0.0')

shutil.rmtree(tmp, ignore_errors=True)
print()
if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all checks passed')
