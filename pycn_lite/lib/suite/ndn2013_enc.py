# pycn_lite/lib/suite/ndn2013_enc.py

# (c) 2015-06-13 and 2018-01-27 <christian.tschudin@unibas.ch>

# encoder for NDN packets
# this module is not needed for forwarding and repo, saves memory for ESP8266

try:
    from uhashlib import sha256
except:
    from hashlib import sha256
import os

import pycn_lite.lib.suite.ndn2013 as ndn

# ----------------------------------------------------------------------
# creating TLVs

def mkTorL(x):
    if x < 253:
        return bytes([x])
    if x < 0x10000:
        return bytes([253, x >> 8, x & 0x0ff])
    if x < 0x100000000:
        return b'\xfe' + x.to_bytes(4, 'big')
    return b'\xff' + x.to_bytes(8, 'big')

def byte_length(v):
    v, n = (v>>8, 1)
    while v != 0:
        n += 1
        v >>= 8
    return n

def prepend_uint(buf, start, v, t = None): # returns new start
    b = v.to_bytes(byte_length(v), 'big')
    return prepend_blob(buf, start, b, t=t)

def prepend_blob(buf, oldstart, blob, t=None): # returns new start
    newstart = oldstart - len(blob)
    buf[newstart:oldstart] = blob
    if t is None:
        return newstart
    return prepend_tl(buf, newstart, t, len(blob))

def prepend_tl(buf, start, t, l): # returns new start
    start = prepend_blob(buf, start, mkTorL(l))
    return prepend_blob(buf, start, mkTorL(t))

def prepend_name(buf, start, comps):  # returns new start
    end = start
    for i in range(len(comps)-1, -1, -1):
        start = prepend_blob(buf, start, comps[i], t=ndn.T_NameComponent)
        # start = prepend_tl(buf, start, ndn.T_NameComponent, len(comps[i]))
    return prepend_tl(buf, start, ndn.T_Name, end - start)

def prepend_empty_signature(buf, start):
    # DigestSha256 signature info + empty value
    start = prepend_blob(buf, start, b'\x17\x00')
    return prepend_blob(buf, start, b'\x16\x03\x1b\x01\x00')

def prepend_metainfo(buf, start, contentType = None):
    if contentType is None:
        return prepend_blob(buf, start, b'\x14\x00')
    metaEnd = start
    start = prepend_uint(buf, start, contentType, ndn.T_ContentType)
    return prepend_tl(buf, start, ndn.T_MetaInfo, metaEnd - start)

def finalize(buf, dummyPT=None):
    h = sha256()
    h.update(buf)
    return (buf, h.digest())

# ---------------------------------------------------------------------------

def encode_interest_wirebytes(comps, hashId = None, payload = None):
    assert payload == None
    buf = bytearray(ndn.MAX_CHUNK_SIZE)
    start = len(buf) - 4
    buf[start:] = os.urandom(4)
    start = prepend_tl(buf, start, ndn.T_Nonce, 0x04)
    if hashId:
        start = prepend_blob(buf, start, hashId, t=ndn.T_HashID)
    start = prepend_name(buf, start, comps)
    start = prepend_tl(buf, start, ndn.T_Interest, len(buf) - start)
    return buf[start:]

def encode_data_wirebytes(comps, blob):
    buf = bytearray(ndn.MAX_CHUNK_SIZE)
    start = prepend_empty_signature(buf, len(buf))
    end = start
    start = prepend_blob(buf, start, blob, t=ndn.T_Content)
    start = prepend_metainfo(buf, start)
    start = prepend_name(buf, start, comps)
    start = prepend_tl(buf, start, ndn.T_Data, end - start)
    return finalize(buf[start:])

def encode_nack_wirebytes(comps, blob=None):
    buf = bytearray(ndn.MAX_CHUNK_SIZE)
    start = prepend_empty_signature(buf, len(buf))
    end = start
    if blob == None:
        blob = ''
    start = prepend_blob(buf, start, blob, t=ndn.T_Content)
    start = prepend_metainfo(buf, start, contentType_nack)
    start = prepend_name(buf, start, comps)
    start = prepend_tl(buf, start, ndn.T_Data, end - start)
    return finalize(buf[start:])

# eof
