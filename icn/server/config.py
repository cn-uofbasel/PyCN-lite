# pycn-lite/icn/server/config.py

# (c) 2018-02-06 <christian.tschudin@unibas.ch>

# (self-) config of server parameters

import icn.lib.packet      as packet
import icn.lib.suite.multi as multi

import sys
if sys.platform == 'esp8266':
    default_lan_if = ('192.168.4.1', 6363)
    default_wan_if = ('127.0.0.1', 6363)
    default_repo_path = '/lib/icn/bin/demo_repo_dir'
    multi.config(['ndn2013','ccnx2015'], decode_only=True)
else:
    default_lan_if = ('127.0.0.1', 6363)
    default_wan_if = ('127.0.0.1', 6363)
    default_repo_path = 'demo_repo_dir'
    multi.config(['ndn2013', 'ccnx2015'])

default_wan_route = (packet.Name('/ndn', suite_name='ndn2013'),
                     ('127.0.0.1', 9999))
                     # ('128.252.153.194', 6363))
                     # WU, see http://ndndemo.arl.wustl.edu/

# eof
