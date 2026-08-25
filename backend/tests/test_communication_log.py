from unittest.mock import patch, MagicMock


def test_communication_log_empty_by_default(auth_client):
    resp = auth_client.get("/api/communication-log")
    assert resp.status_code == 200
    assert resp.json() == []


def test_unconfigured_sends_are_not_logged(auth_client):
    """No credentials set (conftest strips them) - nothing was actually attempted, so nothing
    should land in the log."""
    auth_client.post("/api/sms/send", json={"to": "+911234567890", "message": "hi"})
    auth_client.post("/api/whatsapp/send", json={"to": "+911234567890", "message": "hi"})
    auth_client.post("/api/email/send", json={"to": "a@b.com", "subject": "s", "body": "b"})

    resp = auth_client.get("/api/communication-log")
    assert resp.json() == []


def test_successful_email_send_is_logged(auth_client, monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.fake.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@fake.com")
    monkeypatch.setenv("SMTP_PASSWORD", "fakepass")

    mock_server = MagicMock()
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.return_value = mock_server
        resp = auth_client.post("/api/email/send", json={
            "to": "client@example.com", "subject": "Renewal reminder", "body": "Please renew soon."
        })

    assert resp.status_code == 200
    assert resp.json()["configured"] is True

    log_resp = auth_client.get("/api/communication-log")
    assert log_resp.status_code == 200
    entries = log_resp.json()
    assert len(entries) == 1
    assert entries[0]["channel"] == "Email"
    assert entries[0]["recipient"] == "client@example.com"
    assert entries[0]["subject"] == "Renewal reminder"
    assert entries[0]["status"] == "Sent"

    # Channel filter must scope correctly.
    whatsapp_resp = auth_client.get("/api/communication-log?channel=WhatsApp")
    assert whatsapp_resp.json() == []
    email_resp = auth_client.get("/api/communication-log?channel=Email")
    assert len(email_resp.json()) == 1


def test_failed_email_send_is_logged_with_error(auth_client, monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.fake.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@fake.com")
    monkeypatch.setenv("SMTP_PASSWORD", "fakepass")

    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.side_effect = Exception("connection refused")
        resp = auth_client.post("/api/email/send", json={
            "to": "client@example.com", "subject": "Test", "body": "Body"
        })

    assert resp.status_code == 200
    assert resp.json()["configured"] is True

    entries = auth_client.get("/api/communication-log").json()
    assert len(entries) == 1
    assert entries[0]["status"] == "Failed"
    assert "connection refused" in entries[0]["error_detail"]
