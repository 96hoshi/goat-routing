import pytest

from src.core.config import settings
from tests.utils.commons import client, coordinates_list
from tests.utils.models import QueryResult
from tests.utils.payload_builders import motis_payload
from tests.utils.query_helpers import query_motis_by_payload


@pytest.mark.parametrize("origin,destination", coordinates_list[:3])  # Limit for speed
def test_ab_routing_endpoint_basic(origin, destination):
    """Basic integration test: endpoint responds correctly."""
    payload = motis_payload(
        origin, destination, detailed_transfers=True, maxItineraries=3
    )
    response: QueryResult = query_motis_by_payload(payload)

    if response.status_code != 200:
        pytest.fail(
            f"Expected status 200, got {response.status_code}, payload: {response.data} "
        )

    data = response.data

    # Basic API contract validation
    assert isinstance(data, dict), "Response should be JSON object"
    assert "result" in data, "Response should contain 'result'"
    assert "itineraries" in data["result"], "Result should contain 'itineraries'"

    # Basic result validation
    result = data["result"]
    assert isinstance(result, dict), "Result should be object"
    assert len(result) > 0, "Result should not be empty"


def test_ab_routing_endpoint_error_handling():
    """Test endpoint handles invalid input gracefully."""

    invalid_payload = {"invalid": "payload"}
    response = client.post(settings.PLAN_ROUTE, json=invalid_payload)

    # Should return error status for invalid payload
    assert response.status_code in [
        400,
        422,
    ], f"Expected client error, got {response.status_code}"


def test_ab_routing_endpoint_availability():
    """Test that the endpoint exists and is available."""

    # Test with first coordinate pair
    origin, destination = coordinates_list[0]
    response = client.post(settings.PLAN_ROUTE, json=motis_payload(origin, destination))

    # Endpoint should exist (not 404)
    assert response.status_code != 404, "Endpoint should exist"

    # Should get either success or service error (not internal server error)
    assert response.status_code in [
        200,
        400,
        422,
        503,
    ], f"Unexpected status: {response.status_code}"
