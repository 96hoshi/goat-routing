import os

import matplotlib.pyplot as plt
import pandas as pd

from tests.conftest import IMAGES_DIR, RESULT_DIR
from tests.scripts.modes_comparison import (
    DRIVING_COMPARISON_CSV,
    TRANSPORT_COMPARISON_CSV,
)
from tests.test_otp_routing import OTP_DRIVING_CSV_FILE, OTP_TRANSPORT_CSV_FILE
from tests.utils.commons import get_available_services

AVAILABLE_SERVICES = get_available_services()

# Metrics configuration
METRICS_CONFIG = [
    ("num_routes", "Number of Routes", "Number of Routes", 1),
    ("response_size", "Response Size (KB)", "Response Size", 1024),
    ("duration", "Duration (minutes)", "Duration", 60),
    ("distance", "Distance (km)", "Distance", 1000),
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
    """Load and merge data from the new CSV file formats."""
    if mode not in MODE_CONFIG:
        return pd.DataFrame()

    config = MODE_CONFIG[mode]
    comparison_file = os.path.join(RESULT_DIR, config["comparison_file"])
    otp_file = os.path.join(RESULT_DIR, config["otp_file"])

    # Load comparison data
    if not os.path.exists(comparison_file):
        return pd.DataFrame()

    print(f"📊 Loading {mode} comparison data")
    merged_df = pd.read_csv(comparison_file, dtype=str, on_bad_lines="skip")
    print(f"   Found {len(merged_df)} routes in {mode} comparison")

    # Load and merge OTP data if available
    if not os.path.exists(otp_file):
        return merged_df

    print(f"📊 Loading OTP {mode} routes data")
    otp_df = pd.read_csv(otp_file)

    # Merge OTP data
    min_rows = min(len(merged_df), len(otp_df))
    merged_df = merged_df.iloc[:min_rows].copy()

    # Add OTP columns with mode suffix
    for metric, otp_col in config["otp_columns"].items():
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
    filename,
    unit_conversion=1,
    mode_suffix="",
):
    """Plot a metric for selected services with comparison data."""
    plt.figure(figsize=(14, 8))
    services_plotted = []

    # Create numeric x-positions for proper ordering
    x_positions = list(range(len(route_labels)))

    for service in services:
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

        # Filter out invalid values but keep x-positions aligned
        plot_x = []
        plot_y = []

        for i, value in enumerate(values):
            if pd.notna(value) and value > 0:
                plot_x.append(x_positions[i])
                plot_y.append(value)

        if not plot_x:
            continue

        plt.plot(
            plot_x,
            plot_y,
            label=config["label"],
            marker=config["marker"],
            color=config["color"],
            linewidth=2,
            markersize=8,
        )
        services_plotted.append(service)

    if not services_plotted:
        plt.close()
        print(f"⚠️ No valid data for {filename}")
        return False

    # Set x-axis with proper integer positions and labels
    plt.xticks(x_positions, route_labels, rotation=45, ha="right")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend(loc="best", fontsize=12)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    os.makedirs(IMAGES_DIR, exist_ok=True)
    plt.savefig(os.path.join(IMAGES_DIR, filename), dpi=300, bbox_inches="tight")
    plt.close()

    return True


def generate_mode_plots(df, mode):
    """Generate all plots for a specific mode."""
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

    for metric, ylabel, title_base, unit_conversion in METRICS_CONFIG:
        title = f"{title_base} Comparison - {mode.title()} Mode ({service_labels})"
        filename = f"{mode}_{metric}_comparison.png"

        if plot_metric(
            route_labels,
            df,
            available_services,
            metric,
            ylabel,
            title,
            filename,
            unit_conversion,
            mode,
        ):
            generated_plots.append(filename)

    return generated_plots


def save_comparison_table(df, mode_suffix=""):
    """Save comparison table for transport mode only."""
    if mode_suffix != "transport":
        print(f"⏭️ Skipping comparison table for {mode_suffix} mode")
        return

    available_services = [
        service
        for service in AVAILABLE_SERVICES.keys()
        if f"{service}_duration_transport" in df.columns
    ]

    if not available_services:
        print("⚠️ No transport services found for table generation")
        return

    route_labels = [f"Route {i+1}" for i in range(len(df))]
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
        if f"{service}_{metric}_transport" in df.columns
    ]

    if not table_rows:
        return

    table_df = df[table_rows].T
    table_df.columns = route_labels

    filename = "modes_and_vehicle_lines_transport.csv"
    table_path = os.path.join(RESULT_DIR, filename)
    table_df.to_csv(table_path)
    print(f"✅ Saved transport comparison table: {filename}")


def convert_numeric_columns(df, services, mode):
    """Convert specified columns to numeric format."""
    cols_to_convert = [
        f"{service}_{metric}_{mode}"
        for service in services
        for metric in ["num_routes", "response_size", "duration", "distance"]
        if f"{service}_{metric}_{mode}" in df.columns
    ]

    if cols_to_convert:
        df[cols_to_convert] = df[cols_to_convert].apply(pd.to_numeric, errors="coerce")

    return df


def generate_all_comparisons():
    """Generate comprehensive comparison plots for transport and driving modes."""
    print("🎨 Generating comprehensive routing comparisons...")
    print("=" * 60)

    all_plots = []

    for mode in ["transport", "driving"]:
        config = MODE_CONFIG[mode]
        print(f"\n📊 Loading {mode} data...")

        df = load_and_merge_data(mode=mode)
        if df.empty:
            continue

        # Convert numeric columns
        df = convert_numeric_columns(df, config["services"], mode)

        # Generate plots
        plots = generate_mode_plots(df, mode)
        all_plots.extend([(mode, plot) for plot in plots])

        # Save comparison table
        save_comparison_table(df, mode)

    # Summary
    if all_plots:
        print(f"\n🎨 Generated {len(all_plots)} comparison plots:")
        for mode, plot in all_plots:
            print(f"   {mode.title()}: {plot}")

        return {
            "images_dir": IMAGES_DIR,
            "results_dir": RESULT_DIR,
            "generated_plots": all_plots,
        }
    else:
        print("❌ No plots were generated")
        return None


if __name__ == "__main__":
    results = generate_all_comparisons()
