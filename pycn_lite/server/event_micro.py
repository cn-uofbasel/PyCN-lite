# pycn_lite/lib/event_micro.py

# (c) 2018-02-05 <christian.tschudin@unibas.ch>

# the event loop for Micropython

import uselect
import usocket
import utime

def time_cmp(a, b):
    return utime.ticks_diff(a, b)

def time(offs = 0):
    if offs == 0:
        return utime.ticks_ms()
    return utime.ticks_add(utime.ticks_ms(), offs)

# ---------------------------------------------------------------------------

class Loop():

    def __init__(self):
        self.time_dict = {}
        self.sock_list = []
        self.p = uselect.poll()

    def register_timer(self, cb, delta, arg):
        self.time_dict[cb] = [utime.ticks_ms(), delta, arg]

    def udp_open(self, addr, recv_ready_cb, send_done_cb, arg):
        # recv_ready_cb MUST be set
        s = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
        s.bind(usocket.getaddrinfo(addr[0], addr[1])[0][-1])
        if send_done_cb:
            s.setblocking(False)
        self.sock_list.append([s, recv_ready_cb, send_done_cb, arg])
        self.p.register(s, uselect.POLLIN)
        return s

    def udp_sendto(self, s, buf, addr):
        rc = s.sendto(buf, addr)
        self.p.register(s, uselect.POLLIN | uselect.POLLOUT)

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
            now = utime.ticks_ms()
            tout = None
            for cb in self.time_dict:
                d = utime.ticks_diff(self.time_dict[cb][0], now)
                if d < 0:
                    cb(self, self.time_dict[cb][2])
                    d = self.time_dict[cb][1]
                    self.time_dict[cb][0] = utime.ticks_add(now, d)
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
                    if cb[0] != s:
                        continue
                    if mask & uselect.POLLIN:
                        cb[1](self, s, cb[3])
                    if mask & uselect.POLLOUT:
                        # print('removing POLLOUT')
                        self.p.register(s, uselect.POLLIN)
                        if cb[2]:
                            cb[2](self, s, cb[3])

# eof
