# Overview

he FlexRAN master controller was built from scratch using C++ and currently supports x64 Linux systems. The implementation supports both a real-time and non real-time mode of operation to cater for different time criticalities of the deployed applications and the requirements of the network operators. 

# Usage

This charm is available in the Juju Charm Store, to deploy you'll need a working 
Juju installation, and a successful bootstrap.

    juju deploy flexran-rtc

# Configuration

You can tweak various options for your flexran-rtc deployment:

  * snap -  set the channel to install  the FlexRAN snap 
 
 * bind_addr - set the network interface address to which the controller is binded. Defaul is all interfaces. 

 * bind_sbi_port -  set the port number for the south-bound interface towards the BS.

 * bind_nbi_port -  set the port number for the north-bound interface towards software-development kit and the network control apps.
 


# Contact Information

## FLEXRAN 
 - [FLEXRAN website](http://mosaic-5g.io/flexran/)
## OpenairInterface


## MOSAIC-5G
- [MOSIAC-5G website](mosiac-5g.org)
- [MOSAIC-5G mailing list](contact@mosaic-5g.io)
