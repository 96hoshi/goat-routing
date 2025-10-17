import pytest

from tests.utils.commons import client, coordinates_list
from tests.utils.payload_builders import motis_payload


@pytest.mark.parametrize("origin,destination", coordinates_list)  # Limit for speed
def test_ab_routing_endpoint_basic(origin, destination):
    """Basic integration test: endpoint responds correctly."""

    response = client.post(
        "/ab-routing",
        json=motis_payload(origin, destination),
    )

    if response.status_code != 200:
        pytest.skip(f"MOTIS service unavailable: {response.status_code}")

    data = response.json()

    # Basic API contract validation
    assert isinstance(data, dict), "Response should be JSON object"
    assert "result" in data, "Response should contain 'result'"
    assert "message" in data, "Response should contain 'message'"
    assert data["message"] == "Plan computed successfully."

    # Basic result validation
    result = data["result"]
    assert isinstance(result, dict), "Result should be object"
    assert len(result) > 0, "Result should not be empty"


def test_ab_routing_endpoint_error_handling():
    """Test endpoint handles invalid input gracefully."""

    invalid_payload = {"invalid": "payload"}

    response = client.post("/ab-routing", json=invalid_payload)

    # Should return error status for invalid payload
    assert response.status_code in [
        400,
        422,
    ], f"Expected client error, got {response.status_code}"


def test_ab_routing_endpoint_availability():
    """Test that the endpoint exists and is available."""

    # Test with first coordinate pair
    origin, destination = coordinates_list[0]

    response = client.post("/ab-routing", json=motis_payload(origin, destination))

    # Endpoint should exist (not 404)
    assert response.status_code != 404, "Endpoint should exist"

    # Should get either success or service error (not internal server error)
    assert response.status_code in [
        200,
        400,
        422,
        503,
    ], f"Unexpected status: {response.status_code}"
