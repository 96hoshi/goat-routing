import csv
import os

import pytest

from src.core.config import settings
from tests.utils.commons import client
from tests.utils.models import BenchmarkResult


def log_to_csv_simple(filepath: str, data_dict: dict):
    """Appends a dictionary as a row to a CSV file."""
    header = list(data_dict.keys())
    values = list(data_dict.values())
    file_exists = os.path.exists(filepath)

    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow(values)


def fixture_coordinates():
    coords = []
    with open("tests/coords/coords.csv", "r") as f:
        next(f)  # skip header
        for line in f:
            # substitute , with ;
            lat, lon = line.strip().split(",")
            lat_clean = lat.strip('"')
            lon_clean = lon.strip('"')

            formatted_coord = f"{float(lat_clean):.6f};{float(lon_clean):.6f}"
            coords.append(formatted_coord)
    # save to a file for manual inspection as a list
    with open("tests/coords/fixture_coordinates.txt", "w") as f:
        for coord in coords:
            f.write(f"{coord},\n")
    return coords


def test_one_to_many_integration():
    """request_payload
    Performs a real end-to-end test against the live MOTIS service for /one-to-many.
    """
    coords = fixture_coordinates()

    request_payload = {
        "one": "48.140228;11.558330",
        "many": coords[:10],  # limit to first 100 for speed
        "max": 36000,
        "maxMatchingDistance": 600,
        "mode": "WALK",
        "arriveBy": False,
    }

    response = client.post(settings.ONETOMANY_ROUTE, json=request_payload)
    assert response.status_code == 200, f"Unexpected status code: {response}"

    data = response.json()

    # Assert the envelope structure from your API is correct
    assert "result" in data
    assert "status_code" in data
    assert data["status_code"] == 200

    motis_result = data["result"]

    # append the result to a file for manual inspection
    with open("results/one_to_many.json", "w") as f:
        import json

        json.dump(motis_result, f, indent=2)


@pytest.mark.parametrize("num_many", [50, 100, 200, 300])
def test_container_service_benchmark(benchmark, num_many: int):
    """
    Hybrid benchmark for CONTAINERIZED services.
    """
    # do it for one to many
    from tests.utils.benchmark_helpers import (
        measure_container_performance,
    )

    coords = fixture_coordinates()
    one = "48.140228;11.558330"
    max_seconds = 36000  # seconds (10 hours)
    maxMatchingDistance = 600
    arriveBy = False
    mode = "WALK"

    request_payload = {
        "one": one,
        "many": coords[:num_many],
        "max": max_seconds,
        "maxMatchingDistance": maxMatchingDistance,
        "mode": mode,
        "arriveBy": arriveBy,
    }

    def benchmark_target():
        client.post(settings.ONETOMANY_ROUTE, json=request_payload)

    benchmark.pedantic(target=benchmark_target, rounds=2, iterations=1, warmup_rounds=1)

    # Part 2: Get a single, clean result for validation and container resources

    container_result: BenchmarkResult = measure_container_performance(
        target_container_name="motis",
        client=client,
        endpoint=settings.ONETOMANY_ROUTE,
        payload=request_payload,
        method="POST",
    )

    # Basic assertions
    assert container_result.status_code == 200
    assert container_result.latency_ms < 5000  # example threshold

    data = container_result.response_data

    # Assert the envelope structure from your API is correct
    assert "result" in data
    assert "status_code" in data

    # append the result to a file for manual inspection
    with open("results/one_to_many.json", "w") as f:
        import json

        json.dump(data, f, indent=2)

    params = {
        "one": one,
        "num_many": num_many,
        "max_seconds": max_seconds,
        "maxMatchingDistance": maxMatchingDistance,
        "arriveBy": arriveBy,
        "mode": mode,
    }
    full_data = container_result._asdict() | params

    # --- 4. Call the simple logging function ---
    log_to_csv_simple("results/one_to_many_benchmark.csv", full_data)
