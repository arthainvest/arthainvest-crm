def test_lead_resolves_quotation_title(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    assert "quotation_id" in lead
    assert "quotation_title" in lead


def test_lead_can_be_linked_to_quotation(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Link Test Lead", "email": "link@test.com", "phone": "555-0001", "source": "Direct"
    }).json()
    quote_lead = auth_client.get("/api/leads").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": quote_lead["id"], "title": "Test Quote",
        "items": [{"description": "Processing Fee", "amount": 1000}],
    }).json()
    assert lead.get("quotation_id") is None

    response = auth_client.put(f"/api/leads/{lead['id']}/quotation", json={"quotation_id": quotation["id"]})
    updated = response.json()
    assert updated["quotation_id"] == quotation["id"]
    assert updated["quotation_title"] == "Test Quote"


def test_lead_can_be_unlinked_from_quotation(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Unlink Test Lead", "email": "unlink@test.com", "phone": "555-0002", "source": "Direct"
    }).json()
    quote_lead = auth_client.get("/api/leads").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": quote_lead["id"], "title": "Unlink Quote",
        "items": [{"description": "Fee", "amount": 500}],
    }).json()

    auth_client.put(f"/api/leads/{lead['id']}/quotation", json={"quotation_id": quotation["id"]})
    response = auth_client.put(f"/api/leads/{lead['id']}/quotation", json={"quotation_id": None})
    updated = response.json()
    assert updated["quotation_id"] is None
    assert updated["quotation_title"] is None


def test_quotation_leads_endpoint_exists(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "Endpoint Quote",
        "items": [{"description": "Fee", "amount": 750}],
    }).json()
    resp = auth_client.get(f"/api/quotations/{quotation['id']}/leads")
    assert resp.status_code == 200
    leads = resp.json()
    assert isinstance(leads, list)


def test_quotation_shows_leads_when_linked(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Show Test Lead", "email": "show@test.com", "phone": "555-0003", "source": "Direct"
    }).json()
    quote_lead = auth_client.get("/api/leads").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": quote_lead["id"], "title": "Show Quote",
        "items": [{"description": "Fee", "amount": 900}],
    }).json()

    auth_client.put(f"/api/leads/{lead['id']}/quotation", json={"quotation_id": quotation["id"]})

    quotation_leads = auth_client.get(f"/api/quotations/{quotation['id']}/leads").json()
    assert any(l["id"] == lead["id"] for l in quotation_leads)


def test_lead_unknown_404s(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "404 Quote",
        "items": [{"description": "Fee", "amount": 400}],
    }).json()
    resp = auth_client.put(f"/api/leads/9999/quotation", json={"quotation_id": quotation["id"]})
    assert resp.status_code == 404


def test_quotation_unknown_404s(auth_client):
    resp = auth_client.get("/api/quotations/9999/leads")
    assert resp.status_code == 404
