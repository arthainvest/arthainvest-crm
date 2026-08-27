def test_deal_resolves_call_name(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    assert "call_id" in deal
    assert "call_name" in deal


def test_deal_can_be_linked_to_call(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Deal Link Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 120, "outcome": "Qualified"
    }).json()
    assert deal.get("call_id") is None

    response = auth_client.put(f"/api/deals/{deal['id']}/call", json={"call_id": call["id"]})
    updated = response.json()
    assert updated["call_id"] == call["id"]
    assert updated["call_name"] == call["name"]


def test_deal_can_be_unlinked_from_call(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Deal Unlink Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 60, "outcome": "Interested"
    }).json()

    auth_client.put(f"/api/deals/{deal['id']}/call", json={"call_id": call["id"]})
    response = auth_client.put(f"/api/deals/{deal['id']}/call", json={"call_id": None})
    updated = response.json()
    assert updated["call_id"] is None
    assert updated["call_name"] is None


def test_call_deals_endpoint_exists(auth_client):
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Deal Endpoint Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 120, "outcome": "Qualified"
    }).json()
    resp = auth_client.get(f"/api/calls/{call['id']}/deals")
    assert resp.status_code == 200
    deals = resp.json()
    assert isinstance(deals, list)


def test_call_shows_deals_when_linked(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Deal Show Call", "lead_id": call_lead["id"], "type": "Inbound",
        "duration_seconds": 180, "outcome": "Not Interested"
    }).json()

    auth_client.put(f"/api/deals/{deal['id']}/call", json={"call_id": call["id"]})

    call_deals = auth_client.get(f"/api/calls/{call['id']}/deals").json()
    assert any(d["id"] == deal["id"] for d in call_deals)


def test_deal_unknown_404s(auth_client):
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Deal 404 Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 60, "outcome": "Interested"
    }).json()
    resp = auth_client.put(f"/api/deals/9999/call", json={"call_id": call["id"]})
    assert resp.status_code == 404


def test_call_unknown_404s(auth_client):
    resp = auth_client.get("/api/calls/9999/deals")
    assert resp.status_code == 404
