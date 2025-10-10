"""
Clean routing comparison with proper separation of transport vs driving modes.
- Transport: MOTIS (transit), Google (transit), Valhalla-GTFS (multimodal)
- Driving: Google (driving), Valhalla-NoGTFS (auto)
"""

from tests.conftest import write_result
from tests.utils.commons import coordinates_list
from tests.utils.query_helpers import (
    extract_google_route_summary,
    extract_motis_route_summary,
    query_google,
    query_motis,
)

# Transport services (public transit)
TRANSPORT_SERVICES = {
    "motis": {
        "query_func": query_motis,
        "extract_func": extract_motis_route_summary,
        "query_params": {"transitModes": ["TRANSIT"]},
        "routes_path": ["result", "itineraries"],
    },
    "google": {
        "query_func": query_google,
        "extract_func": extract_google_route_summary,
        "query_params": {"mode": "transit"},
        "routes_path": ["routes"],
    },
    # "valhalla_gtfs": {
    #     "query_func": query_valhalla,
    #     "extract_func": extract_valhalla_route_summary,
    #     "query_params": {"costing": "multimodal"},
    #     "routes_path": ["trip", "legs"],
    #     "extra_fields": ["transit_stops", "agencies", "has_gtfs_data"],
    # },
    # "otp": {
    #     "query_func": query_otp,
    #     "extract_func": extract_otp_route_summary,
    #     "query_params": {
    #         "transport_modes": ["TRANSIT", "WALK"]
    #     },  # Fixed parameter name
    #     "routes_path": [
    #         "data",
    #         "plan",
    #         "itineraries",
    #     ],  # Fixed path for GraphQL response
    #     "extra_fields": ["transit_stops", "agencies"],
    # },
}

# Driving services (car routing)
DRIVING_SERVICES = {
    "google": {
        "query_func": query_google,
        "extract_func": extract_google_route_summary,
        "query_params": {"mode": "driving"},
        "routes_path": ["routes"],
    },
    # "valhalla": {
    #     "query_func": query_valhalla,
    #     "extract_func": extract_valhalla_route_summary,
    #     "query_params": {"costing": "auto"},
    #     "routes_path": ["trip", "legs"],
    #     "use_no_gtfs_endpoint": True,
    # },
}

# Common fields for all services
BASE_FIELDS = ["duration", "distance", "modes", "vehicle_lines"]


def query_service_for_mode(service_name, service_config, origin, destination):
    """Query a service with its specific configuration."""
    try:
        query_func = service_config["query_func"]

        # Handle special case for no-GTFS Valhalla
        if service_config.get("use_no_gtfs_endpoint"):
            # Use the no-GTFS Valhalla endpoint
            params = service_config["query_params"].copy()
            return query_func(origin, destination, **params)
        else:
            return query_func(origin, destination, **service_config["query_params"])

    except Exception as e:
        print(f"Error querying {service_name}: {e}")
        return None, None


def get_route_count(service_config, result):
    """Get route count from service result."""
    if not result:
        return 0

    routes_data = result
    for path_key in service_config["routes_path"]:
        if isinstance(routes_data, dict):
            routes_data = routes_data.get(path_key, [])
        else:
            return 0

    return len(routes_data) if isinstance(routes_data, list) else 0


def extract_service_data(service_name, service_config, result, size, mode):
    """Extract standardized data from service result."""
    extract_func = service_config["extract_func"]
    summary = extract_func(result) if result else None
    num_routes = get_route_count(service_config, result)

    data = {}

    # Add base fields
    for field in BASE_FIELDS:
        if summary and field in summary:
            if field in ["modes", "vehicle_lines"] and isinstance(summary[field], list):
                data[f"{service_name}_{field}_{mode}"] = "|".join(summary[field])
            else:
                data[f"{service_name}_{field}_{mode}"] = summary[field]
        else:
            data[f"{service_name}_{field}_{mode}"] = ""

    # Add standard fields
    data[f"{service_name}_response_size_{mode}"] = size if size is not None else ""
    data[f"{service_name}_num_routes_{mode}"] = num_routes

    # Add extra fields for specific services
    extra_fields = service_config.get("extra_fields", [])
    for field in extra_fields:
        if summary and field in summary:
            if isinstance(summary[field], list):
                data[f"{service_name}_{field}_{mode}"] = "|".join(summary[field])
            else:
                data[f"{service_name}_{field}_{mode}"] = summary[field]
        else:
            data[f"{service_name}_{field}_{mode}"] = ""

    return data


def get_headers_for_services(services, mode):
    """Generate CSV headers for a set of services."""
    headers = []
    for service_name, service_config in services.items():
        # Base fields
        for field in BASE_FIELDS:
            headers.append(f"{service_name}_{field}_{mode}")

        # Standard fields
        headers.extend(
            [
                f"{service_name}_response_size_{mode}",
                f"{service_name}_num_routes_{mode}",
            ]
        )

        # Extra fields
        for field in service_config.get("extra_fields", []):
            headers.append(f"{service_name}_{field}_{mode}")

    return headers


def test_transport_routing():
    """Test transport/transit routing services."""
    filename = "transport_comparison.csv"
    mode = "transport"

    headers = ["origin", "destination", "routing_mode"] + get_headers_for_services(
        TRANSPORT_SERVICES, mode
    )

    for origin, destination in coordinates_list:
        row = {
            "origin": origin,
            "destination": destination,
            "routing_mode": "Public Transport",
        }

        # Query all transport services
        for service_name, service_config in TRANSPORT_SERVICES.items():
            result, size = query_service_for_mode(
                service_name, service_config, origin, destination
            )
            service_data = extract_service_data(
                service_name, service_config, result, size, mode
            )
            row.update(service_data)

        write_result(row, filename=filename, headers=headers)

    return filename


def test_driving_routing():
    """Test driving/car routing services."""
    filename = "driving_comparison.csv"
    mode = "driving"

    headers = ["origin", "destination", "routing_mode"] + get_headers_for_services(
        DRIVING_SERVICES, mode
    )

    for origin, destination in coordinates_list:
        row = {
            "origin": origin,
            "destination": destination,
            "routing_mode": "Driving",
        }

        # Query all driving services
        for service_name, service_config in DRIVING_SERVICES.items():
            result, size = query_service_for_mode(
                service_name, service_config, origin, destination
            )
            service_data = extract_service_data(
                service_name, service_config, result, size, mode
            )
            row.update(service_data)

        write_result(row, filename=filename, headers=headers)

    return filename


def compare_all_routing_modes(verbose=False):
    """Compare both transport and driving routing modes."""

    # Test transport routing
    transport_file = test_transport_routing()

    # Test driving routing
    driving_file = test_driving_routing()

    if verbose:
        print(f"Transport comparison saved to {transport_file}")
        print(f"Driving comparison saved to {driving_file}")


if __name__ == "__main__":
    # Test both modes
    compare_all_routing_modes(verbose=True)
