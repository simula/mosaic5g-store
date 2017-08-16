# Overview OAI NFV RF

This bundle defines a service templates for a 5G Cloud RAN deployment with RRU running on the ubuntu CORE with functional split based on the OpenAirInterface (OAI).

It makes use of the following charms: MYSQL, OAI-HSS, OAI-MEE, OAI-SPGW, OAI-ENB, OAI-RRU-SNAP. You also need a radio frontend that has to be available to the OAI-RRU charm. While the HSS is already provisioned for a set of SIM, you can provision it for your SIM inforrmation. For this, you need to deploy and expose the [phpmyadmin charm](https://jujucharms.com/u/simonsmith5521/phpmyadmin/precise/1).

Machine provisioning, number of service units, and service placements must be adapted to particular cloud infrastructure nd use cases. 

You may generate your own service bundle by adapting this bundle or using the online tool.

# Useful Links
[Creating and using Bundles](https://jujucharms.com/docs/2.0/charms-bundles)
and 
[Demo juju charms](https://demo.jujucharms.com/)

# Contact Information

- [OpenAirInterface website](https://twiki.eurecom.fr/twiki/bin/view/OpenAirInterface/WebHome)
- [Source code](https://gitlab.eurecom.fr/oai/)
- [Mailing List](openair4g-devel@lists.eurecom.fr)
- [More info](contact@openairinterface.org and navid.nikaein@eurecom.fr)
