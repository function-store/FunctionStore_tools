"""macOS credential storage via the login Keychain.

Same contract as secure_storage_windows: store / load / clear a small JSON
payload, machine- and user-locked, with no external dependency. The `security`
binary ships with macOS, so this needs nothing installed.

`storage_dir` is accepted and ignored -- the Keychain is not a directory. It
is in the signature so the two backends are interchangeable and the
dispatcher never has to branch on platform beyond picking one.

No TouchDesigner imports.
"""

import json
import subprocess

SERVICE = 'xyz.functionstore.fnstools'
ACCOUNT = 'entitlement'


def _run(args, payload=None):
    """`security` with no shell and no terminal prompt. Returns
    (returncode, stdout)."""
    p = subprocess.run(
        ['security'] + args,
        input=payload, capture_output=True, text=True, check=False,
    )
    return p.returncode, (p.stdout or '')


def store(storage_dir, payload):
    blob = json.dumps(payload)
    # -U updates in place when the item already exists; without it a second
    # sign-in fails with "item already exists" rather than replacing.
    code, _ = _run(['add-generic-password', '-U',
                    '-s', SERVICE, '-a', ACCOUNT, '-w', blob])
    if code != 0:
        raise RuntimeError('Keychain write failed (%d)' % code)


def load(storage_dir):
    """The stored payload, or None -- for absent, locked, or unreadable
    alike. A caller only ever needs to know whether this machine is signed
    in, and a raise would turn a foreign copy of a .toe into a broken
    toolkit."""
    code, out = _run(['find-generic-password', '-s', SERVICE, '-a', ACCOUNT, '-w'])
    if code != 0 or not out.strip():
        return None
    try:
        return json.loads(out.strip())
    except Exception:
        return None


def clear(storage_dir):
    _run(['delete-generic-password', '-s', SERVICE, '-a', ACCOUNT])
