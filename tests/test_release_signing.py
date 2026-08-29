"""Offline tests of the release-signing chain.

Three implementations must agree: the RFC 8032 vectors (the standard's
own known answers), packaging/ed25519_ref.py (the signer), and the verify
embedded in ExtUpdater.py (the shipped client -- self-contained because a
DAT cannot import from packaging/). Then the client's classification
policy: 'bad' only for a well-formed signature that fails -- tamper
evidence, always refused -- while absent/garbage/error-page sigs are
'unsigned', which the REQUIRE_SIGNED transition flag owns.

    python tests/test_release_signing.py
"""
import base64
import builtins
import os
import sys
import tempfile
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, 'packaging'))
import ed25519_ref  # noqa: E402
import sign_release  # noqa: E402

FAILS = []


def check(label, cond, detail=''):
    if cond:
        print('  PASS  %s' % label)
    else:
        print('  FAIL  %s %s' % (label, detail))
        FAILS.append(label)


# ---- load ExtUpdater under TD stubs (same recipe as test_updater_verify) --
SRC = os.path.join(_ROOT, 'modules', 'suspects', 'FNSTools',
                   'FNS_Updater', 'ExtUpdater.py')
builtins.op = lambda p=None: None
builtins.debug = lambda *a, **k: None
builtins.run = lambda *a, **k: None
builtins.ui = types.SimpleNamespace(messageBox=lambda *a, **k: None)
builtins.project = types.SimpleNamespace(name='test')
builtins.absTime = types.SimpleNamespace(seconds=0)


def _fc(fn=None, **kw):
    return fn if fn is not None else (lambda f: f)


_fm = types.SimpleNamespace(fns_command=_fc, fns_announce=lambda c: None)
_fe = types.SimpleNamespace(tags={'ExtUtils'}, mod=lambda n: _fm)
builtins.me = types.SimpleNamespace(docked=[_fe])
builtins.tdu = types.SimpleNamespace()
mod = types.ModuleType('ExtUpdater')
mod.__dict__['__file__'] = SRC
exec(compile(open(SRC, encoding='utf-8').read(), SRC, 'exec'), mod.__dict__)


print('1. RFC 8032 known answers (TESTs 1-3) against BOTH implementations')
VECTORS = [
    ('9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60',
     'd75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a', '',
     'e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555f'
     'b8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b'),
    ('4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb',
     '3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c', '72',
     '92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da08'
     '5ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00'),
    ('c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7',
     'fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025', 'af82',
     '6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac18'
     'ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a'),
]
for i, (seed_h, pub_h, msg_h, sig_h) in enumerate(VECTORS, 1):
    seed, pub = bytes.fromhex(seed_h), bytes.fromhex(pub_h)
    msg, sig = bytes.fromhex(msg_h), bytes.fromhex(sig_h)
    check('T%d ref derives the public key' % i,
          ed25519_ref.public_from_seed(seed) == pub)
    check('T%d ref signs the known answer' % i,
          ed25519_ref.sign(seed, msg) == sig)
    check('T%d ref verifies' % i, ed25519_ref.verify(pub, sig, msg))
    check('T%d CLIENT verifies the same' % i,
          mod._ed25519_verify(pub, sig, msg))
    check('T%d client refuses tamper' % i,
          not mod._ed25519_verify(pub, sig, msg + b'x'))
    bad = bytearray(sig)
    bad[3] ^= 1
    check('T%d client refuses a flipped bit' % i,
          not mod._ed25519_verify(pub, bytes(bad), msg))

print('2. signer -> shipped-client roundtrip with a fresh key')
seed = os.urandom(32)
pub = ed25519_ref.public_from_seed(seed)
body = b'{"release": "v9.9.9", "packages": []}\n'
sig = ed25519_ref.sign(seed, body)
check('fresh-key roundtrip verifies in the client',
      mod._ed25519_verify(pub, sig, body))
check('a different key refuses',
      not mod._ed25519_verify(ed25519_ref.public_from_seed(os.urandom(32)),
                              sig, body))

print('3. sign_release file flow against the PINNED production key path')
tmp = tempfile.mkdtemp(prefix='fns_sig_')
key = os.path.join(tmp, 'k.key')
with open(key, 'w', encoding='utf-8') as f:
    f.write(os.urandom(32).hex())
doc = os.path.join(tmp, 'manifest.json')
with open(doc, 'wb') as f:
    f.write(body)
sig_path = sign_release.sign_file(doc, key=key)
check('sign_file writes the sidecar', sig_path == doc + '.sig'
      and os.path.exists(sig_path))
test_pub = ed25519_ref.public_from_seed(sign_release.load_seed(key))

print('4. the client classification policy (_signatureState)')
mod.SIGNING_PUBKEY_HEX = test_pub.hex()      # pin the test key for this block
check("signed doc -> 'verified'",
      mod._signatureState(doc, sig_path) == 'verified')
with open(doc, 'ab') as f:
    f.write(b' ')                             # tamper AFTER signing
check("tampered doc -> 'bad' (refused, never 'unsigned')",
      mod._signatureState(doc, sig_path) == 'bad')
with open(doc, 'wb') as f:
    f.write(body)                             # restore
check("restored doc -> 'verified' again",
      mod._signatureState(doc, sig_path) == 'verified')
with open(sig_path, 'w', encoding='utf-8') as f:
    f.write('<html>404 Not Found</html>')     # a CDN error page as the sig
check("error-page sig -> 'unsigned' (transition policy decides)",
      mod._signatureState(doc, sig_path) == 'unsigned')
os.remove(sig_path)
check("absent sig -> 'unsigned'",
      mod._signatureState(doc, sig_path) == 'unsigned')
with open(sig_path, 'w', encoding='utf-8') as f:
    f.write(base64.b64encode(os.urandom(64)).decode())   # well-formed garbage
check("well-formed wrong sig -> 'bad'",
      mod._signatureState(doc, sig_path) == 'bad')

print('5. the shipped pin is a real key, and the real key file signs for it')
pinned = bytes.fromhex(mod.__dict__['ExtUpdater'].__module__ and
                       open(SRC, encoding='utf-8').read().split(
                           "SIGNING_PUBKEY_HEX = '")[1].split("'")[0])
check('pinned key is 32 bytes', len(pinned) == 32)
real_seed = sign_release.load_seed()
if real_seed is not None:
    check('the local signing key derives the PINNED public key',
          ed25519_ref.public_from_seed(real_seed) == pinned,
          '(key at %s does not match the pin!)' % sign_release.key_path())
else:
    print('  skip  no local signing key on this machine (pin not checked '
          'against it)')

print()
if FAILS:
    print('FAILED (%d): %s' % (len(FAILS), ', '.join(FAILS)))
    sys.exit(1)
print('all checks passed')
