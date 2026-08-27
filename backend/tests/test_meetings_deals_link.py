def test_meeting_resolves_deal_label(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Resolve Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    assert "deal_id" in meeting
    assert "deal_label" in meeting


def test_meeting_can_be_linked_to_deal(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Link Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    deal_lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": deal_lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    assert meeting.get("deal_id") is None

    response = auth_client.put(f"/api/meetings/{meeting['id']}/deal", json={"deal_id": deal["id"]})
    updated = response.json()
    assert updated["deal_id"] == deal["id"]
    assert updated["deal_label"] is not None


def test_meeting_can_be_unlinked_from_deal(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Unlink Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    deal_lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": deal_lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()

    auth_client.put(f"/api/meetings/{meeting['id']}/deal", json={"deal_id": deal["id"]})
    response = auth_client.put(f"/api/meetings/{meeting['id']}/deal", json={"deal_id": None})
    updated = response.json()
    assert updated["deal_id"] is None
    assert updated["deal_label"] is None


def test_deal_meetings_endpoint_exists(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    resp = auth_client.get(f"/api/deals/{deal['id']}/meetings")
    assert resp.status_code == 200
    meetings = resp.json()
    assert isinstance(meetings, list)


def test_deal_shows_meetings_when_linked(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Show Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    deal_lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": deal_lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()

    auth_client.put(f"/api/meetings/{meeting['id']}/deal", json={"deal_id": deal["id"]})

    deal_meetings = auth_client.get(f"/api/deals/{deal['id']}/meetings").json()
    assert any(m["id"] == meeting["id"] for m in deal_meetings)


def test_meeting_unknown_404s(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    resp = auth_client.put(f"/api/meetings/9999/deal", json={"deal_id": deal["id"]})
    assert resp.status_code == 404


def test_deal_unknown_404s(auth_client):
    resp = auth_client.get("/api/deals/9999/meetings")
    assert resp.status_code == 404


def test_meetings_list_resolves_deal_label(auth_client):
    """Guards against the list-vs-single-fetch divergence bug found in the leads/tasks list
    endpoints - the meetings list must resolve deal_label too, not just single-meeting GET."""
    meeting = auth_client.post("/api/meetings", json={
        "title": "List Test Meeting", "meeting_date": "2026-09-16"
    }).json()
    deal_lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": deal_lead["id"], "deal_value": 250000, "probability": 0.7
    }).json()
    auth_client.put(f"/api/meetings/{meeting['id']}/deal", json={"deal_id": deal["id"]})

    listed = auth_client.get("/api/meetings?date=2026-09-16").json()
    found = next(m for m in listed if m["id"] == meeting["id"])
    assert found["deal_id"] == deal["id"]
    assert found["deal_label"] is not None
