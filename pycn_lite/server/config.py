# pycn_lite/server/config.py

# (c) 2018-02-06 <christian.tschudin@unibas.ch>

# default server parameters for fwd and repo

import pycn_lite.lib.packet      as packet
import pycn_lite.lib.suite.multi as multi

import sys
if sys.platform == 'esp8266':
    default_lan_if = ('192.168.4.1', 6363)
    default_wan_if = ('192.168.4.1', 0)
    default_repo_path = '/lib/icn/bin/demo_repo_dir'
    multi.config(['ndn2013','ccnx2015'], decode_only=True)
    # multi.config(['ndn2013'], decode_only=True)
    default_wan_routes = [
        (packet.Name('/ndn',  suite_name='ndn2013'),  ('192.168.4.2', 9999)),
#        (packet.Name('/ccnx', suite_name='ccnx2015'), ('192.168.4.2', 9999))
    ]
                     # ('128.252.153.194', 6363))
                     # WU, see http://ndndemo.arl.wustl.edu/
else:
    default_lan_if = ('127.0.0.1', 6363)
    default_wan_if = ('192.168.1.252', 0)
    default_repo_path = 'demo_repo_dir'
    multi.config(['ndn2013', 'ccnx2015'])
    default_wan_routes = [
        (packet.Name('/ndn', suite_name='ndn2013'), ('192.43.193.111', 6363)),
        # (packet.Name('/ccnx', suite_name='ccnx2015'), ('127.0.0.1', 9999))
    ]
                     # ('128.252.153.194', 6363))
                     # WU, see http://ndndemo.arl.wustl.edu/

# eof
