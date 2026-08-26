def test_get_deals_filters_by_lead_id(auth_client):
    """The Leads page's Notes & Follow-up modal shows a 'Deals' section using this filter, so a
    lead already converted into a deal (deals.lead_id) is visible from the Leads page itself,
    not just from Pipeline."""
    deals = auth_client.get("/api/deals").json()
    target_lead_id = deals[0]["lead_id"]

    resp = auth_client.get(f"/api/deals?lead_id={target_lead_id}")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert all(d["lead_id"] == target_lead_id for d in results)


def test_get_deals_filters_by_lead_id_finds_nothing_for_unconverted_lead(auth_client):
    all_leads = auth_client.get("/api/leads").json()
    deals = auth_client.get("/api/deals").json()
    converted_lead_ids = {d["lead_id"] for d in deals}
    unconverted = next((l for l in all_leads if l["id"] not in converted_lead_ids), None)
    if unconverted is None:
        return  # every seeded lead already has a deal - nothing to assert here

    resp = auth_client.get(f"/api/deals?lead_id={unconverted['id']}")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_deals_lead_id_and_stage_filters_combine(auth_client):
    deals = auth_client.get("/api/deals").json()
    target = deals[0]

    resp = auth_client.get(f"/api/deals?lead_id={target['lead_id']}&stage={target['stage']}")
    assert resp.status_code == 200
    assert target["id"] in {d["id"] for d in resp.json()}

    other_stage = "closed" if target["stage"] != "closed" else "new"
    mismatched = auth_client.get(f"/api/deals?lead_id={target['lead_id']}&stage={other_stage}")
    assert target["id"] not in {d["id"] for d in mismatched.json()}


def test_get_deals_without_lead_id_filter_returns_all(auth_client):
    unfiltered = auth_client.get("/api/deals").json()
    all_again = auth_client.get("/api/deals").json()
    assert len(unfiltered) == len(all_again)
