#!/bin/sh

# folder path
osmdata=$HOME"/osm/data/"
osmtemp=$HOME"/osm/data/temp/"

mkdir -p $osmtemp

SCRIPT=`readlink -f $0`
SCRIPTPATH=`dirname $SCRIPT`

cd $SCRIPTPATH

./fr_osm_download.command

python extract_insee.py

./fr_osm_places.command

./fr_osm_cctv.command

python extract_manhack.py