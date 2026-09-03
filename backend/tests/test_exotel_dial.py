from unittest.mock import patch, MagicMock


def _configure_exotel_dial(monkeypatch, auth_client):
    monkeypatch.setenv("EXOTEL_SID", "sid123")
    monkeypatch.setenv("EXOTEL_API_KEY", "key")
    monkeypatch.setenv("EXOTEL_API_TOKEN", "token")
    monkeypatch.setenv("EXOTEL_CALLER_ID", "0XXXXXXXXX")
    auth_client.put("/api/settings", json={"phone": "+919999999999"})


def _fake_exotel_response(sid="CSid1234"):
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"Call": {"Sid": sid, "Status": "queued"}}
    return resp


def test_exotel_dial_success_logs_call_and_provider_sid(auth_client, monkeypatch):
    _configure_exotel_dial(monkeypatch, auth_client)
    with patch("requests.post", return_value=_fake_exotel_response("CSid1")) as mock_post:
        resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    assert data["call_sid"] == "CSid1"
    assert data["call_id"] is not None

    # Hit Exotel's connect endpoint (not Twilio's), authenticated with the API key/token.
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["auth"] == ("key", "token")
    assert call_kwargs["data"]["From"] == "+919999999999"
    assert call_kwargs["data"]["To"] == "+911234567890"
    assert call_kwargs["data"]["CallerId"] == "0XXXXXXXXX"
    assert call_kwargs["data"]["CustomField"] == str(data["call_id"])

    calls = auth_client.get("/api/calls").json()
    logged = next(c for c in calls if c["id"] == data["call_id"])
    assert logged["outcome"] is None
    assert logged["duration_seconds"] == 0


def test_exotel_preferred_over_twilio_when_both_configured(auth_client, monkeypatch):
    """The user explicitly doesn't want Twilio (no SMS/DLT overhead) - Exotel must win
    whenever both providers happen to have credentials set, not whichever check runs first."""
    _configure_exotel_dial(monkeypatch, auth_client)
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "twilio-sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "twilio-token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+10000000000")

    with patch("requests.post", return_value=_fake_exotel_response()) as mock_post, \
         patch("twilio.rest.Client") as mock_twilio_cls:
        resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})

    assert resp.status_code == 200
    assert resp.json()["configured"] is True
    mock_post.assert_called_once()
    mock_twilio_cls.assert_not_called()


def test_exotel_dial_requires_agent_phone_number(auth_client, monkeypatch):
    monkeypatch.setenv("EXOTEL_SID", "sid123")
    monkeypatch.setenv("EXOTEL_API_KEY", "key")
    monkeypatch.setenv("EXOTEL_API_TOKEN", "token")
    monkeypatch.setenv("EXOTEL_CALLER_ID", "0XXXXXXXXX")
    auth_client.put("/api/settings", json={"phone": ""})

    resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is False
    assert "settings" in data["message"].lower()


def test_exotel_dial_api_error_is_reported_not_raised(auth_client, monkeypatch):
    _configure_exotel_dial(monkeypatch, auth_client)
    error_resp = MagicMock(status_code=401)
    error_resp.json.return_value = {"RestException": {"Message": "Authentication failed"}}
    error_resp.text = '{"RestException": {"Message": "Authentication failed"}}'

    with patch("requests.post", return_value=error_resp):
        resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    assert "Authentication failed" in data["message"]
    # The attempt was still logged (a real dial was tried), just without a provider sid.
    assert data["call_id"] is not None


def test_exotel_status_webhook_updates_call_recording_and_outcome(auth_client, monkeypatch):
    _configure_exotel_dial(monkeypatch, auth_client)
    with patch("requests.post", return_value=_fake_exotel_response("CSidABC")):
        dial_resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    call_id = dial_resp.json()["call_id"]

    webhook_resp = auth_client.post(
        "/api/webhooks/exotel/status",
        data={
            "CustomField": str(call_id),
            "DialCallStatus": "completed",
            "DialCallDuration": "87",
            "RecordingUrl": "https://exotel-recordings.example.com/CSidABC.mp3",
        },
    )
    assert webhook_resp.status_code == 200

    logged = next(c for c in auth_client.get("/api/calls").json() if c["id"] == call_id)
    assert logged["outcome"] == "Connected"
    assert logged["duration_seconds"] == 87
    assert logged["recording_url"] == "https://exotel-recordings.example.com/CSidABC.mp3"


def test_exotel_status_webhook_no_answer_marks_unconnected(auth_client, monkeypatch):
    _configure_exotel_dial(monkeypatch, auth_client)
    with patch("requests.post", return_value=_fake_exotel_response("CSidXYZ")):
        dial_resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    call_id = dial_resp.json()["call_id"]

    webhook_resp = auth_client.post(
        "/api/webhooks/exotel/status",
        data={"CustomField": str(call_id), "DialCallStatus": "no-answer", "DialCallDuration": "0"},
    )
    assert webhook_resp.status_code == 200

    logged = next(c for c in auth_client.get("/api/calls").json() if c["id"] == call_id)
    assert logged["outcome"] == "No Answer"


def test_exotel_status_webhook_ignores_unknown_custom_field(auth_client):
    """Must not error even when CustomField doesn't match any real call (e.g. a stale/replayed
    callback) - the important thing is it never 500s back at Exotel."""
    resp = auth_client.post(
        "/api/webhooks/exotel/status",
        data={"CustomField": "999999", "DialCallStatus": "completed", "DialCallDuration": "10"},
    )
    assert resp.status_code == 200


def test_exotel_status_webhook_missing_custom_field_noops(auth_client):
    resp = auth_client.post("/api/webhooks/exotel/status", data={"DialCallStatus": "completed"})
    assert resp.status_code == 200
