import pytest
import respx
from freezegun import freeze_time
from httpx import ConnectError, Response

from src.core.config import settings
from tests.conftest import TIME_BENCH, write_response
from tests.utils.commons import client, coordinates_list
from tests.utils.payload_builders import one_to_all_payload


@freeze_time(
    TIME_BENCH
)  # This ensures the app's default time matches our builder's default
@respx.mock
def test_one_to_all_success_with_builder():
    """
    Test the "happy path" using the new payload builder for clean, robust mocking.
    """
    # 1. Define the input data for this specific test case.
    start_loc = "50.7754385,6.0815102"
    max_time = 45

    # 2. Use the builder to generate the complete payload that your app will
    expected_motis_payload = one_to_all_payload(
        start_location=start_loc,
        max_travel_time=max_time,
    )

    # 3. Use this generated dictionary to mock the `respx` request.
    mock_motis_response = {"results": [{"target": "station_A", "time": 600}]}
    respx.get(settings.MOTIS_ONETOALL_ENDPOINT, params=expected_motis_payload).mock(
        return_value=Response(200, json=mock_motis_response)
    )

    # 4. Define the minimal payload to send TO YOUR API.
    request_to_your_api = {"one": start_loc, "maxTravelTime": max_time}

    # 5. Make the request to your API.
    response = client.post(settings.ONETOALL_ROUTE, json=request_to_your_api)

    # 6. Assert the final response envelope.
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "status_code" in data
    assert data["result"] == mock_motis_response


@freeze_time(TIME_BENCH)
@respx.mock
def test_motis_service_connection_error_with_builder():
    """Test connection error handling using the builder."""
    # 1. Use the builder to generate the payload for the mock.
    expected_motis_payload = one_to_all_payload(
        start_location="any_location", max_travel_time=60
    )

    # 2. Mock the request to raise an error.
    respx.get(settings.MOTIS_ONETOALL_ENDPOINT, params=expected_motis_payload).mock(
        side_effect=ConnectError("Connection failed")
    )

    # 3. Send a corresponding request to your API.
    response = client.post(
        settings.ONETOALL_ROUTE, json={"one": "any_location", "maxTravelTime": 60}
    )

    # 4. Assert the correct error response.
    assert response.status_code == 503
    assert "Cannot connect to motis service" in response.json()["detail"]


@respx.mock
def test_motis_service_returns_400_error():
    """
    Test the error handling when the downstream MOTIS service returns a 400 Bad Request.
    """
    motis_error_text = "Invalid station ID provided"
    respx.get(settings.MOTIS_ONETOALL_ENDPOINT).mock(
        return_value=Response(400, text=motis_error_text)
    )

    # This payload now needs to be valid according to your Pydantic model
    request_payload = {"one": "invalid_id", "maxTravelTime": 60}
    response = client.post(settings.ONETOALL_ROUTE, json=request_payload)

    # Now the status code should correctly be 400
    assert response.status_code == 400
    assert response.json()["detail"] == f"Error from motis service: {motis_error_text}"


@pytest.mark.integration
@pytest.mark.parametrize("origin_coord", coordinates_list[:2])  # Limit for speed
def test_one_to_all_integration(origin_coord):
    """
    Performs a real end-to-end test against the live MOTIS service for /one-to-all.
    The assertions have been updated to match the real MOTIS response structure.
    """

    origin, _ = origin_coord
    request_payload = one_to_all_payload(
        start_location=origin,
        max_travel_time=60,
    )

    response = client.post(settings.ONETOALL_ROUTE, json=request_payload)
    assert response.status_code == 200

    data = response.json()

    # Assert the envelope structure from your API is correct
    assert "result" in data
    assert "status_code" in data
    assert data["status_code"] == 200

    motis_result = data["result"]

    assert isinstance(motis_result, dict)

    # Assert that this dictionary contains the expected keys from the real API
    assert "all" in motis_result
    assert "one" in motis_result

    # Get the list of reachable stations from the "all" key
    reachable_stations = motis_result["all"]

    assert isinstance(reachable_stations, list)

    # This is a great "smoke test" assertion: ensure the service actually found something.
    # It proves the API call was functionally successful.
    assert (
        len(reachable_stations) > 0
    ), "Expected MOTIS to find at least one reachable station."

    first_station = reachable_stations[0]
    assert "duration" in first_station
    assert "place" in first_station
    assert "lat" in first_station["place"]
    assert "lon" in first_station["place"]


# try to reach any possible error codes from real service
@pytest.mark.integration
@pytest.mark.parametrize("coord", coordinates_list[:3])  # Limit for speed
def test_one_to_all_integration_errors(coord):
    """
    Test various error scenarios against the live MOTIS service for /one-to-all.
    """
    start_coord = coord[0]

    # Test with an invalid station ID
    invalid_payload = one_to_all_payload(
        start_location="invalid_station_id",
        max_travel_time=60,
    )

    # this should be 400 but MOTIS returns 500 for invalid IDs
    response = client.post(settings.ONETOALL_ROUTE, json=invalid_payload)
    assert response.status_code == 500
    assert "Error from motis service" in response.json()["detail"]

    # Test with a negative max travel time
    negative_time_payload = one_to_all_payload(
        start_location=start_coord,
        max_travel_time=-10,
    )
    response = client.post(settings.ONETOALL_ROUTE, json=negative_time_payload)
    assert response.status_code == 422  # Unprocessable Entity for validation errors

    wrong_type_payload = {
        "start": start_coord,  # wrong key
        "maxTravelTime": "sixty",
    }  # wrong type
    response = client.post(settings.ONETOALL_ROUTE, json=wrong_type_payload)
    assert response.status_code == 422  # Unprocessable Entity for validation errors

    # Test with missing required fields
    wrong_key_payload = {
        "start": start_coord,  # wrong key
        "maxTravelTime": 60,
    }
    response = client.post(settings.ONETOALL_ROUTE, json=wrong_key_payload)
    assert response.status_code == 422  # Unprocessable Entity for validation errors


@pytest.mark.integration
@pytest.mark.parametrize("origin_coord", coordinates_list[:2])  # Limit for speed
def test_one_to_all_plausibility(origin_coord):
    """
    Performs a real end-to-end test against the live MOTIS service for /one-to-all.
    The assertions have been updated to match the real MOTIS response structure.
    """

    origin, _ = origin_coord
    request_payload = one_to_all_payload(
        start_location=origin,
        max_travel_time=60,
    )

    response = client.post(settings.ONETOALL_ROUTE, json=request_payload)
    assert response.status_code == 200

    data = response.json()

    # Assert the envelope structure from your API is correct
    assert "result" in data
    assert "status_code" in data
    assert data["status_code"] == 200

    motis_result = data["result"]

    assert isinstance(motis_result, dict)

    # Assert that this dictionary contains the expected keys from the real API
    assert "all" in motis_result
    assert "one" in motis_result

    # Get the list of reachable stations from the "all" key
    reachable_stations = motis_result["all"]
    assert isinstance(reachable_stations, list)
    assert len(reachable_stations) > 0
    for station in reachable_stations:
        duration = station.get("duration")
        assert duration is not None, "Each station should have a duration."
        assert 0 <= duration <= 3600, f"Duration {duration} is out of expected range."

    # save the response for manual inspection
    write_response(data, f"one_to_all_plausibility_{origin.replace(',', '_')}.json")
