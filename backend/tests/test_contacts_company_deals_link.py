def test_contacts_company_deals_are_reachable_via_two_hop_link(auth_client):
    """The Contacts page's Notes & Follow-up modal now shows a 'Company Deals' section by
    following contact.company_id -> GET /api/companies/{id}/deals - proving a contact's own
    company's deals are reachable through the same link the Companies page already uses,
    not a fabricated or separate relationship."""
    contact = auth_client.get("/api/contacts").json()[0]
    deal = auth_client.get("/api/deals").json()[0]
    company = auth_client.post("/api/companies", json={"name": "Two Hop Textiles"}).json()

    auth_client.put(f"/api/contacts/{contact['id']}/company", json={"company_id": company["id"]})
    auth_client.put(f"/api/deals/{deal['id']}/company", json={"company_id": company["id"]})

    refreshed_contact = next(c for c in auth_client.get("/api/contacts").json() if c["id"] == contact["id"])
    assert refreshed_contact["company_id"] == company["id"]

    company_deals = auth_client.get(f"/api/companies/{refreshed_contact['company_id']}/deals").json()
    assert len(company_deals) == 1
    assert company_deals[0]["id"] == deal["id"]


def test_contact_with_no_company_has_no_reachable_deals(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    assert contact["company_id"] is None
