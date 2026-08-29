"""Where the entitlement credential lives: the OS keystore, never a file
we wrote ourselves.

Windows DPAPI or the macOS Keychain, both machine-locked and user-locked,
both dependency-free. Picked at call time by platform.

WHY NOT A PAR, AND WHY NOT THE CONFIG JSON (docs/ConfigScope.md):

  * Under `project` config scope the roaming JSON is never written and the
    .toe IS the store -- so a credential on a custom par would be saved
    into the file people share, commit and hand to clients.
  * Under `global` scope it lands in the roaming JSON, where SaveAll is
    last-writer-wins across every project on the machine.
  * There is no "always global, never project" hatch, so nothing
    STRUCTURALLY prevents the leak; it would rest on remembering a flag.

A keystore has none of those failure modes: the secret is not bytes in the
project tree at all.

WHAT IS STORED is only the opaque device token plus non-secret display
data (tier labels, entitled package names, when it was last checked). Never
a Patreon refresh token -- that stays on the gate, which can revoke it.

MAIN-THREAD NOTE: the Windows backend calls into ctypes and the macOS one
spawns `security`. Both are blocking OS calls, short but real, and neither
is safe to call from a worker thread that also touches TD. Call these from
the main thread only.

No TouchDesigner imports -- pure Python, testable outside TD.
"""

import sys
import time

IS_WINDOWS = sys.platform == 'win32'
IS_MACOS = sys.platform == 'darwin'


def backend():
    """The platform backend, or None where there is no keystore we trust.

    Returning None rather than raising is deliberate: an unsupported
    platform must degrade to "cannot stay signed in", not to a toolkit that
    raises on load. Linux TD builds exist and must not be broken by this."""
    try:
        if IS_WINDOWS:
            return mod('secure_storage_windows')
        if IS_MACOS:
            return mod('secure_storage_macos')
    except Exception:
        return None
    return None


def available():
    return backend() is not None


def Store(storage_dir, device_token, products=None, tiers=None, label='',
          checked_at=None):
    b = backend()
    if b is None:
        return False
    b.store(storage_dir, {
        'schema': 1,
        'device_token': device_token,
        'products': sorted(products or []),
        'tiers': sorted(tiers or []),
        'label': label,
        'stored_at': time.time(),
        # when the GATE last confirmed this entitlement -- every write
        # that carries products comes from a gate answer (token, recheck,
        # redeem), so store-time is that moment unless a caller knows
        # better. The picker renders freshness from this; it was emitted
        # as 0 forever because nothing ever wrote it.
        'checked_at': float(checked_at if checked_at is not None
                            else time.time()),
    })
    return True


def Load(storage_dir):
    b = backend()
    if b is None:
        return None
    data = b.load(storage_dir)
    if not isinstance(data, dict) or not data.get('device_token'):
        return None
    return data


def Clear(storage_dir):
    b = backend()
    if b is not None:
        b.clear(storage_dir)
