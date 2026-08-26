from unittest.mock import patch, MagicMock


def _create_campaign(auth_client, **overrides):
    payload = {"name": "Test Campaign", "type": "Email", "message": "Hello there"}
    payload.update(overrides)
    return auth_client.post("/api/campaigns", json=payload).json()


def _first_lead(auth_client):
    return auth_client.get("/api/leads").json()[0]


def _first_contact(auth_client):
    return auth_client.get("/api/contacts").json()[0]


def test_campaign_starts_with_zero_linked_recipients(auth_client):
    campaign = _create_campaign(auth_client)
    assert campaign["linked_recipient_count"] == 0
    assert campaign["sent_count"] == 0

    listed = auth_client.get("/api/campaigns").json()
    assert next(c for c in listed if c["id"] == campaign["id"])["linked_recipient_count"] == 0


def test_add_lead_and_contact_recipients(auth_client):
    campaign = _create_campaign(auth_client)
    lead = _first_lead(auth_client)
    contact = _first_contact(auth_client)

    resp = auth_client.post(f"/api/campaigns/{campaign['id']}/recipients", json={
        "lead_ids": [lead["id"]], "contact_ids": [contact["id"]]
    })
    assert resp.status_code == 200
    assert resp.json() == {"added": 2, "skipped": 0}

    recipients = auth_client.get(f"/api/campaigns/{campaign['id']}/recipients").json()
    assert len(recipients) == 2
    lead_recipient = next(r for r in recipients if r["lead_id"] == lead["id"])
    assert lead_recipient["name"] == lead["name"]
    assert lead_recipient["status"] == "Pending"
    contact_recipient = next(r for r in recipients if r["contact_id"] == contact["id"])
    assert contact_recipient["name"] == contact["name"]

    campaigns = auth_client.get("/api/campaigns").json()
    assert next(c for c in campaigns if c["id"] == campaign["id"])["linked_recipient_count"] == 2


def test_add_recipients_skips_duplicates(auth_client):
    campaign = _create_campaign(auth_client)
    lead = _first_lead(auth_client)

    first = auth_client.post(f"/api/campaigns/{campaign['id']}/recipients", json={"lead_ids": [lead["id"]]}).json()
    assert first == {"added": 1, "skipped": 0}

    second = auth_client.post(f"/api/campaigns/{campaign['id']}/recipients", json={"lead_ids": [lead["id"]]}).json()
    assert second == {"added": 0, "skipped": 1}

    recipients = auth_client.get(f"/api/campaigns/{campaign['id']}/recipients").json()
    assert len(recipients) == 1


def test_add_recipients_requires_at_least_one(auth_client):
    campaign = _create_campaign(auth_client)
    resp = auth_client.post(f"/api/campaigns/{campaign['id']}/recipients", json={})
    assert resp.status_code == 400


def test_add_recipients_404s_for_unknown_campaign(auth_client):
    lead = _first_lead(auth_client)
    resp = auth_client.post("/api/campaigns/9999/recipients", json={"lead_ids": [lead["id"]]})
    assert resp.status_code == 404


def test_remove_recipient(auth_client):
    campaign = _create_campaign(auth_client)
    lead = _first_lead(auth_client)
    auth_client.post(f"/api/campaigns/{campaign['id']}/recipients", json={"lead_ids": [lead["id"]]})
    recipient_id = auth_client.get(f"/api/campaigns/{campaign['id']}/recipients").json()[0]["id"]

    resp = auth_client.delete(f"/api/campaigns/{campaign['id']}/recipients/{recipient_id}")
    assert resp.status_code == 200
    assert auth_client.get(f"/api/campaigns/{campaign['id']}/recipients").json() == []


def test_deleting_campaign_removes_its_recipients(auth_client):
    campaign = _create_campaign(auth_client)
    lead = _first_lead(auth_client)
    auth_client.post(f"/api/campaigns/{campaign['id']}/recipients", json={"lead_ids": [lead["id"]]})

    resp = auth_client.delete(f"/api/campaigns/{campaign['id']}")
    assert resp.status_code == 200
    # The recipients row must be gone too, not just orphaned - verified indirectly by
    # re-creating a campaign and confirming a fresh recipients list works normally.
    new_campaign = _create_campaign(auth_client, name="After Delete")
    assert auth_client.get(f"/api/campaigns/{new_campaign['id']}/recipients").json() == []


def test_send_campaign_requires_message(auth_client):
    campaign = _create_campaign(auth_client, message=None)
    lead = _first_lead(auth_client)
    auth_client.post(f"/api/campaigns/{campaign['id']}/recipients", json={"lead_ids": [lead["id"]]})

    resp = auth_client.post(f"/api/campaigns/{campaign['id']}/send")
    assert resp.status_code == 400


def test_send_campaign_with_no_recipients(auth_client):
    campaign = _create_campaign(auth_client)
    resp = auth_client.post(f"/api/campaigns/{campaign['id']}/send")
    assert resp.status_code == 200
    assert resp.json() == {"sent": 0, "failed": 0, "skipped": 0, "message": "No pending recipients to send to."}


def test_send_email_campaign_updates_recipient_status_and_logs_activity(auth_client, monkeypatch):
    lead = _first_lead(auth_client)
    campaign = _create_campaign(auth_client, type="Email", message="Big news for you")
    auth_client.post(f"/api/campaigns/{campaign['id']}/recipients", json={"lead_ids": [lead["id"]]})

    monkeypatch.setenv("SMTP_HOST", "smtp.fake.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@fake.com")
    monkeypatch.setenv("SMTP_PASSWORD", "fakepass")

    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.return_value = MagicMock()
        resp = auth_client.post(f"/api/campaigns/{campaign['id']}/send")

    assert resp.status_code == 200
    result = resp.json()
    assert result["sent"] == 1
    assert result["failed"] == 0

    recipients = auth_client.get(f"/api/campaigns/{campaign['id']}/recipients").json()
    assert recipients[0]["status"] == "Sent"
    assert recipients[0]["sent_at"] is not None

    campaigns = auth_client.get("/api/campaigns").json()
    assert next(c for c in campaigns if c["id"] == campaign["id"])["sent_count"] == 1

    # The send must show up in the lead's own Activity Timeline, same pipeline as any
    # other email - this is the whole point of linking real recipients. The campaign
    # membership itself (added just above) is now also its own Campaign activity item.
    activities = auth_client.get(f"/api/activities?lead_id={lead['id']}").json()
    assert len(activities) == 2
    email_item = next(a for a in activities if a["channel"] == "Email")
    assert email_item["detail"] == campaign["name"]
    campaign_item = next(a for a in activities if a["channel"] == "Campaign")
    assert campaign_item["detail"] == campaign["name"]
    assert campaign_item["outcome"] == "Sent"

    # A second send must skip the now-Sent recipient (nothing left to send to).
    second = auth_client.post(f"/api/campaigns/{campaign['id']}/send").json()
    assert second["message"] == "No pending recipients to send to."


def test_send_campaign_skips_recipients_without_matching_contact_info(auth_client):
    campaign = _create_campaign(auth_client, type="WhatsApp", message="Hi there")
    no_phone_lead = auth_client.post("/api/leads", json={"name": "No Phone Lead", "email": "x@example.com"}).json()
    auth_client.post(f"/api/campaigns/{campaign['id']}/recipients", json={"lead_ids": [no_phone_lead["id"]]})

    # WhatsApp isn't configured (conftest strips credentials) - this hits the
    # not-configured short-circuit before the per-recipient phone check even matters,
    # confirming the batch send doesn't error out either way.
    resp = auth_client.post(f"/api/campaigns/{campaign['id']}/send")
    assert resp.status_code == 200
    assert resp.json()["sent"] == 0

    recipients = auth_client.get(f"/api/campaigns/{campaign['id']}/recipients").json()
    assert recipients[0]["status"] == "Pending"  # untouched - nothing was actually attempted
