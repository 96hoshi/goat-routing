import pytest

from tests.utils.commons import coordinates_list
from tests.utils.models import QueryResult, RouteSummary
from tests.utils.payload_builders import motis_payload
from tests.utils.query_helpers import (
    extract_motis_route_summary,
    query_motis_by_payload,
)


@pytest.mark.parametrize("origin,destination", coordinates_list[:3])  # Limit for speed
def test_debug_response(origin, destination):
    """Debug test to see what MOTIS actually returns."""

    payload = motis_payload(
        origin, destination, detailed_transfers=True, maxItineraries=3
    )
    response: QueryResult = query_motis_by_payload(payload)

    if response and response.data:
        if "result" in response.data:
            result_data = response.data["result"]
            assert isinstance(result_data, dict)
            assert "itineraries" in result_data
            itineraries = result_data["itineraries"]
            assert isinstance(itineraries, list)
        else:
            pytest.fail(f"No 'result' key in MOTIS response data {response.data}")

        summary: RouteSummary = extract_motis_route_summary(response.data)

        if summary.is_empty():
            pytest.fail("MOTIS returned an empty route summary")
        else:
            assert summary.duration_s > 0
            assert summary.distance_m > 0.0
            print(
                f"✅ Route found: Duration {summary.duration_s/3600:.1f}h, Distance {summary.distance_m/1000:.1f}km, Modes: {summary.modes}"
            )
    else:
        print("❌ No response data received from MOTIS")


@pytest.mark.parametrize("origin,destination", coordinates_list[:3])  # Limit for speed
def test_individual_route(origin, destination):
    """Test individual routes (parametrized)."""
    print(f"\n🧪 Testing: {origin} -> {destination}")

    payload = motis_payload(origin, destination, detailed_transfers=True)
    response: QueryResult = query_motis_by_payload(payload)

    assert response is not None, "No response received from MOTIS"

    # if not response or not response.data:
    #     pytest.skip(f"MOTIS returned no data for {origin} -> {destination}")
    if response.data is None:
        pytest.fail("No data received from MOTIS for route summary extraction")
    summary: RouteSummary = extract_motis_route_summary(response.data)

    assert summary is not None, "No route summary extracted from MOTIS response"
    if not summary or summary.is_empty():
        pytest.skip(f"MOTIS found no route for {origin} -> {destination}")

    # Assertions for valid routes
    assert summary.duration_s > 0, f"Invalid duration: {summary.duration_s}"
    assert summary.distance_m > 0, f"Invalid distance: {summary.distance_m}"

    print(
        f"✅ Route found: {summary.duration_s/3600:.1f}h, {summary.distance_m/1000:.1f}km"
    )
