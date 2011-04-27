#!/bin/sh

# folder path
osmdata=$HOME"/osm/data/"
osmtemp=$HOME"/osm/data/temp/"

mkdir -p $osmtemp

SCRIPT=`readlink -f $0`
SCRIPTPATH=`dirname $SCRIPT`

cp $SCRIPTPATH"/data/manhack.xls" $osmdata"manhack.xls"
cp $SCRIPTPATH"/data/fr_0.xml" $osmdata"fr_0.xml"