"""Offline test of ExtUpdater._settleVerifications' reload-token state machine.

Runs outside TouchDesigner: the module is loaded with the TD builtins it
touches stubbed, and only the pure state machine is exercised. This covers the
one thing that cannot be checked by reading -- that every path eventually
clears 'verify' (so the drain loop added for the retry terminates).

Run it from anywhere:

    python tests/test_updater_verify.py
"""
import builtins
import os
import sys
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools',
                   'FNS_Updater', 'ExtUpdater.py')

# ---- stub the TD builtins the module body / method touches -------------
_OPS = {}


class FakeComp:
    def __init__(self, path, child_ids, errors=''):
        self.path = path
        self._child_ids = list(child_ids)
        self._errors = errors

    @property
    def children(self):
        return [types.SimpleNamespace(id=i) for i in self._child_ids]

    def findChildren(self, *a, **k):
        return self.children

    def errors(self, recurse=True):
        return self._errors

    def reload_as(self, new_ids):
        self._child_ids = list(new_ids)


builtins.op = lambda p=None: _OPS.get(p)
builtins.debug = lambda *a, **k: None
builtins.run = lambda *a, **k: None
builtins.ui = types.SimpleNamespace(messageBox=lambda *a, **k: None)
builtins.project = types.SimpleNamespace(name='test')
def _fake_fns_command(fn=None, **kw):
    """Mirror the real decorator's dual form: bare and called-with-kwargs."""
    if fn is not None:
        return fn
    return lambda f: f


_fake_mod = types.SimpleNamespace(fns_command=_fake_fns_command,
                                  fns_announce=lambda comp: None)
_fake_extutils = types.SimpleNamespace(
    tags={'ExtUtils'}, mod=lambda name: _fake_mod)
builtins.me = types.SimpleNamespace(docked=[_fake_extutils])
builtins.tdu = types.SimpleNamespace()

src = open(SRC, encoding='utf-8').read()
mod = types.ModuleType('ExtUpdater')
mod.__dict__['__file__'] = SRC
exec(compile(src, SRC, 'exec'), mod.__dict__)
ExtUpdater = mod.ExtUpdater

# A bare instance -- __init__ touches TD, so bypass it. _settleVerifications
# uses only its arguments and module-level op().
ext = ExtUpdater.__new__(ExtUpdater)

FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        print('  FAIL  %s %s' % (label, detail))
        FAILS.append(label)


def drain_until_settled(job, max_ticks=10):
    """Mimic _drain's loop: settle, and keep ticking while anything is
    still pending. Returns the number of ticks it took."""
    for tick in range(1, max_ticks + 1):
        ext._settleVerifications(job)
        if not any(r.get('verify') for r in job['results']):
            return tick
    return None


print('1. real reload (child ids all changed) -> ok, one tick')
_OPS.clear()
_OPS['/p/A'] = FakeComp('/p/A', [10, 11, 12])
job = {'results': [{'package': 'A', 'ok': True, 'verify': '/p/A',
                    'reload_token': sorted([1, 2, 3])}]}
ticks = drain_until_settled(job)
r = job['results'][0]
check('settles in 1 tick', ticks == 1, '(got %s)' % ticks)
check('stays ok', r['ok'] is True)
check('token key removed', 'reload_token' not in r)
check('ops recorded', r.get('ops') == 3, '(got %s)' % r.get('ops'))

print('2. no-op reload (ids unchanged) -> retried once, then fails')
_OPS.clear()
_OPS['/p/B'] = FakeComp('/p/B', [1, 2, 3])
job = {'results': [{'package': 'B', 'ok': True, 'verify': '/p/B',
                    'reload_token': sorted([1, 2, 3])}]}
ticks = drain_until_settled(job)
r = job['results'][0]
check('takes exactly 2 ticks', ticks == 2, '(got %s)' % ticks)
check('marked not ok', r['ok'] is False)
check('reason names the no-op', 'did nothing' in r.get('why', ''),
      '(got %r)' % r.get('why'))
check('all bookkeeping keys cleared',
      not {'verify', 'reload_token', 'reload_retried'} & set(r))

print('3. slow reload: unchanged on tick 1, landed by tick 2 -> ok')
_OPS.clear()
slow = FakeComp('/p/C', [1, 2, 3])
_OPS['/p/C'] = slow
job = {'results': [{'package': 'C', 'ok': True, 'verify': '/p/C',
                    'reload_token': sorted([1, 2, 3])}]}
ext._settleVerifications(job)            # tick 1: not landed yet
r = job['results'][0]
check('still pending after tick 1', r.get('verify') == '/p/C')
check('not failed yet', r['ok'] is True)
slow.reload_as([20, 21])                 # the reload lands
ext._settleVerifications(job)            # tick 2
check('ok after it lands', r['ok'] is True)
check('cleared', 'verify' not in r)
check('ops from the NEW contents', r.get('ops') == 2, '(got %s)' % r.get('ops'))

print('4. childless COMP (empty token) -> check skipped, not failed')
_OPS.clear()
_OPS['/p/D'] = FakeComp('/p/D', [])
job = {'results': [{'package': 'D', 'ok': True, 'verify': '/p/D',
                    'reload_token': []}]}
ticks = drain_until_settled(job)
r = job['results'][0]
check('settles in 1 tick', ticks == 1, '(got %s)' % ticks)
check('stays ok (cannot judge, does not guess)', r['ok'] is True)

print('5. COMP gone after reload -> fails, clears')
_OPS.clear()
job = {'results': [{'package': 'E', 'ok': True, 'verify': '/p/GONE',
                    'reload_token': [1]}]}
ticks = drain_until_settled(job)
r = job['results'][0]
check('settles in 1 tick', ticks == 1, '(got %s)' % ticks)
check('marked not ok', r['ok'] is False)
check('reason', r.get('why') == 'gone after reload', '(got %r)' % r.get('why'))

print('6. reload happened but the result errors -> fails on the error')
_OPS.clear()
_OPS['/p/F'] = FakeComp('/p/F', [9, 8], errors='boom: bad thing\nsecond line')
job = {'results': [{'package': 'F', 'ok': True, 'verify': '/p/F',
                    'reload_token': sorted([1, 2])}]}
drain_until_settled(job)
r = job['results'][0]
check('marked not ok', r['ok'] is False)
check('first error line only', r.get('why') == 'boom: bad thing',
      '(got %r)' % r.get('why'))

print('7. results with no verify key are untouched (bound rail only)')
job = {'results': [{'package': 'G', 'ok': True, 'ops': 5}]}
ticks = drain_until_settled(job)
check('settles immediately', ticks == 1, '(got %s)' % ticks)
check('unchanged', job['results'][0] == {'package': 'G', 'ok': True, 'ops': 5})

print('8. termination: every path clears verify within 2 ticks')
_OPS.clear()
_OPS['/p/H'] = FakeComp('/p/H', [1])          # never reloads
job = {'results': [
    {'package': 'H', 'ok': True, 'verify': '/p/H', 'reload_token': [1]},
    {'package': 'I', 'ok': True, 'verify': '/p/MISSING', 'reload_token': [7]},
]}
ticks = drain_until_settled(job)
check('mixed batch settles in <=2 ticks', ticks is not None and ticks <= 2,
      '(got %s)' % ticks)

print('9. TD build floor (_tdBuildTooOld)')
too_old = mod._tdBuildTooOld
check('older build is refused', too_old('2025.33070', '2025.30000') is True)
check('same build passes', too_old('2025.33070', '2025.33070') is False)
check('newer build passes', too_old('2025.33070', '2026.10000') is False)
check('newer YEAR, lower serial still passes',
      too_old('2025.33070', '2026.10') is False)
check('missing floor never refuses', too_old('', '2025.33070') is False)
check('None floor never refuses', too_old(None, '2025.33070') is False)
check('malformed floor never refuses',
      too_old('2025.33070-beta', '2025.33070') is False)
check('three-part floor never refuses', too_old('2025.3.7', '2025.33070') is False)
check('unparseable running build never refuses',
      too_old('2025.33070', 'unknown') is False)
check('the old app.version value ("099") never refuses',
      too_old('099', '2025.33070') is False)

print('10. _verifyFetched: a manifest row with no sha256 is refused')
import hashlib
import tempfile

builtins.absTime = types.SimpleNamespace(seconds=0)


def _tmp_artifact(payload=b'payload'):
    f = tempfile.NamedTemporaryFile(delete=False, suffix='.tox')
    f.write(payload)
    f.close()
    return f.name


GOOD = hashlib.sha256(b'payload').hexdigest()

path = _tmp_artifact()
ext._job = {'failed': [], 'fetched': []}
ext._verifyFetched('X.tox', '', path)
check('not accepted into the store', ext._job['fetched'] == [])
check('reason names the missing hash',
      any('no sha256' in f for f in ext._job['failed']),
      '(got %r)' % ext._job['failed'])
check('file deleted', not os.path.exists(path))

path = _tmp_artifact()
ext._job = {'failed': [], 'fetched': []}
ext._verifyFetched('X.tox', GOOD, path)
check('matching hash still accepted', ext._job['fetched'] == ['X.tox'],
      '(got %r)' % ext._job)
os.remove(path)

path = _tmp_artifact()
ext._job = {'failed': [], 'fetched': []}
ext._verifyFetched('X.tox', 'f' * 64, path)
check('mismatch still refused', ext._job['fetched'] == []
      and any('mismatch' in f for f in ext._job['failed']))
check('mismatched file deleted', not os.path.exists(path))

print()
if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all checks passed')
