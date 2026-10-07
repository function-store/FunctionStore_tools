"""Hover text rides data-tip, never `title`.

TouchDesigner's Web Render (CEF) never draws a native title tooltip, so a
card whose description is clamped to two lines had no way to show the
rest (field report, 2026-09-16). base.js draws one element for every
[data-tip] on the page and is inlined into both web shells by
sync_base.py, so a `title` anywhere in them is a tooltip nobody in
TouchDesigner will ever see.

    python tests/test_tooltips.py
"""
import io
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHELLS = ('packaging/configurator/index.html',
          'modules/suspects/FNSTools/FNS_Console/console_page.html')
BASE_JS = os.path.join(_ROOT, 'packaging', 'configurator', 'base.js')
BASE_CSS = os.path.join(_ROOT, 'packaging', 'configurator', 'base.css')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


def read(rel):
    with io.open(os.path.join(_ROOT, *rel.split('/')), encoding='utf-8') as f:
        return f.read()


print('1. no native title tooltips in either shell')
for rel in SHELLS:
    src = read(rel)
    # an <iframe title> is its accessible name, not a tooltip; the dialog
    # heading's id is dlgtitle; a JS property named .title on data is fine
    attrs = [m.group(0) for m in re.finditer(r'<(?!iframe)[a-z]+[^>]*\stitle="', src)]
    props = re.findall(r'\b[a-zA-Z_]+\.title = ', src)
    check('%s: no title= attribute on any element but <iframe>' % rel, not attrs, attrs[:3])
    check('%s: no element.title = assignment' % rel, not props, props[:3])

print('2. both shells carry the synced base.js block, and it is base.js')
js = io.open(BASE_JS, encoding='utf-8').read()
for rel in SHELLS:
    src = read(rel)
    m = re.search(r'/\* FNS:UIBASEJS:START.*?\*/\n(.*?)\n/\* FNS:UIBASEJS:END \*/', src, re.S)
    check('%s: FNS:UIBASEJS block present' % rel, m is not None)
    check('%s: block is the current base.js' % rel,
          m is not None and m.group(1) == js.strip('\n'))

print('3. the tooltip itself')
check('delegated: one listener, every [data-tip]',
      "closest('[data-tip]')" in js and "addEventListener('mouseover'" in js)
check('a short delay, follows the cursor, stays inside the viewport',
      'DELAY = 350' in js and "addEventListener('mousemove'" in js
      and 'window.innerWidth' in js and 'window.innerHeight' in js)
check('inside an open modal dialog it joins the dialog (the top layer covers body)',
      "closest('dialog[open]')" in js)
check('keyboard focus shows it, a click does not',
      "addEventListener('focusin'" in js and 'lastPress' in js)
check('text is set as text, never markup', 'textContent = text' in js and 'innerHTML' not in js)
css = io.open(BASE_CSS, encoding='utf-8').read()
check('base.css styles it with pre-line, so "Adds: ..." keeps its break',
      re.search(r'\.fns-tip \{[^}]*white-space: pre-line', css, re.S) is not None)
check('it never eats the pointer', re.search(r'\.fns-tip \{[^}]*pointer-events: none', css, re.S) is not None)

print('4. the card')
idx = read(SHELLS[0])
check('a card\'s tip is its full description plus what it adds',
      re.search(r"el\.setAttribute\('data-tip', \(p\.description \|\| ''\)\s*\n\s*\+ \(surf\.length", idx)
      is not None)
check('the description clamp still points at the tip',
      "the full text rides the card's data-tip" in idx)

print()
if FAILS:
    print('FAILED: %d check(s)' % len(FAILS))
    raise SystemExit(1)
print('all tooltip checks pass')
