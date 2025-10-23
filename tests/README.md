# Tests & Benchmarking Guide

This directory contains automated tests and benchmarking scripts for the routing services.

## Contents

- Integration, plausibility, stress, and benchmarking tests
- Scripts for comparing routing service performance
- Comprehensive visualization generation for routing comparisons
- Automated test execution with report generation

## Scripting Folder

The `scripts/` folder contains utility scripts for advanced testing, benchmarking, and analysis:

- **modes_comparison.py**: Compares routing service modes and generates CSV data for analysis
- **visualize.py**: Generates routing comparison visualizations (line, scatter, bar, grouped bar plots)
- **visualize_performances.py**: Creates performance/benchmark comparison charts
- **benchmark_comparison.py**: Compares benchmarking results across different runs and produces summary plots or tables
- **other scripts**: Additional helpers for data processing, result aggregation, or custom test workflows

Refer to each script's inline documentation or usage instructions for details.

## Running Tests

### Run All Tests

```sh
pytest
```

### Run Specific Test Files

```sh
# Plausibility tests
pytest tests/test_ab_routing_plausibility.py

# Integration tests  
pytest tests/test_ab_routing_integration.py

# MOTIS routing tests
pytest tests/test_motis_routing.py

# Benchmarking tests
pytest tests/test_ab_routing_benchmarking.py
```

### Run Benchmarking Tests

Benchmarking results are saved automatically to `results/benchmark_results.csv`.

```sh
pytest --benchmark-save tests/test_ab_routing_benchmarking.py
```

### Run with Verbose Output

```sh
# Show print statements and detailed output
pytest tests/test_motis_routing.py -v -s

# Show only failed test details
pytest tests/test_ab_routing_plausibility.py -v --tb=short
```

## Automated Test Execution

### Comprehensive Test Suite

Run all tests and generate reports automatically:

```sh
# Make executable and run
chmod +x run_tests.sh
./run_tests.sh
```

This script will:
1. Run all test suites (plausibility, integration, MOTIS)
2. Generate comparison data (modes_comparison.py)
3. Create all visualization plots
4. Generate performance comparison charts
5. Create a comprehensive execution report

## Viewing Results

### Generated Files

- **Benchmark results:** `tests/results/benchmark_results.csv`
- **Service comparison:** `tests/results/service_comparison_results.csv` 
- **Transport comparison:** `tests/results/transport_routes_comparison.csv`
- **Driving comparison:** `tests/results/driving_routes_comparison.csv`
- **Response files:** `tests/results/responses/`
- **Visualization plots:** `tests/results/images/*.png`
- **Execution report:** `tests/results/test_execution_report.md`

### Compare Benchmarks

```sh
pytest-benchmark compare .benchmarks/<run>.json
```

### View Generated Images

```sh
# List all generated plots
ls -la tests/results/images/
```
## Comparing and Visualizing Routing Services

### Generate Benchmark Comparisons

```sh
python tests/scripts/benchmark_comparison.py
```

### Generate Service Comparison Data

```sh
python tests/scripts/modes_comparison.py
```

### Generate Routing Visualizations

```sh
# Generate plots
python tests/scripts/visualize_routing_comparison.py
```

### Generate Performance Comparisons

```sh
python tests/scripts/visualize_benchmark.py
```

## Coordinate Sets

The test suite uses different coordinate sets for comprehensive testing:

- **Aachen coordinates:** Local city routing (university, hospital, landmarks)
- **Mannheim coordinates:** Regional metropolitan area routing  
- **Germany coordinates:** Long-distance inter-city routes

## Services Tested

- **MOTIS:** Public transport routing
- **Google Maps:** Public transport and driving directions
- **OpenTripPlanner (OTP):** Public transport and driving (if available)
- **Valhalla:** Driving directions (if available)

## Usage Examples

```sh
# Quick test run with visualization
pytest tests/test_ab_routing_benchmarking.py -v -s
python tests/scripts/visualize_benchmark.py

# Full comprehensive analysis
./run_tests.sh

# View results
ls tests/results/
```