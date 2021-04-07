# Overview

The Home Subscriber Server (HSS) is in charge of storing and updating when
necessary the database containing all the user subscription information. 
It supports authentication, authorization and mobility management functions. 
The HSS provides support to the Mobility Management Entity (MME) in order to 
complete the routing and roaming procedures by resolving authentication, 
authorization, naming and addressing resolution, and location dependencies.

This charm aims to deploy HSS functions of OpenAirInterface (OAI) wireless technology platform, a opensource software-based implementation of the LTE system developed by EURECOM. It is written in the C programming language.


# Usage

This charm is available in the Juju Charm Store, to deploy you'll need a working 
Juju installation, and a successful bootstrap. This charm need to be deployed 
with other charms to get a open LTE network made up of LTE base station and core
network. Mysql charm should be related to HSS. The latter should be related
to EPC charm that should be related to either the OAI eNB charms (either simulated or realtime eNB). 
In a simulated mode, OAI eNB has no radio frontend and integrates the UE protocol, and the process is denoted as "oaisim". In realtime mode, OAI eNB has a radio frontend and operates in a realtime mode, and the process is called "lte-softmodem". The eNB charms and UE charm are under development and will be available in the near future allowing one to install the software to manage a real antenna.

Please refer to the
[Juju Getting Started](https://juju.ubuntu.com/docs/getting-started.html)
documentation before continuing.

__For the time being__ you can use a cloud environment if you have, the manual environment
or the local provider. You could use also your private openstack cloud or MAAS, 
but you stick to manual environment if you don't want to add complexity, and want to manually manage your group of machines. 
For the local provider you must force juju to create kvm instead of lxc by modifying appropriately the environment.yaml file. 
Kvm is needed by EPC software because it deals with kernel modules.
__As soon as the OAI ENB charms will be available__ you will have to use your group of machines to use the right hardware(exmimo2 or usrp).

## Local provider

Once bootstrapped, deploy the MySQL charm then this HSS charm:

    juju deploy mysql
    juju deploy hss

Have a look at what's going on:

    watch juju status --format tabular

Juju creates two KVM nodes with a hss unit and a mysql unit.

Add a relation between the two:

    juju add-relation hss mysql

You can deploy in two lxc nodes within a single kvm by refering to the
[LXC Containers within a KVM Guest](https://jujucharms.com/docs/devel/config-KVM#lxc-containers-within-a-kvm-guest) 

To have a look at the hss output:
    
    juju ssh hss/0
    cat /srv/.out  

Then you could add EPC charm to complete the LTE core network:

    juju deploy epc

Now you have one unit of epc service named "epc" and a unit of hss service named "hss".

Add a relation between epc and hss:

    juju add-relation epc hss

Have a look at the EPC output and see if it is connected to HSS service:
    
    juju ssh epc/0
    cat /srv/.out  

The order of deployment doesn't matter, so you can't deploy all the charms you want to and then add all the relations afterwards. The order in which relations are added can be whatever you want.

Then to complete the LTE network you will have the chance to deploy a simulation of enB and UE:

    juju deploy oaisim(WATCHOUT: YOU CAN'T DO THIS YET) 

In local, only a simulation of the enodeB can be deployed. As soon as enodeB charm is 
completed you'll need to deploy on a machine with an antenna so manual provisioning can be appropriate.

## Manual environment

Deployment example: all KVM nodes in one physical machine(juju bootstrap node).

Once bootstrapped, deploy the MySQL charm then this Hss charm:

    juju deploy --to kvm:0 mysql
    juju deploy --to kvm:0 hss

Juju creates two KVM nodes with a unit of hss and a unit of mysql.

Add a relation between the two:

    juju add-relation hss mysql

To have a look at the hss unit output:
    
    juju ssh hss/0
    cat /srv/.out

Then you could add a unit of EPC charm to complete the LTE core network:

    juju deploy --to kvm:0 epc

Add a relation between the epc service unit and hss service unit:

    juju add-relation epc hss

To have a look at the epc output and see if it is connected to hss unit:
    
    juju ssh epc/0
    cat /srv/.out

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
    juju deploy --to 0 hss

    
    juju deploy --to 1 epc-rome
    juju deploy --to 2 epc-nice
    juju deploy --to 3 epc-torino


    juju add-relation hss mysql
    juju add-relation epc-rome hss
    juju add-relation epc-nice hss
    juju add-relation epc-torino hss

IN FUTURE:

You could add  enodeB services and relate them to a specific EPC service.


## Scale Out Usage
1) TO DO: horizontal scalability for HSS using a load balancer.

2) TO DO: Mysql cluster (
MySQL cluster technology provides
support for synchronous replication, automatic load balancing across data
nodes, data partitioning across data nodes, and automatic fail over. Designing a
system by using MySQL cluster delivers high
availability, high scalability, and high reliability).
(hacluster)

## MySQL Slave

TO DO. This needs support in hss. At the moment there's not the slave relation in HSS charm.
FUTURE

## Known Limitations and Issues

 * **Removing relation between hss service and mysql service(consider the simple case in which we have only one service of hss charm and for this service we have deployed only one unit. Same for mysql service)**


    juju remove-relation hss mysql

If you need to remove the relation between hss service and mysql service, HSS sofware
is stopped and so EPC running software fails to connect to HSS that is put in a zombie state. For this reason db-relation-departed hook execution triggers hss-relation-changed hook on EPC side that stops EPC sofware. As soon
as you re-add a relation with a mysql service, HSS process will be restarted and the db-relation-changed hook execution will trigger hss-relation-changed hook in each EPC unit that will start EPC sofware again.

   __Be aware that the new mysql unit doesn't have the old data, but simply the mme entries to allow the MMEs to connect to hss__

TO DO. Review what just described when OAISIM charm will available.

 * **Removing relation between epc service and hss service**

    juju remove-relation epc-rome hss

Each EPC unit's sofware of the chosen EPC service will be stopped and HSS will be removing the MMEs 
from the database. HSS process remains active because you might 
have more EPC services(epc-rome, epc-turin, epc-nice) using 
the same HSS so we don't want to break the connections.

In future there will be the explanation on what's going on on U-TRAN side(enodeB) as soon as the 
enodeB charm will be available.

 * **Removing HSS unit (for deploying the unit on another machine)**

    
    juju remove-unit hss/0 

When you remove a HSS unit, the relation hooks are
called concurrently in EPC and HSS for the hss relation and in HSS and MYSQL for the db 
relation. If you remove a unit that still has active relations can be dangerous. So it is better to remove first all the relations(db, hss: no matter the order) and
then remove the unit. 
([Removing services, units and environments](https://jujucharms.com/docs/stable/charms-destroy#removing-services,-units-and-environments))
Anyway at the end the stop hook is called to stop HSS software before juju removes the unit 
from the environment.
How to act:

    juju deploy --to ... hss (somewhere)
    juju add-relation epc-rome hss
    juju add-relation epc-nice hss
    juju add-relation hss mysql

 * **Upgrading HSS service**

    juju upgrade-charm hss

When you upgrade HSS charm(juju upgrade-charm hss) HSS software is stopped, rebuilt and restarted.
Each EPC unit fails to connect to HSS and doesn't reattempt to connect. As soon as HSS is running(see /srv/.out)
you restart EPC process:

    juju do action epc/0 restart

Do it for each EPC unit connected to the HSS unit.
 
This action must be done only if there is a relation between EPC and HSS.

# Configuration

You can tweak various options for your EPC deployment:

 * **realm** - Diameter realm of the MME. HSS and EPC have to have the same. NO empty value.
 
 * **debug** - The values can be yes or no depending on how much info you want 
   in the output of the building process. NO empty value

Each of these can be applied by running:

    juju set <service> <option>=<value>

e.g.

    juju set hss realm=mme_gw.lte
    juju set hss debug=no

__Be aware that everytime you change an option runtime you destroy the service continuity.__

We need to distinguish two cases:

1) **If HSS has a relation with MYSQL**, after you set a new value for an option, 
HSS service is stopped with the purpose of rebuilding and restarting it just to take into
account the new configuration. The EPC connection to HSS fails and since EPC doesn't reattempt
to establish a connection we should do an action simply to restart EPC process to reconnect to 
new HSS process that is waiting. 

    juju action do epc/0 restart

2) **If HSS hss no relation with MYSQL**, then you can set new options normally without any further action. 



REALM ISSUE: when you change the realm, you must do it for both HSS and EPC. First set the new realm:

    juju set hss realm=lte.lte
    juju set epc realm=lte.lte

Then depending on which one is restarted first you might need to do:

    juju action do epc/0 restart

Once HSS is running you can checkout the output of each EPC unit and see whether it is connected
to HSS or not. If it is not, you trigger the restart action.

# Contact Information
## MOSAIC-5G
- [MOSIAC-5G website](http://mosaic-5g.io/)
- [MOSAIC-5G mailing list](contact@mosaic-5g.io)

## OpenairInterFace

- [OpenAirInterface website](http://www.openairinterface.org/)
- [Source code](https://gitlab.eurecom.fr/oai/openair-cn/)
- [Mailing List](openaircn-devel@lists.eurecom.fr)
- [More info](contact@openairinterface.org)
