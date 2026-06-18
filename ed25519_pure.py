# ed25519_pure.py — Ed25519 puro Python, sin dependencias nativas
# Basado en el dominio público de djb/ed25519-donna
# Compatible con Python 3.13 + Android ARM64 sin compilación

import hashlib
import struct


# Constantes de la curva Ed25519
Q = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493


def _clamp(k):
    k_list = list(k)
    k_list[0] &= 248
    k_list[31] &= 127
    k_list[31] |= 64
    return bytes(k_list)


def _sha512(data: bytes) -> bytes:
    return hashlib.sha512(data).digest()


def _expmod(b, e, m):
    if e == 0:
        return 1
    t = _expmod(b, e >> 1, m) ** 2 % m
    if e & 1:
        t = t * b % m
    return t


def _inv(x):
    return _expmod(x, Q - 2, Q)


d = -121665 * _inv(121666) % Q
I = _expmod(2, (Q - 1) // 4, Q)


def _xrecover(y):
    x2 = (y * y - 1) * _inv(d * y * y + 1) % Q
    x = _expmod(x2, (Q + 3) // 8, Q)
    if (x * x - x2) % Q != 0:
        x = x * I % Q
    if x % 2 != 0:
        x = Q - x
    return x


B = [
    _xrecover(4 * _inv(5) % Q) % Q,
    4 * _inv(5) % Q
]


def _edwards(P, Q_pt):
    x1, y1 = P
    x2, y2 = Q_pt
    x3 = (x1 * y2 + x2 * y1) * _inv(1 + d * x1 * x2 * y1 * y2) % Q
    y3 = (y1 * y2 + x1 * x2) * _inv(1 - d * x1 * x2 * y1 * y2) % Q
    return [x3 % Q, y3 % Q]


def _scalarmult(P, e):
    if e == 0:
        return [0, 1]
    Q_pt = _scalarmult(P, e >> 1)
    Q_pt = _edwards(Q_pt, Q_pt)
    if e & 1:
        Q_pt = _edwards(Q_pt, P)
    return Q_pt


def _encodepoint(P):
    x, y = P
    bits = [(y >> i) & 1 for i in range(255)] + [x & 1]
    return bytes([sum([bits[i * 8 + j] << j for j in range(8)]) for i in range(32)])


def _decodepoint(s):
    y = sum([((s[i >> 3]) >> (i & 7)) & 1 << i for i in range(255)])
    x = _xrecover(y)
    if x & 1 != s[31] >> 7:
        x = Q - x
    return [x, y]


def _encodeint(y):
    return y.to_bytes(32, 'little')


def _decodeint(s):
    return int.from_bytes(s, 'little')


def _bit(h, i):
    return (h[i >> 3] >> (i & 7)) & 1


def publickey(sk: bytes) -> bytes:
    """Genera public key de 32 bytes desde seed de 32 bytes"""
    h = _sha512(sk)
    a = 2 ** (255 - 4) + sum(2 ** i * _bit(h, i) for i in range(3, 255 - 4 + 1))
    a += 2 ** 254
    return _encodepoint(_scalarmult(B, a))


def sign(msg: bytes, sk: bytes, pk: bytes) -> bytes:
    """Firma un mensaje. sk=seed 32 bytes, pk=public key 32 bytes"""
    h = _sha512(sk)
    a = 2 ** 254 + sum(2 ** i * _bit(h, i) for i in range(3, 255))
    r = _decodeint(_sha512(h[32:] + msg))
    R = _scalarmult(B, r)
    S = (r + _decodeint(_sha512(_encodepoint(R) + pk + msg)) * a) % L
    return _encodepoint(R) + _encodeint(S)
