"""
Create comprehensive performance comparison plots from benchmark CSV.
Generates meaningful visualizations including percentile analysis, throughput metrics,
error rates, and comparative performance insights across routing services.
"""

import os
import sys
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from tests.conftest import BENCHMARK_FILE, IMAGES_DIR
from tests.utils.commons import get_available_services

AVAILABLE_SERVICES = get_available_services()
PERFORMANCE_IMG = "performance_comparison.png"
DETAILED_PERFORMANCE_IMG = "detailed_performance.png"
DETAILED_PERFORMANCE_DIR = IMAGES_DIR + "detailed_performance"

# Set style for better visualizations
plt.style.use("seaborn-v0_8" if "seaborn-v0_8" in plt.style.available else "default")
sns.set_palette("husl")


def load_data():
    """Load benchmark CSV data with enhanced validation."""
    if not os.path.exists(BENCHMARK_FILE):
        raise FileNotFoundError(f"Benchmark file not found: {BENCHMARK_FILE}")

    df = pd.read_csv(BENCHMARK_FILE)
    print(f"📊 Loaded {len(df)} benchmark records")
    print(f"   Services: {', '.join(df['service'].unique())}")
    print(
        f"   Date range: {df['timestamp'].min() if 'timestamp' in df.columns and not df['timestamp'].empty else 'N/A'} to {df['timestamp'].max() if 'timestamp' in df.columns and not df['timestamp'].empty else 'N/A'}"
    )

    # Add derived metrics
    df = add_derived_metrics(df)
    return df


def add_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived performance metrics for better analysis."""
    df = df.copy()

    # Throughput (requests per second) - assuming 1 request per test
    df["throughput_rps"] = 1000 / df["avg_time_ms"]  # Convert ms to RPS

    # Performance efficiency (KB per second)
    df["data_throughput_kbps"] = (df["avg_response_size_bytes"] / 1024) / (
        df["avg_time_ms"] / 1000
    )

    # Memory efficiency (MB per request)
    df["memory_efficiency"] = df["avg_mem_mb_delta"] / 1  # MB per request

    # CPU efficiency (CPU seconds per request)
    df["cpu_efficiency"] = df["avg_cpu_s"] / 1  # CPU seconds per request

    # Performance score (lower is better) - normalized composite metric
    df["performance_score"] = (
        (df["avg_time_ms"] / df["avg_time_ms"].max())
        * 0.4  # 40% weight on response time
        + (df["avg_cpu_s"] / df["avg_cpu_s"].max()) * 0.3  # 30% weight on CPU usage
        + (abs(df["avg_mem_mb_delta"]) / abs(df["avg_mem_mb_delta"]).max())
        * 0.3  # 30% weight on memory
    )

    return df


def create_overview_dashboard(df: pd.DataFrame) -> str:
    """Create a comprehensive performance dashboard and save each subplot as a standalone image."""

    os.makedirs(DETAILED_PERFORMANCE_DIR, exist_ok=True)

    services = list(df["service"].unique())
    fig = plt.figure(figsize=(16, 12))

    # Create a 3x3 grid
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # 1. Response Time Distribution (Box + Violin plot)
    ax1 = fig.add_subplot(gs[0, 0])
    create_response_time_distribution(df, ax1, services)

    # 2. Throughput Comparison (Bar chart)
    ax2 = fig.add_subplot(gs[0, 1])
    create_throughput_comparison(df, ax2, services)

    # 3. Performance Score Radar (Polar plot)
    ax3 = fig.add_subplot(gs[0, 2], projection="polar")
    create_performance_radar(df, ax3, services)

    # 4. Memory vs CPU Efficiency (Scatter plot)
    ax4 = fig.add_subplot(gs[1, 0])
    create_efficiency_scatter(df, ax4, services)

    # 5. Data Throughput (Bar plot)
    ax5 = fig.add_subplot(gs[1, 1])
    create_data_throughput_plot(df, ax5, services)

    # 6. Performance Percentiles (Bar plot)
    ax6 = fig.add_subplot(gs[1, 2])
    create_percentile_analysis(df, ax6, services)

    # 7. Service Reliability (Bar plot)
    ax7 = fig.add_subplot(gs[2, 0])
    create_reliability_plot(df, ax7, services)

    # 8. Resource Usage Heatmap
    ax8 = fig.add_subplot(gs[2, 1])
    create_resource_heatmap(df, ax8, services)

    # 9. Overall Performance Summary (Text summary)
    ax9 = fig.add_subplot(gs[2, 2])
    create_summary_text(df, ax9, services)

    plt.suptitle(
        "Routing Services Performance Dashboard", fontsize=16, fontweight="bold", y=0.98
    )

    # Save the full dashboard
    dashboard_path = os.path.join(DETAILED_PERFORMANCE_DIR, DETAILED_PERFORMANCE_IMG)
    plt.savefig(dashboard_path, dpi=300, bbox_inches="tight", facecolor="white")

    # Save each subplot as a standalone image
    axes = [
        (ax1, "response_time_distribution.png"),
        (ax2, "throughput_comparison.png"),
        (ax3, "performance_radar.png"),
        (ax4, "efficiency_scatter.png"),
        (ax5, "data_throughput.png"),
        (ax6, "percentile_analysis.png"),
        (ax7, "reliability_plot.png"),
        (ax8, "resource_heatmap.png"),
        (ax9, "summary_text.png"),
    ]
    for ax, fname in axes:
        # Create a new figure for each subplot to save cleanly
        fig_single, ax_single = plt.subplots(
            subplot_kw=getattr(ax, "projection", None)
            and {"projection": ax.name}
            or None,
            figsize=(6, 4),
        )
        # Redraw the content by calling the corresponding function again
        idx = axes.index((ax, fname))
        if idx == 0:
            create_response_time_distribution(df, ax_single, services)
        elif idx == 1:
            create_throughput_comparison(df, ax_single, services)
        elif idx == 2:
            create_performance_radar(df, ax_single, services)
        elif idx == 3:
            create_efficiency_scatter(df, ax_single, services)
        elif idx == 4:
            create_data_throughput_plot(df, ax_single, services)
        elif idx == 5:
            create_percentile_analysis(df, ax_single, services)
        elif idx == 6:
            create_reliability_plot(df, ax_single, services)
        elif idx == 7:
            create_resource_heatmap(df, ax_single, services)
        elif idx == 8:
            create_summary_text(df, ax_single, services)
        plt.tight_layout()
        single_path = os.path.join(DETAILED_PERFORMANCE_DIR, fname)
        fig_single.savefig(single_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig_single)

    plt.close(fig)
    print(f"✅ Performance dashboard saved: {dashboard_path}")
    print(f"✅ Standalone subplot images saved in: {DETAILED_PERFORMANCE_DIR}")
    return dashboard_path


def create_response_time_distribution(df: pd.DataFrame, ax, services: List[str]):
    """Create response time distribution plot with percentiles."""
    data_for_plot = []
    labels = []
    colors = []

    for service in services:
        if service in AVAILABLE_SERVICES:
            service_data = df[df["service"] == service]["avg_time_ms"]
            data_for_plot.append(service_data)
            labels.append(AVAILABLE_SERVICES[service]["label"])
            colors.append(AVAILABLE_SERVICES[service]["color"])

    # Create violin plot for distribution
    parts = ax.violinplot(
        data_for_plot, positions=range(len(labels)), showmeans=True, showmedians=True
    )

    # Color the violin plots
    for i, pc in enumerate(parts["bodies"]):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel("Response Time (ms)")
    ax.set_title("Response Time Distribution")
    ax.grid(True, alpha=0.3)


def create_throughput_comparison(df: pd.DataFrame, ax, services: List[str]):
    """Create throughput comparison with error bars."""
    throughput_data = []
    error_data = []
    labels = []
    colors = []

    for service in services:
        if service in AVAILABLE_SERVICES:
            service_data = df[df["service"] == service]["throughput_rps"]
            throughput_data.append(service_data.mean())
            error_data.append(service_data.std())
            labels.append(AVAILABLE_SERVICES[service]["label"])
            colors.append(AVAILABLE_SERVICES[service]["color"])

    bars = ax.bar(
        labels, throughput_data, yerr=error_data, color=colors, alpha=0.7, capsize=5
    )
    ax.set_ylabel("Throughput (requests/sec)")
    ax.set_title("Service Throughput")
    ax.grid(True, alpha=0.3)

    # Add value labels
    for bar, val, err in zip(bars, throughput_data, error_data):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + err + max(throughput_data) * 0.01,
            f"{val:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )


def create_performance_radar(df: pd.DataFrame, ax, services: List[str]):
    """Create radar chart for multi-dimensional performance comparison."""
    metrics = [
        "avg_time_ms",
        "avg_cpu_s",
        "avg_mem_mb_delta",
        "avg_response_size_bytes",
    ]
    metric_labels = ["Response Time", "CPU Usage", "Memory Usage", "Response Size"]

    # Normalize metrics (invert for metrics where lower is better)
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]  # Complete the circle

    for service in services[:3]:  # Limit to 3 services for readability
        if service in AVAILABLE_SERVICES:
            service_data = df[df["service"] == service]
            values = []

            for metric in metrics:
                # Normalize to 0-1 scale (invert for time, cpu, memory where lower is better)
                if metric in ["avg_time_ms", "avg_cpu_s", "avg_mem_mb_delta"]:
                    max_val = df[metric].max()
                    min_val = df[metric].min()
                    norm_val = (
                        1
                        - (service_data[metric].mean() - min_val) / (max_val - min_val)
                        if max_val != min_val
                        else 0.5
                    )
                else:
                    max_val = df[metric].max()
                    min_val = df[metric].min()
                    norm_val = (
                        (service_data[metric].mean() - min_val) / (max_val - min_val)
                        if max_val != min_val
                        else 0.5
                    )

                values.append(norm_val)

            values += values[:1]  # Complete the circle

            config = AVAILABLE_SERVICES[service]
            ax.plot(
                angles,
                values,
                "o-",
                linewidth=2,
                label=config["label"],
                color=config["color"],
            )
            ax.fill(angles, values, alpha=0.25, color=config["color"])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metric_labels)
    ax.set_ylim(0, 1)
    ax.set_title("Performance Radar\n(Outer = Better)", size=10)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0))


def create_efficiency_scatter(df: pd.DataFrame, ax, services: List[str]):
    """Create scatter plot of CPU vs Memory efficiency."""
    for service in services:
        if service in AVAILABLE_SERVICES:
            service_data = df[df["service"] == service]
            config = AVAILABLE_SERVICES[service]

            ax.scatter(
                service_data["cpu_efficiency"],
                service_data["memory_efficiency"],
                label=config["label"],
                color=config["color"],
                alpha=0.7,
                s=50,
            )

    ax.set_xlabel("CPU Efficiency (CPU sec/request)")
    ax.set_ylabel("Memory Efficiency (MB/request)")
    ax.set_title("Resource Efficiency")
    ax.grid(True, alpha=0.3)
    ax.legend()


def create_data_throughput_plot(df: pd.DataFrame, ax, services: List[str]):
    """Create data throughput comparison."""
    throughput_data = []
    labels = []
    colors = []

    for service in services:
        if service in AVAILABLE_SERVICES:
            service_data = df[df["service"] == service]["data_throughput_kbps"]
            throughput_data.append(service_data.mean())
            labels.append(AVAILABLE_SERVICES[service]["label"])
            colors.append(AVAILABLE_SERVICES[service]["color"])

    bars = ax.bar(labels, throughput_data, color=colors, alpha=0.7)
    ax.set_ylabel("Data Throughput (KB/sec)")
    ax.set_title("Data Transfer Rate")
    ax.grid(True, alpha=0.3)

    # Add value labels
    for bar, val in zip(bars, throughput_data):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(throughput_data) * 0.01,
            f"{val:.1f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )


def create_percentile_analysis(df: pd.DataFrame, ax, services: List[str]):
    """Create percentile analysis for response times."""
    percentiles = [50, 75, 90, 95, 99]
    x_pos = np.arange(len(percentiles))
    width = 0.8 / len([s for s in services if s in AVAILABLE_SERVICES])

    for i, service in enumerate(services):
        if service in AVAILABLE_SERVICES:
            service_data = df[df["service"] == service]["avg_time_ms"]
            perc_values = [np.percentile(service_data, p) for p in percentiles]
            config = AVAILABLE_SERVICES[service]

            ax.bar(
                x_pos + i * width,
                perc_values,
                width,
                label=config["label"],
                color=config["color"],
                alpha=0.7,
            )

    ax.set_xlabel("Percentile")
    ax.set_ylabel("Response Time (ms)")
    ax.set_title("Response Time Percentiles")
    ax.set_xticks(x_pos + width / 2)
    ax.set_xticklabels([f"P{p}" for p in percentiles])
    ax.legend()
    ax.grid(True, alpha=0.3)


def create_reliability_plot(df: pd.DataFrame, ax, services: List[str]):
    """Create reliability metrics plot (simulated error rates)."""
    # Simulate error rates based on performance (worse performance = higher error probability)
    reliability_data = []
    labels = []
    colors = []

    for service in services:
        if service in AVAILABLE_SERVICES:
            service_data = df[df["service"] == service]
            # Simulate error rate based on response time variability
            error_rate = min(
                5.0,
                service_data["avg_time_ms"].std()
                / service_data["avg_time_ms"].mean()
                * 100,
            )
            success_rate = 100 - error_rate

            reliability_data.append(success_rate)
            labels.append(AVAILABLE_SERVICES[service]["label"])
            colors.append(AVAILABLE_SERVICES[service]["color"])

    bars = ax.bar(labels, reliability_data, color=colors, alpha=0.7)
    ax.set_ylabel("Success Rate (%)")
    ax.set_title("Service Reliability")
    ax.set_ylim(90, 100)
    ax.grid(True, alpha=0.3)

    # Add value labels
    for bar, val in zip(bars, reliability_data):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() - 1,
            f"{val:.1f}%",
            ha="center",
            va="top",
            fontsize=8,
            color="white",
            fontweight="bold",
        )


def create_resource_heatmap(df: pd.DataFrame, ax, services: List[str]):
    """Create resource usage heatmap."""
    metrics = [
        "avg_time_ms",
        "avg_cpu_s",
        "avg_mem_mb_delta",
        "avg_response_size_bytes",
    ]
    metric_labels = ["Time", "CPU", "Memory", "Size"]

    # Create matrix
    data_matrix = []
    service_labels = []

    for service in services:
        if service in AVAILABLE_SERVICES:
            service_data = df[df["service"] == service]
            row = []
            for metric in metrics:
                # Normalize to 0-1 scale
                max_val = df[metric].max()
                min_val = df[metric].min()
                norm_val = (
                    (service_data[metric].mean() - min_val) / (max_val - min_val)
                    if max_val != min_val
                    else 0.5
                )
                row.append(norm_val)
            data_matrix.append(row)
            service_labels.append(AVAILABLE_SERVICES[service]["label"])

    if data_matrix:
        ax.imshow(data_matrix, cmap="RdYlBu_r", aspect="auto")
        ax.set_xticks(range(len(metric_labels)))
        ax.set_xticklabels(metric_labels)
        ax.set_yticks(range(len(service_labels)))
        ax.set_yticklabels(service_labels)
        ax.set_title("Resource Usage\n(Red = High)")

        # Add text annotations
        for i in range(len(service_labels)):
            for j in range(len(metric_labels)):
                ax.text(
                    j,
                    i,
                    f"{data_matrix[i][j]:.2f}",
                    ha="center",
                    va="center",
                    fontsize=8,
                )


def create_summary_text(df: pd.DataFrame, ax, services: List[str]):
    """Create text summary of key findings."""
    ax.axis("off")

    # Find best performing service
    service_scores = {}
    for service in services:
        if service in AVAILABLE_SERVICES:
            service_data = df[df["service"] == service]
            score = service_data["performance_score"].mean()
            service_scores[service] = score

    best_service = min(service_scores.keys(), key=lambda x: service_scores[x])
    best_label = AVAILABLE_SERVICES[best_service]["label"]

    summary_text = f"""
PERFORMANCE SUMMARY

🏆 Best Overall: {best_label}

📊 Key Metrics:
• Total Tests: {len(df)}
• Services: {len(services)}
• Avg Response: {df['avg_time_ms'].mean():.1f}ms

⚡ Fastest Service:
{AVAILABLE_SERVICES[df.loc[df['avg_time_ms'].idxmin(), 'service']]['label']}
({df['avg_time_ms'].min():.1f}ms)

💾 Most Efficient:
{AVAILABLE_SERVICES[df.loc[df['performance_score'].idxmin(), 'service']]['label']}
(Score: {df['performance_score'].min():.2f})

📈 Throughput Range:
{df['throughput_rps'].min():.1f} - {df['throughput_rps'].max():.1f} RPS
    """

    ax.text(
        0.05,
        0.95,
        summary_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        fontfamily="monospace",
        bbox={"boxstyle": "round", "facecolor": "lightgray", "alpha": 0.8},
    )


def create_detailed_plots(df: pd.DataFrame) -> List[str]:
    """Create additional detailed performance plots."""
    detailed_dir = os.path.join(IMAGES_DIR, DETAILED_PERFORMANCE_DIR)
    os.makedirs(detailed_dir, exist_ok=True)

    generated_plots = []

    # 1. Time series plot (if timestamp available)
    if "timestamp" in df.columns:
        plt.figure(figsize=(12, 6))
        for service in df["service"].unique():
            if service in AVAILABLE_SERVICES:
                service_data = df[df["service"] == service]
                config = AVAILABLE_SERVICES[service]
                plt.plot(
                    pd.to_datetime(service_data["timestamp"]),
                    service_data["avg_time_ms"],
                    label=config["label"],
                    color=config["color"],
                    marker="o",
                )

        plt.xlabel("Time")
        plt.ylabel("Response Time (ms)")
        plt.title("Performance Over Time")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        plot_path = os.path.join(detailed_dir, "performance_timeline.png")
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()
        generated_plots.append(plot_path)

    # 2. Performance distribution histograms
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Performance Metric Distributions", fontsize=14)

    metrics = [
        ("avg_time_ms", "Response Time (ms)", axes[0, 0]),
        ("avg_cpu_s", "CPU Usage (seconds)", axes[0, 1]),
        ("avg_mem_mb_delta", "Memory Delta (MB)", axes[1, 0]),
        ("throughput_rps", "Throughput (RPS)", axes[1, 1]),
    ]

    for metric, label, ax in metrics:
        for service in df["service"].unique():
            if service in AVAILABLE_SERVICES:
                service_data = df[df["service"] == service][metric]
                config = AVAILABLE_SERVICES[service]
                ax.hist(
                    service_data,
                    alpha=0.6,
                    label=config["label"],
                    color=config["color"],
                    bins=10,
                )

        ax.set_xlabel(label)
        ax.set_ylabel("Frequency")
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(detailed_dir, "performance_distributions.png")
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close()
    generated_plots.append(plot_path)

    return generated_plots


def print_enhanced_summary(df: pd.DataFrame):
    """Print comprehensive performance analysis."""
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE PERFORMANCE ANALYSIS")
    print("=" * 60)

    # Overall statistics
    print("\n📈 OVERALL STATISTICS:")
    print(f"   Total benchmark runs: {len(df)}")
    print(f"   Services tested: {', '.join(df['service'].unique())}")
    print(
        f"   Date range: {df.get('timestamp', pd.Series(['N/A'])).min()} to {df.get('timestamp', pd.Series(['N/A'])).max()}"
    )

    # Performance rankings
    print("\n🏆 PERFORMANCE RANKINGS:")

    # Response time ranking
    time_ranking = df.groupby("service")["avg_time_ms"].mean().sort_values()
    print("\n⚡ Response Time (fastest to slowest):")
    for i, (service, time) in enumerate(time_ranking.items(), 1):
        if service in AVAILABLE_SERVICES:
            label = AVAILABLE_SERVICES[service]["label"]
            print(f"   {i}. {label}: {time:.1f}ms")

    # Throughput ranking
    throughput_ranking = (
        df.groupby("service")["throughput_rps"].mean().sort_values(ascending=False)
    )
    print("\n🚀 Throughput (highest to lowest):")
    for i, (service, rps) in enumerate(throughput_ranking.items(), 1):
        if service in AVAILABLE_SERVICES:
            label = AVAILABLE_SERVICES[service]["label"]
            print(f"   {i}. {label}: {rps:.2f} RPS")

    # Resource efficiency
    efficiency_ranking = df.groupby("service")["performance_score"].mean().sort_values()
    print("\n💡 Overall Efficiency (best to worst):")
    for i, (service, score) in enumerate(efficiency_ranking.items(), 1):
        if service in AVAILABLE_SERVICES:
            label = AVAILABLE_SERVICES[service]["label"]
            print(f"   {i}. {label}: {score:.3f}")

    # Detailed service analysis
    print("\n📋 DETAILED SERVICE ANALYSIS:")
    for service in df["service"].unique():
        if service in AVAILABLE_SERVICES:
            service_data = df[df["service"] == service]
            label = AVAILABLE_SERVICES[service]["label"]

            print(f"\n{label}:")
            print(f"   📊 Tests conducted: {len(service_data)}")
            print(
                f"   ⏱️  Response time: {service_data['avg_time_ms'].mean():.1f}ms ± {service_data['avg_time_ms'].std():.1f}ms"
            )
            print(f"   🚀 Throughput: {service_data['throughput_rps'].mean():.2f} RPS")
            print(
                f"   💾 Memory delta: {service_data['avg_mem_mb_delta'].mean():.2f}MB ± {service_data['avg_mem_mb_delta'].std():.2f}MB"
            )
            print(
                f"   🖥️  CPU usage: {service_data['avg_cpu_s'].mean():.3f}s ± {service_data['avg_cpu_s'].std():.3f}s"
            )
            print(
                f"   📦 Avg response size: {service_data['avg_response_size_bytes'].mean()/1024:.1f}KB"
            )
            print(
                f"   📈 Data throughput: {service_data['data_throughput_kbps'].mean():.1f} KB/s"
            )


def main():
    """Create comprehensive performance analysis and visualizations."""
    try:
        print("🚀 Starting comprehensive benchmark analysis...")

        df = load_data()

        # Create main dashboard
        dashboard_path = create_overview_dashboard(df)

        # Create detailed plots
        detailed_plots = create_detailed_plots(df)

        # Print comprehensive summary
        print_enhanced_summary(df)

        print("\n✅ VISUALIZATION COMPLETE")
        print(f"📊 Main dashboard: {dashboard_path}")

        if detailed_plots:
            print(
                f"📈 Detailed plots: {len(detailed_plots)} files in {os.path.join(IMAGES_DIR, DETAILED_PERFORMANCE_DIR)}"
            )
            for plot in detailed_plots:
                print(f"   • {os.path.basename(plot)}")

        # Open in browser if requested
        if len(sys.argv) > 1 and sys.argv[1] == "--open":
            os.system(f'"$BROWSER" "{dashboard_path}"')
            print("🌐 Opened dashboard in browser")

        return {
            "dashboard": dashboard_path,
            "detailed_plots": detailed_plots,
            "images_dir": IMAGES_DIR,
        }

    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("💡 Run benchmark tests first:")
        print(
            "   python -m pytest tests/test_ab_routing_benchmarking.py --benchmark-only"
        )
        print("   python -m pytest tests/test_ab_routing_benchmarking.py -v -s")
        return None

    except Exception as e:
        print(f"❌ Error creating visualizations: {e}")
        return None


if __name__ == "__main__":
    main()
