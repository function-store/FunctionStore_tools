"""/about/: who makes the toolkit, a link to the portfolio, and a Mission
section that stays out of the page until it is written.

website/README.md, "About". Pinned here so the page cannot quietly lose its
nav entry, its build step or the rule that keeps an empty heading off the
site. When a local build exists, the built page is checked against the
fragment: the bio and the portfolio link are there, and the Mission section
is present exactly when the fragment has prose under it.

    python tests/test_about_page.py
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []


def check(label, ok, detail=''):
    print(('  PASS  ' if ok else '  FAIL  ') + label + ('' if ok else '   ' + str(detail)[:200]))
    if not ok:
        FAILS.append(label)


def read(*parts):
    return io.open(os.path.join(ROOT, *parts), encoding='utf-8').read().replace('\r\n', '\n')


site = read('website', 'tools', 'build-site.mjs')
landing = read('website', 'index.html')
fragment = read('website', 'content', 'about.html')

print('1. the fragment')
check('exists with a title', '<h1>About</h1>' in fragment)
check('links the portfolio', 'href="https://functionstore.xyz"' in fragment)
check('carries the Mission heading', '<h2 id="mission">Mission</h2>' in fragment)
check('no em-dash in the prose (house style)', '—' not in re.sub(r'<!--[\s\S]*?-->', '', fragment))

print('2. the build')
check('/about/ is built from the fragment', "['about', 'About | FNSTools'," in site)
check('an unwritten section is dropped', 'const dropUnwrittenSections' in site
      and 'const body = dropUnwrittenSections(raw);' in site)
check('the build says so when it drops one', 'has a heading with nothing written under it yet' in site)
check('About is in the generated header', "['/about/', 'About']," in site)
check('About is in the generated footer', '<a href="/about/">About</a>' in site)

print('3. the landing page')
check('About is in the hand-written header', landing.count('<a href="/about/">About</a>') >= 2)
check('the strip links /about/ and the portfolio',
      '<section id="made-by"' in landing and '<a href="/about/">About Function Store' in landing
      and 'href="https://functionstore.xyz"' in landing[landing.index('<section id="made-by"'):])
check('the output is not committed', '/about/' in read('website', '.gitignore').split('\n'))
check('the README explains the Mission rule', 'Mission section is left out until it is written' in read('website', 'README.md'))

print('4. a local build, when there is one')
built = os.path.join(ROOT, 'website', 'about', 'index.html')
if not os.path.exists(built):
    print('  SKIP  website/about/index.html not built here (cd website && node tools/build-site.mjs)')
else:
    page = read('website', 'about', 'index.html')
    check('the bio is on the page', 'Dan Molnar' in page and 'Function Store' in page)
    check('the portfolio link is on the page', 'href="https://functionstore.xyz"' in page)
    check('the page has the site chrome', '<header class="site">' in page and '<footer class="site">' in page)
    check('About is current in its own header', 'href="/about/" aria-current="page"' in page)
    # Mission: present on the page exactly when the fragment has prose under it.
    m = re.search(r'<h2 id="mission">Mission</h2>([\s\S]*?)(?=<h2\b|$)', fragment)
    under = re.sub(r'<!--[\s\S]*?-->', '', m.group(1)).strip() if m else ''
    if under:
        check('Mission is written, so it is published', 'id="mission"' in page)
    else:
        check('Mission is unwritten, so it stays off the page', 'id="mission"' not in page)
    check('the rest of the page survives the drop', 'id="elsewhere"' in page)

print()
if FAILS:
    print('%d FAILED: %s' % (len(FAILS), '; '.join(FAILS)))
    raise SystemExit(1)
print('all passed')
