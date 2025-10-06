"""
Unit tests for Valhalla routing service integration.
"""

import pytest

from src.core.config import settings
from tests.utils.benchmark_helpers import benchmark_http_requests
from tests.utils.commons import coordinates_list, write_response
from tests.utils.query_helpers import (
    extract_valhalla_route_summary,
    query_valhalla,
)


@pytest.mark.parametrize(
    "origin,destination", coordinates_list[:3]
)  # Test first 3 pairs
def test_valhalla_routing_basic(origin, destination):
    """Test basic Valhalla routing functionality."""
    result, response_size = query_valhalla(origin, destination, costing="auto")

    assert (
        result is not None
    ), f"Valhalla returned no result for {origin} -> {destination}"
    assert (
        response_size is not None and response_size > 0
    ), "Response size should be greater than 0"
    assert "trip" in result, "Response should contain 'trip' key"
    assert "legs" in result["trip"], "Trip should contain 'legs'"


@pytest.mark.parametrize("costing", ["auto", "pedestrian", "bicycle"])
def test_valhalla_different_costing(costing):
    """Test Valhalla with different routing profiles."""
    origin, destination = coordinates_list[0]

    result, _ = query_valhalla(origin, destination, costing=costing)

    assert result is not None, f"Valhalla returned no result for costing '{costing}'"
    assert "trip" in result

    # Extract summary and validate
    summary = extract_valhalla_route_summary(result)
    assert summary is not None, f"Could not extract summary for costing '{costing}'"
    assert summary["duration"] > 0, "Duration should be positive"
    assert summary["distance"] > 0, "Distance should be positive"


def test_valhalla_route_summary_extraction():
    """Test route summary extraction from Valhalla response."""
    origin, destination = coordinates_list[0]

    result, _ = query_valhalla(origin, destination, costing="auto")
    assert result is not None, "Valhalla should return a result"
    # write result to file for inspection if needed
    write_response(result, f"valhalla_response_{origin}_{destination}.json")

    summary = extract_valhalla_route_summary(result)
    assert summary is not None, "Should extract a valid summary"

    # Validate summary structure
    required_keys = ["duration", "distance", "modes", "vehicle_lines"]
    for key in required_keys:
        assert key in summary, f"Summary should contain '{key}'"

    assert isinstance(summary["duration"], (int, float)), "Duration should be numeric"
    assert isinstance(summary["distance"], (int, float)), "Distance should be numeric"
    assert isinstance(summary["modes"], list), "Modes should be a list"
    assert isinstance(summary["vehicle_lines"], list), "Vehicle lines should be a list"


def test_valhalla_benchmark():
    """Test Valhalla benchmarking functionality."""
    from tests.utils.commons import valhalla_payload

    origin, destination = coordinates_list[0]
    payload = valhalla_payload(origin, destination, costing="auto")

    # Run a small benchmark
    avg_time, avg_cpu, avg_memory = benchmark_http_requests(
        None, settings.VALHALLA_URL, payload, num_requests=3
    )

    assert avg_time > 0, "Average time should be positive"
    # CPU and memory might be 0 or None depending on system
    assert avg_cpu is not None, "CPU measurement should return a value"
    assert avg_memory is not None, "Memory measurement should return a value"


def test_valhalla_error_handling():
    """Test Valhalla error handling with invalid coordinates."""
    # Use invalid coordinates
    invalid_origin = "999,999"
    invalid_destination = "888,888"

    result, response_size = query_valhalla(invalid_origin, invalid_destination)

    # Should either return None or handle gracefully
    if result is not None:
        # If we get a result, it should still be well-formed
        assert isinstance(result, dict), "Result should be a dictionary"
    # If result is None, that's also acceptable error handling


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


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])
