"""The root's Pick Tools pulse must reach the installer's own picker on a
fresh install.

Field report, 2026-09-16, fresh TouchDesigner, bootstrap from the website:
no picker, an empty browser address, no core, and one textport line --

    FNSTools: console did not open -- FNS_Console is not installed --
    it serves the settings page now

The bootstrap root ships an FNS_ConfigHost, and a host promotes the config
registry into /sys when it initialises. So on every fresh drop
op.FNS_CONFIGREGISTRY resolves while FNS_Console does not, the registry's
OpenSettingsUI forward refuses, and the root used to treat ANY reply as
handled. The installer was never asked. Development never showed it,
because the dev project always has a console.

This runs the GENERATED handler (ROOT_PULSE_TEXT) outside TouchDesigner
against fakes of exactly that state, so the rule is pinned where the bug
lived: only a console that says it opened counts as handled.

    python tests/test_root_pulses.py
"""
import io
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(_ROOT, 'packaging', 'build_installer.py')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


ns = {'__name__': 'build_installer_under_test'}
exec(compile(io.open(GEN, encoding='utf-8').read(), GEN, 'exec'), ns)
TEXT = ns['ROOT_PULSE_TEXT']


class _Pulse:
    def __init__(self):
        self.count = 0

    def pulse(self):
        self.count += 1


class _Installer:
    def __init__(self):
        self.par = type('P', (), {})()
        self.par.Configure = _Pulse()


class _Root:
    def __init__(self, installer):
        self._inst = installer

    def op(self, name):
        return self._inst if name == ns['COMP_NAME'] else None


class _Shortcuts:
    """Stands in for td.op: only the shortcuts given exist."""
    def __init__(self, **found):
        self.__dict__.update(found)


class _Answers:
    def __init__(self, reply):
        self.reply = reply
        self.calls = 0

    def Open(self, tab=None, panel=True):
        self.calls += 1
        return self.reply

    def OpenSettingsUI(self, tab=None, panel=True):
        self.calls += 1
        return self.reply


def press(shortcuts, installer):
    """Run the generated onPulse for Pick Tools; return the log lines."""
    log = []
    g = {'op': shortcuts,
         'parent': lambda: _Root(installer),
         'debug': lambda *a: log.append(' '.join(str(x) for x in a))}
    exec(compile(TEXT, 'ROOT_PULSE_TEXT', 'exec'), g)
    g['onPulse'](type('Par', (), {'name': 'Picktools'})())
    return log


REFUSAL = {'ok': False,
           'why': 'FNS_Console is not installed -- it serves the settings page now'}

print('1. the field report: a fresh drop, registry in /sys, no console')
inst = _Installer()
reg = _Answers(REFUSAL)
press(_Shortcuts(FNS_CONFIGREGISTRY=reg), inst)
check('the config registry was asked first', reg.calls == 1, reg.calls)
check("its refusal falls through to the installer's picker",
      inst.par.Configure.count == 1, inst.par.Configure.count)

print('2. nothing promoted into /sys at all')
inst = _Installer()
press(_Shortcuts(), inst)
check("the installer's picker opens", inst.par.Configure.count == 1)

print('3. a console that opens is the answer')
inst = _Installer()
con = _Answers({'ok': True, 'url': 'http://127.0.0.1:36710/#tools', 'shown': True})
press(_Shortcuts(FNS_CONSOLE=con), inst)
check('the console was asked', con.calls == 1)
check('and the installer is left alone', inst.par.Configure.count == 0,
      inst.par.Configure.count)

print('4. a console that refuses is not an answer either')
inst = _Installer()
press(_Shortcuts(FNS_CONSOLE=_Answers({'ok': False, 'why': 'no page'})), inst)
check("the installer's picker opens", inst.par.Configure.count == 1)

print('5. nowhere to go is reported, never raised')
try:
    log = press(_Shortcuts(FNS_CONFIGREGISTRY=_Answers(REFUSAL)), None)
    check('no exception inside the pulse callback', True)
    check('the textport says why', any('no installer' in l for l in log), log)
except Exception as e:
    check('no exception inside the pulse callback', False, e)

print()
if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    raise SystemExit(1)
print('all root pulse checks pass')
