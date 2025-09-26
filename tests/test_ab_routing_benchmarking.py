import logging

import pytest

from coords.coordinates_mannheim import coordinates_list
from src.schemas.ab_routing import motis_request_examples
from tests.utils.benchmark_helpers import benchmark_requests
from tests.utils.commons import client

@pytest.mark.benchmark(group="ab_routing")
@pytest.mark.parametrize("payload_name", list(motis_request_examples.keys()))
def test_benchmark_ab_routing_payloads(benchmark, payload_name):
    """
    Benchmark the AB-routing endpoint using pytest-benchmark for different payloads.

    Args:
        benchmark (): pytest-benchmark fixture
        payload_name ()): Key to select the payload from motis_request_examples
    """
    payload = motis_request_examples[payload_name]

    def send_request():
        response = client.post("/ab-routing", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "message" in data
        assert data["message"] == "Plan computed successfully."

    # Run the benchmark
    benchmark(send_request)


# ---------- Benchmarking with Fixed Coordinates ---------- #
@pytest.mark.benchmark(group="ab_routing")
@pytest.mark.parametrize("coord", coordinates_list)
def test_ab_routing_benchmark_with_coords(benchmark, coord):
    """
    Benchmark the AB-routing endpoint using various coordinate pairs.
    Tracks timing, CPU, and memory usage per request.
    """
    def run_benchmark():
        origin, destination = coord
        payload = {
            "fromPlace": origin,
            "toPlace": destination,
            "time": "2025-08-28T08:00:00Z",
        }
        avg_time, avg_cpu, avg_mem = benchmark_requests(
            client, "/ab-routing", payload, num_requests=15
        )
        logging.info(
            f"Route {origin} -> {destination}: "
            f"Avg time {avg_time:.2f} ms, "
            f"Avg CPU Δ {avg_cpu:.4f} sec, "
            f"Avg Memory Δ {avg_mem:.2f} MB"
        )

    benchmark(run_benchmark)
