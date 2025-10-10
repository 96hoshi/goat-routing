import os

import matplotlib.pyplot as plt
import pandas as pd

from tests.utils.commons import IMAGES_DIR, RESULT_DIR

COMPARISON_FILE = "service_comparison_results.csv"

# Service configuration
AVAILABLE_SERVICES = {
    "motis": {"label": "MOTIS", "color": "#1f77b4", "marker": "o"},
    "google": {"label": "Google Maps", "color": "#ff7f0e", "marker": "x"},
    "otp": {"label": "OTP", "color": "#d62728", "marker": "^"},
}


def load_and_merge_data(mode=None):
    """
    Load and merge data from comparison files and OTP performance data.
    Returns merged DataFrame with all service data including modes and vehicle_lines.
    """
    # Determine comparison file
    if mode == "transport":
        comparison_file = "transport_comparison.csv"
    elif mode == "driving":
        comparison_file = "driving_comparison.csv"
    else:
        comparison_file = COMPARISON_FILE

    comparison_path = os.path.join(RESULT_DIR, comparison_file)
    performance_path = os.path.join(RESULT_DIR, "otp_performance.csv")

    # Start with empty DataFrame
    merged_df = pd.DataFrame()

    # Load comparison data if exists
    if os.path.exists(comparison_path):
        print(f"📊 Loading comparison data from {comparison_file}")
        comparison_df = pd.read_csv(comparison_path, dtype=str, on_bad_lines="skip")
        merged_df = comparison_df.copy()
        print(f"   Found {len(comparison_df)} routes in comparison data")

    # Load OTP performance data if exists and merge
    if os.path.exists(performance_path) and mode == "transport":
        print("📊 Loading OTP performance data")
        perf_df = pd.read_csv(performance_path)

        # Map OTP performance columns to comparison format
        if not merged_df.empty:
            # Merge with existing comparison data
            min_rows = min(len(merged_df), len(perf_df))
            merged_df = merged_df.iloc[:min_rows].copy()

            # Add OTP columns from performance data
            mode_suffix = mode if mode else ""
            if mode_suffix:
                # Add numeric columns
                merged_df[f"otp_duration_{mode_suffix}"] = pd.to_numeric(
                    perf_df["route_duration"].iloc[:min_rows], errors="coerce"
                )
                merged_df[f"otp_distance_{mode_suffix}"] = (
                    pd.to_numeric(
                        perf_df["route_distance"].iloc[:min_rows], errors="coerce"
                    )
                    * 1000
                )  # Convert km to meters
                merged_df[f"otp_response_size_{mode_suffix}"] = pd.to_numeric(
                    perf_df["response_size_bytes"].iloc[:min_rows], errors="coerce"
                )
                merged_df[f"otp_num_routes_{mode_suffix}"] = (
                    1  # OTP returns 1 route per query
                )

                # Add modes and vehicle_lines columns
                if "modes" in perf_df.columns:
                    merged_df[f"otp_modes_{mode_suffix}"] = (
                        perf_df["modes"].iloc[:min_rows].values
                    )
                if "vehicle_lines" in perf_df.columns:
                    merged_df[f"otp_vehicle_lines_{mode_suffix}"] = (
                        perf_df["vehicle_lines"].iloc[:min_rows].values
                    )
            else:
                # Add without mode suffix
                merged_df["otp_duration"] = pd.to_numeric(
                    perf_df["route_duration"].iloc[:min_rows], errors="coerce"
                )
                merged_df["otp_distance"] = (
                    pd.to_numeric(
                        perf_df["route_distance"].iloc[:min_rows], errors="coerce"
                    )
                    * 1000
                )
                merged_df["otp_response_size"] = pd.to_numeric(
                    perf_df["response_size_bytes"].iloc[:min_rows], errors="coerce"
                )
                merged_df["otp_num_routes"] = 1

                # Add modes and vehicle_lines
                if "modes" in perf_df.columns:
                    merged_df["otp_modes"] = perf_df["modes"].iloc[:min_rows].values
                if "vehicle_lines" in perf_df.columns:
                    merged_df["otp_vehicle_lines"] = (
                        perf_df["vehicle_lines"].iloc[:min_rows].values
                    )

            print(
                f"   Merged OTP performance data ({min_rows} rows) including modes and vehicle_lines"
            )
        else:
            # Only OTP performance data available, create comparison format
            merged_df = pd.DataFrame()
            mode_suffix = mode if mode else ""

            if mode_suffix:
                merged_df[f"otp_duration_{mode_suffix}"] = pd.to_numeric(
                    perf_df["route_duration"], errors="coerce"
                )
                merged_df[f"otp_distance_{mode_suffix}"] = (
                    pd.to_numeric(perf_df["route_distance"], errors="coerce") * 1000
                )
                merged_df[f"otp_response_size_{mode_suffix}"] = pd.to_numeric(
                    perf_df["response_size_bytes"], errors="coerce"
                )
                merged_df[f"otp_num_routes_{mode_suffix}"] = 1

                # Add modes and vehicle_lines
                if "modes" in perf_df.columns:
                    merged_df[f"otp_modes_{mode_suffix}"] = perf_df["modes"]
                if "vehicle_lines" in perf_df.columns:
                    merged_df[f"otp_vehicle_lines_{mode_suffix}"] = perf_df[
                        "vehicle_lines"
                    ]
            else:
                merged_df["otp_duration"] = pd.to_numeric(
                    perf_df["route_duration"], errors="coerce"
                )
                merged_df["otp_distance"] = (
                    pd.to_numeric(perf_df["route_distance"], errors="coerce") * 1000
                )
                merged_df["otp_response_size"] = pd.to_numeric(
                    perf_df["response_size_bytes"], errors="coerce"
                )
                merged_df["otp_num_routes"] = 1

                # Add modes and vehicle_lines
                if "modes" in perf_df.columns:
                    merged_df["otp_modes"] = perf_df["modes"]
                if "vehicle_lines" in perf_df.columns:
                    merged_df["otp_vehicle_lines"] = perf_df["vehicle_lines"]

            # Add origin/destination from performance data if available
            if "origin" in perf_df.columns:
                merged_df["origin"] = perf_df["origin"]
            if "destination" in perf_df.columns:
                merged_df["destination"] = perf_df["destination"]

            print(
                f"   Created comparison data from OTP performance ({len(merged_df)} rows) including modes and vehicle_lines"
            )

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
    """
    Plot a metric for selected services with comparison data.
    """
    plt.figure(figsize=(12, 6))

    services_plotted = []

    for service in services:
        if service in AVAILABLE_SERVICES:
            if mode_suffix:
                column = f"{service}_{metric}_{mode_suffix}"
            else:
                column = f"{service}_{metric}"

            if column in df.columns:
                config = AVAILABLE_SERVICES[service]
                values = pd.to_numeric(df[column], errors="coerce")

                # Apply unit conversion and filter valid values
                if unit_conversion != 1:
                    values = values / unit_conversion

                # Only plot if we have valid data
                valid_mask = values.notna() & (values > 0)
                if valid_mask.any():
                    plt.plot(
                        [
                            route_labels[i]
                            for i in range(len(values))
                            if valid_mask.iloc[i]
                        ],
                        values[valid_mask],
                        label=config["label"],
                        marker=config["marker"],
                        color=config["color"],
                        linewidth=2,
                        markersize=6,
                    )
                    services_plotted.append(service)

    if services_plotted:
        plt.xticks(rotation=45, ha="right")
        plt.ylabel(ylabel)
        plt.title(title)
        plt.legend()
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.tight_layout()

        # Ensure images directory exists
        os.makedirs(IMAGES_DIR, exist_ok=True)
        plt.savefig(os.path.join(IMAGES_DIR, filename), dpi=150, bbox_inches="tight")
        plt.close()

        print(f"✅ Generated {filename} with services: {services_plotted}")
        return True
    else:
        plt.close()
        print(f"⚠️ No valid data for {filename}")
        return False


def generate_metric_plots(route_labels, df, services, mode_suffix, file_suffix):
    """Generate all metric plots for the given data."""
    # Define metrics to plot with proper unit conversions
    metrics = [
        ("num_routes", "Number of Routes", "Number of Routes", 1),
        ("response_size", "Response Size (KB)", "Response Size", 1024),
        (
            "duration",
            "Duration (minutes)",
            "Duration",
            60,
        ),  # Convert seconds to minutes
        ("distance", "Distance (km)", "Distance", 1000),  # Convert meters to km
    ]

    service_labels = " vs ".join(
        [AVAILABLE_SERVICES[s]["label"] for s in services if s in AVAILABLE_SERVICES]
    )
    mode_title = f" - {mode_suffix.title()} Mode" if mode_suffix else ""

    generated_plots = []

    for metric, ylabel, title_base, unit_conversion in metrics:
        # Check if any service has this metric
        has_data = False
        for service in services:
            if service in AVAILABLE_SERVICES:
                if mode_suffix:
                    column = f"{service}_{metric}_{mode_suffix}"
                else:
                    column = f"{service}_{metric}"
                if column in df.columns:
                    has_data = True
                    break

        if has_data:
            title = f"{title_base} Comparison ({service_labels}){mode_title}"
            filename = f"{metric}_comparison_{file_suffix}.png"

            if plot_metric(
                route_labels,
                df,
                services,
                metric,
                ylabel,
                title,
                filename,
                unit_conversion,
                mode_suffix,
            ):
                generated_plots.append(filename)

    return generated_plots


def save_modes_and_vehicle_lines_table(route_labels, df, services, mode_suffix=""):
    """Save comparison table for selected services including modes and vehicle_lines."""
    table_rows = []

    for service in services:
        if service in AVAILABLE_SERVICES:
            base_metrics = [
                "modes",
                "vehicle_lines",
                "duration",
                "distance",
                "num_routes",
                "response_size",
            ]
            for metric in base_metrics:
                if mode_suffix:
                    col_name = f"{service}_{metric}_{mode_suffix}"
                else:
                    col_name = f"{service}_{metric}"
                table_rows.append(col_name)

    # Filter existing columns only
    existing_rows = [row for row in table_rows if row in df.columns]

    if existing_rows:
        table_df = df[existing_rows].T
        table_df.columns = route_labels

        # Create filename with mode suffix
        filename = "modes_and_vehicle_lines"
        if mode_suffix:
            filename += f"_{mode_suffix}"
        filename += ".csv"

        table_path = os.path.join(RESULT_DIR, filename)
        table_df.to_csv(table_path)
        print(f"✅ Saved comparison table: {filename}")

        # Show sample of modes and vehicle_lines data
        modes_rows = [row for row in existing_rows if "modes" in row]
        vehicle_rows = [row for row in existing_rows if "vehicle" in row]

        if modes_rows:
            print(f"   Modes data available for: {modes_rows}")
        if vehicle_rows:
            print(f"   Vehicle lines data available for: {vehicle_rows}")


def visualize_comparison(services=None, mode=None, custom_file=None):
    """
    Visualize comparison data including OTP performance data.
    """
    # Default to all services if none specified
    if services is None:
        services = list(AVAILABLE_SERVICES.keys())

    # Validate services
    services = [s for s in services if s in AVAILABLE_SERVICES]
    if not services:
        print("No valid services specified. Available: motis, google, otp")
        return None

    print(f"🎨 Generating visualizations for services: {services}")

    # Load and merge data from comparison files and OTP performance
    df = load_and_merge_data(mode=mode)

    if df.empty:
        print("❌ No data available for visualization")
        return None

    # Ensure images directory exists
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Convert numeric columns for the services we're plotting
    mode_suffix = mode if mode else ""
    cols_to_convert = []

    for service in services:
        base_metrics = ["num_routes", "response_size", "duration", "distance"]
        for metric in base_metrics:
            if mode_suffix:
                col = f"{service}_{metric}_{mode_suffix}"
            else:
                col = f"{service}_{metric}"
            if col in df.columns:
                cols_to_convert.append(col)

    if cols_to_convert:
        df[cols_to_convert] = df[cols_to_convert].apply(pd.to_numeric, errors="coerce")

    # Generate route labels
    route_labels = [f"Route {i+1}" for i in range(len(df))]

    # Generate file suffix for output files
    file_suffix = f"{'_vs_'.join(services)}"
    if mode_suffix:
        file_suffix += f"_{mode_suffix}"

    # Generate plots
    generated_plots = generate_metric_plots(
        route_labels, df, services, mode_suffix, file_suffix
    )

    # Save comparison table
    save_modes_and_vehicle_lines_table(route_labels, df, services, mode_suffix)

    if generated_plots:
        print(f"🎨 Generated {len(generated_plots)} comparison plots")
        return {
            "images_dir": IMAGES_DIR,
            "results_dir": RESULT_DIR,
            "generated_plots": generated_plots,
        }
    else:
        print("❌ No plots were generated")
        return None


# Mode-specific visualization functions
def visualize_single_service(service):
    """Visualize results for a single service."""
    return visualize_comparison([service])


def visualize_transport_mode(services=None):
    """Visualize transport/public transit routing results including OTP performance."""
    return visualize_comparison(services=services, mode="transport")


def visualize_driving_mode(services=None):
    """Visualize driving/car routing results."""
    return visualize_comparison(services=services, mode="driving")


def visualize_mode_comparison(mode_pair=["transport", "driving"], services=None):
    """
    Generate visualizations for multiple modes.

    Args:
        mode_pair: List of modes to visualize (e.g., ["transport", "driving"])
        services: List of services to include (default: all available)
    """
    if services is None:
        services = list(AVAILABLE_SERVICES.keys())

    results = {}
    for mode in mode_pair:
        results[mode] = visualize_comparison(services=services, mode=mode)

    return results


def compare_transport_vs_driving(services=None):
    """Quick function to compare transport vs driving modes."""
    return visualize_mode_comparison(["transport", "driving"], services=services)
