"""The bootstrap's first-run welcome DAT must always be valid Python.

WELCOME_EXEC_TEXT is generated source shipped inside every bootstrap --
a syntax error there bricks the first run silently (the exec DAT just
never fires). It now carries a second level: the detached relocation
script (_RELOCATE) that moves a nested drop to /, which is itself
runtime-formatted. Both levels are parsed here, and the relocation
contract is pinned.

    python tests/test_bootstrap_welcome.py
"""
import ast
import io
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(_ROOT, 'packaging', 'build_installer.py')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


# Exec the generator OUTSIDE TouchDesigner: its top level is imports and
# constants only, so the template constants come out without a TD.
ns = {'__name__': 'build_installer_under_test'}
exec(compile(io.open(GEN, encoding='utf-8').read(), GEN, 'exec'), ns)
text = ns['WELCOME_EXEC_TEXT']

print('1. the welcome DAT parses')
try:
    ast.parse(text)
    check('WELCOME_EXEC_TEXT is valid Python', True)
except SyntaxError as e:
    check('WELCOME_EXEC_TEXT is valid Python', False, e)

print('2. the detached relocation script parses (tokens substituted)')
m = re.search(r"_RELOCATE = '''(.*?)'''", text, re.S)
check('the relocation script is present', m is not None)
if m:
    script = (m.group(1).replace('@PATH@', "'/somewhere/FNSTools'")
              .replace('@NAME@', "'FNSTools'"))
    try:
        ast.parse(script)
        check('_RELOCATE is valid Python once formatted', True)
    except SyntaxError as e:
        check('_RELOCATE is valid Python once formatted', False, e)

print('3. the relocation contract')
check('nested drops move home before welcoming',
      'home.path != "/"' in text and '@PATH@' in text)
check('no move over an installed toolkit (name collision at /)',
      re.search(r'dest\.op\(@NAME@\) is None', text) is not None)
check('the move is copy + destroy, detached',
      'dest.copy(old)' in text and 'old.destroy()' in text)
check('the copy is re-armed for the welcome (its own onCreate is inert)',
      re.search(r'new\.store\(.*?"pending"\)', text) is not None
      and 'args[0].valid and args[0].module.welcome()' in text)
check('the dev project never relocates',
      '_isDev' in text and 'IsDevProject' in text)
check('cannot tell = do not move', 'return True' in text)
check('the paste rail is never fought (only "pending" moves)',
      re.search(r'old\.fetch\(.*?\) == "pending"', text) is not None)

print()
if FAILS:
    print('FAILED: %d check(s)' % len(FAILS))
    raise SystemExit(1)
print('all bootstrap welcome checks pass')
