#!/usr/bin/env python3

# pycn_lite/icn/server/cli.py

# (c) 2018-01-27 <christian.tschudin@unibas.ch>

# command line interface for UNIX land

import argparse
import os
import sys

if sys.implementation.name == 'micropython':
    sys.path.append("/Users/tschudin/proj/PyCN-lite")

import icn.lib.network
import icn.lib.packet
import icn.server.config
import icn.server.fwd
import icn.server.repo

# ---------------------------------------------------------------------------

def do_fwd():

    parser = argparse.ArgumentParser(description='ICN Forwarder')
    parser.add_argument('addr', metavar="ip:port", type=str)
    args = parser.parse_args()

    addr = args.addr.split(':')
    icn.server.fwd.start(lan_addr=(addr[0], int(addr[1])))

# ---------------------------------------------------------------------------

def do_repo():

    parser = argparse.ArgumentParser(description='ICN Data Repository')
    parser.add_argument('--suite', choices=['ndn2013', 'ccnx2015'],
                        default='ndn2013', type=str)
    parser.add_argument('path', type=str)
    parser.add_argument('addr', metavar="ip:port", type=str)
    args = parser.parse_args()

    addr = args.addr.split(':')
    icn.server.repo.start(addr=(addr[0], int(addr[1])), path=args.path)

# ---------------------------------------------------------------------------

if __name__ == '__main__':

    prog = sys.argv[0].split(os.sep)[-1]

    if prog == 'forwarder.py':
        do_fwd()

    if prog == 'reposerver.py':
        do_repo()

# eof
