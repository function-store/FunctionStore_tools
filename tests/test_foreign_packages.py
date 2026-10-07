"""Foreign packages (docs/ForeignPackages.md) -- the offline contract.

A foreign package is a catalog entry with a `source` block: its bytes and
version are owned upstream, mirrored by foreign_sync.py, pinned in
foreign.lock.json, and emitted into the manifest by build_manifest without
a live COMP. The contract crosses the catalog, the sync script, the
manifest build, the release rail, the updater, the picker, the site build
and both CMS halves; this pins each side so no single edit silently drops
one.

Runs outside TouchDesigner: build_manifest.py is exec'd with the TD
builtins it touches stubbed, and foreign_sync.py is exercised against a
file:// upstream in a temp directory.

    python tests/test_foreign_packages.py
"""
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(_ROOT, 'packaging')
CATALOG = os.path.join(PKG, 'catalog.json')
MANIFEST_GEN = os.path.join(PKG, 'build_manifest.py')
SYNC = os.path.join(PKG, 'foreign_sync.py')
RELEASE_ONE = os.path.join(PKG, 'release_one.py')
UPDATER = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools',
                       'FNS_Updater', 'ExtUpdater.py')
CONSOLE = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools',
                       'FNS_Console', 'console_page.html')
CMS_EXT = os.path.join(_ROOT, 'FNS_CMS', 'CmsExt.py')
PAGE = os.path.join(PKG, 'configurator', 'index.html')
CMS_MJS = os.path.join(_ROOT, 'website', 'tools', 'cms.mjs')
CMS_HTML = os.path.join(_ROOT, 'website', 'tools', 'cms.html')
SITE = os.path.join(_ROOT, 'website', 'tools', 'build-site.mjs')
DOCS = os.path.join(PKG, 'docs')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


def read(p):
    return io.open(p, encoding='utf-8').read()


def load_build_manifest(repo):
    """Exec build_manifest.py with `project.folder` pointed at `repo` and
    the TD builtins it references at import time stubbed. Only the pure
    helpers are called here; nothing touches a live op."""
    mod = types.ModuleType('build_manifest_under_test')
    mod.__dict__['project'] = types.SimpleNamespace(folder=repo, name='t')
    mod.__dict__['app'] = types.SimpleNamespace(build='2025.33070')
    mod.__dict__['op'] = lambda *a, **k: None
    mod.__dict__['debug'] = lambda *a, **k: None
    code = read(MANIFEST_GEN)
    exec(compile(code, MANIFEST_GEN, 'exec'), mod.__dict__)
    return mod


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- 1
print('1. catalog: the authority rules hold on the real catalog')
cat = json.load(io.open(CATALOG, encoding='utf-8'))
bm = load_build_manifest(_ROOT)
live_guess = {n for n, e in cat['packages'].items() if 'source' not in e}
problems = bm.CatalogProblems(cat, live_guess)
check('CatalogProblems reports nothing on the shipped catalog', not problems,
      problems)
foreign = bm.ForeignEntries(cat)
check('TDXMap is declared foreign', 'TDXMap' in foreign)
check('a foreign entry needs a source.manifest URL',
      all(e['source'].get('manifest', '').startswith('https://')
          for e in foreign.values()))
for n in foreign:
    check('%s has a doc (site build hard-fails otherwise)' % n,
          os.path.exists(os.path.join(DOCS, n + '.md')))
check('no doc still carries a `credit` block (moved to catalog author)',
      not [f for f in os.listdir(DOCS) if f.endswith('.md')
           and re.search(r'^credit:', read(os.path.join(DOCS, f)), re.M)])
check('five vendored packages carry catalog author',
      all(cat['packages'][n].get('author', {}).get('name')
          for n in ('QuickMarks', 'FNS_SearchPalette', 'midiMapper',
                    'oscMapper', 'PasteFromClipboard')))

# ---------------------------------------------------------------- 2
print('2. the authority rules refuse what they must')
bad = {'packages': {
    'Live': {'category': 'X', 'description': '', 'help_url': 'https://x'},
    'Both': {'category': 'X', 'source': {'manifest': 'https://x/m.json'}},
    'NoUrl': {'category': 'X', 'source': {}},
    'BadMode': {'category': 'X', 'source': {'manifest': 'https://x/m.json'},
                'updates': 'weekly'},
}}
p = bm.CatalogProblems(bad, {'Live', 'Both'})
check('help_url on a live package is refused', any('Live:' in x for x in p), p)
check('a live package that also declares a source is refused',
      any('Both:' in x and 'never both' in x for x in p), p)
check('a source without a manifest URL is refused',
      any('NoUrl:' in x for x in p), p)
check('an unknown updates mode is refused',
      any('BadMode:' in x for x in p), p)
check('CuratedLinks drops an author without a name',
      bm.CuratedLinks({'author': {'url': 'https://x'}}) == {})
check('CuratedLinks keeps author/homepage/changelog_url',
      bm.CuratedLinks({'author': {'name': 'A', 'url': 'https://a'},
                       'homepage': 'https://h', 'changelog_url': 'https://c'})
      == {'author': {'name': 'A', 'url': 'https://a'},
          'homepage': 'https://h', 'changelog_url': 'https://c'})

# ---------------------------------------------------------------- 3
print('3. foreign_sync mirrors a flat upstream manifest and pins the lock')
tmp = tempfile.mkdtemp(prefix='fns_foreign_')
try:
    up = os.path.join(tmp, 'upstream')
    os.makedirs(up)
    tox = b'not-really-a-tox-' + os.urandom(16)
    with open(os.path.join(up, 'Thing.tox'), 'wb') as f:
        f.write(tox)
    mpath = os.path.join(up, 'manifest.json')
    murl = 'file:///' + mpath.replace('\\', '/').lstrip('/')
    with open(mpath, 'w', encoding='utf-8') as f:
        json.dump({'latest': '1.2.0', 'version': '1.2.0',
                   'url': murl.rsplit('/', 1)[0] + '/Thing.tox',
                   'sha256': sha(tox), 'notes_url': 'https://x/changelog'}, f)
    repo = os.path.join(tmp, 'repo')
    os.makedirs(os.path.join(repo, 'packaging', 'dist'))
    with open(os.path.join(repo, 'packaging', 'catalog.json'), 'w',
              encoding='utf-8') as f:
        json.dump({'packages': {'Thing': {
            'category': 'X', 'description': 'd',
            'source': {'manifest': murl}, 'updates': 'self'}}}, f)
    # run the sync script against the temp repo
    smod = types.ModuleType('foreign_sync_under_test')
    smod.__dict__['__file__'] = os.path.join(repo, 'packaging', 'foreign_sync.py')
    exec(compile(read(SYNC), SYNC, 'exec'), smod.__dict__)
    out = []
    r = smod.sync(log=out.append)
    check('sync succeeds', r['ok'], r)
    lock = json.load(io.open(os.path.join(repo, 'packaging', 'foreign.lock.json'),
                             encoding='utf-8'))
    rec = lock['packages'].get('Thing', {})
    check('lock pins version + sha + url', rec.get('version') == '1.2.0'
          and rec.get('sha256') == sha(tox) and rec.get('url', '').endswith('Thing.tox'), rec)
    check('lock carries the upstream notes_url',
          rec.get('notes_url') == 'https://x/changelog')
    dist = os.path.join(repo, 'packaging', 'dist', 'Thing.tox')
    check('artifact mirrored into dist', os.path.exists(dist)
          and open(dist, 'rb').read() == tox)
    r2 = smod.sync(log=out.append)
    check('a second sync is a no-op', r2['ok'] and any('unchanged' in l for l in out))

    # tamper upstream: sha no longer matches the bytes
    with open(os.path.join(up, 'Thing.tox'), 'wb') as f:
        f.write(b'tampered')
    # the upstream pins a sha that matches NEITHER dist nor its own bytes:
    # the bytes must be fetched (dist differs from the pin) and then refused
    with open(mpath, 'w', encoding='utf-8') as f:
        json.dump({'version': '1.3.0', 'url': murl.rsplit('/', 1)[0] + '/Thing.tox',
                   'sha256': sha(b'what the author meant to publish')}, f)
    r3 = smod.sync(log=out.append)
    check('sha mismatch is refused', not r3['ok']
          and any('mismatch' in m for m in r3['failed']), r3)
    check('dist left untouched on mismatch', open(dist, 'rb').read() == tox)
    lock = json.load(io.open(os.path.join(repo, 'packaging', 'foreign.lock.json'),
                             encoding='utf-8'))
    check('lock not advanced on mismatch',
          lock['packages']['Thing']['version'] == '1.2.0')

    # a manifest with no sha is refused (unpinned bytes)
    with open(mpath, 'w', encoding='utf-8') as f:
        json.dump({'version': '1.4.0', 'url': murl.rsplit('/', 1)[0] + '/Thing.tox'}, f)
    r4 = smod.sync(log=out.append)
    check('unpinned upstream (no sha256) is refused',
          not r4['ok'] and any('sha256' in m for m in r4['failed']), r4)

    # ------------------------------------------------------------ 4
    print('4. ForeignPackages emits a manifest row from lock + catalog')
    bm2 = load_build_manifest(repo)
    cat2 = json.load(io.open(os.path.join(repo, 'packaging', 'catalog.json'),
                             encoding='utf-8'))
    cat2['packages']['Thing'].update({
        'author': {'name': 'Up Stream', 'url': 'https://up'},
        'homepage': 'https://up', 'help_url': 'https://up/docs/',
        'min_td_build': '2023.12120', 'placement': 'root'})
    rows, probs = bm2.ForeignPackages(cat2, bm2.ForeignLock(
        os.path.join(repo, 'packaging', 'foreign.lock.json')),
        dist_dir=os.path.join(repo, 'packaging', 'dist'))
    check('one row, no problems', len(rows) == 1 and not probs, probs)
    row = rows[0] if rows else {}
    check("kind stays 'tool' (every consumer treats it as a tool)",
          row.get('kind') == 'tool')
    check('row is flagged foreign', row.get('foreign') is True)
    check('version comes from the lock', row.get('version') == '1.2.0')
    check('updates mode carried', row.get('updates') == 'self')
    check('help_url / min_td_build come from the catalog',
          row.get('help_url') == 'https://up/docs/'
          and row.get('min_td_build') == '2023.12120')
    check('author / homepage carried; changelog_url defaults to the '
          'upstream notes_url',
          row.get('author') == {'name': 'Up Stream', 'url': 'https://up'}
          and row.get('homepage') == 'https://up'
          and row.get('changelog_url') == 'https://x/changelog')
    check('placement carried', row.get('placement') == 'root')
    check('artifact hashed from dist and matches the lock',
          (row.get('artifact') or {}).get('sha256') == sha(tox)
          and row['artifact']['path'] == 'packaging/dist/Thing.tox')
    check('nothing reflected: no surfaces, hotkeys, requires, ops',
          row.get('surfaces') == [] and row.get('hotkeys') == []
          and row.get('requires') == [] and row.get('ops') == 0)
    # dist bytes that disagree with the lock: no artifact, a problem
    with open(dist, 'wb') as f:
        f.write(b'drifted')
    rows, probs = bm2.ForeignPackages(cat2, bm2.ForeignLock(
        os.path.join(repo, 'packaging', 'foreign.lock.json')),
        dist_dir=os.path.join(repo, 'packaging', 'dist'))
    check('a dist/lock mismatch drops the artifact and is reported',
          rows and 'artifact' not in rows[0] and any('does not match' in p for p in probs), probs)
    # no lock row at all
    rows, probs = bm2.ForeignPackages(cat2, {}, dist_dir=os.path.join(repo, 'packaging', 'dist'))
    check('an unsynced entry is reported as not synced',
          any('not synced' in p for p in probs), probs)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ---------------------------------------------------------------- 4
print('4. foreign_sync resolves a GitHub release as the upstream manifest')
gh_src = {'manifest': 'https://api.github.com/repos/o/r/releases/latest',
          'tox': 'Thing.tox'}
gh_doc = {'tag_name': 'v2.1.0', 'html_url': 'https://github.com/o/r/releases/tag/v2.1.0',
          'body': 'fixed things\r\n', 'assets': [
              {'name': 'other.zip', 'browser_download_url': 'https://x/other.zip',
               'digest': 'sha256:' + 'a' * 64},
              {'name': 'Thing.tox', 'browser_download_url': 'https://x/Thing.tox',
               'digest': 'sha256:' + 'b' * 64}]}
v, u, s, nu, notes = smod.resolve('Thing', gh_src, gh_doc)
check('tag is the version (leading v dropped), asset is the artifact, digest is the pin',
      v == '2.1.0' and u == 'https://x/Thing.tox' and s == 'b' * 64, (v, u, s))
check('release page is the notes_url and the body rides as notes',
      nu.endswith('/releases/tag/v2.1.0') and notes == 'fixed things')
nodig = {'tag_name': '1.0', 'assets': [{'name': 'Thing.tox',
                                        'browser_download_url': 'https://x/Thing.tox'}]}
try:
    smod.resolve('Thing', gh_src, nodig)
    check('an asset without a sha256 digest is refused', False)
except ValueError as e:
    check('an asset without a sha256 digest is refused', 'digest' in str(e), e)
try:
    smod.resolve('Thing', {'manifest': gh_src['manifest']}, gh_doc)
    check('a GitHub upstream without source.tox is refused', False)
except ValueError as e:
    check('a GitHub upstream without source.tox is refused', 'source.tox' in str(e), e)
try:
    smod.resolve('Thing', dict(gh_src, tox='missing.tox'), gh_doc)
    check('a release without the named asset is refused', False)
except ValueError as e:
    check('a release without the named asset is refused', 'no asset' in str(e), e)
check('the shipped catalog declares ParHoverMIDI_VSN1 as a GitHub-release foreign entry',
      'api.github.com/repos/' in foreign.get('ParHoverMIDI_VSN1', {}).get('source', {}).get('manifest', '')
      and foreign.get('ParHoverMIDI_VSN1', {}).get('source', {}).get('tox') == 'ParHoverMIDI_VSN1.tox')

# ---------------------------------------------------------------- 5
print('5. Build() appends foreign rows and reports catalog problems')
gen = read(MANIFEST_GEN)
check('Build appends ForeignPackages rows after the live loop',
      re.search(r"foreign_rows, foreign_problems = ForeignPackages\(", gen)
      is not None and gen.find('ForeignPackages(\n') > gen.find("packages.append(entry)"))
check('a live package always wins a name collision',
      "if entry['name'] in live_names:\n            continue" in gen)
check('Build reports catalog_problems and foreign names',
      "'catalog_problems': catalog_problems" in gen and "'foreign':" in gen)
check('live rows carry CuratedLinks', 'entry.update(CuratedLinks(meta))' in gen)

# ---------------------------------------------------------------- 6
print('6. the release rail never bumps, exports or PI-saves a foreign name')
ro = read(RELEASE_ONE)
check('ReleaseMany splits foreign names off todo',
      re.search(r"foreign = \[n for n in names if n in foreign_all and n not in by_name\]", ro)
      is not None)
check('a broken mirror refuses the release before the label moves',
      'foreign package(s) not mirrored' in ro
      and ro.find('not mirrored') < ro.find('rel = _setReleaseLabel(label)'))
check('foreign versions come from the lock, not a live par',
      re.search(r"for n in foreign:\s*\n\s*versions\[n\] = str\(\(lock\.get\(n\)", ro)
      is not None)
check('Preflight blocks on catalog authority problems and unmirrored foreign',
      'catalog.json breaks an authority rule' in ro
      and 'foreign package(s) not mirrored' in ro)

# ---------------------------------------------------------------- 7
print("7. the updater has the 'self-managed' state and never touches it")
upd = read(UPDATER)
check("Compare emits 'self-managed' for updates: 'self'",
      re.search(r"pkg\.get\('updates', ''\) or ''\) == 'self':.*?'state': 'self-managed'",
                upd, re.S) is not None)
check('it is decided before the version compare (no Pkgversion needed)',
      upd.find("'state': 'self-managed'") < upd.find("'state': 'unversioned'"))
check('never appended to updates',
      re.search(r"'state': 'self-managed'.*?continue", upd, re.S) is not None)
con = read(CONSOLE)
check('the console labels it and files it with the current rows',
      "'self-managed': ['updates itself', 'ok']" in con
      and "r.state === 'self-managed'" in con)

# ---------------------------------------------------------------- 8
print('8. the picker shows the byline, link-outs and the self-update chip')
page = read(PAGE)
check('byline from manifest author', "p.author && p.author.name" in page)
check('homepage / changelog link-outs',
      "['homepage', 'site" in page and "changelog_url" in page)
check("'updates itself' chip", "p.updates === 'self'" in page)

# ---------------------------------------------------------------- 9
print('9. the site build reads author from the catalog and refuses credit')
site = read(SITE)
check('author from curated catalog entry', 'cur.author' in site)
check('doc frontmatter credit is refused',
      re.search(r"data\.credit !== undefined.*?fail\(", site, re.S) is not None)
check('homepage / changelog / family-product badges',
      'p.homepage' in site and 'p.changelogUrl' in site and 'family product' in site)

# ---------------------------------------------------------------- 10
print('10. both CMS halves author and show it')
mjs = read(CMS_MJS)
check('credit left FM_ORDER', "'credit'" not in mjs.split('const FM_ORDER')[1].split('\n')[0])
check('the PUT handler applies curated fields with the allowed-on rules',
      'function applyCurated' in mjs and 'FOREIGN_ONLY' in mjs
      and 'const bad = applyCurated(entry, body)' in mjs)
check('a save strips credit from frontmatter', 'delete data.credit' in mjs)
check('the server exposes the fields on the package', 'curatedExtras(' in mjs)
html = read(CMS_HTML)
check('editor offers author / website / changelog',
      'id="author-name"' in html and 'id="homepage"' in html
      and 'id="changelog_url"' in html)
check('editor offers the foreign block',
      'id="source-manifest"' in html and 'id="updates"' in html
      and 'id="help_url"' in html and 'id="min_td_build"' in html)
check('save sends them', "source: draft.source || null" in html
      and "author: draft.author || null" in html)
check('release table renders foreign rows with Sync and Retire, no PI Save',
      'relforeignsync' in html and "r.foreign ? `<tr>" in html)
ext = read(CMS_EXT)
check('FNS_CMS appends foreign rows through build_manifest',
      "bm['ForeignPackages'](cat, bm['ForeignLock']())" in ext)
check('FNS_CMS runs the sync detached and exposes its log',
      "'/api/foreignsync'" in ext and "'/api/foreignlog'" in ext
      and 'foreign_sync.py' in ext)
check('retire knows a foreign name has no live COMP',
      "foreign_now" in ext)

print('11. a priced family product is never called free (owner, 2026-09-17)')
# TDXMap installs for everyone (its bytes are public, entitlement is
# enforced inside the tool), so `access` stays free and nothing gates it
# here -- but it is a 14-day trial and then Base or Pro, and the picker
# had counted it among "39 tools are free". The catalog carries the
# words; every surface shows them beside the Patreon mark, never as it.
cat_rows = json.load(io.open(CATALOG, encoding='utf-8'))
cat_rows = cat_rows['packages'] if isinstance(cat_rows, dict) and 'packages' in cat_rows else cat_rows
cat_rows = cat_rows if isinstance(cat_rows, list) else [dict(name=k, **v) for k, v in cat_rows.items()]
tdx = next((p for p in cat_rows if p.get('name') == 'TDXMap'), {})
pr = tdx.get('pricing') or {}
check('catalog: TDXMap carries pricing {summary, detail, url}',
      bool(pr.get('summary')) and bool(pr.get('detail')) and pr.get('url', '').startswith('https://'))
check('catalog: pricing is beside access, never in it',
      tdx.get('access') in (None, 'free'))
gen_src = io.open(MANIFEST_GEN, encoding='utf-8').read()
check('build_manifest passes pricing through in BOTH entry builders (foreign and live)',
      gen_src.count("entry['pricing'] = {k: str(pricing.get(k, '') or '').strip()") == 2)
page_src = io.open(os.path.join(PKG, 'configurator', 'index.html'), encoding='utf-8').read()
check('picker: pricingOf reads the manifest words, isPlus is untouched',
      "function pricingOf(p) { return p.pricing && p.pricing.summary ? p.pricing : null; }" in page_src
      and "function isPlus(p) { return !!p.access && p.access !== 'free'; }" in page_src)
check('picker: the free count leaves a priced product out and names its trial',
      "var free = tools.length - plus.length - priced.length;" in page_src
      and "' a free trial'" in page_src)
check('picker: the card and the quiz row carry the trial chip with the detail as its tip',
      "docsLink(pr.url, pr.summary, 'chip trial')" in page_src
      and "pc.setAttribute('data-tip', pr.detail)" in page_src
      and "nm.appendChild(chip(pricingOf(p).summary, 'trial'));" in page_src)
# the search moved into FNSSearch.prepare (docs/PickerSearch.md, 2026-10-03);
# tests/test_picker_search.py ranks "trial" against the real catalog
check('picker: "trial" finds it in the search box',
      "if (p.pricing && p.pricing.summary) add('trial ' + p.pricing.summary, DESC, true);" in page_src)
site_src = io.open(os.path.join(_ROOT, 'website', 'tools', 'build-site.mjs'), encoding='utf-8').read()
# 0272bb46 (2026-09-24) moved the docs SIDEBAR's access marks into a quiet
# column (sidebarAccess), so the inline marks appear twice, on the index
# row and the feature card, and the sidebar still shows access its own way.
check('site: a trial mark beside every Patreon mark, and a licence note on its page',
      site_src.count("${isPlus(p.name) ? plusMark(p.name) : ''}${variantMark(p.name)}${trialMark(p.name)}") == 2
      and 'sidebarAccess(p.name)' in site_src
      and 'const trialNote = !isPlus(p.name) && pricing' in site_src
      and '${plusNote}${variantNote}${trialNote}' in site_src)
check('picker: a family product is never ticked FOR the user -- starting points skip it',
      'function handPick(p) { return !!(p && (p.foreign || pricingOf(p))); }' in page_src
      and 'return !lockedPatreon([n]).length && (own || !handPick(byName[n]));' in page_src
      and 'function ticks(r) { return installable(r.name) && !handPick(byName[r.name]); }' in page_src)
check('picker: Set up like last time keeps what the user had (own list)',
      'choose(names, bind, false, true);' in page_src
      and 'autoPick(lastNames, true).length' in page_src)
check('picker: the welcome is one sentence of counts, no names',
      "' has' : ' have') + ' a free trial'" in page_src
      and "' come with Patreon'" in page_src and 'among them' not in page_src)
doc_src = io.open(os.path.join(PKG, 'docs', 'TDXMap.md'), encoding='utf-8').read()
check('doc: says it is not free, and what the trial is',
      'TDXMap is not free' in doc_src and '14-day trial' in doc_src)

print()
if FAILS:
    print('%d FAILED: %s' % (len(FAILS), '; '.join(FAILS)))
    sys.exit(1)
print('all passed')
