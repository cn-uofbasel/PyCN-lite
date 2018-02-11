# pycn_lite/lib/event_std.py

# (c) 2018-02-05 <christian.tschudin@unibas.ch>

# the event loop for standard Python3

import select
import socket
import time as std_time

def time_cmp(a, b):
    return a - b

def time(offs = 0):
    if offs == 0:
        return std_time.time()
    return std_time.time() + offs/1000.0

# ---------------------------------------------------------------------------

class Loop():

    def __init__(self):
        self.time_dict = {}
        self.sock_list = []
        self.p = select.poll()

    def register_timer(self, cb, delta, arg):
        self.time_dict[cb] = [std_time.time(), delta/1000, arg]

    def udp_open(self, addr, recv_ready_cb, send_done_cb, arg):
        # recv_ready_cb MUST be set
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(socket.getaddrinfo(addr[0], addr[1])[0][-1])
        if send_done_cb:
            s.setblocking(False)
        self.sock_list.append([s, recv_ready_cb, send_done_cb, arg])
        self.p.register(s.fileno(), select.POLLIN)
        return s

    def udp_sendto(self, s, buf, addr):
        s.sendto(buf, addr)
        for cb in self.sock_list:
            if cb[0] == s and cb[2]:
                self.p.register(s, select.POLLIN | select.POLLOUT)

    def udp_close(self, s):
        rm = None
        for i in range(len(self.sock_list)):
            if self.sock_list[i][0] == s:
                s.close()
                rm = i
                break
        if rm != None:
            del self.sock_list[i]

    def forever(self):
        while True:
            now = std_time.time()
            tout = None
            for cb in self.time_dict:
                d = time_cmp(self.time_dict[cb][0], now)
                if d < 0:
                    cb(self, self.time_dict[cb][2])
                    d = self.time_dict[cb][1]
                    self.time_dict[cb][0] = now + d
                if tout == None or d < tout:
                    tout = d
            try:
                ok = self.p.poll(tout)
            except:
                # KeyboardInterrupt: release socket bindings
                for e in self.sock_list:
                    e[0].close()
                    return
            for s,mask in ok:
                for cb in self.sock_list:
                    if cb[0].fileno() != s:
                        continue
                    if mask & select.POLLIN:
                        # print("calling recv")
                        cb[1](self, cb[0], cb[3])
                    if mask & select.POLLOUT:
                        # print('removing POLLOUT')
                        self.p.register(s, select.POLLIN)
                        if cb[2]:
                            cb[2](self, cb[0], cb[3])

# eof
