def test_contact_resolves_call_name(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    assert "call_id" in contact
    assert "call_name" in contact

def test_contact_can_be_linked_to_call(auth_client):
    contact = auth_client.post("/api/contacts", json={"name": "Link Test", "email": "link@test.com", "phone": "555-0001"}).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={"name": "Test Call", "lead_id": call_lead["id"], "type": "Outbound", "duration_seconds": 120, "outcome": "Qualified"}).json()
    assert contact.get("call_id") is None
    response = auth_client.put(f"/api/contacts/{contact['id']}/call", json={"call_id": call["id"]})
    updated = response.json()
    assert updated["call_id"] == call["id"]
    assert updated["call_name"] == call["name"]

def test_contact_can_be_unlinked_from_call(auth_client):
    contact = auth_client.post("/api/contacts", json={"name": "Unlink Test", "email": "unlink@test.com", "phone": "555-0002"}).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={"name": "Unlink Call", "lead_id": call_lead["id"], "type": "Outbound", "duration_seconds": 60, "outcome": "Interested"}).json()
    auth_client.put(f"/api/contacts/{contact['id']}/call", json={"call_id": call["id"]})
    response = auth_client.put(f"/api/contacts/{contact['id']}/call", json={"call_id": None})
    updated = response.json()
    assert updated["call_id"] is None
    assert updated["call_name"] is None

def test_call_contacts_endpoint_exists(auth_client):
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={"name": "Endpoint Call", "lead_id": call_lead["id"], "type": "Outbound", "duration_seconds": 120, "outcome": "Qualified"}).json()
    resp = auth_client.get(f"/api/calls/{call['id']}/contacts")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_call_shows_contacts_when_linked(auth_client):
    contact = auth_client.post("/api/contacts", json={"name": "Show Test", "email": "show@test.com", "phone": "555-0003"}).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={"name": "Show Call", "lead_id": call_lead["id"], "type": "Inbound", "duration_seconds": 180, "outcome": "Not Interested"}).json()
    auth_client.put(f"/api/contacts/{contact['id']}/call", json={"call_id": call["id"]})
    call_contacts = auth_client.get(f"/api/calls/{call['id']}/contacts").json()
    assert any(c["id"] == contact["id"] for c in call_contacts)

def test_contact_unknown_404s(auth_client):
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={"name": "404 Call", "lead_id": call_lead["id"], "type": "Outbound", "duration_seconds": 60, "outcome": "Interested"}).json()
    resp = auth_client.put(f"/api/contacts/9999/call", json={"call_id": call["id"]})
    assert resp.status_code == 404

def test_call_unknown_404s(auth_client):
    resp = auth_client.get("/api/calls/9999/contacts")
    assert resp.status_code == 404
