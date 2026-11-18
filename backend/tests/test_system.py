def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "service": "nexora-api",
        "environment": "test",
        "prediction_artifacts_available": True,
        "cross_sectional_model_available": False,
        "model_lab_available": False,
    }


def test_unknown_route_uses_json_error(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"
