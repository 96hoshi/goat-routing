"""
Script to visualize and compare routing performance metrics across different services and modes.
Generates plots for transport and driving modes, including line, scatter, bar, and grouped bar charts.
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tests.conftest import IMAGES_DIR, RESULT_DIR
from tests.scripts.modes_comparison import (
    DRIVING_COMPARISON_CSV,
    TRANSPORT_COMPARISON_CSV,
)
from tests.test_otp_routing import OTP_DRIVING_CSV_FILE, OTP_TRANSPORT_CSV_FILE
from tests.utils.commons import get_available_services

AVAILABLE_SERVICES = get_available_services()
MODES_AND_VEHICLES_CSV = "modes_and_vehicle_lines_transport.csv"

# Plot type configuration
PLOT_TYPES = {
    "line": {"marker": True, "line": True},
    "scatter": {"marker": True, "line": False},
    "bar": {"marker": False, "line": False},
    "bar_grouped": {"marker": False, "line": False},
}

# Metrics configuration with default plot types
METRICS_CONFIG = [
    ("num_routes", "Number of Routes", "Number of Routes", 1, "bar"),
    ("response_size", "Response Size (KB)", "Response Size", 1024, "scatter"),
    ("duration", "Duration (minutes)", "Duration", 60, "line"),
    ("distance", "Distance (km)", "Distance", 1000, "line"),
]

# Mode configuration
MODE_CONFIG = {
    "transport": {
        "services": ["motis", "google", "otp"],
        "comparison_file": TRANSPORT_COMPARISON_CSV,
        "otp_file": OTP_TRANSPORT_CSV_FILE,
        "otp_columns": {
            "duration": "duration_s",
            "distance": "distance_m",
            "response_size": "response_size_b",
            "num_routes": "num_routes",
        },
        "emoji": "🚌",
    },
    "driving": {
        "services": ["google", "otp", "valhalla"],
        "comparison_file": DRIVING_COMPARISON_CSV,
        "otp_file": OTP_DRIVING_CSV_FILE,
        "otp_columns": {
            "duration": "duration_s",
            "distance": "distance_m",
            "response_size": "response_size_b",
            "num_routes": "num_routes",
        },
        "emoji": "🚗",
    },
}


def clean_list_string(x):
    """Convert string representation of list to pipe-separated format."""
    if pd.notna(x) and x != "[]":
        return x.strip("[]").replace("'", "").replace('"', "").replace(", ", "|")
    return ""


def load_and_merge_data(mode=None):
    """Load and merge data from the CSV files WITHOUT modifying originals."""
    if mode not in MODE_CONFIG:
        return pd.DataFrame()

    config = MODE_CONFIG[mode]
    comparison_file = os.path.join(RESULT_DIR, config["comparison_file"])
    otp_file = os.path.join(RESULT_DIR, config["otp_file"])

    # Load comparison data
    if not os.path.exists(comparison_file):
        print(f"⚠️ Comparison file not found: {comparison_file}")
        return pd.DataFrame()

    print(f"📊 Loading {mode} comparison data")
    merged_df = pd.read_csv(comparison_file, dtype=str, on_bad_lines="skip").copy()
    print(f"   Found {len(merged_df)} routes in {mode} comparison")

    # Load and merge OTP data if available
    if not os.path.exists(otp_file):
        return merged_df

    print(f"📊 Loading OTP {mode} routes data")
    try:
        otp_df = pd.read_csv(otp_file).copy()
    except Exception as e:
        print(f"❌ Error loading OTP data: {e}")
        return merged_df

    # Merge OTP data
    min_rows = min(len(merged_df), len(otp_df))
    merged_df = merged_df.iloc[:min_rows].copy()

    # Add OTP columns with mode suffix
    for metric, otp_col in config["otp_columns"].items():
        if otp_col in otp_df.columns:
            merged_df[f"otp_{metric}_{mode}"] = pd.to_numeric(
                otp_df[otp_col].iloc[:min_rows], errors="coerce"
            )

    # Add modes and vehicle_lines if available
    for col in ["modes", "vehicle_lines"]:
        if col in otp_df.columns:
            merged_df[f"otp_{col}_{mode}"] = (
                otp_df[col].iloc[:min_rows].apply(clean_list_string)
            )

    print(f"   Merged OTP {mode} data ({min_rows} rows)")
    return merged_df


def plot_metric(
    route_labels,
    df,
    services,
    metric,
    ylabel,
    title,
    base_filename,
    unit_conversion=1,
    mode_suffix="",
    plot_type="line",
):
    """Plot a metric for selected services with different plot types."""
    plt.figure(figsize=(14, 8))
    services_plotted = []

    # Create numeric x-positions for proper ordering
    x_positions = np.array(range(len(route_labels)))

    if plot_type == "bar_grouped":
        # For grouped bar charts, calculate bar positions
        bar_width = 0.8 / len(services)
        bar_positions = {}

    for i, service in enumerate(services):
        if service not in AVAILABLE_SERVICES:
            continue

        column = (
            f"{service}_{metric}_{mode_suffix}"
            if mode_suffix
            else f"{service}_{metric}"
        )

        if column not in df.columns:
            continue

        config = AVAILABLE_SERVICES[service]
        values = pd.to_numeric(df[column], errors="coerce")

        # Apply unit conversion
        if unit_conversion != 1:
            values = values / unit_conversion

        # Handle different plot types
        if plot_type == "line":
            # Filter out invalid values but keep x-positions aligned
            plot_x = []
            plot_y = []
            for j, value in enumerate(values):
                if pd.notna(value) and value > 0:
                    plot_x.append(x_positions[j])
                    plot_y.append(value)

            if plot_x:
                plt.plot(
                    plot_x,
                    plot_y,
                    label=config["label"],
                    marker=config["marker"],
                    color=config["color"],
                    linewidth=2,
                    markersize=8,
                )

        elif plot_type == "scatter":
            # Scatter plot - show all valid points
            valid_mask = pd.notna(values) & (values > 0)
            valid_x = x_positions[valid_mask]
            valid_y = values[valid_mask]

            if len(valid_x) > 0:
                plt.scatter(
                    valid_x,
                    valid_y,
                    label=config["label"],
                    marker=config["marker"],
                    color=config["color"],
                    s=100,
                    alpha=0.7,
                )

        elif plot_type == "bar":
            # Individual bar chart for each service
            valid_mask = pd.notna(values) & (values > 0)
            valid_x = x_positions[valid_mask]
            valid_y = values[valid_mask]

            if len(valid_x) > 0:
                plt.bar(
                    valid_x,
                    valid_y,
                    label=config["label"],
                    color=config["color"],
                    alpha=0.7,
                    width=0.6,
                )

        elif plot_type == "bar_grouped":
            # Grouped bar chart
            if i == 0:
                bar_positions = {
                    service: x_positions + (j - len(services) / 2 + 0.5) * bar_width  # type: ignore
                    for j, service in enumerate(services)
                }

            valid_mask = pd.notna(values) & (values > 0)
            if valid_mask.any():
                bar_x = bar_positions[service][valid_mask]  # type: ignore
                bar_y = values[valid_mask]

                plt.bar(
                    bar_x,
                    bar_y,
                    label=config["label"],
                    color=config["color"],
                    alpha=0.7,
                    width=bar_width,  # type: ignore
                )

        services_plotted.append(service)

    if not services_plotted:
        plt.close()
        print(f"⚠️ No valid data for {base_filename} ({plot_type})")
        return None

    # Set x-axis with proper integer positions and labels
    plt.xticks(x_positions, route_labels, rotation=45, ha="right")
    plt.ylabel(ylabel)
    plt.title(f"{title} ({plot_type.replace('_', ' ').title()} Plot)")
    plt.legend(loc="best", fontsize=12)

    if plot_type in ["scatter", "line"]:
        plt.grid(axis="y", linestyle="--", alpha=0.7)
    elif plot_type in ["bar", "bar_grouped"]:
        plt.grid(axis="y", linestyle="--", alpha=0.3)

    plt.tight_layout()

    # Create unique filename with plot type
    filename = f"{base_filename}_{plot_type}.png"
    os.makedirs(IMAGES_DIR, exist_ok=True)
    plt.savefig(os.path.join(IMAGES_DIR, filename), dpi=300, bbox_inches="tight")
    plt.close()

    print(f"✅ Generated: {filename}")
    return filename


def generate_mode_plots(df, mode, plot_types=None):
    """Generate all plots for a specific mode with different plot types."""
    if mode not in MODE_CONFIG:
        return []

    config = MODE_CONFIG[mode]

    # Find available services for this mode
    available_services = [
        service
        for service in config["services"]
        if f"{service}_duration_{mode}" in df.columns
    ]

    if not available_services:
        print(f"⚠️ No {mode} services found in data")
        return []

    print(f"{config['emoji']} Generating {mode} plots for: {available_services}")

    route_labels = [f"Route {i+1}" for i in range(len(df))]
    service_labels = " vs ".join(
        [AVAILABLE_SERVICES[s]["label"] for s in available_services]
    )
    generated_plots = []

    for (
        metric,
        ylabel,
        title_base,
        unit_conversion,
        default_plot_type,
    ) in METRICS_CONFIG:
        title = f"{title_base} Comparison - {mode.title()} Mode ({service_labels})"
        base_filename = f"{mode}_{metric}_comparison"

        # Use provided plot types or default
        types_to_generate = plot_types or [default_plot_type]

        for plot_type in types_to_generate:
            if plot_type not in PLOT_TYPES:
                print(f"⚠️ Unknown plot type: {plot_type}")
                continue

            filename = plot_metric(
                route_labels,
                df,
                available_services,
                metric,
                ylabel,
                title,
                base_filename,
                unit_conversion,
                mode,
                plot_type,
            )

            if filename:
                generated_plots.append(filename)

    return generated_plots


def save_comparison_table(df, mode_suffix=""):
    """Save comparison table for transport mode only."""
    if mode_suffix != "transport":
        print(f"⏭️ Skipping comparison table for {mode_suffix} mode")
        return

    # Create a copy to avoid modifying original
    table_df = df.copy()

    available_services = [
        service
        for service in AVAILABLE_SERVICES.keys()
        if f"{service}_duration_transport" in table_df.columns
    ]

    if not available_services:
        print("⚠️ No transport services found for table generation")
        return

    route_labels = [f"Route {i+1}" for i in range(len(table_df))]
    base_metrics = [
        "modes",
        "vehicle_lines",
        "duration",
        "distance",
        "num_routes",
        "response_size",
    ]

    table_rows = [
        f"{service}_{metric}_transport"
        for service in available_services
        for metric in base_metrics
        if f"{service}_{metric}_transport" in table_df.columns
    ]

    if not table_rows:
        return

    table_data = table_df[table_rows].T
    table_data.columns = route_labels

    table_path = os.path.join(RESULT_DIR, MODES_AND_VEHICLES_CSV)
    table_data.to_csv(table_path)
    print(f"✅ Saved transport comparison table: {MODES_AND_VEHICLES_CSV}")


def convert_numeric_columns(df, services, mode):
    """Convert specified columns to numeric format WITHOUT modifying original."""
    df_processed = df.copy()

    cols_to_convert = [
        f"{service}_{metric}_{mode}"
        for service in services
        for metric in ["num_routes", "response_size", "duration", "distance"]
        if f"{service}_{metric}_{mode}" in df_processed.columns
    ]

    if cols_to_convert:
        df_processed[cols_to_convert] = df_processed[cols_to_convert].apply(
            pd.to_numeric, errors="coerce"
        )

    return df_processed


def generate_all_comparisons(plot_types=None):
    """Generate comprehensive comparison plots with specified plot types."""
    print("🎨 Generating comprehensive routing comparisons...")
    if plot_types:
        print(f"📊 Plot types: {', '.join(plot_types)}")
    print("=" * 60)

    all_plots = []

    for mode in ["transport", "driving"]:
        config = MODE_CONFIG[mode]
        print(f"\n📊 Loading {mode} data...")

        df = load_and_merge_data(mode=mode)
        if df.empty:
            print(f"⚠️ No data found for {mode} mode")
            continue

        # Convert numeric columns (creates copy, doesn't modify original)
        df_processed = convert_numeric_columns(df, config["services"], mode)

        # Generate plots with specified types
        plots = generate_mode_plots(df_processed, mode, plot_types)
        all_plots.extend([(mode, plot) for plot in plots])

        # Save comparison table
        save_comparison_table(df_processed, mode)

    # Summary
    if all_plots:
        print(f"\n🎨 Generated {len(all_plots)} comparison plots:")
        plot_counts = {}
        for mode, plot in all_plots:
            plot_type = plot.split("_")[-1].replace(".png", "")
            plot_counts[plot_type] = plot_counts.get(plot_type, 0) + 1
            print(f"   {mode.title()}: {plot}")

        print("\n📊 Plot type breakdown:")
        for plot_type, count in plot_counts.items():
            print(f"   {plot_type.title()}: {count} plots")

        print(f"\n📁 Files created in: {IMAGES_DIR}")
        print(f"📄 Tables created in: {RESULT_DIR}")

        return {
            "images_dir": IMAGES_DIR,
            "results_dir": RESULT_DIR,
            "generated_plots": all_plots,
            "plot_type_counts": plot_counts,
        }
    else:
        print("❌ No plots were generated")
        return None


if __name__ == "__main__":
    # Parse command line arguments
    plot_types = None

    if len(sys.argv) > 1:
        # Parse comma-separated plot types
        plot_types = [pt.strip() for pt in sys.argv[1].split(",")]

        # Validate plot types
        valid_types = []
        for pt in plot_types:
            if pt in PLOT_TYPES:
                valid_types.append(pt)
            else:
                print(f"⚠️ Unknown plot type: {pt}")

        plot_types = valid_types if valid_types else None

    # Default to all plot types if none specified or all invalid
    if plot_types is None:
        plot_types = list(PLOT_TYPES.keys())

    print(
        f"🎨 Generating routing visualizations with plot types: {', '.join(plot_types)}"
    )
    results = generate_all_comparisons(plot_types)
