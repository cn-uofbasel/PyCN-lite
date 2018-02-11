#!/usr/bin/env python3

# pycn_lite/server/cli.py

# (c) 2018-01-27 <christian.tschudin@unibas.ch>

# command line interface for UNIX land

import argparse
import os
import sys

if sys.implementation.name == 'micropython':
    sys.path.append(sys.path[0] + '/../..')

import pycn_lite.server.fwd
import pycn_lite.server.fwdrepo
import pycn_lite.server.repo

# ---------------------------------------------------------------------------

def do_fwd():

    parser = argparse.ArgumentParser(description='ICN Forwarder')
    parser.add_argument('addr', metavar="ip:port", type=str)
    args = parser.parse_args()

    addr = args.addr.split(':')
    pycn_lite.server.fwd.start(lan_addr=(addr[0], int(addr[1])))

# ---------------------------------------------------------------------------

def do_repo():

    parser = argparse.ArgumentParser(description='ICN Data Repository')
    parser.add_argument('path', type=str)
    parser.add_argument('addr', metavar="ip:port", type=str)
    args = parser.parse_args()

    addr = args.addr.split(':')
    pycn_lite.server.repo.start(addr=(addr[0], int(addr[1])), path=args.path)

# ---------------------------------------------------------------------------

def do_fwd_repo():

    parser = argparse.ArgumentParser(description=
                                     'Combined ICN Forwarder and Repo')
    parser.add_argument('path', type=str)
    parser.add_argument('addr', metavar="ip:port", type=str)
    args = parser.parse_args()

    addr = args.addr.split(':')
    pycn_lite.server.fwdrepo.start(lan_addr=(addr[0], int(addr[1])),
                         repo_path = args.path)

# ---------------------------------------------------------------------------

if __name__ == '__main__':

    prog = sys.argv[0].split(os.sep)[-1]

    if prog == 'srv_fwd.py':
        do_fwd()

    if prog == 'srv_repo.py':
        do_repo()

    if prog == 'srv_fwdrepo.py':
        do_fwd_repo()

# eof
