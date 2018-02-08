# pycn_lite/icn/server/fwd.py

# (c) 2018-02-01 <christian.tschudi@unibas.ch>

# ICN forwarder for NDN and CCNx packets
# limitation: one forwarder instance only (because of timer callback)

import sys
try:
    import usocket as socket
    import icn.server.event_micro as event
    def q(): # for convenience
        import machine
        machine.reset()
except:
    import socket
    import icn.server.event_std   as event

from icn.lib.packet import ContentPacket, InterestPacket, NackPacket
import icn.lib.suite.multi
import icn.server.config

MAX_CHUNK_SIZE = 1500-50  # max UDP payload for a single Ethernet frame

# ----------------------------------------------------------------------

PIT_TIMEOUT   =  1500 # in msec
PIT_GC_TIME   =   300 # in msec

CS_TIMEOUT    = 10000 # in msec
CS_GC_TIME    =  1000 # in msec
CS_MAX_CAP    =  3000 # in Bytes

FWD_STATUS    =  5000 # in msec

# ----------------------------------------------------------------------

class PIT:

    def __init__(self, loop, fwd):
        # self._loop = loop
        self._fwd = fwd
        self._pend = {}
        loop.register_timer(pit_gc, PIT_GC_TIME, self)

    def rx_interest(self, pkt, face, addr):
        # returns the packet if it is the first for this name
        # print("PIT.rx_interest ", pkt._name)
        for n,e in self._pend.items():
            if n != pkt._name:
                continue
            if face in e[0]:
                a = e[0][face]
                if not addr in a:
                    a.append(addr)
            else:
                e[0][face] = [addr]
            e[2] = 3 # reset retry count
            return None
        self._pend[pkt._name] = [{face:[addr]}, event.time(PIT_TIMEOUT), 3, pkt]
        return pkt

    def waiting_face_iter(self, pkt):
        # print("PIT.waiting_face_iter ", pkt._name)
        for n,e in self._pend.items():
            if n != pkt._name:
                continue
            for face in e[0]:
                for addr in e[0][face]:
                    yield (face, addr)
            del self._pend[pkt._name]
            break
        raise StopIteration

    def is_pend(self, name):
        return name in self._pend

def pit_gc(loop, pit):
    exp = event.time()
    rmset = []
    for n,e in pit._pend.items():
        if event.time_cmp(e[1], exp) < 0:
            if e[2] <= 0:
                rmset.append(n)
            else:
                # print("pit_gc %s %s" % (str(n),str(e)))
                x = e[2] - 1
                e[2] = x
                e[1] = event.time(PIT_TIMEOUT)
                pkt = e[3]
                face = pit._fwd.fib_lpm(pkt._name)
                if face:
                    face.enqueue(pkt)
    for n in rmset:
        # print("pit.removing ", n)
        del pit._pend[n]

# ----------------------------------------------------------------------

class Face:

    def __init__(self, loop, fwd, addr, dest=None):
        self._loop = loop
        self._fwd = fwd
        self._sock = loop.udp_open(addr, face_recv_cb, None, self)
        if dest:
            self._dest = socket.getaddrinfo(dest[0], dest[1])[0][-1]
        else:
            self._dest = None

    def rx(self, data, addr):
        # print("face: datagram received")
        pkt = icn.lib.suite.multi.decode_wirebytes(data)
        if pkt:
            self._fwd.rx_packet(pkt, self, addr)
        else:
            self._fwd._pkt_nvld += 1

    def enqueue(self, pkt, dest=None):
        # print("face: enqueue ", pkt._name)
        if not dest:
            dest = self._dest
        wb, _ = pkt.to_wirebytes()
        self._loop.udp_sendto(self._sock, wb, dest)
        self._fwd._pkt_out += 1

def face_recv_cb(loop, s, face):
    # print("face: recv_cb")
    buf, addr = s.recvfrom(MAX_CHUNK_SIZE)
    face.rx(buf, addr)

# ----------------------------------------------------------------------

class Forwarder:

    def __init__(self, loop):
        self._pit = PIT(loop, self)
        self._fib = {}
        self._cs = {}
        self._cs_sz = 0
        self._pkt_in, self._pkt_out, self._pkt_nvld = (0, 0, 0)
        loop.register_timer(cs_gc_cb, CS_GC_TIME, self)
        loop.register_timer(fwd_status_cb, FWD_STATUS, self)

    def fib_add_rule(self, name, face):
        self._fib[name] = face

    def fib_lpm(self, name): # returns the face
        dest = None
        for pfx,face in self._fib.items():
            if pfx.is_prefix_of(name):
                if not dest or len(pfx._comps) > len(dest.comps):
                    dest = face
        return dest

    def rx_packet(self, pkt, face, addr): # returns data obj if in the CS
        self._pkt_in += 1
        if isinstance(pkt, InterestPacket):
            # print("CS.lookup", pkt._name)
            if pkt._name in self._cs:
                # print("CS.found", pkt._name)
                pkt = self._cs[pkt._name][0]
                face.enqueue(pkt, addr)
                return
            pkt = self._pit.rx_interest(pkt, face, addr)
            if pkt: # this is a new packet, forward it for the first time
                face = self.fib_lpm(pkt._name)
                if face:
                    face.enqueue(pkt)
            return
        if isinstance(pkt, ContentPacket) and self._pit.is_pend(pkt._name):
            if self._cs_sz + len(pkt._wire) < CS_MAX_CAP:
                # print("CS.adding:", pkt._name)
                self._cs[pkt._name] = (pkt, event.time(CS_TIMEOUT))
                self._cs_sz += len(pkt._wire)
        if isinstance(pkt, (ContentPacket, NackPacket)):
            for face,addr in self._pit.waiting_face_iter(pkt):
                face.enqueue(pkt, addr)

def cs_gc_cb(loop, fwd):
    exp = event.time()
    rmset = []
    for n,e in fwd._cs.items():
        if event.time_cmp(e[1], exp) < 0:
            rmset.append(n)
    for n in rmset:
        # print("cs.removing:", n)
        fwd._cs_sz -= len(fwd._cs[n][0]._wire)
        del fwd._cs[n]

def fwd_status_cb(loop, fwd):
    if sys.implementation.name == 'micropython':
        print("packets in/out/invalid:",
              fwd._pkt_in, fwd._pkt_out, fwd._pkt_nvld)

# ---------------------------------------------------------------------------

def start(lan_addr = icn.server.config.default_lan_if,
          wan_addr = icn.server.config.default_wan_if,
          routes   = icn.server.config.default_wan_routes):

    loop = event.Loop()

    fwd = Forwarder(loop)
    lan_face = Face(loop, fwd, lan_addr)

    # collect all IP targets for which we create faces, then register the rules
    wan_targets = []
    for r in routes:
        if not r[1] in wan_targets:
            wan_targets.append(r[1])
    for w in wan_targets:
        wan_face = Face(loop, fwd, wan_addr, w)
        for r in routes:
            if r[1] == w:
                fwd.fib_add_rule(r[0], wan_face)

    print("PyCN-lite forwarder at", lan_addr, "serving",
          [ s.Suite_name for s in icn.lib.suite.multi.Suites ])
    for pfx, face in fwd._fib.items():
        print(" ", pfx, "-->", face._dest)
    print()

    loop.forever()

# eof
