"""Tests for the community recommendations list.

This list publishes straight to every install with no release in between,
so there is no build step in which a bad row would be noticed -- the
publish IS the review, which is why the validator has to be right.

Two things are checked that nothing else can catch:

  * PACKAGE-SHAPED FIELDS ARE REFUSED. This is the failure that would not
    look like a failure: someone pastes a manifest row in, nothing
    complains, and later something downstream treats a third-party link as
    an installable package.
  * THE TWO VALIDATORS AGREE. The CMS refuses rows in JavaScript and the
    publisher refuses them in Python. If they drift, a save looks fine and
    the upload fails hours later, which is the worst place to find out.

    python tests/test_recommendations.py
"""
import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, 'packaging'))
import recommendations as rec           # noqa: E402

FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        print('  FAIL  %s  %s' % (label, detail))
        FAILS.append(label)


def row(**kw):
    base = {'name': 'Thing', 'author': 'Someone',
            'url': 'https://example.com/thing'}
    base.update(kw)
    return base


def doc(*rows, **kw):
    d = {'schema': rec.SCHEMA, 'intro': '', 'tools': list(rows)}
    d.update(kw)
    return d


print('recommendations')

print('\n1. the shipped file is valid')
live = rec.load(_ROOT)
check('packaging/recommendations.json validates', rec.validate(live) == [],
      rec.validate(live))
check('  it is a list, not a mapping', isinstance(live.get('tools'), list))

print('\n2. required fields')
check('a complete row passes', rec.validate(doc(row())) == [])
for f in ('name', 'author', 'url'):
    r = row()
    del r[f]
    check('missing %s is refused' % f,
          any(f in p for p in rec.validate(doc(r))))

print('\n3. package-shaped fields are REFUSED, not ignored')
for f, v in (('version', '1.0.0'), ('requires', []),
             ('artifact', {}), ('access', 'free'), ('Pkgversion', '1.0.0'),
             ('kind', 'tool'), ('seats', 3)):
    problems = rec.validate(doc(row(**{f: v})))
    check('`%s` is refused' % f, any(f in p for p in problems), problems)
check('  the refusal explains why',
      any('not a package' in p for p in rec.validate(doc(row(version='1')))))

print('\n3b. placement fields travel together, and need a pinned hash')
SHA = 'a' * 64
TOX = 'https://example.com/thing.tox'
ok_row = row(tox_url=TOX, sha256=SHA, bytes=1234)
check('a fully pinned row passes', rec.validate(doc(ok_row)) == [],
      rec.validate(doc(ok_row)))
check('  and is installable', rec.installable(ok_row))
check('a link-only row is NOT installable', not rec.installable(row()))
check('tox_url without sha256 is refused',
      any('pinned sha256' in p for p in
          rec.validate(doc(row(tox_url=TOX, bytes=1)))))
check('sha256 without tox_url is refused',
      any('without tox_url' in p for p in rec.validate(doc(row(sha256=SHA)))))
check('tox_url without bytes is refused',
      any('bytes' in p for p in rec.validate(doc(row(tox_url=TOX, sha256=SHA)))))
check('http tox_url is refused',
      any('https' in p for p in rec.validate(
          doc(row(tox_url='http://x.com/a.tox', sha256=SHA, bytes=1)))))
check('a tox_url that is not a .tox is refused',
      any('.tox' in p for p in rec.validate(
          doc(row(tox_url='https://x.com/a.zip', sha256=SHA, bytes=1)))))
check('a short hash is refused',
      any('64' in p for p in rec.validate(
          doc(row(tox_url=TOX, sha256='abc', bytes=1)))))
check('bytes must be a real integer, not a bool',
      any('positive integer' in p for p in rec.validate(
          doc(row(tox_url=TOX, sha256=SHA, bytes=True)))))

print('\n4. links must be https')
check('http url refused',
      any('https' in p for p in rec.validate(doc(row(url='http://x.com/a')))))
check('http author_url refused',
      any('https' in p for p in
          rec.validate(doc(row(author_url='http://x.com')))))
check('https passes', rec.validate(doc(row(author_url='https://x.com'))) == [])

print('\n5. hygiene')
check('duplicate names refused',
      any('duplicate' in p for p in
          rec.validate(doc(row(name='A'), row(name='a')))))
check('unknown field refused',
      any('unknown field' in p for p in rec.validate(doc(row(colour='red')))))
check('over-long description refused',
      any('max' in p for p in rec.validate(doc(row(description='x' * 401)))))
check('wrong schema refused', any('schema' in p for p in
                                  rec.validate(doc(row(), schema=99))))

print('\n6. what actually gets published')
pub = rec.published(doc(row(description='hi', note='n'),
                        intro='Some intro'))
check('drops the editor _comment block', '_comment' not in pub)
check('keeps intro', pub['intro'] == 'Some intro')
check('keeps the curated fields',
      set(pub['tools'][0]) == {'name', 'author', 'url', 'description', 'note'},
      set(pub['tools'][0]))

print('\n7. the CMS validator agrees with this one')
cms = open(os.path.join(_ROOT, 'website', 'tools', 'cms.mjs'),
           encoding='utf-8').read()
m = re.search(r"const REC_FIELDS = \[(.*?)\];", cms, re.S)
check('cms.mjs declares REC_FIELDS', m is not None)
if m:
    js_fields = set(re.findall(r"'(\w+)'", m.group(1)))
    check('  same allowed fields as Python', js_fields == rec.ALLOWED,
          '%s vs %s' % (sorted(js_fields), sorted(rec.ALLOWED)))
check('cms.mjs requires the same three',
      "['name', 'author', 'url']" in cms)
check('cms.mjs enforces https', "startsWith('https://')" in cms)
check('cms.mjs enforces the description cap', '> 400' in cms)
check('cms.mjs enforces the pinned hash', 'needs a pinned sha256' in cms)
check('cms.mjs enforces hex64', 'HEX64.test' in cms)

print('\n8. the pin endpoint')
check('pins with sha256', "createHash('sha256')" in cms)
check('refuses non-https / non-.tox',
      "startsWith('https://')" in cms and "endsWith('.tox')" in cms)
# An HTML error page served with a 200 is the common failure, and pinning
# one would record a hash for a web page as if it were the tool.
check('refuses an HTML body served as 200', "startsWith('<')" in cms)
check('refuses an empty body', 'empty file' in cms)
check('records what it saw', 'pinned_at' in cms and 'bytes: buf.length' in cms)

html = open(os.path.join(_ROOT, 'website', 'tools', 'cms.html'),
            encoding='utf-8').read()
check('the editor offers Pin', 'data-pin' in html and 'pinTool' in html)
# A pin belongs to one url; keeping it across an edit would mean a hash
# for bytes the row no longer points at.
check('changing tox_url drops the pin',
      "delete t.sha256" in html and "f === 'tox_url'" in html)

print()
if FAILS:
    print('%d FAILED: %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all checks passed')
