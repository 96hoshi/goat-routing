import pytest

from tests.utils.benchmark_helpers import validate_service_response
from tests.utils.commons import SERVICES, coordinates_list
from tests.utils.models import ServiceMetrics


def build_performance_result_row(
    service, origin, dest, benchmark_stats, result: ServiceMetrics, is_valid: bool
):
    """Build result row with only the expected fieldnames for CSV output."""
    return {
        # Standard fields expected by benchmark_reporter
        "service": service["name"],
        "origin": origin,
        "destination": dest,
        "avg_time_ms": f"{benchmark_stats['mean'] * 1000:.3f}",
        "avg_cpu_s": f"{result.cpu_s:.4f}",
        "avg_mem_mb_delta": f"{result.mem_mb_delta:.4f}",
        "avg_response_size_bytes": f"{result.response_size_bytes:.0f}",
        "rounds": benchmark_stats["rounds"],
        # Additional performance metrics (if supported by fieldnames)
        "min_time_ms": f"{benchmark_stats['min'] * 1000:.3f}",
        "max_time_ms": f"{benchmark_stats['max'] * 1000:.3f}",
        "median_time_ms": f"{benchmark_stats['median'] * 1000:.3f}",
        "stddev_time_ms": f"{benchmark_stats['stddev'] * 1000:.3f}",
        "status_code": result.status_code,
        "valid_response": is_valid,
        # Performance ratios
        "bytes_per_ms": f"{result.response_size_bytes / (benchmark_stats['mean'] * 1000):.2f}",
        "cpu_efficiency": f"{result.cpu_s / benchmark_stats['mean']:.4f}",
        "cv_percent": f"{(benchmark_stats['stddev'] / benchmark_stats['mean']) * 100:.2f}",
    }


@pytest.mark.parametrize("coord", coordinates_list)
@pytest.mark.parametrize("service", SERVICES)
def test_compare_services_benchmark(
    benchmark, coord, service, benchmark_reporter, response_writer
):
    """
    Enhanced performance benchmarking with detailed timing and resource metrics.
    """
    origin, destination = coord

    # Add transport mode for OTP if needed
    kwargs = {"origin": origin, "destination": destination}
    if service["name"] == "otp":
        kwargs["transport_modes"] = ["TRANSIT", "WALK"]

    payload = service["payload_builder"](**kwargs)

    result: ServiceMetrics = benchmark.pedantic(
        target=service["query_func"],
        kwargs={
            "client": service["client"],
            "endpoint": service["endpoint"],
            "payload": payload,
            "method": service["method"],
        },
        rounds=5,  # Run 5 times for stable stats
        iterations=1,
        warmup_rounds=1,  # Add warmup for more accurate timing
    )

    # Assert that the request was successful
    assert result.status_code == 200, f"Request failed with status {result.status_code}"

    # Validate response contains data (performance check)
    is_valid = validate_service_response(result, service["name"])
    assert is_valid, f"Service {service['name']} returned invalid response"

    # Save response for debugging
    response_filename = f"{service['name']}_{origin}_{destination}.json".replace(
        ",", "_"
    )
    response_writer.save(result.response_data, response_filename)

    # Build performance-focused result row
    row = build_performance_result_row(
        service, origin, destination, benchmark.stats, result, is_valid
    )
    benchmark_reporter.append(row)
