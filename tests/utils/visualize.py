import os

import matplotlib.pyplot as plt
import pandas as pd

from tests.utils.commons import IMAGES_DIR, RESULT_DIR

COMPARISON_FILE = "service_comparison_results.csv"


def plot_metric(
    route_labels, df, y1, y2, y3, label1, label2, label3, ylabel, title, filename
):
    plt.figure(figsize=(12, 6))
    plt.plot(route_labels, df[y1], label=label1, marker="o")
    plt.plot(route_labels, df[y2], label=label2, marker="x")
    plt.plot(route_labels, df[y3], label=label3, marker="s")
    plt.xticks(rotation=90)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, filename))
    plt.close()


def save_modes_and_vehicle_lines_table(route_labels, df):
    table_rows = [
        "motis_modes",
        "google_modes",
        "valhalla_modes",
        "motis_vehicle_lines",
        "google_vehicle_lines",
        "valhalla_vehicle_lines",
        "valhalla_street_names",
        "valhalla_bus_suitable_roads",
        "valhalla_total_streets",
        "valhalla_costing_used",
        "motis_duration",
        "google_duration",
        "valhalla_duration",
        "motis_distance",
        "google_distance",
        "valhalla_distance",
        "motis_num_routes",
        "google_num_routes",
        "valhalla_num_routes",
        "motis_response_size",
        "google_response_size",
        "valhalla_response_size",
    ]
    table_df = df[table_rows].T
    table_df.columns = route_labels
    table_df.to_csv(os.path.join(RESULT_DIR, "modes_and_vehicle_lines.csv"))


def visualize_comparison():
    """Visualize Motis vs Google vs Valhalla routing results."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    comparison_file_path = os.path.join(RESULT_DIR, COMPARISON_FILE)
    df = pd.read_csv(comparison_file_path, dtype=str, on_bad_lines="skip")

    cols = [
        "motis_num_routes",
        "google_num_routes",
        "valhalla_num_routes",
        "motis_response_size",
        "google_response_size",
        "valhalla_response_size",
        "motis_duration",
        "google_duration",
        "valhalla_duration",
        "motis_distance",
        "google_distance",
        "valhalla_distance",
    ]
    df[cols] = df[cols].apply(pd.to_numeric, errors="coerce")

    route_labels = [f"route{i+1}" for i in range(len(df))]

    # Convert durations from seconds to minutes
    df["motis_duration"] = df["motis_duration"] / 60
    df["google_duration"] = df["google_duration"] / 60
    df["valhalla_duration"] = df["valhalla_duration"] / 60

    # Convert distances from meters to kilometers
    df["motis_distance"] = df["motis_distance"] / 1000
    df["google_distance"] = df["google_distance"] / 1000
    df["valhalla_distance"] = df["valhalla_distance"] / 1000

    # Plot Number of Routes
    plot_metric(
        route_labels,
        df,
        "motis_num_routes",
        "google_num_routes",
        "valhalla_num_routes",
        "Motis Routes",
        "Google Routes",
        "Valhalla Routes",
        "Number of Routes",
        "Number of Routes per Route",
        "num_routes.png",
    )
    # Plot Response Sizes
    plot_metric(
        route_labels,
        df,
        "motis_response_size",
        "google_response_size",
        "valhalla_response_size",
        "Motis Response Size",
        "Google Response Size",
        "Valhalla Response Size",
        "Response Size (bytes)",
        "Response Size per Route",
        "response_sizes.png",
    )
    # Plot Durations
    plot_metric(
        route_labels,
        df,
        "motis_duration",
        "google_duration",
        "valhalla_duration",
        "Motis Duration (min)",
        "Google Duration (min)",
        "Valhalla Duration (min)",
        "Duration (minutes)",
        "Duration per Route",
        "durations.png",
    )
    # Plot Distances
    plot_metric(
        route_labels,
        df,
        "motis_distance",
        "google_distance",
        "valhalla_distance",
        "Motis Distance (km)",
        "Google Distance (km)",
        "Valhalla Distance (km)",
        "Distance (kilometers)",
        "Distance per Route",
        "distances.png",
    )
    # Save Modes and Vehicle Lines Table
    save_modes_and_vehicle_lines_table(route_labels, df)
    print(f"Visualizations and tables saved in {IMAGES_DIR} and {RESULT_DIR}")
