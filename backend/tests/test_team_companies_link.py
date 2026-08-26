def test_team_member_companies_endpoint_exists(auth_client):
    team_members = auth_client.get("/api/team").json()
    tm = next(m for m in team_members if m["name"] == "Rajesh Kumar")
    resp = auth_client.get(f"/api/team/{tm['id']}/companies")
    assert resp.status_code == 200
    companies = resp.json()
    assert isinstance(companies, list)


def test_team_member_has_no_companies_initially(auth_client):
    """A team member with no deals has no companies."""
    team_members = auth_client.get("/api/team").json()
    tm = next(m for m in team_members if m["name"] == "Priya Singh")
    companies = auth_client.get(f"/api/team/{tm['id']}/companies").json()
    assert len(companies) == 0


def test_team_member_shows_company_when_deal_assigned(auth_client):
    """Assigning a deal to a team member makes their company visible in the member's portfolio."""
    team_members = auth_client.get("/api/team").json()
    rajesh = next(m for m in team_members if m["name"] == "Rajesh Kumar")

    deal = auth_client.get("/api/deals").json()[0]
    company = auth_client.post("/api/companies", json={"name": "Rajesh's Company"}).json()

    auth_client.put(f"/api/deals/{deal['id']}/assign", json={"team_member_id": rajesh["id"]})
    auth_client.put(f"/api/deals/{deal['id']}/company", json={"company_id": company["id"]})

    companies = auth_client.get(f"/api/team/{rajesh['id']}/companies").json()
    assert len(companies) == 1
    assert companies[0]["id"] == company["id"]
    assert companies[0]["name"] == company["name"]


def test_company_team_members_endpoint_exists(auth_client):
    company = auth_client.post("/api/companies", json={"name": "Test Company"}).json()
    resp = auth_client.get(f"/api/companies/{company['id']}/team_members")
    assert resp.status_code == 200
    members = resp.json()
    assert isinstance(members, list)


def test_company_has_team_members_from_its_deals(auth_client):
    """A company's team member list comes from members assigned to its deals."""
    deal = auth_client.get("/api/deals").json()[0]
    company = auth_client.post("/api/companies", json={"name": "Company with Deal"}).json()
    team_members = auth_client.get("/api/team").json()
    rajesh = next(m for m in team_members if m["name"] == "Rajesh Kumar")

    auth_client.put(f"/api/deals/{deal['id']}/company", json={"company_id": company["id"]})
    auth_client.put(f"/api/deals/{deal['id']}/assign", json={"team_member_id": rajesh["id"]})

    company_members = auth_client.get(f"/api/companies/{company['id']}/team_members").json()
    member_ids = {m["id"] for m in company_members}
    assert rajesh["id"] in member_ids


def test_team_member_unknown_404s(auth_client):
    resp = auth_client.get("/api/team/9999/companies")
    assert resp.status_code == 404


def test_company_unknown_404s(auth_client):
    resp = auth_client.get("/api/companies/9999/team_members")
    assert resp.status_code == 404


def test_each_company_appears_once_despite_multiple_deals(auth_client):
    """If a team member has multiple deals with the same company, the company appears once."""
    team_members = auth_client.get("/api/team").json()
    rajesh = next(m for m in team_members if m["name"] == "Rajesh Kumar")
    company = auth_client.post("/api/companies", json={"name": "Multi-Deal Company"}).json()

    deals = auth_client.get("/api/deals").json()
    deal1, deal2 = deals[0], deals[1]

    auth_client.put(f"/api/deals/{deal1['id']}/assign", json={"team_member_id": rajesh["id"]})
    auth_client.put(f"/api/deals/{deal1['id']}/company", json={"company_id": company["id"]})
    auth_client.put(f"/api/deals/{deal2['id']}/assign", json={"team_member_id": rajesh["id"]})
    auth_client.put(f"/api/deals/{deal2['id']}/company", json={"company_id": company["id"]})

    companies = auth_client.get(f"/api/team/{rajesh['id']}/companies").json()
    assert len(companies) == 1
    assert companies[0]["id"] == company["id"]
