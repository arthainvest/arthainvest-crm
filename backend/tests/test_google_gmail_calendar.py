"""Gmail send and Calendar sync both ride on the same connected Google account as Google
Sheets (see test_google_sheets.py's docstring for why OAuth itself is mocked, not faked
end-to-end) - reuses the same _connect_fake_google_account helper via a local copy so this
file doesn't need to import across test modules."""
from unittest.mock import patch, MagicMock


def _connect_fake_google_account(auth_client, client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "fake-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "fake-client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/integrations/google/callback")
    fake_token_response = MagicMock()
    fake_token_response.json.return_value = {"access_token": "a", "refresh_token": "r", "expires_in": 3600}
    fake_token_response.raise_for_status = MagicMock()
    fake_userinfo_response = MagicMock()
    fake_userinfo_response.json.return_value = {"email": "advisor@example.com"}
    fake_userinfo_response.raise_for_status = MagicMock()
    with patch("requests.post", return_value=fake_token_response), \
         patch("requests.get", return_value=fake_userinfo_response):
        client.get("/api/integrations/google/callback", params={"code": "c", "state": auth_client._token}, follow_redirects=False)


def test_connect_requests_all_three_scopes(auth_client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "fake-client-id")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/integrations/google/callback")
    resp = auth_client.get("/api/integrations/google/connect")
    auth_url = resp.json()["auth_url"]
    assert "gmail.send" in auth_url
    assert "calendar.events" in auth_url
    assert "spreadsheets" in auth_url


def test_gmail_send_not_configured_when_not_connected(auth_client):
    resp = auth_client.post("/api/integrations/gmail/send", json={
        "to": "prospect@example.com", "subject": "Hi", "body": "Following up"
    })
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_gmail_send_success_logs_to_communication_log(auth_client, client, monkeypatch):
    _connect_fake_google_account(auth_client, client, monkeypatch)

    fake_send_response = MagicMock(status_code=200)
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None, **kwargs):
        if "gmail.googleapis.com" in url:
            captured['url'] = url
            captured['auth_header'] = headers.get('Authorization')
            captured['raw'] = json.get('raw')
            return fake_send_response
        return MagicMock(status_code=200)

    with patch("requests.post", side_effect=fake_post):
        resp = auth_client.post("/api/integrations/gmail/send", json={
            "to": "prospect@example.com", "subject": "Following up", "body": "Just checking in"
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    assert "prospect@example.com" in data["message"]
    assert "gmail.googleapis.com" in captured['url']
    assert captured['auth_header'] == "Bearer a"
    assert captured['raw']  # base64url MIME payload, non-empty

    log = auth_client.get("/api/communication-log?channel=Email").json()
    assert any(entry["recipient"] == "prospect@example.com" and entry["status"] == "Sent" for entry in log)


def test_gmail_send_failure_logs_failed_status(auth_client, client, monkeypatch):
    _connect_fake_google_account(auth_client, client, monkeypatch)

    def fake_post(url, headers=None, json=None, timeout=None, **kwargs):
        if "gmail.googleapis.com" in url:
            return MagicMock(status_code=403, text="insufficientPermissions")
        return MagicMock(status_code=200)

    with patch("requests.post", side_effect=fake_post):
        resp = auth_client.post("/api/integrations/gmail/send", json={
            "to": "prospect@example.com", "subject": "Hi", "body": "Body"
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    assert "failed" in data["message"].lower()

    log = auth_client.get("/api/communication-log?channel=Email").json()
    assert any(entry["recipient"] == "prospect@example.com" and entry["status"] == "Failed" for entry in log)


def _create_meeting(auth_client, **overrides):
    body = {"title": "Policy review call", "meeting_date": "2026-09-01", "meeting_time": "14:30"}
    body.update(overrides)
    resp = auth_client.post("/api/meetings", json=body)
    assert resp.status_code == 200
    return resp.json()


def test_calendar_sync_not_configured_when_not_connected(auth_client):
    meeting = _create_meeting(auth_client)
    resp = auth_client.post(f"/api/meetings/{meeting['id']}/sync-to-google-calendar")
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_calendar_sync_unknown_meeting_404s(auth_client, client, monkeypatch):
    _connect_fake_google_account(auth_client, client, monkeypatch)
    resp = auth_client.post("/api/meetings/999999/sync-to-google-calendar")
    assert resp.status_code == 404


def test_calendar_sync_creates_timed_event(auth_client, client, monkeypatch):
    _connect_fake_google_account(auth_client, client, monkeypatch)
    meeting = _create_meeting(auth_client, title="Policy review call", meeting_date="2026-09-01", meeting_time="14:30", location="Zoom")

    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None, **kwargs):
        if "calendar/v3" in url:
            captured['url'] = url
            captured['body'] = json
            return MagicMock(status_code=200, json=lambda: {"id": "evt_abc123", "htmlLink": "https://calendar.google.com/event?eid=abc123"})
        return MagicMock(status_code=200)

    with patch("requests.post", side_effect=fake_post):
        resp = auth_client.post(f"/api/meetings/{meeting['id']}/sync-to-google-calendar")

    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    assert data["event_link"] == "https://calendar.google.com/event?eid=abc123"
    assert captured['body']['summary'] == "Policy review call"
    assert captured['body']['location'] == "Zoom"
    assert captured['body']['start']['dateTime'] == "2026-09-01T14:30:00"
    assert captured['body']['end']['dateTime'] == "2026-09-01T15:00:00"

    stored = auth_client.get("/api/meetings?date=2026-09-01").json()
    synced = next(m for m in stored if m['id'] == meeting['id'])
    assert synced['google_calendar_event_id'] == "evt_abc123"


def test_calendar_sync_all_day_event_when_no_time(auth_client, client, monkeypatch):
    _connect_fake_google_account(auth_client, client, monkeypatch)
    meeting = _create_meeting(auth_client, title="Full day workshop", meeting_date="2026-09-02", meeting_time=None)

    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None, **kwargs):
        if "calendar/v3" in url:
            captured['body'] = json
            return MagicMock(status_code=200, json=lambda: {"id": "evt_allday", "htmlLink": "https://calendar.google.com/event?eid=allday"})
        return MagicMock(status_code=200)

    with patch("requests.post", side_effect=fake_post):
        resp = auth_client.post(f"/api/meetings/{meeting['id']}/sync-to-google-calendar")

    assert resp.status_code == 200
    assert captured['body']['start'] == {"date": "2026-09-02"}
    assert captured['body']['end'] == {"date": "2026-09-02"}


def test_calendar_resync_updates_existing_event_via_patch(auth_client, client, monkeypatch):
    _connect_fake_google_account(auth_client, client, monkeypatch)
    meeting = _create_meeting(auth_client)

    with patch("requests.post", return_value=MagicMock(status_code=200, json=lambda: {"id": "evt_first", "htmlLink": "https://calendar.google.com/event?eid=first"})):
        auth_client.post(f"/api/meetings/{meeting['id']}/sync-to-google-calendar")

    captured = {}

    def fake_patch(url, headers=None, json=None, timeout=None, **kwargs):
        captured['url'] = url
        return MagicMock(status_code=200, json=lambda: {"id": "evt_first", "htmlLink": "https://calendar.google.com/event?eid=first"})

    with patch("requests.post", return_value=MagicMock(status_code=200)), \
         patch("requests.patch", side_effect=fake_patch) as mock_patch:
        resp = auth_client.post(f"/api/meetings/{meeting['id']}/sync-to-google-calendar")

    assert resp.status_code == 200
    assert mock_patch.call_count == 1
    assert "evt_first" in captured['url']
