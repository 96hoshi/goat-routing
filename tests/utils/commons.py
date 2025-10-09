from datetime import datetime, timedelta
from typing import Any, Dict

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.config import settings
from src.endpoints.v2.routing import router
from tests.coords.coords import mannheim_coordinates

from .benchmark_helpers import generic_query_service, google_query_service

# FastAPI test client setup
app = FastAPI()
app.include_router(router)
client = TestClient(app)

# httpx client for external APIs
external_client = httpx.Client()
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


SERVICES = [
    {
        "name": "motis",
        "client": client,
        "endpoint": "/ab-routing",
        "payload_builder": motis_payload,
        "query_func": generic_query_service,  # This one is standard
        "method": "POST",
    },
    {
        "name": "google",
        "client": external_client,
        "endpoint": str(settings.GOOGLE_DIRECTIONS_URL),
        "payload_builder": google_payload,
        "query_func": google_query_service,  # Use the specialized wrapper
        "method": "GET",
    },
    {
        "name": "valhalla",
        "client": external_client,
        "endpoint": str(settings.VALHALLA_URL),
        "payload_builder": valhalla_payload,
        "query_func": generic_query_service,  # This one is also standard
        "method": "POST",
    },
]
