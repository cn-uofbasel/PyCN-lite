# pycn_lite/lib/suite/ndn2013.py

# (c) 2015-06-13 and 2018-01-27 <christian.tschudin@unibas.ch>

# parser for NDN packets, includes constants

Suite_name = 'ndn2013'
MAX_CHUNK_SIZE = 1500-48 # fits inside a UDP/IPv6/Ethernet frame, also IPv4
MANIFEST_OVERHEAD = 50 # some TLs, for manifest chunks

has_interest_payload = False

# ----------------------------------------------------------------------
# suite-specific constants

ContentType_blob     = 0
ContentType_link     = 1
ContentType_key      = 2
ContentType_nack     = 3
ContentType_FLIC     = 1024

T_HashID             = 0x01
T_Interest           = 0x05
T_Data               = 0x06
T_Name               = 0x07
T_NameComponent      = 0x08
T_Selectors          = 0x09
T_Nonce              = 0x0a
T_Scope              = 0x0b
T_InterestLifeTime   = 0x0c
T_MinSuffixComp      = 0x0d
T_MaxSuffixComp      = 0x0e
T_PublisherPubKeyLoc = 0x0f
T_Exclude            = 0x10
T_ChildSelector      = 0x11
T_MustBeFresh        = 0x12
T_Any                = 0x13
T_MetaInfo           = 0x14
T_Content            = 0x15
T_SignatureInfo      = 0x16
T_SignatureValue     = 0x17
T_ContentType        = 0x18
T_FreshnessPeriod    = 0x19
T_FinalBlockId       = 0x1a
T_SignatureType      = 0x1b
T_KeyLocator         = 0x1c
T_KeyLocatorDiges    = 0x1d

# FLIC manifest
T_MANIFEST_HASHGROUP             = 0xc0
T_MANIFEST_HG_PTR2DATA           = 0xc1
T_MANIFEST_HG_PTR2MANIFEST       = 0xc2
T_MANIFEST_HG_METADATA           = T_MetaInfo
T_MANIFEST_MT_LOCATOR            = 0xc3
T_MANIFEST_MT_OVERALLDATASHA256  = 0xc4
T_MANIFEST_MT_OVERALLDATASIZE    = 0xc5
T_MANIFEST_MT_BLOCKSIZE          = 0xc6
T_MANIFEST_MT_TREEDEPTH          = 0xc7
T_MANIFEST_MT_EXTERNALMETADATA   = 0xc8

# ----------------------------------------------------------------------
# reading TLVs

def readTorL(data):
    if not data or len(data) == 0:
        raise EOFError
    val = data[0]
    if val < 253:
        return (val, data[1:])
    n = [3,5,9][val-253]
    if len(data) < n:
        raise EOFError
    return (readUint(data[1:n]), data[n:])

def readTL(data):
    (t, tail1) = readTorL(data)
    (l, tail2) = readTorL(tail1)
    if l > len(tail2):
        raise EOFError
    return (t, l, tail2)

def readUint(data):
    return int.from_bytes(data, 'big')

# ---------------------------------------------------------------------------

def is_interest_wirebytes(data):
    return data[0] == T_Interest

def is_data_wirebytes(data):
    return data[0] == T_Data

def nameTLV_to_comps(data): # returns list of components
    name = []
    while len(data) > 0:
        t, l, tail = readTL(data)
        if t != T_NameComponent:
            raise EOFError
        name.append(tail[0:l])
        data = tail[l:]
    return name

def metadataTLV_to_dict(data):
    meta = {}
    while len(data) > 0:
        t, l, tail = readTL(data)
        if t == T_ContentType:
            meta['contentType']     = readUint(tail[:l])
        elif t == T_FreshnessPeriod:
            meta['freshnessPeriod'] = readUint(tail[:l])
        elif t == T_FinalBlockId:
            meta['finalBlockId']    = tail[:l]
        data = tail[l:]
    return meta

# ---------------------------------------------------------------------------

def decode_interest_wirebytes(data):  # returns (dict,tail)
    data = memoryview(data)
    t, l, tail = readTL(data)
    if t != T_Interest:
        raise EOFError
    data = tail[:l]
    tail = tail[l:]

    d = {}
    while len(data) > 0:
        t, l, tail2 = readTL(data)
        if t == T_Name:
            name = nameTLV_to_comps(tail2[:l])
            d['name'] = name
        elif t == T_HashID:
            d['hashId'] = tail2[0:l]
        else:
            d['type%x' % t] = tail2[0:l]
        data = tail2[l:]
    return (d, tail)

def decode_data_wirebytes(data):  # returns (dict,tail)
    data = memoryview(data)
    t, l, tail = readTL(data)
    if t != T_Data:
        raise EOFError
    data = tail[:l]
    tail = tail[l:]

    d = {}
    while len(data) > 0:
        t, l, tail2 = readTL(data)
        if t == T_Name:
            d['name'] = nameTLV_to_comps(tail2[:l])
        elif t == T_MetaInfo:
            d['meta'] = metadataTLV_to_dict(tail2[:l])
        elif t == T_Content:
            d['data'] = tail2[:l]
        else:
            d['type%x' % t] = tail2[0:l]
        data = tail2[l:]
    return (d, tail)

# eof
