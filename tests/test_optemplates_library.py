"""OpTemplates finds the library a user already has before seeding defaults.

Field report 2026-09-25: an older user upgrading to the new FNSTools could
not find their templates. The automatic path covered one case only (the
palette folder renamed, `OPTemplates1.tox` loaded). It missed the `_2023`
copy TouchDesigner 2023 saved to, an `OPTemplates<N>.tox` from the old
"Create New" choice, and a file the palette migration had set aside. Worse,
a missing library was seeded from the shipped defaults, which then hid all
of those.

adoptExistingLibrary() runs before any seed: when the file is missing, when
it holds a seed (a `.seeded` sidecar), and once per machine (the
`.library_checked` marker). It copies the newest candidate in and keeps what
it replaces as `<name>.before-adopt.tox`. Pure file logic, so this runs it
on scratch folders with the helpers pulled out of OpTemplateExt.py.

Verified live 2026-09-25 on the dev machine, which had exactly case 1: a
2024 `OPTemplates1.tox` and a 2026 `OPTemplates1_2023.tox`. The 2026 set
was adopted and the 2024 file kept as `OPTemplates1.before-adopt.tox`.

    python tests/test_optemplates_library.py
"""
import io
import os
import re
import shutil
import tempfile
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'OpTemplates', 'OpTemplateExt.py')
FAILS = []


def check(label, cond, detail=''):
    print(('  PASS  ' if cond else '  FAIL  ') + label + ('' if cond else '   ' + str(detail)))
    if not cond:
        FAILS.append(label)


text = io.open(SRC, encoding='utf-8').read()
start = text.index('LIBRARY_FILE_RE = ')
end = text.index('def fnsLog(')
ns = {'os': os, 're': re, 'shutil': shutil}
exec(compile(text[start:end], 'optemplates-library', 'exec'), ns)
adopt, seedMarker = ns['adoptExistingLibrary'], ns['seedMarker']


def scratch():
    d = tempfile.mkdtemp(prefix='fns-optemplates-').replace('\\', '/')
    return d + '/FNSTools/OpTemplates', d + '/FNSTools/legacy_FNStools_ext/OpTemplates'


def put(path, text, age=0):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(text)
    t = time.time() - age
    os.utime(path, (t, t))


def read(path):
    with open(path) as f:
        return f.read()


print('1. case 1: a newer _2023 copy beside an old OPTemplates1.tox')
folder, legacy = scratch()
target = folder + '/OPTemplates1.tox'
put(target, 'old 2024 set', age=3000)
put(folder + '/OPTemplates1_2023.tox', 'current 2023 set', age=100)
put(folder + '/OPTemplates2023xxx.tox', 'not a library name', age=10)
got = adopt(target, folder, legacy)
check('the newest library is adopted', read(target) == 'current 2023 set', read(target))
check('what it replaced is kept beside it', read(folder + '/OPTemplates1.before-adopt.tox') == 'old 2024 set')
check('the source stays where it was', read(folder + '/OPTemplates1_2023.tox') == 'current 2023 set')
check('only OPTemplates<N>[_2023].tox names count', got.endswith('OPTemplates1_2023.tox'), got)
check('the machine is marked checked', os.path.exists(folder + '/.library_checked'))
put(folder + '/OPTemplates1_2023.tox', 'saved again in 2023', age=0)
adopt(target, folder, legacy)
check('once checked, an existing library is left alone', read(target) == 'current 2023 set')

print('2. case 2: an OPTemplates<N>.tox from "Create New", no OPTemplates1.tox')
folder, legacy = scratch()
target = folder + '/OPTemplates1.tox'
put(folder + '/OPTemplates2.tox', 'created new', age=50)
adopt(target, folder, legacy)
check('it becomes the library', read(target) == 'created new')

print('3. case 6: a file the migration kept aside, and a seeded target')
folder, legacy = scratch()
target = folder + '/OPTemplates1.tox'
put(target, 'shipped defaults', age=0)
put(seedMarker(target), 'seeded')
put(folder + '/.library_checked', 'x')
put(legacy + '/OPTemplates1.tox', 'the user library', age=5000)
adopt(target, folder, legacy)
check('a seed is replaced even though the machine was checked', read(target) == 'the user library')
check('the seed marker goes with it', not os.path.exists(seedMarker(target)))

print('4. nothing to adopt')
folder, legacy = scratch()
target = folder + '/OPTemplates1.tox'
check('a fresh machine adopts nothing and creates nothing', adopt(target, folder, legacy) is None
      and not os.path.exists(target) and not os.path.exists(folder))
folder, legacy = scratch()
target = folder + '/OPTemplates1.tox'
put(target, 'mine', age=0)
put(folder + '/OPTemplates1_2023.tox', 'older 2023', age=900)
check('an up-to-date library is kept on the first check', adopt(target, folder, legacy) is None
      and read(target) == 'mine' and not os.path.exists(folder + '/OPTemplates1.before-adopt.tox'))

print('5. the wiring in OpTemplateExt')
check('applyScope looks before it seeds',
      text.index('adopted = adoptExistingLibrary(path, self.extFolder, legacy_dir)')
      < text.index("fnsLog(f'OpTemplates: created the global library {path} from {seed.path}')"))
check('only a seed from the shipped base is marked', 'if seed is base:' in text
      and 'with open(seedMarker(path), \'w\') as f:' in text)
check('an adoption reloads the base', 'if not wired or adopted or (prompt and prev == \'project\'):' in text)
check('every save clears the seed marker', text.count('clearSeedMark(') == 4)

print()
if FAILS:
    print('FAILED: %d check(s)' % len(FAILS))
    raise SystemExit(1)
print('all optemplates-library checks pass')
