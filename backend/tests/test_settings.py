def test_get_settings_creates_default_row(auth_client):
    resp = auth_client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["theme"] == "light"
    assert data["timezone"] == "IST"


def test_update_settings_persists(auth_client):
    resp = auth_client.put("/api/settings", json={
        "phone": "+919769432143", "theme": "dark", "ga_tracking_id": "G-TEST123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["phone"] == "+919769432143"
    assert data["theme"] == "dark"
    assert data["ga_tracking_id"] == "G-TEST123"

    resp = auth_client.get("/api/settings")
    assert resp.json()["phone"] == "+919769432143"


def test_update_settings_partial_update_preserves_other_fields(auth_client):
    auth_client.put("/api/settings", json={"company": "ArthaInvest"})
    resp = auth_client.put("/api/settings", json={"theme": "dark"})
    assert resp.json()["company"] == "ArthaInvest"
    assert resp.json()["theme"] == "dark"
