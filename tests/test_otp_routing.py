import time
from dataclasses import dataclass

import httpx
import psutil
import pytest

from src.core.config import settings
from tests.conftest import write_result
from tests.utils.models import ServiceMetrics
from tests.utils.payload_builders import otp_payload
from tests.utils.query_helpers import extract_otp_route_summary, query_otp

# Consistent CSV filenames
OTP_TRANSPORT_CSV_FILE = "otp_routes_transport.csv"
OTP_DRIVING_CSV_FILE = "otp_routes_driving.csv"
OTP_PERFORMANCE_FILE = "otp_performance.csv"

mannheim_list = [
    (
        ("49.487459,8.466039"),
        ("49.452030,8.468946"),
    ),  # Mannheim Hbf to Mannheim Neckarau
    (("49.487459,8.466039"), ("49.395428,8.672437")),  # Mannheim Hbf to Ludwigshafen
    (("49.395428,8.672437"), ("49.487459,8.466039")),  # Ludwigshafen to Mannheim Hbf
]


@dataclass
class OtpPerformanceStats:
    origin: str
    destination: str
    duration_ms: float
    cpu_s: float
    memory_mb: float
    response_size_bytes: int
    status_code: int


def parse_coords(coord_str):
    lat, lon = map(float, coord_str.split(","))
    return lat, lon


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


@pytest.mark.parametrize("mode", ["TRANSIT", "CAR"])
@pytest.mark.parametrize("origin,destination", mannheim_list)
def test_otp_performance(origin, destination, mode):
    """Test OTP routing performance for given origin-destination pairs and transport modes."""

    # Benchmark the OTP query
    metrics = benchmark_otp_query(origin, destination, transport_modes=[mode])

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

    print(f"   ⏱️ Response time: {stats.duration_ms:.1f}ms")
    print(
        f"   🖥️ CPU: {stats.cpu_s:.4f}s, Memory: {stats.memory_mb:.2f}MB, Size: {stats.response_size_bytes} bytes, Status: {stats.status_code}"
    )


@pytest.mark.parametrize("mode", ["TRANSIT", "CAR"])
@pytest.mark.parametrize("origin,destination", mannheim_list)
def test_otp_routing(origin, destination, mode, response_writer):
    """Test OTP routing and write to consistent comparison CSV files."""

    # Test coordinates (Mannheim area) for car routing
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
    # Query OTP
    parsed_origin = parse_coords(origin)
    parsed_destination = parse_coords(destination)
    response = query_otp(
        parsed_origin, parsed_destination, transport_modes=transport_modes
    )
    data = response.data
    size = response.response_size

    summary = extract_otp_route_summary(data)

    # Prepare row data in comparison format
    row = {
        "origin": parsed_origin,
        "destination": parsed_destination,
        "routing_mode": "Public Transport" if mode == "TRANSIT" else "Driving",
        "duration_s": summary.duration_s if summary else 0,
        "distance_m": summary.distance_m if summary else 0,
        "modes": ("|".join(summary.modes) if summary and summary.modes else ""),
        "vehicle_lines": (
            "|".join(summary.vehicle_lines) if summary and summary.vehicle_lines else ""
        ),
        "response_size_b": size,
        "num_routes": summary.num_routes if summary else 0,
    }

    # Write to comparison CSV
    write_result(row, filename=csv_filename, headers=list(row.keys()))

    # Save response for debugging
    response_writer.save(
        response.data,
        filename=f"otp_{origin}_{destination}_{mode_suffix}.json".replace(",", "_"),
    )

    print(
        f"   ✅ Duration: {row['duration_s']}, "
        f"Distance: {row['distance_m']}, "
        f"Routes: {row['num_routes']}"
    )
