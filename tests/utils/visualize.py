import os

import matplotlib.pyplot as plt
import pandas as pd

from tests.utils.commons import IMAGES_DIR, RESULT_DIR

COMPARISON_FILE = "service_comparison_results.csv"


def plot_metric(route_labels, df, y1, y2, label1, label2, ylabel, title, filename):
    plt.figure(figsize=(10, 5))
    plt.plot(route_labels, df[y1], label=label1, marker="o")
    plt.plot(route_labels, df[y2], label=label2, marker="x")
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
        "motis_vehicle_lines",
        "google_vehicle_lines",
        "motis_duration",
        "google_duration",
        "motis_distance",
        "google_distance",
        "motis_num_routes",
        "google_num_routes",
        "motis_response_size",
        "google_response_size",
    ]
    table_df = df[table_rows].T
    table_df.columns = route_labels
    table_df.to_csv(os.path.join(RESULT_DIR, "modes_and_vehicle_lines.csv"))


def visualize_comparison():
    """Visualize Motis vs Google Directions results."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    comparison_file_path = os.path.join(RESULT_DIR, COMPARISON_FILE)
    df = pd.read_csv(comparison_file_path, dtype=str, on_bad_lines="skip")

    cols = [
        "motis_num_routes",
        "google_num_routes",
        "motis_response_size",
        "google_response_size",
        "motis_duration",
        "google_duration",
        "motis_distance",
        "google_distance",
    ]
    df[cols] = df[cols].apply(pd.to_numeric, errors="coerce")

    route_labels = [f"route{i+1}" for i in range(len(df))]

    # Convert durations from seconds to minutes
    df["motis_duration"] = df["motis_duration"] / 60
    df["google_duration"] = df["google_duration"] / 60

    # Convert distances from meters to kilometers
    df["motis_distance"] = df["motis_distance"] / 1000
    df["google_distance"] = df["google_distance"] / 1000

    # Plot Number of Routes
    plot_metric(
        route_labels,
        df,
        "motis_num_routes",
        "google_num_routes",
        "Motis Routes",
        "Google Routes",
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
        "Motis Response Size",
        "Google Response Size",
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
        "Motis Duration (min)",
        "Google Duration (min)",
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
        "Motis Distance (km)",
        "Google Distance (km)",
        "Distance (kilometers)",
        "Distance per Route",
        "distances.png",
    )
    # Save Modes and Vehicle Lines Table
    save_modes_and_vehicle_lines_table(route_labels, df)
    print(f"Visualizations and tables saved in {IMAGES_DIR} and {RESULT_DIR}")
