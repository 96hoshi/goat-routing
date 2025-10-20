import os

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.config import settings
from src.endpoints.v2.routing import router
from tests.coords.lists import (
    aachen_coordinates,
    germany_coordinates,
    mannheim_coordinates,
)
from tests.utils.payload_builders import google_payload, motis_payload

from .benchmark_helpers import (
    generic_query_service,
    google_query_service,
)

# Environment-based coordinate selection
COORDINATE_MAP = {
    "germany": germany_coordinates,
    "mannheim": mannheim_coordinates,
    "aachen": aachen_coordinates,
    "test": mannheim_coordinates[:3],
}


# FastAPI test client setup
app = FastAPI()
app.include_router(router)
client = TestClient(app)

# httpx client for external APIs
external_client = httpx.Client()


def get_test_coordinates():
    """Get coordinates based on environment setting."""
    coord_type = os.getenv("TEST_COORDS", "germany")

    if coord_type not in COORDINATE_MAP:
        print(f"⚠️ Unknown TEST_COORDS '{coord_type}', using 'germany'")
        coord_type = "germany"

    coords = COORDINATE_MAP[coord_type]
    return coords


coordinates_list = get_test_coordinates()

# ----------------- Define routing services configurations ----------------- #
SERVICES = [
    {
        "name": "motis",
        "type": "container",
        "label": "MOTIS",
        "color": "#1f77b4",
        "marker": "o",
        "client": client,
        "endpoint": str(settings.MOTIS_ROUTE),
        "payload_builder": motis_payload,
        "query_func": generic_query_service,
        "method": "POST",
    },
    {
        "name": "google",
        "type": "api",
        "label": "Google Maps",
        "color": "#ff7f0e",
        "marker": "x",
        "client": external_client,
        "endpoint": str(settings.GOOGLE_DIRECTIONS_URL),
        "payload_builder": google_payload,
        "query_func": google_query_service,
        "method": "GET",
    },
    # {
    #     "name": "otp",
    #     "type": "api",
    #     "label": "OTP",
    #     "color": "#d62728",
    #     "marker": "^",
    #     "client": external_client,
    #     "endpoint": str(settings.OPEN_TRIP_PLANNER_URL),
    #     "payload_builder": otp_payload,
    #     "query_func": otp_query_service,
    #     "method": "POST",
    # },
    # {
    #     "name": "valhalla",
    #     "type": "container",
    #     "label": "Valhalla",
    #     "color": "#2ca02c",
    #     "marker": "s",
    #     "client": external_client,
    #     "endpoint": str(settings.VALHALLA_URL),
    #     "payload_builder": valhalla_payload,
    #     "query_func": generic_query_service,
    #     "method": "POST",
    # }
]


def get_service_by_name(name):
    """Get service configuration by name."""
    return next((s for s in SERVICES if s["name"] == name), None)


def get_services_by_type(service_type: str):
    return [s for s in SERVICES if s["type"] == service_type]


def get_service_config():
    return {
        service["name"]: {
            "label": service["label"],
            "color": service["color"],
            "marker": service["marker"],
        }
        for service in SERVICES
    }
