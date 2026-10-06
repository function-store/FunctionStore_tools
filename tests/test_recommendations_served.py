"""The served picker reads the recommendations list from the installer.

Measured 2026-09-17: the embedded picker (FNS_Installer's Web Server DAT on
127.0.0.1) fetched recommendations.json straight from
storage.functionstore.tools, and the bucket sends no
Access-Control-Allow-Origin header, so every load was blocked by CORS and
the lane could never render inside TouchDesigner. The updater already
downloads the list into <store>/community/ with TD's own downloader, where
CORS does not apply; the installer now relays that copy on the page's own
origin, refreshing it when stale and the updater is idle.

Pinned as source contracts: the rails run inside TouchDesigner (verified
live there: a planted row rendered from 127.0.0.1 with no bucket request, a
stale copy triggered one refresh that failed on the bucket's 404 and kept
the last copy without looping, and a refresh that emptied the list removed
the row from an open page).

    python tests/test_recommendations_served.py
"""
import io
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INS = os.path.join(_ROOT, 'packaging', 'InstallerExt.py')
IDX = os.path.join(_ROOT, 'packaging', 'configurator', 'index.html')
BI = os.path.join(_ROOT, 'packaging', 'build_installer.py')
UPD = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'FNS_Updater', 'ExtUpdater.py')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


ins = io.open(INS, encoding='utf-8').read()
idx = io.open(IDX, encoding='utf-8').read()
bi = io.open(BI, encoding='utf-8').read()
upd = io.open(UPD, encoding='utf-8').read()

print('1. the installer relays the store copy')
check('GET /recommendations.json answers from _recommendations()',
      re.search(r"uri == '/recommendations\.json':\n\s*response\['Content-Type'\] = 'application/json'\n\s*response\['data'\] = json\.dumps\(self\._recommendations\(\)\)", ins) is not None)
check('the list comes from the updater\'s CommunityList (the store copy)',
      "return {'tools': upd.CommunityList(), 'retry': retry}" in ins)
check('the copy it reads is the one RefreshCommunity writes',
      "'%s/community/recommendations.json' % upd.StoreFolder()" in ins
      and "return '/'.join([self.StoreFolder(), 'community'] + [p for p in parts])" in upd
      and "COMMUNITY_NAME = 'recommendations.json'" in upd)
check('no updater means an empty answer, never an error',
      "return {'tools': [], 'retry': False}" in ins)

print('2. the copy is refreshed when stale, never in a loop')
check('stale means missing or older than five minutes',
      "COMMUNITY_MAX_AGE = 300" in ins and "stale = age is None or age > self.COMMUNITY_MAX_AGE" in ins)
check('a refresh is asked at most once a minute (a failed download is not retried every poll)',
      "COMMUNITY_RETRY_SECONDS = 60" in ins
      and "recently = asked is not None and absTime.seconds - asked < self.COMMUNITY_RETRY_SECONDS" in ins)
check('never while a store job, a catalog check or a queued fetch is busy (a job aborts the download)',
      re.search(r"if \(self\._refreshActive\(\) or self\._manifestCheckPending\(\)\n\s*or getattr\(self, '_pending_fetch', None\) is not None\):", ins) is not None)
check('RefreshCommunity is called outside the request callback',
      "run('args[0].valid and args[0].RefreshCommunity()', upd," in ins)
check('a list download in flight answers retry',
      "place.get('stage') == 'list'" in ins
      and re.search(r"if self\._communityInFlight\(upd\):\n\s*return \{'tools': upd\.CommunityList\(\), 'retry': True\}", ins) is not None)

print('3. the page asks the installer when served, the bucket otherwise')
check('served: the page fetches its own origin',
      re.search(r"if \(served\) \{\n\s*url = '/recommendations\.json';", idx) is not None)
check('not served (site, standalone): the bucket, as before',
      "url = base + '/recommendations.json';" in idx)
check('the page retries while the installer says retry, bounded',
      "if (served && doc.retry && tries < 8) setTimeout(ask, 3000);" in idx)
check('an empty answer still re-renders when rows were showing (a removal leaves the page)',
      "if (!list.length && !(window.FNS_RECOMMENDS || []).length) return;" in idx)
check('rows without a name and an https link are still never rendered',
      "return t && t.name && String(t.url || '').indexOf('https://') === 0;" in idx)

print('4. the rails carry it')
m = re.search(r"INSTALLER_VERSION = '(\d+)\.(\d+)\.(\d+)'", bi)
check('INSTALLER_VERSION moved past 3.2.18', m is not None and tuple(map(int, m.groups())) > (3, 2, 18), m and m.group(0))

print()
if FAILS:
    print('%d check(s) failed:' % len(FAILS))
    for f in FAILS:
        print('  - ' + f)
    raise SystemExit(1)
print('all served-recommendations checks pass')
