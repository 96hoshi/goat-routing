import pytest

from tests.utils.commons import coordinates_list
from tests.utils.plausibility_helpers import (
    extract_google_route_summary,
    extract_motis_route_summary,
    query_google,
    query_motis,
)

ROUTING_SERVICES = {
    "motis": (query_motis, extract_motis_route_summary),
    "google": (query_google, extract_google_route_summary),
}


@pytest.mark.parametrize("origin,destination", coordinates_list)
@pytest.mark.parametrize("service_name,service_fns", ROUTING_SERVICES.items())
def test_route_plausibility(origin, destination, service_name, service_fns):
    """Check that each service returns plausible results."""
    query_fn, summary_fn = service_fns
    result_raw, _ = query_fn(origin, destination)
    result = summary_fn(result_raw) if result_raw else None
    if result is None:
        pytest.skip(f"{service_name} returned no route for {origin}->{destination}")
    assert isinstance(
        result["duration"], (int, float)
    ), f"{service_name}: duration type"
    assert result["duration"] > 0, f"{service_name}: duration not positive"
    assert isinstance(
        result["distance"], (int, float)
    ), f"{service_name}: distance type"
    assert result["distance"] > 0, f"{service_name}: distance not positive"
    assert isinstance(result["modes"], list), f"{service_name}: modes type"
    assert isinstance(
        result["vehicle_lines"], list
    ), f"{service_name}: vehicle_lines type"


@pytest.mark.parametrize("origin,destination", coordinates_list[:3])  # limit for speed
def test_cross_service_comparison(origin, destination):
    """Compare results between all services for the same OD pair."""
    results = {}
    for name, (query_fn, summary_fn) in ROUTING_SERVICES.items():
        result_raw, _ = query_fn(origin, destination)
        summary = summary_fn(result_raw) if result_raw else None
        results[name] = (
            summary
            if summary is not None
            else {"duration": None, "distance": None, "modes": [], "vehicle_lines": []}
        )

    print(f"\n--- Comparison {origin} -> {destination} ---")
    for name, res in results.items():
        print(f"{name:<8}: {res}")

    durations = [res["duration"] for res in results.values() if res["duration"]]
    if len(durations) >= 2:
        min_d, max_d = min(durations), max(durations)
        assert (
            max_d <= 1.5 * min_d
        ), f"Duration mismatch too large: min={min_d}, max={max_d}"
