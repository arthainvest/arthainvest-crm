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


def test_deal_process_status_persists(auth_client):
    resp = auth_client.get("/api/deals")
    deal = resp.json()[0]
    assert deal["process_status"] == "Login"  # default

    resp = auth_client.put(f"/api/deals/{deal['id']}/process-status", json={"process_status": "Sanction"})
    assert resp.status_code == 200
    assert resp.json()["process_status"] == "Sanction"

    resp = auth_client.get("/api/deals")
    updated = next(d for d in resp.json() if d["id"] == deal["id"])
    assert updated["process_status"] == "Sanction"


def test_deal_document_checklist_starts_empty(auth_client):
    resp = auth_client.get("/api/deals/1/documents")
    assert resp.status_code == 200
    assert resp.json() == []


def test_deal_document_checklist_persists_across_requests(auth_client):
    resp = auth_client.put("/api/deals/1/documents", json={"document_name": "PAN Card", "collected": True})
    assert resp.status_code == 200
    doc = resp.json()
    assert doc["deal_id"] == 1
    assert doc["document_name"] == "PAN Card"
    assert doc["collected"] is True
    assert doc["collected_at"] is not None

    resp = auth_client.get("/api/deals/1/documents")
    docs = resp.json()
    assert len(docs) == 1
    assert docs[0]["document_name"] == "PAN Card"
    assert docs[0]["collected"] is True


def test_deal_document_can_be_uncollected(auth_client):
    auth_client.put("/api/deals/1/documents", json={"document_name": "Aadhar Card", "collected": True})

    resp = auth_client.put("/api/deals/1/documents", json={"document_name": "Aadhar Card", "collected": False})
    assert resp.status_code == 200
    doc = resp.json()
    assert doc["collected"] is False
    assert doc["collected_at"] is None

    resp = auth_client.get("/api/deals/1/documents")
    docs = resp.json()
    assert len(docs) == 1  # upsert, not a second row
    assert docs[0]["collected"] is False


def test_deal_documents_are_scoped_per_deal(auth_client):
    auth_client.put("/api/deals/1/documents", json={"document_name": "PAN Card", "collected": True})
    auth_client.put("/api/deals/2/documents", json={"document_name": "PAN Card", "collected": True})
    auth_client.put("/api/deals/2/documents", json={"document_name": "Bank Statement", "collected": True})

    resp = auth_client.get("/api/deals/1/documents")
    assert len(resp.json()) == 1

    resp = auth_client.get("/api/deals/2/documents")
    assert len(resp.json()) == 2


def test_deal_documents_require_auth(client):
    resp = client.get("/api/deals/1/documents")
    assert resp.status_code == 401

    resp = client.put("/api/deals/1/documents", json={"document_name": "PAN Card", "collected": True})
    assert resp.status_code == 401


def test_update_document_unknown_deal_404s(auth_client):
    resp = auth_client.put("/api/deals/999999/documents", json={"document_name": "PAN Card", "collected": True})
    assert resp.status_code == 404


def test_delete_deal(auth_client):
    resp = auth_client.delete("/api/deals/1")
    assert resp.status_code == 200

    resp = auth_client.get("/api/deals")
    assert len(resp.json()) == 3
