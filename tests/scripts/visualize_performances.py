import os

import matplotlib.pyplot as plt
import pandas as pd

from tests.conftest import BENCHMARK_FILE, IMAGES_DIR
from tests.utils.commons import get_available_services

AVAILABLE_SERVICES = get_available_services()


def load_data():
    """Load benchmark CSV data."""
    if not os.path.exists(BENCHMARK_FILE):
        raise FileNotFoundError(f"Benchmark file not found: {BENCHMARK_FILE}")

    df = pd.read_csv(BENCHMARK_FILE)
    print(f"📊 Loaded {len(df)} benchmark records")
    print(f"   Services: {df['service'].unique()}")
    return df


def create_performance_plots(df):
    """Create performance comparison plots."""
    os.makedirs(IMAGES_DIR, exist_ok=True)

    services = df["service"].unique()

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(
        "Routing Services Performance Comparison", fontsize=14, fontweight="bold"
    )

    # 1. Response Time
    ax1 = axes[0, 0]
    for service in services:
        if service in AVAILABLE_SERVICES:
            data = df[df["service"] == service]["avg_time_ms"]
            config = AVAILABLE_SERVICES[service]
            ax1.boxplot(
                [data],
                positions=[list(services).index(service)],
                patch_artist=True,
                boxprops={"facecolor": config["color"], "alpha": 0.7},
            )

    ax1.set_xticks(range(len(services)))
    ax1.set_xticklabels(
        [AVAILABLE_SERVICES.get(s, {"label": s.upper()})["label"] for s in services]
    )
    ax1.set_title("Response Time Distribution")
    ax1.set_ylabel("Time (ms)")
    ax1.grid(True, alpha=0.3)

    # 2. Response Size
    ax2 = axes[0, 1]
    avg_sizes = []
    colors = []
    labels = []

    for service in services:
        if service in AVAILABLE_SERVICES:
            avg_sizes.append(
                df[df["service"] == service]["avg_response_size_bytes"].mean() / 1024
            )
            colors.append(AVAILABLE_SERVICES[service]["color"])
            labels.append(AVAILABLE_SERVICES[service]["label"])

    bars = ax2.bar(labels, avg_sizes, color=colors, alpha=0.7)
    ax2.set_title("Average Response Size")
    ax2.set_ylabel("Size (KB)")
    ax2.grid(True, alpha=0.3)

    # Add value labels
    for bar, val in zip(bars, avg_sizes, strict=False):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(avg_sizes) * 0.01,
            f"{val:.1f}",
            ha="center",
            va="bottom",
        )

    # 3. CPU Usage
    ax3 = axes[1, 0]
    avg_cpu = []
    colors = []
    labels = []

    for service in services:
        if service in AVAILABLE_SERVICES:
            avg_cpu.append(df[df["service"] == service]["avg_cpu_s"].mean())
            colors.append(AVAILABLE_SERVICES[service]["color"])
            labels.append(AVAILABLE_SERVICES[service]["label"])

    bars = ax3.bar(labels, avg_cpu, color=colors, alpha=0.7)
    ax3.set_title("Average CPU Usage")
    ax3.set_ylabel("CPU Time (s)")
    ax3.grid(True, alpha=0.3)

    for bar, val in zip(bars, avg_cpu, strict=False):
        ax3.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(avg_cpu) * 0.01,
            f"{val:.3f}",
            ha="center",
            va="bottom",
        )

    # 4. Memory Usage
    ax4 = axes[1, 1]
    avg_mem = []
    colors = []
    labels = []

    for service in services:
        if service in AVAILABLE_SERVICES:
            avg_mem.append(df[df["service"] == service]["avg_mem_mb_delta"].mean())
            colors.append(AVAILABLE_SERVICES[service]["color"])
            labels.append(AVAILABLE_SERVICES[service]["label"])

    bars = ax4.bar(labels, avg_mem, color=colors, alpha=0.7)
    ax4.set_title("Average Memory Delta")
    ax4.set_ylabel("Memory (MB)")
    ax4.grid(True, alpha=0.3)

    for bar, val in zip(bars, avg_mem, strict=False):
        height_offset = abs(max(avg_mem)) * 0.1 if avg_mem else 0.1
        ax4.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + height_offset,
            f"{val:.2f}",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()

    plot_path = os.path.join(IMAGES_DIR, "performance_comparison.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"✅ Performance comparison saved: {plot_path}")
    return plot_path


def print_summary(df):
    """Print simple performance summary."""
    print("\n📊 PERFORMANCE SUMMARY")
    print("=" * 50)

    for service in df["service"].unique():
        if service in AVAILABLE_SERVICES:
            data = df[df["service"] == service]
            service_label = AVAILABLE_SERVICES[service]["label"]
            print(f"\n{service_label}:")
            print(f"  Routes tested: {len(data)}")
            print(f"  Avg time: {data['avg_time_ms'].mean():.1f} ms")
            print(f"  Avg CPU: {data['avg_cpu_s'].mean():.3f} s")
            print(f"  Avg size: {data['avg_response_size_bytes'].mean()/1024:.1f} KB")
            print(f"  Memory delta: {data['avg_mem_mb_delta'].mean():.2f} MB")


def main():
    """Create performance comparison plots from benchmark CSV."""
    try:
        df = load_data()
        plot_path = create_performance_plots(df)
        print_summary(df)

        print(f"📈 Chart saved: {plot_path}")

    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("Run benchmark tests first:")
        print("python -m pytest tests/test_ab_routing_benchmarking.py --benchmark-only")


if __name__ == "__main__":
    main()
