from unittest.mock import patch, MagicMock


def _first_lead(auth_client):
    return auth_client.get("/api/leads").json()[0]


def _first_contact(auth_client):
    return auth_client.get("/api/contacts").json()[0]


def _configure_twilio_dial(monkeypatch, auth_client):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+10000000000")
    auth_client.put("/api/settings", json={"phone": "+919999999999"})


def test_dial_without_lead_or_contact_still_works(auth_client, monkeypatch):
    _configure_twilio_dial(monkeypatch, auth_client)
    with patch("twilio.rest.Client") as mock_client_cls:
        mock_client_cls.return_value.calls.create.return_value = MagicMock(sid="CA123")
        resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    assert data["call_id"] is not None

    calls = auth_client.get("/api/calls").json()
    logged = next(c for c in calls if c["id"] == data["call_id"])
    assert logged["name"] == "+911234567890"
    assert logged["lead_id"] is None
    assert logged["contact_id"] is None
    assert logged["outcome"] is None
    assert logged["duration_seconds"] == 0
    assert logged["type"] == "Outbound"


def test_dial_linked_to_lead_auto_logs_call(auth_client, monkeypatch):
    lead = _first_lead(auth_client)
    _configure_twilio_dial(monkeypatch, auth_client)

    with patch("twilio.rest.Client") as mock_client_cls:
        mock_client_cls.return_value.calls.create.return_value = MagicMock(sid="CA456")
        resp = auth_client.post("/api/calls/dial", json={"to": lead["phone"], "lead_id": lead["id"]})

    assert resp.status_code == 200
    call_id = resp.json()["call_id"]

    calls = auth_client.get("/api/calls").json()
    logged = next(c for c in calls if c["id"] == call_id)
    assert logged["lead_id"] == lead["id"]
    assert logged["name"] == lead["name"]  # resolved from the lead, not left as the raw phone number
    assert logged["contact_id"] is None


def test_dial_linked_to_contact_auto_logs_call(auth_client, monkeypatch):
    contact = _first_contact(auth_client)
    _configure_twilio_dial(monkeypatch, auth_client)

    with patch("twilio.rest.Client") as mock_client_cls:
        mock_client_cls.return_value.calls.create.return_value = MagicMock(sid="CA789")
        resp = auth_client.post("/api/calls/dial", json={"to": contact["phone"], "contact_id": contact["id"]})

    assert resp.status_code == 200
    call_id = resp.json()["call_id"]

    calls = auth_client.get("/api/calls").json()
    logged = next(c for c in calls if c["id"] == call_id)
    assert logged["contact_id"] == contact["id"]
    assert logged["name"] == contact["name"]


def test_auto_logged_dial_counts_as_attempted_not_connected(auth_client, monkeypatch):
    """Attempted just counts rows; Connected requires a real outcome - a dial with no outcome
    yet must show up as attempted-but-not-connected in Calls-by-Employee. testuser is
    login-linked to the 'Artha' roster entry, so the auto-logged call attributes there."""
    lead = _first_lead(auth_client)

    baseline = next(s for s in auth_client.get("/api/analytics/calls/by-employee").json() if s["name"] == "Artha")

    _configure_twilio_dial(monkeypatch, auth_client)
    with patch("twilio.rest.Client") as mock_client_cls:
        mock_client_cls.return_value.calls.create.return_value = MagicMock(sid="CA999")
        auth_client.post("/api/calls/dial", json={"to": lead["phone"], "lead_id": lead["id"]})

    after = next(s for s in auth_client.get("/api/analytics/calls/by-employee").json() if s["name"] == "Artha")
    assert after["today_attempted"] == baseline["today_attempted"] + 1
    assert after["today_connected"] == baseline["today_connected"]  # no outcome yet - not counted as connected


def test_dial_unconfigured_does_not_log_a_call(auth_client):
    """No credentials set (conftest strips them) - nothing was actually attempted, so no call
    should be logged, matching the same contract as _log_communication's configured=False path."""
    resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    assert resp.status_code == 200
    assert resp.json()["configured"] is False
    assert resp.json()["call_id"] is None

    calls = auth_client.get("/api/calls").json()
    assert len(calls) == 4  # only the seeded demo calls, nothing new
