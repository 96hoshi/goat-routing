# Tests & Benchmarking Guide

This directory contains automated tests and benchmarking scripts for the routing services.

## Contents

- Integration, plausibility, stress, and benchmarking tests
- Scripts for comparing routing service performance

## Scripting Folder

The `scripts/` folder contains utility scripts for advanced testing, benchmarking, and analysis:

- **modes_comparison.py**: Compares routing service modes and generates performance visualizations.
- **benchmark_comparison.py**: Compares benchmarking results across different runs and can produce summary plots or tables.
- **other scripts**: Additional helpers for data processing, result aggregation, or custom test workflows.

Refer to each script's inline documentation or usage instructions for details.

## Running Tests

### Run All Tests

```sh
pytest
```

### Run a Specific Test File

```sh
pytest tests/test_ab_routing_benchmarking.py
```

### Run Benchmarking Tests

Benchmarking results are saved automatically to `results/benchmark_results.csv`.

```sh
pytest --benchmark-save tests/test_ab_routing_benchmarking.py
```

## Viewing Results

- **Benchmark results:** `results/benchmark_results.csv`
- **Service comparison:** `results/service_comparison_results.csv`
- **Response files:** `results/responses/`
- **Compare benchmarks:**  
    ```sh
    pytest-benchmark compare .benchmarks/<run>.json
    ```

## Comparing and Visualizing Routing Services

To generate service comparison results and visualizations:

```sh
python tests/scripts/modes_comparison.py
```

To compare benchmarking runs and visualize the results:

```sh
python tests/scripts/benchmark_comparison.py
```
