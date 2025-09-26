import time
import logging
import concurrent.futures

from src.schemas.ab_routing import motis_request_examples
from tests.utils.commons import client

def test_heavy_load_concurrent(num_clients=100):
    """
    Simulate many clients calling the same route concurrently and compute average response time.
    """
    timings = []

    def call_motis(idx: int):
        """
        Function to call Motis and return elapsed time.
        """
        logging.basicConfig(level=logging.INFO)

        start = time.perf_counter()
        response = client.post("/ab-routing", json=motis_request_examples["benchmark"])
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
        # Submit all tasks and collect timings
        futures = [executor.submit(call_motis, i) for i in range(num_clients)]
        for future in concurrent.futures.as_completed(futures):
            timings.append(future.result())

    avg_time = sum(timings) / len(timings) if timings else 0
    logging.info(f"Heavy load test completed for {num_clients} clients.")
    logging.info(f"Average response time: {avg_time:.2f} ms")
    logging.info(f"Average response time: {avg_time:.2f} ms")

    print(f"\nHeavy load test completed for {num_clients} clients.")
    print(f"Average response time: {avg_time:.2f} ms")
