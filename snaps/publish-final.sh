#!/bin/bash

ci_channel_tmp="/ci"

build_snap(){
    s=$1
    k=$2
    if [ -d $k ]; then
        cd $k
        version=$(grep -m1 version: snap/snapcraft.yaml | cut -f2 -d: | tr -d "'" | tr -d " ")
		
		sed -i "s/\(.*name:.*\)/name: $k/g" snap/snapcraft.yaml
		snap=$k"_"$version"_multi.snap"
		if [ ! -f $snap ]; then
			echo "You need to build the snap $snap firstly"
			exit 0
		fi

        echo "Validating $snap"
		# echo "snap=$snap, channel=$s, k=$k"
		# exit 0
		review-tools.snap-review $snap
        if [ $? -eq 0 ]; then
            echo ""
            echo "snapcraft upload $snap --release $s"
            echo ""
        else
            echo "$snap not validated, skipping "
        fi

        rev=$(snapcraft upload $snap --release $s | grep -m1 Revision | cut -f2 -d' ')
        echo "snapcraft release $k $rev $s"
        if [ -z "$rev" ]; then
            echo ""
            read -p "what is the revision of the snap to release (e.g. $rev)? " rev
        fi
        if [[ "$s" != *"$ci_channel_tmp"* ]]; then
			echo "snapcraft release $k $rev $s"
        	snapcraft release $k $rev $s
		fi
        cd ..
    fi
}
print_help() {
	echo "
	-s | --snap
		Name of the snap to build. Allowed options:
		all(default), oai-ue, oai-tracer, oai-hss, oai-spgwc, oai-spgwu, flexran, oai-ran
	-c | --channel)		
		channel name. Allowed options: stable, candidate, beta, edge(default)
	Example:
		./publish-final.sh -s ci-flexran -c edge/ci: publish the snap flexran
	"
}
function main() {
	until [ -z "$1" ]; do
		case "$1" in
		-s | --snap)
			SNAP_NAME=1
			# snap_name=$2
			declare -a snaps=$2
			shift 2
			;;
		-c | --channel)
			CHANNEL_NAME=1
			# channels=("$2")
			declare -a channels=$2
			shift 2
			;;
		*)
			print_help
			echo "Unknown option $1"
			break
			;;
		esac
	done

	
	
	if [ "$SNAP_NAME" != "1" ]; then
		declare -a snaps=("oai-ue" "oai-tracer" "oai-hss" "oai-spgwc" "oai-spgwu" "flexran" "oai-ran")
		# if [ "$snap_name" != "all" ]; then
		# 	snaps=$snap_name
		# fi
	fi
	if [ "$CHANNEL_NAME" != "1" ]; then
		# channels=("edge")
		declare -a channels=("edge")
	fi

	for s in "${channels[@]}"; do
		for k in "${snaps[@]}"; do
			build_snap $s $k
			# echo "snap=$k"
		done
	done

}
main "$@"
