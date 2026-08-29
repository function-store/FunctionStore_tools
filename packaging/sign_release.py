"""Release signing: hold the key, sign the two documents everything trusts.

    python packaging/sign_release.py --init          # generate the keypair
    python packaging/sign_release.py --pubkey        # print the public key
    python packaging/sign_release.py --sign FILE...  # write FILE.sig each

The PRIVATE KEY LIVES OUTSIDE THE REPO (owner decision, 2026-08-28):
%USERPROFILE%/.fnstools-release/signing.key -- a 32-byte Ed25519 seed as
hex. Override with FNS_SIGNING_KEY=<path>. It must never enter the repo,
a staged artifact, or the bucket; back it up offline, because a lost key
means shipping a new key generation (a component update every install
must take on trust once, exactly like a pin-list change).

WHAT GETS SIGNED: manifest.json and fnstools.json -- the two documents
the whole chain trusts. Artifact hashes already verify downloads AGAINST
the manifest; these signatures are what verify the manifest itself. The
signature is Ed25519 over the exact file bytes, written as FILE.sig
(base64, one line). publish.Stage() signs at staging time and refuses an
unsigned release unless FNS_ALLOW_UNSIGNED=1 (the offline-test hatch).

The matching PUBLIC key is pinned in ExtUpdater.py (SIGNING_PUBKEY_HEX,
beside DISCOVERY_PINS, same contract: a new key is a new generation of
the component, never an update).
"""

import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ed25519_ref  # noqa: E402

DEFAULT_KEY = os.path.join(os.path.expanduser('~'), '.fnstools-release',
                           'signing.key')


def key_path():
    return os.environ.get('FNS_SIGNING_KEY') or DEFAULT_KEY


def load_seed(path=None):
    """The 32-byte seed, or None when no key exists at the path."""
    path = path or key_path()
    try:
        with open(path, encoding='utf-8') as f:
            seed = bytes.fromhex(f.read().strip())
    except Exception:
        return None
    return seed if len(seed) == 32 else None


def public_hex(path=None):
    seed = load_seed(path)
    return ed25519_ref.public_from_seed(seed).hex() if seed else None


def init_key(path=None):
    path = path or key_path()
    if os.path.exists(path):
        sys.exit('refusing to overwrite the existing key at %s -- a '
                 'replaced key strands every pinned install' % path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    seed = os.urandom(32)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(seed.hex() + '\n')
    pub = ed25519_ref.public_from_seed(seed).hex()
    with open(path[:-4] + '.pub', 'w', encoding='utf-8') as f:
        f.write(pub + '\n')
    return path, pub


def sign_file(file_path, key=None):
    """Sign the exact bytes of file_path; write file_path + '.sig'.

    Returns the sig path. Raises when no key is loadable -- the caller
    decides whether unsigned is allowed (publish.Stage refuses unless
    FNS_ALLOW_UNSIGNED=1)."""
    seed = load_seed(key)
    if seed is None:
        raise RuntimeError('no signing key at %s (run sign_release.py '
                           '--init, or set FNS_SIGNING_KEY)' % (key or key_path()))
    with open(file_path, 'rb') as f:
        body = f.read()
    sig = ed25519_ref.sign(seed, body)
    out = file_path + '.sig'
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(base64.b64encode(sig).decode('ascii') + '\n')
    return out


if __name__ == '__main__':
    args = sys.argv[1:]
    if args[:1] == ['--init']:
        path, pub = init_key()
        print('key written:', path)
        print('public key (pin this in ExtUpdater.SIGNING_PUBKEY_HEX):', pub)
    elif args[:1] == ['--pubkey']:
        pub = public_hex()
        sys.exit(0 if print(pub) is None and pub else 'no key at %s' % key_path())
    elif args[:1] == ['--sign'] and len(args) > 1:
        for f in args[1:]:
            print('signed:', sign_file(f))
    else:
        sys.exit(__doc__)
