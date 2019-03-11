# Create and run a docker container with the OAI-CN that is able to run snap packages

This script allows you to create docker containers already hosting the OAI-CN.

**WARNING NOTE**: This will create a container with **security** options **disabled**, this is an unsupported setup, if you have multiple snap packages inside the same container they will be able to break out of the confinement and see each others data and processes. Use this setup to build or test single snap packages but **do not rely on security inside the container**.

```
usage: build_docker-oai-cn.sh [options]

  -c|--containername <name> (default: oai-cn-all-in-one)
  -i|--imagename <name> (default:oai-cn-all-in-one-image)
```

## Examples

Creating a container with defaults (image: oai-cn-all-in-one-image, container name: oai-cn-all-in-one):

```
$ sudo apt install docker.io
$ ./build_docker-oai-cn.sh
```

If you want to create subsequent other containers using the same image, use the --containername option with a subsequent run of the ./build.sh script.

```
$ ./build_docker-oai-cn.sh -c second
$ sudo docker exec second snap list
Name    Version                       Rev   Tracking  Publisher   Notes
core    16-2.38~pre1+git1187.b587616  6599  edge      canonicalâ  core
oai-cn  1.3                           26    edge      mosaic-5g   devmode

$
```

### Example of installing and running a snap package:

This will install the htop snap and will show the running processes inside the container after connecting the right snap interfaces.

```
$ sudo docker exec oai-cn-all-in-one snap install htop
htop 2.0.2 from 'maxiberta' installed
$ sudo docker exec oai-cn-all-in-one snap connect htop:process-control
$ sudo docker exec oai-cn-all-in-one snap connect htop:system-observe
$ sudo docker exec -ti oai-cn-all-in-one htop
```
## Extra packages installed in the Docker 

1. net-tools
2. iputils-ping
3. vim
4. 
5. 

```

```
# General software architecture tested

```
			-----------------		-----------------------			---------------------
			| Docker OAI-CN |		| Docker-MYSQL-OAI-DB |			| Docker-PHPMYADMIN |
docker0		<->	|		|	<->	|		      |		<->	|		    |
			|		|		|		      |			|		    |
			|		|		|		      |			|		    |
			-----------------		-----------------------			---------------------
172.17.0.1  		  172.17.0.0/24			     172.17.0.0/24 		            172.17.0.0/24
```					   	


Exposed for the users is 0.0.0.0:8081 with the user root and password defined in the hss.conf.
In order to import the standard OAI-CN-HSS-MYSQL-DB in the MYSQ-DB it is necesary to follow the below command.

```
root@fa9a6c67fdb7:/# oai-cn.hss-reset-db 
mysql: [Warning] Using a password on the command line interface can be insecure.
using: MYSQL_SERVER=172.17.0.2, MYSQL_USER=root, MYSQL_PASS=linux HSS_DB_Q1=DROP DATABASE IF EXISTS oai_db;
mysql: [Warning] Using a password on the command line interface can be insecure.
mysql: [Warning] Using a password on the command line interface can be insecure.
mysql: [Warning] Using a password on the command line interface can be insecure.
Successfully Imported the OAI HSS DB to mysql
```

```



```
In the end you need to have the following sets of Dockers 

```
CONTAINER ID        IMAGE                     COMMAND                  CREATED             STATUS              PORTS                            NAMES
9719b646d733        phpmyadmin/phpmyadmin     "/run.sh supervisordâ¦"   8 hours ago         Up 8 hours          9000/tcp, 0.0.0.0:8081->80/tcp   oai-mysql-phpmyadmin
5afeae5bc001        mysql:5.7                 "docker-entrypoint.sâ¦"   8 hours ago         Up 8 hours          3306/tcp, 33060/tcp              oai-cn-mysql-hss
fa9a6c67fdb7        oai-cn-all-in-one-image   "/sbin/init"             3 days ago          Up 8 hours                                           oai-cn-all-in-one
```


The set of the Docker images used are :
```
$ docker images
REPOSITORY                TAG                 IMAGE ID            CREATED             SIZE
oai-cn-all-in-one-image   latest              da71faab30f1        3 days ago          328MB
mysql                     5.7                 ee7cbd482336        5 days ago          372MB
phpmyadmin/phpmyadmin     latest              c6ba363e7c9b        6 weeks ago         166MB
```

```
