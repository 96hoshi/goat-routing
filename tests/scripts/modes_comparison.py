"""
Clean routing comparison with proper separation of transport vs driving modes.
- Transport: MOTIS (transit), Google (transit), OTP (multimodal), Valhalla (auto)
- Driving: Google (driving), Valhalla-NoGTFS (auto)
"""

from datetime import datetime

from tests.conftest import write_result
from tests.utils.commons import coordinates_list
from tests.utils.models import RouteSummary
from tests.utils.query_helpers import (
    extract_google_driving_route_summary,
    extract_google_route_summary,
    extract_motis_route_summary,
    query_google,
    query_motis,
)

# Configuration flags to enable/disable modes for comparison
DRIVE = True
TRANSPORT = True

TRANSPORT_COMPARISON_CSV = "transport_comparison.csv"
DRIVING_COMPARISON_CSV = "driving_comparison.csv"

# Transport services (public transit)
TRANSPORT_SERVICES = {
    "motis": {
        "query_func": query_motis,
        "extract_func": extract_motis_route_summary,
        "query_params": {
            "transitModes": ["TRANSIT"],
            "maxItineraries": 6,
            "detailedTransfers": False,
        },
        "routes_path": ["result", "itineraries"],
    },
    "google": {
        "query_func": query_google,
        "extract_func": extract_google_route_summary,
        "query_params": {"mode": "transit"},
        "routes_path": ["routes"],
    },
}

# Driving services (car routing)
DRIVING_SERVICES = {
    "google": {
        "query_func": query_google,
        "extract_func": extract_google_driving_route_summary,
        "query_params": {"mode": "driving"},
        "routes_path": ["routes"],
    },
}

# EXCLUDE otp for now, it is haldelen in test_otp_routing.py


def query_service_for_mode(service_name, service_config, origin, destination):
    """Query a service with its specific configuration."""
    try:
        query_func = service_config["query_func"]
        params = service_config["query_params"].copy()

        # Call the query function
        result = query_func(origin, destination, **params)

        # Handle different return types
        if hasattr(result, "success"):
            # QueryResult object
            if result.success:
                return result.data, result.response_size
            else:
                print(f"❌ {service_name} query failed: {result.error_message}")
                return None, None
        elif isinstance(result, tuple) and len(result) == 2:
            # Tuple format (data, size) - works for OTP, Google, MOTIS
            return result[0], result[1]
        else:
            print(f"⚠️ Unexpected return format from {service_name}: {type(result)}")
            return None, None

    except Exception as e:
        print(f"❌ Error querying {service_name}: {e}")
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

    try:
        summary = extract_func(result) if result else None
    except Exception as e:
        print(f"⚠️ Error extracting {service_name} summary: {e}")
        summary = None

    num_routes = get_route_count(service_config, result)
    data = {}

    if summary and isinstance(summary, RouteSummary):
        # Use RouteSummary attributes directly
        data[f"{service_name}_duration_{mode}"] = summary.duration_s
        data[f"{service_name}_distance_{mode}"] = summary.distance_m
        data[f"{service_name}_modes_{mode}"] = (
            "|".join(summary.modes) if summary.modes else ""
        )
        data[f"{service_name}_vehicle_lines_{mode}"] = (
            "|".join(summary.vehicle_lines) if summary.vehicle_lines else ""
        )
    else:
        # Empty values if no summary
        data[f"{service_name}_duration_{mode}"] = ""
        data[f"{service_name}_distance_{mode}"] = ""
        data[f"{service_name}_modes_{mode}"] = ""
        data[f"{service_name}_vehicle_lines_{mode}"] = ""

    # Add standard fields
    data[f"{service_name}_response_size_{mode}"] = size if size is not None else 0
    data[f"{service_name}_num_routes_{mode}"] = num_routes

    return data


def get_headers_for_services(services, mode):
    """Generate CSV headers for a set of services using RouteSummary attributes."""
    headers = []

    # Get RouteSummary field names (excluding num_routes as it's handled separately)
    route_fields = ["duration", "distance", "modes", "vehicle_lines"]

    for service_name in services.keys():
        # RouteSummary fields
        for field in route_fields:
            headers.append(f"{service_name}_{field}_{mode}")

        # Standard fields
        headers.extend(
            [
                f"{service_name}_response_size_{mode}",
                f"{service_name}_num_routes_{mode}",
            ]
        )

    return headers


def test_transport_routing():
    """Test transport/transit routing services."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = TRANSPORT_COMPARISON_CSV.replace(".csv", f"_{timestamp}.csv")

    # --- The rest of the function is UNCHANGED ---
    mode = "transport"

    headers = ["origin", "destination", "routing_mode"] + get_headers_for_services(
        TRANSPORT_SERVICES, mode
    )

    print(f"🚌 Testing {len(coordinates_list)} transport routes...")

    for i, (origin, destination) in enumerate(coordinates_list, 1):
        print(f"\n[{i}/{len(coordinates_list)}] Testing {origin} → {destination}")

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

    print(f"✅ Transport comparison saved to {filename}")
    return filename


def test_driving_routing():
    """Test driving/car routing services."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = DRIVING_COMPARISON_CSV.replace(".csv", f"_{timestamp}.csv")
    mode = "driving"

    headers = ["origin", "destination", "routing_mode"] + get_headers_for_services(
        DRIVING_SERVICES, mode
    )

    print(f"🚗 Testing {len(coordinates_list)} driving routes...")

    for _i, (origin, destination) in enumerate(coordinates_list, 1):
        row = {
            "origin": origin,
            "destination": destination,
            "routing_mode": "Driving",
        }

        for service_name, service_config in DRIVING_SERVICES.items():
            result, size = query_service_for_mode(
                service_name, service_config, origin, destination
            )
            service_data = extract_service_data(
                service_name, service_config, result, size, mode
            )
            row.update(service_data)

        write_result(row, filename=filename, headers=headers)

    print(f"✅ Driving comparison saved to {filename}")
    return filename


def compare_routing_modes():
    """Compare both transport and driving routing modes."""

    # Test transport routing
    if TRANSPORT:
        transport_file = test_transport_routing()
        print(f"   Transport: /app/tests/results/{transport_file}")

    if DRIVE:
        driving_file = test_driving_routing()
        print(f"   Driving: /app/tests/results/{driving_file}")


if __name__ == "__main__":
    compare_routing_modes()
