# pycn_lite/icn/lib/flic_dec.py

# (c) 2018-02-10 <christian.tschudin@unibas.ch>

# reconstruct a data collection organized via FLIC

import copy

# ----------------------------------------------------------------------

def isRootManifest(pkt):
    return False

def bytesFromManifestName(nwAccess, rootManifest):
        rootManifest._name._comps.pop() # drop the last component (e.g. '_')
        return _manifestToBytes(nwAccess, rootManifest._name,
                                rootManifest.get_content())

def _indexTable2data(nwAccess, pfx, hashGroup):
    # traverse the hashgroup (manifest subtree)
    # input: index table (hashgroup, i.e. sequence of hash pointers)
    # output: reassembled data
    s = pfx._suite
    out = b''
    cnt = 0
    while len(hashGroup) > 0:
        t, l, tail = s.readTL(hashGroup)
        if t == s.T_MANIFEST_HG_PTR2DATA:
            cnt += 1
            pkt = nwAccess.fetch_pkt(pfx, tail[:l])
            out += pkt.get_content()
        elif t == s.T_MANIFEST_HG_PTR2MANIFEST:
            pkt = nwAccess.fetch_pkt(pfx, tail[:l])
            out += _manifestToBytes(nwAccess, pfx, pkt.get_content())
        else:
            print("invalid index table entry")
            return out
        hashGroup = tail[l:]
    return out

def _manifestToBytes(nwAccess, pfx, manifestBytes):
    # input: manifest (only the payload of the chunk)
    # output: re-assembled raw e2e bytes
    data = memoryview(manifestBytes)
    out = b''
    s = pfx._suite
    while len(data) > 0:
        t, l, tail = s.readTL(data)
        if t != s.T_MANIFEST_HASHGROUP:
            raise EOFError
        out += _indexTable2data(nwAccess, pfx, tail[:l])
        data = tail[l:]
    return out

def bytesFromManifestName(self, name):
    chunk = self.icn.readChunk(name)
    content = NdnTlvEncoder().decode(chunk)
    name._components.pop() # drop the last component (e.g. '_')
    return self._manifestToBytes(name, content.get_bytes())

# TODO:
# def iterFromName(self, name):
#    return DeFLIC_ITER(...)
