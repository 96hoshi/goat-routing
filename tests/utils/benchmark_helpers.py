import time

import httpx
import psutil

from tests.utils.models import ServiceMetrics  # Import our new dataclass


# 2. GENERIC WRAPPER: For services with standard success criteria (HTTP 2xx).
def generic_query_service(client, endpoint, payload, method) -> ServiceMetrics:
    """A standard query that just relies on the core measurement function."""
    return _measure_request(client, endpoint, payload, method)


# 3. SPECIALIZED WRAPPER: For Google, which has unique success criteria.
def google_query_service(client, endpoint, payload, method) -> ServiceMetrics:
    """Wrapper for Google that checks the inner JSON status field."""
    metrics = _measure_request(client, endpoint, payload, method)
    # Add the special Google-specific logic here if needed, for example:
    if metrics.status_code == 200 and isinstance(metrics.response_data, dict):
        if metrics.response_data.get("status") not in ["OK", "ZERO_RESULTS"]:
            print(
                f"Warning: Google API returned outer 200 OK but inner status of '{metrics.response_data.get('status')}'"
            )
    return metrics


# 4. SPECIALIZED WRAPPER: For OTP GraphQL, which has unique GraphQL error handling.
def otp_query_service(client, endpoint, payload, method) -> ServiceMetrics:
    """Wrapper for OpenTripPlanner that checks GraphQL errors in addition to HTTP status."""
    metrics = _measure_request(client, endpoint, payload, method)

    # Add OTP-specific GraphQL error checking
    if metrics.status_code == 200 and isinstance(metrics.response_data, dict):
        if "errors" in metrics.response_data:
            print(
                f"Warning: OTP returned HTTP 200 but GraphQL errors: {metrics.response_data['errors']}"
            )
            # Log the error details but don't fail the benchmark
        elif "data" in metrics.response_data:
            plan = metrics.response_data.get("data", {}).get("plan", {})
            itineraries = plan.get("itineraries", [])
            if not itineraries:
                print("Info: OTP returned successful response but found no routes")
            else:
                print(f"Success: OTP found {len(itineraries)} route(s)")
        else:
            print("Warning: OTP returned unexpected GraphQL response structure")

    return metrics


def _measure_request(
    client: httpx.Client, endpoint: str, payload: dict, method: str = "POST"
) -> ServiceMetrics:
    """
    Performs a single request and measures associated performance metrics.
    This is the core, low-level measurement function. It does not make
    any assumptions about what a "successful" request is beyond the
    HTTP level; its job is simply to measure and report.
    """
    process = psutil.Process()
    response_size = 0
    status_code = -1
    response_data = {}

    # --- Measurement starts here ---
    mem_before_mb = process.memory_info().rss / (1024 * 1024)
    cpu_times_before = process.cpu_times()
    start_time = time.perf_counter()

    try:
        # Determine the HTTP method and make the request
        if method.upper() == "POST":
            response = client.post(endpoint, json=payload, timeout=30.0)
        else:  # Assumes GET for everything else
            response = client.get(endpoint, params=payload, timeout=30.0)

        # Record basic response info
        status_code = response.status_code

        # This will raise an httpx.HTTPStatusError for 4xx or 5xx responses,
        # which is caught by the except block below.
        response.raise_for_status()

        # If we get here, the request was successful (2xx)
        response_size = len(response.content)
        response_data = response.json()

    except httpx.RequestError as e:
        # Covers connection errors, timeouts, etc.
        print(f"An HTTP request error occurred: {e.__class__.__name__} - {e}")
        response_data = {"error": str(e)}
        # status_code will remain -1 or whatever the client might have set

    except httpx.HTTPStatusError as e:
        # This specifically catches 4xx and 5xx responses from raise_for_status()
        print(f"An HTTP status error occurred: {e.response.status_code} - {e}")
        status_code = e.response.status_code
        try:
            # Try to get error details from the response body if possible
            response_data = e.response.json()
        except Exception:
            response_data = {"error": e.response.text or "No response body."}

    except Exception as e:
        # Catch-all for other errors, like JSON decoding failures
        print(f"An unexpected error occurred: {e.__class__.__name__} - {e}")
        response_data = {"error": str(e)}

    finally:
        # This block ALWAYS runs, ensuring we get our "after" measurements
        end_time = time.perf_counter()
        cpu_times_after = process.cpu_times()
        mem_after_mb = process.memory_info().rss / (1024 * 1024)
    # --- Measurement ends here ---

    # Calculate the deltas (changes)
    duration_ms = (end_time - start_time) * 1000
    cpu_delta_s = (cpu_times_after.user + cpu_times_after.system) - (
        cpu_times_before.user + cpu_times_before.system
    )
    mem_delta_mb = mem_after_mb - mem_before_mb

    # Return the structured data, no matter what happened
    return ServiceMetrics(
        time_ms=duration_ms,
        cpu_s=cpu_delta_s,
        mem_mb_delta=mem_delta_mb,
        response_size_bytes=response_size,
        status_code=status_code,
        response_data=response_data,
    )
