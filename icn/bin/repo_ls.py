#!/usr/bin/env python3

# pycn_lite/icn/client/cli.py

# (c) 2018-01-27 <christian.tschudin@unibas.ch>

import argparse
import binascii
import sys

if sys.implementation.name == 'micropython':
    sys.path.append("/Users/tschudin/proj/pycn-lite")
else:
    import traceback

import icn.lib.network
import icn.lib.packet
import icn.lib.suite.multi
import icn.server.repo_fs

# ---------------------------------------------------------------------------

def do_fetch():

    parser = argparse.ArgumentParser(description='ICN Fetch Content')
    parser.add_argument('--hashRestriction', type=str)
    parser.add_argument('--raw', action='store_true')
    parser.add_argument('--suite', default='ndn2013', type=str)
    parser.add_argument('addr', help="ip4:port", type=str)
    parser.add_argument('name', type=str)
    args = parser.parse_args()

    nw = icn.lib.network.access_point()
    addr = args.addr.split(':')
    gw = (addr[0], int(addr[1]))
    nw.attach(gw)

    if args.hashRestriction:
        args.hashRestriction = binascii.unhexlify(args.hashRestriction)
    name = icn.lib.packet.Name(args.name, suite_name=args.suite)
    c = nw.fetch_content_bytes(name, args.hashRestriction, args.raw)
    if args.raw:
        sys.stdout.buffer.write(c)
    else:
        print("received %d bytes: '%s'" % (len(c), c))

# ---------------------------------------------------------------------------

def iter_content_items(path):
    for fn in os.listdir(path):
        t = fn.split('.')
        if len(t) != 2 or len(t[0]) != 24:
            continue
        try:
            with open(path + os.sep + fn, 'rb') as f:
                buf = f.read()
            pkt = icn.lib.suite.multi.decode_wirebytes(buf)
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
        pkt = icn.lib.suite.multi.decode_wirebytes(buf)
        if isinstance(pkt, icn.lib.packet.InterestPacket):
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
    fn = repo._path + os.sep + fn[0] + '.' + fn[1]
    if os.path.isfile(fn):
        # alert that file exists (or add "-nooverwrite" flag?)
        pass
    with open(fn, "wb") as f:
        f.write(wire)


def do_repo_put():

    parser = argparse.ArgumentParser(description='ICN Store Content to Repo')
    parser.add_argument('--prefix', type=str,
                        help="add a prefix to this repo")
    parser.add_argument('--suite', choices=['ndn2013', 'ccnx2015'],
                        default='ndn2013', type=str)
    parser.add_argument('path', type=str)
    parser.add_argument('name', type=str)
    args = parser.parse_args()

    if args.prefix:
        pfxs = [icn.lib.packet.Name(args.prefix, suite_name=args.suite)]
    else:
        pfxs = []
    args.name = icn.lib.packet.Name(args.name, suite_name=args.suite)
    pkt = icn.lib.packet.ContentPacket(args.name, sys.stdin.buffer.read())

    repo = icn.server.repo_fs.RepoFS(args.path, prefixes=pfxs, suite=args.suite)
    (wire, hashId) = pkt.to_wirebytes()
    repo_store_chunk_bytes(repo, args.name, wire, hashId)

# ---------------------------------------------------------------------------

if __name__ == '__main__':

    # this is UNIX land, add all protocol specs:
    icn.lib.suite.multi.config(['ndn2013', 'ccnx2015'])

    import os
    prog = sys.argv[0].split(os.sep)[-1]

    if prog == 'fetch.py':
        do_fetch()
    elif prog == 'repo_ls.py':
        do_repo_ls()
    elif prog == 'repo_put.py':
        do_repo_put()

# eof
