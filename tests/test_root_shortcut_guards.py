"""No source reaches the toolkit root, op.FNS, without a guard.

A tool shipped on its own has no /FNSTools root, so a bare op.FNS raises
there (or, in a parameter bind, reads EMPTY without raising -- the
Configscope lesson of 2026-09-08). Every use of the root in the sources must
sit inside a try block or behind hasattr/getattr. Registry globals
(op.FNS_*) are a tool's own shortcuts and are not policed here.

Docstrings are skipped (they may talk ABOUT op.FNS), comments are skipped,
and a line that itself carries the guard passes. The window for a try block
is the four lines above the use, which is how the shared fnsLog helper is
written.

    python tests/test_root_shortcut_guards.py
"""
import ast
import io
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIRS = ('modules/suspects', 'scripts', 'FNSTools')
ROOT_USE = re.compile(r"\bop\.FNS\b(?!_)")
GUARDED = re.compile(r"(hasattr|getattr)\(\s*op\s*,\s*['\"]FNS['\"]")
STRINGS = re.compile(r"'[^'\n]*'|\"[^\"\n]*\"")
TRY_WINDOW = 4
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


def docstring_lines(tree):
    """Line numbers covered by docstrings, so prose about op.FNS is not a use."""
    covered = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, 'body', None)
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], 'value', None), ast.Constant) \
                    and isinstance(body[0].value.value, str):
                for ln in range(body[0].lineno, body[0].end_lineno + 1):
                    covered.add(ln)
    return covered


def unguarded_uses(path):
    text = io.open(path, encoding='utf-8-sig').read()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []                                  # not a module (a DAT snippet); nothing to police here
    skip = docstring_lines(tree)
    lines = text.splitlines()
    out = []
    for i, line in enumerate(lines, 1):
        if i in skip:
            continue
        code = line.split('#', 1)[0]
        if GUARDED.search(code):
            continue
        code = STRINGS.sub("''", code)              # a string that TALKS about op.FNS is not a use
        if not ROOT_USE.search(code):
            continue
        window = ' '.join(lines[max(0, i - 1 - TRY_WINDOW):i - 1])
        if re.search(r"\btry\s*:", window):
            continue
        out.append((i, line.strip()[:100]))
    return out


sources = []
for d in SOURCE_DIRS:
    base = os.path.join(_ROOT, d)
    for dirpath, _dirs, files in os.walk(base):
        for fn in files:
            if fn.endswith('.py'):
                sources.append(os.path.join(dirpath, fn))

print('1. every op.FNS use in %d sources is guarded' % len(sources))
offenders = []
for p in sources:
    for ln, snippet in unguarded_uses(p):
        offenders.append('%s:%d  %s' % (os.path.relpath(p, _ROOT).replace(os.sep, '/'), ln, snippet))
check('no unguarded op.FNS', not offenders, '\n' + '\n'.join(offenders[:20]) if offenders else '')

print('2. the guard itself is recognised')
check('hasattr form passes', not GUARDED.search("x = 1") and bool(GUARDED.search("op.FNS.par.Configscope if hasattr(op, 'FNS') else 'project'")))
check('bare use is caught', bool(ROOT_USE.search("op.FNS.op('logger')")) and not ROOT_USE.search("op.FNS_UPDATER.par.x"))

if FAILS:
    print('\n%d check(s) failed' % len(FAILS))
    raise SystemExit(1)
print('\nall checks passed')
