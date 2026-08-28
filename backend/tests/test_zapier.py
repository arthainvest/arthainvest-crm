from unittest.mock import patch, MagicMock


def test_create_list_delete_webhook(auth_client):
    resp = auth_client.post("/api/integrations/zapier/webhooks", json={
        "url": "https://hooks.zapier.com/hooks/catch/123/abc/", "event_type": "lead.created"
    })
    assert resp.status_code == 200
    webhook = resp.json()
    assert webhook["url"] == "https://hooks.zapier.com/hooks/catch/123/abc/"
    assert webhook["event_type"] == "lead.created"
    assert webhook["last_triggered_at"] is None

    resp = auth_client.get("/api/integrations/zapier/webhooks")
    assert resp.status_code == 200
    assert any(w["id"] == webhook["id"] for w in resp.json())

    resp = auth_client.delete(f"/api/integrations/zapier/webhooks/{webhook['id']}")
    assert resp.status_code == 200
    assert not any(w["id"] == webhook["id"] for w in auth_client.get("/api/integrations/zapier/webhooks").json())


def test_create_webhook_rejects_bad_event_type(auth_client):
    resp = auth_client.post("/api/integrations/zapier/webhooks", json={
        "url": "https://hooks.zapier.com/hooks/catch/123/abc/", "event_type": "not.a.real.event"
    })
    assert resp.status_code == 400


def test_delete_nonexistent_webhook_404s(auth_client):
    resp = auth_client.delete("/api/integrations/zapier/webhooks/9999")
    assert resp.status_code == 404


def test_lead_created_fires_matching_webhooks(auth_client):
    auth_client.post("/api/integrations/zapier/webhooks", json={
        "url": "https://hooks.zapier.com/leads-hook", "event_type": "lead.created"
    })
    auth_client.post("/api/integrations/zapier/webhooks", json={
        "url": "https://hooks.zapier.com/deals-only-hook", "event_type": "deal.closed"
    })

    fake_response = MagicMock(status_code=200)
    with patch("requests.post", return_value=fake_response) as mock_post:
        resp = auth_client.post("/api/leads", json={"name": "Zapier Test Lead", "source": "Referral"})
        assert resp.status_code == 200

    # Only the lead.created hook should have fired, not the deal.closed-only one
    assert mock_post.call_count == 1
    call_url = mock_post.call_args.args[0]
    assert call_url == "https://hooks.zapier.com/leads-hook"
    body = mock_post.call_args.kwargs["json"]
    assert body["event"] == "lead.created"
    assert body["data"]["name"] == "Zapier Test Lead"

    hooks = {h["url"]: h for h in auth_client.get("/api/integrations/zapier/webhooks").json()}
    assert hooks["https://hooks.zapier.com/leads-hook"]["last_status"] == "success"
    assert hooks["https://hooks.zapier.com/leads-hook"]["last_triggered_at"] is not None
    assert hooks["https://hooks.zapier.com/deals-only-hook"]["last_triggered_at"] is None


def test_deal_closed_fires_only_on_genuine_transition(auth_client):
    auth_client.post("/api/integrations/zapier/webhooks", json={
        "url": "https://hooks.zapier.com/deals-hook", "event_type": "deal.closed"
    })

    fake_response = MagicMock(status_code=200)
    with patch("requests.post", return_value=fake_response) as mock_post:
        # Deal 1 starts at 'new' - moving to 'negotiation' must not fire deal.closed
        resp = auth_client.put("/api/deals/1/move", json={"stage": "negotiation"})
        assert resp.status_code == 200
        assert mock_post.call_count == 0

        # Moving into 'closed' for the first time fires exactly once
        resp = auth_client.put("/api/deals/1/move", json={"stage": "closed"})
        assert resp.status_code == 200
        assert mock_post.call_count == 1
        body = mock_post.call_args.kwargs["json"]
        assert body["event"] == "deal.closed"
        assert body["data"]["id"] == 1

        # Re-saving while already closed must not re-fire
        resp = auth_client.put("/api/deals/1/move", json={"stage": "closed"})
        assert resp.status_code == 200
        assert mock_post.call_count == 1


def test_all_event_type_fires_for_every_event(auth_client):
    auth_client.post("/api/integrations/zapier/webhooks", json={
        "url": "https://hooks.zapier.com/all-hook", "event_type": "all"
    })

    fake_response = MagicMock(status_code=200)
    with patch("requests.post", return_value=fake_response) as mock_post:
        auth_client.post("/api/leads", json={"name": "All Event Lead", "source": "Referral"})
        auth_client.put("/api/deals/1/move", json={"stage": "closed"})

    assert mock_post.call_count == 2


def test_no_registered_webhooks_is_a_silent_noop(auth_client):
    with patch("requests.post") as mock_post:
        resp = auth_client.post("/api/leads", json={"name": "No Hooks Lead", "source": "Referral"})
        assert resp.status_code == 200
        assert mock_post.call_count == 0


def test_failed_delivery_records_failure_status_without_erroring_the_request(auth_client):
    auth_client.post("/api/integrations/zapier/webhooks", json={
        "url": "https://hooks.zapier.com/broken-hook", "event_type": "lead.created"
    })

    with patch("requests.post", side_effect=Exception("connection refused")):
        resp = auth_client.post("/api/leads", json={"name": "Broken Hook Lead", "source": "Referral"})
        assert resp.status_code == 200

    hooks = auth_client.get("/api/integrations/zapier/webhooks").json()
    hook = next(h for h in hooks if h["url"] == "https://hooks.zapier.com/broken-hook")
    assert "failed" in hook["last_status"]
