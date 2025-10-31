import json
import os
import re

import pytest

from tests.conftest import RESULT_DIR
from tests.coords.lists import fixture_coordinates
from tests.utils.commons import coordinates_list
from tests.utils.models import QueryResult, RouteSummary
from tests.utils.payload_builders import motis_payload
from tests.utils.query_helpers import (
    extract_motis_route_summary,
    query_motis_by_payload,
)

COORDS = coordinates_list[:10]  # Limit for speed


@pytest.mark.parametrize("origin,destination", COORDS)  # Limit for speed
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
            pytest.skip("MOTIS returned an empty route summary")
        else:
            assert summary.duration_s > 0
            assert summary.distance_m > 0.0
            print(
                f"✅ Route found: Duration {summary.duration_s/3600:.1f}h, Distance {summary.distance_m/1000:.1f}km, Modes: {summary.modes}"
            )
    else:
        print("❌ No response data received from MOTIS")


@pytest.mark.parametrize(
    "origin,destination",
    COORDS,
)  # Limit for speed
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


# MOTIS Payload Parameters:
# origin: str,
# destination: str,
# time: str = TIME_BENCH,
# detailed_transfers: bool = False,


# --- Test multiple routes with different payloads --- #

# Let's assume you have a way to control snapshot updates, e.g., via a pytest custom option
# For this example, we'll just use an environment variable.
UPDATE_SNAPSHOTS = True


# PRINT
@pytest.mark.parametrize(
    "origin, destination",
    fixture_coordinates,
)
@pytest.mark.parametrize(
    "detailed_transfers", [True, False], ids=["detailed", "simple"]
)
@pytest.mark.parametrize("max_itineraries", [1, 2])
def test_motis_routes(
    origin, destination, detailed_transfers, max_itineraries, request
):
    """
    Test MOTIS routes with specific, isolated parameter variations.
    - `request` is a pytest fixture that gives us access to test context.
    - `ids` in parametrize gives nice names to the test cases in the output.
    """
    print(
        f"\n🧪 Testing route: {origin} -> {destination} (details: {detailed_transfers}, max: {max_itineraries})"
    )

    payload = motis_payload(
        origin,
        destination,
        detailed_transfers=detailed_transfers,
        maxItineraries=max_itineraries,
    )

    response: QueryResult = query_motis_by_payload(payload)

    assert response is not None, "No response received from MOTIS"
    assert (
        response.status_code == 200
    ), f"Unexpected status code: {response.status_code}, got {response.error_message}"

    if response.data is None:
        pytest.fail("No data received from MOTIS for route summary extraction")

    data = response.data.get("result", response.data)
    num_itineraries = len(data.get("itineraries", []))
    assert (
        num_itineraries <= max_itineraries + 1
    ), f"Number of itineraries {num_itineraries} exceeds max {max_itineraries}"

    # --- Controlled Side Effects (Snapshotting) ---
    # Construct a path for the golden file/snapshot
    # The 'request.node.name' gives a unique name for this specific test variation
    os.makedirs(RESULT_DIR + "motis_snapshots", exist_ok=True)
    snapshot_dir = os.path.join(RESULT_DIR, "motis_snapshots")
    node_name = request.node.name
    # Replace characters that are unfriendly to file systems
    sanitized_name = re.sub(r"[\[\]\s,]", "_", node_name).replace("__", "_")
    snapshot_file = os.path.join(snapshot_dir, f"{sanitized_name}.json")

    if UPDATE_SNAPSHOTS:
        os.makedirs(snapshot_dir, exist_ok=True)
        print(f"  -> Updating snapshot: {snapshot_file}")
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return  # No need to compare against the old file when we're updating it

    # Compare the new response with the saved snapshot
    try:
        with open(snapshot_file, "r", encoding="utf-8") as f:
            expected_data = json.load(f)
        # You can do a simple a == b, or use a more advanced library
        # like `pytest-snapshot` or `syrupy` which handle this automatically.
        assert data == expected_data
    except FileNotFoundError:
        pytest.fail(
            f"Snapshot file not found: {snapshot_file}. "
            "Run with UPDATE_SNAPSHOTS=1 to create it."
        )
