# Building

Build with FlexRAN  `snapcraft` from the source file.

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
sudo snap install --devmode flexran*.snap
```


FlexRAN  manual execution with inline logs: run, debug commands
```shell
flexran
flexran.debug
flexran.help
```

FlexRAN execution with snap command: start, stop, restart, services commands:
```shell
sudo snap services
sudo snap stop flexran
sudo snap start flexran
sudo snap restart flexran
```

FlexRAN execution as daemon, start, stop, restart, status
```shell
sudo systemctl restart snap.flexran.daemon.service
sudo systemctl status  snap.flexran.daemon.service
sudo systemctl start  snap.flexran.daemon.service
sudo systemctl stop  snap.flexran.daemon.service
```

Use journalctl to check the flexran output :
```shell
sudo journalctl -u snap.flexran.daemon.service
```

# Operation

The default log configuration file is generated under
`/var/snap/flexran/current/log_config`  during the snap installation.
