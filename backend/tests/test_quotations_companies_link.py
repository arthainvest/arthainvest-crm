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


def test_quotation_unknown_404s(auth_client):
    resp = auth_client.put("/api/quotations/9999/company", json={"company_id": 1})
    assert resp.status_code == 404


def test_company_unknown_404s(auth_client):
    resp = auth_client.get("/api/companies/9999/quotations")
    assert resp.status_code == 404
