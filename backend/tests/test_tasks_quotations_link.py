def test_task_resolves_quotation_title(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Test Task", "due_date": "2026-08-26", "priority": "High"
    }).json()
    assert "quotation_id" in task
    assert "quotation_title" in task


def test_task_can_be_linked_to_quotation(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Link Test Task", "due_date": "2026-08-26", "priority": "High"
    }).json()
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "Test Quotation", "amount": 50000, "status": "Draft"
    }).json()
    assert task.get("quotation_id") is None

    response = auth_client.put(f"/api/tasks/{task['id']}/quotation", json={"quotation_id": quotation["id"]})
    updated = response.json()
    assert updated["quotation_id"] == quotation["id"]
    assert updated["quotation_title"] == quotation["title"]


def test_task_can_be_unlinked_from_quotation(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Unlink Test Task", "due_date": "2026-08-26", "priority": "Normal"
    }).json()
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "Unlink Test Quotation", "amount": 50000, "status": "Draft"
    }).json()

    auth_client.put(f"/api/tasks/{task['id']}/quotation", json={"quotation_id": quotation["id"]})
    response = auth_client.put(f"/api/tasks/{task['id']}/quotation", json={"quotation_id": None})
    updated = response.json()
    assert updated["quotation_id"] is None
    assert updated["quotation_title"] is None


def test_quotation_tasks_endpoint_exists(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "Endpoint Test Quotation", "amount": 50000, "status": "Draft"
    }).json()
    resp = auth_client.get(f"/api/quotations/{quotation['id']}/tasks")
    assert resp.status_code == 200
    tasks = resp.json()
    assert isinstance(tasks, list)


def test_quotation_shows_tasks_when_linked(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Show Test Task", "due_date": "2026-08-26", "priority": "High"
    }).json()
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "Show Test Quotation", "amount": 50000, "status": "Draft"
    }).json()

    auth_client.put(f"/api/tasks/{task['id']}/quotation", json={"quotation_id": quotation["id"]})

    quotation_tasks = auth_client.get(f"/api/quotations/{quotation['id']}/tasks").json()
    assert any(t["id"] == task["id"] for t in quotation_tasks)


def test_task_unknown_404s(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "404 Test Quotation", "amount": 50000, "status": "Draft"
    }).json()
    resp = auth_client.put(f"/api/tasks/9999/quotation", json={"quotation_id": quotation["id"]})
    assert resp.status_code == 404


def test_quotation_unknown_404s(auth_client):
    resp = auth_client.get("/api/quotations/9999/tasks")
    assert resp.status_code == 404


def test_task_list_resolves_quotation_title(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "List Test Task", "due_date": "2026-08-26", "priority": "High"
    }).json()
    contact = auth_client.get("/api/contacts").json()[0]
    quotation = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"], "title": "List Test Quotation", "amount": 50000, "status": "Draft"
    }).json()
    auth_client.put(f"/api/tasks/{task['id']}/quotation", json={"quotation_id": quotation["id"]})

    tasks = auth_client.get("/api/tasks?date=2026-08-26").json()
    listed = next(t for t in tasks if t["id"] == task["id"])
    assert listed["quotation_id"] == quotation["id"]
    assert listed["quotation_title"] == quotation["title"]
