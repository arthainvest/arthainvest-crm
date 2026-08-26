def test_voice_agent_call_requires_lead_or_contact(auth_client):
    import os
    os.environ["VAPI_API_KEY"] = "fake_key"
    os.environ["VAPI_ASSISTANT_ID"] = "fake_assistant"
    os.environ["VAPI_PHONE_NUMBER_ID"] = "fake_number"
    try:
        resp = auth_client.post("/api/voice-agent/call", json={"reason": "test"})
        assert resp.status_code == 400
    finally:
        for k in ["VAPI_API_KEY", "VAPI_ASSISTANT_ID", "VAPI_PHONE_NUMBER_ID"]:
            os.environ.pop(k, None)


def test_voice_agent_call_404s_for_unknown_lead(auth_client):
    import os
    os.environ["VAPI_API_KEY"] = "fake_key"
    os.environ["VAPI_ASSISTANT_ID"] = "fake_assistant"
    os.environ["VAPI_PHONE_NUMBER_ID"] = "fake_number"
    try:
        resp = auth_client.post("/api/voice-agent/call", json={"lead_id": 9999, "reason": "test"})
        assert resp.status_code == 404
    finally:
        for k in ["VAPI_API_KEY", "VAPI_ASSISTANT_ID", "VAPI_PHONE_NUMBER_ID"]:
            os.environ.pop(k, None)


def test_voice_agent_webhook_ignores_non_end_of_call_events(auth_client):
    resp = auth_client.post("/api/voice-agent/webhook", json={"message": {"type": "status-update"}})
    assert resp.status_code == 200
    assert resp.json() == {"received": True}


def test_voice_agent_webhook_logs_call_on_end_of_call_report(auth_client):
    """No matching voice_call_context row (this call id was never triggered through
    /api/voice-agent/call) - the call still logs, just unlinked, same as before."""
    before = auth_client.get("/api/calls").json()

    resp = auth_client.post("/api/voice-agent/webhook", json={
        "message": {
            "type": "end-of-call-report",
            "durationSeconds": 187,
            "endedReason": "customer-ended-call",
            "call": {"id": "untracked-call-id", "customer": {"name": "Rohan Test", "number": "+919999999999"}},
            "analysis": {"summary": "Booked a callback for Thursday."}
        }
    })
    assert resp.status_code == 200
    assert resp.json() == {"received": True}

    after = auth_client.get("/api/calls").json()
    assert len(after) == len(before) + 1

    logged = after[0]
    assert logged["name"] == "Rohan Test"
    assert logged["phone"] == "+919999999999"
    assert logged["duration_seconds"] == 187
    assert logged["outcome"] == "Booked a callback for Thursday."
    assert logged["type"] == "Voice Agent"
    assert logged["lead_id"] is None
    assert logged["contact_id"] is None


def test_voice_agent_call_then_webhook_logs_a_linked_call(auth_client, monkeypatch):
    """The real fix: triggering a Priti call for a lead, then Vapi's later webhook reporting
    the same call.id, must produce a `calls` row linked to that lead - showing up in the
    lead's own Activity Timeline - not a ghost record matched only by name/phone."""
    from unittest.mock import patch, MagicMock

    lead = auth_client.get("/api/leads").json()[0]
    monkeypatch.setenv("VAPI_API_KEY", "fake_key")
    monkeypatch.setenv("VAPI_ASSISTANT_ID", "fake_assistant")
    monkeypatch.setenv("VAPI_PHONE_NUMBER_ID", "fake_number")

    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"id": "vapi-call-42"})
        resp = auth_client.post("/api/voice-agent/call", json={"lead_id": lead["id"], "reason": "Renewal follow-up"})
    assert resp.status_code == 200
    assert resp.json()["configured"] is True
    assert resp.json()["vapi_call_id"] == "vapi-call-42"

    auth_client.post("/api/voice-agent/webhook", json={
        "message": {
            "type": "end-of-call-report",
            "durationSeconds": 94,
            "call": {"id": "vapi-call-42", "customer": {"name": lead["name"], "number": lead.get("phone")}},
            "analysis": {"summary": "Interested, wants a callback."}
        }
    })

    calls = auth_client.get("/api/calls").json()
    logged = next(c for c in calls if c.get("outcome") == "Interested, wants a callback.")
    assert logged["lead_id"] == lead["id"]
    assert logged["type"] == "Voice Agent"

    activities = auth_client.get(f"/api/activities?lead_id={lead['id']}").json()
    call_activity = next(a for a in activities if a["channel"] == "Call" and a["outcome"] == "Interested, wants a callback.")
    assert call_activity["lead_id"] == lead["id"]
