"""Pure-python Ed25519 (RFC 8032) -- sign, verify, derive. Release tooling.

Why pure python: neither the release machine's Python nor TouchDesigner's
ships a crypto package, and a pip dependency on the signing path would be
one more thing a fresh machine forgets. This is the RFC 8032 reference
construction, validated by the RFC's own known-answer vectors in
tests/test_release_signing.py. It is slow (~10 ms/op) and that is fine:
it signs two small JSON documents per release.

The CLIENT does not import this -- ExtUpdater.py embeds its own verify
(a shipped DAT must be self-contained). The two implementations are
cross-checked against each other and the RFC vectors by the same test.
"""

import hashlib

_P = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_D = (-121665 * pow(121666, _P - 2, _P)) % _P
_I = pow(2, (_P - 1) // 4, _P)


def _sha512(m):
    return hashlib.sha512(m).digest()


def _inv(x):
    return pow(x, _P - 2, _P)


def _recover_x(y, sign):
    xx = (y * y - 1) * _inv(_D * y * y + 1) % _P
    x = pow(xx, (_P + 3) // 8, _P)
    if (x * x - xx) % _P != 0:
        x = x * _I % _P
    if (x * x - xx) % _P != 0:
        return None
    if x & 1 != sign:
        x = _P - x
    return x


_BY = 4 * _inv(5) % _P
_BX = _recover_x(_BY, 0)
_B = (_BX, _BY, 1, _BX * _BY % _P)     # extended coords (X, Y, Z, T)


def _add(p, q):
    a = (p[1] - p[0]) * (q[1] - q[0]) % _P
    b = (p[1] + p[0]) * (q[1] + q[0]) % _P
    c = 2 * p[3] * q[3] * _D % _P
    d = 2 * p[2] * q[2] % _P
    e, f, g, h = b - a, d - c, d + c, b + a
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _mul(s, p):
    q = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            q = _add(q, p)
        p = _add(p, p)
        s >>= 1
    return q


def _compress(p):
    z_inv = _inv(p[2])
    x = p[0] * z_inv % _P
    y = p[1] * z_inv % _P
    return int.to_bytes(y | ((x & 1) << 255), 32, 'little')


def _decompress(b):
    n = int.from_bytes(b, 'little')
    y = n & ((1 << 255) - 1)
    if y >= _P:
        return None
    x = _recover_x(y, n >> 255)
    if x is None:
        return None
    return (x, y, 1, x * y % _P)


def _equal(p, q):
    # x1/z1 == x2/z2 and y1/z1 == y2/z2, without divisions
    return ((p[0] * q[2] - q[0] * p[2]) % _P == 0
            and (p[1] * q[2] - q[1] * p[2]) % _P == 0)


def _clamp(h):
    a = int.from_bytes(h[:32], 'little')
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a


def public_from_seed(seed):
    """32-byte seed -> 32-byte public key."""
    a = _clamp(_sha512(seed))
    return _compress(_mul(a, _B))


def sign(seed, msg):
    """32-byte seed + message bytes -> 64-byte signature."""
    h = _sha512(seed)
    a = _clamp(h)
    pub = _compress(_mul(a, _B))
    r = int.from_bytes(_sha512(h[32:] + msg), 'little') % _L
    r_enc = _compress(_mul(r, _B))
    k = int.from_bytes(_sha512(r_enc + pub + msg), 'little') % _L
    s = (r + k * a) % _L
    return r_enc + int.to_bytes(s, 32, 'little')


def verify(pub, sig, msg):
    """32-byte public key, 64-byte signature, message bytes -> bool."""
    if len(pub) != 32 or len(sig) != 64:
        return False
    a = _decompress(pub)
    r = _decompress(sig[:32])
    if a is None or r is None:
        return False
    s = int.from_bytes(sig[32:], 'little')
    if s >= _L:
        return False
    k = int.from_bytes(_sha512(sig[:32] + pub + msg), 'little') % _L
    return _equal(_mul(s, _B), _add(r, _mul(k, a)))
