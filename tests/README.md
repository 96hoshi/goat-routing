# README: /app/tests

## Overview

This folder contains automated tests and benchmarking scripts for the routing services.  
Tests cover integration, plausibility, stress, and benchmarking.

## How to Run Tests

### 1. Run All Tests

```sh
pytest
```

### 2. Run a Specific Test File

```sh
pytest tests/test_ab_routing_benchmarking.py
```

### 3. Run Benchmarking Tests

Benchmarking results are saved to `results/benchmark_results.csv` automatically.

```sh
pytest --benchmark-save tests/test_ab_routing_benchmarking.py
```

### 4. View Test Results

- **Benchmark results:** `results/benchmark_results.csv` and `pytest-benchmark compare .benchmarks/<run>.json`
- **Service comparison:** `results/service_comparison_results.csv`
- **Modes and vehicle lines:** `results/modes_and_vehicle_lines.csv`
- **Response files:** `results/responses/`

### 5. Execute and Compare Routing Services

To run the comparison script and generate service comparison results and visualizations:

```sh
python tests/scripts/comparison.py
```

This will:
- Query both Motis and Google Directions for all coordinate pairs in coords.py.
- Save the comparison results to `results/service_comparison_results.csv`.
- Automatically generate visualizations in `results/images/`.

---

**Note:**  
- Ensure all dependencies are installed (see project requirements).
- Tests are designed for use with `pytest` and `pytest-benchmark`.