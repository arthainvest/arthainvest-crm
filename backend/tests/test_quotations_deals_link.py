def _first_deal(auth_client):
    return auth_client.get("/api/deals").json()[0]


def _first_lead(auth_client):
    return auth_client.get("/api/leads").json()[0]


def test_deal_starts_with_zero_quotations(auth_client):
    deal = _first_deal(auth_client)
    assert deal["quotation_count"] == 0

    listed = auth_client.get("/api/deals").json()
    assert next(d for d in listed if d["id"] == deal["id"])["quotation_count"] == 0


def test_create_quotation_linked_to_deal(auth_client):
    deal = _first_deal(auth_client)
    lead = auth_client.get(f"/api/leads/{deal['lead_id']}").json()

    resp = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"],
        "deal_id": deal["id"],
        "title": "Home Loan Quotation",
        "items": [{"description": "Processing Fee", "amount": 5000}],
    })
    assert resp.status_code == 200
    quotation = resp.json()
    assert quotation["deal_id"] == deal["id"]
    assert lead["name"] in quotation["deal_label"]
    assert deal["loan_product"] in quotation["deal_label"]

    deals = auth_client.get("/api/deals").json()
    assert next(d for d in deals if d["id"] == deal["id"])["quotation_count"] == 1


def test_quotation_resolves_company_through_its_linked_deal(auth_client):
    """Quotations have no company_id of their own - a linked deal's Company (deals.company_id)
    must resolve here too, so the Quotations page can show which company a quote is for
    without the user having to cross-reference the Pipeline/Companies pages by hand."""
    deal = _first_deal(auth_client)
    lead = auth_client.get(f"/api/leads/{deal['lead_id']}").json()
    company = auth_client.post("/api/companies", json={"name": "Quotation Co"}).json()
    auth_client.put(f"/api/deals/{deal['id']}/company", json={"company_id": company["id"]})

    resp = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deal["id"], "title": "LAP Quotation",
        "items": [{"description": "Processing Fee", "amount": 5000}],
    })
    assert resp.status_code == 200
    quotation = resp.json()
    assert quotation["company_id"] == company["id"]
    assert quotation["company_name"] == "Quotation Co"

    listed = auth_client.get("/api/quotations").json()
    fetched = next(q for q in listed if q["id"] == quotation["id"])
    assert fetched["company_name"] == "Quotation Co"


def test_quotation_resolves_assigned_team_member_through_its_linked_deal(auth_client):
    """Quotations have no assigned_team_member_id of their own - a linked deal's assigned team
    member (deals.assigned_team_member_id) must resolve here too, same as company_name, so the
    Quotations page can show who owns the underlying deal without cross-referencing Pipeline."""
    deal = _first_deal(auth_client)
    lead = auth_client.get(f"/api/leads/{deal['lead_id']}").json()
    rajesh = next(m for m in auth_client.get("/api/team").json() if m["name"] == "Rajesh Kumar")
    auth_client.put(f"/api/deals/{deal['id']}/assign", json={"team_member_id": rajesh["id"]})

    resp = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deal["id"], "title": "Team Member Quotation",
        "items": [{"description": "Fee", "amount": 750}],
    })
    assert resp.status_code == 200
    quotation = resp.json()
    assert quotation["assigned_team_member_id"] == rajesh["id"]
    assert quotation["assigned_team_member_name"] == "Rajesh Kumar"

    listed = auth_client.get("/api/quotations").json()
    fetched = next(q for q in listed if q["id"] == quotation["id"])
    assert fetched["assigned_team_member_name"] == "Rajesh Kumar"


def test_quotation_with_unassigned_deal_has_no_assigned_team_member(auth_client):
    deal = _first_deal(auth_client)
    lead = auth_client.get(f"/api/leads/{deal['lead_id']}").json()
    resp = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deal["id"], "title": "Unassigned Deal Quotation",
        "items": [{"description": "Fee", "amount": 250}],
    })
    assert resp.status_code == 200
    quotation = resp.json()
    assert quotation["assigned_team_member_id"] is None
    assert quotation["assigned_team_member_name"] is None


def test_quotation_with_no_deal_has_no_company(auth_client):
    lead = _first_lead(auth_client)
    resp = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "No Deal Quotation",
        "items": [{"description": "Fee", "amount": 1000}],
    })
    assert resp.status_code == 200
    quotation = resp.json()
    assert quotation["company_id"] is None
    assert quotation["company_name"] is None


def test_get_deal_quotations_returns_linked_quotations(auth_client):
    deal = _first_deal(auth_client)
    lead = auth_client.get(f"/api/leads/{deal['lead_id']}").json()

    q1 = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deal["id"], "title": "Quote A", "items": [{"description": "X", "amount": 100}]
    }).json()
    q2 = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "deal_id": deal["id"], "title": "Quote B", "items": [{"description": "Y", "amount": 200}]
    }).json()
    # A quotation not linked to any deal must not show up in the reverse lookup.
    auth_client.post("/api/quotations", json={"lead_id": lead["id"], "title": "Unlinked Quote", "items": []})

    resp = auth_client.get(f"/api/deals/{deal['id']}/quotations")
    assert resp.status_code == 200
    linked = resp.json()
    assert {q["id"] for q in linked} == {q1["id"], q2["id"]}


def test_get_deal_quotations_404s_for_unknown_deal(auth_client):
    resp = auth_client.get("/api/deals/9999/quotations")
    assert resp.status_code == 404


def test_quotation_without_deal_has_no_label(auth_client):
    lead = _first_lead(auth_client)
    resp = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "No Deal Quote", "items": []
    })
    assert resp.status_code == 200
    quotation = resp.json()
    assert quotation["deal_id"] is None
    assert quotation["deal_label"] is None


def test_link_deal_to_quotation_via_update(auth_client):
    lead = _first_lead(auth_client)
    deal = _first_deal(auth_client)
    quotation = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "Test Quote", "items": []
    }).json()
    assert quotation["deal_id"] is None

    resp = auth_client.put(f"/api/quotations/{quotation['id']}", json={"deal_id": deal["id"]})
    assert resp.status_code == 200
    assert resp.json()["deal_id"] == deal["id"]
    assert resp.json()["deal_label"] is not None

    deals = auth_client.get("/api/deals").json()
    assert next(d for d in deals if d["id"] == deal["id"])["quotation_count"] == 1
