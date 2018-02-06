# pycn-lite/icn/server/config.py

# (c) 2018-02-06 <christian.tschudin@unibas.ch>

# (self-) config of server parameters

import icn.lib.suite.multi

import sys
if sys.platform == 'esp8266':
    default_addr = ('192.168.4.1', 6363)
    default_path = '/lib/icn/bin/demo_repo_dir'
    icn.lib.suite.multi.config(['ndn2013','ccnx2015'], decode_only=True)
else:
    default_addr = ('127.0.0.1', 6363)
    default_path = 'demo_repo_dir'
    icn.lib.suite.multi.config(['ndn2013', 'ccnx2015'])
    
# eof
