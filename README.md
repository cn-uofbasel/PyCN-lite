# PyCN-lite

README.md v2018-02-12

![PyCN logo](doc/pycn-lite-logo-952x184.png)

PyCN-lite is a lightweight implementation of the two ICN protocols
NDN and CCNx. It is written for Micropython
[v1.9.3](http://docs.micropython.org/en/v1.9.3/pyboard/) and runs on
IoT devices like the ESP8266 with 28K RAM left for application
programs; UNIX environments with standard Python3 (or Micropython) are
supported, too.

Servers included in PyCN-lite (both UNIX and ESP8266):
* forwarder
* repo server
* combined forwarder and repo server

Command line tools included (UNIX only):
* fetch (FLIC-enabled), repo_ls, repo_put (FLIC-enabled), dump_ndn2013, dump_ccnx2015

Libraries included:
* NDN and CCNx parsing/formatting library, can be used in IoT end devices
* FLIC (File-Like ICN Collections), both generation and consumption

## Example config

You can use a ESP8266 device as a local ICN/WiFi access point
acting at the same time as a gateway to the NDN testbed:

![PyCN config](doc/PyCN-config.png "PyCN as an IoT gateway")


## ESP8266 setup and examples

### FORWARDER Howto (ESP8266)

* install Micropython on the ESP8266
* configure the WiFi access point for 192.168.4.1 and essid of your choice
* adjust the default settings in pycn_lite/server/config.py
* transfer the content of the 'pycn_lite' source code directory to '/lib/pycn_lite' on the ESP8266
* run the following commands on the console (or put them into the boot.py script):
```
>>> import pycn_lite.server.fwd as f
>>> f.start()
PyCN-lite forwarder at ('192.168.4.1', 6363) serving ['ndn2013', 'ccnx2015']
  /ndn --> ('128.252.153.194', 6363)

packets in/out/invalid: 0 0 0
packets in/out/invalid: 0 0 0
packets in/out/invalid: 2 2 0
packets in/out/invalid: 3 5 0
...
```
which will start the forwarder on port 6363. CTRL-C ends server execution.


### REPO-SERVER Howto (ESP8266)

* install Micropython on the ESP8266
* configure the WiFi access point for 192.168.4.1 and essid of your choice
* transfer the content of the 'pycn_lite' source code directory to '/lib/pycn_lite' on the ESP8266
* run the following commands on the console (or put them into the boot.py script):
```
>>> import pycn_lite.server.repo as r
>>> r.start()
PyCN-lite repo server at ('192.168.4.1', 6363) serving ['ndn2013', 'ccnx2015']
```
which will start the repo server on port 6363. CTRL-C ends server execution.


### Combined FORWARD and REPO-SERVER Howto (ESP8266)

* install Micropython on the ESP8266
* configure the WiFi access point for 192.168.4.1 and essid of your choice
* transfer the content of the 'pycn_lite' source code directory to '/lib/pycn_lite' on the ESP8266
* run the following commands on the console (or put them into the boot.py script):
```
>>> import pycn_lite.server.fwdrepo as fr
>>> fr.start()
PyCN-lite combined forwarder and repo at ('192.168.4.1', 6363) serving ['ndn2013', 'ccnx2015']
  /ndn/pycn-lite --> local_repo
  /ndn --> ('192.168.4.2', 9999)
  /ccnx/pycn-lite --> local_repo

packets in/out/invalid: 0 0 0
...
```

## UNIX setup and examples

If you do not wish to install the package and just want to try out
PyCN-lite (the examples below assume this kind of setup):
```
% git clone https://github.com/cn-uofbasel/PyCN-lite.git
% cd PyCN-lite
% export PYTHONPATH=`pwd`
% cd bin
```

If you wish to install the PyCN-lite package (in order to importing
the modules in your own Python script):
```
% git clone https://github.com/cn-uofbasel/PyCN-lite.git
% cd PyCN-lite
% python3 setup.py install
```
which also installs a _bin_ directory that you can add to your PATH,
see the log lines of the install process.


### FETCH Howto (UNIX commandline)
```
% cd PyCN-lite/bin

% ./fetch.py 192.168.4.1:6363 /ndn/pycn-lite/LICENSE
% ./fetch.py --suite ccnx2015 192.168.4.1:6363 /ccnx/pycn-lite/LICENSE
```

### REPO_LS Howto (UNIX commandline) - show content of a file system repo
```
% cd PyCN-lite/bin

% ls -1 ../../demo/repo_dir/
238703794c9a9d8f5757d92f.7d927eef66cd1f871279a6ac
350d8f87c7c04e7e56e212b4.6fb12aec48b6432bd3fd337a
prefix.3885558c37222613acca6faa
prefix.ac6dcf268096fcc84a8238dc

% ./repo_ls.py ../../demo/repo_dir
content (suite=ccnx2015, len=1639): /ccnx/pycn-lite/LICENSE
content (suite=ndn2013, len=1631): /ndn/pycn-lite/LICENSE
prefix (suite=ndn2013): /ndn/pycn-lite
prefix (suite=ccnx2015): /ccnx/pycn-lite
```

### REPO_PUT Howto (UNIX commandline) - add content to a file system repo
```
% cd PyCN-lite/bin

% ./repo_put.py --prefix /ndn/pycn-lite ../../demo/repo_dir /ndn/pycn-lite/LICENSE <../../LICENSE.trimmed 
% ./repo_put.py --prefix /ccnx/pycn-lite --suite ccnx2015 ../../demo/repo_dir /ccnx/pycn-lite/LICENSE <../../LICENSE.trimmed
```

The above commands were used to populate the demo repo directory. The
prefix parameter persists a file with that prefix if it is not already
existing: The --prefix parameter can be ommitted in subsequence put
operations (or additional ones be defined). Note that a trimmed
version of the license file was used such that the chunk fits in a
single UDP packet that itself fits in a single Ethernet frame.

In case of larger content, or if you use the --flic option, the
repo_put command uses the FLIC method to split the content into
multiple chunks linked through "hash-based names" and accessed through
a "root manifest". The fetch command automatically recognizes
FLIC-splitted content and reassembles the content in a fully
transparent way:

```
% ./repo_put.py --flic --prefix /ndn/pycn-lite ../../demo/flic_dir /ndn/pycn-lite/LICENSE <../../LICENSE
% ./repo_put.py --prefix /ccnx/pycn-lite --suite ccnx2015 ../../demo/flic_dir /ccnx/pycn-lite/LICENSE <../../LICENSE
```

Note the different directory names for the repo's files (to avoid
confusion when looking at the example chunks).


### FORWARDER Howto (UNIX commandline) - run a ICN forwarder

```
% cd PyCN-lite/bin

% ./srv_fwd.py 127.0.0.1:6363 &
```
See pycn_lite/server/config.py for default parameters


### REPO-SERVER Howto (UNIX commandline) - run a ICN repo server

```
% cd PyCN-lite/bin

% ./srv_repo.py ../../demo/repo_dir 127.0.0.1:6363 &
# or:
% micropython ./srv_repo.py ../../demo/repo_dir 127.0.0.1:6363 &
```
See pycn_lite/server/config.py for default parameters


### Combined FORWARDER and REPO-SERVER Howto (UNIX commandline)

```
% cd PyCN-lite/bin

% ./srv_fwdrepo.py ../demo/../repo_dir 127.0.0.1:6363 &
```
See pycn_lite/server/config.py for default parameters


## TODO

* validate the ndn and ccnx packet formats
* complete the FLIC library for ccnx
* add (any and a lots of) unit tests
* make the CS optional for UNIX (currently disabled because of ESP8266)
* add signing routines
* ...

## Confirmed IoT devices running the PyCN-lite software:

ESP8266 (features separate WiFis for uplink and local AP, 96KB RAM of
which 28KB is left for Micropython applications)
* [nodeMCU](http://nodemcu.com/index_en.html)
