def test_list_leads_returns_seeded_data(auth_client):
    resp = auth_client.get("/api/leads")
    assert resp.status_code == 200
    leads = resp.json()
    assert len(leads) == 5
    assert {l["name"] for l in leads} == {
        "Neha Singh", "Vikram Reddy", "Anjali Desai", "Amit Patel", "Priya Kapoor"
    }


def test_create_lead(auth_client):
    resp = auth_client.post("/api/leads", json={
        "name": "Test Lead", "company": "Test Co", "phone": "9999999999", "product": "LAP"
    })
    assert resp.status_code == 200
    lead = resp.json()
    assert lead["name"] == "Test Lead"
    assert lead["status"] == "New"

    resp = auth_client.get("/api/leads")
    assert len(resp.json()) == 6


def test_get_single_lead(auth_client):
    resp = auth_client.get("/api/leads/1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Neha Singh"


def test_get_nonexistent_lead_404s(auth_client):
    resp = auth_client.get("/api/leads/9999")
    assert resp.status_code == 404


def test_update_lead_status_persists(auth_client):
    resp = auth_client.put("/api/leads/1", json={"status": "Contacted"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "Contacted"

    resp = auth_client.get("/api/leads/1")
    assert resp.json()["status"] == "Contacted"


def test_delete_lead(auth_client):
    resp = auth_client.delete("/api/leads/1")
    assert resp.status_code == 200

    resp = auth_client.get("/api/leads")
    assert len(resp.json()) == 4


def test_lead_source_roi_groups_by_source(auth_client):
    # Seeded leads all have no source - they should all land in "Not Specified".
    resp = auth_client.get("/api/analytics/lead-sources")
    assert resp.status_code == 200
    rows = resp.json()
    not_specified = next(r for r in rows if r["source"] == "Not Specified")
    assert not_specified["total_leads"] == 5
    assert not_specified["total_deals"] == 4  # 4 seeded deals, one each for leads 1-4

    # A new lead with a real source + a deal against it must show up as its own row.
    lead_resp = auth_client.post("/api/leads", json={"name": "Referral Lead", "source": "Referral"})
    lead_id = lead_resp.json()["id"]
    auth_client.post("/api/deals", json={"lead_id": lead_id, "deal_value": 400000})

    resp = auth_client.get("/api/analytics/lead-sources")
    rows = resp.json()
    referral = next(r for r in rows if r["source"] == "Referral")
    assert referral["total_leads"] == 1
    assert referral["total_deals"] == 1
    assert referral["total_deal_value"] == 400000
    assert referral["conversion_rate"] == 100.0


def test_lead_notes_crud(auth_client):
    resp = auth_client.post("/api/leads/2/notes", json={"transcript": "Discussed CIBIL score."})
    assert resp.status_code == 200
    note = resp.json()
    note_id = note["id"]
    assert note["transcript"] == "Discussed CIBIL score."

    resp = auth_client.get("/api/leads/2/notes")
    assert len(resp.json()) == 1

    resp = auth_client.put(f"/api/leads/2/notes/{note_id}", json={"transcript": "Updated note."})
    assert resp.status_code == 200
    assert resp.json()["transcript"] == "Updated note."

    resp = auth_client.delete(f"/api/leads/2/notes/{note_id}")
    assert resp.status_code == 200
    resp = auth_client.get("/api/leads/2/notes")
    assert len(resp.json()) == 0
