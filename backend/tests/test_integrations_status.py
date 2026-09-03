def test_status_shows_all_unconfigured_by_default(auth_client):
    """conftest strips every credential env var, so every real-status row should read as
    not configured/not connected - this is the whole point of the endpoint existing: showing
    the truth instead of a cosmetic DB toggle that could say anything."""
    resp = auth_client.get("/api/integrations/status")
    assert resp.status_code == 200
    data = resp.json()

    for name in ["WhatsApp Business API", "Twilio", "Exotel", "Email Service", "Mailchimp", "Claude AI", "LinkedIn", "Google Sheets", "Gmail", "Google Calendar", "Zapier", "Slack"]:
        assert name in data
        assert data[name]["configured"] is False


def test_status_reflects_configured_env_vars(auth_client, monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", "fake-token")
    monkeypatch.setenv("WHATSAPP_PHONE_ID", "fake-phone-id")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-anthropic-key")

    data = auth_client.get("/api/integrations/status").json()
    assert data["WhatsApp Business API"]["configured"] is True
    assert data["Claude AI"]["configured"] is True
    # Untouched vars stay false - proves each row is checked independently, not one blanket flag
    assert data["Twilio"]["configured"] is False
    assert data["Mailchimp"]["configured"] is False


def test_status_requires_all_twilio_vars_together(auth_client, monkeypatch):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "fake-sid")
    # auth_token and from_number deliberately left unset
    data = auth_client.get("/api/integrations/status").json()
    assert data["Twilio"]["configured"] is False


def test_status_mailchimp_requires_dash_in_api_key(auth_client, monkeypatch):
    """Mirrors the same real check the sync endpoint itself uses - a Mailchimp key always
    contains a server-prefix suffix after a dash (e.g. abc123-us21); one without it can't be
    a real key even if both env vars are technically set."""
    monkeypatch.setenv("MAILCHIMP_API_KEY", "notarealkeywithoutadash")
    monkeypatch.setenv("MAILCHIMP_AUDIENCE_ID", "fake-audience")
    data = auth_client.get("/api/integrations/status").json()
    assert data["Mailchimp"]["configured"] is False

    monkeypatch.setenv("MAILCHIMP_API_KEY", "fakekey123-us21")
    data = auth_client.get("/api/integrations/status").json()
    assert data["Mailchimp"]["configured"] is True


def test_status_reflects_real_google_sheets_connection(auth_client, client, monkeypatch):
    from unittest.mock import patch, MagicMock
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "fake-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "fake-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/integrations/google/callback")

    fake_token_response = MagicMock()
    fake_token_response.json.return_value = {"access_token": "a", "refresh_token": "r", "expires_in": 3600}
    fake_token_response.raise_for_status = MagicMock()
    fake_userinfo_response = MagicMock()
    fake_userinfo_response.json.return_value = {"email": "advisor@example.com"}
    fake_userinfo_response.raise_for_status = MagicMock()

    assert auth_client.get("/api/integrations/status").json()["Google Sheets"]["configured"] is False

    with patch("requests.post", return_value=fake_token_response), \
         patch("requests.get", return_value=fake_userinfo_response):
        client.get("/api/integrations/google/callback", params={"code": "c", "state": auth_client._token}, follow_redirects=False)

    data = auth_client.get("/api/integrations/status").json()
    assert data["Google Sheets"]["configured"] is True
    assert data["Google Sheets"]["detail"] == "advisor@example.com"
