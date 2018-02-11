# pycn_lite/server/repo_fs.py

# (c) 2018-01-27 <christian.tschudi@unibas.ch>

'''

A file-system based repo for ICN content that
- is multi-suite (NDN and CCNx)
- remembers valid prefixes

chunks are stored in files named as follows:
  hex(icnname)[:24] + '.' + hex(chunk.digest)[:24]
  (the chunk.digest is suite-specific, it's not always the sha256 of the bytes)

prefixes are stores as interest packets in files named as follows:
  'prefix.' + sha1(interestPacket)[:24]

'''

try:
    from uhashlib import sha1
except:
    from hashlib  import sha1
import os

from   pycn_lite.lib import hexlify
import pycn_lite.lib.packet
import pycn_lite.lib.suite.multi

# ----------------------------------------------------------------------

class RepoFS():

    def __init__(self, repopath, prefixes = [], suite='ndn2013'):
        self._path = repopath
        self._prefixes = []
        for fn in os.listdir(self._path):
            t = fn.split('.')
            if t[0] != 'prefix':
                continue
            with open(self._path + '/' + fn, 'rb') as f:
                buf = f.read()
            pkt = pycn_lite.lib.suite.multi.decode_wirebytes(buf)
            if not isinstance(pkt, pycn_lite.lib.packet.InterestPacket):
                continue
            self._prefixes.append(pkt._name)
        for pfx in prefixes:
            if not pfx in self._prefixes:
                wb = pfx._suite.enc.encode_interest_wirebytes(pfx._comps)
                h = sha1()
                h.update(wb)
                fn = self._path + '/prefix.' + h.hexdigest()[:24]
                with open(fn, 'wb') as f:
                    f.write(wb)
                self._prefixes.append(pfx)

    def name2pattern(self, name, digest):
        fn = hexlify(name._hash())[:24]
        fn = bytes(fn).decode('ascii')
        if digest:
            digest = hexlify(digest)[:24]
            return (fn, bytes(digest).decode('ascii'))
        else:
            return (fn, '*')

    def get_chunk_bytes(self, name):
        fnpattern = None
        for pfx in self._prefixes:
            if pfx.is_prefix_of(name):
                fnpattern = self.name2pattern(name, name._hashId)
                break
        if not fnpattern:
            return None
        for fn in os.listdir(self._path):
            t = fn.split('.')
            if len(t) != 2 or t[0] != fnpattern[0]:
                continue
            if fnpattern[1] != '*' and t[1] != fnpattern[1]:
                continue
            fn = self._path + '/' + fn
            with open(fn, 'rb') as f:
                chunk = f.read()
            return chunk
        return None

# eof
