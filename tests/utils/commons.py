import csv
import os
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.config import settings
from src.endpoints.v2.routing import router
from tests.coords.coords import mannheim_coordinates
from tests.utils.benchmark_helpers import (
    benchmark_http_requests,
)

# FastAPI test client setup
app = FastAPI()
app.include_router(router)
client = TestClient(app)
coordinates_list = mannheim_coordinates

# Benchmark result file
RESULT_FILE = "benchmark_results.csv"
RESULT_HEADERS = []
RESULT_DIR = "tests/results/"
RESPONSES_DIR = "tests/results/responses/"
IMAGES_DIR = "tests/results/images/"

# Benchmark time: tomorrow at 08:00 UTC
TIME_BENCH: str = (datetime.utcnow() + timedelta(days=1)).replace(
    hour=8, minute=0, second=0, microsecond=0
).isoformat() + "Z"


# Motis payload builder
def motis_payload(
    origin: str,
    destination: str,
    time: str = TIME_BENCH,
    detailed_transfers: str = "false",
    **kwargs,
) -> Dict[str, str]:
    """
    Build a payload for the Motis routing API.
    """

    return {
        "fromPlace": origin,
        "toPlace": destination,
        "time": time,
        "detailedTransfers": detailed_transfers,
        "maxItineraries": "6",  # Request up to 6 itineraries all is default
        **kwargs,
    }


FROM, TO = coordinates_list[5]
MOTIS_PAYLOAD_BENCH = motis_payload(FROM, TO)


def google_payload(
    origin: str,
    destination: str,
    mode: str = "transit",
    time: str = TIME_BENCH,
    api_key: str = settings.GOOGLE_API_KEY,
) -> Dict[str, Any]:
    """Build payload for Google Directions API."""
    dt = datetime.fromisoformat(time.replace("Z", "+00:00"))
    departure_timestamp = int(dt.timestamp())
    return {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "departure_time": departure_timestamp,
        "key": api_key,
        "alternatives": "true",  # default is 1
    }


def valhalla_payload(
    origin: str, destination: str, costing: str = "multimodal", **kwargs
) -> Dict[str, Any]:
    """Build payload for Valhalla routing API.
    costing values: "multimodal", "auto", "bicycle", "pedestrian", "bus"
    """
    # Parse coordinates from "lat,lon" format
    origin_lat, origin_lon = map(float, origin.split(","))
    dest_lat, dest_lon = map(float, destination.split(","))

    return {
        "locations": [
            {"lat": origin_lat, "lon": origin_lon},
            {"lat": dest_lat, "lon": dest_lon},
        ],
        "costing": costing,
        "directions_options": {"units": "kilometers"},
        **kwargs,
    }


def write_result(
    row: Dict[str, Any], filename: str = RESULT_FILE, headers=None
) -> None:
    """
    Write a single result to a CSV file in the results directory.
    """
    # Ensure the results directory exists
    os.makedirs(RESULT_DIR, exist_ok=True)
    # Always write to the results directory
    filepath = os.path.join(RESULT_DIR, os.path.basename(filename))
    if headers is None:
        headers = list(row.keys())
    file_exists = os.path.isfile(filepath)
    with open(filepath, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def write_response(row, filename: str, headers=None) -> None:
    """
    Write a single route to a JSON file in the routes directory.
    """
    # Ensure the responses directory exists
    os.makedirs(RESPONSES_DIR, exist_ok=True)
    filepath = os.path.join(RESPONSES_DIR, filename)
    if headers is None:
        headers = list(row.keys())
    with open(filepath, "w") as f:
        import json

        json.dump(row, f, indent=2)


SERVICES = [
    {
        "name": "motis",
        "endpoint": "/ab-routing",
        "payload_builder": motis_payload,
        "benchmark_func": benchmark_http_requests,
        "client": client,
    },
    {
        "name": "google",
        "endpoint": str(settings.GOOGLE_DIRECTIONS_URL),
        "payload_builder": google_payload,
        "benchmark_func": benchmark_http_requests,
        "client": None,
    },
    {
        "name": "valhalla",
        "endpoint": str(settings.VALHALLA_URL),
        "payload_builder": valhalla_payload,
        "benchmark_func": benchmark_http_requests,
        "client": None,
    },  # Add more services here...
]
