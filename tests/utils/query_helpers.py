import logging
import math
from typing import Any, Dict, Optional

import httpx
import polyline

from src.core.config import settings
from tests.conftest import TIME_BENCH
from tests.utils.commons import client
from tests.utils.models import QueryResult, RouteSummary
from tests.utils.payload_builders import (
    google_payload,
    motis_payload,
    valhalla_payload,
)


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
        response = client.post(settings.MOTIS_ROUTE, json=payload)
        response_size = len(response.content)
        data = response.json()
        return QueryResult.success_result(data, response_size)
    except Exception as e:
        error_msg = f"Error calling AB-routing for {origin} -> {destination}: {e}"
        return QueryResult.error_result(error_msg)


def query_motis_by_payload(payload: Dict[str, str]) -> QueryResult:
    """Query MOTIS API and return standardized result."""
    try:
        response = client.post(settings.MOTIS_ROUTE, json=payload)
        response.raise_for_status()
        response_size = len(response.content)
        data = response.json()
        http_status = response.status_code  # Get the HTTP response code

        return QueryResult.success_result(data, response_size, http_status)
    except Exception as e:
        error_msg = f"Error: {e}"
        return QueryResult.error_result(error_msg)


def extract_motis_route_summary(result: Dict[str, Any]) -> RouteSummary:
    """Extract route summary from MOTIS response data."""
    # Early validation
    if not result or "result" not in result:
        logging.warning("Invalid MOTIS response structure: missing 'result'")
        return RouteSummary.empty_summary()

    result_data = result["result"]
    routes = result_data.get("itineraries", [])
    direct_routes = result_data.get("direct", [])

    # Select the first available route
    route = None
    if routes:
        route = routes[0]
        route_source = "itineraries"
    elif direct_routes:
        route = direct_routes[0]
        route_source = "direct"
    else:
        logging.info("No routes found in MOTIS response")
        return RouteSummary.empty_summary()

    # Extract duration with fallback calculation
    duration = route.get("duration")
    if duration is None:
        # Calculate from legs if duration not provided
        legs = route.get("legs", [])
        duration = sum(leg.get("duration", 0) for leg in legs)
        if duration == 0:
            logging.warning(f"No duration found in {route_source} route")

    # Extract distance with improved error handling
    distance = 0
    polyline_cache = {}
    legs = route.get("legs", [])

    for i, leg in enumerate(legs):
        leg_distance = 0

        # Method 1: Direct distance field
        if "distance" in leg:
            leg_distance = leg["distance"]

        # Method 2: Decode polyline geometry
        elif "legGeometry" in leg and "points" in leg["legGeometry"]:
            try:
                points_str = leg["legGeometry"]["points"]
                precision = leg["legGeometry"].get("precision", 5)
                points_key = (points_str, precision)

                if points_key in polyline_cache:
                    pts = polyline_cache[points_key]
                else:
                    pts = polyline.decode(points_str, precision)
                    polyline_cache[points_key] = pts

                if len(pts) > 1:  # Need at least 2 points for distance
                    leg_distance = polyline_distance(pts)
                else:
                    logging.warning(
                        f"Leg {i}: Polyline has insufficient points ({len(pts)})"
                    )

            except Exception as e:
                logging.warning(f"Leg {i}: Failed to decode polyline: {e}")
                # Fall back to haversine calculation
                if "from" in leg and "to" in leg:
                    leg_distance = _calculate_haversine_distance(leg)

        # Method 3: Haversine calculation from coordinates
        elif "from" in leg and "to" in leg:
            leg_distance = _calculate_haversine_distance(leg)

        # Method 4: No distance information available
        else:
            logging.warning(
                f"Leg {i}: Cannot determine distance - no geometry or coordinates"
            )
            continue

        distance += leg_distance

    # Extract modes and vehicle lines with improved parsing
    modes, vehicle_lines = _extract_transport_info(route.get("legs", []))

    # Determine number of routes
    num_routes = len(routes) if routes else len(direct_routes)

    return RouteSummary(
        duration_s=duration,
        distance_m=int(distance),
        num_routes=num_routes,
        modes=modes,
        vehicle_lines=vehicle_lines,
    )


def _calculate_haversine_distance(leg: Dict[str, Any]) -> float:
    """Calculate distance between two points using haversine formula."""
    try:
        from_coord = leg["from"]
        to_coord = leg["to"]

        # Validate coordinates
        from_lat = from_coord.get("lat")
        from_lon = from_coord.get("lon")
        to_lat = to_coord.get("lat")
        to_lon = to_coord.get("lon")

        if None in [from_lat, from_lon, to_lat, to_lon]:
            logging.warning("Invalid coordinates in leg")
            return 0.0

        return haversine(from_lat, from_lon, to_lat, to_lon)

    except (KeyError, TypeError) as e:
        logging.warning(f"Error calculating haversine distance: {e}")
        return 0.0


def _extract_transport_info(legs: list) -> tuple[list, list]:
    """Extract transportation modes and vehicle lines from route legs."""
    modes = []
    vehicle_lines = []

    for i, leg in enumerate(legs):
        # Extract mode with multiple fallbacks
        mode = None
        if "mode" in leg:
            mode = leg["mode"]
        elif "transport_mode" in leg:
            mode = leg["transport_mode"]
        elif "transports" in leg:
            # Handle multiple transports in a leg
            for transport in leg["transports"]:
                transport_mode = transport.get("mode", "unknown")
                if transport_mode not in modes:
                    modes.append(transport_mode)

        if mode:
            modes.append(mode)
        elif mode is None:
            logging.debug(f"Leg {i}: No transport mode found")
            modes.append("unknown")

        # Extract vehicle line information
        route_info = _extract_route_info(leg)
        if route_info:
            vehicle_lines.extend(route_info)

    return modes, vehicle_lines


def _extract_route_info(leg: Dict[str, Any]) -> list:
    """Extract route/line information from a single leg."""
    route_names = []

    # Check various possible fields for route information
    route_fields = [
        "routeShortName",
        "route_short_name",
        "shortName",
        "lineName",
        "line_name",
    ]

    for field in route_fields:
        if field in leg and leg[field]:
            route_name = str(leg[field]).strip()
            if route_name and route_name not in route_names:
                route_names.append(route_name)

    # Check nested transport information
    if "transports" in leg:
        for transport in leg["transports"]:
            for field in route_fields:
                if field in transport and transport[field]:
                    route_name = str(transport[field]).strip()
                    if route_name and route_name not in route_names:
                        route_names.append(route_name)

    return route_names


# --------------------------- Google ---------------------- #
def query_google(
    origin,
    destination,
    mode="transit",
    time=TIME_BENCH,
    api_key=str(settings.GOOGLE_API_KEY),
) -> QueryResult:
    """Query Google Directions API and return standardized result."""

    params = google_payload(origin, destination, mode=mode, time=time, api_key=api_key)
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
) -> QueryResult:
    """Query Valhalla API and return standardized result."""
    payload = valhalla_payload(
        origin, destination, costing=costing, time=TIME_BENCH, **kwargs
    )

    if endpoint:
        url = endpoint
    elif costing == "auto":
        url = settings.VALHALLA_NO_GTFS_URL
    else:
        url = settings.VALHALLA_URL

    try:
        with httpx.Client() as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            response_size = len(response.content)
            data = response.json()
            return QueryResult.success_result(data, response_size)
    except Exception as e:
        error_msg = f"Error calling Valhalla API for {origin} -> {destination}: {e}"
        print(error_msg)
        return QueryResult.error_result(error_msg)


def extract_valhalla_route_summary(result: Dict[str, Any]) -> RouteSummary:
    if not result or "trip" not in result:
        return RouteSummary.empty_summary()

    trip = result["trip"]
    legs = trip.get("legs", [])

    if not legs:
        return RouteSummary.empty_summary()

    # Calculate totals from legs
    total_time = trip.get("summary", {}).get("time", 0)  # in seconds
    total_length = trip.get("summary", {}).get("length", 0)  # in km

    # Extract transit and routing information
    modes = []
    vehicle_lines = []

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

    return RouteSummary(
        duration_s=total_time,
        distance_m=total_length * 1000,  # convert km to meters for consistency
        num_routes=1,
        modes=modes,
        vehicle_lines=vehicle_lines,
    )
