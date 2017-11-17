# Overview

Evolved Packet Core (oai-spgw) is a framework for providing converged voice and data on a 4G
Long-Term Evolution (LTE) network. Evolved Packet Core unifies voice and data on an Internet
Protocol (IP ) service architecture and voice is treated as just another IP application. 

This charm aims to deploy oai-spgw/SPGW functions of OpenAirInterface (OAI) wireless technology platform, 
an opensource software-based implementation of the LTE system developed by EURECOM. It is written in the C programming language.


# Usage

This charm is available in the Juju Charm Store, to deploy you'll need a working 
Juju installation, and a successful bootstrap. This charm need to be deployed 
with other charms to get a open LTE network made up of LTE base station and core
network. Mysql charm should be related to oai-mme. The latter should be related
to oai-spgw/SPGW charm that should be related to either the OAI eNB charms (either simulated or realtime eNB). 
In a simulated mode, OAI eNB has no radio frontend and integrates the UE protocol, and the process is denoted as "oaisim".
In realtime mode, OAI eNB has a radio frontend and operates in a realtime mode, and the process is called "lte-softmodem".
The eNB charms and UE charm are under development and will be available in the near future allowing one 
to install the software to manage a real antenna.

Please refer to the
[Juju Getting Started](https://juju.ubuntu.com/docs/getting-started.html)
documentation before continuing.

__For the time being__ you can use a cloud environment if you have, the manual environment
or the local provider. You could use also your private openstack cloud or MAAS, 
but you stick to manual environment if you don't want to add complexity, and want to manually manage your group of machines. 
For the local provider you must force juju to create kvm instead of lxc by modifying appropriately the environment.yaml file. 
Kvm is needed by oai-spgw/SPGW software because it deals with kernel modules.
__As soon as the OAI ENB charms will be available__ you will have to use your group of machines to use the right hardware(exmimo2 or usrp).

## Local provider

Once bootstrapped, deploy the MySQL charm then this oai-mme charm:

    juju deploy mysql
    juju deploy oai-mme

Have a look at what's going on:

    watch juju status --format tabular

Juju creates two KVM nodes with a oai-mme unit and a mysql unit.

Add a relation between the two:

    juju add-relation oai-mme mysql

You can deploy in two lxc nodes within a single kvm by refering to the
[LXC Containers within a KVM Guest](https://jujucharms.com/docs/devel/config-KVM#lxc-containers-within-a-kvm-guest) 

To have a look at the oai-mme output:
    
    juju ssh oai-mme/0
    cat /srv/spgw.out  

Then you could add oai-spgw charm to complete the LTE core network:

    juju deploy oai-spgw

Now you have one unit of oai-spgw service named "oai-spgw" and a unit of oai-mme service named "oai-mme".

Add a relation between oai-spgw and oai-mme:

    juju add-relation oai-spgw oai-mme

Have a look at the oai-spgw output and see if it is connected to oai-mme service:
    
    juju ssh oai-spgw/0
    cat /srv/spgw.out  

The order of deployment doesn't matter, so you can't deploy all the charms you want to and then add all the relations afterwards. The order in which relations are added can be whatever you want.

Then to complete the LTE network you will have the chance to deploy a simulation of enB and UE:

    juju deploy oaisim(WATCHOUT: YOU CAN'T DO THIS YET) 

In local, only a simulation of the enodeB can be deployed. As soon as enodeB charm is 
completed you'll need to deploy on a machine with an antenna so manual provisioning can be appropriate.

## Manual environment

Deployment example: all KVM nodes in one physical machine(juju bootstrap node).

Once bootstrapped, deploy the MySQL charm then this oai-mme charm:

    juju deploy --to kvm:0 mysql
    juju deploy --to kvm:0 oai-mme

Juju creates two KVM nodes with a unit of oai-mme and a unit of mysql.

Add a relation between the two:

    juju add-relation oai-hss mysql

To have a look at the oai-mme unit output:
    
    juju ssh oai-mme/0
    cat /srv/spgw.out

Then you could add a unit of oai-spgw charm to complete the LTE core network:

    juju deploy --to kvm:0 oai-spgw

Add a relation between the oai-spgw service unit and oai-mme service unit:

    juju add-relation oai-spgw oai-mme

To have a look at the oai-spgw output and see if it is connected to oai-mme unit:
    
    juju ssh oai-spgw/0
    cat /srv/spgw.out

NEAR FUTURE:
Then to complete the LTE network you will have the chance to deploy a simulation of enB 
and UE:

    juju deploy --to kvm:0 oaisim(WATCHOUT: YOU CAN'T DO THIS YET)

Or a real enodeB charm(WORK IN PROGRESS) to deploy on a machine equipped with the right 
hardware(antenna).

### Group of services

Consider to deploy directly against physical machines because the KVM that juju creates 
are behind a NAT bridge. In fact if you want to use kvm, you should create some kvm containes
outside of juju with proper networking and add-machine to juju.


    juju deploy --to kvm:0 mysql
    juju deploy --to 0 oai-mme

    
    juju deploy --to 1 oai-spgw-rome
    juju deploy --to 2 oai-spgw-nice
    juju deploy --to 3 oai-spgw-torino


    juju add-relation oai-hss mysql
    juju add-relation oai-spgw-rome oai-mme
    juju add-relation oai-spgw-nice oai-mme
    juju add-relation oai-spgw-torino oai-mme

IN FUTURE:

You could add  enodeB services and relate them to a specific oai-spgw service.


## Scale Out Usage

If you need to scale out your oai-spgw-rome service(for instance), you can add another unit of oai-spgw-rome
by typing:

    juju add-unit oai-spgw-rome --to 4

Since the relation has been done at service level, the new unit of oai-spgw-rome service
knows exactly how to relate and even the configuration options are the same.
As soon as OAISIM charm will be available, you can deploy OAISIM charm and then
relate it to oai-spgw-rome service:

    juju add-relation oaisim oai-spgw-rome 

Oaisim will be related to both units of oai-spgw-rome service.

__More on scale out when oaisim or enodeb charm will be available.__


## Known Limitations and Issues

### Important

__Don't use the oai-spgw relation hooks. They will be usefull only when enodeB charm will be available.__

 * **Removing relation between oai-mme service and mysql service(consider the simple case in which we have only one service of oai-mme charm and for this service we have deployed only one unit. Same for mysql service)**


    juju remove-relation oai-hss mysql

If you need to remove the relation between oai-mme service and mysql service, oai-mme sofware
is stopped and so oai-spgw running software fails to connect to oai-mme that is put in a zombie state. For this reason db-relation-departed hook execution triggers oai-mme-relation-changed hook on oai-spgw side that stops oai-spgw sofware. As soon
as you re-add a relation with a mysql service, oai-mme process will be restarted and the db-relation-changed hook execution will trigger oai-mme-relation-changed hook in each oai-spgw unit that will start oai-spgw sofware again.

   __Be aware that the new mysql unit doesn't have the old data, but simply the mme entries to allow the MMEs to connect to oai-mme__

TO DO. Review what just described when OAISIM charm will available.

 * **Removing relation between oai-spgw service and oai-mme service**

    juju remove-relation oai-spgw-rome oai-mme

Each oai-spgw unit's sofware of the chosen oai-spgw service will be stopped and oai-mme will be removing the MMEs 
from the database. oai-mme process remains active because you might 
have more oai-spgw services(oai-spgw-rome, oai-spgw-turin, oai-spgw-nice) using 
the same oai-mme so we don't want to break the connections.

In future there will be the explanation on what's going on on U-TRAN side(enodeB) as soon as the 
enodeB charm will be available.

 * **Removing oai-mme unit (for deploying the unit on another machine)**

    
    juju remove-unit oai-mme/0 

When you remove a oai-mme unit, the relation hooks are
called concurrently in oai-spgw and oai-mme for the oai-mme relation and in oai-mme and MYSQL for the db 
relation. If you remove a unit that still has active relations can be dangerous. So it is better to remove first all the relations(db, oai-mme: no matter the order) and
then remove the unit. 
([Removing services, units and environments](https://jujucharms.com/docs/stable/charms-destroy#removing-services,-units-and-environments))
Anyway at the end the stop hook is called to stop oai-mme software before juju removes the unit 
from the environment.
How to act:

    juju deploy --to ... oai-mme (somewhere)
    juju add-relation oai-spgw-rome oai-mme
    juju add-relation oai-spgw-nice oai-mme
    juju add-relation oai-hss mysql
 
 * **Removing oai-spgw unit (for redeploying the unit on another machine: scaling up)**

   When you remove a oai-spgw unit (juju remove-unit oai-spgw-rome/1 for example) the relation hooks are
   called concurrently in oai-spgw and oai-mme to handle oai-mme relation.
   Then the stop hook is called to stop oai-spgw process before juju removes the unit from the 
   environment. How to act:

1) In the case you had more than one unit of oai-spgw-rome service:

   
    juju add-unit --to ... oai-spgw-rome (somewhere)

No need to add-relation.

2) In the case you had only one unit of a service:

    
    juju deploy --to ... oai-spgw-rome
    juju add-relation oai-spgw-rome oai-mme    

In future you probably will need to do: 

    juju add-relation oaisim oai-spgw-rome

 * **Upgrading oai-mme service**


    juju upgrade-charm oai-mme

When you upgrade oai-mme charm(juju upgrade-charm oai-mme) oai-mme software is stopped, rebuilt and restarted.
Each oai-spgw unit fails to connect to oai-mme and doesn't reattempt to connect. As soon as oai-mme is running(see /srv/spgw.out)
you restart oai-spgw process:

    juju do action oai-spgw/0 restart

Do it for each oai-spgw unit connected to the oai-mme unit.
 
This action must be done only if there is a relation between oai-spgw and oai-mme.

 * **Upgrading oai-spgw service**

    
    juju upgrade-charm oai-spgw-nice

When you upgrade oai-spgw-nice service, oai-spgw process is stopped, rebuilt and restarted.

__You will have to take care about the behaviour of the U-TRAN side. More on this when enodeb charm will be available__

# Configuration

You can tweak various options for your oai-spgw deployment:

 * realm - Diameter realm of the MME. oai-mme and oai-spgw have to have the same. NO empty value.

 * eth - This is usefull especially when you are in manual environment so you are
  your own machines. The default value is eth0.

 * maxenb - Maximum number of eNB that can connect to MME.

 * maxue - For debug purpose, used to restrict the number of served UEs the MME can handle.

 * relative-capacity - Even though this parameter is not used by the MME for controlling the MME load balancing within a pool (at least for now), the parameter has to be forwarded to the eNB during association procedure. Values going from 0 to 255.

 * mme-statistic-timer - Displayed statistic (stdout) period. You can access the stdout: cat /srv/spgw.out on the machine where oai-spgw charm is deployed.

 * emergency-attach-supported - 

 * authenticated-imsi-supported -

 * verbosity - asn1 verbosity is..... Valid values are "none", "info", or "annoying".

 * gummei-tai-mcc - TAI=MCC.MNC:TAC. MCC is the Mobile Country Code.

 * gummei-tai-mnc - TAI=MCC.MNC:TAC. MNC is the Mobile Network Code.

 * gummei-tai-tac - TAI=MCC.MNC:TAC. TAC is the Tracking Area Code.

 * ipv4-list-start - lower bound of the IP address range that will be assigned to UEs.

 * ipv4-list-end - upper bound of the IP address range that will be assigned to UEs.

 * ipv6-list - Ipv6 addresses available to be assigned to UEs.

 * DEFAULT-DNS-IPV4-ADDRESS - IPv4 address of primary default DNS that can be queried by UEs.

 * DEFAULT-DNS-SEC-IPV4-ADDRESS - IPv4 address of secondary default DNS that can be queried by UEs.

Each option can be changed before deployment by providing a "myconfig.yaml" to your deployment command with the value you want each option to take:


    juju deploy --to 7 --config /home/myconfig.yaml oai-spgw oai-spgw-berlin


Each option can be changed by running:

    juju set <service> <option>=<value>

e.g.

    juju set oai-spgw-rome maxue=15 
    juju set oai-spgw-rome maxue=20
    juju set oai-spgw-rome realm=open.lte
    juju set oai-spgw-rome verbosity=info

__Be aware that everytime you change an option runtime you destroy the service continuity of every UE registered to the MME entity inside one oai-spgw unit belonging to the oai-spgw-rome service.__

We need to distinguish two cases:

1) **If oai-spgw has a relation with oai-mme**, after you set a new value for an option, 
oai-spgw service is stopped with the purpose of rebuilding the config files and restarting it just to take into
account the new configuration. The oai-spgw connection to oai-mme fails, but oai-mme will be simply waiting
for an oai-spgw connection that will be automatically restablished after the config-changed hook is
executed. 

__On the U-TRAN side, we will have to see later what to do for enodeB only when it will be finished to be developed and on the charm store.__

2) **If oai-spgw has no relation with oai-mme**, you can set new options normally without any next action, but in
this case the config files are regenerated and oai-spgw software is not started. 

__ISSUE__: when you change the realm, you must do it for both oai-mme and oai-spgw. First of all we need to remove the relation between oai-spgw and oai-mme services, then set the new realm and finally re-add the relation:

    juju remove-relation oai-spgw oai-mme
    juju set oai-mme realm=lte.lte
    juju set oai-spgw realm=lte.lte
    juju add-relation oai-spgw oai-mme

# Contact Information

## OpenairInterface

- [OpenAirInterface website](https://twiki.eurecom.fr/twiki/bin/view/OpenAirInterface/WebHome)
- [Source code](https://gitlab.eurecom.fr/oai/openair-cn/)
- [Mailing List](openair4g-devel@lists.eurecom.fr)
- [More info](contact@openairinterface.org)

# TODOs
 
 * fix the issue when MNC and MCC is changing 
 * Check the scale-out mechanism. Understand how the load is balanced among different oai-spgw unit of a service all connected to one enodeb(FUTURE, when enodeb will be available)
 * Double-check what exactly needs permissions. At the moment all runs under root.
 * Complete the oai-spgw-relation hooks as soon as enodeb charm is available.
 * Change upstart script in a way that if the machine is rebooted the oai-spgw process is automatically restarted if it was running during the shutdown procedure.
