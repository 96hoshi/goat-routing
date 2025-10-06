from tests.utils.commons import (
    coordinates_list,
    write_result,
)
from tests.utils.query_helpers import (
    extract_google_route_summary,
    extract_motis_route_summary,
    extract_valhalla_route_summary,
    query_google,
    query_motis,
    query_valhalla,
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
    "valhalla_duration",
    "valhalla_distance",
    "valhalla_modes",
    "valhalla_vehicle_lines",
    "valhalla_street_names",
    "valhalla_bus_suitable_roads",
    "valhalla_total_streets",
    "valhalla_costing_used",
    "valhalla_response_size",
    "valhalla_num_routes",
]


def evaluate_service_responses():
    """Evaluate and compare routing service responses for all coordinate pairs."""
    for origin, destination in coordinates_list:
        # Query Motis
        motis_result, motis_size = query_motis(origin, destination)
        motis_num_routes = (
            len(motis_result.get("result", {}).get("itineraries", []))
            if motis_result
            else 0
        )
        motis_summary = (
            extract_motis_route_summary(motis_result) if motis_result else None
        )

        # Query Google
        google_result, google_size = query_google(origin, destination)
        google_num_routes = len(google_result.get("routes", [])) if google_result else 0
        google_summary = (
            extract_google_route_summary(google_result) if google_result else None
        )

        # Query Valhalla
        valhalla_result, valhalla_size = query_valhalla(origin, destination)
        valhalla_num_routes = (
            len(valhalla_result.get("trip", {}).get("legs", []))
            if valhalla_result
            else 0
        )
        valhalla_summary = (
            extract_valhalla_route_summary(valhalla_result) if valhalla_result else None
        )

        row = {
            "origin": origin,
            "destination": destination,
            # Motis results
            "motis_duration": motis_summary["duration"] if motis_summary else "",
            "motis_distance": motis_summary["distance"] if motis_summary else "",
            "motis_modes": "|".join(motis_summary["modes"]) if motis_summary else "",
            "motis_vehicle_lines": (
                "|".join(motis_summary["vehicle_lines"]) if motis_summary else ""
            ),
            "motis_response_size": motis_size if motis_size is not None else "",
            "motis_num_routes": motis_num_routes,
            # Google results
            "google_duration": google_summary["duration"] if google_summary else "",
            "google_distance": google_summary["distance"] if google_summary else "",
            "google_modes": "|".join(google_summary["modes"]) if google_summary else "",
            "google_vehicle_lines": (
                "|".join(google_summary["vehicle_lines"]) if google_summary else ""
            ),
            "google_response_size": google_size if google_size is not None else "",
            "google_num_routes": google_num_routes,
            # Valhalla results
            "valhalla_duration": (
                valhalla_summary["duration"] if valhalla_summary else ""
            ),
            "valhalla_distance": (
                valhalla_summary["distance"] if valhalla_summary else ""
            ),
            "valhalla_modes": (
                "|".join(valhalla_summary["modes"]) if valhalla_summary else ""
            ),
            "valhalla_vehicle_lines": (
                "|".join(valhalla_summary["vehicle_lines"]) if valhalla_summary else ""
            ),
            "valhalla_street_names": (
                "|".join(valhalla_summary["street_names"])
                if valhalla_summary and valhalla_summary.get("street_names")
                else ""
            ),
            "valhalla_bus_suitable_roads": (
                "|".join(valhalla_summary["bus_suitable_roads"])
                if valhalla_summary and valhalla_summary.get("bus_suitable_roads")
                else ""
            ),
            "valhalla_total_streets": (
                valhalla_summary["total_streets"] if valhalla_summary else ""
            ),
            "valhalla_costing_used": (
                valhalla_summary["costing_used"] if valhalla_summary else ""
            ),
            "valhalla_response_size": (
                valhalla_size if valhalla_size is not None else ""
            ),
            "valhalla_num_routes": valhalla_num_routes,
        }
        write_result(row, filename=PLAUSIBILITY_FILE, headers=PLAUSIBILITY_HEADERS)
    visualize_comparison()


if __name__ == "__main__":
    evaluate_service_responses()
