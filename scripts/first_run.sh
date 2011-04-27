#!/bin/sh

# folder path
osmdata=$HOME"/osm/data/"
osmtemp=$HOME"/osm/data/temp/"

mkdir -p $osmtemp

SCRIPT=`readlink -f $0`
SCRIPTPATH=`dirname $SCRIPT`

cd $SCRIPTPATH

./fr_osm_download.sh
python extract_insee.py
./fr_osm_places.sh
./fr_osm_cctv.sh
python extract_manhack.py