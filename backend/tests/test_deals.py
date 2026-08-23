def test_list_deals_returns_seeded_data(auth_client):
    resp = auth_client.get("/api/deals")
    assert resp.status_code == 200
    assert len(resp.json()) == 4


def test_create_deal_defaults_to_lap(auth_client):
    resp = auth_client.post("/api/deals", json={"lead_id": 1, "deal_value": 500000})
    assert resp.status_code == 200
    deal = resp.json()
    assert deal["loan_product"] == "LAP"
    assert deal["stage"] == "new"


def test_create_deal_with_explicit_loan_product(auth_client):
    resp = auth_client.post("/api/deals", json={
        "lead_id": 1, "deal_value": 200000, "loan_product": "Business", "stage": "Proposal"
    })
    assert resp.status_code == 200
    deal = resp.json()
    assert deal["loan_product"] == "Business"
    assert deal["stage"] == "proposal"


def test_move_deal_stage(auth_client):
    resp = auth_client.put("/api/deals/1/move", json={"stage": "negotiation"})
    assert resp.status_code == 200

    resp = auth_client.get("/api/deals")
    deal = next(d for d in resp.json() if d["id"] == 1)
    assert deal["stage"] == "negotiation"


def test_delete_deal(auth_client):
    resp = auth_client.delete("/api/deals/1")
    assert resp.status_code == 200

    resp = auth_client.get("/api/deals")
    assert len(resp.json()) == 3
