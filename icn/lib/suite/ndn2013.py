# pycn_lite/icn/lib/suite/ndn2013.py

# (c) 2015-06-13 and 2018-01-27 <christian.tschudin@unibas.ch>

# parser for NDN packets, includes constants

Suite_name = 'ndn2013'
MAX_CHUNK_SIZE = 1500-14 # fit in a Ethernet frame

enc = None    # will be set by icn.lib.suite.multi.config()

# ----------------------------------------------------------------------
# suite-specific constants

ContentType_blob     = 0
ContentType_link     = 1
ContentType_key      = 2
ContentType_nack     = 3

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

# ----------------------------------------------------------------------
# reading TLVs

def readTorL(data):
    if not data or len(data) == 0:
        raise EOFError
    # b = ord(data[0]) if type(data) == str else data[0]
    b = data[0]
    if b < 253:
        return (b, data[1:])
    maxlen = len(data) - 1
    if maxlen < 3:
        raise EOFError
    if b == 253:
        return (data[1]<<8 | data[2], data[3:])
    if maxlen < 5:
        raise EOFError
    if b == 254:
        return (data[1]<<24 | data[2]<<16 | data[3]<<8 | data[4], data[5:])
    if maxlen < 9:
        raise EOFError
    b = data[1]<<32 | data[2]<<24 | data[3]<<16 | data[4]<<8 | data[5]
    return (b<<24 | data[6]<<16 | data[7]<<8 | data[8], data[9:])

def readTL(data):
    (t, tail1) = readTorL(data)
    (l, tail2) = readTorL(tail1)
    if l > len(tail2):
        raise EOFError
    return (t, l, tail2)

def readInt(data):
    val = 0
    for c in data:
        # if type(data) == str:
        #     c = ord(c)
        val = (val<<8) | c
    return val

# ---------------------------------------------------------------------------

def is_interest_wirebytes(data):
    if not data or len(data) == 0:
        raise EOFError
    # b = ord(data[0]) if type(data) == str else data[0]
    b = data[0]
    return b == T_Interest

def is_data_wirebytes(data):
    if not data or len(data) == 0:
        raise EOFError
    # b = ord(data[0]) if type(data) == str else data[0]
    b = data[0]
    return b == T_Data

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
            meta['contentType']     = readInt(tail[:l])
        elif t == T_FreshnessPeriod:
            meta['freshnessPeriod'] = readInt(tail[:l])
        elif t == T_FinalBlockId:
            meta['finalBlockId']    = tail[:l]
        data = tail[l:]
    return meta

def wire_to_name_components(data): # returns an array with components
    t, l, tail = readTL(data)
    if t != T_Name:
        return None
    return nameTLV_to_comps(tail[:l])

def add_plain_name_components(comps, comp_list):
    for c in comp_list:
        # FIXME: handle escaped chars
        comps.append(c.encode('ascii'))

def get_plain_name_components(comps):
    return [ bytes(c).decode('utf8') for c in comps ]

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
