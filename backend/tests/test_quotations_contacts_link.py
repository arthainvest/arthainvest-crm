def test_quotation_resolves_contact_name(auth_client):
    deal = auth_client.get("/api/deals").json()[0]
    lead = auth_client.get(f"/api/leads/{deal['lead_id']}").json()
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deal["id"], "title": "Test Quotation",
        "items": [{"description": "Fee", "amount": 1000}]
    }).json()
    assert "contact_id" in quotation
    assert "contact_name" in quotation


def test_quotation_can_be_linked_to_contact(auth_client):
    deal = auth_client.get("/api/deals").json()[0]
    lead = auth_client.get(f"/api/leads/{deal['lead_id']}").json()
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deal["id"], "title": "Test Q",
        "items": [{"description": "Fee", "amount": 500}]
    }).json()
    contact = auth_client.get("/api/contacts").json()[0]
    assert quotation.get("contact_id") is None

    auth_client.put(f"/api/quotations/{quotation['id']}/contact", json={"contact_id": contact["id"]})

    updated = auth_client.get(f"/api/quotations/{quotation['id']}").json()
    assert updated["contact_id"] == contact["id"]
    assert updated["contact_name"] == contact["name"]


def test_quotation_can_be_unlinked_from_contact(auth_client):
    deal = auth_client.get("/api/deals").json()[0]
    lead = auth_client.get(f"/api/leads/{deal['lead_id']}").json()
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deal["id"], "title": "Unlink Test",
        "items": [{"description": "Fee", "amount": 500}]
    }).json()
    contact = auth_client.get("/api/contacts").json()[0]

    auth_client.put(f"/api/quotations/{quotation['id']}/contact", json={"contact_id": contact["id"]})
    auth_client.put(f"/api/quotations/{quotation['id']}/contact", json={"contact_id": None})

    updated = auth_client.get(f"/api/quotations/{quotation['id']}").json()
    assert updated["contact_id"] is None
    assert updated["contact_name"] is None


def test_contact_quotations_endpoint_exists(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    resp = auth_client.get(f"/api/contacts/{contact['id']}/quotations")
    assert resp.status_code == 200
    quotations = resp.json()
    assert isinstance(quotations, list)


def test_contact_shows_quotations_when_linked(auth_client):
    deal = auth_client.get("/api/deals").json()[0]
    lead = auth_client.get(f"/api/leads/{deal['lead_id']}").json()
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deal["id"], "title": "Contact Show",
        "items": [{"description": "Fee", "amount": 500}]
    }).json()
    contact = auth_client.get("/api/contacts").json()[0]

    auth_client.put(f"/api/quotations/{quotation['id']}/contact", json={"contact_id": contact["id"]})

    contact_quots = auth_client.get(f"/api/contacts/{contact['id']}/quotations").json()
    assert len(contact_quots) >= 1
    assert any(q["id"] == quotation["id"] for q in contact_quots)


def test_quotation_unknown_404s(auth_client):
    resp = auth_client.put("/api/quotations/9999/contact", json={"contact_id": 1})
    assert resp.status_code == 404


def test_contact_unknown_404s(auth_client):
    resp = auth_client.get("/api/contacts/9999/quotations")
    assert resp.status_code == 404
