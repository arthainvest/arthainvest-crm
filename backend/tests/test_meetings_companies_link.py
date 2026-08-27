def test_meeting_resolves_company_name(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Resolve Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    assert "company_id" in meeting
    assert "company_name" in meeting


def test_meeting_can_be_linked_to_company(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Link Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Link Test Company", "industry": "Tech", "city": "Boston"
    }).json()
    assert meeting.get("company_id") is None

    response = auth_client.put(f"/api/meetings/{meeting['id']}/company", json={"company_id": company["id"]})
    updated = response.json()
    assert updated["company_id"] == company["id"]
    assert updated["company_name"] == "Link Test Company"


def test_meeting_can_be_unlinked_from_company(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Unlink Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Unlink Test Company", "industry": "Finance", "city": "New York"
    }).json()

    auth_client.put(f"/api/meetings/{meeting['id']}/company", json={"company_id": company["id"]})
    response = auth_client.put(f"/api/meetings/{meeting['id']}/company", json={"company_id": None})
    updated = response.json()
    assert updated["company_id"] is None
    assert updated["company_name"] is None


def test_company_meetings_endpoint_exists(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Endpoint Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Endpoint Test Company", "industry": "Retail", "city": "Chicago"
    }).json()
    resp = auth_client.get(f"/api/companies/{company['id']}/meetings")
    assert resp.status_code == 200
    meetings = resp.json()
    assert isinstance(meetings, list)


def test_company_shows_meetings_when_linked(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Show Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Show Test Company", "industry": "Insurance", "city": "Miami"
    }).json()

    auth_client.put(f"/api/meetings/{meeting['id']}/company", json={"company_id": company["id"]})

    company_meetings = auth_client.get(f"/api/companies/{company['id']}/meetings").json()
    assert any(m["id"] == meeting["id"] for m in company_meetings)


def test_meeting_unknown_404s(auth_client):
    company = auth_client.post("/api/companies", json={
        "name": "404 Test Company", "industry": "Services", "city": "Seattle"
    }).json()
    resp = auth_client.put(f"/api/meetings/9999/company", json={"company_id": company["id"]})
    assert resp.status_code == 404


def test_company_unknown_404s(auth_client):
    resp = auth_client.get("/api/companies/9999/meetings")
    assert resp.status_code == 404


def test_meetings_list_resolves_company_name(auth_client):
    """Guards against the list-vs-single-fetch divergence bug found in the leads/tasks list
    endpoints - the meetings list must resolve company_name too, not just single-meeting GET."""
    meeting = auth_client.post("/api/meetings", json={
        "title": "List Test Meeting", "meeting_date": "2026-09-15"
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "List Test Company", "industry": "Legal", "city": "Denver"
    }).json()
    auth_client.put(f"/api/meetings/{meeting['id']}/company", json={"company_id": company["id"]})

    listed = auth_client.get("/api/meetings?date=2026-09-15").json()
    found = next(m for m in listed if m["id"] == meeting["id"])
    assert found["company_id"] == company["id"]
    assert found["company_name"] == "List Test Company"
