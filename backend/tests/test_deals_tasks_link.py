def test_deal_resolves_task_name(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    assert "task_id" in deal
    assert "task_name" in deal


def test_deal_can_be_linked_to_task(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    task = auth_client.post("/api/tasks", json={
        "title": "Deal Link Task", "due_date": "2026-08-26", "priority": "High"
    }).json()
    assert deal.get("task_id") is None

    response = auth_client.put(f"/api/deals/{deal['id']}/task", json={"task_id": task["id"]})
    updated = response.json()
    assert updated["task_id"] == task["id"]
    assert updated["task_name"] == task["title"]


def test_deal_can_be_unlinked_from_task(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    task = auth_client.post("/api/tasks", json={
        "title": "Deal Unlink Task", "due_date": "2026-08-26", "priority": "Normal"
    }).json()

    auth_client.put(f"/api/deals/{deal['id']}/task", json={"task_id": task["id"]})
    response = auth_client.put(f"/api/deals/{deal['id']}/task", json={"task_id": None})
    updated = response.json()
    assert updated["task_id"] is None
    assert updated["task_name"] is None


def test_task_deals_endpoint_exists(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Deal Endpoint Task", "due_date": "2026-08-26", "priority": "High"
    }).json()
    resp = auth_client.get(f"/api/tasks/{task['id']}/deals")
    assert resp.status_code == 200
    deals = resp.json()
    assert isinstance(deals, list)


def test_task_shows_deals_when_linked(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    deal = auth_client.post("/api/deals", json={
        "lead_id": lead["id"], "deal_value": 100000, "probability": 0.8
    }).json()
    task = auth_client.post("/api/tasks", json={
        "title": "Deal Show Task", "due_date": "2026-08-26", "priority": "High"
    }).json()

    auth_client.put(f"/api/deals/{deal['id']}/task", json={"task_id": task["id"]})

    task_deals = auth_client.get(f"/api/tasks/{task['id']}/deals").json()
    assert any(d["id"] == deal["id"] for d in task_deals)


def test_deal_unknown_404s(auth_client):
    task = auth_client.post("/api/tasks", json={
        "title": "Deal 404 Task", "due_date": "2026-08-26", "priority": "High"
    }).json()
    resp = auth_client.put(f"/api/deals/9999/task", json={"task_id": task["id"]})
    assert resp.status_code == 404


def test_task_unknown_404s(auth_client):
    resp = auth_client.get("/api/tasks/9999/deals")
    assert resp.status_code == 404
