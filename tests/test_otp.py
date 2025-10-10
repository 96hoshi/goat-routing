import time

import httpx
import psutil

from src.core.config import settings
from tests.conftest import write_result
from tests.utils.commons import coordinates_list
from tests.utils.models import ServiceMetrics
from tests.utils.query_helpers import extract_otp_route_summary, query_otp


def parse_coords(coord_str):
    lat, lon = map(float, coord_str.split(","))
    return lat, lon


def minimal_otp_payload(origin_str, destination_str) -> dict:
    """Build minimal OTP GraphQL payload that works with this instance."""
    lat1, lon1 = parse_coords(origin_str)
    lat2, lon2 = parse_coords(destination_str)

    return {
        "query": """
        query {
          plan(
            from: {lat: %f, lon: %f}
            to: {lat: %f, lon: %f}
          ) {
            itineraries {
              duration
              legs {
                mode
                distance
                from { name lat lon }
                to { name lat lon }
                route {
                  shortName
                }
              }
            }
          }
        }
        """
        % (lat1, lon1, lat2, lon2)
    }


def test_minimal_otp():
    """Test OTP with minimal GraphQL query."""
    import httpx

    # Minimal OTP query without extra parameters
    minimal_payload = {
        "query": """
        query {
          plan(
            from: {lat: 49.487459, lon: 8.466039}
            to: {lat: 49.48959, lon: 8.467236}
          ) {
            itineraries {
              duration
              legs {
                mode
                distance
                from { name }
                to { name }
              }
            }
          }
        }
        """
    }

    try:
        with httpx.Client() as client:
            response = client.post(
                "https://routing.klnavi.de/pedestrian/standard/otp/routers/default/index/graphql",
                json=minimal_payload,
                headers={"Content-Type": "application/json"},
                timeout=30.0,
            )

            print(f"Status: {response.status_code}")
            data = response.json()

            if "errors" in data:
                print(f"GraphQL Errors: {data['errors']}")
            elif "data" in data:
                plan = data.get("data", {}).get("plan", {})
                itineraries = plan.get("itineraries", [])
                print(f"Found {len(itineraries)} routes")

                if itineraries:
                    print("First route:")
                    for i, leg in enumerate(itineraries[0].get("legs", [])):
                        print(
                            f"  Leg {i+1}: {leg.get('mode')} - {leg.get('distance')}m"
                        )
                else:
                    print("Plan response:", plan)
            else:
                print("Unexpected response:", data)

    except Exception as e:
        print(f"Error: {e}")


def benchmark_otp_query(
    origin: str,
    destination: str,
    endpoint: str = str(settings.OPEN_TRIP_PLANNER_URL),
) -> ServiceMetrics:
    """
    Benchmark OTP GraphQL query with performance metrics and GraphQL error handling.
    Returns ServiceMetrics with timing, memory, and response data.
    """

    # Use minimal payload that works
    payload = minimal_otp_payload(origin, destination)

    # Performance measurement setup
    process = psutil.Process()
    response_size = 0
    status_code = -1
    response_data = {}

    # --- Measurement starts here ---
    mem_before_mb = process.memory_info().rss / (1024 * 1024)
    cpu_times_before = process.cpu_times()
    start_time = time.perf_counter()

    try:
        with httpx.Client() as client:
            response = client.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30.0,
            )

            status_code = response.status_code
            response.raise_for_status()

            # Successful HTTP response
            response_size = len(response.content)
            response_data = response.json()

    except httpx.RequestError as e:
        print(f"OTP HTTP request error: {e.__class__.__name__} - {e}")
        response_data = {"error": str(e)}

    except httpx.HTTPStatusError as e:
        print(f"OTP HTTP status error: {e.response.status_code} - {e}")
        status_code = e.response.status_code
        try:
            response_data = e.response.json()
        except Exception:
            response_data = {"error": e.response.text or "No response body"}

    except Exception as e:
        print(f"OTP unexpected error: {e.__class__.__name__} - {e}")
        response_data = {"error": str(e)}

    finally:
        # Always measure performance metrics
        end_time = time.perf_counter()
        cpu_times_after = process.cpu_times()
        mem_after_mb = process.memory_info().rss / (1024 * 1024)

    # --- Measurement ends here ---

    # Calculate performance deltas
    duration_ms = (end_time - start_time) * 1000
    cpu_delta_s = (cpu_times_after.user + cpu_times_after.system) - (
        cpu_times_before.user + cpu_times_before.system
    )
    mem_delta_mb = mem_after_mb - mem_before_mb

    # OTP-specific GraphQL error checking
    if status_code == 200 and isinstance(response_data, dict):
        if "errors" in response_data:
            print(f"⚠️ OTP GraphQL errors: {response_data['errors']}")
            # Log errors but don't fail the benchmark

        elif "data" in response_data:
            data_field = response_data.get("data", {})
            if isinstance(data_field, dict):
                plan = data_field.get("plan", {})
            else:
                plan = {}
            itineraries = plan.get("itineraries", [])

            if not itineraries:
                print("ℹ️ OTP: No routes found for the given parameters")
            else:
                print(f"✅ OTP: Found {len(itineraries)} route(s)")

                # Log route details for debugging
                for i, itin in enumerate(itineraries[:2]):  # Show first 2 routes
                    duration = itin.get("duration", 0)
                    modes = [leg.get("mode", "") for leg in itin.get("legs", [])]
                    print(f"   Route {i+1}: {duration}s, modes: {modes}")
        else:
            print("⚠️ OTP: Unexpected GraphQL response structure")

    return ServiceMetrics(
        time_ms=duration_ms,
        cpu_s=cpu_delta_s,
        mem_mb_delta=mem_delta_mb,
        response_size_bytes=response_size,
        status_code=status_code,
        response_data=response_data,
    )


def test_otp_performance():
    """Test OTP routing with performance metrics."""
    headers = [
        "origin",
        "destination",
        "duration_ms",
        "cpu_s",
        "memory_mb",
        "response_size_bytes",
        "status_code",
        "route_duration",
        "route_distance",
        "modes",
        "vehicle_lines",
    ]

    for origin, destination in coordinates_list:
        print(f"\n🧪 Testing {origin} -> {destination}")

        # Benchmark the OTP query
        metrics = benchmark_otp_query(origin, destination)

        # Extract route summary from response
        if isinstance(metrics.response_data, dict):
            route_summary = extract_otp_route_summary(metrics.response_data)
        else:
            route_summary = {}

        # Prepare CSV row
        row = {
            "origin": origin,
            "destination": destination,
            "duration_ms": round(metrics.time_ms, 2),
            "cpu_s": round(metrics.cpu_s, 4),
            "memory_mb": round(metrics.mem_mb_delta, 2),
            "response_size_bytes": metrics.response_size_bytes,
            "status_code": metrics.status_code,
            "route_duration": route_summary.get("duration", 0),
            "route_distance": route_summary.get("distance", 0),
            "modes": "|".join(route_summary.get("modes", [])),
            "vehicle_lines": "|".join(route_summary.get("vehicle_lines", [])),
        }

        write_result(row, filename="otp_performance.csv", headers=headers)

        print(f"   ⏱️ Response time: {metrics.time_ms:.1f}ms")
        print(
            f"   📊 Route: {route_summary.get('duration', 0)}s, {route_summary.get('distance', 0)}km"
        )


def test_otp_routing():
    # Test coordinates (Mannheim area) for car routing
    for coord in coordinates_list:
        origin = parse_coords(coord[0])
        destination = parse_coords(coord[1])
        row = {
            "origin": origin,
            "destination": destination,
            "response_size_bytes": 0,
        }
        data, size = query_otp(origin, destination)
        summary = extract_otp_route_summary(data)
        row["response_size_bytes"] = size
        row.update(summary)
        write_result(row, filename="otp.csv", headers=list(row.keys()))

        print(f"Response size: {size} bytes")

        if data:
            print(data)


# Example usage and testing
if __name__ == "__main__":

    # test_otp_routing()
    test_otp_performance()
