import concurrent.futures
import time

from tests.utils.commons import MOTIS_PAYLOAD_BENCH, client, write_result

STRESS_TEST_FILE = "stress_test_results"
STRESS_TEST_HEADERS = [
    "num_clients",
    "avg_time_ms",
    "timings_ms",
]


def test_heavy_load_concurrent(num_clients=50):
    """
    Simulate many clients calling the same route concurrently and write results to CSV.
    """
    timings = []

    def call_motis(idx: int):
        start = time.perf_counter()
        response = client.post("/ab-routing", json=MOTIS_PAYLOAD_BENCH)
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000

        assert (
            response.status_code == 200
        ), f"Status {response.status_code} for client {idx}"
        data = response.json()
        assert "result" in data
        assert "message" in data and data["message"] == "Plan computed successfully."

        return elapsed_ms

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(call_motis, i) for i in range(num_clients)]
        for future in concurrent.futures.as_completed(futures):
            timings.append(future.result())

    avg_time = sum(timings) / len(timings) if timings else 0

    row = {
        "num_clients": num_clients,
        "avg_time_ms": avg_time,
        "timings_ms": "|".join(f"{t:.2f}" for t in timings),
    }
    write_result(row, filename=STRESS_TEST_FILE, headers=STRESS_TEST_HEADERS)
