#!/bin/sh

# folder path
osmdata=$HOME"/osm/data/"
osmtemp=$HOME"/osm/data/temp/"

# download france data from geofabrik (pbf compression)
echo "Downloading france.osm.pbf from geofabrik.de"
curl "http://download.geofabrik.de/osm/europe/france.osm.pbf" -o $osmtemp"france.osm.pbf"
