# pycn-lite/icn/server/repo.py

# (c) 2018-02-03 <christian.tschudin@unibas.ch>

# ICN repo server loop

try:
    import micropython
    import icn.server.event_micro as event
except:
    import icn.server.event_std   as event

import icn.lib.suite.multi
import icn.server.config
import icn.server.repo_fs

# ---------------------------------------------------------------------------

def repo_recv_cb(loop, s, repo):
    buf, addr = s.recvfrom(1024)
    # print("repo: got %d bytes" % len(buf))
    pkt = icn.lib.suite.multi.decode_wirebytes(buf)
    if pkt == None:
        # print("repo: cannot decode")
        return
    wire = repo.get_chunk_bytes(pkt._name)
    if not wire:
        # print("repo: no chunk for " + pkt._name.to_string())
        # wire = pkt._name._suite.encode_nack_wirebytes(pkt._name._comps)
        # send this nack ...
        return
    # print("repo: sending chunk for " + pkt._name.to_string())
    loop.udp_sendto(s, wire, addr)

def start(addr = icn.server.config.default_addr,
          path = icn.server.config.default_path):
    theRepo = icn.server.repo_fs.RepoFS(path)
    loop = event.Loop()
    sock = loop.udp_open(addr, repo_recv_cb, None, theRepo)
    
    sn = [ s.Suite_name for s in icn.lib.suite.multi.Suites ]
    print("Starting the ICN repo server for " + str(sn))

    loop.forever()

# eof
