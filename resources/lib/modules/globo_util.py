import time
import base64
import hashlib
import random


# methods below are part of globo hashing scheme
# original procedure at http://s.videos.globo.com/p2/j/api.min.js
# version > 2.5.4
def get_signed_hashes(a):
    return P(bytes(a.encode('ascii'))).decode('ascii')


G = 3600
H = b"0xAC10FD"

table1 = bytes.maketrans(b'/+', b'_-')


def J(a):
    digest = hashlib.md5(a + H).digest()
    return base64.b64encode(digest).translate(table1, b'=')


def K(a):
    digest = hashlib.md5(a + H).digest()
    return base64.b16encode(digest).replace(b'=', b'')


def L():
    return b'%010d' % random.randint(1, int(1e10))


def M(a):
    b, c, d, e = (a[0:2], a[2:12], a[12:22], a[22:44])
    f, g = (int(c) + G, L())
    h = J(b'%s%d%s' % (e, f, g))
    return b'%s%s%s%s%d%s%s' % (b'05', b, c, d, f, g, h)


def N():
    return int(time.time())


def O(a):
    b, c, d, e, f, g, h = (
            a[0:2], a[2:3], a[3:13], a[13:23], a[24:46],
            N() + G, L())
    i = J(b'%s%d%s' % (f, g, h))
    return b'%s%s%s%s%d%s%s' % (b, c, d, e, g, h, i)


def P(a):
    b, c, d, e, f = (b'04', b'03', b'02', b'', a[0:2])
    return (f == b and O(a) or
            (f == c or f == d) and M(a) or e)
