def test_meeting_resolves_quotation_title(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Resolve Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    assert "quotation_id" in meeting
    assert "quotation_title" in meeting


def test_meeting_can_be_linked_to_quotation(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Link Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    lead = auth_client.get("/api/leads").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "Link Test Quote",
        "items": [{"description": "Processing Fee", "amount": 1200}],
    }).json()
    assert meeting.get("quotation_id") is None

    response = auth_client.put(f"/api/meetings/{meeting['id']}/quotation", json={"quotation_id": quotation["id"]})
    updated = response.json()
    assert updated["quotation_id"] == quotation["id"]
    assert updated["quotation_title"] == "Link Test Quote"


def test_meeting_can_be_unlinked_from_quotation(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Unlink Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    lead = auth_client.get("/api/leads").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "Unlink Test Quote",
        "items": [{"description": "Fee", "amount": 600}],
    }).json()

    auth_client.put(f"/api/meetings/{meeting['id']}/quotation", json={"quotation_id": quotation["id"]})
    response = auth_client.put(f"/api/meetings/{meeting['id']}/quotation", json={"quotation_id": None})
    updated = response.json()
    assert updated["quotation_id"] is None
    assert updated["quotation_title"] is None


def test_quotation_meetings_endpoint_exists(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "Endpoint Test Quote",
        "items": [{"description": "Fee", "amount": 800}],
    }).json()
    resp = auth_client.get(f"/api/quotations/{quotation['id']}/meetings")
    assert resp.status_code == 200
    meetings = resp.json()
    assert isinstance(meetings, list)


def test_quotation_shows_meetings_when_linked(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Show Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    lead = auth_client.get("/api/leads").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "Show Test Quote",
        "items": [{"description": "Fee", "amount": 950}],
    }).json()

    auth_client.put(f"/api/meetings/{meeting['id']}/quotation", json={"quotation_id": quotation["id"]})

    quotation_meetings = auth_client.get(f"/api/quotations/{quotation['id']}/meetings").json()
    assert any(m["id"] == meeting["id"] for m in quotation_meetings)


def test_meeting_unknown_404s(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "404 Test Quote",
        "items": [{"description": "Fee", "amount": 300}],
    }).json()
    resp = auth_client.put(f"/api/meetings/9999/quotation", json={"quotation_id": quotation["id"]})
    assert resp.status_code == 404


def test_quotation_unknown_404s(auth_client):
    resp = auth_client.get("/api/quotations/9999/meetings")
    assert resp.status_code == 404


def test_meetings_list_resolves_quotation_title(auth_client):
    """Guards against the list-vs-single-fetch divergence bug found in earlier list
    endpoints - the meetings list must resolve quotation_title too, not just single-meeting
    GET."""
    meeting = auth_client.post("/api/meetings", json={
        "title": "List Test Meeting", "meeting_date": "2026-09-19"
    }).json()
    lead = auth_client.get("/api/leads").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "List Test Quote",
        "items": [{"description": "Fee", "amount": 1100}],
    }).json()
    auth_client.put(f"/api/meetings/{meeting['id']}/quotation", json={"quotation_id": quotation["id"]})

    listed = auth_client.get("/api/meetings?date=2026-09-19").json()
    found = next(m for m in listed if m["id"] == meeting["id"])
    assert found["quotation_id"] == quotation["id"]
    assert found["quotation_title"] == "List Test Quote"
