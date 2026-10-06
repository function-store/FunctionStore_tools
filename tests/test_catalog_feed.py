"""The site publishes /catalog.json, the tool feed functionstore.xyz reads.

docs/PortfolioCatalogFeed.md. The portfolio renders its Tools section from
this document instead of a Notion database, so the wiring that produces it
is pinned here: written after the last refusal gate, gitignored, served
with CORS, named in the README, and -- when a local build has produced it --
consistent with the catalog (counts add up, no preview package leaks, every
url is a docs page on this site).

    python tests/test_catalog_feed.py
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []


def check(label, ok, detail=''):
    print(('  PASS  ' if ok else '  FAIL  ') + label + ('' if ok else '   ' + str(detail)[:200]))
    if not ok:
        FAILS.append(label)


def read(*parts):
    return io.open(os.path.join(ROOT, *parts), encoding='utf-8').read().replace('\r\n', '\n')


site = read('website', 'tools', 'build-site.mjs')
print('1. the build')
check('writes website/catalog.json', "path.join(WEB, 'catalog.json')" in site)
check('after the last refusal gate (the /get/ page)',
      site.index("path.join(WEB, 'catalog.json')") > site.index("built /get/"))
check('declares schema 1', 'schema: 1,' in site)
check('previews are already filtered (built from `pages`)',
      "const tools = displayCategories.flatMap((cat) => pages" in site)
check('urls are absolute docs pages', "url: abs(`/docs/${p.slug}/`)," in site)
check('access is the two-word vocabulary', "access: isPlus(p.name) ? 'patreon' : 'free'," in site)

print('2. the surfaces')
check('the output is not committed', '/catalog.json' in read('website', '.gitignore').split('\n'))
vercel = json.loads(read('website', 'vercel.json'))
cors = [h for h in vercel.get('headers', []) if h.get('source') == '/catalog.json']
check('vercel.json has a header rule for it', len(cors) == 1, cors)
if cors:
    hdrs = {h['key']: h['value'] for h in cors[0]['headers']}
    check('sent with Access-Control-Allow-Origin: *', hdrs.get('Access-Control-Allow-Origin') == '*', hdrs)
    check('cached briefly, never immutable',
          'max-age=' in hdrs.get('Cache-Control', '') and 'immutable' not in hdrs.get('Cache-Control', ''), hdrs)
check('the README names it', 'catalog.json' in read('website', 'README.md'))
doc = read('docs', 'PortfolioCatalogFeed.md')
check('the contract is in force', doc.startswith('---\nstatus: in-force\n'))

print('3. a local build, when there is one')
feed_path = os.path.join(ROOT, 'website', 'catalog.json')
if not os.path.exists(feed_path):
    print('  SKIP  website/catalog.json not built here (cd website && node tools/build-site.mjs)')
else:
    feed = json.loads(read('website', 'catalog.json'))
    catalog = json.loads(read('packaging', 'catalog.json'))
    tools = feed.get('tools') or []
    check('schema 1', feed.get('schema') == 1, feed.get('schema'))
    check('has tools', len(tools) > 0)
    check('counts.tools matches', feed['counts']['tools'] == len(tools), feed['counts'])
    check('counts.free + counts.patreon = tools',
          feed['counts']['free'] + feed['counts']['patreon'] == len(tools), feed['counts'])
    check('counts.categories matches', feed['counts']['categories'] == len(feed['categories']))
    check('category counts add up', sum(c['count'] for c in feed['categories']) == len(tools))
    required = ('name', 'title', 'slug', 'url', 'category', 'description', 'access')
    check('every tool has the required fields',
          all(all(k in t for k in required) for t in tools))
    check('every url is a docs page on the site',
          all(t['url'].startswith(feed['site'] + '/docs/') and t['url'].endswith('/') for t in tools))
    check('access is free or patreon', all(t['access'] in ('free', 'patreon') for t in tools))
    previews = {n for n, p in catalog['packages'].items() if p.get('preview') is True}
    leaked = sorted(previews & {t['name'] for t in tools})
    check('no preview package leaks', not leaked, leaked)
    known = {n for n, p in catalog['packages'].items() if p.get('preview') is not True}
    check('every non-preview package is present', known == {t['name'] for t in tools},
          sorted(known ^ {t['name'] for t in tools}))
    check('every tool category is a listed category',
          {t['category'] for t in tools} <= {c['name'] for c in feed['categories']})
    check('gated tools carry an unlock sentence',
          all(t['unlock'] for t in tools if t['access'] == 'patreon'))
    check('free tools carry none', all(not t['unlock'] for t in tools if t['access'] == 'free'))
    check('titles are public names', not any(t['title'].startswith('FNS_') for t in tools))
    check('family cards come along', isinstance(feed.get('family'), list) and len(feed['family']) >= 1)

print()
if FAILS:
    print('%d FAILED: %s' % (len(FAILS), '; '.join(FAILS)))
    raise SystemExit(1)
print('all passed')
