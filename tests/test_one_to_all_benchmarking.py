import pytest

from tests.utils.benchmark_helpers import (
    build_container_result_row,
    measure_container_performance,
)
from tests.utils.commons import (
    coordinates_list,
    get_service_by_name,
)

COORDS = coordinates_list[:3]  # Limit for speed


@pytest.mark.parametrize("coord", COORDS)
@pytest.mark.parametrize("service", get_service_by_name("motis"))
def test_container_service_benchmark(
    benchmark,
    coord,
    service,
    container_benchmark_reporter,
):
    """
    Hybrid benchmark for CONTAINERIZED services.
    Measures latency with pytest-benchmark and container resources with Docker SDK.
    """
    origin, _ = coord
    payload = service["onetoall_payload_builder"](
        start_location=origin,
        max_travel_time=60,
    )

    # Part 1: Pure latency benchmark
    def benchmark_target():
        service["client"].post(service["onetoall_endpoint"], json=payload)

    benchmark.pedantic(target=benchmark_target, rounds=5, iterations=1, warmup_rounds=1)

    # Part 2: Get a single, clean result for validation and container resources
    container_result = measure_container_performance(
        target_container_name=service["name"],
        client=service["client"],
        endpoint=service["onetoall_endpoint"],
        payload=payload,
        method=service["method"],
    )

    # Part 3: Validate and Report (using our hybrid result builder)
    assert container_result and container_result.status_code == 200

    # ... save response, build row, append to reporter ...
    row = build_container_result_row(
        service=service,
        origin=origin,
        dest=None,
        latency_stats=benchmark.stats,
        container_result=container_result,
        is_valid=None,  # Validation can be added if needed
    )
    container_benchmark_reporter.append(row)
