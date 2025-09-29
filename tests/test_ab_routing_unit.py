import respx
from httpx import Response

from src.core.config import settings
from src.schemas.ab_routing import motis_request_examples
from tests.utils.commons import client


@respx.mock
def test_compute_ab_routing_success():
    """
    Test the /ab-routing endpoint with a mocked successful response from Motis.
    """

    respx.get(settings.MOTIS_PLAN_ENDPOINT).mock(
        return_value=Response(200, json={"routes": [{"id": 1}]})
    )

    response = client.post("/ab-routing", json=motis_request_examples["benchmark"])
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Plan computed successfully."
    assert "result" in data


@respx.mock
def test_compute_ab_routing_motis_error():
    """
    Test the /ab-routing endpoint handling an error response from Motis.
    """
    respx.get(settings.MOTIS_PLAN_ENDPOINT).mock(
        return_value=Response(500, text="Internal Server Error")
    )

    response = client.post("/ab-routing", json=motis_request_examples["benchmark"])
    assert response.status_code == 500
    assert "Error from motis service" in response.json()["detail"]


@respx.mock
def test_compute_ab_routing_connection_error():
    """
    Test the /ab-routing endpoint handling a connection error to Motis.
    """
    import httpx

    respx.get(settings.MOTIS_PLAN_ENDPOINT).mock(
        side_effect=httpx.ConnectError("Cannot connect")
    )

    response = client.post("/ab-routing", json=motis_request_examples["benchmark"])
    assert response.status_code == 503
    assert "Cannot connect to motis service" in response.json()["detail"]
