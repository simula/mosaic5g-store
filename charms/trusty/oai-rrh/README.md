# Overview

Remote Radio head (RRH) Gateway.

This charm provides an Ethernet-based RRH gateway function that can be connected to the OpenAirInterface eNB.

# Usage

This charm is available in the Juju Charm Store, to deploy you'll need a working Juju installation, and a successful bootstrap. This charm need to be deployed with oai-enb charm to setup an LTE base station.

# Configuration

You can tweak various options for your oai-epc deployment:
 * target_hardware - default usrp

 * frontaul_if - default eth0

 * fronthaul_port - default 2210

 * transport_mode - default udp

 * verbosity - default none

 * loopback - default no


# Contact Information

## OpenairInterface

- [OpenAirInterface website](https://twiki.eurecom.fr/twiki/bin/view/OpenAirInterface/WebHome)
- [Source code](https://gitlab.eurecom.fr/oai/openair-cn/)
- [Mailing List](openair4g-devel@lists.eurecom.fr)
- [More info](contact@openairinterface.org)

# TODOs