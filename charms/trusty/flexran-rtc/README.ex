# Overview

he FlexRAN master controller was built from scratch using C++ and currently supports x64 Linux systems. The implementation supports both a real-time and non real-time mode of operation to cater for different time criticalities of the deployed applications and the requirements of the network operators. 

# Usage

This charm is available in the Juju Charm Store, to deploy you'll need a working 
Juju installation, and a successful bootstrap.

    juju deploy flexran-rtc

# Configuration

You can tweak various options for your flexran-rtc deployment:

 * branch -  set the branch name 

 * revision - set the revision number

 * user_name - set the user name

 * passwd - set the user password

 * kernel - set the linux kerenl type, generic or lowlatency

 * bind_if - set the name of interface to which the controller is binded. Defaul is all interfaces. 

 * bind_port -  set the port number.


# Contact Information

## FLEXRAN 
 - [FLEXRAN website](hhttp://networks.inf.ed.ac.uk/flexran)
## OpenairInterface

- [OpenAirInterface website](https://twiki.eurecom.fr/twiki/bin/view/OpenAirInterface/WebHome)
- [Source code](https://gitlab.eurecom.fr/oai/openair-cn/)
- [Mailing List](openair4g-devel@lists.eurecom.fr)
- [More info](contact@openairinterface.org)

## MOSAIC-5G
- [MOSIAC-5G website](mosiac-5g.org)
- [MOSAIC-5G mailing list](mosiac-5g@list.eurecom.fr)

# TODOs

 * Double-check what exactly needs permissions. At the moment all runs under root.
 * Change upstart script in a way that if the machine is rebooted the oai-enb process is automatically restarted if it was running during the shutdown procedure.
