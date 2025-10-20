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
IMAGES_DIR = os.path.join(RESULT_DIR, "images")
RESPONSES_DIR = os.path.join(RESULT_DIR, "responses")
BENCHMARK_DIR = os.path.join(RESULT_DIR, "benchmarks")


@pytest.fixture(scope="session")
def container_benchmark_reporter(request):
    """Fixture to collect benchmark results for containerized services."""
    results = []
    # Attach the list to the config so we can access it later
    request.config.container_benchmark_data = results
    yield results


@pytest.fixture(scope="session")
def api_benchmark_reporter(request):
    """Fixture to collect benchmark results for external API services."""
    results = []
    # Attach the list to the config so we can access it later
    request.config.api_benchmark_data = results
    yield results


def pytest_sessionfinish(session):
    """
    Hook that runs after the entire test session finishes.
    Writes collected benchmark data to separate CSV files.
    """
    print("\n--- Writing final benchmark reports ---")
    os.makedirs(RESULT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- Write the Container Benchmark Report ---
    container_data = getattr(session.config, "container_benchmark_data", [])
    if container_data:
        filename = os.path.join(RESULT_DIR, f"container_benchmarks_{timestamp}.csv")
        print(
            f"Writing {len(container_data)} container benchmark results to {filename}..."
        )

        fieldnames = container_data[0].keys()

        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(container_data)
    else:
        print("No container benchmark data to write.")

    # --- Write the API Benchmark Report ---
    api_data = getattr(session.config, "api_benchmark_data", [])
    if api_data:
        filename = os.path.join(RESULT_DIR, f"api_benchmarks_{timestamp}.csv")
        print(f"Writing {len(api_data)} API benchmark results to {filename}...")

        fieldnames = api_data[0].keys()

        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(api_data)
    else:
        print("No API benchmark data to write.")


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


def write_result(row, filename, headers=None):
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
