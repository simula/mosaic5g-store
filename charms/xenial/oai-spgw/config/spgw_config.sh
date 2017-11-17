#!/bin/bash
juju config oai-spgw sgw-eth=br-eth0
juju config oai-spgw  pgw-eth=br-eth0
juju config oai-spgw  DEFAULT_DNS_IPV4_ADDRESS=172.27.60.1
juju config oai-spgw  DEFAULT_DNS_SEC_IPV4_ADDRESS=172.27.61.254
juju config oai-spgw  ipv4_list_start="172.16.0.0/12"
juju config oai-spgw  ipv4_list_end="172.16.0.0/12"
