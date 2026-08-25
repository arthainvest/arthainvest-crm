def _first_deal(auth_client):
    return auth_client.get("/api/deals").json()[0]


def _create_company(auth_client, name="Acme Textiles"):
    return auth_client.post("/api/companies", json={"name": name}).json()


def test_company_starts_with_zero_deals(auth_client):
    company = _create_company(auth_client)
    assert company["deal_count"] == 0

    listed = auth_client.get("/api/companies").json()
    assert listed[0]["deal_count"] == 0


def test_link_deal_to_company_updates_count_and_name(auth_client):
    deal = _first_deal(auth_client)
    company = _create_company(auth_client)

    resp = auth_client.put(f"/api/deals/{deal['id']}/company", json={"company_id": company["id"]})
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["company_id"] == company["id"]
    assert updated["company_name"] == "Acme Textiles"

    companies = auth_client.get("/api/companies").json()
    linked = next(c for c in companies if c["id"] == company["id"])
    assert linked["deal_count"] == 1
    assert linked["contact_count"] == 0  # independent from the contact link

    all_deals = auth_client.get("/api/deals").json()
    fetched = next(d for d in all_deals if d["id"] == deal["id"])
    assert fetched["company_name"] == "Acme Textiles"


def test_get_company_deals_returns_linked_deals(auth_client):
    deals = auth_client.get("/api/deals").json()
    company = _create_company(auth_client)

    auth_client.put(f"/api/deals/{deals[0]['id']}/company", json={"company_id": company["id"]})
    auth_client.put(f"/api/deals/{deals[1]['id']}/company", json={"company_id": company["id"]})

    resp = auth_client.get(f"/api/companies/{company['id']}/deals")
    assert resp.status_code == 200
    linked = resp.json()
    assert len(linked) == 2
    assert {d["id"] for d in linked} == {deals[0]["id"], deals[1]["id"]}

    if len(deals) > 2:
        assert deals[2]["id"] not in {d["id"] for d in linked}


def test_get_company_deals_404s_for_unknown_company(auth_client):
    resp = auth_client.get("/api/companies/9999/deals")
    assert resp.status_code == 404


def test_unlink_deal_from_company(auth_client):
    deal = _first_deal(auth_client)
    company = _create_company(auth_client)

    auth_client.put(f"/api/deals/{deal['id']}/company", json={"company_id": company["id"]})
    linked_check = auth_client.get("/api/companies").json()
    assert next(c for c in linked_check if c["id"] == company["id"])["deal_count"] == 1

    resp = auth_client.put(f"/api/deals/{deal['id']}/company", json={"company_id": None})
    assert resp.status_code == 200
    assert resp.json()["company_id"] is None
    assert resp.json()["company_name"] is None

    after = auth_client.get("/api/companies").json()
    assert next(c for c in after if c["id"] == company["id"])["deal_count"] == 0


def test_link_deal_to_nonexistent_company_404s(auth_client):
    deal = _first_deal(auth_client)
    resp = auth_client.put(f"/api/deals/{deal['id']}/company", json={"company_id": 9999})
    assert resp.status_code == 404


def test_link_nonexistent_deal_404s(auth_client):
    company = _create_company(auth_client)
    resp = auth_client.put("/api/deals/9999/company", json={"company_id": company["id"]})
    assert resp.status_code == 404


def test_deleting_company_unlinks_its_deals(auth_client):
    deal = _first_deal(auth_client)
    company = _create_company(auth_client)
    auth_client.put(f"/api/deals/{deal['id']}/company", json={"company_id": company["id"]})

    del_resp = auth_client.delete(f"/api/companies/{company['id']}")
    assert del_resp.status_code == 200

    refreshed = next(d for d in auth_client.get("/api/deals").json() if d["id"] == deal["id"])
    assert refreshed["company_id"] is None
    assert refreshed["company_name"] is None


def test_deleting_company_unlinks_both_contacts_and_deals(auth_client):
    """A company linked from both sides at once must be fully cleaned up, not just one side."""
    deal = _first_deal(auth_client)
    contact = auth_client.get("/api/contacts").json()[0]
    company = _create_company(auth_client)

    auth_client.put(f"/api/deals/{deal['id']}/company", json={"company_id": company["id"]})
    auth_client.put(f"/api/contacts/{contact['id']}/company", json={"company_id": company["id"]})

    auth_client.delete(f"/api/companies/{company['id']}")

    deal_after = next(d for d in auth_client.get("/api/deals").json() if d["id"] == deal["id"])
    contact_after = next(c for c in auth_client.get("/api/contacts").json() if c["id"] == contact["id"])
    assert deal_after["company_id"] is None
    assert contact_after["company_id"] is None


def test_create_deal_with_company_id(auth_client):
    company = _create_company(auth_client)
    lead = auth_client.get("/api/leads").json()[0]

    resp = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 250000, "loan_product": "LAP", "company_id": company["id"]
    })
    assert resp.status_code == 200
    created = resp.json()
    assert created["company_id"] == company["id"]
    assert created["company_name"] == "Acme Textiles"

    companies = auth_client.get("/api/companies").json()
    assert next(c for c in companies if c["id"] == company["id"])["deal_count"] == 1
