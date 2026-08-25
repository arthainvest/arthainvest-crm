from datetime import date, timedelta


def test_tasks_crud_and_date_filter(auth_client):
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    resp = auth_client.post("/api/tasks", json={"title": "Call Neha Singh", "due_date": today})
    assert resp.status_code == 200
    task = resp.json()
    assert task["due_date"] == today
    assert task["completed"] is False

    auth_client.post("/api/tasks", json={"title": "Future task", "due_date": tomorrow})

    resp = auth_client.get(f"/api/tasks?date={today}")
    assert resp.status_code == 200
    today_tasks = resp.json()
    assert len(today_tasks) == 1
    assert today_tasks[0]["title"] == "Call Neha Singh"

    resp = auth_client.get(f"/api/tasks?date={tomorrow}")
    assert len(resp.json()) == 1

    resp = auth_client.put(f"/api/tasks/{task['id']}", json={"completed": True})
    assert resp.status_code == 200
    assert resp.json()["completed"] is True

    resp = auth_client.delete(f"/api/tasks/{task['id']}")
    assert resp.status_code == 200
    resp = auth_client.get(f"/api/tasks?date={today}")
    assert len(resp.json()) == 0


def test_task_priority_defaults_and_high_priority_smart_filter(auth_client):
    today = date.today().isoformat()
    far_future = (date.today() + timedelta(days=30)).isoformat()

    normal_task = auth_client.post("/api/tasks", json={"title": "Routine follow-up", "due_date": today}).json()
    assert normal_task["priority"] == "Normal"

    high_today = auth_client.post("/api/tasks", json={
        "title": "Urgent - call Vikram Reddy", "due_date": today, "priority": "High"
    }).json()
    assert high_today["priority"] == "High"

    # A High-priority task due a month out must still show up in the smart filter - it's not
    # scoped to any particular day, unlike the default date-filtered view.
    high_future = auth_client.post("/api/tasks", json={
        "title": "Urgent - renewal chase", "due_date": far_future, "priority": "High"
    }).json()

    resp = auth_client.get("/api/tasks?view=high_priority")
    assert resp.status_code == 200
    titles = {t["title"] for t in resp.json()}
    assert titles == {"Urgent - call Vikram Reddy", "Urgent - renewal chase"}

    # Completing a High-priority task removes it from the smart filter (it's "open" tasks only).
    auth_client.put(f"/api/tasks/{high_today['id']}", json={"completed": True})
    resp = auth_client.get("/api/tasks?view=high_priority")
    titles = {t["title"] for t in resp.json()}
    assert titles == {"Urgent - renewal chase"}

    # Changing priority down to Normal also removes it.
    auth_client.put(f"/api/tasks/{high_future['id']}", json={"priority": "Normal"})
    resp = auth_client.get("/api/tasks?view=high_priority")
    assert resp.json() == []


def test_tasks_default_to_today_when_no_date_param(auth_client):
    today = date.today().isoformat()
    auth_client.post("/api/tasks", json={"title": "Undated-filter task", "due_date": today})

    resp = auth_client.get("/api/tasks")
    assert resp.status_code == 200
    assert any(t["title"] == "Undated-filter task" for t in resp.json())


def test_meetings_crud_links_lead_and_contact(auth_client):
    today = date.today().isoformat()

    resp = auth_client.post("/api/meetings", json={
        "title": "Loan discussion", "meeting_date": today, "meeting_time": "15:00",
        "lead_id": 1, "location": "Office"
    })
    assert resp.status_code == 200
    meeting = resp.json()
    assert meeting["status"] == "Scheduled"
    assert meeting["lead_name"] == "Neha Singh"

    resp = auth_client.get(f"/api/meetings?date={today}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = auth_client.put(f"/api/meetings/{meeting['id']}", json={"status": "Conducted"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "Conducted"

    resp = auth_client.delete(f"/api/meetings/{meeting['id']}")
    assert resp.status_code == 200
    resp = auth_client.get(f"/api/meetings?date={today}")
    assert len(resp.json()) == 0


def test_delete_nonexistent_task_and_meeting_404(auth_client):
    resp = auth_client.delete("/api/tasks/9999")
    assert resp.status_code == 404
    resp = auth_client.delete("/api/meetings/9999")
    assert resp.status_code == 404
