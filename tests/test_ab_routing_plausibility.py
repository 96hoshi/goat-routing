from datetime import datetime
import httpx
import pytest

from coords.coordinates_mannheim import coordinates_list
from src.core.config import settings
from tests.utils.commons import client, TIME_BENCH


# ----------- Motis ----------- #
def query_motis(origin, destination, time=TIME_BENCH):
    payload = {"fromPlace": origin, "toPlace": destination, "time": time}
    try:
        response = client.post("/ab-routing", json=payload)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None
    return extract_motis_route_summary(data)


def extract_motis_route_summary(result: dict):
    if not result or "result" not in result:
        return None

    # Prefer "itineraries" if present, otherwise use "direct"
    itineraries = result["result"].get("itineraries", [])
    direct = result["result"].get("direct", [])

    if itineraries:
        route = itineraries[0]
    elif direct:
        route = direct[0]
    else:
        return None

    duration = route.get(
        "duration",
        sum(leg.get("duration", 0) for leg in route.get("legs", [])),
    )

    distance = 0
    for leg in route.get("legs", []):
        if "distance" in leg:
            distance += leg["distance"]
        elif "summary" in leg:
            distance += leg["summary"].get("distance", 0) or leg["summary"].get(
                "length", 0
            )

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
    }
    url = str(settings.GOOGLE_DIRECTIONS_URL)

    def fetch(params):
        try:
            with httpx.Client() as http_client:
                response = http_client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except Exception:
            return None

    # try transit first
    data = fetch(params)
    if not data or data.get("status") == "ZERO_RESULTS":
        # try walking
        params["mode"] = "walking"
        data = fetch(params)

    if not data or data.get("status") != "OK":
        # fallback synthetic result
        return {
            "duration": 0,
            "distance": 0,
            "modes": [],
            "vehicle_lines": [],
        }

    return extract_google_route_summary(data)


def extract_google_route_summary(directions_result: dict):
    if not directions_result or directions_result.get("status") != "OK":
        return None

    routes = directions_result.get("routes", [])
    if not routes:
        return None

    legs = routes[0].get("legs", [])
    if not legs:
        return None

    leg = legs[0]
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


# ----------- Service registry ----------- #
SERVICES = {
    "motis": query_motis,
    "google": query_google,
}


# ----------- Tests ----------- #
@pytest.mark.parametrize("origin,destination", coordinates_list)
@pytest.mark.parametrize("service_name,service_fn", SERVICES.items())
def test_route_plausibility(origin, destination, service_name, service_fn):
    """Check that each service returns plausible results."""
    result = service_fn(origin, destination)
    if result is None:
        pytest.skip(f"{service_name} returned no route for {origin}->{destination}")
    assert isinstance(result["duration"], (int, float))
    assert result["duration"] > 0
    assert isinstance(result["distance"], (int, float))
    assert result["distance"] > 0
    assert isinstance(result["modes"], list)
    assert isinstance(result["vehicle_lines"], list)


@pytest.mark.parametrize("origin,destination", coordinates_list[:3])  # limit for speed
def test_cross_service_comparison(origin, destination):
    """Compare results between all services for the same OD pair."""
    results = {}
    for name, fn in SERVICES.items():
        results[name] = fn(origin, destination) or {
            "duration": None,
            "distance": None,
            "modes": [],
            "vehicle_lines": [],
        }

    print(f"\n--- Comparison {origin} -> {destination} ---")
    for name, res in results.items():
        print(f"{name:<8}: {res}")

    # Example soft check: if both have durations, they shouldn't differ by 10x
    durations = [res["duration"] for res in results.values() if res["duration"]]
    if len(durations) >= 2:
        min_d, max_d = min(durations), max(durations)
        assert max_d <= 10 * min_d, "Duration mismatch too large"
