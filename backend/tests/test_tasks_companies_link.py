def test_task_resolves_company_name(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Resolve Test Task", "due_date": "2026-09-01"
    }).json()
    assert "company_id" in task
    assert "company_name" in task


def test_task_can_be_linked_to_company(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Link Test Task", "due_date": "2026-09-01"
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Link Test Company", "industry": "Tech", "city": "Boston"
    }).json()
    assert task.get("company_id") is None

    response = auth_client.put(f"/api/tasks/{task['id']}/company", json={"company_id": company["id"]})
    updated = response.json()
    assert updated["company_id"] == company["id"]
    assert updated["company_name"] == "Link Test Company"


def test_task_can_be_unlinked_from_company(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Unlink Test Task", "due_date": "2026-09-01"
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Unlink Test Company", "industry": "Finance", "city": "New York"
    }).json()

    auth_client.put(f"/api/tasks/{task['id']}/company", json={"company_id": company["id"]})
    response = auth_client.put(f"/api/tasks/{task['id']}/company", json={"company_id": None})
    updated = response.json()
    assert updated["company_id"] is None
    assert updated["company_name"] is None


def test_company_tasks_endpoint_exists(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Endpoint Test Task", "due_date": "2026-09-01"
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Endpoint Test Company", "industry": "Retail", "city": "Chicago"
    }).json()
    resp = auth_client.get(f"/api/companies/{company['id']}/tasks")
    assert resp.status_code == 200
    tasks = resp.json()
    assert isinstance(tasks, list)


def test_company_shows_tasks_when_linked(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Show Test Task", "due_date": "2026-09-01"
    }).json()
    company = auth_client.post("/api/companies", json={
        "name": "Show Test Company", "industry": "Insurance", "city": "Miami"
    }).json()

    auth_client.put(f"/api/tasks/{task['id']}/company", json={"company_id": company["id"]})

    company_tasks = auth_client.get(f"/api/companies/{company['id']}/tasks").json()
    assert any(t["id"] == task["id"] for t in company_tasks)


def test_task_unknown_404s(auth_client):
    company = auth_client.post("/api/companies", json={
        "name": "404 Test Company", "industry": "Services", "city": "Seattle"
    }).json()
    resp = auth_client.put(f"/api/tasks/9999/company", json={"company_id": company["id"]})
    assert resp.status_code == 404


def test_company_unknown_404s(auth_client):
    resp = auth_client.get("/api/companies/9999/tasks")
    assert resp.status_code == 404
