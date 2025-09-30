import pytest

from tests.utils.commons import SERVICES, coordinates_list, write_result

BENCHMARK_FILE = "benchmark_results.csv"
BENCHMARK_HEADERS = [
    "service",
    "origin",
    "destination",
    "avg_time_ms",
    "avg_cpu_s",
    "avg_mem_mb",
    "response_size_bytes",
]


def build_result_row(
    service, origin, destination, avg_time, avg_cpu, avg_mem, response_size
):
    return {
        "service": service["name"],
        "origin": origin,
        "destination": destination,
        "avg_time_ms": avg_time,
        "avg_cpu_s": avg_cpu if avg_cpu is not None else "",
        "avg_mem_mb": avg_mem if avg_mem is not None else "",
        "response_size_bytes": response_size,
    }


@pytest.mark.benchmark(group="ab_routing")
@pytest.mark.parametrize("coord", coordinates_list)
@pytest.mark.parametrize("service", SERVICES)
def test_compare_services_benchmark_with_coords(benchmark, coord, service):
    """
    Benchmark a single routing service using a coordinate pair.
    Tracks timing, CPU, memory usage, and response size per request.
    Saves results to a CSV file.
    """
    origin, destination = coord

    def run_benchmark():
        payload = service["payload_builder"](origin, destination)
        avg_time, avg_cpu, avg_mem = service["benchmark_func"](
            service["client"], service["endpoint"], payload, num_requests=15
        )
        # Measure response size for a single request
        if service["client"]:
            response = service["client"].post(service["endpoint"], json=payload)
            response_size = len(response.content)
        else:
            import requests

            response = requests.get(service["endpoint"], params=payload)
            response_size = len(response.content)
        row = build_result_row(
            service, origin, destination, avg_time, avg_cpu, avg_mem, response_size
        )
        write_result(row, filename=BENCHMARK_FILE, headers=BENCHMARK_HEADERS)

    benchmark(run_benchmark)
