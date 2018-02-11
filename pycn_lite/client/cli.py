#!/usr/bin/env python3

# pycn_lite/client/cli.py

# (c) 2018-01-27 <christian.tschudin@unibas.ch>

import argparse
import binascii
import os
import sys

if sys.implementation.name == 'micropython':
    sys.path.append("/Users/tschudin/proj/PyCN-lite")

import pycn_lite.lib.network
import pycn_lite.lib.packet
import pycn_lite.lib.flic_dec
import pycn_lite.lib.flic_enc
import pycn_lite.lib.suite.multi
import pycn_lite.server.repo_fs as repo_impl

# ---------------------------------------------------------------------------

def do_fetch():

    parser = argparse.ArgumentParser(description='ICN Fetch Content')
    parser.add_argument('--hashRestriction', type=str)
    parser.add_argument('--raw', action='store_true')
    parser.add_argument('--suite', default='ndn2013', type=str)
    parser.add_argument('addr', help="ip4:port", type=str)
    parser.add_argument('name', type=str)
    args = parser.parse_args()

    nw = pycn_lite.lib.network.access_point()
    addr = args.addr.split(':')
    gw = (addr[0], int(addr[1]))
    nw.attach(gw)

    if args.hashRestriction:
        args.hashRestriction = binascii.unhexlify(args.hashRestriction)
    name = pycn_lite.lib.packet.Name(args.name, suite_name=args.suite)
    try:
        pkt = nw.fetch_pkt(name)
        if pkt._meta and 'contentType' in pkt._meta \
           and pkt._meta['contentType'] == 1024:
            pkt._name._comps.pop()
            c = pycn_lite.lib.flic_dec._manifestToBytes(nw, pkt._name, pkt.get_content())
        else:
            c = pkt.get_content()
        if args.raw:
            sys.stdout.buffer.write(c)
        else:
            print('received %d bytes: "%s"' % (len(c), c))
    except Exception as e:
        if e.__class__.__name__ == 'TimeoutError': # (class not define in uPy)
            print("# retransmission limit exceeded")
        else:
            raise

# ---------------------------------------------------------------------------

def iter_content_items(path):
    for fn in os.listdir(path):
        t = fn.split('.')
        if len(t) != 2 or len(t[0]) != 24:
            continue
        try:
            with open(path + os.sep + fn, 'rb') as f:
                buf = f.read()
            pkt = pycn_lite.lib.suite.multi.decode_wirebytes(buf)
        except:
            # traceback.print_exc()
            continue
        if pkt:
            yield (pkt._name, len(buf))
        else:
            print("unknown content in %s" % fn)
    raise StopIteration

def iter_prefixes(path):
    for fn in os.listdir(path):
        t = fn.split('.')
        if len(t) != 2 or t[0] != 'prefix':
            continue
        with open(path + os.sep + fn, 'rb') as f:
            buf = f.read()
        pkt = pycn_lite.lib.suite.multi.decode_wirebytes(buf)
        if isinstance(pkt, pycn_lite.lib.packet.InterestPacket):
            yield pkt._name
    raise StopIteration

def do_repo_ls():
    parser = argparse.ArgumentParser(description='List Repository Content')
    parser.add_argument('path', type=str)
    args = parser.parse_args()

    for i in iter_content_items(args.path):
        print("content (suite=%s, len=%d): %s" % (i[0]._suite.Suite_name,
                                                  i[1], str(i[0])))
    for n in iter_prefixes(args.path):
        print("prefix (suite=%s): %s" % (n._suite.Suite_name, str(n)))

# ---------------------------------------------------------------------------

def repo_store_chunk_bytes(repo, name, wire, hashId):
    fn = None
    for pfx in repo._prefixes:
        if pfx.is_prefix_of(name):
            fn = repo.name2pattern(name, hashId)
            break
    if not fn:
        raise IOError
    if len(wire) > 1500-50:
        sys.stdout.write("WARNING: chunk has %d bytes, exceeding the max Ethernet frame length of 1500 Bytes\n" % len(wire))
    fn = repo._path + os.sep + fn[0] + '.' + fn[1]
    if os.path.isfile(fn):
        # alert that file exists (or add "-nooverwrite" flag?)
        pass
    with open(fn, "wb") as f:
        f.write(wire)

def do_repo_put():

    parser = argparse.ArgumentParser(description='ICN Store Content to Repo')
    parser.add_argument('--flic', action='store_true')
    parser.add_argument('--prefix', type=str,
                        help="add a prefix to this repo")
    parser.add_argument('--suite', choices=['ndn2013', 'ccnx2015'],
                        default='ndn2013', type=str)
    parser.add_argument('path', type=str)
    parser.add_argument('name', type=str)
    args = parser.parse_args()

    if args.prefix:
        pfxs = [pycn_lite.lib.packet.Name(args.prefix, suite_name=args.suite)]
    else:
        pfxs = []
    args.name = pycn_lite.lib.packet.Name(args.name, suite_name=args.suite)
    data = sys.stdin.buffer.read()

    repo = repo_impl.RepoFS(args.path, prefixes=pfxs, suite=args.suite)
    if not args.flic:
        pkt = pycn_lite.lib.packet.ContentPacket(args.name, data)
        (wire, hashId) = pkt.to_wirebytes()
        repo_store_chunk_bytes(repo, args.name, wire, hashId)
    else:
        pycn_lite.lib.flic_enc.bytesToManifest(repo, args.name, data)

# ---------------------------------------------------------------------------

if __name__ == '__main__':

    # this is UNIX land, add all protocol specs:
    # pycn_lite.lib.suite.multi.config(['ndn2013', 'ccnx2015'])
    pycn_lite.lib.suite.multi.config(['ndn2013'])

    prog = sys.argv[0].split(os.sep)[-1]

    if prog == 'fetch.py':
        do_fetch()
    elif prog == 'repo_ls.py':
        do_repo_ls()
    elif prog == 'repo_put.py':
        do_repo_put()
    else:
        print("?")

# eof
