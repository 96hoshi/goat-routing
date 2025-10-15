import pytest

from src.core.config import settings
from tests.utils.benchmark_helpers import generic_query_service
from tests.utils.commons import coordinates_list, external_client
from tests.utils.models import ServiceMetrics
from tests.utils.payload_builders import valhalla_payload
from tests.utils.query_helpers import (
    query_valhalla,
)

COSTING_MODES = ["multimodal", "auto", "bicycle", "pedestrian", "bus"]


@pytest.mark.parametrize("origin,destination", coordinates_list[:3])
def test_valhalla_routing_basic(origin, destination):
    """Test basic Valhalla routing functionality."""
    result, response_size = query_valhalla(
        origin, destination, costing=COSTING_MODES[0]
    )

    assert (
        result is not None
    ), f"Valhalla returned no result for {origin} -> {destination}"
    assert (
        response_size is not None and response_size > 0
    ), "Response size should be greater than 0"
    assert "trip" in result, "Response should contain 'trip' key"
    assert "legs" in result["trip"], "Trip should contain 'legs'"


def test_valhalla_query_service_smoke_test():
    """
    A smoke test to ensure generic_query_service works for Valhalla.
    It performs one request and checks for a valid result.
    """

    origin, destination = coordinates_list[0]
    payload = valhalla_payload(origin, destination, costing=COSTING_MODES[0])

    # Use a real httpx client for external calls
    result: ServiceMetrics = generic_query_service(
        client=external_client,
        endpoint=str(settings.VALHALLA_URL),
        payload=payload,
        method="POST",
    )

    # Most important: Did the request actually succeed?
    assert result.status_code == 200, f"Request failed with status {result.status_code}"

    # Check that the metrics have plausible values
    assert result.time_ms > 0, "Time measurement should be positive"
    assert result.cpu_s is not None, "CPU measurement should return a value"
    assert result.mem_mb_delta is not None, "Memory measurement should return a value"
    assert result.response_size_bytes > 0, "Response should have content"

    # You can even check the response data itself
    assert "trip" in result.response_data, "Valhalla response should contain a 'trip'"


def test_valhalla_error_handling():
    """Test Valhalla error handling with invalid coordinates."""
    # Use invalid coordinates
    invalid_origin = "999,999"
    invalid_destination = "888,888"

    result, _ = query_valhalla(invalid_origin, invalid_destination)

    if result is not None:
        # If we get a result, it should still be well-formed
        assert isinstance(result, dict), "Result should be a dictionary"
        assert (
            "error" in result or "trip" in result
        ), "Result should contain 'error' or 'trip'"


@pytest.mark.integration
def test_valhalla_service_available():
    """Integration test to verify Valhalla service is available."""
    origin, destination = coordinates_list[0]

    result, response_size = query_valhalla(origin, destination)

    assert result is not None, (
        f"Valhalla service appears to be unavailable at {settings.VALHALLA_URL}. "
        "Make sure Valhalla is running and accessible."
    )
    assert (
        response_size is not None and response_size > 0
    ), "Should receive a non-empty response"
