from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import automations_scheduler


def _create_automation_with_steps(auth_client, steps):
    return auth_client.post("/api/automations", json={
        "name": "Test Sequence", "trigger_type": "manual", "steps": steps
    }).json()


def _due_now(cursor, automation_id, entity_type, entity_id):
    """Force an enrollment's next_run_at into the past so the scheduler treats it as due -
    enroll() always schedules relative to 'now', which a test can't otherwise backdate."""
    cursor.execute(
        "UPDATE automation_enrollments SET next_run_at = ? WHERE automation_id = ? AND entity_type = ? AND entity_id = ?",
        ((datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)).isoformat(), automation_id, entity_type, entity_id)
    )


def _fake_meta_response():
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"messages": [{"id": "wamid.TEST123"}]}
    return resp


def test_scheduler_does_nothing_without_whatsapp_credentials(auth_client):
    """conftest strips WHATSAPP_TOKEN/WHATSAPP_PHONE_ID for every test - the scheduler must
    no-op rather than firing a request at Meta's API with an empty token."""
    lead = auth_client.post("/api/leads", json={"name": "No Creds Lead", "phone": "919876500010"}).json()
    automation = _create_automation_with_steps(auth_client, [{"wait_minutes": 0, "message_type": "text", "body": "Hi"}])
    auth_client.post(f"/api/automations/{automation['id']}/enroll", json={"entity_type": "lead", "entity_id": lead["id"]})

    with patch("requests.post") as mock_post:
        automations_scheduler._process_due_enrollments()
        mock_post.assert_not_called()


def test_scheduler_sends_due_step_and_advances_to_next(auth_client, monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", "fake-token")
    monkeypatch.setenv("WHATSAPP_PHONE_ID", "123456")

    lead = auth_client.post("/api/leads", json={"name": "Two Step Lead", "phone": "919876500011"}).json()
    automation = _create_automation_with_steps(auth_client, [
        {"wait_minutes": 0, "message_type": "text", "body": "Step one"},
        {"wait_minutes": 30, "message_type": "text", "body": "Step two"},
    ])
    auth_client.post(f"/api/automations/{automation['id']}/enroll", json={"entity_type": "lead", "entity_id": lead["id"]})

    import database_sqlite
    with database_sqlite.get_db() as conn:
        _due_now(conn.cursor(), automation["id"], "lead", lead["id"])
        conn.commit()

    with patch("requests.post", return_value=_fake_meta_response()) as mock_post:
        automations_scheduler._process_due_enrollments()
        assert mock_post.called
        sent_body = mock_post.call_args.kwargs["json"]
        assert sent_body["text"]["body"] == "Step one"

    enrollments = auth_client.get(f"/api/automations/{automation['id']}/enrollments").json()
    enrollment = enrollments[0]
    assert enrollment["current_step"] == 1
    assert enrollment["status"] == "active"
    # Next step waits 30 minutes - next_run_at should be roughly 30 minutes out, not immediate.
    next_run = datetime.fromisoformat(enrollment["next_run_at"])
    assert next_run > datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=25)


def test_scheduler_completes_enrollment_after_last_step(auth_client, monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", "fake-token")
    monkeypatch.setenv("WHATSAPP_PHONE_ID", "123456")

    lead = auth_client.post("/api/leads", json={"name": "One Step Lead", "phone": "919876500012"}).json()
    automation = _create_automation_with_steps(auth_client, [{"wait_minutes": 0, "message_type": "text", "body": "Only step"}])
    auth_client.post(f"/api/automations/{automation['id']}/enroll", json={"entity_type": "lead", "entity_id": lead["id"]})

    import database_sqlite
    with database_sqlite.get_db() as conn:
        _due_now(conn.cursor(), automation["id"], "lead", lead["id"])
        conn.commit()

    with patch("requests.post", return_value=_fake_meta_response()):
        automations_scheduler._process_due_enrollments()

    enrollment = auth_client.get(f"/api/automations/{automation['id']}/enrollments").json()[0]
    assert enrollment["status"] == "completed"


def test_scheduler_stops_enrollment_when_entity_has_no_phone(auth_client, monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", "fake-token")
    monkeypatch.setenv("WHATSAPP_PHONE_ID", "123456")

    lead = auth_client.post("/api/leads", json={"name": "No Phone Lead"}).json()
    automation = _create_automation_with_steps(auth_client, [{"wait_minutes": 0, "message_type": "text", "body": "Hi"}])
    auth_client.post(f"/api/automations/{automation['id']}/enroll", json={"entity_type": "lead", "entity_id": lead["id"]})

    import database_sqlite
    with database_sqlite.get_db() as conn:
        _due_now(conn.cursor(), automation["id"], "lead", lead["id"])
        conn.commit()

    with patch("requests.post") as mock_post:
        automations_scheduler._process_due_enrollments()
        mock_post.assert_not_called()

    enrollment = auth_client.get(f"/api/automations/{automation['id']}/enrollments").json()[0]
    assert enrollment["status"] == "stopped"


def test_scheduler_skips_enrollments_not_yet_due(auth_client, monkeypatch):
    """enroll() schedules the first step relative to 'now' - a fresh enrollment with any
    wait_minutes > 0 isn't due yet, and the scheduler must leave it alone."""
    monkeypatch.setenv("WHATSAPP_TOKEN", "fake-token")
    monkeypatch.setenv("WHATSAPP_PHONE_ID", "123456")

    lead = auth_client.post("/api/leads", json={"name": "Future Lead", "phone": "919876500013"}).json()
    automation = _create_automation_with_steps(auth_client, [{"wait_minutes": 60, "message_type": "text", "body": "Not yet"}])
    auth_client.post(f"/api/automations/{automation['id']}/enroll", json={"entity_type": "lead", "entity_id": lead["id"]})

    with patch("requests.post") as mock_post:
        automations_scheduler._process_due_enrollments()
        mock_post.assert_not_called()

    enrollment = auth_client.get(f"/api/automations/{automation['id']}/enrollments").json()[0]
    assert enrollment["current_step"] == 0
    assert enrollment["status"] == "active"
