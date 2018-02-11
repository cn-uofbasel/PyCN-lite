# pycn_lite/lib/suite/multi.py

# (c) 2015-06-13 and 2018-01-27 <christian.tschudin@unibas.ch>

# managing multiple ICN packet formats

import pycn_lite.lib.packet

# ---------------------------------------------------------------------------

Suites = []

def config(suite_names=['ndn2013'], decode_only=False):
    global Suites

    if 'ndn2013' in suite_names:
        import pycn_lite.lib.suite.ndn2013
        s = pycn_lite.lib.suite.ndn2013
        if not decode_only:
            import pycn_lite.lib.suite.ndn2013_enc
            s.enc = pycn_lite.lib.suite.ndn2013_enc
        Suites.append(s)
    if 'ccnx2015' in suite_names:
        import pycn_lite.lib.suite.ccnx2015
        s = pycn_lite.lib.suite.ccnx2015
        if not decode_only:
            import pycn_lite.lib.suite.ccnx2015_enc
            s.enc = pycn_lite.lib.suite.ccnx2015_enc
        Suites.append(s)
        
def suite_from_str(suite_name):
    for s in Suites:
        if s.Suite_name == suite_name:
            return s
    return None

def decode_wirebytes(buf):
    for s in Suites:
        try:
            if s.is_interest_wirebytes(buf):
                d, _ = s.decode_interest_wirebytes(buf)
                hashId = d['hashId'] if 'hashId' in d else None
                n = pycn_lite.lib.packet.Name(suite=s, hashId = hashId)
                n._comps = d['name']
                return pycn_lite.lib.packet.InterestPacket(n, buf)
        except MemoryError:
            print("out of mem")
        except:
            pass

        try:
            if s.is_data_wirebytes(buf):
                d, _ = s.decode_data_wirebytes(buf)
                metadict = d['meta'] if 'meta' in d else None
                n = pycn_lite.lib.packet.Name(suite=s)
                n._comps = d['name']
                # TODO: check whether meta says that this is a nack ...
                # ... 'contentType' in metadict and \
                #   metadict['contentType'] == ndn2013.ContentType_nack:
                #    return pycn_lite.lib.packet.NackPacket(n, d['data'])
                return pycn_lite.lib.packet.ContentPacket(n, payload=d['data'],
                                                 wirebytes=buf, meta=metadict)
        except MemoryError:
            print("out of mem")
        except:
            pass

    return None

# eof
