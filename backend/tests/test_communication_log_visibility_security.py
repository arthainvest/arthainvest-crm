"""Security tests for communication_log access control (Gate M-1/M-2).

communication_log is creator-owned (communication_log.created_by), NOT linked-Lead/Contact-owned
- the critical rejected design was `creator visibility OR linked Lead/Contact visibility`, which
would have let an employee read another employee's actual email/WhatsApp/SMS content merely
because they own the recipient's Lead/Contact. These tests specifically prove that rule was
NOT implemented, alongside the standard manager-hierarchy/peer-isolation matrix.
"""
from unittest.mock import patch, MagicMock


class _TokenedClient:
    def __init__(self, client, token):
        self._c = client
        self._t = token

    def _url(self, path):
        sep = '&' if '?' in path else '?'
        return f"{path}{sep}token={self._t}"

    def get(self, path, **kw):
        return self._c.get(self._url(path), **kw)

    def post(self, path, **kw):
        return self._c.post(self._url(path), **kw)

    def put(self, path, **kw):
        return self._c.put(self._url(path), **kw)

    def delete(self, path, **kw):
        return self._c.delete(self._url(path), **kw)


def _register_and_login(client, admin_token, username, role="employee"):
    resp = client.post(
        f"/api/auth/register?token={admin_token}",
        json={
            "username": username, "email": f"{username}@example.com",
            "password": "pass12345", "full_name": username, "role": role,
        },
    )
    assert resp.status_code == 200, resp.text
    user_id = resp.json()["id"]
    login = client.post("/api/auth/login", json={"username": username, "password": "pass12345"})
    assert login.status_code == 200, login.text
    return user_id, login.json()["access_token"]


def hierarchy(client, auth_client, auth_token):
    yogesh_user_id, yogesh_token = _register_and_login(client, auth_token, "yogesh_comm", role="admin")
    samiksha_user_id, samiksha_token = _register_and_login(client, auth_token, "samiksha_comm")
    chirag_user_id, chirag_token = _register_and_login(client, auth_token, "chirag_comm")
    amol_user_id, amol_token = _register_and_login(client, auth_token, "amol_comm")

    samiksha_tm = auth_client.post("/api/team", json={"name": "Samiksha Comm", "role": "employee"}).json()
    chirag_tm = auth_client.post("/api/team", json={"name": "Chirag Comm", "role": "employee"}).json()
    amol_tm = auth_client.post("/api/team", json={"name": "Amol Comm", "role": "employee"}).json()

    assert auth_client.put(f"/api/team/{samiksha_tm['id']}", json={"user_id": samiksha_user_id}).status_code == 200
    assert auth_client.put(f"/api/team/{chirag_tm['id']}", json={"user_id": chirag_user_id, "reports_to": samiksha_tm['id']}).status_code == 200
    assert auth_client.put(f"/api/team/{amol_tm['id']}", json={"user_id": amol_user_id, "reports_to": samiksha_tm['id']}).status_code == 200

    return {
        "nimita": auth_client,
        "yogesh": _TokenedClient(client, yogesh_token),
        "samiksha": _TokenedClient(client, samiksha_token), "samiksha_tm_id": samiksha_tm['id'],
        "chirag": _TokenedClient(client, chirag_token), "chirag_tm_id": chirag_tm['id'],
        "amol": _TokenedClient(client, amol_token), "amol_tm_id": amol_tm['id'],
    }


def _send_email(client, monkeypatch, to, subject, body, lead_id=None, contact_id=None):
    """Sends a real (mocked-SMTP) email as `client`, so a communication_log row gets created
    with created_by = client's own user_id - the only reliable way to produce a row with a
    known creator, since /api/email/send is the sole write path into this table."""
    monkeypatch.setenv("SMTP_HOST", "smtp.fake.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@fake.com")
    monkeypatch.setenv("SMTP_PASSWORD", "fakepass")
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.return_value = MagicMock()
        payload = {"to": to, "subject": subject, "body": body}
        if lead_id is not None:
            payload["lead_id"] = lead_id
        if contact_id is not None:
            payload["contact_id"] = contact_id
        resp = client.post("/api/email/send", json=payload)
    assert resp.status_code == 200, resp.text
    assert resp.json()["configured"] is True


def test_admin_sees_all_communication_logs(client, auth_client, auth_token, monkeypatch):
    h = hierarchy(client, auth_client, auth_token)
    _send_email(h["chirag"], monkeypatch, "client@x.com", "Chirag's Email", "Body A")
    _send_email(h["amol"], monkeypatch, "client@y.com", "Amol's Email", "Body B")

    for admin in (h["nimita"], h["yogesh"]):
        entries = admin.get("/api/communication-log").json()
        subjects = {e["subject"] for e in entries}
        assert "Chirag's Email" in subjects
        assert "Amol's Email" in subjects


def test_manager_sees_own_and_reports(client, auth_client, auth_token, monkeypatch):
    h = hierarchy(client, auth_client, auth_token)
    _send_email(h["chirag"], monkeypatch, "client@x.com", "Chirag's Email", "Body A")
    _send_email(h["amol"], monkeypatch, "client@y.com", "Amol's Email", "Body B")
    _send_email(h["samiksha"], monkeypatch, "client@z.com", "Samiksha's Own Email", "Body C")

    entries = h["samiksha"].get("/api/communication-log").json()
    subjects = {e["subject"] for e in entries}
    assert {"Chirag's Email", "Amol's Email", "Samiksha's Own Email"} <= subjects


def test_peer_isolation(client, auth_client, auth_token, monkeypatch):
    h = hierarchy(client, auth_client, auth_token)
    _send_email(h["chirag"], monkeypatch, "client@x.com", "Chirag's Email", "Body A")
    _send_email(h["amol"], monkeypatch, "client@y.com", "Amol's Email", "Body B")

    chirag_subjects = {e["subject"] for e in h["chirag"].get("/api/communication-log").json()}
    assert "Chirag's Email" in chirag_subjects
    assert "Amol's Email" not in chirag_subjects

    amol_subjects = {e["subject"] for e in h["amol"].get("/api/communication-log").json()}
    assert "Amol's Email" in amol_subjects
    assert "Chirag's Email" not in amol_subjects


def test_creator_owned_linked_lead_remains_visible_to_creator(client, auth_client, auth_token, monkeypatch):
    """User A creates a communication log linked to User B's Lead. User A can still see it -
    ownership belongs to the sender, not the Lead's owner."""
    h = hierarchy(client, auth_client, auth_token)
    amol_lead = h["amol"].post("/api/leads", json={"name": "Amol's Lead", "phone": "9991110001"}).json()

    _send_email(h["chirag"], monkeypatch, "client@x.com", "About Amol's Lead", "Body", lead_id=amol_lead["id"])

    entries = h["chirag"].get("/api/communication-log").json()
    assert any(e["subject"] == "About Amol's Lead" for e in entries)


def test_linked_lead_ownership_does_not_grant_communication_log_visibility(client, auth_client, auth_token, monkeypatch):
    """The critical rejected-rule test: User B owns the Lead but did NOT create the
    communication log - User B must NOT see it, proving creator-visibility OR linked-visibility
    was NOT implemented."""
    h = hierarchy(client, auth_client, auth_token)
    amol_lead = h["amol"].post("/api/leads", json={"name": "Amol's Lead", "phone": "9991110002"}).json()

    _send_email(h["chirag"], monkeypatch, "client@x.com", "About Amol's Lead", "Sensitive body content", lead_id=amol_lead["id"])

    amol_entries = h["amol"].get("/api/communication-log").json()
    assert not any(e["subject"] == "About Amol's Lead" for e in amol_entries)


def test_unlinked_communication_log_visible_only_to_creator(client, auth_client, auth_token, monkeypatch):
    h = hierarchy(client, auth_client, auth_token)
    _send_email(h["chirag"], monkeypatch, "adhoc@x.com", "Unlinked Email", "Body")

    assert any(e["subject"] == "Unlinked Email" for e in h["chirag"].get("/api/communication-log").json())
    assert not any(e["subject"] == "Unlinked Email" for e in h["amol"].get("/api/communication-log").json())


def test_message_subject_recipient_error_detail_isolation(client, auth_client, auth_token, monkeypatch):
    h = hierarchy(client, auth_client, auth_token)
    _send_email(h["chirag"], monkeypatch, "secret-recipient@x.com", "Confidential Subject", "Confidential message body")

    amol_entries = h["amol"].get("/api/communication-log").json()
    all_text = str(amol_entries)
    assert "Confidential Subject" not in all_text
    assert "Confidential message body" not in all_text
    assert "secret-recipient@x.com" not in all_text


def test_direct_communication_log_endpoint_isolation(client, auth_client, auth_token, monkeypatch):
    """Same isolation matrix, explicitly against GET /api/communication-log directly (not via
    the activity feed) - the endpoint this file is primarily testing."""
    h = hierarchy(client, auth_client, auth_token)
    _send_email(h["chirag"], monkeypatch, "client@x.com", "Chirag Direct", "Body")
    _send_email(h["amol"], monkeypatch, "client@y.com", "Amol Direct", "Body")

    chirag_view = h["chirag"].get("/api/communication-log").json()
    assert len(chirag_view) == 1
    assert chirag_view[0]["subject"] == "Chirag Direct"


def test_cross_entity_lead_contact_name_redaction(client, auth_client, auth_token, monkeypatch):
    """Chirag creates a comm-log entry linked to Amol's Lead - Chirag can see the record itself
    (he's the creator) but the linked Lead's name must be redacted since Chirag can't see it."""
    h = hierarchy(client, auth_client, auth_token)
    amol_lead = h["amol"].post("/api/leads", json={"name": "Amol's Real Lead Name", "phone": "9991110003"}).json()

    _send_email(h["chirag"], monkeypatch, "client@x.com", "Redaction Test", "Body", lead_id=amol_lead["id"])

    chirag_view = next(e for e in h["chirag"].get("/api/communication-log").json() if e["subject"] == "Redaction Test")
    assert chirag_view["lead_id"] == amol_lead["id"]
    assert chirag_view["lead_name"] is None

    nimita_view = next(e for e in h["nimita"].get("/api/communication-log").json() if e["subject"] == "Redaction Test")
    assert nimita_view["lead_name"] == "Amol's Real Lead Name"


def test_channel_filter_combines_with_visibility(client, auth_client, auth_token, monkeypatch):
    h = hierarchy(client, auth_client, auth_token)
    _send_email(h["chirag"], monkeypatch, "client@x.com", "Chirag Email", "Body")
    _send_email(h["amol"], monkeypatch, "client@y.com", "Amol Email", "Body")

    chirag_view = h["chirag"].get("/api/communication-log?channel=Email").json()
    assert len(chirag_view) == 1
    assert chirag_view[0]["subject"] == "Chirag Email"
