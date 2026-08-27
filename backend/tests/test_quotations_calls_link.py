def test_quotation_resolves_call_name(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "Test Quotation", "amount": 50000, "status": "Draft"
    }).json()
    assert "call_id" in quotation
    assert "call_name" in quotation


def test_quotation_can_be_linked_to_call(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "Link Test Quotation", "amount": 50000, "status": "Draft"
    }).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Quotation Link Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 120, "outcome": "Qualified"
    }).json()
    assert quotation.get("call_id") is None

    response = auth_client.put(f"/api/quotations/{quotation['id']}/call", json={"call_id": call["id"]})
    updated = response.json()
    assert updated["call_id"] == call["id"]
    assert updated["call_name"] == call["name"]


def test_quotation_can_be_unlinked_from_call(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "Unlink Test Quotation", "amount": 50000, "status": "Draft"
    }).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Quotation Unlink Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 60, "outcome": "Interested"
    }).json()

    auth_client.put(f"/api/quotations/{quotation['id']}/call", json={"call_id": call["id"]})
    response = auth_client.put(f"/api/quotations/{quotation['id']}/call", json={"call_id": None})
    updated = response.json()
    assert updated["call_id"] is None
    assert updated["call_name"] is None


def test_call_quotations_endpoint_exists(auth_client):
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Quotation Endpoint Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 120, "outcome": "Qualified"
    }).json()
    resp = auth_client.get(f"/api/calls/{call['id']}/quotations")
    assert resp.status_code == 200
    quotations = resp.json()
    assert isinstance(quotations, list)


def test_call_shows_quotations_when_linked(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "Show Test Quotation", "amount": 50000, "status": "Draft"
    }).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Quotation Show Call", "lead_id": call_lead["id"], "type": "Inbound",
        "duration_seconds": 180, "outcome": "Not Interested"
    }).json()

    auth_client.put(f"/api/quotations/{quotation['id']}/call", json={"call_id": call["id"]})

    call_quotations = auth_client.get(f"/api/calls/{call['id']}/quotations").json()
    assert any(q["id"] == quotation["id"] for q in call_quotations)


def test_quotation_unknown_404s(auth_client):
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Quotation 404 Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 60, "outcome": "Interested"
    }).json()
    resp = auth_client.put(f"/api/quotations/9999/call", json={"call_id": call["id"]})
    assert resp.status_code == 404


def test_call_unknown_404s(auth_client):
    resp = auth_client.get("/api/calls/9999/quotations")
    assert resp.status_code == 404
