#!/bin/bash
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
#   For more information about the Mosaic5G:
#       contact@mosaic-5g.io
#
#
################################################################################
# file          build_docker
# brief         Mosaic5G.io automated build and install tool 
# author        Mihai IDU

set -e
###################################
# colorful echos
###################################

black='\E[30m'
red='\E[31m'
green='\E[32m'
yellow='\E[33m'
blue='\E[1;34m'
magenta='\E[35m'
cyan='\E[36m'
white='\E[37m'
reset_color='\E[00m'
COLORIZE=1

cecho()  { 
    # Color-echo
    # arg1 = message
    # arg2 = color
    local default_msg="No Message."
    message=${1:-$default_msg}
    color=${2:-$green}
    [ "$COLORIZE" = "1" ] && message="$color$message$reset_color"
    echo -e "$message"
    return
}

echo_error()   { cecho "$*" $red          ;}
echo_fatal()   { cecho "$*" $red; exit -1 ;}
echo_warning() { cecho "$*" $yellow       ;}
echo_success() { cecho "$*" $green        ;}
echo_info()    { cecho "$*" $blue         ;}

#
################################
# Set the global variables
################################
# OAI-CN Docker
CONTNAME=oai-cn
IMGNAME=oai-cn-image
RELEASE=16.04

# MYSQL Docker
CONTNAME_MYSQL=oai-cn-mysql
IMGNAME_MYSQL=mysql
RELEASE_MYSQL=5.7

# phpmyadmin Docker
CONTNAME_PHPMYADMIN=oai-mysql-phpmyadmin
IMGNAME_PHPMYADMIN=phpmyadmin/phpmyadmin
RELEASE_PHPMYADMIN=latest

# FLEXRAN Docker
CONTNAME_FLEXRAN=flexran
IMGNAME_FLEXRAN=flexran-image
RELEASE_FLEXRAN=16.04

# LL-MEC Docker
CONTNAME_LL_MEC=ll-mec
IMGNAME_LL_MEC=ll-mec-image
RELEASE_LL_MEC=16.04

# Switch to the sudo user
SUDO=""
if [ -z "$(id -Gn|grep docker)" ] && [ "$(id -u)" != "0" ]; then
    SUDO="sudo"
fi

# ======
# Checking if the Docker images necesary are pulled from the public repo'
#
#
# =====
echo_info "======================================================================"
echo_info "Check if the local repository of Docker has the base docker images:"
echo_info " "
#Checking if the base docker image is pulled from the global repo'
if [ -n "$($SUDO docker images 2>&1 | grep $IMGNAME:$RELEASE )"]; then
        echo_info "The Docker Image $IMGNAME is already pull"
else
        $SUDO docker pull $IMGNAME:$RELEASE
fi
#Cheching if the base docker images are pulled from the global repo' for mysql and phpmyadmin
if [ -n "$($SUDO docker images 2>&1 | grep $IMGNAME_MYSQL:$RELEASE_MYSQL )"]; then
        echo_info "The Docker Image $IMGNAME_MYSQL is already pull"
else
        $SUDO docker pull $IMGNAME_MYSQL:$RELEASE_MYSQL
fi
if [ -n "$($SUDO docker images 2>&1 | grep $IMGNAME_PHPMYADMIN:$RELEASE_PHPMYADMIN )"]; then
        echo_info "The Docker Image $IMGNAME_PHPMYADMIN is already pull"
else
        $SUDO docker pull $IMGNAME_PHPMYADMIN
fi
#Checking if the base docker images are pulled from the global repo' 
if [ -n "$($SUDO docker images 2>&1 | grep $IMGNAME_FLEXRAN:$RELEASE_FLEXRAN )"]; then
        echo_info "The Docker Image $IMGNAME_FLEXRAN is already pull"
else
        $SUDO docker pull $IMGNAME_FLEXRAN:$RELEASE_FLEXRAN
fi
if [ -n "$($SUDO docker images 2>&1 | grep $IMGNAME_LL_MEC:$RELEASE_LL_MEC )"]; then
        echo_info "The Docker Image $IMGNAME_LL_MEC is already pull"
else
        $SUDO docker pull $IMGNAME_LL_MEC:$RELEASE_LL_MEC
fi
echo_info "======================================================================"
# =====
# Check where is the directory pushed
#and change to the specific directory 
#to use the Dockerfile and scripts 
# =====
DIR=$(pwd)
change_director_oai_cn(){
	cd $DIR	
	cd oai-cn
	BUILDDIR=$(pwd)
}
change_director_flexran(){
	cd $DIR
	cd flexran
	BUILDDIR_FLEXRAN=$(pwd)
}
change_director_ll_mec(){
	cd $DIR
	cd ll-mec
	BUILDDIR_LL_MEC=$(pwd)
}

usage() {
    	echo_info "usage: $(basename $0) [options]"
    	echo_info
#    	echo "-c|--containername 	         <name> "
#    	echo "-i|--imagename 			 <name> "
	echo_info "-C|--snap-core-network	Install OAI-CN from snap"
	echo_info "-F|--snap-flexran		Install FlexRAN realtime controller from snap"
	echo_info "-L|--snap-ll-mec-network	Install LL-MEC agent from snap"
}

print_info() {
    echo_info
    echo_info "use: $SUDO docker exec -it $CONTNAME <command> ... to run a command inside this container"
    echo_info
    echo_info "to remove the container use: $SUDO docker rm -f $CONTNAME"
    echo_info "to remove the related image use: $SUDO docker rmi $IMGNAME"
}
trap clean_up 1 2 3 4 9 15

#while [ $# -gt 0 ]; do
until [ -z "$1" ]; do
       case "$1" in
		-C|--snap-core-network)
			SNAP_OAI_CN=1 || usage
        	        echo_info "Choose to install OAI CN from snap"
			shift;;
		-F|--snap-flexran)
                        SNAP_FLEXRAN=1 || usage
                        echo_info "Choose to install FLEXRAN from snap"
			shift;;
		-L|--snap-ll-mec-network)
                        SNAP_LL_MEC=1 || usage
                        echo_info "Choose to install LL-MEC Agent from snap"
			shift;;
		-h|--help)
                       usage
                       shift;;
               	*)
                       usage
                       if [ "$1" != "-h" -o "$1" != "--help" -o "$1" != "-help" ]; then
                       echo_fatal "Unknown option $1"
               	       fi
                       break;;
       esac
done



# =====
# Check if the Container requested are already running based on Docker_NAME
# =====
#Checking if the OAI-CN Docker is running
echo_warning "======================================================================"
if [ -n "$($SUDO docker ps -f name=$CONTNAME -q)" ]; then
    	echo_warning "Container $CONTNAME already running!"
	CONT_OAI_CN=1
fi
#Checking if the FLEXRAN Docker is running
if [ -n "$($SUDO docker ps -f name=$CONTNAME_FLEXRAN -q)" ]; then
    	echo_warning "Container $CONTNAME_FLEXRAN already running!"
	CONT_FLEXRAN=1
fi
#Checking if the LL-MEC Docker is running
if [ -n "$($SUDO docker ps -f name=$CONTNAME_LL_MEC -q)" ]; then
    	echo_warning "Container $CONTNAME_LL_MEC already running!"
	CONT_LL_MEC=1
fi
echo_warning "======================================================================"
build_oai_cn(){
#Building the image according to chooise 
	$SUDO docker build -t $IMGNAME --force-rm=true --rm=true $BUILDDIR || clean_up

#Run the docker with specific parameters.
	$SUDO docker run \
    	--name=$CONTNAME \
    	-ti \
    	--tmpfs /run \
    	--tmpfs /run/lock \
    	--tmpfs /tmp \
    	--cap-add SYS_ADMIN \
    	--device=/dev/fuse \
    	--security-opt apparmor:unconfined \
    	--security-opt seccomp:unconfined \
    	-v /sys/fs/cgroup:/sys/fs/cgroup:ro \
    	-v /lib/modules:/lib/modules:ro \
    	-h ubuntu \
    	-d $IMGNAME || clean_up

#waiting for 60sec in order to the snapd process to start
	TIMEOUT=20
	SLEEP=3
	echo_info -n "Waiting $(($TIMEOUT*3)) seconds for Docker startup\n"
	while [ -z "$($SUDO docker exec $CONTNAME pgrep snapd)" ]; do
    	echo_info -n "."
    	sleep $SLEEP || clean_up
    	if [ "$TIMEOUT" -le "0" ]; then
        	echo " Timed out!"
        	clean_up
    	fi
    	TIMEOUT=$(($TIMEOUT-1))
	done

	$SUDO docker exec -it $CONTNAME /bin/bash -c "service snapd stop"
	$SUDO docker exec -it $CONTNAME /bin/bash -c "service snapd start"
	$SUDO docker exec -it $CONTNAME snap list
	$SUDO docker exec -it $CONTNAME /bin/bash -c "echo '127.0.0.1 ubuntu.openair4G.eur ubuntu hss' >> /etc/hosts"
	$SUDO docker exec -it $CONTNAME /bin/bash -c "echo '127.0.0.1 ubuntu.openair4G.eur ubuntu mme' >> /etc/hosts"
	$SUDO docker exec -it $CONTNAME /bin/bash -c "service snapd stop"
	$SUDO docker exec -it $CONTNAME /bin/bash -c "service snapd start"
	$SUDO docker exec -it $CONTNAME /bin/bash -c "service snapd stop"
	$SUDO docker exec -it $CONTNAME /bin/bash -c "service snapd start"
	$SUDO docker exec -it $CONTNAME /bin/bash -c "snap install oai-cn --channel=edge --devmode"
	$SUDO docker run --name=$CONTNAME_MYSQL -e MYSQL_ROOT_PASSWORD=linux -e MYSQL_DATABASE=oai_db -d $IMGNAME_MYSQL:$RELEASE_MYSQL
	$SUDO docker run --name=$CONTNAME_PHPMYADMIN -d --link $CONTNAME_MYSQL:db -p 8081:80 $IMGNAME_PHPMYADMIN

	echo_info "container $CONTNAME started with ..."
	echo_info ""
	echo_info "-------------------------------------------------------------"
	echo_info "     Listing the installed snaps installed on the Docker     "
	echo_info "-------------------------------------------------------------"
	echo_info ""
	$SUDO docker exec $CONTNAME snap list
	echo_info "-------------------------------------------------------------"
	echo_info "The following list of containers started:
		$CONTNAME , $CONTNAME_MYSQL and $CONTNAME_PHPMYADMIN"
}


build_flexran(){
#Building the image according to chooise 
        $SUDO docker build -t $IMGNAME_FLEXRAN --force-rm=true --rm=true $BUILDDIR_FLEXRAN || clean_up

#Run the docker with specific parameters.
        $SUDO docker run \
        --name=$CONTNAME_FLEXRAN \
        -ti \
        --tmpfs /run \
        --tmpfs /run/lock \
        --tmpfs /tmp \
        --cap-add SYS_ADMIN \
        --device=/dev/fuse \
        --security-opt apparmor:unconfined \
        --security-opt seccomp:unconfined \
        -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
        -v /lib/modules:/lib/modules:ro \
        -h ubuntu \
        -d $IMGNAME_FLEXRAN || clean_up

#waiting for 60sec in order to the snapd process to start
        TIMEOUT=20
        SLEEP=3
        echo_info -n "Waiting $(($TIMEOUT*3)) seconds for Docker startup\n"
        while [ -z "$($SUDO docker exec $CONTNAME_FLEXRAN pgrep snapd)" ]; do
        echo_info -n "."
        sleep $SLEEP || clean_up
        if [ "$TIMEOUT" -le "0" ]; then
                echo " Timed out!"
                clean_up
        fi
        TIMEOUT=$(($TIMEOUT-1))
        done

        $SUDO docker exec -it $CONTNAME_FLEXRAN /bin/bash -c "service snapd stop"
        $SUDO docker exec -it $CONTNAME_FLEXRAN /bin/bash -c "service snapd start"
        $SUDO docker exec -it $CONTNAME_FLEXRAN /bin/bash -c "snap install flexran --channel=edge --devmode"
        
        echo_info "container $CONTNAME_FLEXRAN started with ..."
        echo_info ""
        echo_info "-------------------------------------------------------------"
        echo_info "     Listing the installed snaps installed on the Docker     "
	echo_info "-------------------------------------------------------------"
	$SUDO docker exec $CONTNAME_FLEXRAN snap list
	echo_info "-------------------------------------------------------------"
}


build_ll_mec(){
#Building the image according to chooise 
        $SUDO docker build -t $IMGNAME_LL_MEC --force-rm=true --rm=true $BUILDDIR_LL_MEC || clean_up

#Run the docker with specific parameters.
        $SUDO docker run \
        --name=$CONTNAME_LL_MEC \
        -ti \
        --tmpfs /run \
        --tmpfs /run/lock \
        --tmpfs /tmp \
        --cap-add SYS_ADMIN \
        --device=/dev/fuse \
        --security-opt apparmor:unconfined \
        --security-opt seccomp:unconfined \
        -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
        -v /lib/modules:/lib/modules:ro \
        -h ubuntu \
        -d $IMGNAME_LL_MEC || clean_up

#waiting for 60sec in order to the snapd process to start
        TIMEOUT=20
        SLEEP=3
        echo_info -n "Waiting $(($TIMEOUT*3)) seconds for Docker startup\n"
        while [ -z "$($SUDO docker exec $CONTNAME_LL_MEC pgrep snapd)" ]; do
        echo_info -n "."
        sleep $SLEEP || clean_up
        if [ "$TIMEOUT" -le "0" ]; then
                echo " Timed out!"
                clean_up
        fi
        TIMEOUT=$(($TIMEOUT-1))
        done

        $SUDO docker exec -it $CONTNAME_LL_MEC /bin/bash -c "service snapd stop"
        $SUDO docker exec -it $CONTNAME_LL_MEC /bin/bash -c "service snapd start"
        $SUDO docker exec -it $CONTNAME_LL_MEC /bin/bash -c "snap install ll-mec --channel=edge --devmode"

        echo_info "container $CONTNAME_LL_MEC started with ..."
        echo_info ""
        echo_info "-------------------------------------------------------------"
        echo_info "     Listing the installed snaps installed on the Docker     "
        echo_info "-------------------------------------------------------------"
        $SUDO docker exec $CONTNAME_LL_MEC snap list
	echo_info "-------------------------------------------------------------"
}


if [ ("$SNAP_OAI_CN" = "1") && ("$CONT_OAI_CN" = "0") ] ; then
	change_director_oai_cn
	build_oai_cn
fi	

if [ ("$SNAP_FLEXRAN" = "1") && ("$CONT_FLEXRAN" = "0") ] ; then
        change_director_flexran
        build_flexran
fi
if [ ("$SNAP_LL_MEC" = "1") && ("$CONT_LL_MEC" = "0") ] ; then
        change_director_ll_mec
        build_ll_mec
fi
