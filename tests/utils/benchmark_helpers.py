import time

import httpx
import psutil

from tests.utils.models import ServiceMetrics


def build_result_row(
    service, origin, dest, avg_time, avg_cpu, avg_mem, response_size, rounds
):
    return {
        "service": service["name"],
        "origin": origin,
        "destination": dest,
        "avg_time_ms": f"{avg_time:.3f}",
        "avg_cpu_s": f"{avg_cpu:.4f}",
        "avg_mem_mb_delta": f"{avg_mem:.4f}",
        "avg_response_size_bytes": f"{response_size:.0f}",
        "rounds": rounds,
    }


def generic_query_service(client, endpoint, payload, method) -> ServiceMetrics:
    """Standard query for services with HTTP 2xx success criteria."""
    return _measure_request(client, endpoint, payload, method)


def google_query_service(client, endpoint, payload, method) -> ServiceMetrics:
    """Google-specific wrapper that validates API status."""
    metrics = _measure_request(client, endpoint, payload, method)

    # Validate Google's nested status
    if metrics.status_code == 200 and isinstance(metrics.response_data, dict):
        google_status = metrics.response_data.get("status")
        # You can add logic here if you want to handle non-OK statuses
        if google_status not in ["OK", "ZERO_RESULTS"]:
            print(f"⚠️ Google API returned status: {google_status}")

    return metrics


def otp_query_service(client, endpoint, payload, method) -> ServiceMetrics:
    """OTP GraphQL wrapper with error checking."""
    metrics = _measure_request(client, endpoint, payload, method)

    if metrics.status_code == 200 and isinstance(metrics.response_data, dict):
        # Check for GraphQL errors
        if "errors" in metrics.response_data:
            print(f"⚠️ OTP GraphQL errors: {metrics.response_data['errors']}")

        # Check for successful data
        elif "data" in metrics.response_data:
            plan = metrics.response_data.get("data", {}).get("plan", {})
            itineraries = plan.get("itineraries", [])

            if not itineraries:
                print("ℹ️ OTP: No routes found")
        else:
            print("⚠️ OTP: Unexpected response structure")

    return metrics


def _measure_request(
    client: httpx.Client, endpoint: str, payload: dict, method: str = "POST"
) -> ServiceMetrics:
    """Core measurement function with improved error handling."""
    process = psutil.Process()
    response_size = 0
    status_code = -1
    response_data = {}

    # Measurement starts
    mem_before_mb = process.memory_info().rss / (1024 * 1024)
    cpu_times_before = process.cpu_times()
    start_time = time.perf_counter()

    try:
        # Determine timeout based on method/service type
        timeout = 45.0
        if method.upper() == "POST" and any(
            key in str(payload) for key in ["plan", "itineraries"]
        ):
            timeout = 60.0  # Longer timeout for complex routing queries

        # Make the HTTP request
        if method.upper() == "POST":
            response = client.post(endpoint, json=payload, timeout=timeout)
        else:
            response = client.get(endpoint, params=payload, timeout=timeout)

        status_code = response.status_code
        response.raise_for_status()

        # Parse successful response
        response_size = len(response.content)
        try:
            response_data = response.json()
        except ValueError as e:
            print(f"⚠️ JSON parsing failed: {e}")
            response_data = {
                "error": "Invalid JSON response",
                "raw_content": response.text[:500],
            }

    except httpx.TimeoutException as e:
        print(f"⏱️ Request timeout {e}")
        response_data = {"error": "Request timed out"}

    except httpx.RequestError as e:
        print(f"🌐 Network error: {e.__class__.__name__} - {e}")
        response_data = {"error": str(e)}

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP {e.response.status_code}: {e}")
        status_code = e.response.status_code
        try:
            response_data = e.response.json()
        except Exception:
            response_data = {
                "error": (
                    e.response.text[:500] if e.response.text else "No response body"
                )
            }

    except Exception as e:
        print(f"💥 Unexpected error: {e.__class__.__name__} - {e}")
        response_data = {"error": str(e)}

    finally:
        # Measurement ends - this ALWAYS runs
        end_time = time.perf_counter()
        cpu_times_after = process.cpu_times()
        mem_after_mb = process.memory_info().rss / (1024 * 1024)

    # Calculate metrics
    duration_ms = (end_time - start_time) * 1000
    cpu_delta_s = (cpu_times_after.user + cpu_times_after.system) - (
        cpu_times_before.user + cpu_times_before.system
    )
    mem_delta_mb = mem_after_mb - mem_before_mb

    # Return with correct field names matching ServiceMetrics model
    return ServiceMetrics(
        time_ms=duration_ms,
        cpu_s=cpu_delta_s,
        mem_mb_delta=mem_delta_mb,
        response_size_bytes=response_size,
        status_code=status_code,
        response_data=response_data,
    )


# Helper function to validate service responses
def validate_service_response(metrics: ServiceMetrics, service_name: str) -> bool:
    """Validate if a service response contains valid routing data."""
    if metrics.status_code != 200:
        return False

    response_data = metrics.response_data
    if not response_data or (
        isinstance(response_data, dict) and "error" in response_data
    ):
        return False

    # Service-specific validation
    if service_name == "google":
        if isinstance(response_data, dict):
            return response_data.get("status") in ["OK", "ZERO_RESULTS"]

    elif service_name == "otp":
        if isinstance(response_data, dict):
            if "errors" in response_data:
                return False
            plan = response_data.get("data", {}).get("plan", {})
            return "itineraries" in plan

    elif service_name == "motis":
        if isinstance(response_data, dict):
            # MOTIS has a nested structure: response_data.result.connections
            result = response_data.get("result", {})
            message = response_data.get("message", "")

            # Check for successful message and presence of result
            has_success_message = "successfully" in message.lower()
            has_result = isinstance(result, dict)

            # MOTIS might return empty connections but still be valid
            return has_success_message and has_result

    return True


# Quick test function for debugging
def test_service_directly(service_name: str):
    """Test a service directly for debugging."""
    from tests.utils.commons import SERVICES

    service = next((s for s in SERVICES if s["name"] == service_name), None)
    if not service:
        print(f"❌ Service '{service_name}' not found")
        return

    # Test coordinates (Karlsruhe area)
    origin = "49.4875,8.4660"
    destination = "49.4817,8.4454"

    try:
        payload = service["payload_builder"](origin, destination)
        print(f"🧪 Testing {service_name} with payload: {str(payload)[:100]}...")

        metrics = service["query_func"](
            service["client"], service["endpoint"], payload, service["method"]
        )

        print("📊 Results:")
        print(f"   Status: {metrics.status_code}")
        print(f"   Time: {metrics.time_ms:.2f}ms")
        print(f"   CPU: {metrics.cpu_s:.4f}s")
        print(f"   Memory: {metrics.mem_mb_delta:.2f}MB")
        print(f"   Size: {metrics.response_size_bytes} bytes")
        print(f"   Valid: {validate_service_response(metrics, service_name)}")

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    # Example usage for direct testing
    for service_name in ["google", "otp", "motis"]:
        test_service_directly(service_name)
        print("-" * 40)
