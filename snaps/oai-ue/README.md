# Building

Build with OAI-RAN `snapcraft` from the source file.

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
snap find oai-ran
sudo snap install --devmode oai-ran*.snap
```

OAI-RAN config file operation: list, set, get, show commands:
```shell
oai-ran.list-conf            : show the list of available configuration file
oai-ran.set-conf  myenb.conf : set the default configuration file
oai-ran.get-conf             : get the path to the default configuration file
oai-ran.show-conf            : show the content of the default configuration file
```
Note that you need to manually configure the parameters within the config file.

OAI-RAN manual execution with inline logs: run, debug commands
```shell
oai-ran
oai-ran.debug
```
Note that run and debug commands will take the config file set with `oai-ran.set-conf  myenb.conf` command.

OAI-RAN  execution with snap command: start, stop, restart, services commands:
```shell
sudo snap services
sudo snap stop oai-ran
sudo snap start oai-ran
sudo snap restart oai-ran
```

OAI-RAN execution as daemon, start, stop, restart, status
```shell
sudo systemctl restart snap.oai-ran.daemon.service
sudo systemctl status  snap.oai-ran.daemon.service
sudo systemctl start  snap.oai-ran.daemon.service
sudo systemctl stop  snap.oai-ran.daemon.service
```

Use journalctl to check the oai-ran output :
```shell
sudo journalctl -u snap.oai-ran.daemon.service
```

# Operation

The default configuration file is generated under
`/var/snap/oai-ran/current/enb.band7.tm1.50PRB.usrpb210.conf`  during the snap installation.
The customized configuration file, set by the user using the `oai-ran.set-conf  myenb.conf` command, is stored in ~/snap/oai-ran/current directory.





