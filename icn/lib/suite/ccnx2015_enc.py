# pycn_lite/icn/lib/suite/ccnx2015.py

# (c) 2018-02-01 <christian.tschudin@unibas.ch>

# encoder for CCNX packets
# this module is not needed for forwarding and repo, saves memory for ESP8266

try:
    from uhashlib import sha256
    import ustruct   as struct
except:
    from hashlib import sha256
    import struct

import icn.lib.suite.ccnx2015 as ccnx

# ----------------------------------------------------------------------
# creating TLVs

# def mk_name_tlv(comps):

def prepend_int(buf, start, v): # returns new start
    while True:
        start -= 1
        buf[start] = v & 0x0ff
        v >>= 8
        if v == 0:
            break
    return start

def prepend_blob(buf, start, blob): # returns new start
    start = start - len(blob)
    buf[start:start + len(blob)] = blob
    return start

def prepend_tl(buf, start, t, l): # returns new start
    if start < 4:
        raise IOError
    struct.pack_into('>H', buf, start-2, l)
    struct.pack_into('>H', buf, start-4, t)
    return start - 4

def prepend_name(buf, start, comps):  # returns new start
    end = start
    for i in range(len(comps)-1, -1, -1):
        start = prepend_blob(buf, start, comps[i])
    start = prepend_tl(buf, start, ccnx.CCNX_TLV_M_Name, end - start)
    return start

#def name_components_to_wirebytes(comps):
#    n = b''
#    for c in comps:
#        n += c
#    tl = bytearray(4)
#    struct.pack_into('>H', tl, 2, len(n))
#    struct.pack_into('>H', tl, 0, CCNX_TLV_M_Name)
#    return tl + n

#    buf = bytearray(3000)
#    offs = prepend_name(buf, len(buf), comps)
#    buf = buf[offs:]
#    return buf

# ----------------------------------------------------------------------

def encode_interest_wirebytes(comps, hashId = None):
    buf = bytearray(ccnx.MAX_CHUNK_SIZE)
    start = len(buf)
    if hashId:
        start = prepend_blob(buf, start, hashId)
        start = prepend_tl(buf, start, ccnx.CCNX_TLV_M_ObjHashRestriction,
                           len(hashId))
    start = prepend_name(buf, start, comps)
    start = prepend_tl(buf, start, ccnx.CCNX_TLV_TL_Interest, len(buf) - start)
    hdr = bytearray(b'\x01\x00  \x10\x00\x00\x08')
    struct.pack_into('>H', hdr, 2, len(buf) - start + len(hdr))
    return hdr + buf[start:]

def encode_data_wirebytes(comps, blob):
    buf = bytearray(ccnx.MAX_CHUNK_SIZE)
    start = len(buf)
    start = prepend_blob(buf, start, blob)
    start = prepend_tl(buf, start, ccnx.CCNX_TLV_M_Payload, len(blob))
    start = prepend_name(buf, start, comps)
    start = prepend_tl(buf, start, ccnx.CCNX_TLV_TL_Object, len(buf) - start)
    h = sha256()
    h.update(buf[start:])
    hdr = bytearray(b'\x01\x01  \x10\x00\x00\x08')
    struct.pack_into('>H', hdr, 2, len(buf) - start + len(hdr))
    return (hdr + buf[start:], h.digest())

def encode_nack_wirebytes(comps, blob=None):
    # ccnx does not have a app-level nack?
    return None

# eof
