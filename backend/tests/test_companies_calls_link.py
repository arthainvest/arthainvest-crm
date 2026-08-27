def test_call_resolves_company_name(auth_client):
    call = auth_client.post("/api/calls", json={
        "name": "Resolve Test Call", "phone": "555-1001", "type": "Outbound"
    }).json()
    assert "company_id" in call
    assert "company_name" in call


def test_call_can_be_linked_to_company(auth_client):
    call = auth_client.post("/api/calls", json={
        "name": "Link Test Call", "phone": "555-1002", "type": "Outbound"
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Link Test Company", "industry": "Tech", "city": "Boston"
    }).json()
    assert call.get("company_id") is None

    response = auth_client.put(f"/api/calls/{call['id']}/company", json={"company_id": company["id"]})
    updated = response.json()
    assert updated["company_id"] == company["id"]
    assert updated["company_name"] is not None


def test_call_can_be_unlinked_from_company(auth_client):
    call = auth_client.post("/api/calls", json={
        "name": "Unlink Test Call", "phone": "555-1003", "type": "Outbound"
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Unlink Test Company", "industry": "Finance", "city": "New York"
    }).json()

    auth_client.put(f"/api/calls/{call['id']}/company", json={"company_id": company["id"]})
    response = auth_client.put(f"/api/calls/{call['id']}/company", json={"company_id": None})
    updated = response.json()
    assert updated["company_id"] is None
    assert updated["company_name"] is None


def test_company_calls_endpoint_exists(auth_client):
    company = auth_client.post("/api/companies", json={
        "name": "Endpoint Test Company", "industry": "Retail", "city": "Chicago"
    }).json()
    resp = auth_client.get(f"/api/companies/{company['id']}/calls")
    assert resp.status_code == 200
    calls = resp.json()
    assert isinstance(calls, list)


def test_company_shows_calls_when_linked(auth_client):
    call = auth_client.post("/api/calls", json={
        "name": "Show Test Call", "phone": "555-1004", "type": "Outbound"
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Show Test Company", "industry": "Insurance", "city": "Miami"
    }).json()

    auth_client.put(f"/api/calls/{call['id']}/company", json={"company_id": company["id"]})

    company_calls = auth_client.get(f"/api/companies/{company['id']}/calls").json()
    assert any(c["id"] == call["id"] for c in company_calls)


def test_call_unknown_404s(auth_client):
    company = auth_client.post("/api/companies", json={
        "name": "404 Test Company", "industry": "Services", "city": "Seattle"
    }).json()
    resp = auth_client.put(f"/api/calls/9999/company", json={"company_id": company["id"]})
    assert resp.status_code == 404


def test_company_unknown_404s(auth_client):
    resp = auth_client.get("/api/companies/9999/calls")
    assert resp.status_code == 404
