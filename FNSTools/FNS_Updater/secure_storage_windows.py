"""Windows credential storage via DPAPI.

Zero external dependencies -- ctypes straight to the Windows CryptoAPI.
Data is encrypted with the user's Windows login credentials, so it is
machine-locked AND user-locked: it cannot be decrypted on another machine,
or by another user on this one.

Adapted with permission from DOTsimulate's tox_updater (docs/
GatedDeliveryResearch.md 5b), with three changes: the storage directory is
passed IN rather than hardcoded to their AppData folder, the entropy is
ours, and the DLLs are loaded with use_last_error=True -- without it
ctypes.get_last_error() reads a private copy that the call never sets, so
every failure reported error code 0.

  https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata

No TouchDesigner imports: this module is pure Python and testable outside
TD, which is the point -- it is the piece that must not be wrong.
"""

import base64
import ctypes
import json
import os
from ctypes import POINTER, Structure, byref, c_char, create_string_buffer, wintypes

# Extra entropy: an attacker needs the user's Windows credentials AND this
# value. Changing it invalidates every token already stored on every
# machine, which is a silent forced sign-out -- so treat it as permanent.
ENTROPY = b'functionstore_fnstools_v1'

CRYPTPROTECT_UI_FORBIDDEN = 0x01     # never pop UI; we may be headless


class DATA_BLOB(Structure):
    _fields_ = [('cbData', wintypes.DWORD), ('pbData', POINTER(c_char))]


_crypt32 = ctypes.WinDLL('crypt32', use_last_error=True)
_kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)


def _blobBytes(blob):
    """Copy a DATA_BLOB out and free the memory Windows allocated for it."""
    n = int(blob.cbData)
    buf = create_string_buffer(n)
    ctypes.memmove(buf, blob.pbData, n)
    _kernel32.LocalFree(blob.pbData)
    return buf.raw


def _blob(data):
    buf = create_string_buffer(bytes(data), len(data))
    b = DATA_BLOB()
    b.cbData = len(data)
    b.pbData = ctypes.cast(buf, POINTER(c_char))
    # ctypes.cast keeps `buf` alive through the pointer's _objects, so the
    # buffer cannot be collected while the API call is using it.
    return b


def encrypt(data, entropy=ENTROPY):
    out = DATA_BLOB()
    ok = _crypt32.CryptProtectData(byref(_blob(data)), None, byref(_blob(entropy)),
                                   None, None, CRYPTPROTECT_UI_FORBIDDEN, byref(out))
    if not ok:
        raise RuntimeError('DPAPI encrypt failed (%d)' % ctypes.get_last_error())
    return _blobBytes(out)


def decrypt(blob, entropy=ENTROPY):
    out = DATA_BLOB()
    ok = _crypt32.CryptUnprotectData(byref(_blob(blob)), None, byref(_blob(entropy)),
                                     None, None, CRYPTPROTECT_UI_FORBIDDEN, byref(out))
    if not ok:
        raise RuntimeError('DPAPI decrypt failed (%d)' % ctypes.get_last_error())
    return _blobBytes(out)


def store(storage_dir, payload):
    os.makedirs(storage_dir, exist_ok=True)
    blob = encrypt(json.dumps(payload).encode('utf-8'))
    with open(os.path.join(storage_dir, 'auth.dat'), 'w', encoding='ascii') as f:
        f.write(base64.b64encode(blob).decode('ascii'))


def load(storage_dir):
    """The stored payload, or None.

    Returns None rather than raising for EVERY failure -- absent, corrupt,
    copied from another machine, or written by another user. All of them
    mean the same thing to a caller ("you are not signed in here"), and a
    raise would turn a foreign copy of a .toe into a broken toolkit."""
    path = os.path.join(storage_dir, 'auth.dat')
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='ascii') as f:
            return json.loads(decrypt(base64.b64decode(f.read())).decode('utf-8'))
    except Exception:
        return None


def clear(storage_dir):
    path = os.path.join(storage_dir, 'auth.dat')
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
