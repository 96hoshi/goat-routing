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
<<<<<<< HEAD
chmod +x run_tests.sh
./run_tests.sh

=======
chmod +x run_all_tests_and_generate_reports.sh
./run_all_tests_and_generate_reports.sh

# Or use Python version
python run_comprehensive_tests.py
```
>>>>>>> a21fa2d0b9b70e4331a83841622cbdb8e70b3d63

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
<<<<<<< HEAD
- **Visualization plots:** `tests/results/images/*.png`
=======
- **Visualization plots:** `tests/images/*.png`
>>>>>>> a21fa2d0b9b70e4331a83841622cbdb8e70b3d63
- **Execution report:** `tests/results/test_execution_report.md`

### Compare Benchmarks

```sh
pytest-benchmark compare .benchmarks/<run>.json
```

### View Generated Images

```sh
# List all generated plots
<<<<<<< HEAD
ls -la tests/results/images/
=======
ls -la tests/images/

# Open specific plots in browser (dev container)
"$BROWSER" tests/images/transport_duration_comparison_line.png
"$BROWSER" tests/images/driving_distance_comparison_scatter.png
"$BROWSER" tests/images/performance_comparison.png
```
>>>>>>> a21fa2d0b9b70e4331a83841622cbdb8e70b3d63

## Comparing and Visualizing Routing Services

### Generate Service Comparison Data

```sh
python tests/scripts/modes_comparison.py
```

### Generate Routing Visualizations

```sh
# Generate all plot types (line, scatter, bar, grouped bar)
python tests/scripts/visualize.py

# Generate specific plot types
python tests/scripts/visualize.py line,scatter

# Generate only bar charts
python tests/scripts/visualize.py bar,bar_grouped
```

### Generate Performance Comparisons

```sh
python tests/scripts/visualize_performances.py
```

### Generate Benchmark Comparisons

```sh
python tests/scripts/benchmark_comparison.py
```

## File Structure

```
tests/
├── scripts/
│   ├── modes_comparison.py       # Generate comparison CSV data
│   ├── visualize.py              # Create routing visualizations  
│   ├── visualize_performances.py # Create performance charts
│   └── benchmark_comparison.py   # Compare benchmark runs
├── results/
│   ├── benchmark_results.csv     # Performance metrics
│   ├── *_comparison.csv          # Service comparison data
│   ├── responses/                # Raw API responses
│   └── test_execution_report.md  # Comprehensive report
├── images/
│   ├── *_comparison_line.png     # Line plot visualizations
│   ├── *_comparison_scatter.png  # Scatter plot visualizations
│   ├── *_comparison_bar.png      # Bar chart visualizations
│   └── performance_comparison.png # Performance charts
└── coords/
    └── lists.py                  # Test coordinate sets
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

## Plot Types Generated

### Routing Comparisons
- **Line plots:** Show trends across routes
- **Scatter plots:** Display data distribution
- **Bar plots:** Compare individual metrics
- **Grouped bar plots:** Direct service comparison

### Performance Comparisons  
- **Response time:** Service speed comparison
- **Memory usage:** Resource utilization
- **CPU usage:** Processing efficiency
- **Response size:** Data payload analysis

## Usage Examples

```sh
# Quick test run with visualization
pytest tests/test_ab_routing_plausibility.py -v -s
python tests/scripts/visualize.py line

# Full comprehensive analysis
./run_all_tests_and_generate_reports.sh

# View results
ls tests/results/
<<<<<<< HEAD
=======
ls tests/images/
>>>>>>> a21fa2d0b9b70e4331a83841622cbdb8e70b3d63
"$BROWSER" tests/results/test_execution_report.md
```

## Troubleshooting

### No Data Found
- Check if services are properly configured in `src/core/config.py`
- Verify API keys are set in environment variables
- Run individual scripts to isolate issues

### Missing Plots
- Ensure CSV comparison files exist in `tests/results/`
- Run `modes_comparison.py` first to generate data
- Check log files in `logs/` directory

### Performance Issues
- Use smaller coordinate sets for faster testing
- Run specific test files instead of full suite
- Check service availability and response times