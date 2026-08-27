def test_meeting_resolves_task_name(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Resolve Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    assert "task_id" in meeting
    assert "task_name" in meeting


def test_meeting_can_be_linked_to_task(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Link Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    task = auth_client.post("/api/tasks", json={
        "title": "Link Test Task", "due_date": "2026-09-01"
    }).json()
    assert meeting.get("task_id") is None

    response = auth_client.put(f"/api/meetings/{meeting['id']}/task", json={"task_id": task["id"]})
    updated = response.json()
    assert updated["task_id"] == task["id"]
    assert updated["task_name"] == "Link Test Task"


def test_meeting_can_be_unlinked_from_task(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Unlink Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    task = auth_client.post("/api/tasks", json={
        "title": "Unlink Test Task", "due_date": "2026-09-01"
    }).json()

    auth_client.put(f"/api/meetings/{meeting['id']}/task", json={"task_id": task["id"]})
    response = auth_client.put(f"/api/meetings/{meeting['id']}/task", json={"task_id": None})
    updated = response.json()
    assert updated["task_id"] is None
    assert updated["task_name"] is None


def test_task_meetings_endpoint_exists(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Endpoint Test Task", "due_date": "2026-09-01"
    }).json()
    resp = auth_client.get(f"/api/tasks/{task['id']}/meetings")
    assert resp.status_code == 200
    meetings = resp.json()
    assert isinstance(meetings, list)


def test_task_shows_meetings_when_linked(auth_client):
    meeting = auth_client.post("/api/meetings", json={
        "title": "Show Test Meeting", "meeting_date": "2026-09-01"
    }).json()
    task = auth_client.post("/api/tasks", json={
        "title": "Show Test Task", "due_date": "2026-09-01"
    }).json()

    auth_client.put(f"/api/meetings/{meeting['id']}/task", json={"task_id": task["id"]})

    task_meetings = auth_client.get(f"/api/tasks/{task['id']}/meetings").json()
    assert any(m["id"] == meeting["id"] for m in task_meetings)


def test_meeting_unknown_404s(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "404 Test Task", "due_date": "2026-09-01"
    }).json()
    resp = auth_client.put(f"/api/meetings/9999/task", json={"task_id": task["id"]})
    assert resp.status_code == 404


def test_task_unknown_404s(auth_client):
    resp = auth_client.get("/api/tasks/9999/meetings")
    assert resp.status_code == 404


def test_meetings_list_resolves_task_name(auth_client):
    """Guards against the list-vs-single-fetch divergence bug found in earlier list
    endpoints - the meetings list must resolve task_name too, not just single-meeting GET."""
    meeting = auth_client.post("/api/meetings", json={
        "title": "List Test Meeting", "meeting_date": "2026-09-18"
    }).json()
    task = auth_client.post("/api/tasks", json={
        "title": "List Test Task", "due_date": "2026-09-18"
    }).json()
    auth_client.put(f"/api/meetings/{meeting['id']}/task", json={"task_id": task["id"]})

    listed = auth_client.get("/api/meetings?date=2026-09-18").json()
    found = next(m for m in listed if m["id"] == meeting["id"])
    assert found["task_id"] == task["id"]
    assert found["task_name"] == "List Test Task"
