def test_call_resolves_contact_name(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Test Call", "lead_id": lead["id"], "type": "Outbound",
        "duration_seconds": 120, "outcome": "Qualified"
    }).json()
    assert "contact_id" in call
    assert "contact_name" in call


def test_call_can_be_linked_to_contact(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Test Call", "lead_id": lead["id"], "type": "Outbound",
        "duration_seconds": 120, "outcome": "Qualified"
    }).json()
    contact = auth_client.post("/api/contacts", json={
        "name": "Link Test Contact", "email": "link@test.com", "phone": "9999999999"
    }).json()
    assert call.get("contact_id") is None

    auth_client.put(f"/api/calls/{call['id']}/contact", json={"contact_id": contact["id"]})

    updated = auth_client.get(f"/api/calls").json()[0]
    if updated["id"] == call["id"]:
        assert updated["contact_id"] == contact["id"]
        assert updated["contact_name"] == contact["name"]


def test_call_can_be_unlinked_from_contact(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Unlink Test", "lead_id": lead["id"], "type": "Outbound",
        "duration_seconds": 60, "outcome": "Interested"
    }).json()
    contact = auth_client.post("/api/contacts", json={
        "name": "Unlink Contact", "email": "unlink@test.com", "phone": "8888888888"
    }).json()

    auth_client.put(f"/api/calls/{call['id']}/contact", json={"contact_id": contact["id"]})
    auth_client.put(f"/api/calls/{call['id']}/contact", json={"contact_id": None})

    updated = auth_client.get(f"/api/calls").json()
    call_record = [c for c in updated if c["id"] == call["id"]][0]
    assert call_record["contact_id"] is None
    assert call_record["contact_name"] is None


def test_contact_calls_endpoint_exists(auth_client):
    contact = auth_client.post("/api/contacts", json={
        "name": "Endpoint Contact", "email": "endpoint@test.com", "phone": "7777777777"
    }).json()
    resp = auth_client.get(f"/api/contacts/{contact['id']}/calls")
    assert resp.status_code == 200
    calls = resp.json()
    assert isinstance(calls, list)


def test_contact_shows_calls_when_linked(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Show Test Call", "lead_id": lead["id"], "type": "Inbound",
        "duration_seconds": 180, "outcome": "Not Interested"
    }).json()
    contact = auth_client.post("/api/contacts", json={
        "name": "Show Contact", "email": "show@test.com", "phone": "6666666666"
    }).json()

    auth_client.put(f"/api/calls/{call['id']}/contact", json={"contact_id": contact["id"]})

    contact_calls = auth_client.get(f"/api/contacts/{contact['id']}/calls").json()
    assert any(c["id"] == call["id"] for c in contact_calls)


def test_call_unknown_404s(auth_client):
    resp = auth_client.put("/api/calls/9999/contact", json={"contact_id": 1})
    assert resp.status_code == 404


def test_contact_unknown_404s(auth_client):
    resp = auth_client.get("/api/contacts/9999/calls")
    assert resp.status_code == 404
