def test_task_resolves_contact_name(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Test Task", "due_date": "2026-09-01", "priority": "High"
    }).json()
    assert "contact_id" in task
    assert "contact_name" in task


def test_task_can_be_linked_to_contact(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Link Test", "due_date": "2026-09-05", "priority": "Normal"
    }).json()
    contact = auth_client.post("/api/contacts", json={
        "name": "Task Link Contact", "email": "tasklink@test.com", "phone": "5555555555"
    }).json()
    assert task.get("contact_id") is None

    response = auth_client.put(f"/api/tasks/{task['id']}/contact", json={"contact_id": contact["id"]})
    updated = response.json()
    assert updated["contact_id"] == contact["id"]
    assert updated["contact_name"] == contact["name"]


def test_task_can_be_unlinked_from_contact(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Unlink Test", "due_date": "2026-09-10", "priority": "Low"
    }).json()
    contact = auth_client.post("/api/contacts", json={
        "name": "Task Unlink Contact", "email": "taskunlink@test.com", "phone": "4444444444"
    }).json()

    auth_client.put(f"/api/tasks/{task['id']}/contact", json={"contact_id": contact["id"]})
    response = auth_client.put(f"/api/tasks/{task['id']}/contact", json={"contact_id": None})
    updated = response.json()
    assert updated["contact_id"] is None
    assert updated["contact_name"] is None


def test_contact_tasks_endpoint_exists(auth_client):
    contact = auth_client.post("/api/contacts", json={
        "name": "Task Endpoint Contact", "email": "endpoint@test.com", "phone": "3333333333"
    }).json()
    resp = auth_client.get(f"/api/contacts/{contact['id']}/tasks")
    assert resp.status_code == 200
    tasks = resp.json()
    assert isinstance(tasks, list)


def test_contact_shows_tasks_when_linked(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Show Test Task", "due_date": "2026-09-15", "priority": "High"
    }).json()
    contact = auth_client.post("/api/contacts", json={
        "name": "Task Show Contact", "email": "taskshow@test.com", "phone": "2222222222"
    }).json()

    auth_client.put(f"/api/tasks/{task['id']}/contact", json={"contact_id": contact["id"]})

    contact_tasks = auth_client.get(f"/api/contacts/{contact['id']}/tasks").json()
    assert any(t["id"] == task["id"] for t in contact_tasks)


def test_task_unknown_404s(auth_client):
    resp = auth_client.put("/api/tasks/9999/contact", json={"contact_id": 1})
    assert resp.status_code == 404


def test_contact_unknown_404s(auth_client):
    resp = auth_client.get("/api/contacts/9999/tasks")
    assert resp.status_code == 404
