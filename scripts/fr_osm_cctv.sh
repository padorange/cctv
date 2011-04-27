#!/bin/sh

# folder path
osmdata=$HOME"/osm/data/"
osmtemp=$HOME"/osm/data/temp/"

# create cctv surveillance data
osmosis --rb $osmtemp"france.osm.pbf" --tf accept-nodes "man_made=surveillance" --tf reject-ways --tf reject-relations --wx $osmtemp"frn.xml"
osmosis --rb $osmtemp"france.osm.pbf" --tf accept-ways "man_made=surveillance" --tf reject-relations --used-node --wx $osmtemp"frw.xml"
osmosis --rb $osmtemp"france.osm.pbf" --tf accept-relations "man_made=surveillance"  --used-way --used-node --wx $osmtemp"frr.xml"
osmosis --rx $osmtemp"frn.xml" --rx $osmtemp"frw.xml" --rx $osmtemp"frr.xml" --merge --merge --wx $osmdata"fr_surveillance.xml"

# run python preprocess
python extract_cctv.py