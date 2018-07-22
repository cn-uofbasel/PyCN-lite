# pycn_lite/lib/__init__.py

def hexlify(b):
    d = b'0123456789abcdef'
    h = bytearray(2*len(b))
    for i in range(len(b)):
        h[2*i]   = d[ b[i] >> 4 ]
        h[2*i+1] = d[ b[i] & 0x0f ]
    return h

def dehexlify(s):
    return bytes([int(s[2*i:2*i+2],16) for i in range(len(s)>>1)])

def escapedUTF8toComponent(s):
    # if str starts with '0x', dehexlify it, otherwise
    # encode the given UTF string, then replace all
    # '%xx' patters by the corresponding byte val
    if len(s) >= 4 and s[:2] == '0x':
        return bytes.fromhex(s[2:])

    c2 = b''
    c = s.encode('utf8')
    while len(c) > 0:
        try:
            i = c.index(ord('%'))
            c2 += c[:i] + bytes([int(c[i+1:i+3],16)])
            c = c[i+3:]
        except:
            c2 += c
            break
    return c2

def componentToEscapedUTF8(c):
    # return hexlified if shorter or not decodable as UTF8, else
    # escape '/' and '%' with the '%xx' pattern,
    # then make this a UTF8 string
    h = (b'0x' + hexlify(c)).decode('utf8') # c.hex()
    c2 = b''
    while len(c) > 0:
        try:
            i = c.index(ord('%'))
            c2 += c[:i] + b'%25'
            c = c[i+1:]
            continue
        except:
            c2 += c
            break
    c2, c = (b'', c2)
    while len(c) > 0:
        try:
            i = c.index(ord('/'))
            c2 += c[:i] + b'%2f'
            c = c[i+1:]
            continue
        except:
            c2 += c
            break
    try:
        c = c2.decode('utf8')
    except:
        return h
    return h if len(h) < len(c) else c

def pkt_dump(buf):
    while len(buf) > 0:
        line = hexlify(buf[:16]).decode('ascii')
        print(' '.join([line[4*i:4*i+4] for i in range(8)]))
        buf = buf[16:]

# eof
