import concurrent.futures
import csv
import logging
import os
import time
from collections import Counter
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from src.core.config import settings
from tests.conftest import RESULT_DIR
from tests.utils.commons import client
from tests.utils.payload_builders import motis_payload, one_to_all_payload

# --- SETUP STRESS TEST ---

# 1. Configure the logger
stress_test_logger = logging.getLogger("stress_test")
stress_test_logger.setLevel(logging.INFO)

# Create a handler to write logs to a file
log_handler = logging.FileHandler("logs/stress_test_log.log", mode="w")
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler.setFormatter(log_formatter)
stress_test_logger.addHandler(log_handler)

# 2. Define CSV file details
STRESS_TEST_RESULTS_DIR = os.path.join(RESULT_DIR, "stress_tests")

# Fixed headers to match the summary_row keys
STRESS_TEST_HEADERS = [
    "service",
    "endpoint_type",
    "timestamp",
    "num_clients",
    "success_rate",
    "avg_latency_ms",
    "p50_latency_ms",
    "p95_latency_ms",
    "p99_latency_ms",
    "successful_requests",
    "failed_requests_503",
    "other_failed_requests",
]

# Create the results directory if it doesn't exist
os.makedirs(STRESS_TEST_RESULTS_DIR, exist_ok=True)


# --- CORE STRESS TEST ENGINE ---


def run_stress_test(
    payload_func: Callable[[], Dict[str, Any]],
    endpoint: str,
    service_name: str,
    endpoint_type: str,
    num_clients: int = 30,
    max_workers: int = 20,
) -> Dict[str, Any]:
    """
    Core stress test engine that can be reused for different endpoints and payloads.

    Args:
        payload_func: Function that returns the payload dict
        endpoint: API endpoint to test
        service_name: Name of the service for logging
        endpoint_type: Type of endpoint (e.g., "ab_routing", "onetoall")
        num_clients: Number of concurrent clients
        max_workers: Maximum thread pool workers

    Returns:
        Dictionary with test results
    """
    results = []

    def call_service(idx: int):
        payload = payload_func()
        start = time.perf_counter()
        try:
            response = client.post(endpoint, json=payload)
            elapsed_ms = (time.perf_counter() - start) * 1000

            stress_test_logger.info(
                f"Client {idx} ({endpoint_type}): Status {response.status_code}, Latency {elapsed_ms:.2f}ms"
            )

            return {"status": response.status_code, "latency_ms": elapsed_ms}
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            stress_test_logger.error(
                f"Client {idx} ({endpoint_type}): Exception after {elapsed_ms:.2f}ms - {e}"
            )
            return {"status": "exception", "latency_ms": elapsed_ms, "error": str(e)}

    # Execute the stress test
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(max_workers, num_clients)
    ) as executor:
        futures = [executor.submit(call_service, i) for i in range(num_clients)]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    # --- AGGREGATE RESULTS ---
    status_counts = Counter(r["status"] for r in results)
    successful_timings = sorted(
        [r["latency_ms"] for r in results if r["status"] == 200]
    )

    # Calculate statistics
    num_successful = status_counts.get(200, 0)
    num_unavailable = status_counts.get(503, 0)
    num_other_errors = len(results) - num_successful - num_unavailable
    success_rate = num_successful / num_clients if num_clients > 0 else 0

    avg_latency = (
        sum(successful_timings) / len(successful_timings) if successful_timings else 0
    )
    p50_latency = (
        successful_timings[int(len(successful_timings) * 0.5)]
        if successful_timings
        else 0
    )
    p95_latency = (
        successful_timings[int(len(successful_timings) * 0.95)]
        if successful_timings
        else 0
    )
    p99_latency = (
        successful_timings[int(len(successful_timings) * 0.99)]
        if successful_timings
        else 0
    )

    # --- LOG SUMMARY ---
    summary_message = (
        f"Stress Test Summary ({endpoint_type}): "
        f"Clients={num_clients}, Success Rate={success_rate:.2%}, "
        f"Avg Latency={avg_latency:.2f}ms, P95 Latency={p95_latency:.2f}ms, "
        f"503s={num_unavailable}"
    )
    print(f"\n{summary_message}")
    stress_test_logger.info(summary_message)

    # --- PREPARE RESULTS ---
    summary_row = {
        "service": service_name,
        "endpoint_type": endpoint_type,
        "timestamp": datetime.now().isoformat(),
        "num_clients": num_clients,
        "success_rate": f"{success_rate:.2%}",
        "avg_latency_ms": f"{avg_latency:.2f}",
        "p50_latency_ms": f"{p50_latency:.2f}",
        "p95_latency_ms": f"{p95_latency:.2f}",
        "p99_latency_ms": f"{p99_latency:.2f}",
        "successful_requests": num_successful,
        "failed_requests_503": num_unavailable,
        "other_failed_requests": num_other_errors,
    }

    # Save to CSV
    _save_stress_results_to_csv(summary_row, endpoint_type)

    return {
        "success_rate": success_rate,
        "avg_latency": avg_latency,
        "summary_row": summary_row,
        "raw_results": results,
    }


def _save_stress_results_to_csv(summary_row: Dict[str, Any], endpoint_type: str):
    """Save stress test results to CSV file."""
    csv_filename = os.path.join(
        STRESS_TEST_RESULTS_DIR,
        f"stress_{endpoint_type}.csv",
    )

    try:
        # Ensure directory exists
        os.makedirs(STRESS_TEST_RESULTS_DIR, exist_ok=True)

        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(csv_filename)
        write_header = not file_exists

        # Write to CSV
        with open(csv_filename, mode="a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=STRESS_TEST_HEADERS)

            if write_header:
                writer.writeheader()
                print(f"📊 Created new CSV file: {csv_filename}")

            writer.writerow(summary_row)
            csvfile.flush()

        print(f"✅ Results saved to: {csv_filename}")
        stress_test_logger.info(f"Results saved to CSV: {csv_filename}")

        # Verify the file was written
        if os.path.exists(csv_filename):
            file_size = os.path.getsize(csv_filename)
            print(f"📝 CSV file size: {file_size} bytes")

    except Exception as e:
        error_msg = f"Failed to write CSV results: {e}"
        print(f"❌ {error_msg}")
        stress_test_logger.error(error_msg)


# --- PAYLOAD GENERATORS ---


def create_ab_routing_payload(
    origin: str = "53.552809,9.979069", destination: str = "53.475653,9.704257"
):
    """Generate A-B routing payload."""
    return motis_payload(
        origin=origin, destination=destination, detailed_transfers=False
    )


def create_onetoall_payload(
    origin: str = "53.552809,9.979069",
    max_duration: int = 90,
    departure_time: Optional[int] = None,
):
    """Generate one-to-all routing payload."""

    return one_to_all_payload(
        start_location=origin,
        max_travel_time=max_duration,
    )


# --- STANDARD TEST FUNCTIONS ---


def test_motis_ab_routing_stress(num_clients: int = 30):
    """Test A-B routing endpoint with stress load."""
    result = run_stress_test(
        payload_func=create_ab_routing_payload,
        endpoint=settings.PLAN_ROUTE,
        service_name="motis_ab_routing",
        endpoint_type="ab_routing",
        num_clients=num_clients,
    )

    # Assert success criteria
    assert (
        result["success_rate"] > 0.8
    ), f"A-B routing success rate {result['success_rate']:.2%} below 80%"
    return result


def test_motis_onetoall_stress(num_clients: int = 30):
    """Test one-to-all routing endpoint with stress load."""
    result = run_stress_test(
        payload_func=create_onetoall_payload,
        endpoint=settings.ONETOALL_ROUTE,
        service_name="motis_onetoall_routing",
        endpoint_type="onetoall",
        num_clients=num_clients,
    )

    # Assert success criteria
    assert (
        result["success_rate"] > 0.8
    ), f"One-to-all routing success rate {result['success_rate']:.2%} below 80%"
    return result
