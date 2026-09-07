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


def test_sms_falls_back_to_msg91_when_twilio_unconfigured(auth_client, monkeypatch):
    """Twilio env vars stay unset (conftest strips them) - MSG91 should be tried instead."""
    monkeypatch.setenv("MSG91_AUTH_KEY", "fake-auth-key")
    monkeypatch.setenv("MSG91_SENDER_ID", "ARTHA1")

    mock_response = MagicMock(status_code=200, content=b'{"type": "success"}')
    mock_response.json.return_value = {"type": "success"}
    with patch("requests.post", return_value=mock_response) as mock_post:
        resp = auth_client.post("/api/sms/send", json={"to": "+911234567890", "message": "hi"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    assert "msg91" in data["message"].lower()
    assert mock_post.call_args.kwargs["headers"]["authkey"] == "fake-auth-key"

    log_resp = auth_client.get("/api/communication-log")
    entries = log_resp.json()
    assert len(entries) == 1
    assert entries[0]["channel"] == "SMS"
    assert entries[0]["status"] == "Sent"


def test_sms_msg91_failure_is_logged(auth_client, monkeypatch):
    monkeypatch.setenv("MSG91_AUTH_KEY", "fake-auth-key")
    monkeypatch.setenv("MSG91_SENDER_ID", "ARTHA1")

    mock_response = MagicMock(status_code=200, content=b'{"type": "error", "message": "Invalid sender id"}')
    mock_response.json.return_value = {"type": "error", "message": "Invalid sender id"}
    with patch("requests.post", return_value=mock_response):
        resp = auth_client.post("/api/sms/send", json={"to": "+911234567890", "message": "hi"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    assert "invalid sender id" in data["message"].lower()

    log_resp = auth_client.get("/api/communication-log")
    entries = log_resp.json()
    assert len(entries) == 1
    assert entries[0]["status"] == "Failed"


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
