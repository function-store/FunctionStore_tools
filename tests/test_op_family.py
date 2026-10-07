"""The FNS operator family (docs/OperatorFamilyFromStore.md): the manifest's
`family` block is derived from a live package's FamManifest or curated in
the catalog, a member implies pane placement, the catalog rules refuse the
two-sources case, and the updater keeps the family folder as a derived
mirror of the store.

Runs outside TouchDesigner: build_manifest.py is exec'd with the TD
builtins it touches stubbed; the updater's rails are pinned as source
contracts.

    python tests/test_op_family.py
"""
import io
import json
import os
import re
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(_ROOT, 'packaging')
MANIFEST_GEN = os.path.join(PKG, 'build_manifest.py')
CATALOG = os.path.join(PKG, 'catalog.json')
DOCS = os.path.join(PKG, 'docs')
UPD = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'FNS_Updater', 'ExtUpdater.py')
WRANGLER = os.path.join(_ROOT, 'worker', 'wrangler.toml')
FAILS = []


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
    code = read(MANIFEST_GEN)
    exec(compile(code, MANIFEST_GEN, 'exec'), mod.__dict__)
    return mod


class FakeDAT(object):
    def __init__(self, text):
        self.text = text


class FakeComp(object):
    """A package with a FamManifest: op('FamManifest') -> a comp whose
    op('OpInfo') etc. are DATs of JSON."""
    def __init__(self, name, dats=None):
        self.name = name
        self._dats = dats

    def op(self, path):
        if path == 'FamManifest' and self._dats is not None:
            return FakeComp(self.name + '/FamManifest', self._dats)
        if self._dats is not None and path in self._dats:
            return FakeDAT(self._dats[path])
        return None


bm = load_build_manifest(_ROOT)

# ---------------------------------------------------------------- 1
print('1. the family block is derived from FamManifest')
comp = FakeComp('FNS_Foo', {
    'OpInfo': json.dumps({'op_type': 'foo', 'op_label': 'Foo', 'op_group': 'CHOP',
                          'isFilter': True, 'compatible_types': ['CHOP', 'TOP'],
                          'summary': 'Does foo.', 'search_words': 'foo bar'}),
    'ParRetain': json.dumps({'Speed': 'value'}),
    'StateRetain': '{}',
    'Shortcuts': json.dumps({'ctrl.shift.b': 'Bypass'}),
})
fam = bm.FamilyFor(comp)
check('op_type, label, group, summary come through', fam.get('op_type') == 'foo'
      and fam.get('op_label') == 'Foo' and fam.get('op_group') == 'CHOP'
      and fam.get('summary') == 'Does foo.', fam)
check("TDFam's isFilter becomes is_filter", fam.get('is_filter') is True, fam)
check('a space-separated search_words string becomes a list',
      fam.get('search_words') == ['foo', 'bar'], fam)
check('compatible_types stays a list', fam.get('compatible_types') == ['CHOP', 'TOP'], fam)
check('a non-empty ParRetain rides as par_retain', fam.get('par_retain') == {'Speed': 'value'}, fam)
check('an empty StateRetain is left out', 'state_retain' not in fam, fam)
check('Shortcuts ride as shortcuts', fam.get('shortcuts') == {'ctrl.shift.b': 'Bypass'}, fam)
check('a package with no FamManifest derives nothing', bm.FamilyFor(FakeComp('FNS_Bare')) == {})
check('op_name rides beside a lowercase op_type',
      bm.FamilyFor(FakeComp('FNS_Named', {'OpInfo': json.dumps({'op_type': 'scenechanger', 'op_name': 'sceneChanger'})}))
      .get('op_name') == 'sceneChanger')
check('a type with capitals derives nothing (TDFam could never replace its stubs)',
      bm.FamilyFor(FakeComp('FNS_Camel', {'OpInfo': json.dumps({'op_type': 'sceneChanger'})})) == {})
check('FamilyProblems names the capitalised type, the bad group and a broken retain DAT',
      len(bm.FamilyProblems(FakeComp('FNS_Bad', {'OpInfo': json.dumps({'op_type': 'sceneChanger', 'op_group': 'Widgets'}),
                                                 'ParRetain': '{nope'}))) == 3)
check('FamilyProblems is empty for a good member and for a non-member',
      bm.FamilyProblems(comp) == [] and bm.FamilyProblems(FakeComp('FNS_Bare')) == [])
check('an OpInfo that is not JSON derives nothing (never breaks the build)',
      bm.FamilyFor(FakeComp('FNS_Broken', {'OpInfo': '{not json'})) == {})
check('an OpInfo without a usable op_type derives nothing',
      bm.FamilyFor(FakeComp('FNS_NoType', {'OpInfo': json.dumps({'op_label': 'X'})})) == {})

# ---------------------------------------------------------------- 2
print('2. a curated block, for a foreign or hostless entry')
cur = bm.CuratedFamily({'family': {'op_type': 'bar', 'op_group': 'TOP', 'is_filter': False,
                                   'par_retain': {'A': 'value'}}})
check('CuratedFamily normalises the same way', cur.get('op_type') == 'bar'
      and cur.get('op_group') == 'TOP' and cur.get('is_filter') is False
      and cur.get('par_retain') == {'A': 'value'}, cur)
check('no family key, no block', bm.CuratedFamily({'category': 'X'}) == {})
check('a family that is not an object is ignored here (CatalogProblems reports it)',
      bm.CuratedFamily({'family': 'bar'}) == {})

# ---------------------------------------------------------------- 3
print('3. the catalog rules')
good = {'packages': {'FNS_Foo': {'category': 'X', 'description': '',
                                 'family': {'op_type': 'foo', 'op_group': 'CHOP'}}}}
check('a good curated block on a hostless live package passes',
      bm.CatalogProblems(good, {'FNS_Foo'}, family_hosted=set()) == [])
bad = {'packages': {
    'Str': {'category': 'X', 'family': 'foo'},
    'Type': {'category': 'X', 'family': {'op_type': 'no spaces here'}},
    'Group': {'category': 'X', 'family': {'op_type': 'g', 'op_group': 'Widgets'}},
    'Both': {'category': 'X', 'family': {'op_type': 'both', 'op_group': 'CHOP'}},
    'Root': {'category': 'X', 'placement': 'root', 'family': {'op_type': 'r', 'op_group': 'COMP'}},
}}
p = bm.CatalogProblems(bad, set(bad['packages']), family_hosted={'Both'})
check('family must be an object', any(x.startswith('Str:') for x in p), p)
check('op_type must be a word', any(x.startswith('Type:') and 'op_type' in x for x in p), p)
check('op_group must be an operator family', any(x.startswith('Group:') and 'op_group' in x for x in p), p)
check('a curated block beside a live FamManifest is refused',
      any(x.startswith('Both:') and 'FamManifest' in x for x in p), p)
check('a member at the root is refused', any(x.startswith('Root:') and 'root' in x for x in p), p)
check('a curated type with capitals is refused', any(x.startswith('Camel:') for x in
      bm.CatalogProblems({'packages': {'Camel': {'category': 'X', 'family': {'op_type': 'sceneChanger'}}}}, {'Camel'})))
check('outside TD (family_hosted None) the two-sources case is not judged',
      not any(x.startswith('Both:') for x in bm.CatalogProblems(bad, set(bad['packages']))))

# ---------------------------------------------------------------- 4
print('4. the shipped catalog and docs')
cat = json.load(io.open(CATALOG, encoding='utf-8'))
live_guess = {n for n, e in cat['packages'].items() if 'source' not in e}
check('CatalogProblems reports nothing on the shipped catalog',
      not bm.CatalogProblems(cat, live_guess))
MEMBERS = ('FNS_RandomCHOP', 'FNS_SimpleSceneChanger', 'FNS_ProSceneChanger', 'FNS_SwitchTools',
           'FNS_MixSequencer', 'FNS_OpSequencer', 'FNS_CamSequencer')
check('no member curates a family block (they carry FamManifest, which derives it)',
      not [n for n in MEMBERS if 'family' in cat['packages'].get(n, {})])
# A member is NOT placed (owner 2026-09-18). It is reached from the FNS tab of
# the OP Create dialog and from the family folder on disk, which is the whole
# reason it ships as a family member; spawning a copy into the user's network
# at install was never wanted. This asserted 'pane' until then.
check('no member is placed at install',
      all(cat['packages'][n].get('placement') == 'none' for n in MEMBERS),
      {n: cat['packages'][n].get('placement') for n in MEMBERS})
check('FNS_OpFamily is catalogued free, FNS_RandomCHOP at the Base tier',
      cat['packages']['FNS_OpFamily'].get('access', 'free') == 'free'
      and cat['packages']['FNS_RandomCHOP'].get('access') == '8323905')
for n in ('FNS_OpFamily', 'FNS_RandomCHOP'):
    check('%s has a doc (site build hard-fails otherwise)' % n,
          os.path.exists(os.path.join(DOCS, n + '.md')))
wr = read(WRANGLER)
tiers = re.findall(r'"(\d+)": \[(.*?)\]', wr, re.S)
check('the Worker map has tiers to check', len(tiers) >= 2)
check('every tier that grants SimpleSceneChanger (Base and above) grants FNS_RandomCHOP',
      all('FNS_RandomCHOP' in body for tid, body in tiers if 'FNS_SimpleSceneChanger' in body))

# ---------------------------------------------------------------- 5
print('5. the updater keeps the family folder (source contracts)')
upd = read(UPD)
check('the family folder is <user palette>/FNSTools/FNS, from the palette resolver (2026-09-18)',
      "root = _fnsPaletteRoot()" in upd
      and "return '%s/%s' % (root, self._FAMILY_NAME) if root else ''" in upd)
check('only rows with a family block are mirrored',
      re.search(r"fam = pkg\.get\('family'\)\n\s*if not isinstance\(fam, dict\) or not fam\.get\('op_type'\):\n\s*continue", upd) is not None)
check("a tox the store does not hold is skipped, never fetched",
      re.search(r"src = self\._storePath\(name\)\n\s*if not os\.path\.exists\(src\):", upd) is not None)
check("files carry the PUBLIC name with a .json sidecar (flat, 2026-09-18; the version rides the sidecar)",
      "stem = name[4:] if name.startswith('FNS_') else name" in upd
      and "dest = '%s/%s.tox' % (folder, stem)" in upd
      and "side = '%s/%s.json' % (folder, stem)" in upd)
check('the op_group rides the sidecar, not a subfolder',
      "'op_group': str(fam.get('op_group', '') or '')," in upd
      and 'dest_dir' not in upd.split('def SyncFamilyFolder')[1].split('def _dropLegacyFamilyTree')[0])
check('the sidecar carries OpInfo, ParRetain, StateRetain and Shortcuts',
      all(("'%s'" % k) in upd for k in ('OpInfo', 'ParRetain', 'StateRetain', 'Shortcuts')))
check('the sidecar type is lowercase and its op_name the readable spelling',
      "'op_type': str(fam.get('op_type', '') or '').lower()," in upd
      and "'op_name': str(fam.get('op_name', '') or fam.get('op_type', '') or '')," in upd)
check('the sidecar version is the manifest version, the doc_url the help_url',
      "'op_version': str(pkg.get('version', '') or '')" in upd
      and "'doc_url': str(pkg.get('help_url', '') or '')" in upd)
check('what is not a kept tox or sidecar is removed (stale names, non-members)',
      re.search(r"elif fp\.lower\(\) not in keep and fn\.lower\(\)\.endswith\(\('\.tox', '\.json'\)\):\n\s*os\.remove\(fp\)", upd) is not None)
check('the full-mirror hook syncs the folder',
      re.search(r"def _afterStoreComplete\(self, status\):.*?self\.SyncFamilyFolder\(\)", upd, re.S) is not None)
check('a scoped refresh (a picker install) syncs it too',
      re.search(r"elif job\.get\('names'\):\n(\s*#.*\n)*\s*self\.SyncFamilyFolder\(\)", upd) is not None)
check('an update pass syncs before it chains the store mirror',
      "self.SyncFamilyFolder()\n\t\tself._keepStoreLater()" in upd)
check("TDFam is reached by shortcut, never a path",
      "reg = getattr(op, 'FAMREGISTRY', None)" in upd and '/sys/TDFamRegistry' not in upd)
check('the refresh asks the registered owner, guarded',
      re.search(r"owner = reg\.GetFamilyOwner\(self\._FAMILY_NAME\)\n\s*if owner is None:\n\s*return False\n\s*reg\.RefreshCache\(self\._FAMILY_NAME, owner, folder\)", upd) is not None)

# ---------------------------------------------------------------- 6
print('6. the family package guards the toolkit and offers commands')
FAMDIR = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'FNS_OpFamily')
cbs = read(os.path.join(FAMDIR, 'default_callbacks.py'))
cmds = read(os.path.join(FAMDIR, 'FamilyCommandsExt.py'))
check('the pre-stub, pre-replace and pre-update hooks skip anything inside the toolkit container',
      "return not _inToolkit(info.get('comp'))" in cbs
      and "return not _inToolkit(info.get('stub'))" in cbs
      and "return not _inToolkit(info.get('oldComp'))" in cbs)
check('the toolkit container is the family package parent, and the bare root never counts',
      "home = me.parent().parent()" in cbs and "home.path == '/'" in cbs)
check('five commands, declared with FNSCommand',
      all(("def %s(" % n) in cmds for n in ('StubFamilyOperators', 'ReplaceFamilyStubs',
                                           'UpdateFamilyOperators', 'SyncFamilyFromStore',
                                           'RemoveOperatorFamily'))
      and cmds.count('@FNSCommand.fns_command(') == 5)
check('the commands never open a dialog (the TDFam pulses do; these are reachable from scripts)',
      'messageBox' not in cmds)
check('every command that finds operators drops the toolkit container first',
      cmds.count('self._placed(fam._find') == 3)
check('the updater is reached by shortcut', "getattr(op, 'FNS_UPDATER', None)" in cmds)
check('no __future__ import (PI stamps an info header above the module)',
      '__future__' not in cmds)

# ---------------------------------------------------------------- 7
print('7. the content CMS edits the family facts where they live')
cms_py = read(os.path.join(_ROOT, 'FNS_CMS', 'CmsExt.py'))
mjs = read(os.path.join(_ROOT, 'website', 'tools', 'cms.mjs'))
html = read(os.path.join(_ROOT, 'website', 'tools', 'cms.html'))
check('FNS_CMS routes familyread and familywrite',
      "('POST', '/api/familyread')" in cms_py and "('POST', '/api/familywrite')" in cms_py)
check("the write validates with build_manifest's own rules",
      "bm['FAMILY_TYPE_RE'].match(op_type)" in cms_py and "bm['FAMILY_GROUPS']" in cms_py
      and "bm['FamilyProblems'](comp)" in cms_py)
check('the write refuses without PI (an unsaved manifest dies on reload) and saves after writing',
      "if pi is None:" in cms_py and cms_py.count('pi.Save(comp)') >= 2)
check("the write stamps TDFam's tags (FindOps and a stub replace find a member by them)",
      "'<FAM:FNS>', '<TYPE:%s>' % op_type, '<MANIFEST>'" in cms_py)
check('the server curates `family` for a foreign package only',
      "family is curated only on a foreign package" in mjs and "'family', ...LINK_KEYS" in mjs)
check('the server refuses a type with capitals, and a member that would be placed',
      "/^[a-z][a-z0-9_]*$/.test(type)" in mjs
      and "a family member is not placed at install" in mjs)
check('the page reads and writes a live package through TD, and a foreign block rides the save',
      "/api/td/familyread" in html and "/api/td/familywrite" in html
      and "family: draft.foreign ? (draft.family || null) : undefined," in html)
check('the page says why when TD is not connected, instead of editing a copy',
      "TouchDesigner is not connected, so this cannot be edited" in html)

print()
if FAILS:
    print('%d check(s) failed:' % len(FAILS))
    for f in FAILS:
        print('  - ' + f)
    raise SystemExit(1)
print('all op-family checks pass')
