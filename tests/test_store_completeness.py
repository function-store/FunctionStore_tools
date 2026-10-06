"""Keepstore: the store holds the whole release, and a full mirror's
completion is one hook (docs/StoreCompleteness.md).

Pinned as source contracts, since the rails run inside TouchDesigner:
the chain points, the refusal while a job runs, that nothing chains
after a refresh (no self-trigger), and the hook the operator family
will feed from.

    python tests/test_store_completeness.py
"""
import io
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPD = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools', 'FNS_Updater', 'ExtUpdater.py')
INS = os.path.join(_ROOT, 'packaging', 'InstallerExt.py')
FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        FAILS.append(label)
        print('  FAIL  %s   %s' % (label, detail))


upd = io.open(UPD, encoding='utf-8').read()
ins = io.open(INS, encoding='utf-8').read()

print('1. the updater')
check('KeepStore reads the toggle, a missing par reads as on',
      "if not self._parBool('Keepstore', True):" in upd)
check('it refuses while a job runs, and is a plain full RefreshStore otherwise',
      re.search(r"def KeepStore\(self\):.*?not in \('done', 'failed'\):.*?return self\.RefreshStore\(names=None\)",
                upd, re.S) is not None)
check('an update pass chains it, scheduled after the report',
      re.search(r"self\._keepStoreLater\(\)\n\s*return \{'ok': not bad and not job\.get\('failed'\), 'updated': done",
                upd) is not None
      and "run('args[0].valid and args[0].extensionsReady and args[0].KeepStore()'" in upd)
check('nothing chains after a refresh (a mirror never re-triggers itself)',
      re.search(r"if kind == 'refresh':(.*?)return \{'ok': st\.get\('ok'\)", upd, re.S) is not None
      and '_keepStoreLater' not in re.search(r"if kind == 'refresh':(.*?)return \{'ok': st\.get\('ok'\)", upd, re.S).group(1))
check('a FULL mirror that succeeded calls the one hook',
      re.search(r"if job\.get\('names'\) is None and not job\.get\('failed'\):\n\s*self\._afterStoreComplete\(st\)", upd)
      is not None)
check('the hook names the operator family as its future occupant',
      re.search(r"def _afterStoreComplete\(self, status\):.*?operator\s*\n?\s*family", upd, re.S) is not None)

print('2. the installer')
# Order, not adjacency: SyncFamilyToggle() joined the tail in v3.2.30 and
# an anchor that demanded `return res` on the very next line went red for
# a change that kept the rule it was guarding.
check('every install rail chains it after Install() returned',
      re.search(r"self\._afterPasteInstall\(res\)\n\s*self\._keepStore\(\)"
                r"(\n\s*self\.\w+\([^\n]*\))*\n\s*return res", ins) is not None)
check('scheduled through the updater, never inline',
      "run('args[0].valid and args[0].KeepStore()', self._updaterComp()," in ins)
check('the picker\'s done text says the download is happening',
      'the rest of the release downloads in the ' in ins and "self._keepStoreWanted()" in ins)
check('an updater without the toggle or the method is skipped, not an error',
      re.search(r"def _keepStoreWanted\(self\):.*?except Exception:\n\s*return False", ins, re.S) is not None)

print()
if FAILS:
    print('FAILED: %d check(s)' % len(FAILS))
    raise SystemExit(1)
print('all store completeness checks pass')
