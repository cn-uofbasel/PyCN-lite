# pycn_lite/lib/__init__.py

def hexlify(b):
    d = b'0123456789abcdef'
    h = bytearray(2*len(b))
    for i in range(len(b)):
        h[2*i]   = d[ b[i] >> 4 ]
        h[2*i+1] = d[ b[i] & 0x0f ]
    return h

# eof
