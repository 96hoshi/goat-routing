from tests.utils.commons import (
    coordinates_list,
    write_result,
)
from tests.utils.query_helpers import (
    extract_google_route_summary,
    extract_motis_route_summary,
    query_google,
    query_motis,
)
from tests.utils.visualize import visualize_comparison

PLAUSIBILITY_FILE = "service_comparison_results.csv"
PLAUSIBILITY_HEADERS = [
    "origin",
    "destination",
    "motis_duration",
    "motis_distance",
    "motis_modes",
    "motis_vehicle_lines",
    "motis_response_size",
    "motis_num_routes",
    "google_duration",
    "google_distance",
    "google_modes",
    "google_vehicle_lines",
    "google_response_size",
    "google_num_routes",
]


def evaluate_service_responses():
    """Evaluate and compare routing service responses for all coordinate pairs."""
    for origin, destination in coordinates_list:
        motis_result, motis_size = query_motis(origin, destination)
        motis_num_routes = (
            len(motis_result.get("result", {}).get("itineraries", []))
            if motis_result
            else 0
        )

        motis_summary = (
            extract_motis_route_summary(motis_result) if motis_result else None
        )
        google_result, google_size = query_google(origin, destination)
        google_num_routes = len(google_result.get("routes", [])) if google_result else 0
        google_summary = (
            extract_google_route_summary(google_result) if google_result else None
        )

        row = {
            "origin": origin,
            "destination": destination,
            "motis_duration": motis_summary["duration"] if motis_summary else "",
            "motis_distance": motis_summary["distance"] if motis_summary else "",
            "motis_modes": "|".join(motis_summary["modes"]) if motis_summary else "",
            "motis_vehicle_lines": (
                "|".join(motis_summary["vehicle_lines"]) if motis_summary else ""
            ),
            "motis_response_size": motis_size if motis_size is not None else "",
            "motis_num_routes": motis_num_routes,
            "google_duration": google_summary["duration"] if google_summary else "",
            "google_distance": google_summary["distance"] if google_summary else "",
            "google_modes": "|".join(google_summary["modes"]) if google_summary else "",
            "google_vehicle_lines": (
                "|".join(google_summary["vehicle_lines"]) if google_summary else ""
            ),
            "google_response_size": google_size if google_size is not None else "",
            "google_num_routes": google_num_routes,
        }
        write_result(row, filename=PLAUSIBILITY_FILE, headers=PLAUSIBILITY_HEADERS)
    visualize_comparison()


if __name__ == "__main__":
    evaluate_service_responses()
