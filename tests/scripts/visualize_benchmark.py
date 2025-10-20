"""
Create comprehensive performance comparison plots by intelligently merging
container (server-side) and api (client-side) benchmark results, using a
dynamic configuration loaded from the test suite.
"""

import glob
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from tests.conftest import IMAGES_DIR, RESULT_DIR
from tests.utils.commons import get_service_config

# --- Configuration ---
DETAILED_PERFORMANCE_DIR = os.path.join(IMAGES_DIR, "detailed_performance")

# A simple map for service colors and labels
SERVICE_CONFIG = get_service_config()

# Create a color palette dictionary for seaborn from the dynamic config
COLOR_PALETTE = {service: config["color"] for service, config in SERVICE_CONFIG.items()}

# Set style for better visualizations
plt.style.use(
    "seaborn-v0_8-whitegrid"
    if "seaborn-v0_8-whitegrid" in plt.style.available
    else "default"
)

# --- DATA LOADING AND PREPARATION ---


def find_latest_benchmark_file(pattern: str) -> str | None:
    """Finds the most recent file in the result directory matching a pattern."""
    search_path = os.path.join(RESULT_DIR, pattern)
    files = glob.glob(search_path)
    return max(files, key=os.path.getctime) if files else None


def load_and_prepare_data():
    """Load, standardize, and merge benchmark CSVs into a single DataFrame."""
    container_file = find_latest_benchmark_file("container_benchmarks_*.csv")
    api_file = find_latest_benchmark_file("api_benchmarks_*.csv")

    if not container_file and not api_file:
        raise FileNotFoundError("No benchmark files found in 'reports/' directory.")

    df_container = pd.read_csv(container_file) if container_file else pd.DataFrame()
    df_api = pd.read_csv(api_file) if api_file else pd.DataFrame()

    all_dfs = []
    if not df_container.empty:
        print(f"📊 Loaded {len(df_container)} container benchmark records.")
        df_container["cost_type"] = "Server-Side"
        df_container.rename(
            columns={"container_cpu_s": "cpu_s", "container_mem_peak_mb": "memory_mb"},
            inplace=True,
        )
        all_dfs.append(df_container)

    if not df_api.empty:
        print(f"📊 Loaded {len(df_api)} API benchmark records.")
        df_api["cost_type"] = "Client-Side"
        df_api.rename(
            columns={"client_cpu_s": "cpu_s", "client_mem_mb_delta": "memory_mb"},
            inplace=True,
        )
        all_dfs.append(df_api)

    df_combined = pd.concat(all_dfs, ignore_index=True)
    df_combined["throughput_rps"] = 1000 / df_combined["avg_time_ms"]
    return df_combined


# --- INDIVIDUAL PLOTTING FUNCTIONS ---


def get_label(service_name):
    """Safely get a service label from the config."""
    return SERVICE_CONFIG.get(service_name, {"label": service_name.upper()})["label"]


def create_response_time_plot(df, ax):
    """Plots response time distribution."""
    sns.boxplot(
        x="service",
        y="avg_time_ms",
        data=df,
        ax=ax,
        palette=COLOR_PALETTE,
        hue="service",
        legend=False,
    )
    ax.set_xticklabels([get_label(s.get_text()) for s in ax.get_xticklabels()])
    ax.set_title("Response Time Distribution")
    ax.set_xlabel(None)
    ax.set_ylabel("Time (ms)")


def create_throughput_plot(df, ax):
    """Plots average throughput."""
    sns.barplot(
        x="service",
        y="throughput_rps",
        data=df,
        ax=ax,
        palette=COLOR_PALETTE,
        hue="service",
        legend=False,
        estimator=np.mean,
    )
    ax.set_xticklabels([get_label(s.get_text()) for s in ax.get_xticklabels()])
    ax.set_title("Average Throughput (Requests/Sec)")
    ax.set_xlabel(None)
    ax.set_ylabel("RPS (Higher is Better)")


def create_cpu_plot(df, ax):
    """Plots CPU usage, differentiating server vs. client cost."""
    sns.barplot(
        x="service",
        y="cpu_s",
        hue="cost_type",
        data=df,
        ax=ax,
        palette="viridis",
        estimator=np.mean,
    )
    ax.set_xticklabels([get_label(s.get_text()) for s in ax.get_xticklabels()])
    ax.set_title("CPU Usage: Server vs. Client Cost")
    ax.set_xlabel(None)
    ax.set_ylabel("CPU Time (s, log scale)")
    ax.set_yscale("log")
    ax.legend(title="Cost Type")


def create_memory_plot(df, ax):
    """Plots memory usage, differentiating server vs. client cost."""
    sns.barplot(
        x="service",
        y="memory_mb",
        hue="cost_type",
        data=df,
        ax=ax,
        palette="magma",
        estimator=np.mean,
    )
    ax.set_xticklabels([get_label(s.get_text()) for s in ax.get_xticklabels()])
    ax.set_title("Memory Usage: Peak Server vs. Client Delta")
    ax.set_xlabel(None)
    ax.set_ylabel("Memory (MB, log scale)")
    ax.set_yscale("log")
    ax.legend(title="Cost Type")


def create_efficiency_scatter_plot(df, ax):
    """Creates a scatter plot of CPU vs Memory, using custom markers."""
    ax.set_title("Resource Efficiency (CPU vs. Memory)")
    sns.scatterplot(
        data=df,
        x="cpu_s",
        y="memory_mb",
        hue="service",
        style="cost_type",
        palette=COLOR_PALETTE,
        ax=ax,
        s=100,  # size of markers
        alpha=0.8,
    )
    ax.set_xlabel("CPU Time (s, log scale)")
    ax.set_ylabel("Memory (MB, log scale)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.grid(True, which="both", ls="--", linewidth=0.5)


# --- MAIN DASHBOARD AND SAVING LOGIC ---


def save_plot(fig, ax, plot_func, df, filename):
    """Helper to save a single plot."""
    plot_func(df, ax)
    fig.tight_layout()  # Simple layout for single plots
    plot_path = os.path.join(DETAILED_PERFORMANCE_DIR, filename)
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)


def main():
    """Load, analyze, and visualize benchmark data."""
    try:
        print("🚀 Starting benchmark analysis...")
        os.makedirs(IMAGES_DIR, exist_ok=True)
        os.makedirs(DETAILED_PERFORMANCE_DIR, exist_ok=True)

        df = load_and_prepare_data()

        # Define all plots and their creation functions
        plot_definitions = {
            "01_response_time.png": create_response_time_plot,
            "02_throughput.png": create_throughput_plot,
            "03_cpu_usage.png": create_cpu_plot,
            "04_memory_usage.png": create_memory_plot,
            "05_efficiency_scatter.png": create_efficiency_scatter_plot,
        }

        # --- Create Main Dashboard ---
        fig, axes = plt.subplots(3, 2, figsize=(15, 15))
        fig.suptitle(
            "Routing Services Performance Dashboard", fontsize=16, fontweight="bold"
        )
        flat_axes = axes.flatten()

        for i, (_filename, plot_func) in enumerate(plot_definitions.items()):
            if i < len(flat_axes):
                plot_func(df, flat_axes[i])

        for i in range(len(plot_definitions), len(flat_axes)):
            flat_axes[i].set_visible(False)

        # Apply the corrected tight_layout call for the dashboard
        plt.tight_layout(rect=(0, 0.03, 1, 0.95))
        dashboard_path = os.path.join(IMAGES_DIR, "performance_dashboard.png")
        plt.savefig(dashboard_path, dpi=150)
        plt.close(fig)
        print(f"✅ Performance dashboard saved: {dashboard_path}")

        # --- Save Detailed Plots ---
        for filename, plot_func in plot_definitions.items():
            fig_single, ax_single = plt.subplots(figsize=(8, 6))
            save_plot(fig_single, ax_single, plot_func, df, filename)

        print(
            f"✅ {len(plot_definitions)} detailed plots saved in: {DETAILED_PERFORMANCE_DIR}"
        )

    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("💡 Run benchmark tests first using `pytest`.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
