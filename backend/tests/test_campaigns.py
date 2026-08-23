def test_list_campaigns_computes_engagement_and_progress(auth_client):
    resp = auth_client.get("/api/campaigns")
    assert resp.status_code == 200
    campaigns = resp.json()
    assert len(campaigns) == 3

    insurance_awareness = next(c for c in campaigns if c["name"] == "Insurance Awareness")
    # 450 clicks / 3000 recipients = 15%
    assert insurance_awareness["engagement"] == 15
    assert insurance_awareness["status"] == "Active"
    # Active (not Completed) -> progress is opens/recipients, not 100
    assert insurance_awareness["progress"] != 100

    completed = next(c for c in campaigns if c["status"] == "Completed")
    assert completed["progress"] == 100


def test_create_update_delete_campaign(auth_client):
    resp = auth_client.post("/api/campaigns", json={"name": "New Campaign", "recipients": 1000})
    assert resp.status_code == 200
    campaign_id = resp.json()["id"]
    assert resp.json()["type"] == "Email"  # default

    resp = auth_client.put(f"/api/campaigns/{campaign_id}", json={"status": "Completed"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "Completed"
    assert resp.json()["progress"] == 100

    resp = auth_client.delete(f"/api/campaigns/{campaign_id}")
    assert resp.status_code == 200

    resp = auth_client.get("/api/campaigns")
    assert len(resp.json()) == 3
