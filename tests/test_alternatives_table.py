"""Op alternatives live in a table the content CMS can edit.

docs/OpAlternatives.md, "The list lives in a table". The eight tools that
offer themselves keep their operator types in an `alternatives` table
(type | label | help) and share one onAlternatives() reader; FNS_CMS reads
and writes the table for the CMS field. Verified live 2026-09-25: the
registry offered the same alternatives after the move, a write added and
removed limitCHOP on ChopProcess, a bad type was refused, and OpTemplates
refused a write (its list is computed).

    python tests/test_alternatives_table.py
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = ['ChopBank', 'ChopProcess', 'ConstantCHOP', 'ExpressionPOP', 'FeedbackDisplace',
         'FNS_RandomCHOP', 'PrismTOP', 'ThresholdColor']
FAILS = []


def check(label, ok, detail=''):
    print(('  PASS  ' if ok else '  FAIL  ') + label + ('' if ok else '   ' + str(detail)[:200]))
    if not ok:
        FAILS.append(label)


def read(*parts):
    return io.open(os.path.join(ROOT, *parts), encoding='utf-8').read().replace('\r\n', '\n')


print('1. one reader in every tool')
reader = None
for n in TOOLS:
    s = read('modules', 'suspects', 'FNSTools', n, 'opmenu_callbacks.py')
    i = s.index('def onAlternatives():')
    j = s.find('\ndef ', i + 5)
    body = s[i:j if j >= 0 else len(s)].rstrip()
    reader = reader or body
    check('%s reads its alternatives table' % n,
          "t = me.parent().op('alternatives')" in body and body == reader)

print('2. FNS_CMS reads and writes it')
cms = read('FNS_CMS', 'CmsExt.py')
check('both routes are served', "('POST', '/api/altread')" in cms and "('POST', '/api/altwrite')" in cms)
check('a write validates the types like the manifest build', "bm['ALT_TYPE_RE'].match(x)" in cms)
check('a write saves the tool', 'pi.Save(comp)' in cms[cms.index('def _apiAltWrite'):])
check('a computed list is refused', 'its list is computed by the tool' in cms)
check('reads answer with what a release would publish', "bm['AlternativesFor'](comp)" in cms)

print('3. the CMS field')
html = read('website', 'tools', 'cms.html')
check('reads the tool, writes the tool', "api('/api/td/altread'" in html and "api('/api/td/altwrite'" in html)
check('a computed list is read-only', 'Computed by the tool (read-only here)' in html)
check('bound with the family section', 'bindFamily(d);\n  bindAlternatives(d);' in html)
check('Save writes a changed list to the tool (no separate button)',
      'wroteAlt = await saveAlternatives(saved.name);' in html and 'id="alt-write"' not in html
      and '|| altChanged();' in html)

if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all alternatives-table checks pass')
