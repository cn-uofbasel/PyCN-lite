#!/usr/bin/env python3

# pycn_lite/lib/suite/ndn2013_dump.py

# (c) 2015-06-13 and 2018-01-27 <christian.tschudin@unibas.ch>

# import sys
# if sys.implementation.name == 'micropython':
#     import ustruct as struct

import sys

try:
    from uhashlib import sha256
    sys.path.append(sys.path[0] + '/../..')
    def read_from_stdin():
        return bytearray(sys.stdin.read())
except:
    from hashlib import sha256
    def read_from_stdin():
        return sys.stdin.buffer.read()

import pycn_lite.lib
import pycn_lite.lib.suite.ndn2013 as ndn

# ---------------------------------------------------------------------------

ndntlv_types = {
    ndn.T_HashID :           'HashID',
    ndn.T_Interest :         'Interest',
    ndn.T_Data :             'Data',
    ndn.T_Name :             'Name',
    ndn.T_NameComponent :    'NameComponent',
    ndn.T_Selectors :        'Selectors',
    ndn.T_Nonce :            'Nonce',
    ndn.T_Scope :            'Scope',
    ndn.T_InterestLifeTime : 'InterestLifeTime',
    ndn.T_MinSuffixComp :    'MinSuffixComp',
    ndn.T_MaxSuffixComp :    'MaxSuffixComp',
    ndn.T_PublisherPubKeyLoc : 'PublisherPubKeyLoc',
    ndn.T_Exclude :          'Exclude',
    ndn.T_ChildSelector :    'ChildSelector',
    ndn.T_MustBeFresh :      'MustBeFresh',
    ndn.T_Any :              'Any',
    ndn.T_MetaInfo :         'MetaInfo',
    ndn.T_Content :          'Content',
    ndn.T_SignatureInfo :    'SignatureInfo',
    ndn.T_SignatureValue :   'SignatureValue',
    ndn.T_ContentType :      'ContentType',
    ndn.T_FreshnessPeriod :  'FreshnessPeriod',
    ndn.T_FinalBlockId :     'FinalBlockId',
    ndn.T_SignatureType :    'SignatureType',
    ndn.T_KeyLocator :       'KeyLocator',
    ndn.T_KeyLocatorDiges :  'KeyLocatorDigest',
    ndn.T_MANIFEST_HASHGROUP:            'Manifest_Hashgroup',
    ndn.T_MANIFEST_HG_PTR2DATA:          'Manifest_DataPointer',
    ndn.T_MANIFEST_HG_PTR2MANIFEST:      'Manifest_ManifestPointer',
    ndn.T_MANIFEST_MT_LOCATOR:           'Manifest_Locator',
    ndn.T_MANIFEST_MT_OVERALLDATASHA256: 'Manifest_OverallDataSha256',
    ndn.T_MANIFEST_MT_OVERALLDATASIZE:   'Manifest_OverallDatasize',
    ndn.T_MANIFEST_MT_BLOCKSIZE:         'Manifest_Blocksize',
    ndn.T_MANIFEST_MT_TREEDEPTH:         'Manifest_TreeDepth',
    ndn.T_MANIFEST_MT_EXTERNALMETADATA:  'Manifest_ExternalMetadata',
}

ndntlv_recurseSet = { 0x05, 0x06, 0x07, 0x09, 0x14, 0x16, 0x1c }
ndntlv_isPrint = { 0x08, 0x15 }

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

isManifest = False

def dump_tlv(data, lev):
    global isManifest
    while len(data) > 0:
        s = ''
        for i in range(0, lev):
            s = s + '  '
        t, l, tail = ndn.readTL(data)
        if t in ndntlv_types:
            s = s + ndntlv_types[t]
        else:
            s = s + "type%x" % t
        if t == ndn.T_ContentType and tail[:l] == b'\xfd\x04\x00':
            isManifest = True
        print(s + " (%d bytes)" % l)
        if t in ndntlv_recurseSet or (isManifest and t == ndn.T_Content):
            dump_tlv(tail[:l], lev+1)
        elif l > 0:
            hexDump(tail[:l], lev+1, t in ndntlv_isPrint)
        data = tail[l:]

def dump_wirebytes(data):
    dump_tlv(data, 0)
    h = sha256()
    h.update(data)
    print("pkt.digest= 0x" + str(pycn_lite.lib.hexlify(h.digest()), 'ascii'))

# ---------------------------------------------------------------------------

if __name__ == '__main__':

    chunk = read_from_stdin()
    dump_wirebytes(chunk)

# eof
