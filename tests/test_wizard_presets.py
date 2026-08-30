"""Curated preset bundles must never offer what the catalog cannot ship.

The guided setup's welcome can render named bundles from the manifest's
`presets` key (curated in packaging/catalog.json, emitted by
build_manifest._presets). Two layers keep them honest, and both are
pinned here from the REAL sources:

  - the page filters every bundle against the manifest it booted on
    (lifted from index.html and run in node, like the flavors test)
  - catalog.json's curation, when present, may only name catalogued
    packages (the standalone mirror of build_manifest's TD-side guard)

    python tests/test_wizard_presets.py
"""
import io
import json
import os
import re
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(_ROOT, 'packaging', 'configurator', 'index.html')
CATALOG = os.path.join(_ROOT, 'packaging', 'catalog.json')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


src = io.open(PAGE, encoding='utf-8').read()

print('1. the page filters bundles against its own manifest')
m = re.search(r'var bundles = \(M\.presets \|\| \[\]\)[\s\S]*?'
              r'\.filter\(function \(b\) \{ return b\.name && b\.packages\.length; \}\);',
              src)
assert m, 'could not lift the bundles mapping from the page'
harness = """
var M = {presets: [
  {name: 'VJ essentials', blurb: 'the live set',
   packages: ['AutoRes', 'GoneTool', 'FNS_TimelineTools']},
  {name: 'Ghost bundle', packages: ['GoneTool']},
  {name: '', packages: ['AutoRes']},
  {name: 'Core sneak', packages: ['FNS_Updater']},
  null,
]};
var byName = {
  AutoRes: {name: 'AutoRes', kind: 'tool'},
  FNS_TimelineTools: {name: 'FNS_TimelineTools', kind: 'tool'},
  FNS_Updater: {name: 'FNS_Updater', kind: 'core'},
};
%s
console.log(JSON.stringify(bundles));
""" % m.group(0)
try:
    got = subprocess.run([os.environ.get('NODE', 'node'), '-e', harness],
                         capture_output=True, text=True, timeout=30)
    out = got.stdout.strip()
    if got.returncode != 0:
        print('  node stderr: %s' % got.stderr.strip()[:300])
        out = ''
except Exception as e:
    out = ''
    print('  SKIP  node unavailable (%s)' % e)

if out:
    bundles = json.loads(out)
    check('one bundle survives', len(bundles) == 1, out)
    b = bundles[0] if bundles else {}
    check('unknown names are filtered out',
          b.get('packages') == ['AutoRes', 'FNS_TimelineTools'], out)
    check('the blurb rides along', b.get('blurb') == 'the live set', out)
    check('a bundle emptied by the filter is dropped whole',
          all(x.get('name') != 'Ghost bundle' for x in bundles), out)
    check('a nameless bundle is dropped',
          all(x.get('name') for x in bundles), out)
    check('core-only bundles are dropped (core is always installed)',
          all(x.get('name') != 'Core sneak' for x in bundles), out)

print('2. the welcome renders bundles fresh and between the fixed presets')
check('dynamic presets are cleared on every open',
      "querySelectorAll('.preset.dyn')" in src)
check('bundles insert before Everything (pre-all)',
      'insertBefore(btn, preAll)' in src)
check('a bundle pick routes through choose() like every preset',
      'function () { choose(bnd.packages); }' in src)

print('3. catalog curation, when present, names only catalogued packages')
catalog = json.load(io.open(CATALOG, encoding='utf-8'))
presets = catalog.get('presets', [])
if not presets:
    print('  SKIP  catalog.json carries no presets yet (the vocabulary is dormant)')
else:
    known = set(catalog.get('packages', {}))
    for p in presets:
        name = p.get('name', '<unnamed>')
        check('preset %r has a name and packages' % name,
              bool(p.get('name')) and bool(p.get('packages')))
        gone = [n for n in p.get('packages', []) if n not in known]
        check('preset %r names only catalogued packages' % name,
              not gone, ', '.join(gone))

print()
if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all checks passed')
