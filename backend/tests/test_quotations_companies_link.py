def test_quotation_resolves_company_name(auth_client):
    deal = auth_client.get("/api/deals").json()[0]
    lead = auth_client.get(f"/api/leads/{deal['lead_id']}").json()
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deal["id"], "title": "Test Quotation",
        "items": [{"description": "Fee", "amount": 1000}]
    }).json()
    assert "company_id" in quotation
    assert "company_name" in quotation


def test_quotation_can_be_linked_to_company(auth_client):
    deal = auth_client.get("/api/deals").json()[0]
    lead = auth_client.get(f"/api/leads/{deal['lead_id']}").json()
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deal["id"], "title": "Test Q",
        "items": [{"description": "Fee", "amount": 500}]
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Test Company", "industry": "Tech", "employee_count": 50, "rating": 4.5
    }).json()
    assert quotation.get("company_id") is None

    auth_client.put(f"/api/quotations/{quotation['id']}/company", json={"company_id": company["id"]})

    updated = auth_client.get(f"/api/quotations/{quotation['id']}").json()
    assert updated["company_id"] == company["id"]
    assert updated["company_name"] == company["name"]


def test_quotation_can_be_unlinked_from_company(auth_client):
    deal = auth_client.get("/api/deals").json()[0]
    lead = auth_client.get(f"/api/leads/{deal['lead_id']}").json()
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deal["id"], "title": "Unlink Test",
        "items": [{"description": "Fee", "amount": 500}]
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Unlink Test Company", "industry": "Finance", "employee_count": 100, "rating": 4.0
    }).json()

    auth_client.put(f"/api/quotations/{quotation['id']}/company", json={"company_id": company["id"]})
    auth_client.put(f"/api/quotations/{quotation['id']}/company", json={"company_id": None})

    updated = auth_client.get(f"/api/quotations/{quotation['id']}").json()
    assert updated["company_id"] is None
    assert updated["company_name"] is None


def test_company_quotations_endpoint_exists(auth_client):
    company = auth_client.post("/api/companies", json={
        "name": "Endpoint Test Company", "industry": "Retail", "employee_count": 25, "rating": 3.5
    }).json()
    resp = auth_client.get(f"/api/companies/{company['id']}/quotations")
    assert resp.status_code == 200
    quotations = resp.json()
    assert isinstance(quotations, list)


def test_company_shows_quotations_when_linked(auth_client):
    company = auth_client.post("/api/companies", json={
        "name": "Show Test Company", "industry": "Manufacturing", "employee_count": 150, "rating": 4.5
    }).json()
    company_quots = auth_client.get(f"/api/companies/{company['id']}/quotations").json()
    assert isinstance(company_quots, list)
    initial_count = len(company_quots)

    deal = auth_client.get("/api/deals").json()[0]
    lead = auth_client.get(f"/api/leads/{deal['lead_id']}").json()
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deal["id"], "title": "Company Show",
        "items": [{"description": "Fee", "amount": 500}]
    }).json()

    response = auth_client.put(f"/api/quotations/{quotation['id']}/company", json={"company_id": company["id"]})
    linked_quotation = response.json()
    assert linked_quotation["company_id"] == company["id"]
    assert linked_quotation["company_name"] == company["name"]

    company_quots_after = auth_client.get(f"/api/companies/{company['id']}/quotations").json()
    assert len(company_quots_after) == initial_count + 1
    assert any(q["id"] == quotation["id"] for q in company_quots_after)


def test_company_quotation_count_includes_directly_linked_quotation_with_no_deal(auth_client):
    """CompanyResponse.quotation_count (shown on the Companies list/detail pages) is a
    separate COUNT(*) subquery from the reverse-lookup endpoint - it had the same
    deals-only blind spot and needs its own coverage."""
    company = auth_client.post("/api/companies", json={
        "name": "Count Test Company", "industry": "Legal", "employee_count": 5, "rating": 4.0
    }).json()
    assert company["quotation_count"] == 0

    lead = auth_client.get("/api/leads").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "Count Test Quote",
        "items": [{"description": "Fee", "amount": 200}]
    }).json()
    auth_client.put(f"/api/quotations/{quotation['id']}/company", json={"company_id": company["id"]})

    listed = auth_client.get("/api/companies").json()
    found = next(c for c in listed if c["id"] == company["id"])
    assert found["quotation_count"] == 1


def test_company_quotations_finds_directly_linked_quotation_with_no_deal(auth_client):
    """A quotation can be linked straight to a Company (quotations.company_id) without going
    through a Deal at all - the reverse lookup must find it via that direct link, not only
    through deals.company_id."""
    company = auth_client.post("/api/companies", json={
        "name": "Direct Link Company", "industry": "Legal", "employee_count": 10, "rating": 4.0
    }).json()
    lead = auth_client.get("/api/leads").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "No Deal Quote",
        "items": [{"description": "Fee", "amount": 300}]
    }).json()
    assert quotation.get("deal_id") is None

    auth_client.put(f"/api/quotations/{quotation['id']}/company", json={"company_id": company["id"]})

    company_quots = auth_client.get(f"/api/companies/{company['id']}/quotations").json()
    assert any(q["id"] == quotation["id"] for q in company_quots)


def test_quotation_unknown_404s(auth_client):
    resp = auth_client.put("/api/quotations/9999/company", json={"company_id": 1})
    assert resp.status_code == 404


def test_company_unknown_404s(auth_client):
    resp = auth_client.get("/api/companies/9999/quotations")
    assert resp.status_code == 404
