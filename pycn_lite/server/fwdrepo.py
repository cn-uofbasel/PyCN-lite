# pycn_lite/server/fwdrepo.py

# (c) 2018-02-08 <christian.tschudi@unibas.ch>

# Combined ICN forwarder and repo server for NDN and CCNx packets

try:
    import usocket as socket
    import pycn_lite.server.event_micro as event
    def q(): # for convenience
        import machine
        machine.reset()
except:
    import socket
    import pycn_lite.server.event_std   as event

import pycn_lite.server.fwd # import it first for memory reasons on the ESP8266
import pycn_lite.lib.suite.multi
import pycn_lite.server.config
import pycn_lite.server.repo_fs

# ----------------------------------------------------------------------

class RepoFace:

    def __init__(self, loop, fwd, repoPath):
        self._loop = loop
        self._fwd = fwd
        self._repo = pycn_lite.server.repo_fs.RepoFS(repoPath)
        self._dest = 'local_repo'

    def enqueue(self, pkt, dest=None):
        # print("repoFace: enqueue i.e., request", pkt._name)
        wire = self._repo.get_chunk_bytes(pkt._name)
        if wire:
            # print("repoFace: content found, injecting it", len(wire))
            pkt = pycn_lite.lib.suite.multi.decode_wirebytes(wire)
            if pkt:
                self._fwd.rx_packet(pkt, self, None)
        else:
            # print("repoFace: no chunk for", pkt)
            # should generate nack ...
            pass

# ---------------------------------------------------------------------------

def start(lan_addr = pycn_lite.server.config.default_lan_if,
          wan_addr = pycn_lite.server.config.default_wan_if,
          routes   = pycn_lite.server.config.default_wan_routes,
          repo_path = pycn_lite.server.config.default_repo_path):

    loop = event.Loop()

    fwd = pycn_lite.server.fwd.Forwarder(loop)
    lan_face = pycn_lite.server.fwd.Face(loop, fwd, lan_addr)

    repo_face = RepoFace(loop, fwd, repo_path)
    for pfx in repo_face._repo._prefixes:
        fwd.fib_add_rule(pfx, repo_face)

    # collect all IP targets for which we create faces, then register the rules
    wan_targets = []
    for r in routes:
        if not r[1] in wan_targets:
            wan_targets.append(r[1])
    for w in wan_targets:
        wan_face = pycn_lite.server.fwd.Face(loop, fwd, wan_addr, w)
        for r in routes:
            if r[1] == w:
                fwd.fib_add_rule(r[0], wan_face)

    print("PyCN-lite combined forwarder and repo at", lan_addr, "serving",
          [ s.Suite_name for s in pycn_lite.lib.suite.multi.Suites ])
    for pfx, face in fwd._fib.items():
        print(" ", pfx, "-->", face._dest)
    print()

    loop.forever()

# eof
