def test_contact_resolves_quotation_title(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    assert "quotation_id" in contact
    assert "quotation_title" in contact


def test_contact_can_be_linked_to_quotation(auth_client):
    contact = auth_client.post("/api/contacts", json={
        "name": "Link Test Contact", "email": "link@test.com", "phone": "555-0001"
    }).json()
    quotation_contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": quotation_contact["id"], "title": "Test Quotation", "amount": 50000, "status": "Draft"
    }).json()
    assert contact.get("quotation_id") is None

    response = auth_client.put(f"/api/contacts/{contact['id']}/quotation", json={"quotation_id": quotation["id"]})
    updated = response.json()
    assert updated["quotation_id"] == quotation["id"]
    assert updated["quotation_title"] == quotation["title"]


def test_contact_can_be_unlinked_from_quotation(auth_client):
    contact = auth_client.post("/api/contacts", json={
        "name": "Unlink Test Contact", "email": "unlink@test.com", "phone": "555-0002"
    }).json()
    quotation_contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": quotation_contact["id"], "title": "Unlink Test Quotation", "amount": 50000, "status": "Draft"
    }).json()

    auth_client.put(f"/api/contacts/{contact['id']}/quotation", json={"quotation_id": quotation["id"]})
    response = auth_client.put(f"/api/contacts/{contact['id']}/quotation", json={"quotation_id": None})
    updated = response.json()
    assert updated["quotation_id"] is None
    assert updated["quotation_title"] is None


def test_quotation_contacts_endpoint_exists(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "Endpoint Test Quotation", "amount": 50000, "status": "Draft"
    }).json()
    resp = auth_client.get(f"/api/quotations/{quotation['id']}/contacts")
    assert resp.status_code == 200
    contacts = resp.json()
    assert isinstance(contacts, list)


def test_quotation_shows_contacts_when_linked(auth_client):
    contact = auth_client.post("/api/contacts", json={
        "name": "Show Test Contact", "email": "show@test.com", "phone": "555-0003"
    }).json()
    quotation_contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": quotation_contact["id"], "title": "Show Test Quotation", "amount": 50000, "status": "Draft"
    }).json()

    auth_client.put(f"/api/contacts/{contact['id']}/quotation", json={"quotation_id": quotation["id"]})

    quotation_contacts = auth_client.get(f"/api/quotations/{quotation['id']}/contacts").json()
    assert any(c["id"] == contact["id"] for c in quotation_contacts)


def test_contact_unknown_404s(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "404 Test Quotation", "amount": 50000, "status": "Draft"
    }).json()
    resp = auth_client.put(f"/api/contacts/9999/quotation", json={"quotation_id": quotation["id"]})
    assert resp.status_code == 404


def test_quotation_unknown_404s(auth_client):
    resp = auth_client.get("/api/quotations/9999/contacts")
    assert resp.status_code == 404
