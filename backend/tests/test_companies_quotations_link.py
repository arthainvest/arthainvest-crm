def _first_deal(auth_client):
    return auth_client.get("/api/deals").json()[0]


def _create_company(auth_client, name="Quote Co"):
    return auth_client.post("/api/companies", json={"name": name}).json()


def test_company_starts_with_zero_quotations(auth_client):
    company = _create_company(auth_client)
    assert company["quotation_count"] == 0

    listed = auth_client.get("/api/companies").json()
    assert next(c for c in listed if c["id"] == company["id"])["quotation_count"] == 0


def test_quotation_via_deal_updates_company_quotation_count(auth_client):
    """Quotations have no company_id of their own - the count must be derived through the
    linked deal's company_id (quotations.deal_id -> deals.company_id), the same indirect path
    fetch_quotation_with_details already resolves for a single quotation's company_name."""
    deal = _first_deal(auth_client)
    lead = auth_client.get(f"/api/leads/{deal['lead_id']}").json()
    company = _create_company(auth_client)
    auth_client.put(f"/api/deals/{deal['id']}/company", json={"company_id": company["id"]})

    auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deal["id"], "title": "Quote 1",
        "items": [{"description": "Fee", "amount": 1000}],
    })

    companies = auth_client.get("/api/companies").json()
    linked = next(c for c in companies if c["id"] == company["id"])
    assert linked["quotation_count"] == 1


def test_get_company_quotations_returns_quotations_via_linked_deals(auth_client):
    deals = auth_client.get("/api/deals").json()
    company = _create_company(auth_client)
    auth_client.put(f"/api/deals/{deals[0]['id']}/company", json={"company_id": company["id"]})

    lead = auth_client.get(f"/api/leads/{deals[0]['lead_id']}").json()
    created = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deals[0]["id"], "title": "Company Quote",
        "items": [{"description": "Processing Fee", "amount": 2500}],
    }).json()

    resp = auth_client.get(f"/api/companies/{company['id']}/quotations")
    assert resp.status_code == 200
    quotations = resp.json()
    assert len(quotations) == 1
    assert quotations[0]["id"] == created["id"]
    assert quotations[0]["company_id"] == company["id"]
    assert quotations[0]["company_name"] == company["name"]


def test_get_company_quotations_excludes_other_companies(auth_client):
    deals = auth_client.get("/api/deals").json()
    company_a = _create_company(auth_client, name="Company A")
    company_b = _create_company(auth_client, name="Company B")
    auth_client.put(f"/api/deals/{deals[0]['id']}/company", json={"company_id": company_a["id"]})

    lead = auth_client.get(f"/api/leads/{deals[0]['lead_id']}").json()
    auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deals[0]["id"], "title": "A's Quote",
        "items": [{"description": "Fee", "amount": 500}],
    })

    resp = auth_client.get(f"/api/companies/{company_b['id']}/quotations")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_company_quotations_404s_for_unknown_company(auth_client):
    resp = auth_client.get("/api/companies/9999/quotations")
    assert resp.status_code == 404


def test_unlinking_deal_from_company_removes_its_quotations_from_the_count(auth_client):
    deal = _first_deal(auth_client)
    lead = auth_client.get(f"/api/leads/{deal['lead_id']}").json()
    company = _create_company(auth_client)
    auth_client.put(f"/api/deals/{deal['id']}/company", json={"company_id": company["id"]})
    auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deal["id"], "title": "Soon Unlinked",
        "items": [{"description": "Fee", "amount": 100}],
    })

    auth_client.put(f"/api/deals/{deal['id']}/company", json={"company_id": None})

    companies = auth_client.get("/api/companies").json()
    linked = next(c for c in companies if c["id"] == company["id"])
    assert linked["quotation_count"] == 0
