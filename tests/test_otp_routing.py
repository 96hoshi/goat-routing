import time
from dataclasses import asdict, dataclass

import httpx
import psutil

from src.core.config import settings
from tests.conftest import write_response, write_result
from tests.utils.commons import coordinates_list
from tests.utils.models import RouteSummary, ServiceMetrics
from tests.utils.payload_builders import otp_payload

# Consistent CSV filenames
OTP_TRANSPORT_CSV_FILE = "otp_routes_transport.csv"
OTP_DRIVING_CSV_FILE = "otp_routes_driving.csv"
OTP_PERFORMANCE_FILE = "otp_performance.csv"


@dataclass
class OtpPerformanceStats:
    origin: str
    destination: str
    duration_ms: float
    cpu_s: float
    memory_mb: float
    response_size_bytes: int
    status_code: int


# -------------------------- OTP ---------------------- #
def query_otp(
    origin,
    destination,
    transport_modes: list[str] = ["TRANSIT", "WALK"],
    endpoint: str = str(settings.OPEN_TRIP_PLANNER_URL),
):
    """Query OpenTripPlanner GraphQL API and return standardized result."""
    origin_str = f"{origin[0]},{origin[1]}"
    destination_str = f"{destination[0]},{destination[1]}"

    payload = otp_payload(origin_str, destination_str, transport_modes=transport_modes)

    try:
        with httpx.Client() as client_http:
            response = client_http.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                print(f"OTP GraphQL errors: {data['errors']}")
                return {}, 0

            return data, len(response.content)

    except httpx.HTTPError as e:
        print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return {}, 0


def extract_otp_route_summary(response) -> RouteSummary:
    """Extract route summary from OTP GraphQL response."""

    def empty_summary():
        return RouteSummary(
            duration_s=0,
            distance_m=0.0,
            num_routes=0,
            modes=[],
            vehicle_lines=[],
        )

    if not response or "data" not in response:
        return empty_summary()

    plan = response["data"].get("plan", {})
    itineraries = plan.get("itineraries", [])
    if not itineraries:
        return empty_summary()

    # Use the first itinerary for summary
    first_itinerary = itineraries[0]

    # Extract basic metrics
    duration_seconds = first_itinerary.get("duration", 0)

    # Calculate total distance by summing all leg distances
    distance_meters = 0.0
    modes = []
    vehicle_lines = set()

    for leg in first_itinerary.get("legs", []):
        mode = leg.get("mode", "")
        if mode:
            modes.append(mode)
        # Extract route info for transit legs (non-null route)
        route = leg.get("route")
        if route is not None and isinstance(route, dict):
            short_name = route.get("shortName", "")
            if short_name:
                vehicle_lines.add(short_name)

        # Sum up leg distances
        leg_distance = leg.get("distance", 0)
        distance_meters += leg_distance

    return RouteSummary(
        duration_s=duration_seconds,
        distance_m=round(distance_meters, 3),
        num_routes=len(itineraries),
        modes=modes,
        vehicle_lines=list(vehicle_lines),
    )


def benchmark_otp_query(
    origin: str,
    destination: str,
    transport_modes: list[str] = ["TRANSIT", "WALK"],
    endpoint: str = str(settings.OPEN_TRIP_PLANNER_URL),
) -> ServiceMetrics:
    """
    Benchmark OTP GraphQL query with performance metrics and GraphQL error handling.
    Returns ServiceMetrics with timing, memory, and response data.
    """

    # Use minimal payload that works
    payload = otp_payload(origin, destination, transport_modes=transport_modes)

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
                timeout=45.0,
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


def test_otp_performance(mode: str = "TRANSIT"):
    """Test OTP routing with performance metrics."""
    if mode == "CAR":
        transport_modes = ["WALK", "CAR"]
    else:
        transport_modes = ["TRANSIT", "WALK"]

    for origin, destination in coordinates_list:
        print(f"\n🧪 Testing {origin} -> {destination}")

        # Benchmark the OTP query
        metrics = benchmark_otp_query(
            origin, destination, transport_modes=transport_modes
        )

        # Prepare stats object
        stats = OtpPerformanceStats(
            origin=origin,
            destination=destination,
            duration_ms=round(metrics.time_ms, 2),
            cpu_s=round(metrics.cpu_s, 4),
            memory_mb=round(metrics.mem_mb_delta, 2),
            response_size_bytes=metrics.response_size_bytes,
            status_code=metrics.status_code,
        )

        write_result(
            asdict(stats),
            filename=OTP_PERFORMANCE_FILE,
            headers=list(asdict(stats).keys()),
        )

        print(f"   ⏱️ Response time: {stats.duration_ms:.1f}ms")
        print(
            f"   🖥️ CPU: {stats.cpu_s:.4f}s, Memory: {stats.memory_mb:.2f}MB, Size: {stats.response_size_bytes} bytes, Status: {stats.status_code}"
        )


def test_otp_routing(mode: str = "TRANSIT"):
    """Test OTP routing and write to consistent comparison CSV files."""

    # Test coordinates (Mannheim area) for car routing
    def parse_coords(coord_str):
        lat, lon = map(float, coord_str.split(","))
        return lat, lon

    if mode == "CAR":
        transport_modes = ["WALK", "CAR"]
        csv_filename = OTP_DRIVING_CSV_FILE
        mode_suffix = "driving"
        print(f"🚗 Testing OTP driving routes, writing to {csv_filename}")
    else:
        transport_modes = ["TRANSIT", "WALK"]
        csv_filename = OTP_TRANSPORT_CSV_FILE
        mode_suffix = "transport"
        print(f"🚌 Testing OTP transport routes, writing to {csv_filename}")

    for i, coord in enumerate(coordinates_list, 1):
        origin = parse_coords(coord[0])
        destination = parse_coords(coord[1])

        print(f"\n[{i}/{len(coordinates_list)}] Testing {coord[0]} → {coord[1]}")

        data, size = query_otp(origin, destination, transport_modes=transport_modes)
        summary = extract_otp_route_summary(data)

        # Prepare row data in comparison format
        row = {
            "origin": coord[0],
            "destination": coord[1],
            "routing_mode": "Public Transport" if mode == "TRANSIT" else "Driving",
            "duration_s": summary.duration_s if summary else 0,
            "distance_m": summary.distance_m if summary else 0,
            "modes": ("|".join(summary.modes) if summary and summary.modes else ""),
            "vehicle_lines": (
                "|".join(summary.vehicle_lines)
                if summary and summary.vehicle_lines
                else ""
            ),
            "response_size_b": size,
            "num_routes": summary.num_routes if summary else 0,
        }

        # Write to comparison CSV
        write_result(row, filename=csv_filename, headers=list(row.keys()))

        # Save response for debugging
        response_filename = f"otp_{coord[0]}_{coord[1]}_{mode_suffix}.json".replace(
            ",", "_"
        )
        write_response(data, response_filename)

        print(
            f"   ✅ Duration: {row['duration_s']}, "
            f"Distance: {row['distance_m']}, "
            f"Routes: {row['num_routes']}"
        )

    print(f"✅ OTP {mode_suffix} results saved to {csv_filename}")


def test_both_modes():
    """Test both transport and driving modes, always writing to comparison files."""
    print("🗺️ Testing OTP for both transport and driving modes")
    print("=" * 60)

    # Test transport mode
    print("\n🚌 Starting TRANSIT mode testing...")
    test_otp_routing(mode="TRANSIT")
    test_otp_performance(mode="TRANSIT")

    # Test driving mode
    print("\n🚗 Starting CAR mode testing...")
    test_otp_routing(mode="CAR")
    # test_otp_performance(mode="CAR")

    print("\n✅ All OTP tests completed!")
    print(f"   Transport results: {OTP_TRANSPORT_CSV_FILE}")
    print(f"   Driving results: {OTP_DRIVING_CSV_FILE}")
    print(f"   Performance data: {OTP_PERFORMANCE_FILE}")


# Example usage and testing
if __name__ == "__main__":
    # Always test both modes and write to comparison files
    test_both_modes()
