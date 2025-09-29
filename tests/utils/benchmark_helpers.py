import time

import psutil
import requests


def benchmark_requests(client, endpoint, payload, num_requests=15):
    """
    Send requests to the given endpoint and measure timing, CPU, and memory usage.
    Returns average timing, CPU usage, and memory usage.
    """
    timings = []
    cpu_usages = []
    mem_usages = []
    process = psutil.Process()

    for _ in range(num_requests):
        mem_before = process.memory_info().rss / (1024 * 1024)
        cpu_times_before = process.cpu_times()

        start = time.perf_counter()
        response = client.post(endpoint, json=payload)
        end = time.perf_counter()

        mem_after = process.memory_info().rss / (1024 * 1024)
        cpu_times_after = process.cpu_times()

        timings.append((end - start) * 1000)  # ms
        cpu_time_delta = (cpu_times_after.user + cpu_times_after.system) - (
            cpu_times_before.user + cpu_times_before.system
        )
        cpu_usages.append(cpu_time_delta)
        mem_usages.append(mem_after - mem_before)

        assert response.status_code == 200

    avg_time = sum(timings) / len(timings) if timings else 0
    avg_cpu = sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0
    avg_mem = sum(mem_usages) / len(mem_usages) if mem_usages else 0

    return avg_time, avg_cpu, avg_mem


def benchmark_google_requests(client_unused, endpoint, payload, num_requests=15):
    timings = []
    for _ in range(num_requests):
        start = time.perf_counter()
        response = requests.get(endpoint, params=payload)
        end = time.perf_counter()
        timings.append((end - start) * 1000)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "OK"
    avg_time = sum(timings) / len(timings) if timings else 0
    return avg_time, None, None
