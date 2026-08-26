from datetime import date


def _first_lead(auth_client):
    return auth_client.get("/api/leads").json()[0]


def _first_contact(auth_client):
    return auth_client.get("/api/contacts").json()[0]


def test_create_task_linked_to_lead(auth_client):
    today = date.today().isoformat()
    lead = _first_lead(auth_client)

    resp = auth_client.post("/api/tasks", json={
        "title": "Chase KYC docs", "due_date": today, "lead_id": lead["id"]
    })
    assert resp.status_code == 200
    task = resp.json()
    assert task["lead_id"] == lead["id"]
    assert task["lead_name"] == lead["name"]
    assert task["contact_id"] is None

    listed = auth_client.get(f"/api/tasks?date={today}").json()
    fetched = next(t for t in listed if t["id"] == task["id"])
    assert fetched["lead_name"] == lead["name"]


def test_create_task_linked_to_contact(auth_client):
    today = date.today().isoformat()
    contact = _first_contact(auth_client)

    resp = auth_client.post("/api/tasks", json={
        "title": "Renewal reminder call", "due_date": today, "contact_id": contact["id"]
    })
    assert resp.status_code == 200
    task = resp.json()
    assert task["contact_id"] == contact["id"]
    assert task["contact_name"] == contact["name"]
    assert task["lead_id"] is None


def test_high_priority_filter_includes_lead_link(auth_client):
    today = date.today().isoformat()
    lead = _first_lead(auth_client)

    auth_client.post("/api/tasks", json={
        "title": "Urgent - call back", "due_date": today, "priority": "High", "lead_id": lead["id"]
    })

    resp = auth_client.get("/api/tasks?view=high_priority")
    assert resp.status_code == 200
    task = next(t for t in resp.json() if t["title"] == "Urgent - call back")
    assert task["lead_name"] == lead["name"]


def test_link_task_to_lead_via_update(auth_client):
    today = date.today().isoformat()
    lead = _first_lead(auth_client)
    task = auth_client.post("/api/tasks", json={"title": "Plain task", "due_date": today}).json()
    assert task["lead_id"] is None

    resp = auth_client.put(f"/api/tasks/{task['id']}", json={"lead_id": lead["id"]})
    assert resp.status_code == 200
    assert resp.json()["lead_id"] == lead["id"]
    assert resp.json()["lead_name"] == lead["name"]


def test_task_without_link_has_null_lead_and_contact(auth_client):
    today = date.today().isoformat()
    task = auth_client.post("/api/tasks", json={"title": "No link task", "due_date": today}).json()
    assert task["lead_id"] is None
    assert task["lead_name"] is None
    assert task["contact_id"] is None
    assert task["contact_name"] is None
