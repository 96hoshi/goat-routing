#!/bin/sh
set -e

TARGET="linux-amd64"
GEODATA_DIR="geodata"

echo "Retrieving Motis..."
wget https://github.com/motis-project/motis/releases/latest/download/motis-${TARGET}.tar.bz2
tar xf motis-${TARGET}.tar.bz2
rm motis-${TARGET}.tar.bz2

MAP_FILE=
for f in ${GEODATA_DIR}/*.pbf; do
    [ -f "$f" ] || continue
    MAP_FILE="$f"
    break
done

TRANSFERS_FILE=
for f in ${GEODATA_DIR}/*.zip; do
    [ -f "$f" ] || continue
    TRANSFERS_FILE="$f"
    break
done

echo "Using local map file: $MAP_FILE"
echo "Using transfer map file: $TRANSFERS_FILE"

./motis config ${MAP_FILE} ${TRANSFERS_FILE}
./motis import

# Run the server
./motis server -d data/


# Maachen
# set -e

# TARGET="linux-amd64"

# MAP_FILE="aachen.osm.pbf"
# TRANSFERS_FILE="AVV_GTFS_Masten_mit_SPNV.zip"
# MAP_LINK="https://github.com/motis-project/test-data/raw/aachen/${MAP_FILE}"
# TRANSFERS_LINK="https://opendata.avv.de/current_GTFS/${TRANSFERS_FILE}"

# echo "Retrieving Motis..."
# wget https://github.com/motis-project/motis/releases/latest/download/motis-${TARGET}.tar.bz2
# tar xf motis-${TARGET}.tar.bz2
# rm motis-${TARGET}.tar.bz2

# if [ ! -f "data/config.yml" ]; then
#   echo "First run: setting up environment..."

#   wget ${MAP_LINK}
#   wget ${TRANSFERS_LINK}

#   ./motis config ${MAP_FILE} ${TRANSFERS_FILE}
#   ./motis import

# else
#   echo "Data folder exists, skipping setup..."
# fi

# # always run the server
# ./motis server -d data/

