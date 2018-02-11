#!/usr/bin/env python3

# pycn_lite/lib/suite/ccnx2015_dump.py

# (c) 2018-02-01 <christian.tschudin@unibas.ch>

import sys

try:
    from uhashlib import sha256
    import ustruct    as struct
    sys.path.append(sys.path[0] + '/../..')
    def read_from_stdin():
        return bytearray(sys.stdin.read())
except:
    from hashlib import  sha256
    import struct
    def read_from_stdin(): # b/c we need the raw bytes, not a str
        return sys.stdin.buffer.read()

import pycn_lite.lib
import pycn_lite.lib.suite.ccnx2015 as ccnx

# ---------------------------------------------------------------------------

# content payload type (Sect 3.6.2.2.1)
CCNX_PAYLDTYPE_Data                     = 0
CCNX_PAYLDTYPE_Key                      = 1
CCNX_PAYLDTYPE_Link                     = 2
CCNX_PAYLDTYPE_Manifest                 = 3

# manifest (flic)
CCNX_MANIFEST_HASHGROUP                 = 1
CCNX_MANIFEST_HG_METADATA               = 1
CCNX_MANIFEST_HG_PTR2DATA               = 2
CCNX_MANIFEST_HG_PTR2MANIFEST           = 3
CCNX_MANIFEST_MT_LOCATOR                = 0 # == CCNX_TLV_M_Name
CCNX_MANIFEST_MT_EXTERNALMETADATA       = 1 # == CCNX_TLV_M_Name
CCNX_MANIFEST_MT_BLOCKSIZE              = 2
CCNX_MANIFEST_MT_OVERALLDATASIZE        = 3
CCNX_MANIFEST_MT_OVERALLDATASHA256      = 4
CCNX_MANIFEST_MT_TREEDEPTH              = 5

# validation algorithms (Sect 3.6.4.1)
CCNX_VALIDALGO_CRC32C                   = 2
CCNX_VALIDALGO_HMAC_SHA256              = 4
CCNX_VALIDALGO_VMAC_128                 = 5
CCNX_VALIDALGO_RSA_SHA256               = 6
CCNX_VALIDALGO_EC_SECP_256K1            = 7
CCNX_VALIDALGO_EC_SECP_384R1            = 8

# validation dependent data (Sect 3.6.4.1.4)
CCNX_VALIDALGO_KEYID                    = 9
CCNX_VALIDALGO_PUBLICKEY                = 0x000b
CCNX_VALIDALGO_CERT                     = 0x000c
CCNX_VALIDALGO_KEYNAME                  = 0x000e
CCNX_VALIDALGO_SIGTIME                  = 0x000f

# CCNX_TLV_IntFrag                        0x0001 // TODO: correct type value?
# CCNX_TLV_ObjFrag                        0x0002 // TODO: correct type value?

# contexts (identifier scopes)
CTX_GLOBAL                  = 1
CTX_TOPLEVEL                = 2
CTX_MSG                     = 3
CTX_NAME                    = 4
CTX_MFST                    = 5
CTX_MFST_HASHGRP            = 6
CTX_MFST_HASHGRP_METADATA   = 7
CTX_METADATA                = 8
CTX_VALIDALGO               = 9
CTX_VALIDALGODEPEND         = 10

ccnx2015tlv_typenames = {
    CTX_GLOBAL: {
        -1:                            'globalCtx',
        ccnx.CCNX_TLV_G_Pad:                'G_Pad'
    },
    CTX_TOPLEVEL: {
        # top level(Sect 3.4)
        -1:                            'toplevelCtx',
        ccnx.CCNX_TLV_TL_Interest:          'Interest',
        ccnx.CCNX_TLV_TL_Object:            'Object',
        ccnx.CCNX_TLV_TL_ValidationAlgo:    'ValidationAlgo',
        ccnx.CCNX_TLV_TL_ValidationPayload: 'ValidationPayload',
        ccnx.CCNX_TLV_TL_Fragment:          'Fragment',
        ccnx.CCNX_TLV_TL_Manifest:          'Manifest'
    },
    CTX_MSG: {
        -1:                            'msgCtx',
        ccnx.CCNX_TLV_M_Name:               "Name",
        ccnx.CCNX_TLV_M_Payload:            "Payload",
        ccnx.CCNX_TLV_M_ObjHashRestriction: "ObjHashRestriction",
        ccnx.CCNX_TLV_M_ENDChunk:           "EndChunk",
        ccnx.CCNX_TLV_C_PayloadType:        "PayloadType",
        ccnx.CCNX_TLV_C_ExpiryTime:         "ExpiryTime"
    },
    CTX_NAME: {
        -1:                             "nameCtx",
        ccnx.CCNX_TLV_N_NameSegment:         "NameSegment",
        ccnx.CCNX_TLV_N_IPID:                "InterestPID",
        # case CCNX_TLV_N_NameKey:        tn = "NameKey"; break;
        # case CCNX_TLV_N_ObjHash:        tn = "ObjHash"; break;
        ccnx.CCNX_TLV_N_Chunk:               "Chunk",
        ccnx.CCNX_TLV_N_Meta:                "MetaData"
    },
    CTX_MFST: {
        -1:                             "manifestCtx",
        ccnx.T_MANIFEST_HASHGROUP:             "HashGroup"
    },
    CTX_MFST_HASHGRP: {
        -1:                             "manifestHashGroupCtx",
        ccnx.T_MANIFEST_HG_METADATA:         "MetaData",
        ccnx.T_MANIFEST_HG_PTR2DATA:         "DataPtr",
        ccnx.T_MANIFEST_HG_PTR2MANIFEST:     "ManifestPtr"
    },
    CTX_MFST_HASHGRP_METADATA: {
        -1:                             "manifestMetaDataCtx",
        ccnx.T_MANIFEST_MT_LOCATOR:          "Locator",
        ccnx.T_MANIFEST_MT_EXTERNALMETADATA: "ExternalMetaData",
        ccnx.T_MANIFEST_MT_BLOCKSIZE:        "BlockSize",
        ccnx.T_MANIFEST_MT_OVERALLDATASIZE:  "OverallSize",
        ccnx.T_MANIFEST_MT_OVERALLDATASHA256:  "OverallSHA256",
        ccnx.T_MANIFEST_MT_TREEDEPTH:        "TreeDepth"
    },
    CTX_METADATA: {
        -1:                             "metaDataCtx",
        #CCNX_TLV_M_KeyID:         "KeyId",
        #CCNX_TLV_M_ObjHash:         "ObjHash",
        #CCNX_TLV_M_PayldType:         "PayloadType",
        #CCNX_TLV_M_Create:         "Create"
    },
    CTX_VALIDALGO: {
        -1:                             "validAlgoCtx",
        ccnx.CCNX_VALIDALGO_CRC32C:         "CRC32C",
        ccnx.CCNX_VALIDALGO_HMAC_SHA256:         "HMAC_SHA256",
        ccnx.CCNX_VALIDALGO_VMAC_128:         "VMAC_128",
        ccnx.CCNX_VALIDALGO_RSA_SHA256:         "RSA_SHA256",
        ccnx.CCNX_VALIDALGO_EC_SECP_256K1:         "EC_SECP_256K1",
        ccnx.CCNX_VALIDALGO_EC_SECP_384R1:         "EC_SECP_384R1"
    },
    CTX_VALIDALGODEPEND: {
        -1:                             "validAlgoDependendCtx",
        ccnx.CCNX_VALIDALGO_KEYID:          "KeyID"
    }
}

def ccnx2015_getTypeNames(ctx, typ):
    if not ctx in ccnx2015tlv_typenames:
        return ("CTX%x" % ctx, "TYP%x" % typ)
    ctx = ccnx2015tlv_typenames[ctx]
    if typ in ctx:
        typ = ctx[typ]
    else:
        typ = "type%x" % typ
    return (typ, ctx[-1])

recurse_dict = {
    CTX_TOPLEVEL : {
        ccnx.CCNX_TLV_TL_Interest:       CTX_MSG,
        ccnx.CCNX_TLV_TL_Object:         CTX_MSG,
        ccnx.CCNX_TLV_TL_Manifest:       CTX_MFST,
        ccnx.CCNX_TLV_TL_ValidationAlgo: CTX_VALIDALGO },
    CTX_MSG : {
        ccnx.CCNX_TLV_M_Name:            CTX_NAME },
    CTX_MFST : {
        ccnx.CCNX_TLV_M_Name:            CTX_NAME,
        ccnx.T_MANIFEST_HASHGROUP:       CTX_MFST_HASHGRP },
    CTX_MFST_HASHGRP : {
        ccnx.T_MANIFEST_HG_METADATA:     CTX_MFST_HASHGRP_METADATA },
    CTX_MFST_HASHGRP_METADATA : {
        ccnx.T_MANIFEST_MT_LOCATOR:      CTX_NAME,
        ccnx.T_MANIFEST_MT_EXTERNALMETADATA: CTX_NAME },
    CTX_NAME : {
        ccnx.CCNX_TLV_N_Meta:            CTX_METADATA },
    CTX_VALIDALGO : {
        ccnx.CCNX_VALIDALGO_HMAC_SHA256: CTX_VALIDALGODEPEND }
}

ccnxtlv_isPrint = { 0x08, 0x15 }

def must_recurse(ctx, typ):
    if not ctx in recurse_dict:
        return None
    ctx = recurse_dict[ctx]
    if typ in ctx:
        return ctx[typ]
    return None

def hexDump(data, lev, doPrint):
    cnt = 0
    line = ''
    offs = 0
    while offs < len(data):
        if cnt == 0:
            s = ''
            for i in range(0, lev):
                s = s + '  '
        c = data[offs]
        s = s + '%02x ' % (ord(c[0]) if type(data) == str else c)
        if c >= ord(' ') and c <= ord('~'):
            line += chr(c)
        else:
            line += '.'
        cnt += 1
        if cnt == 8:
            s = s + ' '
        elif offs == len(data) or cnt == 16:
            if doPrint:
                print("%-61s |%s|" % (s, line))
            else:
                print(s)
            cnt = 0
            line = ''
        offs += 1

    if cnt != 0:
        if doPrint:
            print("%-61s |%s|" % (s, line))
        else:
            print(s)

def dump_header(data):
    pktlen = struct.unpack('>H', data[2:4])[0]
    fill = struct.unpack('>H', data[5:7])[0]
    print('hdr.vers=%d'       % data[0])
    print('hdr.pkttyp=%d'     % data[1])
    print('hdr.pktlen=%d'     % pktlen)
    print('hdr.hoplim=%d'     % data[4])
    print('hdr.errcod=0x%04x' % fill)
    print('hdr.hdrlen=%d'     % data[7])
    return (data[8:data[7]], data[data[7]:])

def dump_tlv(data, ctx, lev):
    while len(data) > 0:
        s = ''
        for i in range(0, lev):
            s = s + '  '
        t, l, tail = ccnx.readTL(data)
        tn = ccnx2015_getTypeNames(ctx, t)
        print( s + "<%s\%s, len=%d>" % (tn[0], tn[1], l) )
        ctx2 = must_recurse(ctx, t)
        if ctx2 != None:
            dump_tlv(tail[:l], ctx2, lev+1)
        elif l > 0:
            hexDump(tail[:l], lev+1, True) # t in ndntlv_isPrint)
        data = tail[l:]

def dump_wirebytes(data):
    (options, body) = dump_header(data)
    if len(options) > 0:
        print('hdr.option=%d bytes' % len(options))
    print("hdr.end")

    h = sha256()
    h.update(body)
    dump_tlv(body, CTX_TOPLEVEL, 1)
    print("pkt.digest= 0x" + str(pycn_lite.lib.hexlify(h.digest()),'ascii'))

# ---------------------------------------------------------------------------

if __name__ == '__main__':

    chunk = read_from_stdin()
    dump_wirebytes(chunk)

# eof
