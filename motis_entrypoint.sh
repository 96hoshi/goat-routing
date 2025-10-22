#!/bin/sh
set -e

# --- Configuration ---
TARGET="linux-amd64"
GEODATA_DIR="geodata"
MOTIS_BINARY="./motis"
DATA_DIR="data"


# --- Functions ---

# Prints usage instructions and exits.
usage() {
  echo "Usage: $0 [mode]"
  echo ""
  echo "Modes:"
  echo "  local                - Use first .pbf and .zip found in the '${GEODATA_DIR}' directory."
  echo "  aachen               - Automatically download and use Aachen test data (will be stored in '${GEODATA_DIR}')."
  echo "  custom <map> <gtfs>  - Use a specific .pbf map and .zip GTFS file."
  echo "                         (Files are looked for in '.' and then in '${GEODATA_DIR}/')"
  echo ""
  echo "Example for custom mode:"
  echo "  # Assumes 'berlin.pbf' and 'transit.zip' are in the '${GEODATA_DIR}' directory"
  echo "  $0 custom berlin.pbf transit.zip"
  exit 1
}

# Downloads and extracts the Motis binary if it doesn't already exist.
download_motis() {
  if [ ! -f "${MOTIS_BINARY}" ]; then
    echo ">> Motis binary not found. Retrieving..."
    wget "https://github.com/motis-project/motis/releases/latest/download/motis-${TARGET}.tar.bz2"
    tar xf "motis-${TARGET}.tar.bz2"
    rm "motis-${TARGET}.tar.bz2"
    echo ">> Motis downloaded."
  else
    echo ">> Motis binary already exists."
  fi
}


# --- Main Script Logic ---

# Check for mode argument
MODE=$1
if [ -z "$MODE" ]; then
  echo "Error: No mode specified."
  usage
fi

# Create geodata directory if it doesn't exist
mkdir -p "${GEODATA_DIR}"

# Download Motis if needed, regardless of mode
download_motis

# Initialize file variables
MAP_FILE=
GTFS_FILE=

# Shift past the mode argument to make it easier to access other args
shift

# Determine which files to use based on the selected mode
case $MODE in
  local)
    echo ">> Running in 'local' mode. Searching for files in '${GEODATA_DIR}'..."
    for f in "${GEODATA_DIR}"/*.pbf; do [ -f "$f" ] && MAP_FILE="$f" && break; done
    for f in "${GEODATA_DIR}"/*.zip; do [ -f "$f" ] && GTFS_FILE="$f" && break; done

    if [ -z "$MAP_FILE" ] || [ ! -e "$MAP_FILE" ]; then
      echo "Error: No .pbf file found in '${GEODATA_DIR}' directory." >&2; exit 1
    fi
    if [ -z "$GTFS_FILE" ] || [ ! -e "$GTFS_FILE" ]; then
      echo "Error: No .zip file found in '${GEODATA_DIR}' directory." >&2; exit 1
    fi
    ;;

  aachen)
    echo ">> Running in 'aachen' mode. Using public Aachen test data."
    MAP_FILENAME="aachen.osm.pbf"
    GTFS_FILENAME="AVV_GTFS_Masten_mit_SPNV.zip"
    MAP_FILE="${GEODATA_DIR}/${MAP_FILENAME}"
    GTFS_FILE="${GEODATA_DIR}/${GTFS_FILENAME}"
    
    if [ ! -f "$MAP_FILE" ]; then
      echo ">> Downloading Aachen map data to '${MAP_FILE}'..."
      wget "https://github.com/motis-project/test-data/raw/aachen/${MAP_FILENAME}" -O "${MAP_FILE}"
    fi
    if [ ! -f "$GTFS_FILE" ]; then
      echo ">> Downloading Aachen GTFS data to '${GTFS_FILE}'..."
      wget "https://opendata.avv.de/current_GTFS/${GTFS_FILENAME}" -O "${GTFS_FILE}"
    fi
    ;;

  custom)
    echo ">> Running in 'custom' mode."
    if [ -z "$1" ] || [ -z "$2" ]; then
      echo "Error: 'custom' mode requires <map_file.pbf> and <gtfs_file.zip> arguments."
      usage
    fi
    MAP_ARG=$1
    GTFS_ARG=$2

    # Find the map file, checking current dir then geodata dir
    if [ -f "$MAP_ARG" ]; then
      MAP_FILE="$MAP_ARG"
    elif [ -f "${GEODATA_DIR}/$MAP_ARG" ]; then
      MAP_FILE="${GEODATA_DIR}/$MAP_ARG"
    else
      echo "Error: Map file not found in '.' or in '${GEODATA_DIR}/': $MAP_ARG" >&2; exit 1
    fi

    # Find the GTFS file, checking current dir then geodata dir
    if [ -f "$GTFS_ARG" ]; then
      GTFS_FILE="$GTFS_ARG"
    elif [ -f "${GEODATA_DIR}/$GTFS_ARG" ]; then
      GTFS_FILE="${GEODATA_DIR}/$GTFS_ARG"
    else
      echo "Error: GTFS file not found in '.' or in '${GEODATA_DIR}/': $GTFS_ARG" >&2; exit 1
    fi
    ;;

  *)
    echo "Error: Unknown mode '$MODE'."
    usage
    ;;
esac

echo "----------------------------------------"
echo "Using Map File:   $MAP_FILE"
echo "Using GTFS File:  $GTFS_FILE"
echo "----------------------------------------"

# We check for the final import artifact. If it exists, we can skip the slow import.
echo ">> Generating configuration..."
"${MOTIS_BINARY}" config "${MAP_FILE}" "${GTFS_FILE}"

if [ ! -f "${DATA_DIR}/schedule.raw" ]; then
  echo ">> No existing dataset found in '${DATA_DIR}/'. Starting import (this may take a while)..."
  "${MOTIS_BINARY}" import
  echo ">> Import finished."
else
  echo ">> Existing dataset found in '${DATA_DIR}/'. Skipping import."
fi

# Always run the server
echo ">> Starting Motis server..."
"${MOTIS_BINARY}" server -d "${DATA_DIR}/"