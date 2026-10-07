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

print('4. a toolkit that did not land under the mouse is revealed (owner, 2026-09-16)')
# Two rails put the toolkit somewhere the user was not looking: the
# relocation of a nested drop, and the paste rail's loadTox straight into
# /. Both looked as if the drop vanished, and both left it on top of
# whatever sat at its stored position. reveal() on the welcome DAT is the
# one answer: above the topmost operator, the pane moved there, selected.
reloc = m.group(1) if m else ''
rv = re.search(r'\ndef reveal\(root, home_path=None\):\n(.*?)\n\n_RELOCATE', text, re.S)
check('reveal() is a module-level function of the welcome DAT (the paste rail calls it too)',
      rv is not None)
body = rv.group(1) if rv else ''
check('it sits 200 units above the topmost operator of its network, centred on it',
      'max(others, key=lambda c: c.nodeY + c.nodeHeight)' in body
      and 'root.nodeY = topmost.nodeY + topmost.nodeHeight + 200' in body
      and 'root.nodeCenterX = topmost.nodeCenterX' in body)
check('an empty network leaves the position alone', 'if others:' in body)
check('only panes that showed the drop network move (the current pane as fallback)',
      'pane.owner.path == home_path' in body and 'ui.panes.current' in body)
check('the pane goes to the network and homes on the toolkit without zooming',
      'pane.owner = dest' in body and 'pane.home(zoom=False, op=root)' in body)
check('the toolkit is selected and made current, nothing else stays selected',
      'root.selected = True' in body and 'root.current = True' in body
      and 'c.selected = False' in body)
check('the network the drop landed in is read BEFORE the original is destroyed',
      re.search(r'home_path = old\.parent\(\)\.path.*?\n\s*old\.destroy\(\)', reloc, re.S)
      is not None)
check('the relocation reveals the copy through its own welcome DAT, before re-arming',
      'we.module.reveal(new, home_path)' in reloc
      and reloc.index('we.module.reveal(new, home_path)') < reloc.index('args[0].module.welcome()'))
check('a reveal failure is logged, never fatal to the welcome',
      re.search(r'try:\n\s*we\.module\.reveal\(new, home_path\)\n\s*except Exception as e:\n\s*debug\(',
                reloc) is not None)

print('5. the paste rail reveals the toolkit it loaded into /')
PAGE = os.path.join(_ROOT, 'packaging', 'configurator', 'index.html')
page = io.open(PAGE, encoding='utf-8').read()
check('right after loadTox, through the welcome DAT, guarded for an older bootstrap',
      re.search(r'''"root = op\('/'\)\.loadTox\(f\)",\n'''
                r'''\s*"root\.store\('FNS_welcomed', 'paste'\)",\n'''
                r'''\s*"w_ = root\.op\('exec_root_welcome'\)",\n'''
                r'''\s*"_ = w_ is not None and hasattr\(w_\.module, 'reveal'\) and w_\.module\.reveal\(root\)",''',
                page) is not None)

print()
if FAILS:
    print('FAILED: %d check(s)' % len(FAILS))
    raise SystemExit(1)
print('all bootstrap welcome checks pass')
