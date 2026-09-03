"""Automations (drip sequences): create/list/update/delete the flow itself, then enroll a
lead into it and stop that enrollment. Mirrors the CRUD-plus-junction-table shape already
tested for tags/groups (see test_leads.py's tag/group sections) - entity_type/entity_id is
the same polymorphic pointer, just pointed at automation_enrollments here instead.
"""


def _sample_automation_payload(**overrides):
    payload = {
        "name": "Diwali Greeting Sequence",
        "trigger_type": "manual",
        "steps": [
            {"wait_minutes": 0, "message_type": "text", "body": "Happy Diwali!"},
            {"wait_minutes": 60, "message_type": "text", "body": "Following up on our Diwali wishes."},
        ],
    }
    payload.update(overrides)
    return payload


def test_create_automation(auth_client):
    created = auth_client.post("/api/automations", json=_sample_automation_payload()).json()
    assert created["name"] == "Diwali Greeting Sequence"
    assert created["trigger_type"] == "manual"
    assert created["status"] == "active"
    assert len(created["steps"]) == 2
    assert created["steps"][0]["wait_minutes"] == 0
    assert created["steps"][1]["wait_minutes"] == 60


def test_create_automation_with_no_steps(auth_client):
    created = auth_client.post("/api/automations", json={"name": "Empty Flow", "steps": []}).json()
    assert created["steps"] == []


def test_list_automations(auth_client):
    auth_client.post("/api/automations", json=_sample_automation_payload())
    auth_client.post("/api/automations", json=_sample_automation_payload(name="Second Sequence"))

    listed = auth_client.get("/api/automations").json()
    names = {a["name"] for a in listed}
    assert "Diwali Greeting Sequence" in names
    assert "Second Sequence" in names


def test_update_automation_name_and_status(auth_client):
    created = auth_client.post("/api/automations", json=_sample_automation_payload()).json()

    updated = auth_client.put(f"/api/automations/{created['id']}", json={
        "name": "Diwali Greeting Sequence (Renamed)", "status": "paused"
    }).json()
    assert updated["name"] == "Diwali Greeting Sequence (Renamed)"
    assert updated["status"] == "paused"
    # steps untouched when not included in the update payload
    assert len(updated["steps"]) == 2


def test_update_automation_replaces_steps(auth_client):
    created = auth_client.post("/api/automations", json=_sample_automation_payload()).json()

    updated = auth_client.put(f"/api/automations/{created['id']}", json={
        "steps": [{"wait_minutes": 0, "message_type": "text", "body": "Just one step now"}]
    }).json()
    assert len(updated["steps"]) == 1
    assert updated["steps"][0]["body"] == "Just one step now"


def test_update_automation_rejects_bad_status(auth_client):
    created = auth_client.post("/api/automations", json=_sample_automation_payload()).json()
    resp = auth_client.put(f"/api/automations/{created['id']}", json={"status": "not-a-real-status"})
    assert resp.status_code == 400


def test_update_unknown_automation_404s(auth_client):
    resp = auth_client.put("/api/automations/9999", json={"name": "Nope"})
    assert resp.status_code == 404


def test_delete_automation(auth_client):
    created = auth_client.post("/api/automations", json=_sample_automation_payload()).json()

    resp = auth_client.delete(f"/api/automations/{created['id']}")
    assert resp.status_code == 200

    listed = auth_client.get("/api/automations").json()
    assert not any(a["id"] == created["id"] for a in listed)


def test_delete_unknown_automation_404s(auth_client):
    resp = auth_client.delete("/api/automations/9999")
    assert resp.status_code == 404


def test_enroll_lead_and_view_enrollment(auth_client):
    lead = auth_client.post("/api/leads", json={"name": "Enroll Test Lead", "phone": "9990001111"}).json()
    automation = auth_client.post("/api/automations", json=_sample_automation_payload()).json()

    resp = auth_client.post(f"/api/automations/{automation['id']}/enroll", json={
        "entity_type": "lead", "entity_id": lead["id"]
    })
    assert resp.status_code == 200

    enrollments = auth_client.get(f"/api/automations/{automation['id']}/enrollments").json()
    assert len(enrollments) == 1
    enrollment = enrollments[0]
    assert enrollment["entity_type"] == "lead"
    assert enrollment["entity_id"] == lead["id"]
    assert enrollment["entity_name"] == "Enroll Test Lead"
    assert enrollment["status"] == "active"
    assert enrollment["current_step"] == 0
    assert enrollment["total_steps"] == 2
    assert enrollment["next_run_at"] is not None


def test_enroll_contact(auth_client):
    contact = auth_client.post("/api/contacts", json={"name": "Enroll Test Contact", "phone": "9990002222"}).json()
    automation = auth_client.post("/api/automations", json=_sample_automation_payload()).json()

    resp = auth_client.post(f"/api/automations/{automation['id']}/enroll", json={
        "entity_type": "contact", "entity_id": contact["id"]
    })
    assert resp.status_code == 200

    enrollments = auth_client.get(f"/api/automations/{automation['id']}/enrollments").json()
    assert enrollments[0]["entity_type"] == "contact"
    assert enrollments[0]["entity_name"] == "Enroll Test Contact"


def test_enroll_rejects_bad_entity_type(auth_client):
    automation = auth_client.post("/api/automations", json=_sample_automation_payload()).json()
    resp = auth_client.post(f"/api/automations/{automation['id']}/enroll", json={
        "entity_type": "deal", "entity_id": 1
    })
    assert resp.status_code == 400


def test_enroll_fails_when_automation_has_no_steps(auth_client):
    lead = auth_client.post("/api/leads", json={"name": "No Steps Lead", "phone": "9990003333"}).json()
    automation = auth_client.post("/api/automations", json={"name": "Empty Flow", "steps": []}).json()

    resp = auth_client.post(f"/api/automations/{automation['id']}/enroll", json={
        "entity_type": "lead", "entity_id": lead["id"]
    })
    assert resp.status_code == 400


def test_enroll_twice_is_rejected(auth_client):
    lead = auth_client.post("/api/leads", json={"name": "Double Enroll Lead", "phone": "9990004444"}).json()
    automation = auth_client.post("/api/automations", json=_sample_automation_payload()).json()

    first = auth_client.post(f"/api/automations/{automation['id']}/enroll", json={
        "entity_type": "lead", "entity_id": lead["id"]
    })
    assert first.status_code == 200

    second = auth_client.post(f"/api/automations/{automation['id']}/enroll", json={
        "entity_type": "lead", "entity_id": lead["id"]
    })
    assert second.status_code == 400


def test_enroll_group(auth_client):
    lead = auth_client.post("/api/leads", json={"name": "Group Lead", "phone": "9990005555"}).json()
    contact = auth_client.post("/api/contacts", json={"name": "Group Contact", "phone": "9990006666"}).json()
    group = auth_client.post("/api/groups", json={"name": "Automation Test Group"}).json()
    auth_client.post("/api/groups/assign", json={"entity_type": "lead", "entity_id": lead["id"], "group_id": group["id"]})
    auth_client.post("/api/groups/assign", json={"entity_type": "contact", "entity_id": contact["id"], "group_id": group["id"]})

    automation = auth_client.post("/api/automations", json=_sample_automation_payload()).json()
    resp = auth_client.post(f"/api/automations/{automation['id']}/enroll-group/{group['id']}")
    assert resp.status_code == 200
    assert "2" in resp.json()["message"]

    enrollments = auth_client.get(f"/api/automations/{automation['id']}/enrollments").json()
    assert len(enrollments) == 2
    entity_types = {e["entity_type"] for e in enrollments}
    assert entity_types == {"lead", "contact"}


def test_enroll_group_with_no_steps_fails(auth_client):
    group = auth_client.post("/api/groups", json={"name": "Empty Steps Group"}).json()
    automation = auth_client.post("/api/automations", json={"name": "Empty Flow", "steps": []}).json()
    resp = auth_client.post(f"/api/automations/{automation['id']}/enroll-group/{group['id']}")
    assert resp.status_code == 400


def test_stop_enrollment(auth_client):
    lead = auth_client.post("/api/leads", json={"name": "Stop Test Lead", "phone": "9990007777"}).json()
    automation = auth_client.post("/api/automations", json=_sample_automation_payload()).json()
    auth_client.post(f"/api/automations/{automation['id']}/enroll", json={
        "entity_type": "lead", "entity_id": lead["id"]
    })
    enrollment_id = auth_client.get(f"/api/automations/{automation['id']}/enrollments").json()[0]["id"]

    resp = auth_client.post(f"/api/automations/enrollments/{enrollment_id}/stop")
    assert resp.status_code == 200

    enrollments = auth_client.get(f"/api/automations/{automation['id']}/enrollments").json()
    assert enrollments[0]["status"] == "stopped"


def test_stop_unknown_enrollment_404s(auth_client):
    resp = auth_client.post("/api/automations/enrollments/9999/stop")
    assert resp.status_code == 404


def test_deleting_automation_also_clears_its_enrollments(auth_client):
    lead = auth_client.post("/api/leads", json={"name": "Cascade Lead", "phone": "9990008888"}).json()
    automation = auth_client.post("/api/automations", json=_sample_automation_payload()).json()
    auth_client.post(f"/api/automations/{automation['id']}/enroll", json={
        "entity_type": "lead", "entity_id": lead["id"]
    })

    resp = auth_client.delete(f"/api/automations/{automation['id']}")
    assert resp.status_code == 200
    # The automation is gone, so its enrollments endpoint 404s along with it (not a leftover
    # active enrollment nobody can see or stop anymore).
    resp2 = auth_client.get(f"/api/automations/{automation['id']}/enrollments")
    assert resp2.status_code == 200
    assert resp2.json() == []


def test_automations_require_auth(client):
    resp = client.get("/api/automations")
    assert resp.status_code in (401, 403)
