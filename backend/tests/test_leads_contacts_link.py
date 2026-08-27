def test_lead_resolves_contact_name(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    assert "contact_id" in lead
    assert "contact_name" in lead


def test_lead_can_be_linked_to_contact(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Link Test Lead", "email": "link@test.com", "phone": "555-0001", "source": "Direct"
    }).json()
    contact = auth_client.post("/api/contacts", json={
        "name": "Link Test Contact", "email": "linkc@test.com", "phone": "555-1111"
    }).json()
    assert lead.get("contact_id") is None

    response = auth_client.put(f"/api/leads/{lead['id']}/contact", json={"contact_id": contact["id"]})
    updated = response.json()
    assert updated["contact_id"] == contact["id"]
    assert updated["contact_name"] == "Link Test Contact"


def test_lead_can_be_unlinked_from_contact(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Unlink Test Lead", "email": "unlink@test.com", "phone": "555-0002", "source": "Direct"
    }).json()
    contact = auth_client.post("/api/contacts", json={
        "name": "Unlink Test Contact", "email": "unlinkc@test.com", "phone": "555-2222"
    }).json()

    auth_client.put(f"/api/leads/{lead['id']}/contact", json={"contact_id": contact["id"]})
    response = auth_client.put(f"/api/leads/{lead['id']}/contact", json={"contact_id": None})
    updated = response.json()
    assert updated["contact_id"] is None
    assert updated["contact_name"] is None


def test_contact_leads_endpoint_exists(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    contact = auth_client.post("/api/contacts", json={
        "name": "Endpoint Test Contact", "email": "endpointc@test.com", "phone": "555-3333"
    }).json()
    resp = auth_client.get(f"/api/contacts/{contact['id']}/leads")
    assert resp.status_code == 200
    leads = resp.json()
    assert isinstance(leads, list)


def test_contact_shows_leads_when_linked(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Show Test Lead", "email": "show@test.com", "phone": "555-0003", "source": "Direct"
    }).json()
    contact = auth_client.post("/api/contacts", json={
        "name": "Show Test Contact", "email": "showc@test.com", "phone": "555-4444"
    }).json()

    auth_client.put(f"/api/leads/{lead['id']}/contact", json={"contact_id": contact["id"]})

    contact_leads = auth_client.get(f"/api/contacts/{contact['id']}/leads").json()
    assert any(l["id"] == lead["id"] for l in contact_leads)


def test_lead_unknown_404s(auth_client):
    contact = auth_client.post("/api/contacts", json={
        "name": "404 Test Contact", "email": "404c@test.com", "phone": "555-5555"
    }).json()
    resp = auth_client.put(f"/api/leads/9999/contact", json={"contact_id": contact["id"]})
    assert resp.status_code == 404


def test_contact_unknown_404s(auth_client):
    resp = auth_client.get("/api/contacts/9999/leads")
    assert resp.status_code == 404


def test_lead_contact_link_distinct_from_conversion(auth_client):
    """A linked contact_id must not be confused with converted_contact_id - linking should
    never touch the lead's conversion state."""
    lead = auth_client.post("/api/leads", json={
        "name": "Distinct Test Lead", "email": "distinct@test.com", "phone": "555-6666", "source": "Direct"
    }).json()
    contact = auth_client.post("/api/contacts", json={
        "name": "Distinct Test Contact", "email": "distinctc@test.com", "phone": "555-7777"
    }).json()

    response = auth_client.put(f"/api/leads/{lead['id']}/contact", json={"contact_id": contact["id"]})
    updated = response.json()
    assert updated["contact_id"] == contact["id"]
    assert updated["converted_contact_id"] is None
