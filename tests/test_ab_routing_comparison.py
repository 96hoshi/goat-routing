from datetime import datetime

import httpx

from src.core.config import settings
from tests.utils.commons import (
    TIME_BENCH,
    client,
    coordinates_list,
    motis_payload,
    write_result,
)

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


# ---------- Motis Routing ---------- #
def get_motis_route(origin, destination, time=TIME_BENCH):
    payload = motis_payload(origin, destination, time)
    try:
        response = client.post("/ab-routing", json=payload)
        response_size = len(response.content)
        data = response.json()
        num_routes = len(data.get("result", {}).get("itineraries", []))
        return data, response_size, num_routes
    except Exception as e:
        print(f"Error calling AB-routing for {origin} -> {destination}: {e}")
        return None, None, 0


def extract_motis_route_summary(result):
    """
    Extract only the first route summary from a Motis API response.
    """
    routes = result.get("result", {}).get("itineraries", [])
    if not routes:
        return None

    route = routes[0]  # take first option only

    # Total duration
    duration = route.get(
        "duration", sum(leg.get("duration", 0) for leg in route.get("legs", []))
    )

    # Total distance
    distance = 0
    for leg in route.get("legs", []):
        if "distance" in leg:
            distance += leg["distance"]
        elif "summary" in leg:
            distance += leg["summary"].get("distance", 0) or leg["summary"].get(
                "length", 0
            )

    # Modes and vehicle lines
    modes, vehicle_lines = [], []
    for leg in route.get("legs", []):
        if "mode" in leg:
            modes.append(leg["mode"])
        elif "transport_mode" in leg:
            modes.append(leg["transport_mode"])
        elif "transports" in leg:
            for t in leg["transports"]:
                modes.append(t.get("mode", "unknown"))
        else:
            modes.append("unknown")

        route_name = leg.get("routeShortName")
        if route_name:
            vehicle_lines.append(route_name)

    return {
        "duration": duration,
        "distance": distance,
        "modes": modes,
        "vehicle_lines": vehicle_lines,
    }


# ---------- Google Direction ---------- #
def get_google_directions(
    origin,
    destination,
    mode="transit",
    time=TIME_BENCH,
    api_key=str(settings.GOOGLE_API_KEY),
):
    dt = datetime.fromisoformat(time.replace("Z", "+00:00"))
    departure_timestamp = int(dt.timestamp())
    params = {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "departure_time": departure_timestamp,
        "key": api_key,
    }
    url = str(settings.GOOGLE_DIRECTIONS_URL)
    try:
        with httpx.Client() as client_http:
            response = client_http.get(url, params=params)
            response.raise_for_status()
            response_size = len(response.content)
            data = response.json()
            num_routes = len(data.get("routes", []))
            return data, response_size, num_routes
    except httpx.HTTPError as e:
        print(f"HTTP Error occurred while calling Google Directions API: {e}")
        return None, None, 0
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None, 0


def extract_google_route_summary(directions_result):
    """
    Extract only the first route summary from a Google Directions API response.
    """
    routes = directions_result.get("routes", [])
    if not routes:
        return None

    legs = routes[0].get("legs", [])
    if not legs:
        return None

    leg = legs[0]  # take first leg
    duration = leg["duration"]["value"]
    distance = leg["distance"]["value"]

    modes, vehicle_lines = [], []
    for step in leg.get("steps", []):
        transit_details = step.get("transit_details", {})
        line_info = transit_details.get("line", {})
        vehicle_type = line_info.get("vehicle", {}).get("type")
        line_name = line_info.get("short_name")

        if vehicle_type:
            modes.append(vehicle_type)
            if line_name:
                vehicle_lines.append(line_name)
        else:
            modes.append(step.get("travel_mode", "UNKNOWN"))

    return {
        "duration": duration,
        "distance": distance,
        "modes": modes,
        "vehicle_lines": vehicle_lines,
    }


# ---------- Benchmarking ---------- #
def evaluate_service_responses():
    for origin, destination in coordinates_list:
        motis_result, motis_size, motis_num_routes = get_motis_route(
            origin, destination
        )
        motis_summary = (
            extract_motis_route_summary(motis_result) if motis_result else None
        )
        google_result, google_size, google_num_routes = get_google_directions(
            origin, destination
        )
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


if __name__ == "__main__":
    evaluate_service_responses()
