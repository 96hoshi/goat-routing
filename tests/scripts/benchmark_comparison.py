import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tests.utils.commons import IMAGES_DIR, RESULT_DIR


def load_benchmark_data(filepath="/app/tests/results/benchmark_results.csv"):
    """Load benchmark data from CSV file."""
    return pd.read_csv(filepath)


def create_summary_table(df, services=None):
    """Create comprehensive summary table for benchmark data."""
    if services is None:
        services = ["motis", "google", "otp"]

    summary_data = []

    for service in services:
        service_data = df[df["service"] == service]

        if service_data.empty:
            continue

        summary_row = {
            "Service": service.upper(),
            "Routes_Tested": len(service_data),
            "Avg_Response_Time_ms": round(service_data["avg_time_ms"].mean(), 1),
            "StdDev_Response_Time_ms": round(service_data["avg_time_ms"].std(), 1),
            "Min_Response_Time_ms": round(service_data["avg_time_ms"].min(), 1),
            "Max_Response_Time_ms": round(service_data["avg_time_ms"].max(), 1),
            "Avg_CPU_Usage_s": round(service_data["avg_cpu_s"].mean(), 4),
            "Avg_Memory_Delta_MB": round(service_data["avg_mem_mb_delta"].mean(), 2),
            "Avg_Response_Size_bytes": round(
                service_data["avg_response_size_bytes"].mean(), 0
            ),
            "Avg_Response_Size_KB": round(
                service_data["avg_response_size_bytes"].mean() / 1024, 1
            ),
            "Min_Response_Size_bytes": int(
                service_data["avg_response_size_bytes"].min()
            ),
            "Max_Response_Size_bytes": int(
                service_data["avg_response_size_bytes"].max()
            ),
            "Total_Test_Rounds": service_data["rounds"].iloc[0],
        }
        summary_data.append(summary_row)

    return pd.DataFrame(summary_data)


def save_summary_table(summary_df, filename="benchmark_summary_table.csv"):
    """Save summary table to CSV and print results."""
    summary_path = os.path.join(RESULT_DIR, filename)
    summary_df.to_csv(summary_path, index=False)

    print("✅ Benchmark Summary Table Created")
    print("=" * 60)
    print(summary_df.to_string(index=False))
    print(f"\n💾 Saved to: {summary_path}")

    return summary_path


def create_boxplots(df, services=None, colors=None):
    """Create box plots comparing all services across different metrics."""
    if services is None:
        services = ["motis", "google", "otp"]

    if colors is None:
        colors = {"motis": "#1f77b4", "google": "#ff7f0e", "otp": "#d62728"}

    # Ensure images directory exists
    os.makedirs(IMAGES_DIR, exist_ok=True)

    plt.figure(figsize=(12, 8))

    services_upper = [s.upper() for s in services]

    # 1. Response Time Comparison
    plt.subplot(2, 2, 1)
    response_times = [df[df["service"] == s]["avg_time_ms"].values for s in services]
    box_plot = plt.boxplot(response_times, patch_artist=True)
    for patch, service in zip(box_plot["boxes"], services, strict=True):
        patch.set_facecolor(colors[service])
    plt.xticks(range(1, len(services) + 1), services_upper)
    plt.title("Response Time Distribution")
    plt.ylabel("Time (ms)")
    plt.grid(True, alpha=0.3)

    # 2. Response Size Comparison
    plt.subplot(2, 2, 2)
    response_sizes = [
        df[df["service"] == s]["avg_response_size_bytes"].values / 1024
        for s in services
    ]
    box_plot = plt.boxplot(response_sizes, patch_artist=True)
    for patch, service in zip(box_plot["boxes"], services, strict=True):
        patch.set_facecolor(colors[service])
    plt.xticks(range(1, len(services) + 1), services_upper)
    plt.title("Response Size Distribution")
    plt.ylabel("Size (KB)")
    plt.grid(True, alpha=0.3)

    # 3. CPU Usage Comparison
    plt.subplot(2, 2, 3)
    cpu_usage = [df[df["service"] == s]["avg_cpu_s"].values for s in services]
    box_plot = plt.boxplot(cpu_usage, patch_artist=True)
    for patch, service in zip(box_plot["boxes"], services, strict=True):
        patch.set_facecolor(colors[service])
    plt.xticks(range(1, len(services) + 1), services_upper)
    plt.title("CPU Usage Distribution")
    plt.ylabel("CPU Time (s)")
    plt.grid(True, alpha=0.3)

    # 4. Memory Usage Comparison
    plt.subplot(2, 2, 4)
    memory_usage = [df[df["service"] == s]["avg_mem_mb_delta"].values for s in services]
    box_plot = plt.boxplot(memory_usage, patch_artist=True)
    for patch, service in zip(box_plot["boxes"], services, strict=True):
        patch.set_facecolor(colors[service])
    plt.xticks(range(1, len(services) + 1), services_upper)
    plt.title("Memory Delta Distribution")
    plt.ylabel("Memory Change (MB)")
    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save plot
    boxplot_path = os.path.join(IMAGES_DIR, "benchmark_comparison_boxplots.png")
    plt.savefig(boxplot_path, dpi=150, bbox_inches="tight")
    plt.close()

    print("✅ Created benchmark comparison box plots")
    return boxplot_path


def create_bar_charts(df, services=None, colors=None):
    """Create bar charts comparing average metrics across services."""
    if services is None:
        services = ["motis", "google", "otp"]

    if colors is None:
        colors = {"motis": "#1f77b4", "google": "#ff7f0e", "otp": "#d62728"}

    # Ensure images directory exists
    os.makedirs(IMAGES_DIR, exist_ok=True)

    plt.figure(figsize=(15, 10))

    # Prepare data for bar charts
    services_upper = [s.upper() for s in services]
    avg_response_time = [df[df["service"] == s]["avg_time_ms"].mean() for s in services]
    avg_response_size_kb = [
        df[df["service"] == s]["avg_response_size_bytes"].mean() / 1024
        for s in services
    ]
    avg_cpu_usage = [df[df["service"] == s]["avg_cpu_s"].mean() for s in services]

    # 1. Average Response Time
    plt.subplot(2, 2, 1)
    plt.bar(services_upper, avg_response_time, color=[colors[s] for s in services])
    plt.title("Average Response Time")
    plt.ylabel("Time (ms)")
    plt.grid(True, alpha=0.3)
    for i, v in enumerate(avg_response_time):
        plt.text(
            i, v + max(avg_response_time) * 0.01, f"{v:.1f}", ha="center", va="bottom"
        )

    # 2. Average Response Size
    plt.subplot(2, 2, 2)
    plt.bar(services_upper, avg_response_size_kb, color=[colors[s] for s in services])
    plt.title("Average Response Size")
    plt.ylabel("Size (KB)")
    plt.grid(True, alpha=0.3)
    for i, v in enumerate(avg_response_size_kb):
        plt.text(
            i,
            v + max(avg_response_size_kb) * 0.01,
            f"{v:.1f}",
            ha="center",
            va="bottom",
        )

    # 3. Average CPU Usage
    plt.subplot(2, 2, 3)
    plt.bar(services_upper, avg_cpu_usage, color=[colors[s] for s in services])
    plt.title("Average CPU Usage")
    plt.ylabel("CPU Time (s)")
    plt.grid(True, alpha=0.3)
    for i, v in enumerate(avg_cpu_usage):
        plt.text(i, v + max(avg_cpu_usage) * 0.01, f"{v:.3f}", ha="center", va="bottom")

    # 4. Performance Summary Score (lower is better)
    plt.subplot(2, 2, 4)
    # Normalize metrics (0-1 scale) and create composite score
    norm_time = np.array(avg_response_time) / max(avg_response_time)
    norm_size = np.array(avg_response_size_kb) / max(avg_response_size_kb)
    norm_cpu = np.array(avg_cpu_usage) / max(avg_cpu_usage)
    composite_score = (norm_time + norm_size + norm_cpu) / 3

    plt.bar(services_upper, composite_score, color=[colors[s] for s in services])
    plt.title("Composite Performance Score\n(Lower = Better)")
    plt.ylabel("Normalized Score")
    plt.grid(True, alpha=0.3)
    for i, v in enumerate(composite_score):
        plt.text(
            i, v + max(composite_score) * 0.01, f"{v:.3f}", ha="center", va="bottom"
        )

    plt.tight_layout()

    # Save plot
    barchart_path = os.path.join(IMAGES_DIR, "benchmark_comparison_bars.png")
    plt.savefig(barchart_path, dpi=150, bbox_inches="tight")
    plt.close()

    print("✅ Created benchmark comparison bar charts")
    return barchart_path


def main():
    """Main function to run the complete benchmark comparison analysis."""
    # Load data
    df = load_benchmark_data()

    # Create and save summary table
    summary_df = create_summary_table(df)
    summary_path = save_summary_table(summary_df)

    # Define service colors
    colors = {"motis": "#1f77b4", "google": "#ff7f0e", "otp": "#d62728"}

    # Create visualizations
    boxplot_path = create_boxplots(df, colors=colors)
    barchart_path = create_bar_charts(df, colors=colors)

    print("\n🎉 Benchmark comparison analysis complete!")
    print(f"📊 Summary table: {summary_path}")
    print(f"📈 Box plots: {boxplot_path}")
    print(f"📊 Bar charts: {barchart_path}")


if __name__ == "__main__":
    main()
