from tests.utils.commons import client, coordinates_list, motis_payload


def test_compute_ab_routing_real_motis():
    """
    Integration test: actually calls the Motis service.
    """
    response = client.post(
        "/ab-routing",
        json=motis_payload(coordinates_list[5][0], coordinates_list[5][1]),
    )
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
