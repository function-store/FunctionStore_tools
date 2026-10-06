"""The toolkit root's FNSTools page carries only its entry points.

Owner decision 2026-09-17: the Installer Parameters pulse (Openinstaller),
which opened FNS_Installer's own parameter dialog, does not belong on the
top-level page. It is gone from the entry points and the forwarder, and
EnsureRootEntryPoints removes it from roots that still carry it (a pulse,
so nothing a user set is lost). Verified live on the dev root: removed on
the first run, nothing on the second.

    python tests/test_root_entry_points.py
"""
import ast
import io
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BI = os.path.join(_ROOT, 'packaging', 'build_installer.py')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


src = io.open(BI, encoding='utf-8').read()
ns = {}
exec(re.search(r"^COMP_NAME = .*$", src, re.M).group(0), ns)
exec(src[src.index('ROOT_ENTRY_POINTS = ('):src.index('# Toggles beside the pulses')], ns)
start = src.index('ROOT_PULSE_TEXT = (')
exec(src[start:src.index('\n\n', src.index('% (COMP_NAME, COMP_NAME))', start))], ns)

print('1. the entry points')
names = [n for n, _, _ in ns['ROOT_ENTRY_POINTS']]
check('Pick Tools and Open Settings are the root pulses', names == ['Picktools', 'Opensettings'], names)
check('Installer Parameters is not one of them', 'Openinstaller' not in names)
check('it is retired, so existing roots lose it', ns['ROOT_RETIRED_PARS'] == ('Openinstaller',))

print('2. the forwarder')
text = ns['ROOT_PULSE_TEXT']
check('the generated forwarder parses', ast.parse(text) is not None)
check('it no longer handles or mentions Openinstaller',
      'Openinstaller' not in text and 'Installer Parameters' not in text)
check('Pick Tools still falls back to the installer\'s own picker', 'inst.par.Configure.pulse()' in text)

print('3. retirement is safe')
check('only a custom PULSE is destroyed (never a par holding a value)',
      "if par is not None and par.isCustom and par.style == 'Pulse':" in src)
check('EnsureRootEntryPoints reports what it retired', "'retired': retired," in src)

print()
if FAILS:
    print('%d check(s) failed:' % len(FAILS))
    for f in FAILS:
        print('  - ' + f)
    raise SystemExit(1)
print('all root entry-point checks pass')
