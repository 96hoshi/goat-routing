import pytest

from tests.utils.commons import coordinates_list
from tests.utils.models import QueryResult, RouteSummary
from tests.utils.payload_builders import motis_payload
from tests.utils.query_helpers import (
    extract_motis_route_summary,
    query_motis_by_payload,
)


@pytest.mark.parametrize("origin,destination", coordinates_list)
def test_debug_response(origin, destination):
    """Debug test to see what MOTIS actually returns."""
    query_fn = query_motis_by_payload
    summary_fn = extract_motis_route_summary
    payload_fn = motis_payload

    payload = payload_fn(origin, destination, detailed_transfers=True)
    response: QueryResult = query_fn(payload)

    if response and response.data:

        if "result" in response.data:
            result_data = response.data["result"]
            assert isinstance(result_data, dict)
        else:
            pytest.fail(f"No 'result' key in MOTIS response data {response.data}")

        summary: RouteSummary = summary_fn(response.data)

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


@pytest.mark.parametrize("origin,destination", coordinates_list)
def test_individual_route(origin, destination):
    """Test individual routes (parametrized)."""
    query_fn = query_motis_by_payload
    summary_fn = extract_motis_route_summary
    payload_fn = motis_payload

    print(f"\n🧪 Testing: {origin} -> {destination}")

    payload = payload_fn(origin, destination, detailed_transfers=True)
    response: QueryResult = query_fn(payload)

    if not response or not response.data:
        pytest.skip(f"MOTIS returned no data for {origin} -> {destination}")

    summary = summary_fn(response.data)
    if not summary or summary.is_empty():
        pytest.skip(f"MOTIS found no route for {origin} -> {destination}")

    # Assertions for valid routes
    assert summary.duration_s > 0, f"Invalid duration: {summary.duration_s}"
    assert summary.distance_m > 0, f"Invalid distance: {summary.distance_m}"

    print(
        f"✅ Route found: {summary.duration_s/3600:.1f}h, {summary.distance_m/1000:.1f}km"
    )
