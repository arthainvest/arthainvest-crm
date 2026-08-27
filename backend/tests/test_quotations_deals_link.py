def test_quotation_resolves_deal_label(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "Test Quotation", "amount": 50000, "status": "Draft"
    }).json()
    assert "deal_id" in quotation
    assert "deal_label" in quotation


def test_quotation_can_be_linked_to_deal(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "Link Test Quotation", "amount": 50000, "status": "Draft"
    }).json()
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    assert quotation.get("deal_id") is None

    response = auth_client.put(f"/api/quotations/{quotation['id']}/deal", json={"deal_id": deal["id"]})
    updated = response.json()
    assert updated["deal_id"] == deal["id"]
    assert updated["deal_label"] is not None


def test_quotation_can_be_unlinked_from_deal(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "Unlink Test Quotation", "amount": 50000, "status": "Draft"
    }).json()
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()

    auth_client.put(f"/api/quotations/{quotation['id']}/deal", json={"deal_id": deal["id"]})
    response = auth_client.put(f"/api/quotations/{quotation['id']}/deal", json={"deal_id": None})
    updated = response.json()
    assert updated["deal_id"] is None
    assert updated["deal_label"] is None


def test_deal_quotations_endpoint_exists(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    resp = auth_client.get(f"/api/deals/{deal['id']}/quotations")
    assert resp.status_code == 200
    quotations = resp.json()
    assert isinstance(quotations, list)


def test_deal_shows_quotations_when_linked(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "Show Test Quotation", "amount": 50000, "status": "Draft"
    }).json()
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()

    auth_client.put(f"/api/quotations/{quotation['id']}/deal", json={"deal_id": deal["id"]})

    deal_quotations = auth_client.get(f"/api/deals/{deal['id']}/quotations").json()
    assert any(q["id"] == quotation["id"] for q in deal_quotations)


def test_quotation_unknown_404s(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    resp = auth_client.put(f"/api/quotations/9999/deal", json={"deal_id": deal["id"]})
    assert resp.status_code == 404


def test_deal_unknown_404s(auth_client):
    resp = auth_client.get("/api/deals/9999/quotations")
    assert resp.status_code == 404
