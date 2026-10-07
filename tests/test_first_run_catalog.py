"""A clean machine can always find the bucket, and says so when it cannot.

Field report 2026-09-18, a genuinely clean macOS install: the picker sat on
"First run: fetching the package catalog from the bucket... this page
refreshes itself" for good. Measured on that machine: `_job` was None and
the store folder did not exist, so no refresh had ever STARTED.

The cause is a deadlock between two rungs of ExtUpdater.BaseUrl. The
shipped `Baseurl` par is empty (verified in dist/FNS_Updater.tox 3.2.11:
val and default both ''), discovery is on, and DiscoveredBase() reads a
CACHED document -- which a clean machine does not have. BaseUrl therefore
returned '', and _startJob refuses on `if not base` BEFORE it creates a
job, so discovery could never run to fill the cache that BaseUrl needed.
A dev machine cannot reproduce it: its store already holds the document.

So the shipped endpoint is a module constant derived from the first
discovery pin, and the refusal is no longer emitted as a JS comment.

That fixed the machine with NO store. The machine with an OLD store was
still broken, and it fails silently instead of hanging, which is worse.
Field report 2026-09-19: a clean start on a store left at v3.2.37
installed all 67 packages at v3.2.37 -- the `installed` table carried
today's timestamps and that release -- because the silent "set up like
last time" rail read DefaultManifest() and planned from whatever the
store held. The store is machine-wide and outlives every project, so it
never looked again. The family members were still `placement: pane` in
that catalog, so seven of them spawned into the root network, which is
the one thing `none` exists to prevent. Section 4 pins the refresh.

    python tests/test_first_run_catalog.py
"""
import io
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPD = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'FNS_Updater',
                   'ExtUpdater.py')
INS = os.path.join(_ROOT, 'packaging', 'InstallerExt.py')
IDX = os.path.join(_ROOT, 'packaging', 'configurator', 'index.html')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


upd = io.open(UPD, encoding='utf-8').read()
ins = io.open(INS, encoding='utf-8').read()
idx = io.open(IDX, encoding='utf-8').read()

print('1. the endpoint ships in the binary')
check('PINNED_BASE is derived from the first discovery pin, not retyped',
      "PINNED_BASE = DISCOVERY_PINS[0].split('/.well-known/')[0]" in upd)
check('BaseUrl falls back to it when the par is empty',
      'return par or PINNED_BASE' in upd)
check('the par still wins when someone sets one (a mirror, a moved bucket)',
      upd.index("par = self._par('Baseurl')") < upd.index('return par or PINNED_BASE'))
check('and discovery still outranks the constant',
      upd.index('found = self.DiscoveredBase()') < upd.index('return par or PINNED_BASE'))

print('2. _startJob still refuses an EMPTY base -- the guard is not the bug')
check('the guard is intact',
      "return {'ok': False, 'why': 'no Baseurl set'}" in upd)

print('3. a refusal is visible, not a comment')
check('the installer sends the reason as a global',
      "window.FNS_REFRESH_ERROR = %s;" in ins
      and "json.dumps(why or '')" in ins)
check('the old JS-comment smuggling is gone',
      "' // ' + why if why else ''" not in ins)
check('the page shows it instead of promising a refresh',
      "var refuse = String(window.FNS_REFRESH_ERROR || '');" in idx
      and "'The package catalog could not be fetched: ' + refuse" in idx
      and "refuse ? 'store refresh refused' : 'refreshing store…'" in idx)
check('the reason is set as TEXT, never innerHTML',
      "note.textContent = 'The package catalog could not be fetched: ' + refuse;" in idx)

print('4. a store that ALREADY has a manifest is refreshed too')
ins = io.open(INS, encoding='utf-8').read()
check('the silent rail refreshes before it plans, not only on an empty store',
      "if stage == 'plan' and (full is None or _inStore(full)):" in ins)
check('the old only-when-absent gate is gone',
      "if stage == 'manifest':" not in ins)
check('a missing manifest is still the hard stop it was',
      "return self._lastSetupStop('the store manifest did not arrive')" in ins)
check('a dev Manifestfile outside the store is left alone',
      '_inStore(full)' in ins and 'def _inStore(path)' in ins)
check('the picker keeps its own guard (this does not replace it)',
      'def _checkManifest(self, full)' in ins
      and 'MANIFEST_CHECK_SECONDS' in ins)

print()
if FAILS:
    print('%d check(s) failed:' % len(FAILS))
    for f in FAILS:
        print('  - ' + f)
    raise SystemExit(1)
print('all first-run catalog checks pass')
