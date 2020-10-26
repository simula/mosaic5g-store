#!/bin/bash

declare -a snaps=("oai-ue" "oai-tracer" "oai-hss" "oai-spgwc" "oai-spgwu" "oai-mme" "flexran" "oai-ran" "ll-mec" "oai-cn")

declare -a snap_list=("all oai-ue oai-tracer oai-hss oai-spgwc oai-spgwu oai-mme flexran oai-ran oai-cn ll-mec")

declare -a snap_parts=("all gdb frontend tracer hss spgw spgwc spgwu mme flexran enb ll-mec ue")

SNAP_CLEAN_PART="frontend"

# to be removed later
declare -a snap_list=("all oai-ue oai-tracer oai-hss oai-spgwc oai-spgwu oai-mme flexran oai-ran oai-cn")

export SNAPCRAFT_BUILD_ENVIRONMENT=host

CURRENT_PATH=$PWD

function build_snap() {

    if [ "$SNAP_REMOVE" = "1" ]; then
        echo "Removing Snap $1 "
        remove_snap $1
    fi

    if [ -d $1 ]; then
        snap_remote=$1
        cd $snap_remote
        version=$(grep -m1 version: snap/snapcraft.yaml | cut -f2 -d: | tr -d "'" | tr -d " ")
        confinement=$(grep -m1 confinement: snap/snapcraft.yaml | cut -f2 -d: | tr -d " ")
        if [ "$confinement" = "classic" ]; then
            confinement="--$confinement --dangerous "
        elif [ "$confinement" = "devmode" ]; then
            confinement="--$confinement "
        else
            confinement=" "
        fi

        snap=$snap_remote"_"$version"_multi.snap"
        shift
        echo "----Building $snap V$version $confinement----"
        echo "snapcraft $@ && snapcraft"
        # echo "snap_remote=$snap_remote $@"
        # pwd
        # exit 0
        # docker rm --force snap-build-ubuntu1804
        docker run --name snap-build-ubuntu1804 \
            -v $STORE:$HOME/store \
            -w $HOME/store/snaps/$snap_remote \
            mosaic5gecosys/snapcraft:1.0 \
            snapcraft $@ && snapcraft
        # snapcraft $@
        # snapcraft
        # echo "sudo snap install ./$snap $confinement"
        # sudo snap install $snap $confinement
        now=$(date)
        echo "------$now------"
        cd -
    fi
    echo "build snap done"
}

function remove_snap() {
    sudo snap remove $1
}

function build_all_snaps() {
    for k in "${snaps[@]}"; do
        build_snap $k $1
    done

}

function test_snap() {

    if [ "$1" = "oai-ran" ]; then
        suff="enb-"
    fi

    conf=$($1.${suff}conf-get)
    echo "$1.${suff}conf-get:" $conf
    echo $CURRENT_PATH
    cp $conf .
    echo "$1.${suff}conf-set:" $(sudo $1.${suff}conf-set $CURRENT_PATH/$(basename $conf))
    conf=$($1.${suff}conf-get)
    echo "$1.${suff}conf-get:" $conf
    rm $conf
    echo "$1.${suff}conf-set:" $(sudo $1.${suff}conf-set $(basename $conf))
    echo "$1.${suff}conf-get:" $($1.${suff}conf-get)

}


function test_all_snaps() {

    for k in "${snaps[@]}"; do
        test_snap $k
    done

}

function list_include_item() {
    local list="$1"
    local item="$2"
    if [[ $list =~ (^|[[:space:]])"$item"($|[[:space:]]) ]]; then
        # yes, list include item
        result=0
    else
        result=1
    fi
    return $result
}

function print_help() {
    echo '
This program build M5G Snaps 
Options
-h
   print this help
-c | --clean-part
   rebuild part of a given snap. Valid options: all frontend(default) tracer hss spgw spgwc spgwu mme flexran enb ll-mec ue.
-n | --snap-name
   rebuild a specific snap define by a name. Valid options: "all" "oai-ue" "oai-tracer" "oai-hss" "oai-spgwc" "oai-spgwu" "oai-mme" "flexran" "oai-ran" "oai-cn".
-r | --remove-snap
   remove the snap, specified by its name (option -s) before installation
-t | --test-conf 
   test the internal conf command of the snap
Usage:
    ./build_snap -f  : rebuild the frontend of all the snaps
    ./build-final.sh -n flexran -c all: rebuild from scartch the oai-hss snap
'
}

function main() {
    until [ -z "$1" ]; do

        case "$1" in
        -c | --clean-part)
            list_include_item "$snap_parts" $2
            [[ $? -ne 0 ]] && echo "" && echo "[ERR] Snap part \"$2\" not recognized" && return $?
            echo "$1: will Rebuild part: $2"
            SNAP_CLEAN_PART=$2
            shift 2
            ;;
        -n | --snap-name)
            list_include_item "$snap_list" $2
            [[ $? -ne 0 ]] && echo "" && echo "[ERR] Snap name \"$2\" not recognized" && return $?
            echo "$1: Will build snap: $2"
            SNAP_NAME=$2
            shift 2
            ;;
        -r | --remove-snap)
            echo "$1: Will remove the snap before building and installation"
            SNAP_REMOVE=1
            shift
            ;;
        -t | --test-conf)
            echo "$1: Will test the conf command of the snap"
            SNAP_TEST=1
            shift
            ;;
        -h | --help)
            print_help
            exit 1
            ;;
        *)
            print_help
            if [ "$1" != "-h" -o "$1" != "--help" -o "$1" != "-help" ]; then
                echo "Unknown option $1"
                exit 1
            fi
            break
            ;;
        esac
    done

    if [ "$SNAP_CLEAN_PART" = "all" ]; then
        SNAP_ARGS=" clean "
    else
        SNAP_ARGS=" clean $SNAP_CLEAN_PART "
    fi

    #read -p "Are you sure you want to clean the snap (y/n)? " clean
    #list_include_item  "y yes YES Y" $clean
    #[[ $? -ne 0 ]] && echo "" && echo "Skipping the build" && return $?
    #SNAP_ARGS=" clean "

    if [ "$SNAP_TEST" = "1" ]; then
        if [ "$SNAP_NAME" = "all" ]; then
            test_all_snaps
        elif [ "$SNAP_NAME" != "" ]; then
            test_snap "$SNAP_NAME"

        else
            echo "Please specifiy a snap to test"
        fi
    else
        if [ "$SNAP_NAME" = "all" ]; then
            build_all_snaps "$SNAP_ARGS"
        elif [ "$SNAP_NAME" != " " ]; then
            #echo "build_snap $SNAP_NAME $SNAP_ARGS"
            build_snap "$SNAP_NAME" "$SNAP_ARGS"
        else
            echo "Please specifiy a snap to test"
        fi
    fi
}

main "$@"
