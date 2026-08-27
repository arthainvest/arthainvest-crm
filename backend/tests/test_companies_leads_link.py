def test_lead_resolves_company_name(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    assert "company_id" in lead
    assert "company_name" in lead


def test_lead_can_be_linked_to_company(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Link Test Lead", "email": "link@test.com", "phone": "555-0001", "source": "Direct"
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Link Test Company", "industry": "Tech", "city": "Boston"
    }).json()
    assert lead.get("company_id") is None

    response = auth_client.put(f"/api/leads/{lead['id']}/company", json={"company_id": company["id"]})
    updated = response.json()
    assert updated["company_id"] == company["id"]
    assert updated["company_name"] is not None


def test_lead_can_be_unlinked_from_company(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Unlink Test Lead", "email": "unlink@test.com", "phone": "555-0002", "source": "Direct"
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Unlink Test Company", "industry": "Finance", "city": "New York"
    }).json()

    auth_client.put(f"/api/leads/{lead['id']}/company", json={"company_id": company["id"]})
    response = auth_client.put(f"/api/leads/{lead['id']}/company", json={"company_id": None})
    updated = response.json()
    assert updated["company_id"] is None
    assert updated["company_name"] is None


def test_company_leads_endpoint_exists(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    company = auth_client.post("/api/companies", json={
        "name": "Endpoint Test Company", "industry": "Retail", "city": "Chicago"
    }).json()
    resp = auth_client.get(f"/api/companies/{company['id']}/leads")
    assert resp.status_code == 200
    leads = resp.json()
    assert isinstance(leads, list)


def test_company_shows_leads_when_linked(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Show Test Lead", "email": "show@test.com", "phone": "555-0003", "source": "Direct"
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Show Test Company", "industry": "Insurance", "city": "Miami"
    }).json()

    auth_client.put(f"/api/leads/{lead['id']}/company", json={"company_id": company["id"]})

    company_leads = auth_client.get(f"/api/companies/{company['id']}/leads").json()
    assert any(l["id"] == lead["id"] for l in company_leads)


def test_lead_unknown_404s(auth_client):
    company = auth_client.post("/api/companies", json={
        "name": "404 Test Company", "industry": "Services", "city": "Seattle"
    }).json()
    resp = auth_client.put(f"/api/leads/9999/company", json={"company_id": company["id"]})
    assert resp.status_code == 404


def test_company_unknown_404s(auth_client):
    resp = auth_client.get("/api/companies/9999/leads")
    assert resp.status_code == 404
