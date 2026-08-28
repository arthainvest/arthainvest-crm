from unittest.mock import patch, MagicMock


def test_create_list_delete_webhook(auth_client):
    resp = auth_client.post("/api/integrations/slack/webhooks", json={
        "url": "https://hooks.slack.com/services/T00/B00/xxxxxxxx", "event_type": "lead.created"
    })
    assert resp.status_code == 200
    webhook = resp.json()
    assert webhook["url"] == "https://hooks.slack.com/services/T00/B00/xxxxxxxx"
    assert webhook["event_type"] == "lead.created"
    assert webhook["last_triggered_at"] is None

    resp = auth_client.get("/api/integrations/slack/webhooks")
    assert resp.status_code == 200
    assert any(w["id"] == webhook["id"] for w in resp.json())

    resp = auth_client.delete(f"/api/integrations/slack/webhooks/{webhook['id']}")
    assert resp.status_code == 200
    assert not any(w["id"] == webhook["id"] for w in auth_client.get("/api/integrations/slack/webhooks").json())


def test_create_webhook_rejects_bad_event_type(auth_client):
    resp = auth_client.post("/api/integrations/slack/webhooks", json={
        "url": "https://hooks.slack.com/services/T00/B00/xxxxxxxx", "event_type": "not.a.real.event"
    })
    assert resp.status_code == 400


def test_delete_nonexistent_webhook_404s(auth_client):
    resp = auth_client.delete("/api/integrations/slack/webhooks/9999")
    assert resp.status_code == 404


def test_status_reflects_registered_webhooks(auth_client):
    assert auth_client.get("/api/integrations/status").json()["Slack"]["configured"] is False

    auth_client.post("/api/integrations/slack/webhooks", json={
        "url": "https://hooks.slack.com/services/T00/B00/xxxxxxxx", "event_type": "all"
    })
    data = auth_client.get("/api/integrations/status").json()
    assert data["Slack"]["configured"] is True
    assert "1 webhook" in data["Slack"]["detail"]


def test_lead_created_sends_formatted_slack_message(auth_client):
    auth_client.post("/api/integrations/slack/webhooks", json={
        "url": "https://hooks.slack.com/services/leads-channel", "event_type": "lead.created"
    })
    auth_client.post("/api/integrations/slack/webhooks", json={
        "url": "https://hooks.slack.com/services/deals-only-channel", "event_type": "deal.closed"
    })

    fake_response = MagicMock(status_code=200)
    with patch("requests.post", return_value=fake_response) as mock_post:
        resp = auth_client.post("/api/leads", json={
            "name": "Slack Test Lead", "company": "Acme Corp", "source": "Referral"
        })
        assert resp.status_code == 200

    assert mock_post.call_count == 1
    call_url = mock_post.call_args.args[0]
    assert call_url == "https://hooks.slack.com/services/leads-channel"
    body = mock_post.call_args.kwargs["json"]
    assert "Slack Test Lead" in body["text"]
    assert "Acme Corp" in body["text"]

    hooks = {h["url"]: h for h in auth_client.get("/api/integrations/slack/webhooks").json()}
    assert hooks["https://hooks.slack.com/services/leads-channel"]["last_status"] == "success"
    assert hooks["https://hooks.slack.com/services/deals-only-channel"]["last_triggered_at"] is None


def test_deal_closed_fires_only_on_genuine_transition(auth_client):
    auth_client.post("/api/integrations/slack/webhooks", json={
        "url": "https://hooks.slack.com/services/deals-channel", "event_type": "deal.closed"
    })

    fake_response = MagicMock(status_code=200)
    with patch("requests.post", return_value=fake_response) as mock_post:
        resp = auth_client.put("/api/deals/1/move", json={"stage": "negotiation"})
        assert resp.status_code == 200
        assert mock_post.call_count == 0

        resp = auth_client.put("/api/deals/1/move", json={"stage": "closed"})
        assert resp.status_code == 200
        assert mock_post.call_count == 1
        body = mock_post.call_args.kwargs["json"]
        assert "Deal closed" in body["text"]

        resp = auth_client.put("/api/deals/1/move", json={"stage": "closed"})
        assert resp.status_code == 200
        assert mock_post.call_count == 1


def test_no_registered_webhooks_is_a_silent_noop(auth_client):
    with patch("requests.post") as mock_post:
        resp = auth_client.post("/api/leads", json={"name": "No Slack Hooks Lead", "source": "Referral"})
        assert resp.status_code == 200
        assert mock_post.call_count == 0


def test_failed_delivery_records_failure_status_without_erroring_the_request(auth_client):
    auth_client.post("/api/integrations/slack/webhooks", json={
        "url": "https://hooks.slack.com/services/broken-channel", "event_type": "lead.created"
    })

    with patch("requests.post", side_effect=Exception("connection refused")):
        resp = auth_client.post("/api/leads", json={"name": "Broken Slack Hook Lead", "source": "Referral"})
        assert resp.status_code == 200

    hooks = auth_client.get("/api/integrations/slack/webhooks").json()
    hook = next(h for h in hooks if h["url"] == "https://hooks.slack.com/services/broken-channel")
    assert "failed" in hook["last_status"]


def test_zapier_and_slack_both_fire_independently_for_the_same_event(auth_client):
    """Zapier and Slack webhooks are separate tables/endpoints entirely - registering one
    shouldn't affect the other, and both should fire off the same lead.created event."""
    auth_client.post("/api/integrations/zapier/webhooks", json={
        "url": "https://hooks.zapier.com/hooks/catch/1/a/", "event_type": "lead.created"
    })
    auth_client.post("/api/integrations/slack/webhooks", json={
        "url": "https://hooks.slack.com/services/both-test", "event_type": "lead.created"
    })

    fake_response = MagicMock(status_code=200)
    with patch("requests.post", return_value=fake_response) as mock_post:
        auth_client.post("/api/leads", json={"name": "Both Hooks Lead", "source": "Referral"})

    assert mock_post.call_count == 2
    called_urls = {call.args[0] for call in mock_post.call_args_list}
    assert called_urls == {"https://hooks.zapier.com/hooks/catch/1/a/", "https://hooks.slack.com/services/both-test"}
