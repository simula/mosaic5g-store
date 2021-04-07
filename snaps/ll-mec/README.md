# Building

Build with LL-MEC `snapcraft` from the source file.

# Installation

To use on an Ubuntu 16.04 or later system ,
install stable updates and make sure snaps are working:
```shell
snap version
sudo snap install hello-world
hello-world
```

Then install with:
```shell
sudo snap install --devmode ll-mec*.snap
```

LL-MEC config file operation: set, get, show commands:
```shell
ll-mec.conf-set  llmec_config.jsom
ll-mec.conf-get
ll-mec.conf-show
```
Note that you need to manually configure the parameters within the config file.

LL-MEC  manual execution with inline logs: run, debug commands
```shell
ll-mec 
ll-mec.debug
```
Note that run and debug commands will take the config file set with `ll-mec.set-conf  llmec_config.json` command.

LL-MEC  execution with snap command: start, stop, restart, services commands:
```shell
sudo snap services
sudo snap stop ll-mec
sudo snap start ll-mec
sudo snap restart ll-mec
```

LL-MEC execution as daemon, start, stop, restart, status
```shell
sudo systemctl restart snap.ll-mec.daemon.service
sudo systemctl status  snap.ll-mec.daemon.service
sudo systemctl start  snap.ll-mec.daemon.service
sudo systemctl stop  snap.ll-mec.daemon.service
```

Use journalctl to check the ll-mec output :
```shell
sudo journalctl -u snap.ll-mec.daemon.service
```

# Operation

The default configuration file is generated under
`/var/snap/ll-mec/current/llmec_config.json`  during the snap installation.
The customized configuration file, set by the user using the `ll-mec.set-conf  llmec_config.json` command, is stored in ~/snap/ll-mec/current directory.
