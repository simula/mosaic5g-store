# Create and run a docker container with the OAI-CN that is able to run snap packages

This script allows you to create docker containers already hosting the OAI-CN.

**WARNING NOTE**: This will create a container with **security** options **disabled**, this is an unsupported setup, if you have multiple snap packages inside the same container they will be able to break out of the confinement and see each others data and processes. Use this setup to build or test single snap packages but **do not rely on security inside the container**.

Note: The host machine which hosts the Dockers needs to have the 4.7.x kernel from pre-compiled debian package and enable the GTP module

## Installing the kernel:
```
$ git clone https://gitlab.eurecom.fr/oai/linux-4.7.x.git
$ cd linux-4.7.x
$ sudo dpkg -i linux-headers-4.7.7-oaiepc_4.7.7-oaiepc-10.00.Custom_amd64.deb linux-image-4.7.7-oaiepc_4.7.7-oaiepc-10.00.Custom_amd64.deb
```
## Rebooting the host machine to load the new features:
```
$ sudo reboot now
```
## Test if the new kernel is load:
```
$ uname -a
## The output of the previous command should be similar to : Linux <hostname_of_the_host_machine> 4.7.1 
```
## Enable the GTP module in linux kernel:
```
$ sudo modprobe gtp
```
## Check if the module was loaded:
```
$ dmesg |tail # You should see something that says about GTP kernel module
```

```
usage: build_docker-oai-cn.sh [options]

  -c|--containername <name> (default: oai-cn-all-in-one)
  -i|--imagename <name> (default:oai-cn-all-in-one-image)
```

## Examples

Creating a container with defaults (image: oai-cn-all-in-one-image, container name: oai-cn-all-in-one):

```
$ sudo apt install docker.io
$ ./build_docker-oai-cn.sh
$ ./build_mysql_db.sh
```

If you want to create subsequent other containers using the same image, use the --containername option with a subsequent run of the ./build_docker-oai-cn.sh script.

```
$ ./build_docker-oai-cn.sh -c second
$ sudo docker exec second snap list
Name    Version                       Rev   Tracking  Publisher   Notes
core    16-2.38~pre1+git1187.b587616  6599  edge      canonicalâ  core
oai-cn  1.3                           26    edge      mosaic-5g   devmode

$
```

### Example of installing and running a snap package:

This will install the htop snap and will show the running processes inside the container after connecting the right snap interfaces.

```
$ sudo docker exec oai-cn-all-in-one snap install htop
htop 2.0.2 from 'maxiberta' installed
$ sudo docker exec oai-cn-all-in-one snap connect htop:process-control
$ sudo docker exec oai-cn-all-in-one snap connect htop:system-observe
$ sudo docker exec -ti oai-cn-all-in-one htop
```
## Extra packages installed in the Docker 

1. net-tools
2. iputils-ping
3. vim
4. 
5. 

```

```
# General software architecture tested

```
			-----------------		-----------------------			---------------------
			| Docker OAI-CN |		| Docker-MYSQL-OAI-DB |			| Docker-PHPMYADMIN |
docker0		<->	|		|	<->	|		      |		<->	|		    |
			|		|		|		      |			|		    |
			|		|		|		      |			|		    |
			-----------------		-----------------------			---------------------
172.17.0.1  		  172.17.0.0/24			     172.17.0.0/24 		            172.17.0.0/24
```					   	


Exposed for the users is 0.0.0.0:8081 with the user root and password defined in the hss.conf.
In order to import the standard OAI-CN-HSS-MYSQL-DB in the MYSQ-DB it is necesary to follow the below command.

```
root@fa9a6c67fdb7:/# oai-cn.hss-reset-db 
mysql: [Warning] Using a password on the command line interface can be insecure.
using: MYSQL_SERVER=172.17.0.2, MYSQL_USER=root, MYSQL_PASS=linux HSS_DB_Q1=DROP DATABASE IF EXISTS oai_db;
mysql: [Warning] Using a password on the command line interface can be insecure.
mysql: [Warning] Using a password on the command line interface can be insecure.
mysql: [Warning] Using a password on the command line interface can be insecure.
Successfully Imported the OAI HSS DB to mysql
```


In the end you need to have the following sets of Dockers 

```
CONTAINER ID        IMAGE                     COMMAND                  CREATED             STATUS              PORTS                            NAMES
9719b646d733        phpmyadmin/phpmyadmin     "/run.sh supervisordâ¦"   8 hours ago         Up 8 hours          9000/tcp, 0.0.0.0:8081->80/tcp   oai-mysql-phpmyadmin
5afeae5bc001        mysql:5.7                 "docker-entrypoint.sâ¦"   8 hours ago         Up 8 hours          3306/tcp, 33060/tcp              oai-cn-mysql-hss
fa9a6c67fdb7        oai-cn-all-in-one-image   "/sbin/init"             3 days ago          Up 8 hours                                           oai-cn-all-in-one
```
## To enter any of the dockers and configure

```
$ sudo docker exec -it fa9a6c67fdb7 bash
root@fa9a6c67fdb7:/#
root@fa9a6c67fdb7:/# vi /var/snap/oai-cn/26/hss.conf
```
To modify the **hss.conf**, please modify the IP address of the MYSQL_server with the IP address of the **oai-cn-mysql-hss Docker** and change the comment between the **OPERATOR_key** parameters
```
################################################################################
# Licensed to the OpenAirInterface (OAI) Software Alliance under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The OpenAirInterface Software Alliance licenses this file to You under 
# the Apache License, Version 2.0  (the "License"); you may not use this file
# except in compliance with the License.  
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#-------------------------------------------------------------------------------
# For more information about the OpenAirInterface (OAI) Software Alliance:
#      contact@openairinterface.org
################################################################################
HSS :
{
## MySQL mandatory options
MYSQL_server = "172.17.0.2";     # HSS S6a bind address
MYSQL_user   = "root";           # Database server login
MYSQL_pass   = "linux";          # Database server password
MYSQL_db     = "oai_db";         # Your database name 

## HSS options
#OPERATOR_key = "1006020f0a478bf6b699f15c062e42b3"; # OP key matching your database
OPERATOR_key = "11111111111111111111111111111111"; # OP key matching your database

RANDOM = "true";                                   # True random or only pseudo random (for subscriber vector generation)

## Freediameter options
FD_conf = "/var/snap/oai-cn/current/hss_fd.conf";
};
```
Next to configure is the **hss_fd.conf** file
```
root@fa9a6c67fdb7:/# vi /var/snap/oai-cn/26/hss_fd.conf
```
To modify the **hss_fd.conf**, please modify the Identity FQDN with the hostname of the Docker.
Example, in our case is fa9a6c67fdb7
```
# -------- Local ---------
# The first parameter in this section is Identity, which will be used to 
# identify this peer in the Diameter network. The Diameter protocol mandates 
# that the Identity used is a valid FQDN for the peer. This parameter can be 
# omitted, in that case the framework will attempt to use system default value 
# (as returned by hostname --fqdn). 
Identity = "fa9a6c67fdb7.openair4G.eur";

# In Diameter, all peers also belong to a Realm. If the realm is not specified,
# the framework uses the part of the Identity after the first dot.
Realm = "openair4G.eur";


# This parameter is mandatory, even if it is possible to disable TLS for peers 
# connections. A valid certificate for this Diameter Identity is expected. 
TLS_Cred = "/var/snap/oai-cn/current/hss.cert.pem", "/var/snap/oai-cn/current/hss.key.pem";
TLS_CA = "/var/snap/oai-cn/current/hss.cacert.pem";


# Disable use of TCP protocol (only listen and connect in SCTP)
# Default : TCP enabled
No_SCTP;


# This option is ignored if freeDiameter is compiled with DISABLE_SCTP option.
# Prefer TCP instead of SCTP for establishing new connections.
# This setting may be overwritten per peer in peer configuration blocs.
# Default : SCTP is attempted first.
Prefer_TCP;


# Disable use of IPv6 addresses (only IP)
# Default : IPv6 enabled
No_IPv6;


# Overwrite the number of SCTP streams. This value should be kept low, 
# especially if you are using TLS over SCTP, because it consumes a lot of 
# resources in that case. See tickets 19 and 27 for some additional details on 
# this.
# Limit the number of SCTP streams
SCTP_streams = 3;


# By default, freeDiameter acts as a Diameter Relay Agent by forwarding all 
# messages it cannot handle locally. This parameter disables this behavior.
NoRelay;


# Use RFC3588 method for TLS protection, where TLS is negociated after CER/CEA exchange is completed
# on the unsecure connection. The alternative is RFC6733 mechanism, where TLS protects also the
# CER/CEA exchange on a dedicated secure port.
# This parameter only affects outgoing connections.
# The setting can be also defined per-peer (see Peers configuration section).
# Default: use RFC6733 method with separate port for TLS.

#TLS_old_method;


# Number of parallel threads that will handle incoming application messages. 
# This parameter may be deprecated later in favor of a dynamic number of threads
# depending on the load. 
AppServThreads = 4;

# Specify the addresses on which to bind the listening server. This must be 
# specified if the framework is unable to auto-detect these addresses, or if the
# auto-detected values are incorrect. Note that the list of addresses is sent 
# in CER or CEA message, so one should pay attention to this parameter if some 
# adresses should be kept hidden. 
#ListenOn = "127.0.0.1";

Port = 3868;
SecPort = 5868;

# -------- Extensions ---------

# Uncomment (and create rtd.conf) to specify routing table for this peer.
#LoadExtension = "rt_default.fdx" : "rtd.conf";

# Uncomment (and create acl.conf) to allow incoming connections from other peers.
LoadExtension = "acl_wl.fdx" : "/var/snap/oai-cn/current/acl.conf";

# Uncomment to display periodic state information
#LoadExtension = "dbg_monitor.fdx";

# Uncomment to enable an interactive Python interpreter session.
# (see doc/dbg_interactive.py.sample for more information)
#LoadExtension = "dbg_interactive.fdx";

# Load the RFC4005 dictionary objects
#LoadExtension = "dict_nasreq.fdx";

LoadExtension = "dict_nas_mipv6.fdx";
LoadExtension = "dict_s6a.fdx";

# Load RFC4072 dictionary objects
#LoadExtension = "dict_eap.fdx";

# Load the Diameter EAP server extension (requires diameap.conf)
#LoadExtension = "app_diameap.fdx" : "diameap.conf";

# Load the Accounting Server extension (requires app_acct.conf)
#LoadExtension = "app_acct.fdx" : "app_acct.conf";

# -------- Peers ---------

# The framework will actively attempt to establish and maintain a connection
# with the peers listed here.
# For only accepting incoming connections, see the acl_wl.fx extension.

#ConnectPeer = "ubuntu.localdomain" { ConnectTo = "127.0.0.1"; No_TLS; };
```

The set of the Docker images used are :
```
$ docker images
REPOSITORY                TAG                 IMAGE ID            CREATED             SIZE
oai-cn-all-in-one-image   latest              da71faab30f1        3 days ago          328MB
mysql                     5.7                 ee7cbd482336        5 days ago          372MB
phpmyadmin/phpmyadmin     latest              c6ba363e7c9b        6 weeks ago         166MB
```

```
To access the phpmyadmin webinterface, just lunch the host machine browser and type http://0.0.0.0:8081/db_structure.php?server=1&db=oai_db. 
Enter the root user credentials that you have set in the bash script file for diployment of the MYSQL Docker.
user 		: 		(default: root)
password 	:		(default: linux)

```
