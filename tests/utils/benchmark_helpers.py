import time

import docker
import docker.errors
import httpx
import psutil

from tests.utils.models import BenchmarkResult, ServiceMetrics


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
def validate_service_response(
    metrics: ServiceMetrics | BenchmarkResult, service_name: str
) -> bool:
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
            result = response_data.get("result", {})
            return "itineraries" in result

    return True


def measure_container_performance(
    target_container_name: str,
    client: httpx.Client,
    endpoint: str,
    payload: dict,
    method: str = "POST",
) -> BenchmarkResult | None:
    """
    Measures both request latency and target container resource usage.
    """
    try:
        # 1. Connect to the Docker daemon
        docker_client = docker.from_env()
        container = docker_client.containers.get(target_container_name)
    except docker.errors.NotFound:
        print(f"❌ Error: Container '{target_container_name}' not found.")
        return None
    except Exception as e:
        print(f"❌ Error connecting to Docker: {e}")
        return None

    # 2. Get container stats BEFORE the request
    stats_before = container.stats(stream=False)

    # 3. USE YOUR EXISTING FUNCTION to run the web request
    # This measures latency and response size
    request_metrics = _measure_request(client, endpoint, payload, method)

    # 4. Get container stats AFTER the request
    stats_after = container.stats(stream=False)

    # --- 5. Calculate Container Resource Deltas ---

    # CPU Delta Calculation (Docker reports total CPU usage in nanoseconds)
    cpu_delta_ns = (
        stats_after["cpu_stats"]["cpu_usage"]["total_usage"]
        - stats_before["cpu_stats"]["cpu_usage"]["total_usage"]
    )
    container_cpu_s = cpu_delta_ns / 1_000_000_000  # Convert nanoseconds to seconds

    # Memory Peak (Docker provides 'max_usage' during the stat collection period)
    mem_stats = stats_after.get("memory_stats", {})
    peak_usage_bytes = mem_stats.get("max_usage", mem_stats.get("usage", 0))
    container_mem_peak_mb = peak_usage_bytes / (1024 * 1024)

    # Network I/O Delta
    net_rx_delta = 0
    net_tx_delta = 0

    # Don't assume the network name. Iterate over the networks and sum their stats.
    # In most docker-compose setups, there will only be one network anyway.
    if "networks" in stats_after and "networks" in stats_before:
        for network_name in stats_after["networks"]:
            if network_name in stats_before["networks"]:
                net_rx_delta += (
                    stats_after["networks"][network_name]["rx_bytes"]
                    - stats_before["networks"][network_name]["rx_bytes"]
                )
                net_tx_delta += (
                    stats_after["networks"][network_name]["tx_bytes"]
                    - stats_before["networks"][network_name]["tx_bytes"]
                )

    return BenchmarkResult(
        latency_ms=request_metrics.time_ms,
        response_size_bytes=request_metrics.response_size_bytes,
        status_code=request_metrics.status_code,
        container_name=target_container_name,
        container_cpu_usage_total_s=container_cpu_s,
        container_mem_peak_mb=container_mem_peak_mb,
        container_net_rx_bytes=net_rx_delta,
        container_net_tx_bytes=net_tx_delta,
        response_data=request_metrics.response_data,
    )


def _build_base_result(service, origin, dest, latency_stats):
    """
    Builds the dictionary of common fields derived from pytest-benchmark stats.
    This is a private helper function.
    """
    return {
        "service": service["name"],
        "origin": origin,
        "destination": dest if dest is not None else "",
        "avg_time_ms": f"{latency_stats['mean'] * 1000:.3f}",
        "min_time_ms": f"{latency_stats['min'] * 1000:.3f}",
        "max_time_ms": f"{latency_stats['max'] * 1000:.3f}",
        "median_time_ms": f"{latency_stats['median'] * 1000:.3f}",
        "stddev_time_ms": f"{latency_stats['stddev'] * 1000:.3f}",
        "rounds": latency_stats["rounds"],
    }


def build_api_result_row(
    service, origin, dest, benchmark_stats, result: ServiceMetrics, is_valid: bool
):
    """Builds the result row for external API services with clearer naming."""
    # Start with the common timing fields
    base_row = _build_base_result(service, origin, dest, benchmark_stats)

    # Calculate average time for ratios
    avg_time_ms = benchmark_stats["mean"] * 1000
    avg_time_s = benchmark_stats["mean"]

    # Add the fields specific to the API/client-side measurement
    api_specific_fields = {
        # --- RENAMED for clarity ---
        "client_cpu_s": f"{result.cpu_s:.4f}",
        "client_mem_mb_delta": f"{result.mem_mb_delta:.4f}",
        # --- Unchanged ---
        "avg_response_size_bytes": f"{result.response_size_bytes:.0f}",
        "status_code": result.status_code,
        "valid_response": is_valid,
        # Performance ratios
        "bytes_per_ms": (
            f"{result.response_size_bytes / avg_time_ms:.2f}"
            if avg_time_ms > 0
            else "0.00"
        ),
        "cpu_efficiency_client": (
            f"{result.cpu_s / avg_time_s:.4f}" if avg_time_s > 0 else "0.0000"
        ),
        "cv_percent": (
            f"{(benchmark_stats['stddev'] / benchmark_stats['mean']) * 100:.2f}"
            if benchmark_stats["mean"] > 0
            else "0.00"
        ),
    }

    # Merge the two dictionaries and return
    return base_row | api_specific_fields


def build_container_result_row(
    service,
    origin,
    dest,
    latency_stats,
    container_result: BenchmarkResult,
    is_valid: bool | None,
):
    """Builds the result row for containerized services with all collected metrics."""
    # Start with the common timing fields
    base_row = _build_base_result(service, origin, dest, latency_stats)

    # Calculate average time in ms for ratios to avoid division by zero
    avg_time_ms = latency_stats["mean"] * 1000
    avg_time_s = latency_stats["mean"]

    # Add ALL the fields specific to the container measurement
    container_specific_fields = {
        # --- Raw Resource Metrics ---
        "container_cpu_s": f"{container_result.container_cpu_usage_total_s:.4f}",
        "container_mem_peak_mb": f"{container_result.container_mem_peak_mb:.4f}",
        # --- NEW: Raw Network Metrics ---
        "container_net_rx_kb": f"{container_result.container_net_rx_bytes / 1024:.2f}",
        "container_net_tx_kb": f"{container_result.container_net_tx_bytes / 1024:.2f}",
        # --- Other Core Metrics ---
        "avg_response_size_bytes": f"{container_result.response_size_bytes:.0f}",
        "status_code": container_result.status_code,
        "valid_response": is_valid,
        # --- Performance Ratios ---
        "bytes_per_ms": (
            f"{container_result.response_size_bytes / avg_time_ms:.2f}"
            if avg_time_ms > 0
            else "0.00"
        ),
        "cpu_efficiency_server": (
            f"{container_result.container_cpu_usage_total_s / avg_time_s:.4f}"
            if avg_time_s > 0
            else "0.0000"
        ),
        "cv_percent": (
            f"{(latency_stats['stddev'] / latency_stats['mean']) * 100:.2f}"
            if latency_stats["mean"] > 0
            else "0.00"
        ),
    }

    # Merge the two dictionaries and return
    return base_row | container_specific_fields
