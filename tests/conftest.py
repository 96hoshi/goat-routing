import csv
import json
import os
from datetime import datetime, timedelta

import pytest

# Benchmark time: tomorrow at 08:00 UTC
TIME_BENCH: str = (datetime.utcnow() + timedelta(days=1)).replace(
    hour=8, minute=0, second=0, microsecond=0
).isoformat() + "Z"

RESULT_DIR = "tests/results/"
IMAGES_DIR = "tests/results/images/"
RESULT_FILE = "benchmark_results.csv"
RESPONSES_DIR = "tests/results/responses/"

BENCHMARK_FILE = os.path.join(RESULT_DIR, RESULT_FILE)


@pytest.fixture(scope="session")
def benchmark_reporter():
    """A session-scoped fixture to collect benchmark data and write it once."""
    results = []
    os.makedirs(RESULT_DIR, exist_ok=True)  # Ensure directory exists
    yield results

    if not results:
        print("\nNo benchmark results to report.")
        return

    print(f"\nWriting {len(results)} benchmark results to {BENCHMARK_FILE}...")
    with open(BENCHMARK_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print("Benchmark report written successfully.")


@pytest.fixture(scope="session")
def response_writer():
    """A helper object to safely write individual JSON responses."""
    os.makedirs(RESPONSES_DIR, exist_ok=True)  # Ensure directory exists

    class Writer:
        def save(self, data: dict, filename: str):
            filepath = os.path.join(RESPONSES_DIR, filename)
            try:
                with open(filepath, "w") as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"Error writing response to {filepath}: {e}")

    yield Writer()


def write_result(row, filename: str = RESULT_FILE, headers=None):
    """
    Write a single result to a CSV file in the results directory.
    """
    # Ensure the results directory exists
    os.makedirs(RESULT_DIR, exist_ok=True)
    # Always write to the results directory
    filepath = os.path.join(RESULT_DIR, os.path.basename(filename))
    if headers is None:
        headers = list(row.keys())
    file_exists = os.path.isfile(filepath)
    with open(filepath, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def write_response(data: dict, filename: str):
    """
    Write a JSON response to the responses directory.
    """
    os.makedirs(RESPONSES_DIR, exist_ok=True)
    filepath = os.path.join(RESPONSES_DIR, filename)
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error writing response to {filepath}: {e}")
