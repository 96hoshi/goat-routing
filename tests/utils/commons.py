import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.config import settings
from src.endpoints.v2.routing import router
from tests.coords.coords import mannheim_coordinates
from tests.utils.payload_builders import google_payload, motis_payload, otp_payload

from .benchmark_helpers import (
    generic_query_service,
    google_query_service,
    otp_query_service,
)

# FastAPI test client setup
app = FastAPI()
app.include_router(router)
client = TestClient(app)

# httpx client for external APIs
external_client = httpx.Client()

# Test coordinates list (latitude,longitude)
coordinates_list = mannheim_coordinates

# ----------------- Define routing services configurations ----------------- #
SERVICES = [
    {
        "name": "motis",
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
        "label": "Google Maps",
        "color": "#ff7f0e",
        "marker": "x",
        "client": external_client,
        "endpoint": str(settings.GOOGLE_DIRECTIONS_URL),
        "payload_builder": google_payload,
        "query_func": google_query_service,
        "method": "GET",
    },
    {
        "name": "otp",
        "label": "OTP",
        "color": "#d62728",
        "marker": "^",
        "client": external_client,
        "endpoint": str(settings.OPEN_TRIP_PLANNER_URL),
        "payload_builder": otp_payload,
        "query_func": otp_query_service,
        "method": "POST",
    },
    # {
    #     "name": "valhalla",
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


# Helper function to get service by name
def get_service_by_name(name):
    """Get service configuration by name."""
    return next((s for s in SERVICES if s["name"] == name), None)


# Helper function to get AVAILABLE_SERVICES format for backward compatibility
def get_available_services():
    """Get services in AVAILABLE_SERVICES format for visualization scripts."""
    return {
        service["name"]: {
            "label": service["label"],
            "color": service["color"],
            "marker": service["marker"],
        }
        for service in SERVICES
    }
