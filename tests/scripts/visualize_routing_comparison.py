"""
Creates comparison plots for routing results by loading, transforming, and
visualizing data. Generates a main dashboard and saves each subplot
individually to a dedicated subfolder.
"""

import glob
import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from tests.conftest import IMAGES_DIR, RESULT_DIR
from tests.utils.commons import get_service_config

ROUTING_DETAILS_DIR = os.path.join(IMAGES_DIR, "routing_details")

SERVICE_CONFIG = get_service_config()
COLOR_PALETTE = {k: v["color"] for k, v in SERVICE_CONFIG.items()}

# --- 1. Data Loading and Preparation ---


def find_latest_file(pattern: str) -> str | None:
    """Finds the most recent file in the result directory matching a pattern."""
    search_path = os.path.join(RESULT_DIR, pattern)
    files = glob.glob(search_path)
    return max(files, key=os.path.getctime) if files else None


def load_and_prepare_data():
    """Loads and prepares data, replacing long route labels with simple ones."""
    driving_file = find_latest_file("driving_comparison*.csv")
    transport_file = find_latest_file("transport_comparison*.csv")

    if not driving_file and not transport_file:
        raise FileNotFoundError(
            "No comparison CSV files found in 'reports/' directory."
        )

    processed_rows = []

    # Process Transport Data
    if transport_file:
        df_transport = pd.read_csv(transport_file)
        print(f"📊 Loaded {len(df_transport)} public transport records.")
        for _, row in df_transport.iterrows():
            route_identifier = f"{row['origin']}|{row['destination']}"
            for service in ["motis", "google"]:
                processed_rows.append(
                    {
                        "service": service,
                        "routing_mode": "Public Transport",
                        "route_label": route_identifier,
                        "duration_min": row[f"{service}_duration_transport"] / 60,
                        "distance_km": row[f"{service}_distance_transport"] / 1000,
                        "num_routes": row[f"{service}_num_routes_transport"],
                        "response_size_kb": row[f"{service}_response_size_transport"]
                        / 1024,
                    }
                )

    # Process Driving Data
    if driving_file:
        df_driving = pd.read_csv(driving_file)
        print(f"🚗 Loaded {len(df_driving)} driving records.")
        for _, row in df_driving.iterrows():
            route_identifier = f"{row['origin']}|{row['destination']}"
            processed_rows.append(
                {
                    "service": "google",
                    "routing_mode": "Driving",
                    "route_label": route_identifier,
                    "duration_min": row["google_duration_driving"] / 60,
                    "distance_km": row["google_distance_driving"] / 1000,
                    "num_routes": row["google_num_routes_driving"],
                    "response_size_kb": row["google_response_size_driving"] / 1024,
                }
            )

    if not processed_rows:
        return pd.DataFrame()
    df_final = pd.DataFrame(processed_rows)

    if not df_final.empty:
        unique_route_ids = pd.unique(df_final["route_label"])
        route_map = {long_id: f"{i+1}" for i, long_id in enumerate(unique_route_ids)}
        df_final["route_label"] = df_final["route_label"].map(route_map)

    return df_final


# --- 2. More Flexible Individual Plotting Functions ---


def plot_barplot(df, ax, y_metric, title, ylabel, **plot_kwargs):
    """
    A generic bar plot function that handles both single and grouped plots by
    accepting extra keyword arguments and passing them to seaborn.
    """
    # **plot_kwargs will now contain {'hue': 'service', 'palette': ...} for transport
    # or {'color': ...} for driving. This is passed directly to seaborn.
    sns.barplot(
        data=df, x="route_label", y=y_metric, ax=ax, estimator=np.mean, **plot_kwargs
    )

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel(None)  # X-label is set on the figure level
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")

    ax.grid(True, linestyle="--", alpha=0.6)

    # Only add a legend if a 'hue' was provided
    if "hue" in plot_kwargs:
        ax.legend(title="Service")


# --- 3. Main Dashboard and Saving Logic ---


def create_dashboard(df, plot_definitions, suptitle, filename_prefix, grid_size=(2, 2)):
    """Generic function to create a dashboard plot."""
    fig, axes = plt.subplots(
        grid_size[0], grid_size[1], figsize=(grid_size[1] * 8, grid_size[0] * 6)
    )
    fig.suptitle(suptitle, fontsize=16, fontweight="bold")
    flat_axes = axes.flatten()  # type: ignore

    for i, (plot_func, kwargs) in enumerate(plot_definitions):
        plot_func(df, flat_axes[i], **kwargs)

    # Hide any unused subplots
    for i in range(len(plot_definitions), len(flat_axes)):
        flat_axes[i].set_visible(False)

    plt.tight_layout(rect=(0, 0.03, 1, 0.95))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.png"
    save_path = os.path.join(IMAGES_DIR, filename)
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"✅ Dashboard saved to: {save_path}")


def save_detailed_plots(df, plot_definitions, filename_prefix):
    """Generic function to save individual detailed plots."""
    subfolder_path = os.path.join(ROUTING_DETAILS_DIR, filename_prefix)
    os.makedirs(subfolder_path, exist_ok=True)

    for i, (plot_func, kwargs) in enumerate(plot_definitions):
        fig, ax = plt.subplots(figsize=(10, 6))
        plot_func(df, ax, **kwargs)
        ax.set_xlabel("Route")  # Add x-label to single plots

        plt.tight_layout()

        # Use a descriptive name based on the plotted metric
        metric_name = kwargs.get("y_metric", f"plot_{i+1}")
        filename = f"{i+1:02d}_{metric_name}.png"
        save_path = os.path.join(subfolder_path, filename)

        plt.savefig(save_path, dpi=150)
        plt.close()

    print(f"✅ Detailed plots for '{filename_prefix}' saved in: {subfolder_path}")


# --- 4. Main Execution ---


def main():
    """Main function to load data and generate all plots."""
    try:
        print("🚀 Starting routing comparison analysis...")
        os.makedirs(IMAGES_DIR, exist_ok=True)

        df_all = load_and_prepare_data()
        if df_all.empty:
            print("No data processed. Exiting.")
            return

        # --- Define Plot Configurations ---

        # Transport plots will be grouped by 'service'
        transport_plot_defs = [
            (
                plot_barplot,
                {
                    "y_metric": "duration_min",
                    "title": "Duration",
                    "ylabel": "Duration (min)",
                    "hue": "service",
                    "palette": COLOR_PALETTE,
                },
            ),
            (
                plot_barplot,
                {
                    "y_metric": "distance_km",
                    "title": "Distance",
                    "ylabel": "Distance (km)",
                    "hue": "service",
                    "palette": COLOR_PALETTE,
                },
            ),
            (
                plot_barplot,
                {
                    "y_metric": "num_routes",
                    "title": "Route Options",
                    "ylabel": "Num. of Routes",
                    "hue": "service",
                    "palette": COLOR_PALETTE,
                },
            ),
            (
                plot_barplot,
                {
                    "y_metric": "response_size_kb",
                    "title": "Response Size",
                    "ylabel": "Response Size (KB)",
                    "hue": "service",
                    "palette": COLOR_PALETTE,
                },
            ),
        ]

        # Driving plots will be simple bars with a single color
        driving_plot_defs = [
            (
                plot_barplot,
                {
                    "y_metric": "duration_min",
                    "title": "Duration",
                    "ylabel": "Duration (min)",
                    "color": COLOR_PALETTE.get("google"),
                },
            ),
            (
                plot_barplot,
                {
                    "y_metric": "distance_km",
                    "title": "Distance",
                    "ylabel": "Distance (km)",
                    "color": COLOR_PALETTE.get("google"),
                },
            ),
            (
                plot_barplot,
                {
                    "y_metric": "num_routes",
                    "title": "Route Options",
                    "ylabel": "Num. of Routes",
                    "color": COLOR_PALETTE.get("google"),
                },
            ),
        ]

        # --- Create Plots ---
        df_transport = df_all[df_all["routing_mode"] == "Public Transport"]
        if not df_transport.empty:
            create_dashboard(
                df_transport,
                transport_plot_defs,
                "Public Transport Comparison: MOTIS vs. Google",
                "public_transport_comparison",
            )
            save_detailed_plots(df_transport, transport_plot_defs, "public_transport")

        df_driving = df_all[df_all["routing_mode"] == "Driving"]
        if not df_driving.empty:
            create_dashboard(
                df_driving,
                driving_plot_defs,
                "Google Driving: Performance Summary",
                "driving_summary",
                grid_size=(1, 3),
            )
            save_detailed_plots(df_driving, driving_plot_defs, "driving")

    except FileNotFoundError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
