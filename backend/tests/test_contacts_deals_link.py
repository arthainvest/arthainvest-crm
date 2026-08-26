def test_deal_resolves_contact_name(auth_client):
    deal = auth_client.get("/api/deals").json()[0]
    assert "contact_id" in deal
    assert "contact_name" in deal


def test_convert_lead_backfills_deal_contact_id(auth_client):
    """When a lead is converted to a contact, all its deals get the contact_id filled."""
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.get(f"/api/deals?lead_id={lead['id']}").json()[0]
    assert deal.get("contact_id") is None

    contact = auth_client.post(f"/api/leads/{lead['id']}/convert").json()

    updated_deal = next(d for d in auth_client.get("/api/deals").json() if d["id"] == deal["id"])
    assert updated_deal["contact_id"] == contact["id"]
    assert updated_deal["contact_name"] == contact["name"]


def test_contact_can_be_directly_linked_to_deal(auth_client):
    deal = auth_client.get("/api/deals").json()[0]
    contact = auth_client.get("/api/contacts").json()[0]

    auth_client.put(f"/api/deals/{deal['id']}/contact", json={"contact_id": contact["id"]})

    updated_deal = next(d for d in auth_client.get("/api/deals").json() if d["id"] == deal["id"])
    assert updated_deal["contact_id"] == contact["id"]
    assert updated_deal["contact_name"] == contact["name"]


def test_unlink_deal_from_contact(auth_client):
    deal = auth_client.get("/api/deals").json()[0]
    contact = auth_client.get("/api/contacts").json()[0]

    auth_client.put(f"/api/deals/{deal['id']}/contact", json={"contact_id": contact["id"]})
    auth_client.put(f"/api/deals/{deal['id']}/contact", json={"contact_id": None})

    updated_deal = next(d for d in auth_client.get("/api/deals").json() if d["id"] == deal["id"])
    assert updated_deal["contact_id"] is None
    assert updated_deal["contact_name"] is None
