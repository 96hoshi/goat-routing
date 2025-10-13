from datetime import datetime, timedelta
from textwrap import dedent
from typing import Any, Dict

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.config import settings
from src.endpoints.v2.routing import router
from tests.coords.coords import mannheim_coordinates

from .benchmark_helpers import (
    generic_query_service,
    google_query_service,
    otp_query_service,
)

RESULT_DIR = "tests/results/"
RESPONSES_DIR = "tests/results/responses/"
IMAGES_DIR = "tests/results/images/"
# Benchmark time: tomorrow at 08:00 UTC
TIME_BENCH: str = (datetime.utcnow() + timedelta(days=1)).replace(
    hour=8, minute=0, second=0, microsecond=0
).isoformat() + "Z"

# FastAPI test client setup
app = FastAPI()
app.include_router(router)
client = TestClient(app)
# httpx client for external APIs
external_client = httpx.Client()

# Test coordinates list (latitude,longitude)
coordinates_list = mannheim_coordinates


# ----------- PAYLOAD BUILDERS ----------- #
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


def otp_payload(
    origin: str,
    destination: str,
    transport_modes: list[str] = ["TRANSIT", "WALK"],
    time: str = TIME_BENCH.split("T")[1].replace("Z", ""),
    date: str = TIME_BENCH.split("T")[0],
) -> dict[str, Any]:
    """Build minimal GraphQL payload for OTP CAR test."""

    def parse_coords(coord_str: str) -> dict[str, float]:
        lat, lon = map(float, coord_str.split(","))
        return {"lat": lat, "lon": lon}

    query = dedent(
        """
        query PlanTrip(
          $from: InputCoordinates!,
          $to: InputCoordinates!,
          $date: String!,
          $time: String!,
          $transportModes: [TransportMode!]!
        ) {
          plan(
            from: $from,
            to: $to,
            date: $date,
            time: $time,
            transportModes: $transportModes
          ) {
            date
            from { name lat lon }
            to { name lat lon }
            itineraries {
              startTime
              endTime
              duration
              legs {
                startTime
                endTime
                mode
                duration
                distance
                from { name lat lon }
                to { name lat lon }
                route {
                  shortName
                  longName
                }
              }
            }
          }
        }
        """
    )

    variables = {
        "from": parse_coords(origin),
        "to": parse_coords(destination),
        "transportModes": [{"mode": mode} for mode in transport_modes],
        "date": date,
        "time": time,
    }

    return {"query": query.strip(), "variables": variables}


# ----------- SERVICE CONFIGURATION ----------- #
SERVICES = [
    {
        "name": "motis",
        "client": client,
        "endpoint": "/ab-routing",
        "payload_builder": motis_payload,
        "query_func": generic_query_service,
        "method": "POST",
    },
    {
        "name": "google",
        "client": external_client,
        "endpoint": str(settings.GOOGLE_DIRECTIONS_URL),
        "payload_builder": google_payload,
        "query_func": google_query_service,
        "method": "GET",
    },
    # {
    #     "name": "valhalla",
    #     "client": external_client,
    #     "endpoint": str(settings.VALHALLA_URL),
    #     "payload_builder": valhalla_payload,
    #     "query_func": generic_query_service,
    #     "method": "POST",
    # },
    {
        "name": "otp",
        "client": external_client,
        "endpoint": str(settings.OPEN_TRIP_PLANNER_URL),
        "payload_builder": otp_payload,
        "query_func": otp_query_service,
        "method": "POST",
    },
]
