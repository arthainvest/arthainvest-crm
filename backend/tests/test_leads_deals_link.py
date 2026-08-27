def test_lead_resolves_deal_label(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    assert "deal_id" in lead
    assert "deal_label" in lead


def test_lead_can_be_linked_to_deal(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Link Test Lead", "email": "link@test.com", "phone": "555-0001", "source": "Direct"
    }).json()
    deal_lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": deal_lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    assert lead.get("deal_id") is None

    response = auth_client.put(f"/api/leads/{lead['id']}/deal", json={"deal_id": deal["id"]})
    updated = response.json()
    assert updated["deal_id"] == deal["id"]
    assert updated["deal_label"] is not None


def test_lead_can_be_unlinked_from_deal(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Unlink Test Lead", "email": "unlink@test.com", "phone": "555-0002", "source": "Direct"
    }).json()
    deal_lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": deal_lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()

    auth_client.put(f"/api/leads/{lead['id']}/deal", json={"deal_id": deal["id"]})
    response = auth_client.put(f"/api/leads/{lead['id']}/deal", json={"deal_id": None})
    updated = response.json()
    assert updated["deal_id"] is None
    assert updated["deal_label"] is None


def test_deal_leads_endpoint_exists(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    resp = auth_client.get(f"/api/deals/{deal['id']}/leads")
    assert resp.status_code == 200
    leads = resp.json()
    assert isinstance(leads, list)


def test_deal_shows_leads_when_linked(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Show Test Lead", "email": "show@test.com", "phone": "555-0003", "source": "Direct"
    }).json()
    deal_lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": deal_lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()

    auth_client.put(f"/api/leads/{lead['id']}/deal", json={"deal_id": deal["id"]})

    deal_leads = auth_client.get(f"/api/deals/{deal['id']}/leads").json()
    assert any(l["id"] == lead["id"] for l in deal_leads)


def test_lead_unknown_404s(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    resp = auth_client.put(f"/api/leads/9999/deal", json={"deal_id": deal["id"]})
    assert resp.status_code == 404


def test_deal_unknown_404s(auth_client):
    resp = auth_client.get("/api/deals/9999/leads")
    assert resp.status_code == 404
