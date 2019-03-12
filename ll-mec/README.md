# Create and run a docker container with the LL-MEC that is able to run snap packages

This script allows you to create docker containers already hosting the LL-MEC.

**WARNING NOTE**: This will create a container with **security** options **disabled**, this is an unsupported setup, if you have multiple snap packages inside the same container they will be able to break out of the confinement and see each others data and processes. Use this setup to build or test single snap packages but **do not rely on security inside the container**.

```
usage: build_docker-ll-mec.sh [options]

  -c|--containername <name> (default: oai-ll-mec)
  -i|--imagename <name> (default:oai-ll-mec-image)
```

## Examples

Creating a container with defaults (image: oai-ll-mec-image, container name: oai-ll-mec):

```
$ sudo apt install docker.io
$ ./build_docker-ll-mec.sh
```

If you want to create subsequent other containers using the same image, use the --containername option with a subsequent run of the ./build_docker-ll-mec.sh script.

```
$ ./build_docker-oai-cn.sh -c second
$ sudo docker exec -it second snap list
Name     Version                       Rev   Tracking  Publisher   Notes
core     16-2.38~pre1+git1188.69c1cf2  6615  edge      canonicalâ  core
flexran  1.4                           12    edge      mosaic-5g   devmode
$
```
### Docker hostname of the docker is **ubuntu**:
```
$ docker ps
CONTAINER ID        IMAGE                   COMMAND                  CREATED             STATUS              PORTS                            NAMES
fbd65c797040        oai-flexran-image       "/sbin/init"             8 minutes ago       Up 8 minutes        2210/tcp, 9999/tcp               oai-flexran
sudo docker exec -it fbd65c797040 bash
root@ubuntu:/# hostname
ubuntu
```
### Example of installing and running a snap package:

This will install the htop snap and will show the running processes inside the container after connecting the right snap interfaces.

```
$ sudo docker exec oai-ll-mec snap install htop
htop 2.0.2 from 'maxiberta' installed
$ sudo docker exec oai-ll-mec snap connect htop:process-control
$ sudo docker exec oai-ll-mec snap connect htop:system-observe
$ sudo docker exec -ti oai-ll-mec htop
```
## Extra packages installed in the Docker 
```
1. net-tools
2. iputils-ping
3. vim
4. 
5. 

```
