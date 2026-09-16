"""Security tests for the unified /api/activities feed (Gate M-1/M-2).

/api/activities merges five sources (communication_log, calls, tasks, meetings,
campaign_recipients) with zero prior visibility filtering - a direct bypass of every
per-entity fix already shipped for Calls/Tasks, plus the first-ever gate for
communication_log/campaign_recipients. Each source must now be scoped in SQL before its own
LIMIT, and lead_id/contact_id must remain ordinary filters, never an access-control bypass.
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
    yogesh_user_id, yogesh_token = _register_and_login(client, auth_token, "yogesh_act", role="admin")
    samiksha_user_id, samiksha_token = _register_and_login(client, auth_token, "samiksha_act")
    chirag_user_id, chirag_token = _register_and_login(client, auth_token, "chirag_act")
    amol_user_id, amol_token = _register_and_login(client, auth_token, "amol_act")

    samiksha_tm = auth_client.post("/api/team", json={"name": "Samiksha Act", "role": "employee"}).json()
    chirag_tm = auth_client.post("/api/team", json={"name": "Chirag Act", "role": "employee"}).json()
    amol_tm = auth_client.post("/api/team", json={"name": "Amol Act", "role": "employee"}).json()

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


def _send_email(client, monkeypatch, subject, lead_id=None):
    monkeypatch.setenv("SMTP_HOST", "smtp.fake.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@fake.com")
    monkeypatch.setenv("SMTP_PASSWORD", "fakepass")
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.return_value = MagicMock()
        payload = {"to": "client@x.com", "subject": subject, "body": "Body"}
        if lead_id is not None:
            payload["lead_id"] = lead_id
        resp = client.post("/api/email/send", json=payload)
    assert resp.status_code == 200, resp.text


def _detail_titles(items, channel=None):
    if channel:
        items = [i for i in items if i["channel"] == channel]
    return {i["detail"] for i in items}


def test_admin_sees_all_five_sources(client, auth_client, auth_token, monkeypatch):
    h = hierarchy(client, auth_client, auth_token)
    _send_email(h["chirag"], monkeypatch, "Chirag Email")
    h["chirag"].post("/api/calls", json={"name": "Chirag Call"})
    h["chirag"].post("/api/tasks", json={"title": "Chirag Task", "due_date": "2027-01-20"})
    h["chirag"].post("/api/meetings", json={"title": "Chirag Meeting", "meeting_date": "2027-01-20"})
    campaign = h["nimita"].post("/api/campaigns", json={"name": "Shared Campaign"}).json()
    chirag_lead = h["chirag"].post("/api/leads", json={"name": "Chirag Lead For Campaign", "phone": "9992220001"}).json()
    h["nimita"].post(f"/api/campaigns/{campaign['id']}/recipients", json={"lead_ids": [chirag_lead["id"]]})

    for admin in (h["nimita"], h["yogesh"]):
        items = admin.get("/api/activities?limit=100").json()
        channels = {i["channel"] for i in items}
        assert {"Email", "Call", "Task", "Meeting", "Campaign"} <= channels


def test_manager_hierarchy(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["chirag"].post("/api/tasks", json={"title": "Chirag Task", "due_date": "2027-01-20"})
    h["amol"].post("/api/tasks", json={"title": "Amol Task", "due_date": "2027-01-20"})
    h["samiksha"].post("/api/tasks", json={"title": "Samiksha Own Task", "due_date": "2027-01-20"})

    titles = _detail_titles(h["samiksha"].get("/api/activities?limit=100").json(), "Task")
    assert any("Chirag Task" in t for t in titles)
    assert any("Amol Task" in t for t in titles)
    assert any("Samiksha Own Task" in t for t in titles)


def test_peer_isolation_across_meetings_calls_tasks(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["chirag"].post("/api/meetings", json={"title": "Chirag Meeting Peer", "meeting_date": "2027-01-20"})
    h["amol"].post("/api/meetings", json={"title": "Amol Meeting Peer", "meeting_date": "2027-01-20"})
    h["chirag"].post("/api/calls", json={"name": "Chirag Call Peer"})
    h["amol"].post("/api/calls", json={"name": "Amol Call Peer"})
    h["chirag"].post("/api/tasks", json={"title": "Chirag Task Peer", "due_date": "2027-01-20"})
    h["amol"].post("/api/tasks", json={"title": "Amol Task Peer", "due_date": "2027-01-20"})

    chirag_items = h["chirag"].get("/api/activities?limit=100").json()
    chirag_details = " ".join(i["detail"] or "" for i in chirag_items) + " ".join(i["contact"] or "" for i in chirag_items)
    assert "Chirag Meeting Peer" in chirag_details
    assert "Amol Meeting Peer" not in chirag_details
    assert any(i["channel"] == "Call" and i["contact"] == "Chirag Call Peer" for i in chirag_items)
    assert not any(i["channel"] == "Call" and i["contact"] == "Amol Call Peer" for i in chirag_items)
    assert "Chirag Task Peer" in chirag_details
    assert "Amol Task Peer" not in chirag_details


def test_hidden_communication_log_and_campaign_recipient_do_not_appear(client, auth_client, auth_token, monkeypatch):
    h = hierarchy(client, auth_client, auth_token)
    _send_email(h["amol"], monkeypatch, "Amol's Private Email")

    amol_campaign = h["amol"].post("/api/campaigns", json={"name": "Amol's Campaign"}).json()
    amol_lead = h["amol"].post("/api/leads", json={"name": "Amol's Campaign Lead", "phone": "9992220002"}).json()
    h["nimita"].put(f"/api/campaigns/{amol_campaign['id']}", json={})  # no-op, ensures campaign exists under amol
    h["amol"].post(f"/api/campaigns/{amol_campaign['id']}/recipients", json={"lead_ids": [amol_lead["id"]]})

    chirag_items = h["chirag"].get("/api/activities?limit=100").json()
    assert not any(i["channel"] == "Email" and i["detail"] == "Amol's Private Email" for i in chirag_items)
    assert not any(i["channel"] == "Campaign" and i["detail"] == "Amol's Campaign" for i in chirag_items)

    # Admin still sees both.
    nimita_items = h["nimita"].get("/api/activities?limit=100").json()
    assert any(i["channel"] == "Email" and i["detail"] == "Amol's Private Email" for i in nimita_items)
    assert any(i["channel"] == "Campaign" and i["detail"] == "Amol's Campaign" for i in nimita_items)


def test_arbitrary_lead_id_does_not_bypass_visibility(client, auth_client, auth_token, monkeypatch):
    """Chirag supplies Amol's real Lead id as a query filter - he must get only whatever slice
    of that lead's activity he can already see (here: nothing), never Amol's actual data."""
    h = hierarchy(client, auth_client, auth_token)
    amol_lead = h["amol"].post("/api/leads", json={"name": "Amol's Bypass Test Lead", "phone": "9992220003"}).json()
    _send_email(h["amol"], monkeypatch, "Amol's Lead Email", lead_id=amol_lead["id"])
    h["amol"].post("/api/tasks", json={"title": "Amol's Lead Task", "due_date": "2027-01-20", "lead_id": amol_lead["id"]})

    resp = h["chirag"].get(f"/api/activities?lead_id={amol_lead['id']}")
    assert resp.status_code == 200
    assert resp.json() == []

    # The lead's owner (Amol) still sees it via the same filter.
    amol_view = h["amol"].get(f"/api/activities?lead_id={amol_lead['id']}").json()
    assert len(amol_view) >= 1


def test_arbitrary_contact_id_does_not_bypass_visibility(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_contact = h["amol"].post("/api/contacts", json={"name": "Amol's Bypass Contact", "phone": "9992220004"}).json()
    h["amol"].post("/api/tasks", json={"title": "Amol's Contact Task", "due_date": "2027-01-20", "contact_id": amol_contact["id"]})

    resp = h["chirag"].get(f"/api/activities?contact_id={amol_contact['id']}")
    assert resp.status_code == 200
    assert resp.json() == []


def test_cross_entity_name_redaction_in_feed(client, auth_client, auth_token):
    """A Task visible to Chirag (he created it) but linked to Amol's Lead must show lead_id
    without lead_name."""
    h = hierarchy(client, auth_client, auth_token)
    amol_lead = h["amol"].post("/api/leads", json={"name": "Amol's Redaction Lead", "phone": "9992220005"}).json()
    h["chirag"].post("/api/tasks", json={"title": "Chirag Task About Amol Lead", "due_date": "2027-01-20", "lead_id": amol_lead["id"]})

    chirag_item = next(i for i in h["chirag"].get("/api/activities?limit=100").json() if i["channel"] == "Task" and "Chirag Task About Amol Lead" in (i["detail"] or ""))
    assert chirag_item["lead_id"] == amol_lead["id"]
    assert chirag_item["lead_name"] is None

    nimita_item = next(i for i in h["nimita"].get("/api/activities?limit=100").json() if i["channel"] == "Task" and "Chirag Task About Amol Lead" in (i["detail"] or ""))
    assert nimita_item["lead_name"] == "Amol's Redaction Lead"


def test_campaign_field_protection(client, auth_client, auth_token):
    """Reconfirms (implementation-time, per the checkpoint) that campaign_name is the only
    campaign-specific field surfaced, and it's protected by the same campaigns.created_by scope
    as everything else - no other campaign field (message content, recipient counts) leaks
    through this feed."""
    h = hierarchy(client, auth_client, auth_token)
    amol_campaign = h["amol"].post("/api/campaigns", json={"name": "Amol's Secret Campaign", "message": "Confidential campaign body"}).json()
    amol_lead = h["amol"].post("/api/leads", json={"name": "Amol Campaign Lead", "phone": "9992220006"}).json()
    h["amol"].post(f"/api/campaigns/{amol_campaign['id']}/recipients", json={"lead_ids": [amol_lead["id"]]})

    chirag_items = h["chirag"].get("/api/activities?limit=100").json()
    all_text = str(chirag_items)
    assert "Amol's Secret Campaign" not in all_text
    assert "Confidential campaign body" not in all_text


def test_ordering_and_limit_not_consumed_by_invisible_rows(client, auth_client, auth_token):
    """Constructs the exact scenario the SQL-before-LIMIT design prevents: many of another
    employee's invisible, more-recent Tasks must not consume the caller's own per-source LIMIT
    slot, starving out the caller's own older, real activity."""
    h = hierarchy(client, auth_client, auth_token)
    h["chirag"].post("/api/tasks", json={"title": "Chirag's Only Task", "due_date": "2027-01-20"})
    for i in range(10):
        h["amol"].post("/api/tasks", json={"title": f"Amol Task {i}", "due_date": "2027-01-20"})

    # A tight limit that would be entirely consumed by Amol's 10 newer, invisible tasks if
    # the scope filter were applied in Python after the SQL LIMIT instead of inside the WHERE.
    items = h["chirag"].get("/api/activities?limit=1&channel=Task").json()
    assert len(items) == 1
    assert "Chirag's Only Task" in items[0]["detail"]
