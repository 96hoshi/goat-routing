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


@pytest.mark.parametrize("origin,destination", coordinates_list[:5])
@pytest.mark.parametrize("service_name,service_fns", ROUTING_SERVICES.items())
def test_route_plausibility(origin, destination, service_name, service_fns):
    """Check that each service returns plausible results."""
    query_fn, summary_fn = service_fns

    response: QueryResult = query_fn(origin, destination)
    if not response or not response.data:
        pytest.skip(f"{service_name} returned no data for {origin}->{destination}")

    result: RouteSummary = summary_fn(response.data)
    if not result:
        pytest.skip(
            f"{service_name} returned no route summary for {origin}->{destination}"
        )

    # Check if this is an empty route (service found no route)
    if result.is_empty():
        pytest.skip(f"{service_name} found no route between {origin} and {destination}")

    # Basic validation - only for valid routes
    assert result.duration_s > 0, f"Invalid duration: {result.duration_s}"
    assert result.distance_m > 0, f"Invalid distance: {result.distance_m}"
    assert len(result.modes) > 0, "No transport modes found"

    # Realistic plausibility checks for public transport
    assert (
        60 <= result.duration_s <= 43200  # 1 minute to 12 hours
    ), f"Duration {result.duration_s}s ({result.duration_s/3600:.1f}h) seems unrealistic"
    assert (
        50 <= result.distance_m <= 2000000  # 50m to 2000km
    ), f"Distance {result.distance_m}m ({result.distance_m/1000:.1f}km) seems unrealistic"

    # Additional checks for very long routes
    if result.distance_m > 200000:  # > 200km
        # Long distance routes can take longer (up to 16 hours for cross-country)
        assert (
            result.duration_s <= 57600
        ), f"Even long-distance routes shouldn't exceed 16 hours: {result.duration_s}s"
        print(
            f"🚄 Long-distance route detected: {result.distance_m/1000:.1f}km, {result.duration_s/3600:.1f}h"
        )

    print(
        f"✅ {service_name}: {origin}->{destination} "
        f"({result.duration_s}s / {result.duration_s/3600:.1f}h, {result.distance_m/1000:.1f}km)"
    )


@pytest.mark.parametrize("origin,destination", coordinates_list[:3])
def test_cross_service_comparison(origin, destination):
    """Compare results between services for the same route."""
    results = {}

    # Collect results from all services
    for name, (query_fn, summary_fn) in ROUTING_SERVICES.items():
        try:
            response = query_fn(origin, destination)
            if response and response.data:
                summary = summary_fn(response.data)
                # Only include routes that actually found a path
                if summary and not summary.is_empty():
                    results[name] = summary
        except Exception as e:
            print(f"⚠️ {name} failed: {e}")

    if len(results) == 0:
        pytest.skip(f"No services found valid routes for {origin} -> {destination}")

    # Print results with better formatting
    print(f"\n{origin} -> {destination}:")
    for name, summary in results.items():
        print(
            f"  {name}: {summary.duration_s/3600:.1f}h, {summary.distance_m/1000:.1f}km, "
            f"modes={summary.modes[:3]}{'...' if len(summary.modes) > 3 else ''}"
        )

    # Compare if multiple services succeeded
    if len(results) >= 2:
        durations = [r.duration_s for r in results.values()]
        distances = [r.distance_m for r in results.values()]

        # More lenient variance for realistic public transport differences
        duration_ratio = max(durations) / min(durations)
        distance_ratio = max(distances) / min(distances)

        # Public transport can have very different routing strategies
        assert (
            duration_ratio <= 4.0
        ), f"Duration variance too high: {duration_ratio:.2f} (min: {min(durations)/3600:.1f}h, max: {max(durations)/3600:.1f}h)"
        assert (
            distance_ratio <= 3.0
        ), f"Distance variance too high: {distance_ratio:.2f} (min: {min(distances)/1000:.1f}km, max: {max(distances)/1000:.1f}km)"

        print(
            f"✅ Comparison passed (duration ratio: {duration_ratio:.2f}, distance ratio: {distance_ratio:.2f})"
        )
    else:
        print("ℹ️ Only one service found a valid route - no comparison possible")
