# pycn_lite/server/repo.py

# (c) 2018-02-03 <christian.tschudin@unibas.ch>

# ICN repo server loop

try:
    import usocket # or any other micropyhton-specific module
    import pycn_lite.server.event_micro as event
    def q(): # for convenience
        import machine
        machine.reset()
except:
    import pycn_lite.server.event_std   as event

import pycn_lite.lib.suite.multi
import pycn_lite.server.config
import pycn_lite.server.repo_fs

# ---------------------------------------------------------------------------

def repo_recv_cb(loop, s, repo):
    buf, addr = s.recvfrom(1024)
    # print("repo: got %d bytes" % len(buf))
    pkt = pycn_lite.lib.suite.multi.decode_wirebytes(buf)
    if pkt == None:
        print("repo: cannot decode")
        return
    wire = repo.get_chunk_bytes(pkt._name)
    if not wire:
        print("repo: no chunk for " + pkt._name.to_string())
        # wire = pkt._name._suite.encode_nack_wirebytes(pkt._name._comps)
        # send this nack ...
        return
    # print("repo: send data for %s to %s" % (pkt._name.to_string(), str(addr)))
    loop.udp_sendto(s, wire, addr)

def start(addr = pycn_lite.server.config.default_lan_if,
          path = pycn_lite.server.config.default_repo_path):
    theRepo = pycn_lite.server.repo_fs.RepoFS(path)
    loop = event.Loop()
    sock = loop.udp_open(addr, repo_recv_cb, None, theRepo)
    
    sn = [ s.Suite_name for s in pycn_lite.lib.suite.multi.Suites ]
    print("PyCN-lite repo server at", addr, "serving", sn)

    loop.forever()

# eof
