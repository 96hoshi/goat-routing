"""
Visualize Motis vs Google Directions results from service_comparison_results.csv.

Saves each plot as a PNG file in the tests/results/images directory.
Uses route1, route2, ... as x-axis labels instead of OD pairs.
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
from test_ab_routing_comparison import PLAUSIBILITY_HEADERS

CSV_FILE = "tests/results/service_comparison_results.csv"
IMAGES_DIR = "tests/results/images"


def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)

    df = pd.read_csv(
        CSV_FILE,
        names=PLAUSIBILITY_HEADERS,
        header=None,
        dtype=str,
        on_bad_lines="skip",
    )

    # Convert relevant columns to numeric, coercing errors to NaN
    for col in [
        "motis_num_routes",
        "google_num_routes",
        "motis_response_size",
        "google_response_size",
        "motis_duration",
        "google_duration",
        "motis_distance",
        "google_distance",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Generate route labels: route1, route2, ...
    route_labels = [f"route{i+1}" for i in range(len(df))]

    # Plot number of routes
    plt.figure(figsize=(10, 5))
    plt.plot(route_labels, df["motis_num_routes"], label="Motis Routes", marker="o")
    plt.plot(route_labels, df["google_num_routes"], label="Google Routes", marker="x")
    plt.xticks(rotation=90)
    plt.ylabel("Number of Routes")
    plt.title("Number of Routes per Route")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, "num_routes.png"))
    plt.close()

    # Plot response sizes
    plt.figure(figsize=(10, 5))
    plt.plot(
        route_labels, df["motis_response_size"], label="Motis Response Size", marker="o"
    )
    plt.plot(
        route_labels,
        df["google_response_size"],
        label="Google Response Size",
        marker="x",
    )
    plt.xticks(rotation=90)
    plt.ylabel("Response Size (bytes)")
    plt.title("Response Size per Route")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, "response_sizes.png"))
    plt.close()

    # Plot durations
    plt.figure(figsize=(10, 5))
    plt.plot(route_labels, df["motis_duration"], label="Motis Duration (s)", marker="o")
    plt.plot(
        route_labels, df["google_duration"], label="Google Duration (s)", marker="x"
    )
    plt.xticks(rotation=90)
    plt.ylabel("Duration (seconds)")
    plt.title("Duration per Route")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, "durations.png"))
    plt.close()

    # Plot distances
    plt.figure(figsize=(10, 5))
    plt.plot(route_labels, df["motis_distance"], label="Motis Distance (m)", marker="o")
    plt.plot(
        route_labels, df["google_distance"], label="Google Distance (m)", marker="x"
    )
    plt.xticks(rotation=90)
    plt.ylabel("Distance (meters)")
    plt.title("Distance per Route")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, "distances.png"))
    plt.close()


if __name__ == "__main__":
    main()
