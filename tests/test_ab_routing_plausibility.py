import pytest

from tests.utils.commons import coordinates_list
from tests.utils.models import QueryResult, RouteSummary
from tests.utils.query_helpers import (
    extract_google_route_summary,
    extract_motis_route_summary,
    # extract_valhalla_route_summary,
    query_google,
    query_motis,
)

ROUTING_SERVICES = {
    "motis": (query_motis, extract_motis_route_summary),
    "google": (query_google, extract_google_route_summary),
    # "valhalla": (query_valhalla, extract_valhalla_route_summary),
}

PLAUSIBILITY_BOUNDS = {
    "MIN_DURATION_S": 60,
    "MAX_DURATION_S": 12 * 3600,
    "MIN_DISTANCE_M": 50,
    "MAX_DISTANCE_M": 2_000_000,
    "LONG_DISTANCE_THRESHOLD_M": 200_000,
    "MAX_LONG_DISTANCE_DURATION_S": 16 * 3600,
}

COMPARISON_THRESHOLDS = {
    "MAX_DURATION_RATIO": 4.0,
    "MAX_DISTANCE_RATIO": 3.0,
    "MAX_ABSOLUTE_DURATION_DIFF_S": 2
    * 3600,  # Don't allow more than a 2-hour absolute difference
}
# --- Helper Functions for Readability ---


def assert_plausible_route_summary(summary: RouteSummary, service_name: str):
    """Contains all plausibility assertions for a given route summary."""
    assert (
        summary.duration_s > 0
    ), f"[{service_name}] Invalid duration: {summary.duration_s}"
    assert (
        summary.distance_m > 0
    ), f"[{service_name}] Invalid distance: {summary.distance_m}"
    assert len(summary.modes) > 0, f"[{service_name}] No transport modes found"

    min_dur, max_dur = (
        PLAUSIBILITY_BOUNDS["MIN_DURATION_S"],
        PLAUSIBILITY_BOUNDS["MAX_DURATION_S"],
    )
    assert (
        min_dur <= summary.duration_s <= max_dur
    ), f"[{service_name}] Duration {summary.duration_s/3600:.1f}h is outside plausible range [{min_dur/60}min, {max_dur/3600}h]"

    min_dist, max_dist = (
        PLAUSIBILITY_BOUNDS["MIN_DISTANCE_M"],
        PLAUSIBILITY_BOUNDS["MAX_DISTANCE_M"],
    )
    assert (
        min_dist <= summary.distance_m <= max_dist
    ), f"[{service_name}] Distance {summary.distance_m/1000:.1f}km is outside plausible range [{min_dist}m, {max_dist/1000}km]"

    if summary.distance_m > PLAUSIBILITY_BOUNDS["LONG_DISTANCE_THRESHOLD_M"]:
        max_long_dur = PLAUSIBILITY_BOUNDS["MAX_LONG_DISTANCE_DURATION_S"]
        assert (
            summary.duration_s <= max_long_dur
        ), f"[{service_name}] Long-distance route duration {summary.duration_s/3600:.1f}h exceeds max of {max_long_dur/3600}h"


def generate_id(param):
    """Creates a descriptive ID for pytest parametrization."""
    if (
        isinstance(param, tuple)
        and len(param) == 2
        and isinstance(param[0], (int, float))
    ):
        return f"Coord({param[0]:.2f},{param[1]:.2f})"
    return str(param)


# --- The Main Test Function ---


@pytest.mark.integration  # This should definitely be marked as an integration test
@pytest.mark.parametrize("origin,destination", coordinates_list[:5])
def test_cross_service_consistency(origin, destination):
    """
    Compares results between multiple routing services for the same route
    to ensure their results are consistent and coherent.
    """
    results: dict[str, RouteSummary] = {}

    # 1. Collect results from all services
    for name, (query_fn, summary_fn) in ROUTING_SERVICES.items():
        try:
            response = query_fn(origin, destination)
            if response and response.data:
                summary = summary_fn(response.data)
                if summary and not summary.is_empty():
                    results[name] = summary
        except Exception as e:
            # Issue a formal pytest warning instead of just printing.
            pytest.fail(f"Service '{name}' failed during query: {e}")

    # 2. Skip test if not enough data is available for a comparison
    if len(results) < 2:
        pytest.skip(
            f"Could not get results from at least two services for {origin} -> {destination}"
        )

    # 3. Perform the comparison assertions
    print(f"\nComparing {len(results)} services for route: {origin} -> {destination}")
    for name, summary in results.items():
        print(
            f"  - {name}: {summary.duration_s/3600:.1f}h, {summary.distance_m/1000:.1f}km"
        )

    durations = [r.duration_s for r in results.values()]
    distances = [r.distance_m for r in results.values()]

    min_duration, max_duration = min(durations), max(durations)
    min_distance, max_distance = min(distances), max(distances)

    # Check Ratios (good for relative differences)
    duration_ratio = max_duration / min_duration if min_duration > 0 else float("inf")
    distance_ratio = max_distance / min_distance if min_distance > 0 else float("inf")

    assert (
        duration_ratio <= COMPARISON_THRESHOLDS["MAX_DURATION_RATIO"]
    ), f"Duration variance ratio too high: {duration_ratio:.2f}x ({min_duration/60:.0f}m vs {max_duration/60:.0f}m)"

    assert (
        distance_ratio <= COMPARISON_THRESHOLDS["MAX_DISTANCE_RATIO"]
    ), f"Distance variance ratio too high: {distance_ratio:.2f}x ({min_distance/1000:.1f}km vs {max_distance/1000:.1f}km)"

    # Check Absolute Difference (good for catching large-scale deviations)
    duration_abs_diff = max_duration - min_duration
    assert (
        duration_abs_diff <= COMPARISON_THRESHOLDS["MAX_ABSOLUTE_DURATION_DIFF_S"]
    ), f"Absolute duration difference is too high: {duration_abs_diff/3600:.1f} hours"


@pytest.mark.parametrize(
    "origin,destination",
    coordinates_list[:5],
    ids=[f"{generate_id(o)}_to_{generate_id(d)}" for o, d in coordinates_list[:5]],
)
@pytest.mark.parametrize(
    "service_name,service_fns",
    ROUTING_SERVICES.items(),
    ids=list(ROUTING_SERVICES.keys()),
)
def test_route_plausibility(origin, destination, service_name, service_fns):
    """Check that each service returns plausible results for a given route."""
    query_fn, summary_fn = service_fns

    response: QueryResult = query_fn(origin, destination)
    if not response or not response.data:
        pytest.skip(f"{service_name} returned no data for {origin}->{destination}")

    result: RouteSummary = summary_fn(response.data)
    if not result:
        pytest.skip(
            f"{service_name} could not create a summary for {origin}->{destination}"
        )

    if result.is_empty():
        pytest.skip(f"{service_name} found no route between {origin} and {destination}")

    # Single call to the validation helper
    assert_plausible_route_summary(result, service_name)
