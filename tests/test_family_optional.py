"""The FNS operator family is optional, and easy to turn off once on.

Owner decision 2026-09-17: some users want the family operators in their
palette without an FNS tab in the OP Create dialog. The picker shows a
switch ("Add FNS tab to OP Create") while a family operator is ticked; the
selection carries `family`; the installer honours it and, when a selection
does not say, keeps the project as it is (members installed without the
family means it was turned off). The last-install record and the site's
paste script carry the choice. Turning it off later is the same switch, or
the family's Remove Operator Family command, which calls the installer's
RemoveFamily. The installer releases the family from TDFam before it
destroys the component, so the tab leaves the dialog at once.

A destroy hook on the family was tried first and removed: a reinit ran it,
and a promoted lookup on the owner there deadlocked TouchDesigner's main
thread. This test keeps it from coming back.

    python tests/test_family_optional.py
"""
import ast
import io
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(_ROOT, 'packaging')
INS = os.path.join(PKG, 'InstallerExt.py')
BI = os.path.join(PKG, 'build_installer.py')
IDX = os.path.join(PKG, 'configurator', 'index.html')
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


ins, bi, idx, fce = read(INS), read(BI), read(IDX), read(FCE)


def function(src, name, ns):
    """Exec one top-level function out of a module's source into `ns`."""
    tree = ast.parse(src)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), name, 'exec'), ns)
    return ns[name]


class Cell(object):
    def __init__(self, val):
        self.val = val


class Table(object):
    def __init__(self, names):
        self.rows = [['package']] + [[n] for n in names]
        self.numRows = len(self.rows)

    def __getitem__(self, rc):
        return Cell(self.rows[rc[0]][rc[1]])


class Comp(object):
    family = 'COMP'

    def __init__(self, name, children=(), recorded=None, path=None):
        self.name = name
        self.children = list(children)
        self._rec = Table(recorded) if recorded is not None else None
        self.path = path or '/' + name
        self.valid = True

    def op(self, name):
        if name == 'installed':
            return self._rec
        return next((c for c in self.children if c.name == name), None)


index = {'FNS_SwitchTools': {'family': {'op_type': 'switchtools'}},
         'FNS_RandomCHOP': {'family': {'op_type': 'random'}},
         'FNS_AutoRes': {}, 'FNS_OpFamily': {'companion': 'family'}}
comps = ['FNS_OpFamily']
ns = {'INSTALLED_DAT': 'installed'}
FamilyWanted = function(ins, 'FamilyWanted', ns)

print('1. the installer decides from the selection, else from the project')
fresh = Comp('FNSTools')
check('a fresh project with no flag gets the family', FamilyWanted({}, index, comps, fresh) is True)
check('family: false keeps it out', FamilyWanted({'family': False}, index, comps, fresh) is False)
check('family: true brings it in even where it was turned off',
      FamilyWanted({'family': True}, index, comps,
                   Comp('FNSTools', recorded=['FNS_SwitchTools'])) is True)
off = Comp('FNSTools', children=[Comp('FNS_AutoRes')], recorded=['FNS_SwitchTools'])
check('members installed without the family: an unsaid selection keeps it off',
      FamilyWanted({}, index, comps, off) is False)
on = Comp('FNSTools', children=[Comp('FNS_OpFamily')], recorded=['FNS_SwitchTools'])
check('the family installed: an unsaid selection keeps it on', FamilyWanted({}, index, comps, on) is True)
check('a non-bool flag is not a choice', FamilyWanted({'family': 'no'}, index, comps, off) is False
      and FamilyWanted({'family': 'no'}, index, comps, fresh) is True)
check('no target: the family comes with a member', FamilyWanted({}, index, comps, None) is True)
check('ResolvePlan resolves the target before the companion rule',
      ins.index("root_comp = op(tgt)") < ins.index("if has_member and FamilyWanted(sel, index, companions, root_comp):"))

print('2. the family leaves TDFam before its component is destroyed')


class Owner(Comp):
    pass


class Registry(object):
    def __init__(self, owners):
        self.RegisteredFams = dict(owners)
        self.unregistered = []

    def UnregisterFamily(self, owner):
        self.unregistered.append(owner.path)
        return True


fam = Owner('FNS_OpFamily', path='/FNSTools/FNS_OpFamily')
other = Owner('Theirs', path='/project1/Theirs')
reg = Registry({'FNS': fam, 'THEIRS': other})
opns = {'debug': lambda *a: None}


class OpShim(object):
    FAMREGISTRY = reg


opns['op'] = OpShim
release = function(ins, '_releaseFamilies', opns)
check('the family owned by the removed component is unregistered',
      release(fam) == ['/FNSTools/FNS_OpFamily'] and reg.unregistered == ['/FNSTools/FNS_OpFamily'])
reg.unregistered = []
check('another family is left alone', release(Comp('FNS_AutoRes', path='/FNSTools/FNS_AutoRes')) == []
      and reg.unregistered == [])
check('RemoveTools releases before it destroys',
      re.search(r"name = comp\.name\n\s*_releaseFamilies\(comp\)", ins) is not None
      and ins.index('_releaseFamilies(comp)') < ins.index('comp.destroy()'))
OpShim.FAMREGISTRY = None
check('no TDFam registry: nothing to release, nothing raised', release(fam) == [])

print('3. no destroy hook on the family')
check('FamilyCommandsExt has no onDestroyTD (a reinit ran it and deadlocked TouchDesigner)',
      'onDestroyTD' not in fce)

print('4. turning it off')
check('RemoveFamily refuses the source checkout and can answer without acting',
      'def RemoveFamily(self, confirm=True):' in ins and 'locked = SourceLock(root.path)' in ins
      and "return {'ok': True, 'would_remove': present}" in ins)
check('it removes through RemoveTools (the same path as a picker removal)',
      "RemoveTools({'target': root.path, 'steps': [], 'to_remove': present})" in ins)
check('the family command checks first, then removes after it returns (it destroys its own COMP)',
      'def RemoveOperatorFamily(self) -> dict:' in fce
      and 'inst.RemoveFamily(confirm=False)' in fce
      and "run('args[0].valid and args[0].RemoveFamily()', inst, delayFrames=1" in fce)

print('5. the choice is remembered')
check('the last-install record says whether the family was installed',
      '\'\\trec["family"] = FAMILY in names\\n\'' in bi and "FAMILY_PACKAGE = 'FNS_OpFamily'" in bi
      and '% (ROOT_CANONICAL, FAMILY_PACKAGE, COMP_NAME))' in bi)
check('"Set up like last time" passes a recorded flag on, and only a real one',
      "if isinstance(rec.get('family'), bool):\n            sel['family'] = rec['family']" in ins)

print('6. the picker')
check('the switch exists, hidden until a family operator is ticked',
      'id="famopt" hidden' in idx and 'id="famchk"' in idx
      and "document.getElementById('famopt').hidden = !famMember;" in idx)
check('served, it starts from the project: members without the family read as off',
      "(last && typeof last.family === 'boolean' ? last.family : (familyHere || !membersHere))" in idx)
check('the selection always says, when the release has a family',
      'if (companions.length) sel.family = familyOn;' in idx)
check('turning it off counts as a change to apply',
      "var famGoes = served && familyHere && !(famMember && familyOn);" in idx
      and "(removals || famGoes) ? 'Apply changes…' : 'Review install…'" in idx
      and "notes.push('FNS tab removed')" in idx)
check('inside TouchDesigner the switch moves into the toolbar with the count',
      "act.appendChild(document.getElementById('famopt'));" in idx)
check('like last time applies the recorded choice',
      "if (last && typeof last.family === 'boolean') familyOn = last.family;" in idx)
check('the paste script adds the family with a free family pick unless the switch is off',
      '"FAM = " + (familyOn ? \'True\' : \'False\')' in idx
      and "if FAM and any(idx[t].get('family') for t in SEL) else [])" in idx
      and "'install': names, 'family': FAM}" in idx)

print('7. the root toggle (FNSTools page, FNS Tab in OP Create)')
check('declared as a project toggle, labelled for the dialog',
      "ROOT_PROJECT_TOGGLES = (\n    ('Opfamily', 'FNS Tab in OP Create'," in bi)
check('it never roams: the root config host excludes it',
      "missing = [n for n, _, _ in ROOT_PROJECT_TOGGLES if n not in tokens]" in bi
      and "ex.val = ' '.join(tokens + missing)" in bi)
check('the forwarder hears value changes and hands them to SetFamily, deferred',
      "pe.par.valuechange = True" in bi
      and "' '.join(n for n, _, _ in ROOT_ENTRY_POINTS + ROOT_PROJECT_TOGGLES)" in bi
      and 'run("args[0].valid and args[0].SetFamily(args[1])", inst, bool(par.eval()),' in bi)
check('the page is sorted by name list (par.order ties there)', 'pg.sort(*(ours + ' in bi)
check('SetFamily: off is RemoveFamily; on refuses without a family operator and fetches when needed',
      'def SetFamily(self, on=True, fetched=False):' in ins
      and 'res = self.RemoveFamily()' in ins
      and "install an FNS family operator first" in ins
      and "self._fetchSelection(plan['to_fetch'])" in ins
      and 'def familyWhenFetched(self, tries=0):' in ins)
check('a refusal puts the toggle back', "def _familyRefused(self, why):" in ins
      and ins.index('self.SyncFamilyToggle()', ins.index('def _familyRefused(self, why):'))
      < ins.index('def SetFamily('))
check('the toggle follows every install and removal, and the installer init',
      ins.count('self.SyncFamilyToggle()') >= 6
      and "run('args[0].SyncFamilyToggle()', self, delayFrames=90)" in ins)
check('a staged build copy (no running extensions) reads the root itself',
      "fam.val = root.op(FAMILY_PACKAGE) is not None" in bi)

print()
if FAILS:
    print('%d check(s) failed:' % len(FAILS))
    for f in FAILS:
        print('  - ' + f)
    raise SystemExit(1)
print('all optional-family checks pass')
