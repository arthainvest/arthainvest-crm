def test_task_resolves_call_name(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Test Task", "due_date": "2026-08-26", "priority": "High"
    }).json()
    assert "call_id" in task
    assert "call_name" in task


def test_task_can_be_linked_to_call(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Link Test Task", "due_date": "2026-08-26", "priority": "High"
    }).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Task Link Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 120, "outcome": "Qualified"
    }).json()
    assert task.get("call_id") is None

    response = auth_client.put(f"/api/tasks/{task['id']}/call", json={"call_id": call["id"]})
    updated = response.json()
    assert updated["call_id"] == call["id"]
    assert updated["call_name"] == call["name"]


def test_task_can_be_unlinked_from_call(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Unlink Test Task", "due_date": "2026-08-26", "priority": "Normal"
    }).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Task Unlink Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 60, "outcome": "Interested"
    }).json()

    auth_client.put(f"/api/tasks/{task['id']}/call", json={"call_id": call["id"]})
    response = auth_client.put(f"/api/tasks/{task['id']}/call", json={"call_id": None})
    updated = response.json()
    assert updated["call_id"] is None
    assert updated["call_name"] is None


def test_call_tasks_endpoint_exists(auth_client):
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Task Endpoint Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 120, "outcome": "Qualified"
    }).json()
    resp = auth_client.get(f"/api/calls/{call['id']}/tasks")
    assert resp.status_code == 200
    tasks = resp.json()
    assert isinstance(tasks, list)


def test_call_shows_tasks_when_linked(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Show Test Task", "due_date": "2026-08-26", "priority": "High"
    }).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Task Show Call", "lead_id": call_lead["id"], "type": "Inbound",
        "duration_seconds": 180, "outcome": "Not Interested"
    }).json()

    auth_client.put(f"/api/tasks/{task['id']}/call", json={"call_id": call["id"]})

    call_tasks = auth_client.get(f"/api/calls/{call['id']}/tasks").json()
    assert any(t["id"] == task["id"] for t in call_tasks)


def test_task_unknown_404s(auth_client):
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Task 404 Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 60, "outcome": "Interested"
    }).json()
    resp = auth_client.put(f"/api/tasks/9999/call", json={"call_id": call["id"]})
    assert resp.status_code == 404


def test_call_unknown_404s(auth_client):
    resp = auth_client.get("/api/calls/9999/tasks")
    assert resp.status_code == 404


def test_task_list_resolves_call_name(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "List Test Task", "due_date": "2026-08-26", "priority": "High"
    }).json()
    call_lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Task List Call", "lead_id": call_lead["id"], "type": "Outbound",
        "duration_seconds": 120, "outcome": "Qualified"
    }).json()
    auth_client.put(f"/api/tasks/{task['id']}/call", json={"call_id": call["id"]})

    tasks = auth_client.get("/api/tasks?date=2026-08-26").json()
    listed = next(t for t in tasks if t["id"] == task["id"])
    assert listed["call_id"] == call["id"]
    assert listed["call_name"] == call["name"]
