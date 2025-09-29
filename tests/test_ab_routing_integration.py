from tests.utils.commons import MOTIS_PAYLOAD_BENCH, client


def test_compute_ab_routing_real_motis():
    """
    Integration test: actually calls the Motis service.
    """
    response = client.post("/ab-routing", json=MOTIS_PAYLOAD_BENCH)

    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "result" in data
    assert "message" in data
    assert data["message"] == "Plan computed successfully."

    direct_routes = data["result"].get("direct")
    assert isinstance(direct_routes, list)
    assert len(direct_routes) > 0
