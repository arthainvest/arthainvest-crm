"""Every external-service endpoint must return configured: False with a clear message when
its credentials aren't set, rather than raising an error - this is what lets the frontend fall
back cleanly (tel:/wa.me/mailto: links) instead of showing a broken feature. conftest.py strips
all credential env vars before each test, so these always exercise the unconfigured path."""

from unittest.mock import patch, MagicMock


def test_twilio_dial_unconfigured(auth_client):
    resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is False
    assert "not configured" in data["message"].lower() or "no calling provider" in data["message"].lower()


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


def test_generate_marketing_content_unconfigured(auth_client):
    resp = auth_client.post("/api/marketing/generate-content", json={"occasion": "Diwali", "platform": "WhatsApp"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is False
    assert data["content"] is None


def test_marketing_content_falls_back_to_openai_when_claude_unconfigured(auth_client, monkeypatch):
    """With ANTHROPIC_API_KEY unset (stripped by conftest) but OPENAI_API_KEY present, the
    shared _call_ai_text helper must route to OpenAI instead of returning unconfigured."""
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai-key-for-test")
    fake_response = MagicMock()
    fake_response.choices = [MagicMock(message=MagicMock(content="Happy Diwali from ArthaInvest!"))]

    with patch("openai.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value.chat.completions.create.return_value = fake_response
        resp = auth_client.post("/api/marketing/generate-content", json={"occasion": "Diwali", "platform": "WhatsApp"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    assert data["content"] == "Happy Diwali from ArthaInvest!"
    assert "OpenAI" in data["message"]


def test_ai_suggestion_falls_back_to_openai_when_claude_fails(auth_client, monkeypatch):
    """With ANTHROPIC_API_KEY set but the Claude call itself failing (e.g. low credit balance),
    and OPENAI_API_KEY also set, the fallback must still produce a usable suggestion rather
    than surfacing the Claude error."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-anthropic-key-for-test")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai-key-for-test")

    auth_client.post("/api/leads/1/notes", json={"transcript": "Client wants to review the home loan next week."})

    fake_response = MagicMock()
    fake_response.choices = [MagicMock(message=MagicMock(content="Follow up about the home loan terms."))]

    with patch("anthropic.Anthropic") as mock_anthropic_cls, patch("openai.OpenAI") as mock_openai_cls:
        mock_anthropic_cls.return_value.messages.create.side_effect = Exception("credit balance too low")
        mock_openai_cls.return_value.chat.completions.create.return_value = fake_response
        resp = auth_client.post("/api/leads/1/ai-suggest")

    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    assert data["suggestion"] == "Follow up about the home loan terms."
    assert "OpenAI" in data["message"]


def test_ai_chat_unconfigured(auth_client):
    resp = auth_client.post("/api/ai/chat", json={"message": "How many leads do I have?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is False
    assert data["reply"] is None


def test_ai_chat_answers_from_real_data_snapshot(auth_client, monkeypatch):
    """The chatbot must actually build and send a snapshot of the seeded CRM data - not just
    return a canned response - so a mocked model call still exercises the real DB query path."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-anthropic-key-for-test")

    fake_content_block = MagicMock()
    fake_content_block.text = "You have 5 leads."
    fake_response = MagicMock()
    fake_response.content = [fake_content_block]

    with patch("anthropic.Anthropic") as mock_anthropic_cls:
        mock_anthropic_cls.return_value.messages.create.return_value = fake_response
        resp = auth_client.post("/api/ai/chat", json={"message": "How many leads do I have?"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    assert data["reply"] == "You have 5 leads."

    # The snapshot (seeded lead data) must have actually been sent to the model.
    call_kwargs = mock_anthropic_cls.return_value.messages.create.call_args.kwargs
    assert "LEADS" in call_kwargs["system"]


def test_voice_agent_call_unconfigured(auth_client):
    resp = auth_client.post("/api/voice-agent/call", json={"lead_id": 1, "reason": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is False
    assert "not configured" in data["message"].lower()


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
