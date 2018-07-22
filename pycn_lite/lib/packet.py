# pycn_lite/lib/packet.py

# (c) 2018-01-27 <christian.tschudin@unibas.ch>

try:
    from uhashlib import sha1
except:
    from hashlib import sha1

from   pycn_lite.lib import hexlify
import pycn_lite.lib.suite.multi

# ---------------------------------------------------------------------------

class Name():

    def __init__(self, display_str = None, comps = None, suite=None,
                       suite_name='ndn2013', hashId=None):
        if suite:
            self._suite = suite
        else:
            self._suite = pycn_lite.lib.suite.multi.suite_from_str(suite_name)
        self._hashId = hashId
        self._publId = None
        self._comps = None
        if display_str:
            if display_str[-1] == '/':
                display_str = display_str[:-1]
            self._comps = [ pycn_lite.lib.escapedUTF8toComponent(c) \
                                        for c in display_str.split("/")[1:] ]
        if comps:
            self._comps = comps
        if self._comps is None:
            self._comps = []

    def to_string(self):
        # FIXME: escape binary values and '/' as part of a component
        comps = [ pycn_lite.lib.componentToEscapedUTF8(c) for c in self._comps ]
        s = '/' + '/'.join(comps)
        e = ''
        if self._hashId:
            e += " ,hashId=%s" % str(hexlify(self._hashId), 'ascii')
        if self._publId:
            e += " ,publId=%s" % str(hexlify(self._publId), 'ascii')
        if len(e) > 0:
            s += '[' + e[2:] + ']'
        return s

    # def to_wirebytes(self):
    #    return self._suite.name_components_to_wirebytes(self._comps)

    def is_prefix_of(self, name):
        if self._suite != name._suite or len(self._comps) > len(name._comps):
            return False
        for i in range(len(self._comps)):
            if self._comps[i] != name._comps[i]:
                return False
        return True

    def _hash(self):
        h = sha1()
        h.update(self._suite.Suite_name.encode('ascii'))
        for c in self._comps:
            h.update(c)
        return h.digest()

    def __hash__(self):
        return int.from_bytes(self._hash()[:8],'big')

    def __str__(self):
        return self.to_string()

    def __eq__(self, o):
        if      type(self) != type(o) or \
                self._suite != o._suite or \
                self._hashId != o._hashId or \
                self._publId != o._publId:
            return False
        return self._comps == o._comps

# ---------------------------------------------------------------------------

class InterestPacket():

    def __init__(self, name, wire=None, hashRestriction=None, payload=None):
        self._name = name
        self._wire = wire
        self._hashRestr = hashRestriction
        self._payload = payload

    def to_wirebytes(self): # returns wirebytes
        if not self._wire:
            s = self._name._suite.enc
            self._wire = s.encode_interest_wirebytes(self._name._comps,
                           hashId=self._hashRestr, payload=self._payload)
        return (self._wire, None)

# ---------------------------------------------------------------------------

class ContentPacket():

    def __init__(self, name, payload=None, wirebytes=None,
                       digest=None, meta=None):
        self._name   = name
        if payload:
            assert (type(payload) in [bytes, bytearray, memoryview]), "MUST be raw bytes"
        self._cont   = payload
        self._wire   = wirebytes
        self._digest = digest
        self._meta   = meta

    def to_wirebytes(self): # returns (wirebytes, digest)
        if not self._wire:
            s = self._name._suite.enc
            wb = s.encode_data_wirebytes(self._name._comps, self._cont)
            (self._wire, self._digest) = wb
        return (self._wire, self._digest)

    def get_content(self):
        return self._cont

# ---------------------------------------------------------------------------

class NackPacket():

    def __init__(self, name, wirebytes=None):
        self._name = name
        self._wire = wirebytes

    def to_wirebytes(self):
        if not self._wire:
            s = self._name._suite.enc
            self._wire = s.encode_nack_wirebytes(self._name._comps)
        return (self._wire, None)

# eof
