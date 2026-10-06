"""The site's download buttons point at latest/, and nothing rewrites them.

Field report 2026-09-17: a fresh FNSTools.tox drop was still the previous
build. The homepage shipped its buttons on `latest/` but upgraded every
href on load to the pinned release path, for reproducible URLs. A release
path is immutable, so a tab opened before a release kept handing out the
old bootstrap however often it was clicked, and only a page refresh fixed
it. The pinned URL stays published (the manifest, the docs); the buttons
stay on the alias that cannot go stale.

    python tests/test_site_download_links.py
"""
import io
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANDING = os.path.join(_ROOT, 'website', 'index.html')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


html = io.open(LANDING, encoding='utf-8').read()

print('1. every download button is the mutable alias')
hrefs = re.findall(r'<a[^>]*class="[^"]*js-fns-download[^"]*"[^>]*href="([^"]+)"', html)
hrefs += re.findall(r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*js-fns-download[^"]*"', html)
check('the page has download buttons', len(hrefs) >= 3, hrefs)
check('all of them are latest/FNSTools.tox',
      all(h == 'https://storage.functionstore.tools/fnstools/latest/FNSTools.tox' for h in hrefs), hrefs)
check('no button links a pinned release path',
      not re.search(r'js-fns-download[^>]*storage\.functionstore\.tools/fnstools/v\d', html))

print('2. nothing rewrites an href at runtime')
check('no script assigns a.href for the download or installer buttons',
      "a.href = base + '/' + m.release" not in html
      and '.js-fns-installer' not in html)
check('the manifest fetch remains, for the tool count',
      "fetch(BASE + '/manifest.json'" in html and ".js-fns-count" in html)
check('the reason is written down where the script is',
      'A release path is immutable' in html)

print()
if FAILS:
    print('%d check(s) failed:' % len(FAILS))
    for f in FAILS:
        print('  - ' + f)
    raise SystemExit(1)
print('all site download-link checks pass')
