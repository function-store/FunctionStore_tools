"""The website's /community/ section: other creators' tools as posts.

docs/CommunityHighlights.md, "The website". Verified by building with
three example rows on 2026-09-25 (a pinned tox with a post and an image, a
tdp package with a post, a link-only row): the index, both posts and the
landing strip rendered, a write-up without a row, a row without its
write-up and a relative image path each refused the build. This pins the
wiring so those rules cannot drift out.

    python tests/test_community_site.py
"""
import io
import os
import sys

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
check('reads the recommendations list', "path.join(REPO, 'packaging', 'recommendations.json')" in site)
check('write-ups live in website/content/community', "path.join(WEB, 'content', 'community')" in site)
check('a write-up needs a row', 'no row in packaging/recommendations.json has slug' in site)
check('a row with a slug needs its write-up', 'does not exist`' in site and 'has slug "${t.slug}"' in site)
check('a named image must exist', 'not found in website/content/community/images/' in site)
check('post images use the absolute path', 'must be /community/images/<file>' in site)
check('post links are checked like the docs', 'checkLinks(html, `content/community/${w.file}`, null);' in site)
check('credit comes before the write-up',
      site.index('${creditBox(t)}') < site.index('${p.html}', site.index('${creditBox(t)}')))
check('every post says it is not ours', 'Not part of FNSTools. ${esc(t.author)} made it and' in site)
check('newest first', "String(b.date || '').localeCompare(String(a.date || ''))" in site)

print('1b. drafts (owner, 2026-09-26: highlights are written before they go up)')
import importlib, sys as _sys
_sys.path.insert(0, os.path.join(ROOT, 'packaging'))
import recommendations as _rec
_doc = {'schema': 1, 'intro': '', 'tools': [
    {'name': 'A', 'author': 'x', 'url': 'https://a.example', 'draft': True},
    {'name': 'B', 'author': 'x', 'url': 'https://b.example'}]}
check('a draft row validates', _rec.validate(_doc) == [], _rec.validate(_doc))
check('draft must be a boolean', _rec.validate({'schema': 1, 'tools': [dict(_doc['tools'][0], draft='yes')]}) != [])
_pub = _rec.published(_doc)['tools']
check('installs never download a draft', [t['name'] for t in _pub] == ['B'] and 'draft' not in _pub[0])
check('the site leaves drafts out unless the local preview asks',
      "const highlights = (recommends.tools || []).filter((t) => SHOW_DRAFTS || t.draft !== true);" in site
      and "FNS_SHOW_DRAFTS: '1'" in read('website', 'tools', 'cms.mjs'))
check('a draft never reaches the committed landing strip',
      'const shown = highlights.filter((t) => t.draft !== true);' in site
      and 'prod-grid' not in site[site.index('const shown = highlights'):site.index('const shown = highlights') + 900])
check('a draft write-up is not an orphan', "const bySlug = new Map((recommends.tools || []).filter((t) => t.slug)" in site)
check('bad frontmatter is a refusal, not a crash', 'its frontmatter is not valid YAML' in site)
check('the CMS offers the Draft toggle', 'data-draft' in read('website', 'tools', 'cms.html'))

check('an unwritten section is left out, the written ones stay',
      "(?:(?!<\/h2>)[\s\S])*<\/h2>" in site)
check('Community is in the header menu', "['/community/', 'Community']," in site
      and '<a href="/community/">Community</a>' in read('website', 'index.html'))

print('1c. Built with TDFam (owner, 2026-09-28)')
import json as _j, subprocess as _s
_fam_doc = lambda fams: {'schema': 1, 'intro': '', 'tools': [
    {'name': 'T3D', 'author': 'Josef Pelz', 'url': 'https://www.patreon.com/JosefPelz/'}], 'families': fams}
good = [{'name': 'FNS', 'author': 'Function Store', 'url': '/docs/fns-opfamily/', 'ours': True},
        {'name': 'T3D', 'author': 'Josef Pelz', 'url': 'https://www.patreon.com/JosefPelz/', 'ops': 48, 'tool': 'T3D'}]
fam_cases = [good,
             [{'name': 'A', 'author': 'x', 'url': 'http://insecure'}],
             [{'name': 'A', 'author': 'x', 'url': 'https://a', 'tool': 'Nope'}],
             [{'name': 'A', 'author': 'x', 'url': 'https://a', 'ops': 0}],
             [{'name': 'A', 'author': 'x', 'url': 'https://a', 'ours': 'yes'}],
             [{'name': 'A', 'url': 'https://a'}],
             [{'name': 'A', 'author': 'x', 'url': 'https://a', 'image': 'x.png'}],
             [{'name': 'A', 'author': 'x', 'url': 'https://a'}, {'name': 'a', 'author': 'y', 'url': 'https://b'}]]
py_bad = [_rec.validate(_fam_doc(f)) != [] for f in fam_cases]
check('the family list validates, and bad rows are refused', py_bad == [False] + [True] * (len(fam_cases) - 1), py_bad)
check('installs never download the family list', 'families' not in _rec.published(_fam_doc(good)))
_cms = read('website', 'tools', 'cms.mjs')
_start = _cms.index('const REC_FIELDS')
_end = _cms.index('  return bad;\n}', _cms.index('function validateRecommends')) + len('  return bad;\n}')
_js = _cms[_start:_end] + ('\nconst cases = JSON.parse(require("fs").readFileSync(0, "utf8"));'
                           '\nconsole.log(JSON.stringify(cases.map((d) => validateRecommends(d).length > 0)));')
_out = _s.run(['node', '-e', _js], input=_j.dumps([_fam_doc(f) for f in fam_cases]), capture_output=True, text=True)
check('the CMS refuses exactly the same family rows', _out.returncode == 0 and _j.loads(_out.stdout) == py_bad,
      _out.stderr[-200:] or _out.stdout)
check('the site builds the section at /community/#tdfam', '<section class="cm-families" id="tdfam">' in site
      and 'const familiesBlock = families.length ?' in site)
check('FNS is counted from the release, previews left out',
      "return (m.packages || []).filter((p) => p.family && !p.preview).length;" in site)
check('a card opens its tool\'s post only when that post is published',
      "const href = post ? `/community/${post.t.slug}/` : f.url;" in site)
check('the CMS edits it', 'function familyRows()' in read('website', 'tools', 'cms.html')
      and "families: Array.isArray(body.families) ? body.families : (doc.families || [])," in _cms)

print('2. the surfaces')
landing = read('website', 'index.html')
check('the landing page carries the strip markers',
      '<!-- COMMUNITY:START -->' in landing and '<!-- COMMUNITY:END -->' in landing)
check('an empty list leaves no heading', "` : '\\n';" in site)
check('both footers link /community/', landing.count('href="/community/"') >= 1
      and '<a href="/community/">Community</a>' in site)
check('the output is not committed', '/community/' in read('website', '.gitignore').split('\n'))
check('the public mirror carries the list the site reads',
      "'packaging/recommendations.json'" in read('scripts', 'publish_public.py'))
check('styled', '.cm-credit' in read('website', 'docs.css'))

print('3. the CMS')
mjs = read('website', 'tools', 'cms.mjs')
html = read('website', 'tools', 'cms.html')
check('the list and its write-ups save as one step', 'saveCommunity(await readBody(req));' in mjs)
check('everything is checked before anything is written',
      mjs.index("if (bad.length) throw new Error(bad.join('; '));", mjs.index('function saveCommunity'))
      < mjs.index('writeRecommends(next);', mjs.index('function saveCommunity')))
check('a slug needs a write-up', 'has a slug, so it needs a write-up' in mjs)
check('a removed write-up is archived, never deleted',
      'fs.renameSync(src, path.join(COMMUNITY_ARCHIVE' in mjs and 'unlinkSync' not in mjs[mjs.index('function saveCommunity'):mjs.index('function saveCommunityImage')])
check('an image upload never overwrites by accident', "already exists`);" in mjs)
check('the editor offers the post, the image and the package',
      'data-f="slug"' in html and 'data-upload' in html and 'data-tdp="package"' in html
      and 'data-tdp="lock"' not in html and 'data-pintdp' in html)
check('draft-only fields are stripped before the list is sent', 'const { _md, _from, _toxes, _single, ...row } = t;' in html)

print('4. a pinned tox is placed (verified in TD 2026-09-25: placed, a bad hash refused and deleted)')
page = read('packaging', 'configurator', 'index.html')
ins = read('packaging', 'InstallerExt.py')
upd = read('modules', 'suspects', 'FNSTools', 'FNS_Updater', 'ExtUpdater.py')
cb = read('modules', 'suspects', 'FNSTools', 'FNS_Console', 'console_server_callbacks.py')
base = read('packaging', 'configurator', 'base.js')
check('the cards live in the shared base script (one copy)', 'window.fnsCommunity = {card: card' in base
      and 'function recCard' not in page and 'function placeCommunity' not in page)
check('a card offers Place only when served and pinned', 'if (served && pinned(r)) {' in base)
check('a card links its post and the author', "link(post, 'our write-up ↗', null, served)" in base
      and "link(r.url, (PLATFORM[r.platform] || 'their site') + ' ↗', null, served)" in base)
check('served links open in the system browser', "json('/open', {url: href})" in base)
check('the card is not a link itself (nothing interactive nests)', "var c = el('div', 'card rec');" in base)

check('the installer places into the working network', "target, note = PanePlacement('', lock=CommunityLock)" in ins
      and "uri == '/community/place'" in ins)
check('placement adds, so only the toolkit source is off limits (owner, 2026-09-26: the root was refused)',
      "PanePlacement('', lock=CommunityLock)" in ins and ins.count("PanePlacement('', lock=CommunityLock)") == 2
      and 'def CommunityLock(target_path):' in ins and "target_path.startswith(home + '/')" in ins)
check('and never outside a request callback', "run('args[0].valid and args[0].PlaceCommunityTool(args[1], args[2])'" in ins)
check('the updater reports the last placement', 'def communityPlaceResult(self):' in upd
      and "'state': 'placed'" in upd and "'state': 'failed'" in upd)
check('a refused download is deleted', upd.count('self._discard(path)') == 2)
check('the console forwards the list and the placement', "'/recommendations.json', '/community/place'" in cb)

print('5. Community is its own place (owner, 2026-09-26)')
con = read('modules', 'suspects', 'FNSTools', 'FNS_Console', 'console_page.html')
check('the console has a Community view', 'id="view-community"' in con and 'function loadCommunity()' in con
      and 'window.fnsCommunity.card(t, {served: true})' in con)
check('and a built-in tab after Updates (owner, 2026-09-26)',
      "{'name': 'community', 'label': 'Community', 'order': 30, 'builtin': True}" in read(
          'modules', 'suspects', 'FNSTools', 'FNS_Console', 'ConsoleRegistryExt.py')
      and "{name: 'community', label: 'Community', builtin: true, order: 30, displayed: true}" in con
      and "tabs.splice(at < 0 ? tabs.length : at, 0, FALLBACK_TABS[2]);" in con
      and "tabs.splice(at + 1, 0, FALLBACK_TABS[3]);" in con)
check('the picker lists none of them, one line points there',
      'if (recs.length) listEl.appendChild(communityPointer(recs.length));' in page
      and "window.parent.postMessage('fns:community', '*');" in page
      and "if (e.data === 'fns:community') showView('view-community');" in con)
check('both pages carry the same base script', base.replace('\r\n', '\n').strip()[-200:] in con and base.replace('\r\n', '\n').strip()[-200:] in page)
if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all community-site checks pass')
