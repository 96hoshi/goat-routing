"""
Benchmark Analysis Script
Processes benchmark results and saves aggregated statistics to CSV files.
"""

import csv
import os
from collections import defaultdict
from statistics import mean, median, stdev

# File paths
BENCHMARK_INPUT = "tests/results/benchmark_results.csv"
SUMMARY_OUTPUT = "tests/results/benchmark_summary.csv"
DETAILED_OUTPUT = "tests/results/benchmark_detailed_stats.csv"


def load_benchmark_data():
    """Load benchmark data from CSV file."""
    data = []

    if not os.path.exists(BENCHMARK_INPUT):
        print(f"Benchmark file not found: {BENCHMARK_INPUT}")
        return data

    with open(BENCHMARK_INPUT, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convert numeric fields
            try:
                row["avg_time_ms"] = (
                    float(row["avg_time_ms"]) if row["avg_time_ms"] else 0
                )
                row["avg_cpu_s"] = float(row["avg_cpu_s"]) if row["avg_cpu_s"] else 0
                row["avg_mem_mb"] = float(row["avg_mem_mb"]) if row["avg_mem_mb"] else 0
                row["response_size_bytes"] = (
                    int(row["response_size_bytes"]) if row["response_size_bytes"] else 0
                )
                data.append(row)
            except ValueError:
                continue

    return data


def calculate_service_stats(data):
    """Calculate statistics per service."""
    service_data = defaultdict(
        lambda: {"time_ms": [], "cpu_s": [], "mem_mb": [], "size_bytes": []}
    )

    # Group data by service
    for row in data:
        service = row["service"]
        service_data[service]["time_ms"].append(row["avg_time_ms"])
        service_data[service]["cpu_s"].append(row["avg_cpu_s"])
        service_data[service]["mem_mb"].append(row["avg_mem_mb"])
        service_data[service]["size_bytes"].append(row["response_size_bytes"])

    # Calculate statistics
    stats = []
    for service, metrics in service_data.items():
        if not metrics["time_ms"]:  # Skip if no data
            continue

        stat = {
            "service": service,
            "request_count": len(metrics["time_ms"]),
            # Time statistics
            "avg_time_ms": mean(metrics["time_ms"]),
            "median_time_ms": median(metrics["time_ms"]),
            "min_time_ms": min(metrics["time_ms"]),
            "max_time_ms": max(metrics["time_ms"]),
            "std_time_ms": (
                stdev(metrics["time_ms"]) if len(metrics["time_ms"]) > 1 else 0
            ),
            # CPU statistics
            "avg_cpu_s": mean(metrics["cpu_s"]),
            "median_cpu_s": median(metrics["cpu_s"]),
            "min_cpu_s": min(metrics["cpu_s"]),
            "max_cpu_s": max(metrics["cpu_s"]),
            "std_cpu_s": stdev(metrics["cpu_s"]) if len(metrics["cpu_s"]) > 1 else 0,
            # Memory statistics
            "avg_mem_mb": mean(metrics["mem_mb"]),
            "median_mem_mb": median(metrics["mem_mb"]),
            "min_mem_mb": min(metrics["mem_mb"]),
            "max_mem_mb": max(metrics["mem_mb"]),
            "std_mem_mb": stdev(metrics["mem_mb"]) if len(metrics["mem_mb"]) > 1 else 0,
            # Response size statistics
            "avg_size_bytes": mean(metrics["size_bytes"]),
            "median_size_bytes": median(metrics["size_bytes"]),
            "min_size_bytes": min(metrics["size_bytes"]),
            "max_size_bytes": max(metrics["size_bytes"]),
            "std_size_bytes": (
                stdev(metrics["size_bytes"]) if len(metrics["size_bytes"]) > 1 else 0
            ),
        }
        stats.append(stat)

    return stats


def save_summary_stats(stats):
    if not stats:
        return

    # Ensure results directory exists
    os.makedirs("tests/results", exist_ok=True)

    # Simple summary with key metrics
    summary_headers = [
        "service",
        "request_count",
        "avg_time_ms",
        "avg_cpu_s",
        "avg_mem_mb",
        "avg_size_bytes",
    ]

    with open(SUMMARY_OUTPUT, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=summary_headers)
        writer.writeheader()
        for stat in stats:
            summary_row = {key: stat[key] for key in summary_headers}
            writer.writerow(summary_row)


def save_detailed_stats(stats):
    """Save detailed statistics with all metrics."""
    if not stats:
        return

    # All available headers
    if stats:
        headers = list(stats[0].keys())

        with open(DETAILED_OUTPUT, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(stats)


def print_summary(stats):
    """Print summary to console."""
    if not stats:
        return

    print("\n📊 BENCHMARK SUMMARY")
    print("=" * 60)
    print(
        f"{'Service':<10} {'Requests':<8} {'Avg Time (ms)':<12} {'Avg CPU (s)':<10} {'Avg Mem (MB)':<12}"
    )
    print("-" * 60)

    for stat in stats:
        print(
            f"{stat['service']:<10} {stat['request_count']:<8} "
            f"{stat['avg_time_ms']:<12.2f} {stat['avg_cpu_s']:<10.4f} "
            f"{stat['avg_mem_mb']:<12.4f}"
        )

    print("=" * 60)


def main():
    """Main function to process benchmarks and save results."""
    data = load_benchmark_data()
    if not data:
        return

    stats = calculate_service_stats(data)

    save_summary_stats(stats)
    save_detailed_stats(stats)

    print_summary(stats)


if __name__ == "__main__":
    main()
