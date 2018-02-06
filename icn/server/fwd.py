# pycn_lite/icn/server/fwd.py

# (c) 2018-02-01 <christian.tschudi@unibas.ch>

'''
An ICN forwarder
'''

# import asyncio

from icn.lib.packet import ContentPacket, InterestPacket, NackPacket
import icn.lib.suite.multi

# ----------------------------------------------------------------------

PIT_TIMEOUT   =  1.0 # in sec
PIT_GC_TIME   =  0.2 # in sec

CS_TIMEOUT    = 10.0 # inc sec
CS_GC_TIME    =  1.0 # in sec

class CS():

    def __init__(self):
        self._d = {}
        # self._lock = threading.Lock()
        self._loop = asyncio.get_event_loop()
        self._gc = self._loop.create_task(cs_gc(self._loop, self))

    def add(self, pkt):
        # self._lock.acquire()
        self._d[pkt._name] = (pkt, self._loop.time())
        # self._lock.release()

    def lookup(self, pkt):
        print("CS.lookup %s" % str(pkt._name))
        c = None
        # self._lock.acquire()
        if pkt._name in self._d:
            # print("cs.found %s" % pkt._name)
            c = self._d[pkt._name][0]
        # self._lock.release()
        return c

async def cs_gc(loop, cs):
    while True:
        await asyncio.sleep(CS_GC_TIME)
        # print("CS GC loop")
        exp = loop.time() - CS_TIMEOUT
        rmset = []
        # cs._lock.acquire()
        for n,e in cs._d.items():
            if e[1] < exp:
                rmset.append(n)
        for n in rmset:
            # print("cs.removing %s" % n)
            del cs._d[n]
        # cs._lock.release()


class PIT():

    def __init__(self, fwd):
        self._fwd = fwd
        self._pending = {}
        # self._lock = threading.Lock()
        self._loop = asyncio.get_event_loop()
        self._gc = self._loop.create_task(pit_gc(self._loop, self))

    def rx_interest(self, pkt, face, addr): # returns the packet if it is the first
        print("PIT.rx_interest %s" % str(pkt._name))
        # self._lock.acquire()
        for n,e in self._pending.items():
            if n != pkt._name:
                continue
            if face in e[0]:
                a = e[0][face]
                if not addr in a:
                    a.append(addr)
            else:
                e[0][face] = [addr]
            e[2] = 3 # reset retry count
            # self._lock.release()
            return None
        self._pending[pkt._name] = [{face:[addr]}, self._loop.time(), 3, pkt]
        # self._lock.release()
        return pkt

    def waiting_face_iter(self, pkt):
        print("PIT.waiting_face_iter %s" % str(pkt._name))
        # self._lock.acquire()
        for n,e in self._pending.items():
            if n != pkt._name:
                continue
            for face in e[0]:
                for addr in e[0][face]:
                    yield (face, addr)
            del self._pending[pkt._name]
            break
        # self._lock.release()
        raise StopIteration

    def is_pending(self, name):
        # print("PIT.is_pending %s" % str(name))
        return name in self._pending

async def pit_gc(loop, pit):
    while True:
        await asyncio.sleep(PIT_GC_TIME)
        exp = loop.time() - PIT_TIMEOUT
        # pit._lock.acquire()
        rmset = []
        for n,e in pit._pending.items():
            if e[1] < exp:
                if e[2] <= 0:
                    rmset.append(n)
                else:
                    e[1] = loop.time()
                    e[2] -= 1
                    pkt = e[3]
                    for face in pit._fwd._fib.matching_face_iter(pkt):
                        face.enqueue(pkt)
        for n in rmset:
            # print("pit.removing %s" % n)
            del pit._pending[n]
        # pit._lock.release()


class FIB():

    def __init__(self):
        self._rules = {}

    def add_rule(self, name, face):
        self._rules[name] = face

    def matching_face_iter(self, pkt): # iterates over all matching entries
        # print("FIB.matching_face_iter %s" % str(pkt._name))
        for pfx,face in self._rules.items():
            if pfx.is_prefix_of(pkt._name):
                yield face
        raise StopIteration


# class FACE(asyncio.DatagramProtocol):
class FACE():

    def __init__(self, fwd):
        self._fwd = fwd
        self._transport = None

    def connection_made(self, transport):
        # print("transport received")
        self._transport = transport

    def datagram_received(self, data, addr):
        # print("datagram received")
        pkt = icn.lib.suite.multi.decode_wirebytes(data)
        if pkt:
            self._fwd.rx_packet(pkt, self, addr)

    def enqueue(self, pkt, dest=None):
        # print("enqueue %s" % str(pkt._name))
        if not self._transport:
            return
        wb, _ = pkt.to_wirebytes()
        print("sending %d bytes to %s" % (len(wb), str(dest)))
        self._transport.sendto(wb, dest)
        
                
class Forwarder():

    def __init__(self):
        self._cs = CS()
        self._pit = PIT(self)
        self._fib = FIB()

    def rx_packet(self, pkt, face, addr): # returns data obj if in the CS
        if isinstance(pkt, InterestPacket):
            data = self._cs.lookup(pkt)
            if data:
                face.enqueue(data, addr)
            else:
                pkt = self._pit.rx_interest(pkt, face, addr)
                if pkt: # this is a new packet, forward it for the first time
                    for face in self._fib.matching_face_iter(pkt):
                        face.enqueue(pkt)
            return
        if isinstance(pkt, ContentPacket) and self._pit.is_pending(pkt._name):
            self._cs.add(pkt)
        if isinstance(pkt, (ContentPacket, NackPacket)):
            for face,addr in self._pit.waiting_face_iter(pkt):
                face.enqueue(pkt, addr)

# eof
