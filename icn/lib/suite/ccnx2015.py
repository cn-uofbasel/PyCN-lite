# pycn_lite/icn/lib/suite/ccnx2015.py

# (c) 2018-02-01 <christian.tschudin@unibas.ch>

try:
    import ustruct   as struct
except:
    import struct

Suite_name = 'ccnx2015'
MAX_CHUNK_SIZE = 1500-48 # fits inside a UDP/IPv6/Ethernet frame, also IPv4
MANIFEST_OVERHEAD = 32 # header plus some TLs, for manifest chunks

enc = None    # will be set by icn.lib.suite.multi.config()

# ----------------------------------------------------------------------
# suite-specific constants

# packet types (header byte at offset 1)
CCNX_PT_Interest                        = 0
CCNX_PT_Data                            = 1
CCNX_PT_NACK                            = 2 # "Interest Return"
CCNX_PT_Fragment                        = 3 # fragment

# top level(Sect 3.4)
CCNX_TLV_TL_Interest                    = 0x0001
CCNX_TLV_TL_Object                      = 0x0002
CCNX_TLV_TL_ValidationAlgo              = 0x0003
CCNX_TLV_TL_ValidationPayload           = 0x0004
CCNX_TLV_TL_Fragment                    = 0x0005
CCNX_TLV_TL_Manifest                    = 0x0006

# global (Sect 3.5.1)
CCNX_TLV_G_Pad                          = 0x007F # TODO: correcty type?

# per msg (Sect 3.6)
# 3.6.1
CCNX_TLV_M_Name                         = 0x0000
CCNX_TLV_M_Payload                      = 0x0001
CCNX_TLV_M_ENDChunk                     = 0x0019 # chunking document

# per name (Sect 3.6.1)
CCNX_TLV_N_NameSegment                  = 0x0001
CCNX_TLV_N_IPID                         = 0x0002
CCNX_TLV_N_Chunk                        = 0x0010 # chunking document
CCNX_TLV_N_Meta                         = 0x0011
# CCNX_TLV_N_App                          0x1000 - 0x1FFF

# meta
# ...

# (opt) message TLVs (Sect 3.6.2)
CCNX_TLV_M_KeyIDRestriction             = 0x0002
CCNX_TLV_M_ObjHashRestriction           = 0x0003
CCNX_TLV_M_IPIDM                        = 0x0004

# (opt) content msg TLVs (Sect 3.6.2.2)
CCNX_TLV_C_PayloadType                  = 0x0005
CCNX_TLV_C_ExpiryTime                   = 0x0006

# content payload type (Sect 3.6.2.2.1)
CCNX_PAYLDTYPE_Data                     = 0
CCNX_PAYLDTYPE_Key                      = 1
CCNX_PAYLDTYPE_Link                     = 2
CCNX_PAYLDTYPE_Manifest                 = 3

# FLIC manifest
T_MANIFEST_HASHGROUP                    = 1
T_MANIFEST_HG_METADATA                  = 1
T_MANIFEST_HG_PTR2DATA                  = 2
T_MANIFEST_HG_PTR2MANIFEST              = 3
T_MANIFEST_MT_LOCATOR                   = 0 # == CCNX_TLV_M_Name
T_MANIFEST_MT_EXTERNALMETADATA          = 1 # == CCNX_TLV_M_Name
T_MANIFEST_MT_BLOCKSIZE                 = 2
T_MANIFEST_MT_OVERALLDATASIZE           = 3
T_MANIFEST_MT_OVERALLDATASHA256         = 4
T_MANIFEST_MT_TREEDEPTH                 = 5

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

# ----------------------------------------------------------------------
# reading TLVs

def readTL(data):
    if len(data) < 4:
        raise EOFError
    t = int.from_bytes(data[0:2], 'big')
    l = int.from_bytes(data[2:4], 'big')
    tail = data[4:]
    if l > len(tail):
        raise EOFError
    return (t, l, tail)

# ---------------------------------------------------------------------------

def is_interest_wirebytes(data):
    if not data or len(data) < 8:
        raise EOFError
    return data[:2] == b'\x01\x00'

def is_data_wirebytes(data):
    if not data or len(data) < 8:
        raise EOFError
    return data[:2] == b'\x01\x01'

def nameTLV_to_comps(data): # returns list of components
    comps = []
    while len(data) > 0:
        if len(data) < 4:
            return EOFError
        l = int.from_bytes(data[2:4], 'big')
        if (l + 4) > len(data):
            raise EOFError
        comps.append(data[0:4+l])
        data = data[4+l:]
    return comps

def wire_to_name_components(data): # returns an array with components
    t, l, tail = readTL(data)
    if t != CCNX_TLV_M_Name:
        return None
    return nameTLV_to_comps(tail[:l])
    
def add_plain_name_components(comps, comp_list):
    for c in comp_list:
        comps.append(CCNX_TLV_N_NameSegment.to_bytes(2, 'big') + \
                     len(c).to_bytes(2, 'big') + \
                     c.encode('utf8'))

def get_plain_name_components(comps):
    return [ c[4:].decode('utf8') for c in comps ]

# ---------------------------------------------------------------------------

def decode_interest_wirebytes(data):  # returns (dict,tail)
    if len(data) < 8 or data[0] != 1 or data[1] != 0:
        raise EOFError
    data = data[data[7]:]
    t, l, tail = readTL(data)
    if t != CCNX_TLV_TL_Interest or l < len(tail):
        raise EOFError
    data = tail[:l]
    tail = tail[l:]
    d = {}
    while len(data) > 0:
        t, l, tail2 = readTL(data)
        if t == CCNX_TLV_M_Name:
            comps = nameTLV_to_comps(tail2[:l])
            d['name'] = comps
        elif t == CCNX_TLV_M_ObjHashRestriction:
            d['hashId'] = tail2[0:l]
        else:
            d['type%x' % t] = tail2[0:l]
        data = tail2[l:]
    return (d, tail)

def decode_data_wirebytes(data):  # returns (dict,tail)
    if len(data) < 8 or data[0] != 1 or data[1] != 1:
        raise EOFError
    data = data[data[7]:]
    t, l, tail = readTL(data)
    if t != CCNX_TLV_TL_Object or l < len(tail):
        raise EOFError
    data = tail[:l]
    tail = tail[l:]
    d = {}
    while len(data) > 0:
        t, l, tail2 = readTL(data)
        if t == CCNX_TLV_M_Name:
            comps = nameTLV_to_comps(tail2[:l])
            d['name'] = comps
        elif t == CCNX_TLV_M_Payload:
            d['data'] = tail2[0:l]
        else:
            d['type%x' % t] = tail2[0:l]
        data = tail2[l:]
    return (d, tail)

# eof
