"""The embedded picker learns about a newer release.

Field report, v3.2.26: a fresh FNSTools.tox's picker did not list the new
packages. The picker reads the machine store's manifest and only fetched a
catalog when the store had none, so a store from an older release was
served as-is forever. Now serving a store manifest starts a manifest-only
refresh (throttled), /manifest/release reports the outcome, and the page
reloads itself, or offers a reload when the reader has already changed
something. An install's download queues behind any running store job
instead of being refused by the updater.

Pinned as source contracts: the rails run inside TouchDesigner (verified
live there, 2026-09-17).

    python tests/test_picker_catalog_check.py
"""
import io
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INS = os.path.join(_ROOT, 'packaging', 'InstallerExt.py')
IDX = os.path.join(_ROOT, 'packaging', 'configurator', 'index.html')
BI = os.path.join(_ROOT, 'packaging', 'build_installer.py')
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

print('1. serving a store manifest starts a catalog check')
check('/manifest.js runs the check on the manifest it serves',
      re.search(r"checking = self\._checkManifest\(full\)\n\s*with open\(full, 'r', encoding='utf-8'\) as f:", ins) is not None)
check('and tells the page with window.FNS_CHECKING',
      "'window.FNS_CHECKING = %s;\\n'" in ins and "% (json.dumps(checking)," in ins)
check('only the machine store is checked, never a dev Manifestfile',
      re.search(r"def _checkManifest\(self, full\):.*?if not _inStore\(full\):\n\s*return False", ins, re.S) is not None)
check('the check is manifest-only (names=[]) and throttled to once a minute',
      "why = self._refreshStore(names=[])" in ins and "MANIFEST_CHECK_SECONDS = 60" in ins
      and "now - prev.get('started', 0) < self.MANIFEST_CHECK_SECONDS" in ins)
check('a running store job is waited on, not doubled',
      re.search(r"if self\._refreshActive\(\):\n\s*return True\s+# a running pass", ins) is not None)
check('a check that has not started yet still counts as pending for a few seconds',
      "absTime.seconds - chk.get('started', 0) < 10" in ins)

print('2. /manifest/release reports the outcome')
check('the route exists and answers checking, release and served',
      "uri == '/manifest/release'" in ins
      and "{'checking': pending, 'release': release," in ins
      and "'served': chk.get('served', '')" in ins)

print('3. the page reloads, or offers the reload')
check('only the served picker with a check running watches',
      "if (served && window.FNS_CHECKING) watchCatalog();" in idx)
check('it polls /manifest/release without the cache, bounded',
      "fetch('/manifest/release', { cache: 'no-store' })" in idx and "tries < 30" in idx)
check('an unchanged release does nothing',
      "if (!d.release || !M.release || d.release === M.release) return;" in idx)
check('picks changed or a dialog open (other than the welcome) means offer, not reload',
      "if (busy()) offer(d.release); else location.reload();" in idx
      and "dialog[open]:not(#welcome)" in idx
      and "Array.from(picked).sort().join(',') !== picksAtLoad" in idx)
check('the offer is a note with a Reload button, shown once',
      "box.id = 'catalog-new';" in idx and "btn.textContent = 'Reload the list';" in idx
      and "if (document.getElementById('catalog-new')) return;" in idx)

print('4. an install download queues behind a running store job')
# Counted call sites here once, and a fourth rail (SetFamily, v3.2.30)
# made the test wrong without making the code wrong. What matters is that
# nothing hands a plan's downloads to anything BUT the queue, which stays
# true however many rails there are.
# (len() and join() also take the list, to count and to report it; only
# the calls that could DOWNLOAD it are the question, so: our own methods.)
_fetchers = set(re.findall(r"(self\.[\w.]+)\(plan\['to_fetch'\]", ins))
check('every selection download goes through the queue',
      _fetchers == {'self._fetchSelection'}
      and "self._refreshStore(names=plan['to_fetch'])" not in ins,
      sorted(_fetchers))
check('a busy updater (job or pending catalog check) queues instead of refusing',
      "if not self._refreshActive() and not self._manifestCheckPending():" in ins
      and "self._pending_fetch = list(names)" in ins)
check('the queue starts the fetch when idle and always clears itself',
      re.search(r"def fetchWhenIdle\(self, tries=0\):.*?upd\.RefreshStore\(names=names\).*?finally:\n\s*self\._pending_fetch = None", ins, re.S) is not None)
check('/status reports a queued fetch as fetching',
      "or getattr(self, '_pending_fetch', None) is not None)" in ins)
check('the silent last-setup rail waits for a queued fetch too',
      "if self._refreshActive() or getattr(self, '_pending_fetch', None) is not None:" in ins)

print('5. the rails carry it')
m = re.search(r"INSTALLER_VERSION = '(\d+)\.(\d+)\.(\d+)'", bi)
check('INSTALLER_VERSION moved past 3.2.17', m is not None and tuple(map(int, m.groups())) > (3, 2, 17), m and m.group(0))

print()
if FAILS:
    print('%d check(s) failed:' % len(FAILS))
    for f in FAILS:
        print('  - ' + f)
    raise SystemExit(1)
print('all picker catalog-check checks pass')
