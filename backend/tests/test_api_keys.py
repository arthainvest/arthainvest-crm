def test_create_api_key_returns_raw_value_once(auth_client):
    resp = auth_client.post("/api/api-keys", json={"name": "Website Contact Form"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Website Contact Form"
    assert body["api_key"].startswith("ai_")
    assert len(body["api_key"]) > 20

    # The list endpoint must never return the raw key again - only a short, non-secret prefix.
    resp = auth_client.get("/api/api-keys")
    assert resp.status_code == 200
    keys = resp.json()
    created = next(k for k in keys if k["id"] == body["id"])
    assert "api_key" not in created
    assert created["key_prefix"] == body["api_key"][:10]
    assert created["revoked_at"] is None


def test_create_api_key_requires_name(auth_client):
    resp = auth_client.post("/api/api-keys", json={"name": ""})
    assert resp.status_code == 422


def test_revoke_api_key(auth_client):
    created = auth_client.post("/api/api-keys", json={"name": "To Be Revoked"}).json()

    resp = auth_client.delete(f"/api/api-keys/{created['id']}")
    assert resp.status_code == 200

    keys = auth_client.get("/api/api-keys").json()
    revoked = next(k for k in keys if k["id"] == created["id"])
    assert revoked["revoked_at"] is not None


def test_revoke_nonexistent_key_404s(auth_client):
    resp = auth_client.delete("/api/api-keys/9999")
    assert resp.status_code == 404


def test_public_leads_with_valid_key_creates_lead(client, auth_client):
    created = auth_client.post("/api/api-keys", json={"name": "Zapier"}).json()
    raw_key = created["api_key"]

    before = len(auth_client.get("/api/leads").json())

    resp = client.post(
        "/api/public/leads",
        json={"name": "Public Website Lead", "phone": "9876500000", "source": "Website Form"},
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 200
    lead = resp.json()
    assert lead["name"] == "Public Website Lead"
    assert lead["source"] == "Website Form"
    assert lead["status"] == "New"

    # It's a real row - shows up through the normal, authenticated leads list too.
    after = auth_client.get("/api/leads").json()
    assert len(after) == before + 1
    assert any(l["name"] == "Public Website Lead" for l in after)


def test_public_leads_defaults_source_to_api_when_omitted(client, auth_client):
    created = auth_client.post("/api/api-keys", json={"name": "No Source Hook"}).json()

    resp = client.post(
        "/api/public/leads",
        json={"name": "No Source Lead"},
        headers={"X-API-Key": created["api_key"]},
    )
    assert resp.status_code == 200
    assert resp.json()["source"] == "API"


def test_public_leads_missing_key_401s(client):
    resp = client.post("/api/public/leads", json={"name": "No Key Lead"})
    assert resp.status_code == 401


def test_public_leads_invalid_key_401s(client):
    resp = client.post(
        "/api/public/leads",
        json={"name": "Bad Key Lead"},
        headers={"X-API-Key": "not_a_real_key"},
    )
    assert resp.status_code == 401


def test_public_leads_revoked_key_401s(client, auth_client):
    created = auth_client.post("/api/api-keys", json={"name": "Soon Revoked"}).json()
    auth_client.delete(f"/api/api-keys/{created['id']}")

    resp = client.post(
        "/api/public/leads",
        json={"name": "Revoked Key Lead"},
        headers={"X-API-Key": created["api_key"]},
    )
    assert resp.status_code == 401


def test_public_leads_rejects_missing_required_name(client, auth_client):
    created = auth_client.post("/api/api-keys", json={"name": "Validation Hook"}).json()

    resp = client.post(
        "/api/public/leads",
        json={"phone": "9876500000"},
        headers={"X-API-Key": created["api_key"]},
    )
    assert resp.status_code == 422


def test_public_leads_rejects_oversized_fields(client, auth_client):
    created = auth_client.post("/api/api-keys", json={"name": "Oversized Hook"}).json()

    resp = client.post(
        "/api/public/leads",
        json={"name": "A" * 1000},
        headers={"X-API-Key": created["api_key"]},
    )
    assert resp.status_code == 422
