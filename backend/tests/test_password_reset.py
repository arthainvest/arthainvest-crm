import re
from unittest.mock import patch, MagicMock


def _send_forgot_password_and_capture_token(client, username):
    """Sends the forgot-password request with SMTP mocked, then digs the raw reset token out
    of the (fake) email body the app tried to send - the only place the raw token ever
    appears, since the DB only stores its hash."""
    mock_server = MagicMock()
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.return_value = mock_server
        resp = client.post("/api/auth/forgot-password", json={"username": username})

    assert resp.status_code == 200
    if not mock_server.sendmail.called:
        return resp, None

    _from, _to, msg_string = mock_server.sendmail.call_args[0]
    match = re.search(r"token=([\w\-]+)", msg_string)
    return resp, (match.group(1) if match else None)


def test_forgot_password_known_user_emails_reset_link(client, monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.fake.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@fake.com")
    monkeypatch.setenv("SMTP_PASSWORD", "fakepass")

    resp, token = _send_forgot_password_and_capture_token(client, "testuser")
    assert "password reset link has been emailed" in resp.json()["message"]
    assert token


def test_forgot_password_unknown_user_same_generic_message_no_email(client, monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.fake.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@fake.com")
    monkeypatch.setenv("SMTP_PASSWORD", "fakepass")

    resp, token = _send_forgot_password_and_capture_token(client, "nobody-here")
    assert "password reset link has been emailed" in resp.json()["message"]
    assert token is None  # no email attempted - username enumeration not possible


def test_reset_password_with_valid_token_succeeds(client, monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.fake.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@fake.com")
    monkeypatch.setenv("SMTP_PASSWORD", "fakepass")

    _, token = _send_forgot_password_and_capture_token(client, "testuser")
    assert token

    resp = client.post("/api/auth/reset-password", json={
        "reset_token": token, "new_password": "brandnew1"
    })
    assert resp.status_code == 200

    assert client.post("/api/auth/login", json={"username": "testuser", "password": "12345"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "testuser", "password": "brandnew1"}).status_code == 200


def test_reset_password_token_is_single_use(client, monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.fake.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@fake.com")
    monkeypatch.setenv("SMTP_PASSWORD", "fakepass")

    _, token = _send_forgot_password_and_capture_token(client, "testuser")

    first = client.post("/api/auth/reset-password", json={"reset_token": token, "new_password": "firstuse1"})
    assert first.status_code == 200

    second = client.post("/api/auth/reset-password", json={"reset_token": token, "new_password": "secondtry1"})
    assert second.status_code == 400
    assert "already been used" in second.json()["detail"]


def test_reset_password_with_garbage_token_rejected(client):
    resp = client.post("/api/auth/reset-password", json={
        "reset_token": "not-a-real-token", "new_password": "whatever12"
    })
    assert resp.status_code == 400
    assert "invalid" in resp.json()["detail"].lower()
