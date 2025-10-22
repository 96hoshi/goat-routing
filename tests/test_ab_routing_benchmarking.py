import pytest

from tests.utils.benchmark_helpers import (
    build_api_result_row,
    build_container_result_row,
    measure_container_performance,
    validate_service_response,
)
from tests.utils.commons import coordinates_list, get_services_by_type
from tests.utils.models import ServiceMetrics


@pytest.mark.parametrize("coord", coordinates_list)
@pytest.mark.parametrize("service", get_services_by_type("container"))
def test_container_service_benchmark(
    benchmark, coord, service, container_benchmark_reporter, response_writer
):
    """
    Hybrid benchmark for CONTAINERIZED services.
    Measures latency with pytest-benchmark and container resources with Docker SDK.
    """
    origin, destination = coord
    payload = service["payload_builder"](origin=origin, destination=destination)

    # Part 1: Pure latency benchmark
    def benchmark_target():
        service["client"].post(service["endpoint"], json=payload, timeout=60)

    benchmark.pedantic(target=benchmark_target, rounds=5, iterations=1, warmup_rounds=1)

    # Part 2: Get a single, clean result for validation and container resources
    container_result = measure_container_performance(
        target_container_name=service["name"],
        client=service["client"],
        endpoint=service["endpoint"],
        payload=payload,
        method=service["method"],
    )

    # Part 3: Validate and Report (using our hybrid result builder)
    assert container_result and container_result.status_code == 200
    is_valid = validate_service_response(container_result, service["name"])
    assert is_valid

    # ... save response, build row, append to reporter ...
    row = build_container_result_row(
        service=service,
        origin=origin,
        dest=destination,
        latency_stats=benchmark.stats,
        container_result=container_result,
        is_valid=is_valid,
    )
    container_benchmark_reporter.append(row)


@pytest.mark.parametrize("coord", coordinates_list)
@pytest.mark.parametrize("service", get_services_by_type("api"))
def test_api_service_benchmark(benchmark, coord, service, api_benchmark_reporter):
    """
    Original benchmark for EXTERNAL/API services.
    Measures latency and CLIENT-SIDE resource usage (psutil).
    """
    origin, destination = coord
    payload = service["payload_builder"](origin=origin, destination=destination)

    # Use the original workflow that works with immutable objects
    def benchmark_target():
        service["query_func"](
            client=service["client"],
            endpoint=service["endpoint"],
            payload=payload,
            method=service["method"],
        )

    benchmark.pedantic(target=benchmark_target, rounds=5, iterations=1, warmup_rounds=1)

    # Get a single result for validation
    result: ServiceMetrics = service["query_func"](
        client=service["client"],
        endpoint=service["endpoint"],
        payload=payload,
        method=service["method"],
    )

    # Validate and Report (using your original result builder)
    assert result and result.status_code == 200
    is_valid = validate_service_response(result, service["name"])
    assert is_valid

    # ... save response, build row, append to reporter ...
    row = build_api_result_row(
        service=service,
        origin=origin,
        dest=destination,
        benchmark_stats=benchmark.stats,
        result=result,
        is_valid=is_valid,
    )
    api_benchmark_reporter.append(row)
