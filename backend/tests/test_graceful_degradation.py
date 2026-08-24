"""Every external-service endpoint must return configured: False with a clear message when
its credentials aren't set, rather than raising an error - this is what lets the frontend fall
back cleanly (tel:/wa.me/mailto: links) instead of showing a broken feature. conftest.py strips
all credential env vars before each test, so these always exercise the unconfigured path."""


def test_twilio_dial_unconfigured(auth_client):
    resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is False
    assert "not configured" in data["message"].lower()


def test_twilio_sms_unconfigured(auth_client):
    resp = auth_client.post("/api/sms/send", json={"to": "+911234567890", "message": "hi"})
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_whatsapp_unconfigured(auth_client):
    resp = auth_client.post("/api/whatsapp/send", json={"to": "+911234567890", "message": "hi"})
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_email_unconfigured(auth_client):
    resp = auth_client.post("/api/email/send", json={"to": "a@b.com", "subject": "s", "body": "b"})
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_mailchimp_sync_unconfigured(auth_client):
    resp = auth_client.post("/api/marketing/mailchimp/sync")
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_claude_ai_suggest_unconfigured_for_contact(auth_client):
    resp = auth_client.post("/api/contacts/1/ai-suggest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is False
    assert data["suggestion"] is None


def test_claude_ai_suggest_unconfigured_for_lead(auth_client):
    resp = auth_client.post("/api/leads/1/ai-suggest")
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_linkedin_connect_unconfigured(auth_client):
    resp = auth_client.get("/api/integrations/linkedin/connect")
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is False
    assert data["auth_url"] is None


def test_linkedin_post_not_connected(auth_client):
    """Even with LINKEDIN_CLIENT_ID/SECRET set, posting must fail gracefully (not crash) if
    this particular user never completed the OAuth connect flow."""
    resp = auth_client.post("/api/marketing/linkedin/post", json={"text": "Hello LinkedIn"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is False
    assert "connect" in data["message"].lower()


def test_dial_requires_agent_phone_number(auth_client):
    """Even with Twilio env vars set, dialing must fail gracefully (not crash) if the agent
    hasn't saved their own phone number in Settings yet."""
    import os
    os.environ["TWILIO_ACCOUNT_SID"] = "fake_sid"
    os.environ["TWILIO_AUTH_TOKEN"] = "fake_token"
    os.environ["TWILIO_FROM_NUMBER"] = "+15551234567"
    try:
        auth_client.put("/api/settings", json={"phone": ""})
        resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["configured"] is False
        assert "settings" in data["message"].lower()
    finally:
        for k in ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER"]:
            os.environ.pop(k, None)
