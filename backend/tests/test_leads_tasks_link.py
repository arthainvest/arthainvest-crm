def test_lead_resolves_task_name(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Test Lead", "company": "Test Co", "email": "lead@test.com"
    }).json()
    assert "task_id" in lead
    assert "task_name" in lead


def test_lead_can_be_linked_to_task(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Link Test Lead", "company": "Test Co"
    }).json()
    task = auth_client.post("/api/tasks", json={
        "title": "Link Test Task", "due_date": "2026-08-26", "priority": "High"
    }).json()
    assert lead.get("task_id") is None

    response = auth_client.put(f"/api/leads/{lead['id']}/task", json={"task_id": task["id"]})
    updated = response.json()
    assert updated["task_id"] == task["id"]
    assert updated["task_name"] == task["title"]


def test_lead_can_be_unlinked_from_task(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Unlink Test Lead", "company": "Test Co"
    }).json()
    task = auth_client.post("/api/tasks", json={
        "title": "Unlink Test Task", "due_date": "2026-08-26", "priority": "Normal"
    }).json()

    auth_client.put(f"/api/leads/{lead['id']}/task", json={"task_id": task["id"]})
    response = auth_client.put(f"/api/leads/{lead['id']}/task", json={"task_id": None})
    updated = response.json()
    assert updated["task_id"] is None
    assert updated["task_name"] is None


def test_task_leads_endpoint_exists(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Endpoint Test Task", "due_date": "2026-08-26", "priority": "High"
    }).json()
    resp = auth_client.get(f"/api/tasks/{task['id']}/leads")
    assert resp.status_code == 200
    leads = resp.json()
    assert isinstance(leads, list)


def test_task_shows_leads_when_linked(auth_client):
    lead = auth_client.post("/api/leads", json={
        "name": "Show Test Lead", "company": "Test Co"
    }).json()
    task = auth_client.post("/api/tasks", json={
        "title": "Show Test Task", "due_date": "2026-08-26", "priority": "High"
    }).json()

    auth_client.put(f"/api/leads/{lead['id']}/task", json={"task_id": task["id"]})

    task_leads = auth_client.get(f"/api/tasks/{task['id']}/leads").json()
    assert any(l["id"] == lead["id"] for l in task_leads)


def test_lead_unknown_404s(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "404 Test Task", "due_date": "2026-08-26", "priority": "High"
    }).json()
    resp = auth_client.put(f"/api/leads/9999/task", json={"task_id": task["id"]})
    assert resp.status_code == 404


def test_task_unknown_404s(auth_client):
    resp = auth_client.get("/api/tasks/9999/leads")
    assert resp.status_code == 404
