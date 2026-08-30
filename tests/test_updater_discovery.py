"""Offline test of ExtUpdater's discovery layer.

Runs outside TouchDesigner, same shape as test_updater_verify.py: the module
is loaded with TD builtins stubbed and only the pure logic is exercised --
document parsing, base-url precedence, and the minimum_updater kill switch.

These three are worth pinning down because each fails in a direction that is
invisible in normal use:

  * a half-parsed document must not override a working Baseurl
  * a LOCAL Baseurl (the file:// / mirror test rail) must never be
    second-guessed by a network lookup
  * the kill switch must refuse ONLY on a floor it genuinely parsed and
    that is genuinely newer -- a malformed value stranding the whole fleet
    is a far worse failure than a bad build running one release too long

Run it from anywhere:

    python tests/test_updater_discovery.py
"""
import builtins
import json
import os
import shutil
import sys
import tempfile
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools',
                   'FNS_Updater', 'ExtUpdater.py')

# ---- stub the TD builtins the module body touches ---------------------
builtins.op = lambda p=None: None
builtins.debug = lambda *a, **k: None
builtins.run = lambda *a, **k: None
builtins.ui = types.SimpleNamespace(messageBox=lambda *a, **k: None)
builtins.project = types.SimpleNamespace(name='test')
builtins.absTime = types.SimpleNamespace(seconds=0.0)
builtins.app = types.SimpleNamespace(userPaletteFolder='/nowhere')
builtins.tdu = types.SimpleNamespace()


def _fake_fns_command(fn=None, **kw):
    if fn is not None:
        return fn
    return lambda f: f


_fake_mod = types.SimpleNamespace(fns_command=_fake_fns_command,
                                  fns_announce=lambda comp: None)
builtins.me = types.SimpleNamespace(
    docked=[types.SimpleNamespace(tags={'ExtUtils'}, mod=lambda n: _fake_mod)])

src = open(SRC, encoding='utf-8').read()
mod = types.ModuleType('ExtUpdater')
mod.__dict__['__file__'] = SRC
exec(compile(src, SRC, 'exec'), mod.__dict__)
ExtUpdater = mod.ExtUpdater

FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        print('  FAIL  %s %s' % (label, detail))
        FAILS.append(label)


class FakePar:
    def __init__(self, v):
        self._v = v

    def eval(self):
        return self._v


def make_ext(store, baseurl='', pkgversion='3.0.0', usediscovery=True):
    """A bare instance -- __init__ touches TD, so bypass it."""
    ext = ExtUpdater.__new__(ExtUpdater)
    pars = types.SimpleNamespace(
        Storefolder=FakePar(store), Baseurl=FakePar(baseurl),
        Pkgversion=FakePar(pkgversion), Usediscovery=FakePar(usediscovery))
    # _version is child-first (FNS_About wins); the fake has no children
    ext.ownerComp = types.SimpleNamespace(par=pars, op=lambda _name: None)
    return ext


def write_doc(store, doc, name=None):
    os.makedirs(store, exist_ok=True)
    path = os.path.join(store, name or mod.DISCOVERY_CACHE)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(doc, f)
    return path


BUCKET = 'https://storage.functionstore.tools/fnstools'
MOVED = 'https://cdn.example.com/fnstools'


def good(minimum='', notices=None):
    return {'schema': 1, 'endpoints': {'manifest': MOVED},
            'minimum_updater': minimum, 'notices': notices or []}


def main():
    store = tempfile.mkdtemp(prefix='fns_disco_')
    print('ExtUpdater discovery')

    print('\n1. document parsing')
    ext = make_ext(store)
    check('no document -> no base', ext.DiscoveredBase() == '')
    write_doc(store, good())
    check('valid document -> its endpoint', ext.DiscoveredBase() == MOVED,
          ext.DiscoveredBase())
    write_doc(store, {'schema': 1, 'endpoints': {}})
    check('document with no endpoint is treated as absent',
          ext.DiscoveredBase() == '', ext.DiscoveredBase())
    with open(os.path.join(store, mod.DISCOVERY_CACHE), 'w') as f:
        f.write('<html>404 not found</html>')
    check('error page is treated as absent', ext.DiscoveredBase() == '')
    write_doc(store, ['not', 'a', 'dict'])
    check('non-object document is treated as absent',
          ext.DiscoveredBase() == '')

    print('\n2. BaseUrl precedence')
    write_doc(store, good())
    ext = make_ext(store, baseurl=BUCKET)
    check('discovery overrides the par', ext.BaseUrl() == MOVED, ext.BaseUrl())
    ext = make_ext(store, baseurl=BUCKET, usediscovery=False)
    check('Usediscovery off -> the par wins', ext.BaseUrl() == BUCKET,
          ext.BaseUrl())
    # The mirror / offline test rail must never be re-routed by a lookup.
    local = store.replace('\\', '/')
    ext = make_ext(store, baseurl=local)
    check('a LOCAL path beats discovery', ext.BaseUrl() == local.rstrip('/'),
          ext.BaseUrl())
    ext = make_ext(store, baseurl='file:///C:/mirror')
    check('a file:// URL beats discovery',
          ext.BaseUrl() == 'file:///C:/mirror', ext.BaseUrl())
    # A fresh install with no network history still knows where to look.
    empty = tempfile.mkdtemp(prefix='fns_disco_empty_')
    ext = make_ext(empty, baseurl=BUCKET)
    check('no document -> falls back to the par', ext.BaseUrl() == BUCKET,
          ext.BaseUrl())
    shutil.rmtree(empty, ignore_errors=True)

    print('\n3. the kill switch')
    write_doc(store, good(minimum='3.1.0'))
    ext = make_ext(store, pkgversion='3.0.0')
    refused, floor = ext._belowFloor()
    check('below the floor -> refused', refused is True and floor == '3.1.0',
          (refused, floor))
    ext = make_ext(store, pkgversion='3.1.0')
    check('exactly at the floor -> allowed', ext._belowFloor()[0] is False)
    ext = make_ext(store, pkgversion='3.2.0')
    check('above the floor -> allowed', ext._belowFloor()[0] is False)
    # 1.10 vs 1.9 is the case string comparison gets wrong.
    write_doc(store, good(minimum='1.9.0'))
    ext = make_ext(store, pkgversion='1.10.0')
    check('1.10.0 is not below 1.9.0', ext._belowFloor()[0] is False)

    print('\n4. the kill switch never strands the fleet')
    write_doc(store, good(minimum=''))
    check('empty floor -> allowed', make_ext(store)._belowFloor()[0] is False)
    write_doc(store, {'schema': 1, 'endpoints': {'manifest': MOVED}})
    check('absent floor -> allowed', make_ext(store)._belowFloor()[0] is False)
    with open(os.path.join(store, mod.DISCOVERY_CACHE), 'w') as f:
        f.write('{ broken')
    check('unreadable document -> allowed',
          make_ext(store)._belowFloor()[0] is False)

    print('\n5. notices')
    write_doc(store, good(notices=['one', '', '  ', 'two']))
    check('notices are returned, blanks dropped',
          make_ext(store).Notices() == ['one', 'two'],
          make_ext(store).Notices())
    write_doc(store, good())
    check('no notices -> empty list', make_ext(store).Notices() == [])

    print('\n6. pins are a non-empty, ordered, https-only tuple')
    check('pins is a tuple (immutable)', isinstance(mod.DISCOVERY_PINS, tuple))
    check('at least two pins', len(mod.DISCOVERY_PINS) >= 2)
    check('all https', all(u.startswith('https://') for u in mod.DISCOVERY_PINS))
    check('no duplicate hosts',
          len({u.split('/')[2] for u in mod.DISCOVERY_PINS})
          == len(mod.DISCOVERY_PINS))

    shutil.rmtree(store, ignore_errors=True)
    print()
    if FAILS:
        print('%d FAILED: %s' % (len(FAILS), ', '.join(FAILS)))
        return 1
    print('all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
