# pycn_lite/icn/lib/suite/ndn2013_enc.py

# (c) 2015-06-13 and 2018-01-27 <christian.tschudin@unibas.ch>

# encoder for NDN packets
# this module is not needed for forwarding and repo, saves memory for ESP8266

try:
    from uhashlib import sha256
except:
    from hashlib import sha256
import os

import icn.lib.suite.ndn2013 as ndn

# ----------------------------------------------------------------------
# creating TLVs

def mkTorL(x):
    if x < 253:
        buf = bytes([x])
    elif x < 0x10000:
        buf = bytes([253, x >> 8, x & 0x0ff])
    elif x < 0x100000000:
        buf = b'\xfe    '
        for i in range(4,1,-1):
            b[i] = x & 0x0ff
            x >>= 8
    else:
        buf = b'\xff        '
        for i in range(8,1,-1):
            b[i] = x & 0x0ff
            x >>= 8
    return buf

# def mk_name_tlv(comps):

def prepend_int(buf, start, v): # returns new start
    return prepend_blob(buf, start, mkTorL(v))

def prepend_blob(buf, oldstart, blob): # returns new start
    newstart = oldstart - len(blob)
    buf[newstart:oldstart] = blob
    return newstart

def prepend_tl(buf, start, t, l): # returns new start
    start = prepend_int(buf, start, l)
    start = prepend_int(buf, start, t)
    return start

def prepend_name(buf, start, comps):  # returns new start
    end = start
    for i in range(len(comps)-1, -1, -1):
        start = prepend_blob(buf, start, comps[i])
        start = prepend_tl(buf, start, ndn.T_NameComponent, len(comps[i]))
    start = prepend_tl(buf, start, ndn.T_Name, end - start)
    return start

#def name_components_to_wirebytes(comps):
#    n = b''
#    for c in comps:
#        # if type(c) != str:
#        #    c = c.getValue().toBytes()
#        n += mkTorL(ndn.T_NameComponent) + mkTorL(len(c)) + c
#    return mkTorL(ndn.T_Name) + mkTorL(len(n)) + n

#    buf = bytearray(3000)
#    offs = prepend_name(buf, len(buf), comps)
#    buf = buf[offs:]
#    return buf

# ---------------------------------------------------------------------------

def encode_interest_wirebytes(comps, hashId = None):
    buf = bytearray(ndn.MAX_CHUNK_SIZE)
    start = len(buf) - 4
    buf[start:] = os.urandom(4)
    start = prepend_tl(buf, start, ndn.T_Nonce, 0x04)
    if hashId:
        start = prepend_blob(buf, start, hashId)
        start = prepend_tl(buf, start, ndn.T_HashID, len(hashId))
    start = prepend_name(buf, start, comps)
    start = prepend_tl(buf, start, ndn.T_Interest, len(buf) - start)
    return buf[start:]

def encode_data_wirebytes(comps, blob):
    buf = bytearray(ndn.MAX_CHUNK_SIZE)
    start = len(buf)
    # DigestSha256 signature info + empty value
    start = prepend_blob(buf, start, bytearray([0x17, 0x00]))
    start = prepend_blob(buf, start, bytearray([0x16, 0x03, 0x1b, 0x01, 0x00]))
    start = prepend_blob(buf, start, blob)
    start = prepend_tl(buf, start, ndn.T_Content, len(blob))
    # empty metadata
    start = prepend_blob(buf, start, bytearray([ndn.T_MetaInfo, 0x00]))
    start = prepend_name(buf, start, comps)
    start = prepend_tl(buf, start, ndn.T_Data, len(buf) - start)
    buf = buf[start:]
    h = sha256()
    h.update(buf)
    return (buf, h.digest())

def encode_nack_wirebytes(comps, blob=None):
    buf = bytearray(ndn.MAX_CHUNK_SIZE)
    start = len(buf)
    # DigestSha256 signature info + empty value
    start = prepend_blob(buf, start, bytearray([0x17, 0x00]))
    start = prepend_blob(buf, start, bytearray([0x16, 0x03, 0x1b, 0x01, 0x00]))
    if blob == None:
        blob = ''
    else:
        start = prepend_blob(buf, start, blob)
    start = prepend_tl(buf, start, ndn.T_Content, len(blob))
    # metadata with nack
    metaEnd = start
    start = prepend_blob(buf, start, bytearray([contentType_nack]))
    start = prepend_tl(buf, start, ndn.T_ContentType, metaEnd - start)
    start = prepend_tl(buf, start, ndn.T_MetaInfo, metaEnd - start)
    start = prepend_name(buf, start, comps)
    start = prepend_tl(buf, start, ndn.T_Data, len(buf) - start)
    return buf[start:]


# eof
