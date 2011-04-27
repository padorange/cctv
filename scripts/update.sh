#!/bin/sh

# folder path
osmdata=$HOME"/osm/data/"
osmtemp=$HOME"/osm/data/temp/"

mkdir -p $osmtemp

SCRIPT=`readlink -f $0`
SCRIPTPATH=`dirname $SCRIPT`

cd $SCRIPTPATH

./fr_osm_download.sh
./fr_osm_cctv.sh