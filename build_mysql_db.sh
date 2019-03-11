#! /bin/bash
################################################################################
# Licensed to the Mosaic5G under one or more contributor license
# agreements. See the NOTICE file distributed with this
# work for additional information regarding copyright ownership.
# The Mosaic5G licenses this file to You under the
# Apache License, Version 2.0  (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  
#       http://www.apache.org/licenses/LICENSE-2.0

#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
# -------------------------------------------------------------------------------
#   For more information about the:
#       
#
#
################################################################################
# file 		build_mysql_db.sh
# brief  	MYSQL and PHPMYADMIN automated Docker deployment 
# author 	Mihai IDU (C) - 2019 mihai.idu@eurecom.fr


# defining the parameters for MYSQL Docker
CONTNAME=oai-cn-mysql-hss
IMGNAME=mysql
RELEASE=5.7

# defining the parameters for phpmyadmin Docker
CONTNAME_PHPMYADMIN=oai-mysql-phpmyadmin
IMGNAME_PHPMYADMIN=phpmyadmin/phpmyadmin

#Cheching if the docker images are pulled from the global repo' for mysql and phpmyadmin
if [ -n "$($SUDO docker images 2>&1 | grep $IMGNAME:$RELEASE )"]; then
	echo "The Docker Image $IMGNAME is already pull"
else 
	docker pull mysql:$RELEASE
fi

if [ -n "$($SUDO docker images 2>&1 | grep $IMGNAME_PHPMYADMIN)"]; then
        echo "The Docker Image $IMGNAME_PHPMYADMIN is already pull"
else
        docker pull $IMGNAME_PHPMYADMIN
fi

set -e


SUDO=""
if [ -z "$(id -Gn|grep docker)" ] && [ "$(id -u)" != "0" ]; then
    SUDO="sudo"
fi

#Checking if the docker is running 
if [ -n "$($SUDO docker ps -f name=$CONTNAME -q)" ]; then
    	echo "Container $CONTNAME already running!"
	exit
fi

if [ -n "$($SUDO docker ps -f name=$CONTNAME_PHPMYADMIN -q)" ]; then
        echo "Container $CONTNAME_PHPMYADMIN already running!"
        exit
fi


DOCKERID=$SUDO docker ps -aq --filter name=$CONTNAME

echo "Docker id for the $CONTNAME is : $DOCKERID"

DOCKERID_PHPMYADMIN=$SUDO docker ps -aq --filter name=$CONTNAME_PHPMYADMIN

echo "Docker id for the $CONTNAME_PHPMYADMIN is : $DOCKERID_PHPMYADMIN"

$SUDO docker run --name=$CONTNAME -e MYSQL_ROOT_PASSWORD=linux -e MYSQL_DATABASE=oai_db -d $IMGNAME:$RELEASE

$SUDO docker run --name=$CONTNAME_PHPMYADMIN -d --link $CONTNAME:db -p 8081:80 $IMGNAME_PHPMYADMIN
