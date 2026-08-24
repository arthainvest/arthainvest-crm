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
    before = auth_client.get("/api/calls").json()

    resp = auth_client.post("/api/voice-agent/webhook", json={
        "message": {
            "type": "end-of-call-report",
            "durationSeconds": 187,
            "endedReason": "customer-ended-call",
            "call": {"customer": {"name": "Rohan Test", "number": "+919999999999"}},
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
    assert logged["type"] == "Outbound"
