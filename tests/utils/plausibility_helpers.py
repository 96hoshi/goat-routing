from datetime import datetime

import httpx

from src.core.config import settings
from tests.utils.commons import (
    TIME_BENCH,
    client,
    motis_payload,
    write_response,
)


# ----------- Motis ----------- #
def query_motis(origin, destination, time=TIME_BENCH):
    payload = motis_payload(origin, destination, time)
    try:
        response = client.post("/ab-routing", json=payload)
        response_size = len(response.content)
        data = response.json()
        write_response(data, filename="motis_{}_{}.txt".format(origin, destination))
        return data, response_size
    except Exception as e:
        print(f"Error calling AB-routing for {origin} -> {destination}: {e}")
        return None, None


def extract_motis_route_summary(result):
    """
    Extract the first available route summary from a Motis API response.
    Handles both 'itineraries' (public transport) and 'direct' (walk/bike/car).
    """
    routes = result.get("result", {}).get("itineraries", [])
    if routes:
        route = routes[0]
    else:
        # Try direct route if no itineraries
        direct_routes = result.get("result", {}).get("direct", [])
        if not direct_routes:
            print("No route found:", result)
            return None
        route = direct_routes[0]

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


# ----------- Google ----------- #
def query_google(
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
        "alternatives": "true",  # default is 1
    }
    url = str(settings.GOOGLE_DIRECTIONS_URL)
    try:
        with httpx.Client() as client_http:
            response = client_http.get(url, params=params)
            response.raise_for_status()
            response_size = len(response.content)
            data = response.json()
            write_response(
                data, filename="google_{}_{}.txt".format(origin, destination)
            )
            return data, response_size
    except httpx.HTTPError as e:
        print(f"HTTP Error occurred while calling Google Directions API: {e}")
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None


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
