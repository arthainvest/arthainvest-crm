def test_convert_lead_creates_contact_with_carried_over_fields(auth_client):
    lead = auth_client.get("/api/leads").json()[0]

    resp = auth_client.post(f"/api/leads/{lead['id']}/convert")
    assert resp.status_code == 200
    contact = resp.json()
    assert contact["name"] == lead["name"]
    assert contact["company"] == lead["company"]
    assert contact["email"] == lead["email"]
    assert contact["phone"] == lead["phone"]
    assert contact["status"] == "Active"
    assert contact["converted_from_lead_id"] == lead["id"]
    assert contact["converted_from_lead_name"] == lead["name"]


def test_convert_lead_carries_over_assigned_team_member(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    rajesh = next(m for m in auth_client.get("/api/team").json() if m["name"] == "Rajesh Kumar")
    auth_client.put(f"/api/leads/{lead['id']}/assign", json={"team_member_id": rajesh["id"]})

    resp = auth_client.post(f"/api/leads/{lead['id']}/convert")
    assert resp.status_code == 200
    contact = resp.json()
    assert contact["assigned_team_member_id"] == rajesh["id"]
    assert contact["assigned_team_member_name"] == "Rajesh Kumar"


def test_convert_lead_marks_lead_as_converted(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    contact = auth_client.post(f"/api/leads/{lead['id']}/convert").json()

    updated_lead = next(l for l in auth_client.get("/api/leads").json() if l["id"] == lead["id"])
    assert updated_lead["converted_contact_id"] == contact["id"]
    assert updated_lead["converted_contact_name"] == contact["name"]


def test_converting_an_already_converted_lead_400s(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    auth_client.post(f"/api/leads/{lead['id']}/convert")

    resp = auth_client.post(f"/api/leads/{lead['id']}/convert")
    assert resp.status_code == 400


def test_convert_unknown_lead_404s(auth_client):
    resp = auth_client.post("/api/leads/9999/convert")
    assert resp.status_code == 404


def test_convert_lead_backfills_activity_onto_new_contact_without_clearing_lead_id(auth_client):
    """The whole point: a lead's prior calls/tasks must show up on the new Contact's own
    Activity Timeline, without erasing the original lead's own history either."""
    lead = auth_client.get("/api/leads").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": lead["name"], "phone": lead.get("phone"), "lead_id": lead["id"]
    }).json()
    task = auth_client.post("/api/tasks", json={
        "title": "Follow up before conversion", "due_date": "2026-09-01", "lead_id": lead["id"]
    }).json()

    contact = auth_client.post(f"/api/leads/{lead['id']}/convert").json()

    updated_call = next(c for c in auth_client.get("/api/calls").json() if c["id"] == call["id"])
    assert updated_call["lead_id"] == lead["id"]
    assert updated_call["contact_id"] == contact["id"]

    all_tasks_for_lead = auth_client.get(f"/api/activities?lead_id={lead['id']}").json()
    task_activity = next(a for a in all_tasks_for_lead if a["id"] == f"task-{task['id']}")
    assert task_activity["lead_id"] == lead["id"]
    assert task_activity["contact_id"] == contact["id"]

    contact_activities = auth_client.get(f"/api/activities?contact_id={contact['id']}").json()
    assert any(a["id"] == f"call-{call['id']}" for a in contact_activities)
    assert any(a["id"] == f"task-{task['id']}" for a in contact_activities)

    lead_activities = auth_client.get(f"/api/activities?lead_id={lead['id']}").json()
    assert any(a["id"] == f"call-{call['id']}" for a in lead_activities)
    assert any(a["id"] == f"task-{task['id']}" for a in lead_activities)


def test_convert_lead_does_not_backfill_activity_already_linked_to_another_contact(auth_client):
    """A call already linked to a different contact must not be silently re-pointed."""
    lead = auth_client.get("/api/leads").json()[0]
    other_contact = auth_client.get("/api/contacts").json()[0]
    call = auth_client.post("/api/calls", json={
        "name": "Dual context call", "lead_id": lead["id"], "contact_id": other_contact["id"]
    }).json()

    new_contact = auth_client.post(f"/api/leads/{lead['id']}/convert").json()

    updated_call = next(c for c in auth_client.get("/api/calls").json() if c["id"] == call["id"])
    assert updated_call["contact_id"] == other_contact["id"]
    assert updated_call["contact_id"] != new_contact["id"]
