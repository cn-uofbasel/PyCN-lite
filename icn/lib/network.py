# pycn_lite/icn/lib/network.py

# (c) 2018-01-27 <christian.tschudin@unibas.ch>

import binascii
import socket
import sys

if sys.implementation.name == 'micropython':
    import uselect as select
    class FileNotFoundError(Exception):
        pass
    class TimeoutError(Exception):
        pass
else:
    import select

import icn.lib.suite.multi

RECV_MAX_TRANSFER_UNIT = 4096
RECV_MAX_RETRY_COUNT   = 3
RECV_TIMEOUT_MSEC      = 1500   # in milliseconds

# -----------------------------------------------------------------

class access_point():

    def __init__(self):
        self._sock = None

    def attach(self, ip4_default_gw):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ip4_default_gw = ip4_default_gw

    def listen(self, ip4_local_addr):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(ip4_local_addr)

    def detach(self):
        self._sock = None

    def recv_pkt(self, timeout = None):
        p = select.poll()
        p.register(self._sock.fileno(), select.POLLIN)
        while True:
            ok = p.poll(timeout)
            if len(ok) > 0:
                wire, addr = self._sock.recvfrom(RECV_MAX_TRANSFER_UNIT)
                pkt = icn.lib.suite.multi.decode_wirebytes(wire)
                if pkt != None:
                    return (pkt, addr)
                # print(binascii.hexlify(wire))
                break
            if timeout:
                break
        return (None, None)

    def send_wirebytes(self, wire, addr = None):
        if not addr:
            addr= self.ip4_default_gw
        self._sock.sendto(wire, addr)
        
    def send_pkt(self, pkt, addr = None):
        self.send_wirebytes(pkt.to_wirebytes()[0], addr)

    def fetch_content_bytes(self, name, digest= None, raw=False):
        pkt = icn.lib.packet.InterestPacket(name, hashRestriction=digest)
        for i in range(RECV_MAX_RETRY_COUNT):
            if i != 0:
                print("# retransmitting Interest")
            rc = self.send_pkt(pkt)
            (reply, addr) = self.recv_pkt(RECV_TIMEOUT_MSEC)
            if type(reply) == icn.lib.packet.ContentPacket:
                if raw:
                    return reply._wire
                else:
                    return reply.get_content()
            if type(reply) == icn.lib.packet.NackPacket:
                raise FileNotFoundError
        raise TimeoutError

# eof
