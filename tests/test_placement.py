"""`placement: pane` -- the package-authored install destination.

A package may declare in catalog.json (edited in the CMS) that it is a
reusable component: the installer spawns it into the network the user is
working in instead of the toolkit container. That contract crosses five
files -- catalog, manifest build, installer, updater, and both UIs -- and
this pins the load-bearing pieces of each so no single edit silently
drops one side of it.

    python tests/test_placement.py
"""
import io
import json
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(_ROOT, 'packaging', 'catalog.json')
MANIFEST_GEN = os.path.join(_ROOT, 'packaging', 'build_manifest.py')
INSTALLER = os.path.join(_ROOT, 'packaging', 'InstallerExt.py')
UPDATER = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools',
                       'FNS_Updater', 'ExtUpdater.py')
PAGE = os.path.join(_ROOT, 'packaging', 'configurator', 'index.html')
CMS_MJS = os.path.join(_ROOT, 'website', 'tools', 'cms.mjs')
CMS_HTML = os.path.join(_ROOT, 'website', 'tools', 'cms.html')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


print('1. catalog: placement only ever holds the one supported value')
cat = json.load(io.open(CATALOG, encoding='utf-8'))
bad = {n: e['placement'] for n, e in cat.get('packages', {}).items()
       if 'placement' in e and e['placement'] != 'pane'}
check('every placement value is "pane" (stored as presence)', not bad, bad)

print('2. the manifest build carries it (as presence, like recommended)')
gen = io.open(MANIFEST_GEN, encoding='utf-8').read()
check('placement read from curated meta, pane-only',
      re.search(r"meta\.get\('placement'.*?==\s*'pane'", gen, re.S)
      is not None)
check('emitted onto the entry', "entry['placement'] = 'pane'" in gen)

print('3. the installer lands pane packages in the working network')
inst = io.open(INSTALLER, encoding='utf-8').read()
check('PanePlacement resolves the current network editor pane',
      re.search(r"def PanePlacement.*?ui\.panes\.current.*?"
                r"PaneType\.NETWORKEDITOR", inst, re.S) is not None)
check('/ui and /sys are refused (rebuilt on open)',
      re.search(r"def PanePlacement.*?\('/ui', '/sys'\)", inst, re.S)
      is not None)
check('a protected (source) network falls back',
      re.search(r"def PanePlacement.*?SourceLock\(owner\.path\)", inst, re.S)
      is not None)
check('presence for a pane package is the install RECORD, not a root '
      'child',
      re.search(r"name in recorded if placement == 'pane'", inst)
      is not None)
check('the record always lands on the plan target',
      'RecordInstalled(parent_comp, name, landed' in inst)
check('unselecting a pane package clears only the record',
      "to_unrecord" in inst
      and 'forgotten; the copies in your networks' in inst)
check('a spawn sitting in the target root is removed for real, not '
      'double-handled as a forget',
      re.search(r"to_unrecord = sorted\(\(recorded & pane_names & tool_names\)"
                r"\s*\n\s*- set\(wanted\) - set\(to_remove\)\)", inst)
      is not None)
check('a spawn beside the toolkit container (network root) is removed '
      'for real too',
      re.search(r"home = parent_comp\.parent\(\).*?"
                r"destroy_and_clean\(beside\)", inst, re.S) is not None)
check('everywhere else stays a record-only forget',
      "stay yours" in inst)
check('the served page counts recorded pane spawns as installed',
      re.search(r"placement'\) == 'pane'.*?rec_t\[i, 0\]\.val in pane_names",
                inst, re.S) is not None)
check('a pane spawn never destroys a same-named user op',
      re.search(r"existing = None if pane else dest\.op\(name\)", inst)
      is not None)
check('console exposure does not apply outside the toolkit',
      'exposed = [] if pane else ExposeConsoleHosts(comp)' in inst)

print('4. the updater treats a pane package as a component, never missing')
upd = io.open(UPDATER, encoding='utf-8').read()
check("Compare has the 'component' state",
      re.search(r"placement'\) == 'pane'.*?'state': 'component'", upd, re.S)
      is not None)
check('it is reported before the missing row',
      upd.find("'state': 'component'") < upd.find("'state': 'missing'"))
check('Compare also walks the doorstep (siblings of the root)',
      re.search(r"candidates = list\(root\.children\).*?home\.children.*?"
                r"placement'\) == 'pane'", upd, re.S) is not None)
check('the replace rail resolves a doorstep spawn',
      re.search(r"def _replacePackage.*?step\.get\('placement'\) == 'pane'",
                upd, re.S) is not None)
check('the embedded replace anchors on the comp\'s own parent',
      re.search(r"carrier = dest\.parent\(\).*?carrier\.loadTox\(path\)",
                upd, re.S) is not None)
check('update steps carry placement',
      re.search(r"'placement': \(pkg or \{\}\)\.get\('placement'", upd)
      is not None)

print('5. the picker says where a pane package lands')
page = io.open(PAGE, encoding='utf-8').read()
check('the card carries the chip',
      "lands in your working network" in page)
check('the selection sentence counts pane picks',
      'will spawn into the network you are working in' in page)

print('6. the CMS authors it')
mjs = io.open(CMS_MJS, encoding='utf-8').read()
check('the server exposes placement on the package',
      re.search(r"placement: String\(cat\.packages\[name\]\.placement",
                mjs) is not None)
check('the PUT handler validates and stores as presence',
      re.search(r"unknown placement.*?entry\.placement = 'pane'.*?"
                r"delete entry\.placement", mjs, re.S) is not None)
html = io.open(CMS_HTML, encoding='utf-8').read()
check('the editor offers the control', 'id="placement"' in html
      and '<option value="pane">' in html)
check('saving sends it', 'placement: draft.placement' in html)

print()
if FAILS:
    print('FAILED: %d check(s)' % len(FAILS))
    raise SystemExit(1)
print('all placement checks pass')
