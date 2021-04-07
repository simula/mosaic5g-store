# Overview

The LL-MEC platform is made up of two main components: the LL-MEC platfrom and data-control APIs. The LL-MEC provides two main services: native IP-service endpoint and realtime radio network information to MEC applications on per user and service basis, and can be connected to a number of underlying RANs and CN gateways. The data plane APIs acts as an abstraction layer between RAN and CN data plane and LL-MEC platform. The OpenFlow and FlexRAN protocols facilitate the communication between the LL-MEC and underlying RAN and CN. With LL-MEC, coordinated RAN and CN network applications can be developed by leveraging both LL-MEC and FlexRAN SDKs allowing to monitor and control not only the traffic but also the state of network infrastructure. Such applications could vary from elastic application that obtain user traffic statistics to low latency applications that redirect user traffic (local breakout) and apply policies to setup the data path. All the produced RAN and CN data and APIs are open to be consumed by other apps as well as 3rd parties.

# Usage

This charm is available in the Juju Charm Store, to deploy you'll need a working 
Juju installation, and a successful bootstrap.

    juju deploy ll-mec

# Configuration

Available ll-mec configuration options :

 * snap -  set the channel to install  the ll-mec snap 

 * bind_addr - set the addr of interface to which the LL-MEC is binded. Defaul is all interfaces. 

 * bind_sbi_port -  set the south-bound port number towards user-plane function provided by OVS.

 * bind_nbi_port -  set the north-bound port number for REST API calls towards software-development kit and the network control apps.

 * gw_mac_addr -  set the mac address of the gateway (where NAT is performed).


# Contact Information

##  
 - [LL-MEC website](http://mosaic-5g.io/ll-mec/)

## MOSAIC-5G
- [MOSIAC-5G website](http://mosaic-5g.io/)
- [MOSAIC-5G mailing list](contact@mosaic-5g.io)
