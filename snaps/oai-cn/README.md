# Building

Build with OAI-CN `snapcraft` from the source file.

# Installation

To use on an Ubuntu 16.04 or later system (14.04 should work too but untested),
install stable updates and make sure snaps are working:
```shell
snap version
sudo snap install hello-world
hello-world
```

Then install with:
```shell
snap find oai-cn
sudo snap install --devmode oai-cn*.snap
```

OAI-CN config file operation: list, set, get, show commands:
```shell
oai-cn.list-mme-conf            : show the list of available MME configuration file
oai-cn.set-mme-conf  myenb.conf : set the default MME configuration file
oai-cn.get-mme-conf             : get the path to the default MME configuration file
oai-cn.show-mme-conf            : show the content of the default MME configuration file
```
Note that you need to manually configure the parameters within the config file. The same commands are available for SPGW and HSS.

# Operation

The default configuration file is generated under
`/var/snap/oai-cn/current/mme/mme.conf` and `/var/snap/oai-cn/current/mme/mme_fd.conf`  during the snap installation.
The customized configuration file, set by the user using the `oai-cn.set-mme-conf  mymme.conf` command, is stored in ~/snap/oai-cn/current directory.





