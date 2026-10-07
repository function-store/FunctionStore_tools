"""Always Set Up Like Last Time: the root toggle, the silent rail, and
the welcome's routing.

A fresh drop with the toggle on installs the machine's last recorded
setup with no picker and no window. Two things are easy to lose in a
refactor and are pinned here: the toggle is read from the roaming file
itself (the host that restores the par has not run when the welcome
asks), and the silent rail never removes anything.

    python tests/test_auto_setup.py
"""
import io
import json
import os
import re
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INST = os.path.join(_ROOT, 'packaging', 'InstallerExt.py')
GEN = os.path.join(_ROOT, 'packaging', 'build_installer.py')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


# InstallerExt's top level is imports and constants: it execs outside TD,
# and the readers under test take an explicit path so `app` is never touched.
ns = {'__name__': 'installer_under_test'}
exec(compile(io.open(INST, encoding='utf-8').read(), INST, 'exec'), ns)
AutoSetupWanted = ns['AutoSetupWanted']
src = io.open(INST, encoding='utf-8').read()
gen = {'__name__': 'build_installer_under_test'}
exec(compile(io.open(GEN, encoding='utf-8').read(), GEN, 'exec'), gen)


class _Par:
    def __init__(self, val):
        self._val = val

    def eval(self):
        return self._val


class _Root:
    def __init__(self, **pars):
        self.par = type('P', (), {})()
        for k, v in pars.items():
            setattr(self.par, k, _Par(v))


def _config(toggle=None, record=True):
    d = {'schema': 1, 'tools': {'FNS': {'pars': {}, 'state': {}}}}
    if toggle is not None:
        d['tools']['FNS']['pars']['Setuplikelast'] = {'mode': 'CONSTANT', 'val': toggle, 'eval': toggle}
    if record:
        d['tools']['FNS']['state']['last_install'] = {
            'packages': ['FNS_AutoRes', 'FNS_Toolbar'], 'project': 'Show.toe',
            'when': '2026-09-16T12:00:00', 'bind': 'embedded'}
    fd, path = tempfile.mkstemp(suffix='.json')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(d, f)
    return path


print('1. the toggle is read from the roaming file before the host restores it')
p = _config(toggle=True)
check('file says on, record present, no root par yet -> wanted',
      AutoSetupWanted(_Root(), p) is True)
check('file says on but the live par is off (not restored yet) -> the file wins',
      AutoSetupWanted(_Root(Setuplikelast=False), p) is True)
check('live par on -> wanted without opening the file twice',
      AutoSetupWanted(_Root(Setuplikelast=True), p) is True)
os.remove(p)
p = _config(toggle=False)
check('file says off -> the picker', AutoSetupWanted(_Root(), p) is False)
os.remove(p)
p = _config(toggle=None)
check('no toggle in the file -> the picker', AutoSetupWanted(_Root(), p) is False)
os.remove(p)

print('2. it never fires without something to install, or under project scope')
p = _config(toggle=True, record=False)
check('toggle on, no last-install record -> the picker',
      AutoSetupWanted(_Root(Setuplikelast=True), p) is False)
os.remove(p)
p = _config(toggle=True)
check('project scope never reads the roaming file',
      AutoSetupWanted(_Root(Configscope='project'), p) is False)
check('a missing file is a no, not an error',
      AutoSetupWanted(_Root(), p + '.missing') is False)
os.remove(p)

print('3. the silent rail')
check('InstallLastSetup is DRY RUN by default',
      re.search(r"def InstallLastSetup\(self, confirm=False\)", src) is not None
      and re.search(r"if not confirm:\s*\n\s*full = self\._manifestPath\(\)", src) is not None)
check('it never removes -- this rail only adds the remembered tools',
      re.search(r"res = self\.Install\(remove=False\)", src) is not None)
# Was: fetched only when the store had NO manifest. A store is
# machine-wide, so that never looked again and a stale store installed a
# whole old release into a clean project (2026-09-19, v3.2.37 over
# v3.2.42). The fetch is now unconditional at stage 'plan'.
check('the manifest is fetched before planning, store or no store',
      re.search(r"if stage == 'plan' and \(full is None or _inStore\(full\)\):"
                r".*?why = self\._refreshStore\(names=\[\]\)", src, re.S) is not None
      and re.search(r"if full is None:.*?return self\._lastSetupStop\("
                    r"'the store manifest did not arrive'\)", src, re.S)
      is not None)
check('the same download missing twice stops the rail instead of looping',
      re.search(r"if plan\['to_fetch'\]:\s*\n\s*if stage == 'artifacts':\s*\n\s*return self\._lastSetupStop",
                src) is not None)
check('the wait is bounded and frame-scheduled, never a sleep',
      'LAST_SETUP_TRIES = 600' in src
      and re.search(r"run\(\"args\[0\]\.valid and args\[0\]\.ext\.InstallerExt\._lastSetupTick", src)
      is not None)
check('Patreon holds are kept wanted and named in the Textport',
      "return self._holdPatreonLocked(sel)" in src
      and 'waiting for Patreon sign-in before these install' in src)
check('names the release no longer has fall away, core never rides as a tool',
      "names = [n for n in names if n in known and n not in core]" in src)
check('a stop says how to continue by hand',
      'Pick Tools on ' in src and 'continues by hand' in src)

print('4. the root toggle')
toggles = dict((n, (l, h)) for n, l, h in gen['ROOT_TOGGLES'])
check('Setuplikelast is declared beside the entry points', 'Setuplikelast' in toggles)
check('it has help that says what happens and that it roams',
      'Setuplikelast' in toggles and 'no picker' in toggles['Setuplikelast'][1]
      and 'Roams' in toggles['Setuplikelast'][1])
gsrc = io.open(GEN, encoding='utf-8').read()
check('EnsureRootEntryPoints creates it get-or-create, default off',
      re.search(r"for name, label, help_text in ROOT_TOGGLES:.*?appendToggle\(name, label=label\)\[0\]\s*\n\s*par\.default = False",
                gsrc, re.S) is not None)
# The forwarder carried only the entry-point pulses until the FNS tab
# toggle joined it (v3.2.30): a toggle is useless without value changes,
# so `valuechange` is on and the project toggles ride the same DAT. The
# roaming ROOT_TOGGLES stay off it -- nothing acts on them at the moment
# they change, they are read when a pass runs.
check('the forwarder carries the entry points and the project toggles',
      "pe.par.pars = ' '.join(n for n, _, _ in ROOT_ENTRY_POINTS + ROOT_PROJECT_TOGGLES)" in gsrc
      and 'pe.par.valuechange = True' in gsrc)

print('5. the welcome asks before it opens anything')
w = gen['WELCOME_EXEC_TEXT']
i_shown = w.index('root.store(FLAG, "shown")')
i_auto = w.index('if _setUpLikeLastTime(root):')
i_pick = w.index('par = getattr(root.par, "Picktools", None)')
check('flag first, then the silent rail, then (only if it declined) Pick Tools',
      i_shown < i_auto < i_pick)
check('it consults the installer module (file-backed read), then the promoted rail',
      'module.AutoSetupWanted(root)' in w and 'InstallLastSetup(confirm=True)' in w)
check('anything short of a started install falls through to the picker',
      'return False' in w[w.index('def _setUpLikeLastTime'):w.index('def _isDev')]
      and '-- opening Pick Tools' in w)

print()
if FAILS:
    print('FAILED: %d check(s)' % len(FAILS))
    raise SystemExit(1)
print('all auto-setup checks pass')
