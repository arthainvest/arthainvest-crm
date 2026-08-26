from unittest.mock import patch, MagicMock


def _first_lead(auth_client):
    return auth_client.get("/api/leads").json()[0]


def _first_contact(auth_client):
    return auth_client.get("/api/contacts").json()[0]


def test_email_send_linked_to_lead_shows_in_communication_log(auth_client, monkeypatch):
    lead = _first_lead(auth_client)
    monkeypatch.setenv("SMTP_HOST", "smtp.fake.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@fake.com")
    monkeypatch.setenv("SMTP_PASSWORD", "fakepass")

    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.return_value = MagicMock()
        auth_client.post("/api/email/send", json={
            "to": "client@example.com", "subject": "Hi", "body": "Body", "lead_id": lead["id"]
        })

    entries = auth_client.get("/api/communication-log").json()
    assert len(entries) == 1
    assert entries[0]["lead_id"] == lead["id"]
    assert entries[0]["lead_name"] == lead["name"]
    assert entries[0]["contact_id"] is None


def test_whatsapp_send_linked_to_contact(auth_client):
    contact = _first_contact(auth_client)
    # WHATSAPP_TOKEN/PHONE_ID unset - returns configured=False, nothing logged (matches the
    # existing graceful-degradation contract), so just confirm the request itself is accepted
    # and doesn't error when contact_id is present.
    resp = auth_client.post("/api/whatsapp/send", json={
        "to": "+911234567890", "message": "hi", "contact_id": contact["id"]
    })
    assert resp.status_code == 200
    assert resp.json()["configured"] is False
    assert auth_client.get("/api/communication-log").json() == []


def test_sms_send_linked_to_lead(auth_client, monkeypatch):
    lead = _first_lead(auth_client)
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+10000000000")

    with patch("twilio.rest.Client") as mock_client_cls:
        mock_client_cls.return_value.messages.create.return_value = MagicMock()
        auth_client.post("/api/sms/send", json={"to": "+911234567890", "message": "hi", "lead_id": lead["id"]})

    entries = auth_client.get("/api/communication-log").json()
    assert len(entries) == 1
    assert entries[0]["channel"] == "SMS"
    assert entries[0]["lead_id"] == lead["id"]


def test_logged_call_linked_to_contact(auth_client):
    contact = _first_contact(auth_client)
    resp = auth_client.post("/api/calls", json={
        "name": contact["name"], "phone": contact["phone"], "contact_id": contact["id"]
    })
    assert resp.status_code == 200
    call = resp.json()
    assert call["contact_id"] == contact["id"]
    assert call["contact_name"] == contact["name"]
    assert call["lead_id"] is None

    listed = auth_client.get("/api/calls").json()
    assert next(c for c in listed if c["id"] == call["id"])["contact_name"] == contact["name"]


def test_activities_feed_filters_by_lead_id(auth_client, monkeypatch):
    lead = _first_lead(auth_client)
    other_lead = auth_client.get("/api/leads").json()[1]

    monkeypatch.setenv("SMTP_HOST", "smtp.fake.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@fake.com")
    monkeypatch.setenv("SMTP_PASSWORD", "fakepass")

    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.return_value = MagicMock()
        auth_client.post("/api/email/send", json={
            "to": "a@example.com", "subject": "s1", "body": "b1", "lead_id": lead["id"]
        })
        auth_client.post("/api/email/send", json={
            "to": "b@example.com", "subject": "s2", "body": "b2", "lead_id": other_lead["id"]
        })

    resp = auth_client.get(f"/api/activities?lead_id={lead['id']}")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["lead_id"] == lead["id"]
    assert items[0]["lead_name"] == lead["name"]


def test_activities_feed_filters_by_contact_id_includes_calls(auth_client):
    contact = _first_contact(auth_client)
    other_contact = auth_client.get("/api/contacts").json()[1]

    auth_client.post("/api/calls", json={"name": contact["name"], "contact_id": contact["id"]})
    auth_client.post("/api/calls", json={"name": other_contact["name"], "contact_id": other_contact["id"]})

    resp = auth_client.get(f"/api/activities?contact_id={contact['id']}")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["channel"] == "Call"
    assert items[0]["contact_id"] == contact["id"]
    assert items[0]["contact_name"] == contact["name"]


def test_activities_feed_includes_linked_task(auth_client):
    """Tasks already carry lead_id/contact_id (editable from the Today page), but were missing
    from the merged activities feed - a task linked to a lead never showed up on that lead's
    own Activity Timeline until now."""
    lead = _first_lead(auth_client)
    task = auth_client.post("/api/tasks", json={
        "title": "Send KYC checklist", "due_date": "2026-09-01", "lead_id": lead["id"]
    }).json()

    resp = auth_client.get(f"/api/activities?lead_id={lead['id']}")
    assert resp.status_code == 200
    items = resp.json()
    task_item = next(i for i in items if i["id"] == f"task-{task['id']}")
    assert task_item["channel"] == "Task"
    assert task_item["lead_id"] == lead["id"]
    assert task_item["lead_name"] == lead["name"]
    assert task_item["outcome"] == "Pending"

    auth_client.put(f"/api/tasks/{task['id']}", json={"completed": True})
    completed_item = next(i for i in auth_client.get(f"/api/activities?lead_id={lead['id']}").json()
                           if i["id"] == f"task-{task['id']}")
    assert completed_item["outcome"] == "Completed"


def test_activities_feed_includes_linked_meeting(auth_client):
    contact = _first_contact(auth_client)
    meeting = auth_client.post("/api/meetings", json={
        "title": "Policy review", "meeting_date": "2026-09-02", "contact_id": contact["id"]
    }).json()

    resp = auth_client.get(f"/api/activities?contact_id={contact['id']}")
    assert resp.status_code == 200
    items = resp.json()
    meeting_item = next(i for i in items if i["id"] == f"meeting-{meeting['id']}")
    assert meeting_item["channel"] == "Meeting"
    assert meeting_item["contact_id"] == contact["id"]
    assert meeting_item["contact_name"] == contact["name"]
    assert meeting_item["outcome"] == "Scheduled"


def test_activities_feed_channel_filter_accepts_task_and_meeting(auth_client):
    lead = _first_lead(auth_client)
    auth_client.post("/api/tasks", json={"title": "Follow up", "due_date": "2026-09-01", "lead_id": lead["id"]})
    auth_client.post("/api/meetings", json={"title": "Intro call", "meeting_date": "2026-09-02", "lead_id": lead["id"]})

    task_only = auth_client.get("/api/activities?channel=Task").json()
    assert len(task_only) == 1
    assert task_only[0]["channel"] == "Task"

    meeting_only = auth_client.get("/api/activities?channel=Meeting").json()
    assert len(meeting_only) == 1
    assert meeting_only[0]["channel"] == "Meeting"


def test_activities_feed_includes_campaign_membership(auth_client):
    """campaign_recipients was previously only visible from the Marketing page's own recipient
    list (Campaign -> its recipients). A Lead/Contact's own Activity Timeline must show the
    reverse - which campaigns they've been added to - closing the one-way link."""
    lead = _first_lead(auth_client)
    campaign = auth_client.get("/api/campaigns").json()[0]
    auth_client.post(f"/api/campaigns/{campaign['id']}/recipients", json={"lead_ids": [lead["id"]]})

    resp = auth_client.get(f"/api/activities?lead_id={lead['id']}")
    assert resp.status_code == 200
    items = resp.json()
    campaign_item = next(i for i in items if i["channel"] == "Campaign")
    assert campaign_item["detail"] == campaign["name"]
    assert campaign_item["lead_id"] == lead["id"]
    assert campaign_item["outcome"] == "Pending"


def test_activities_feed_channel_filter_accepts_campaign(auth_client):
    lead = _first_lead(auth_client)
    campaign = auth_client.get("/api/campaigns").json()[0]
    auth_client.post(f"/api/campaigns/{campaign['id']}/recipients", json={"lead_ids": [lead["id"]]})

    campaign_only = auth_client.get("/api/activities?channel=Campaign").json()
    assert len(campaign_only) == 1
    assert campaign_only[0]["channel"] == "Campaign"


def test_activities_feed_unlinked_items_have_null_lead_and_contact(auth_client):
    auth_client.post("/api/calls", json={"name": "Cold Call Prospect"})
    items = auth_client.get("/api/activities").json()
    call_item = next(i for i in items if i["channel"] == "Call")
    assert call_item["lead_id"] is None
    assert call_item["contact_id"] is None
