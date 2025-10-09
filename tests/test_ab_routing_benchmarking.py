import pytest

from tests.utils.commons import SERVICES, coordinates_list
from tests.utils.models import ServiceMetrics

NUM_REQUESTS = 15


# This function can now be in this file or a utils file.
def build_result_row(
    service, origin, dest, avg_time, avg_cpu, avg_mem, response_size, rounds
):
    return {
        "service": service["name"],
        "origin": origin,
        "destination": dest,
        "avg_time_ms": f"{avg_time:.3f}",
        "avg_cpu_s": f"{avg_cpu:.4f}",
        "avg_mem_mb_delta": f"{avg_mem:.4f}",
        "avg_response_size_bytes": f"{response_size:.0f}",
        "rounds": rounds,
    }


@pytest.mark.benchmark(group="ab_routing")
@pytest.mark.parametrize("coord", coordinates_list[:3])
@pytest.mark.parametrize("service", SERVICES)
def test_compare_services_benchmark(
    benchmark, coord, service, benchmark_reporter, response_writer
):
    """
    Benchmarks a service, capturing timing, CPU, memory, response size and the response itself.
    """
    origin, destination = coord
    payload = service["payload_builder"](origin, destination)

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
    )

    # Assert that the request was successful
    assert result.status_code == 200, f"Request failed with status {result.status_code}"

    # Get reliable timing from the benchmark framework
    avg_time_ms = benchmark.stats["mean"] * 1000

    # Use our custom fixture to write the full JSON response
    response_filename = f"{service['name']}_{origin}_{destination}.json".replace(
        ",", "_"
    )
    response_writer.save(result.response_data, response_filename)

    # Append the aggregated result to our CSV reporter
    row = build_result_row(
        service,
        origin,
        destination,
        avg_time=avg_time_ms,
        avg_cpu=result.cpu_s,
        avg_mem=result.mem_mb_delta,
        response_size=result.response_size_bytes,
        rounds=benchmark.stats["rounds"],
    )
    benchmark_reporter.append(row)
