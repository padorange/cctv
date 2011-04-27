#!/bin/sh

# folder path
osmdata=$HOME"/osm/data/"
osmtemp=$HOME"/osm/data/temp/"

# create admin boundary data
#osmosis --rb $osmtemp"france.osm.pbf" --tf accept-ways "boundary=administrative" --tf reject-relations --used-node --wx $osmtemp"fr_admin1.xml"
#osmosis --rb $osmtemp"france.osm.pbf" --tf accept-relations "boundary=administrative"  --used-way --used-node --wx $osmtemp"fr_admin2.xml"
#osmosis --rx $osmtemp"fr_admin1.xml" --rx $osmtemp"fr_admin2.xml" --merge --wx $osmdata"fr_admin.xml"

# create place data
osmosis --rb $osmtemp"france.osm.pbf" --tf accept-nodes "place=city,town,village,hamlet" --tf reject-ways --tf reject-relations --wx $osmtemp"fr_place0.xml"
osmosis --rb $osmtemp"france.osm.pbf" --tf accept-ways "place=city,town,village,hamlet" --tf reject-relations --used-node --wx $osmtemp"fr_place1.xml"
osmosis --rb $osmtemp"france.osm.pbf" --tf accept-relations "place=city,town,village,hamlet"  --used-way --used-node --wx $osmtemp"fr_place2.xml"
osmosis --rx $osmtemp"fr_place0.xml" --rx $osmtemp"fr_place1.xml" --rx $osmtemp"fr_place2.xml" --merge --merge --wx $osmdata"fr_places.xml"

python extract_admin.py -f$osmdata"fr_places.xml" -l8
python insee2sql.py