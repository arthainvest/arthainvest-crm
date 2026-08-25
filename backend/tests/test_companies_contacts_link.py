def _first_contact(auth_client):
    return auth_client.get("/api/contacts").json()[0]


def _create_company(auth_client, name="Acme Textiles"):
    return auth_client.post("/api/companies", json={"name": name}).json()


def test_company_starts_with_zero_contacts(auth_client):
    company = _create_company(auth_client)
    assert company["contact_count"] == 0

    listed = auth_client.get("/api/companies").json()
    assert listed[0]["contact_count"] == 0


def test_link_contact_to_company_updates_count_and_name(auth_client):
    contact = _first_contact(auth_client)
    company = _create_company(auth_client)

    resp = auth_client.put(f"/api/contacts/{contact['id']}/company", json={"company_id": company["id"]})
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["company_id"] == company["id"]
    assert updated["company_name"] == "Acme Textiles"

    # The free-text company field (if any) survives a link - it's a separate column.
    assert updated["company"] == contact.get("company")

    companies = auth_client.get("/api/companies").json()
    linked = next(c for c in companies if c["id"] == company["id"])
    assert linked["contact_count"] == 1

    # And it shows up in /api/contacts too, not just the single-contact fetch.
    all_contacts = auth_client.get("/api/contacts").json()
    fetched = next(c for c in all_contacts if c["id"] == contact["id"])
    assert fetched["company_name"] == "Acme Textiles"


def test_get_company_contacts_returns_linked_contacts(auth_client):
    contacts = auth_client.get("/api/contacts").json()
    company = _create_company(auth_client)

    auth_client.put(f"/api/contacts/{contacts[0]['id']}/company", json={"company_id": company["id"]})
    auth_client.put(f"/api/contacts/{contacts[1]['id']}/company", json={"company_id": company["id"]})

    resp = auth_client.get(f"/api/companies/{company['id']}/contacts")
    assert resp.status_code == 200
    linked = resp.json()
    assert len(linked) == 2
    assert {c["id"] for c in linked} == {contacts[0]["id"], contacts[1]["id"]}

    # A contact not linked to this company must not appear.
    assert contacts[2]["id"] not in {c["id"] for c in linked}


def test_get_company_contacts_404s_for_unknown_company(auth_client):
    resp = auth_client.get("/api/companies/9999/contacts")
    assert resp.status_code == 404


def test_unlink_contact_from_company(auth_client):
    contact = _first_contact(auth_client)
    company = _create_company(auth_client)

    auth_client.put(f"/api/contacts/{contact['id']}/company", json={"company_id": company["id"]})
    linked_check = auth_client.get("/api/companies").json()
    assert next(c for c in linked_check if c["id"] == company["id"])["contact_count"] == 1

    resp = auth_client.put(f"/api/contacts/{contact['id']}/company", json={"company_id": None})
    assert resp.status_code == 200
    assert resp.json()["company_id"] is None
    assert resp.json()["company_name"] is None

    after = auth_client.get("/api/companies").json()
    assert next(c for c in after if c["id"] == company["id"])["contact_count"] == 0


def test_link_to_nonexistent_company_404s(auth_client):
    contact = _first_contact(auth_client)
    resp = auth_client.put(f"/api/contacts/{contact['id']}/company", json={"company_id": 9999})
    assert resp.status_code == 404


def test_link_nonexistent_contact_404s(auth_client):
    company = _create_company(auth_client)
    resp = auth_client.put("/api/contacts/9999/company", json={"company_id": company["id"]})
    assert resp.status_code == 404


def test_deleting_company_unlinks_its_contacts(auth_client):
    contact = _first_contact(auth_client)
    company = _create_company(auth_client)
    auth_client.put(f"/api/contacts/{contact['id']}/company", json={"company_id": company["id"]})

    del_resp = auth_client.delete(f"/api/companies/{company['id']}")
    assert del_resp.status_code == 200

    refreshed = next(c for c in auth_client.get("/api/contacts").json() if c["id"] == contact["id"])
    assert refreshed["company_id"] is None
    assert refreshed["company_name"] is None


def test_create_contact_with_company_id(auth_client):
    company = _create_company(auth_client)
    resp = auth_client.post("/api/contacts", json={
        "name": "Rohit Sharma", "phone": "9876543299", "company_id": company["id"]
    })
    assert resp.status_code == 200
    created = resp.json()
    assert created["company_id"] == company["id"]
    assert created["company_name"] == "Acme Textiles"

    companies = auth_client.get("/api/companies").json()
    assert next(c for c in companies if c["id"] == company["id"])["contact_count"] == 1
