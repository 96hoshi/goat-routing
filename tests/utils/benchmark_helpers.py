import time

import httpx
import psutil


def benchmark_http_requests(
    client_or_none, endpoint, payload, num_requests=15, method="POST"
):
    """
    Universal benchmark function that works for both internal (TestClient)
    and external (HTTP) endpoints.

    Args:
        client_or_none: TestClient for internal calls, None for external HTTP calls
        endpoint: URL endpoint to call
        payload: Request payload
        num_requests: Number of requests to make
        method: HTTP method ("POST" or "GET")

    Returns:
        Tuple of (avg_time_ms, avg_cpu_seconds, avg_memory_mb)
    """
    timings = []
    cpu_usages = []
    mem_usages = []
    process = psutil.Process()

    for _ in range(num_requests):
        mem_before = process.memory_info().rss / (1024 * 1024)
        cpu_times_before = process.cpu_times()

        start = time.perf_counter()

        try:
            if client_or_none is None:
                # External HTTP call (Google, Valhalla)
                with httpx.Client(timeout=30.0) as http_client:
                    if method.upper() == "GET":
                        response = http_client.get(endpoint, params=payload)
                    else:
                        response = http_client.post(endpoint, json=payload)
                    response.raise_for_status()

                    # Special validation for Google
                    if "googleapis.com" in endpoint:
                        data = response.json()
                        assert data.get("status") == "OK"

            else:
                # Internal FastAPI call (Motis)
                response = client_or_none.post(endpoint, json=payload)
                assert response.status_code == 200

        except Exception as e:
            print(f"Error in benchmark request to {endpoint}: {e}")
            continue

        end = time.perf_counter()

        mem_after = process.memory_info().rss / (1024 * 1024)
        cpu_times_after = process.cpu_times()

        timings.append((end - start) * 1000)  # ms
        cpu_time_delta = (cpu_times_after.user + cpu_times_after.system) - (
            cpu_times_before.user + cpu_times_before.system
        )
        cpu_usages.append(cpu_time_delta)
        mem_usages.append(mem_after - mem_before)

    avg_time = sum(timings) / len(timings) if timings else 0
    avg_cpu = sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0
    avg_mem = sum(mem_usages) / len(mem_usages) if mem_usages else 0

    return avg_time, avg_cpu, avg_mem
