def test_list_integrations_catalog(auth_client):
    resp = auth_client.get("/api/integrations")
    assert resp.status_code == 200
    integrations = resp.json()
    assert len(integrations) == 24

    names = {i["name"] for i in integrations}
    assert "Razorpay Payments" not in names  # explicitly removed, must never reappear
    assert {"Twilio", "Claude AI", "WhatsApp Business API", "Mailchimp",
            "DigiLocker", "Google Analytics", "Priti (AI Voice Caller)", "OpenAI",
            "Facebook Lead Ads", "IndiaMart", "TradeIndia", "Zendesk",
            "QuickBooks", "Aircall", "MSG91", "Apollo.io"}.issubset(names)


def test_toggle_integration(auth_client):
    resp = auth_client.get("/api/integrations")
    slack = next(i for i in resp.json() if i["name"] == "Slack")
    assert slack["connected"] is False

    resp = auth_client.put(f"/api/integrations/{slack['id']}/toggle", json={"connected": True})
    assert resp.status_code == 200
    assert resp.json()["connected"] is True
    assert resp.json()["last_sync"] == "now"

    resp = auth_client.put(f"/api/integrations/{slack['id']}/toggle", json={"connected": False})
    assert resp.json()["connected"] is False
    assert resp.json()["last_sync"] == "never"


def test_toggle_nonexistent_integration_404s(auth_client):
    resp = auth_client.put("/api/integrations/9999/toggle", json={"connected": True})
    assert resp.status_code == 404
