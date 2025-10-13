import math
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import httpx
import polyline

from src.core.config import settings
from tests.utils.commons import TIME_BENCH, client, motis_payload
from tests.utils.models import QueryResult, RouteSummary


def retry_api_call(func, max_retries=2):
    """Retry API calls with exponential backoff."""
    import time

    for attempt in range(max_retries + 1):
        try:
            return func()
        except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            if attempt == max_retries:
                raise e
            wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
            print(
                f"API call failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {wait_time}s..."
            )
            time.sleep(wait_time)
    return None


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def polyline_distance(points):
    dist = 0
    for i in range(1, len(points)):
        dist += haversine(
            points[i - 1][0], points[i - 1][1], points[i][0], points[i][1]
        )
    return dist


# -------------------------------------- Motis ------------------------------------ #
def query_motis(origin, destination, time=TIME_BENCH, **kwargs) -> QueryResult:
    """Query MOTIS API and return standardized result."""
    payload = motis_payload(origin, destination, time=time, **kwargs)
    try:
        response = client.post("/ab-routing", json=payload)
        response_size = len(response.content)
        data = response.json()
        return QueryResult.success_result(data, response_size)
    except Exception as e:
        error_msg = f"Error calling AB-routing for {origin} -> {destination}: {e}"
        print(error_msg)
        return QueryResult.error_result(error_msg)


def extract_motis_route_summary(result: Dict[str, Any]) -> RouteSummary:
    """Extract route summary from MOTIS response data."""
    routes = result.get("result", {}).get("itineraries", [])
    direct_routes = result.get("result", {}).get("direct", [])

    if routes:
        route = routes[0]
    else:
        # Try direct route if no itineraries
        if not direct_routes:
            print("No route found:", result)
            return RouteSummary.empty_summary()
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
        elif "legGeometry" in leg and "points" in leg["legGeometry"]:
            pts = polyline.decode(
                leg["legGeometry"]["points"], leg["legGeometry"].get("precision", 5)
            )
            distance += polyline_distance(pts)
        elif "from" in leg and "to" in leg:
            distance += haversine(
                leg["from"]["lat"],
                leg["from"]["lon"],
                leg["to"]["lat"],
                leg["to"]["lon"],
            )
        else:
            print(f"Warning: No distance found for leg: {leg}")

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

    return RouteSummary(
        duration_s=duration,
        distance_m=distance,
        num_routes=len(routes) if routes else len(direct_routes),
        modes=modes,
        vehicle_lines=vehicle_lines,
    )


# --------------------------- Google ---------------------- #
def query_google(
    origin,
    destination,
    mode="transit",
    time=TIME_BENCH,
    api_key=str(settings.GOOGLE_API_KEY),
) -> QueryResult:
    """Query Google Directions API and return standardized result."""
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

    def make_request():
        with httpx.Client() as client_http:
            response = client_http.get(url, params=params)
            response.raise_for_status()
            response_size = len(response.content)
            data = response.json()
            return data, response_size

    try:
        data, response_size = retry_api_call(make_request)
        return QueryResult.success_result(data, response_size)
    except Exception as e:
        error_msg = f"Error calling Google Directions API: {e}"
        return QueryResult.error_result(error_msg)


def extract_google_route_summary(directions_result):
    """
    Extract only the first route summary from a Google Directions API response.
    Returns a RouteSummary object.
    """
    routes = directions_result.get("routes", [])
    if not routes:
        return RouteSummary.empty_summary()

    legs = routes[0].get("legs", [])
    if not legs:
        return RouteSummary.empty_summary()

    leg = legs[0]  # take first leg
    duration = leg.get("duration", {}).get("value", 0)
    distance = leg.get("distance", {}).get("value", 0)

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

    return RouteSummary(
        duration_s=duration,
        distance_m=distance,
        num_routes=len(routes),
        modes=modes,
        vehicle_lines=vehicle_lines,
    )


def extract_google_driving_route_summary(response: Dict[str, Any]) -> RouteSummary:
    """Extract route summary from Google Maps driving directions."""

    if not response or "routes" not in response:
        return RouteSummary.empty_summary()

    routes = response["routes"]
    if not routes:
        return RouteSummary.empty_summary()

    # Use the first route
    route = routes[0]
    legs = route.get("legs", [])

    if not legs:
        return RouteSummary.empty_summary()

    # Sum up all legs
    total_duration = 0
    total_distance = 0

    for leg in legs:
        duration = leg.get("duration", {}).get("value", 0)
        distance = leg.get("distance", {}).get("value", 0)
        total_duration += duration
        total_distance += distance

    return RouteSummary(
        duration_s=total_duration,
        distance_m=total_distance,
        num_routes=len(routes),
        modes=["DRIVING"],  # For driving routes, always just DRIVING
        vehicle_lines=[],  # No vehicle lines for driving
    )


# -------------------------- Valhalla ---------------------- #
def query_valhalla(
    origin: str,
    destination: str,
    costing: str = "multimodal",
    endpoint: Optional[str] = None,
    **kwargs,
) -> Tuple[Optional[Dict[str, Any]], Optional[int]]:
    # Parse coordinates
    origin_lat, origin_lon = map(float, origin.split(","))
    dest_lat, dest_lon = map(float, destination.split(","))

    payload = {
        "locations": [
            {"lat": origin_lat, "lon": origin_lon},
            {"lat": dest_lat, "lon": dest_lon},
        ],
        "costing": costing,
        "directions_options": {
            "units": "kilometers",
            "narrative": True,
        },
        **kwargs,
    }

    # Add date_time for multimodal routing
    if costing == "multimodal":
        payload["date_time"] = {
            "type": 1,  # departure time
            "value": TIME_BENCH,  # use the same time as other services
        }

    # Choose endpoint based on parameter or service type
    if endpoint:
        url = endpoint
    elif costing == "auto":
        # Use no-GTFS endpoint for car routing
        url = settings.VALHALLA_NO_GTFS_URL
    else:
        # Use GTFS-enabled endpoint for multimodal/transit routing
        url = settings.VALHALLA_URL

    try:
        with httpx.Client() as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            response_size = len(response.content)
            data = response.json()
            return data, response_size

    except httpx.HTTPError as e:
        print(f"HTTP Error occurred while calling Valhalla API: {e}")
        return None, None
    except Exception as e:
        print(f"Error calling Valhalla for {origin} -> {destination}: {e}")
        return None, None


def extract_valhalla_route_summary(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not result or "trip" not in result:
        return None

    trip = result["trip"]
    legs = trip.get("legs", [])

    if not legs:
        return None

    # Calculate totals from legs
    total_time = trip.get("summary", {}).get("time", 0)  # in seconds
    total_length = trip.get("summary", {}).get("length", 0)  # in km

    # Extract transit and routing information
    modes = []
    vehicle_lines = []  # Bus/train line numbers from GTFS
    transit_stops = []
    agencies = []

    for leg in legs:
        # Extract travel mode/type
        travel_type = leg.get("type", leg.get("summary", {}).get("travel_type", ""))
        if travel_type and travel_type not in modes:
            modes.append(travel_type)

        # Extract detailed information from maneuvers
        maneuvers = leg.get("maneuvers", [])
        for maneuver in maneuvers:
            # Check travel type for each maneuver
            maneuver_travel_type = maneuver.get("travel_type")
            if maneuver_travel_type and maneuver_travel_type not in modes:
                modes.append(maneuver_travel_type)

            # Extract GTFS transit information
            transit_info = maneuver.get("transit_info", {})
            if transit_info:
                # Extract bus/train line numbers
                short_name = transit_info.get("short_name")
                if short_name and short_name not in vehicle_lines:
                    vehicle_lines.append(short_name)

                # Extract agency information
                agency_name = transit_info.get("agency_name")
                if agency_name and agency_name not in agencies:
                    agencies.append(agency_name)

                # Extract stop names
                stop_name = transit_info.get("stop_name")
                if stop_name and stop_name not in transit_stops:
                    transit_stops.append(stop_name)

    # Determine if this is a transit-enabled route
    has_transit_data = len(vehicle_lines) > 0 or any(
        mode in ["transit", "bus", "rail", "tram", "subway"] for mode in modes
    )

    return {
        "duration": total_time,
        "distance": total_length * 1000,  # convert km to meters for consistency
        "modes": modes,  # Travel modes (walking, transit, etc.)
        "vehicle_lines": vehicle_lines,  # Bus/train line numbers from GTFS
        "transit_stops": transit_stops[:5],  # Transit stops used
        "agencies": agencies,
        "total_transit_stops": len(transit_stops),
        "has_gtfs_data": has_transit_data,
        "costing_used": "multimodal_gtfs" if has_transit_data else "multimodal_no_gtfs",
        "note": (
            "GTFS-enabled multimodal routing with actual transit lines"
            if has_transit_data
            else "Multimodal routing without transit data"
        ),
    }
