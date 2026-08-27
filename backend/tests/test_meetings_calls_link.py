def test_meeting_resolves_call_name(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Resolve Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    assert "call_id" in meeting
    assert "call_name" in meeting


def test_meeting_can_be_linked_to_call(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Link Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    call = auth_client.post("/api/calls", json={
        "name": "Link Test Call", "phone": "555-0001", "type": "Outbound"
    }).json()
    assert meeting.get("call_id") is None

    response = auth_client.put(f"/api/meetings/{meeting['id']}/call", json={"call_id": call["id"]})
    updated = response.json()
    assert updated["call_id"] == call["id"]
    assert updated["call_name"] == "Link Test Call"


def test_meeting_can_be_unlinked_from_call(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Unlink Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    call = auth_client.post("/api/calls", json={
        "name": "Unlink Test Call", "phone": "555-0002", "type": "Inbound"
    }).json()

    auth_client.put(f"/api/meetings/{meeting['id']}/call", json={"call_id": call["id"]})
    response = auth_client.put(f"/api/meetings/{meeting['id']}/call", json={"call_id": None})
    updated = response.json()
    assert updated["call_id"] is None
    assert updated["call_name"] is None


def test_call_meetings_endpoint_exists(auth_client):
    call = auth_client.post("/api/calls", json={
        "name": "Endpoint Test Call", "phone": "555-0003", "type": "Outbound"
    }).json()
    resp = auth_client.get(f"/api/calls/{call['id']}/meetings")
    assert resp.status_code == 200
    meetings = resp.json()
    assert isinstance(meetings, list)


def test_call_shows_meetings_when_linked(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Show Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    call = auth_client.post("/api/calls", json={
        "name": "Show Test Call", "phone": "555-0004", "type": "Outbound"
    }).json()

    auth_client.put(f"/api/meetings/{meeting['id']}/call", json={"call_id": call["id"]})

    call_meetings = auth_client.get(f"/api/calls/{call['id']}/meetings").json()
    assert any(m["id"] == meeting["id"] for m in call_meetings)


def test_meeting_unknown_404s(auth_client):
    call = auth_client.post("/api/calls", json={
        "name": "404 Test Call", "phone": "555-0005", "type": "Outbound"
    }).json()
    resp = auth_client.put(f"/api/meetings/9999/call", json={"call_id": call["id"]})
    assert resp.status_code == 404


def test_call_unknown_404s(auth_client):
    resp = auth_client.get("/api/calls/9999/meetings")
    assert resp.status_code == 404


def test_meetings_list_resolves_call_name(auth_client):
    """Guards against the list-vs-single-fetch divergence bug found in earlier list
    endpoints - the meetings list must resolve call_name too, not just single-meeting GET."""
    meeting = auth_client.post("/api/meetings", json={
        "title": "List Test Meeting", "meeting_date": "2026-09-17"
    }).json()
    call = auth_client.post("/api/calls", json={
        "name": "List Test Call", "phone": "555-0006", "type": "Outbound"
    }).json()
    auth_client.put(f"/api/meetings/{meeting['id']}/call", json={"call_id": call["id"]})

    listed = auth_client.get("/api/meetings?date=2026-09-17").json()
    found = next(m for m in listed if m["id"] == meeting["id"])
    assert found["call_id"] == call["id"]
    assert found["call_name"] == "List Test Call"
