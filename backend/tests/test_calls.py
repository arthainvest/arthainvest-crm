def test_list_calls_returns_seeded_data(auth_client):
    resp = auth_client.get("/api/calls")
    assert resp.status_code == 200
    assert len(resp.json()) == 4


def test_create_call_formats_duration(auth_client):
    resp = auth_client.post("/api/calls", json={
        "name": "New Prospect", "phone": "7777777777", "duration_seconds": 125, "type": "Outbound"
    })
    assert resp.status_code == 200
    call = resp.json()
    assert call["duration"] == "2m 5s"


def test_delete_call(auth_client):
    resp = auth_client.delete("/api/calls/1")
    assert resp.status_code == 200

    resp = auth_client.get("/api/calls")
    assert len(resp.json()) == 3


def test_calls_analytics(auth_client):
    resp = auth_client.get("/api/analytics/calls")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_calls"] == 4
