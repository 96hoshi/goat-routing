import os

import matplotlib.pyplot as plt
import pandas as pd

from tests.utils.commons import IMAGES_DIR, RESULT_DIR

COMPARISON_FILE = "service_comparison_results.csv"

# Service configuration
AVAILABLE_SERVICES = {
    "motis": {"label": "MOTIS", "color": "#1f77b4", "marker": "o"},
    "google": {"label": "Google Maps", "color": "#ff7f0e", "marker": "x"},
    "valhalla": {"label": "Valhalla", "color": "#2ca02c", "marker": "s"},
}


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
    Plot a metric for selected services.

    Args:
        route_labels: Labels for x-axis
        df: DataFrame with data
        services: List of services to plot (e.g., ['motis', 'google'])
        metric: Base metric name (e.g., 'duration', 'distance')
        ylabel: Y-axis label
        title: Plot title
        filename: Output filename
        unit_conversion: Factor to convert units (e.g., 60 for seconds to minutes)
        mode_suffix: Mode suffix for column names (e.g., 'transit', 'driving')
    """
    plt.figure(figsize=(12, 6))

    for service in services:
        if service in AVAILABLE_SERVICES:
            if mode_suffix:
                column = f"{service}_{metric}_{mode_suffix}"
            else:
                column = f"{service}_{metric}"

            if column in df.columns:
                config = AVAILABLE_SERVICES[service]
                values = (
                    df[column] / unit_conversion if unit_conversion != 1 else df[column]
                )
                plt.plot(
                    route_labels,
                    values,
                    label=config["label"],
                    marker=config["marker"],
                    color=config["color"],
                )

    plt.xticks(rotation=90)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, filename))
    plt.close()


def generate_metric_plots(route_labels, df, services, mode_suffix, file_suffix):
    """Generate all metric plots for the given data."""
    # Define metrics to plot
    metrics = [
        ("num_routes", "Number of Routes", "Number of Routes", 1),
        ("response_size", "Response Size (bytes)", "Response Size", 1),
        ("duration", "Duration (minutes)", "Duration", 60),
        ("distance", "Distance (kilometers)", "Distance", 1000),
    ]

    service_labels = ", ".join([AVAILABLE_SERVICES[s]["label"] for s in services])
    mode_title = f" - {mode_suffix.title()} Mode" if mode_suffix else ""

    for metric, ylabel, title_base, unit_conversion in metrics:
        title = f"{title_base} per Route ({service_labels}){mode_title}"
        filename = f"{metric}_{file_suffix}.png"

        plot_metric(
            route_labels,
            df,
            services,
            metric,
            ylabel,
            title,
            filename,
            unit_conversion,
            mode_suffix,
        )


def save_modes_and_vehicle_lines_table(route_labels, df, services, mode_suffix=""):
    """Save comparison table for selected services."""
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
                    table_rows.append(f"{service}_{metric}_{mode_suffix}")
                else:
                    table_rows.append(f"{service}_{metric}")

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

        table_df.to_csv(os.path.join(RESULT_DIR, filename))


def visualize_comparison(services=None, mode=None, custom_file=None):
    # Default to all services if none specified
    if services is None:
        services = list(AVAILABLE_SERVICES.keys())

    # Validate services
    services = [s for s in services if s in AVAILABLE_SERVICES]
    if not services:
        print("No valid services specified. Available: motis, google, valhalla")
        return

    # Determine which file to use
    if custom_file:
        filename = custom_file
        mode_suffix = custom_file.replace("service_comparison_", "").replace(".csv", "")
    elif mode in ["driving", "transport"]:
        if mode == "transport":
            filename = "transport_comparison.csv"
        elif mode == "driving":
            filename = "driving_comparison.csv"
        mode_suffix = mode
    else:
        filename = COMPARISON_FILE
        mode_suffix = ""

    os.makedirs(IMAGES_DIR, exist_ok=True)
    comparison_file_path = os.path.join(RESULT_DIR, filename)  # type: ignore

    if not os.path.exists(comparison_file_path):
        print(f"Error: File {comparison_file_path} not found")
        return

    df = pd.read_csv(comparison_file_path, dtype=str, on_bad_lines="skip")

    # Convert numeric columns - handle mode-specific suffixes
    cols = []
    for service in services:
        base_metrics = ["num_routes", "response_size", "duration", "distance"]
        for metric in base_metrics:
            if mode_suffix:
                cols.append(f"{service}_{metric}_{mode_suffix}")
            else:
                cols.append(f"{service}_{metric}")

    # Filter existing columns
    existing_cols = [col for col in cols if col in df.columns]
    df[existing_cols] = df[existing_cols].apply(pd.to_numeric, errors="coerce")

    route_labels = [f"route{i+1}" for i in range(len(df))]

    # Generate file suffix for output files
    file_suffix = f"{'_'.join(services)}"
    if mode_suffix:
        file_suffix += f"_{mode_suffix}"

    generate_metric_plots(route_labels, df, services, mode_suffix, file_suffix)
    save_modes_and_vehicle_lines_table(route_labels, df, services, mode_suffix)

    return {"images_dir": IMAGES_DIR, "results_dir": RESULT_DIR}


# Mode-specific visualization functions
def visualize_single_service(service):
    """Visualize results for a single service."""
    visualize_comparison([service])


def visualize_transport_mode(services=None):
    """Visualize transport/public transit routing results."""
    visualize_comparison(services=services, mode="transport")


def visualize_driving_mode(services=None):
    """Visualize driving/car routing results."""
    visualize_comparison(services=services, mode="driving")


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
    visualize_mode_comparison(["transport", "driving"], services=services)
