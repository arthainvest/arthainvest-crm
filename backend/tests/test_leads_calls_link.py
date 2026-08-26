def test_lead_resolves_call_name(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Test Lead", "company": "Test Co", "email": "lead@test.com"
    }).json()
    assert "call_id" in lead
    assert "call_name" in lead


def test_lead_can_be_linked_to_call(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Link Test Lead", "company": "Test Co"
    }).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Link Test Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 120, "outcome": "Qualified"
    }).json()
    assert lead.get("call_id") is None

    response = auth_client.put(f"/api/leads/{lead['id']}/call", json={"call_id": call["id"]})
    updated = response.json()
    assert updated["call_id"] == call["id"]
    assert updated["call_name"] == call["name"]


def test_lead_can_be_unlinked_from_call(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Unlink Test Lead", "company": "Test Co"
    }).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Unlink Test Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 60, "outcome": "Interested"
    }).json()

    auth_client.put(f"/api/leads/{lead['id']}/call", json={"call_id": call["id"]})
    response = auth_client.put(f"/api/leads/{lead['id']}/call", json={"call_id": None})
    updated = response.json()
    assert updated["call_id"] is None
    assert updated["call_name"] is None


def test_call_leads_endpoint_exists(auth_client):
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Endpoint Test Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 120, "outcome": "Qualified"
    }).json()
    resp = auth_client.get(f"/api/calls/{call['id']}/leads")
    assert resp.status_code == 200
    leads = resp.json()
    assert isinstance(leads, list)


def test_call_shows_leads_when_linked(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Show Test Lead", "company": "Test Co"
    }).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Show Test Call", "lead_id": call_lead["id"], "type": "Inbound",
        "duration_seconds": 180, "outcome": "Not Interested"
    }).json()

    auth_client.put(f"/api/leads/{lead['id']}/call", json={"call_id": call["id"]})

    call_leads = auth_client.get(f"/api/calls/{call['id']}/leads").json()
    assert any(l["id"] == lead["id"] for l in call_leads)


def test_lead_unknown_404s(auth_client):
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "404 Test Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 60, "outcome": "Interested"
    }).json()
    resp = auth_client.put(f"/api/leads/9999/call", json={"call_id": call["id"]})
    assert resp.status_code == 404


def test_call_unknown_404s(auth_client):
    resp = auth_client.get("/api/calls/9999/leads")
    assert resp.status_code == 404
