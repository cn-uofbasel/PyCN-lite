# pycn_lite/icn/lib/flic_enc.py

# (c) 2018-02-09 <christian.tschudin@unibas.ch>

import copy

import icn.lib.packet
import icn.client.cli

# ----------------------------------------------------------------------

def bytesToManifest(repo, name, data):
    # input: byte array
    # output: (nameOfRootManifest, rootManifestChunk)
    # name already has an additional component (that will be dropped for
    # the non-root manifest or data nodes)

    data = memoryview(data)
    s = name._suite
    MTU = s.MAX_CHUNK_SIZE - s.MANIFEST_OVERHEAD
    subname = icn.lib.packet.Name(suite=name._suite)
    subname._comps = copy.deepcopy(name._comps)
    subname._comps.pop()
    buf = bytearray(MTU)
    MTU -= len(buf) - s.enc.prepend_name(buf, len(buf), subname._comps)

    # cut content in pieces
    raw = []
    while len(data) > 0:
        raw.append(data[:MTU])
        data = data[MTU:]

    # persist pieces and learn their hash pointers
    ptrs = []
    for r in raw:
        chunk, hashId = s.enc.encode_data_wirebytes(subname._comps, r)
        icn.client.cli.repo_store_chunk_bytes(repo, subname, chunk, hashId)
        ptrs.append(hashId)

    # create list of index tables, the M pointers will be added later
    # [DDDDDD(M->), DDDDD(M->), ..., DDDDD]
    # note: read the list of pointers backwards
    tables = []
    while len(ptrs) > 0:
        tbl = bytearray(MTU) # build index table, already in wire format
        start = len(tbl)
        # collect pointers as long as the table fits in a chunk
        while len(ptrs) > 0 and start > len(ptrs[-1]) + 4:
            ptr = ptrs.pop()
            # append an entry to the index table's bytes
            start = s.enc.prepend_blob(tbl, start, ptr,
                                       s.T_MANIFEST_HG_PTR2DATA)
        tables.append(tbl[start:])

    # persist the index tables as manifests
    # append the M pointer (to the previous tbl) first: DDDDD(M->)
    tailPtr = None
    buf = bytearray(s.MAX_CHUNK_SIZE)
    start = end = len(buf)
    if s.Suite_name == 'ndn2013':
        s.enc.prepend_empty_signature(buf, start)
        end = start
    while len(tables) > 0:
        n = name if len(tables) == 1 else subname
        tbl = tables[0]
        del tables[0]
        if tailPtr:
            start = s.enc.prepend_blob(buf, start, tailPtr,
                                       s.T_MANIFEST_HG_PTR2MANIFEST)
        start = s.enc.prepend_blob(buf, start, tbl)
        start = s.enc.prepend_tl(buf, start, s.T_MANIFEST_HASHGROUP,
                                 end - start)
        if s.Suite_name == 'ndn2013':
            start = s.enc.prepend_tl(buf, start, s.T_Content, end - start)
            start = s.enc.prepend_metainfo(buf, start, s.ContentType_FLIC)
            start = s.enc.prepend_name(buf, start, n._comps)
            start = s.enc.prepend_tl(buf, start, s.T_Data, end - start)
            chunk, hashId = s.enc.finalize(buf[start:])
        else:
            print("not implemented yet")
        tailPtr = hashId
        icn.client.cli.repo_store_chunk_bytes(repo, n, chunk, hashId)
        start = end
    return (name, buf)

# eof
