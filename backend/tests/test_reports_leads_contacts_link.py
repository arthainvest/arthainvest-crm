def test_get_leads_filters_by_source(auth_client):
    all_leads = auth_client.get("/api/leads").json()
    source_leads = [l for l in all_leads if (l.get("source") or "").strip()]
    if not source_leads:
        # Seed data has no source set - create one so the filter has something real to prove.
        created = auth_client.post("/api/leads", json={"name": "Sourced Lead", "source": "Website"}).json()
        resp = auth_client.get("/api/leads?source=Website")
        assert resp.status_code == 200
        ids = {l["id"] for l in resp.json()}
        assert created["id"] in ids
        other = auth_client.get("/api/leads?source=Referral")
        assert created["id"] not in {l["id"] for l in other.json()}
    else:
        target_source = source_leads[0]["source"]
        resp = auth_client.get(f"/api/leads?source={target_source}")
        assert resp.status_code == 200
        assert all(l["source"] == target_source for l in resp.json())


def test_get_leads_filters_by_not_specified_source(auth_client):
    """Matches the same COALESCE(NULLIF(TRIM(source), ''), 'Not Specified') grouping the Lead
    Source ROI report uses, so drilling into a 'Not Specified' row finds the right leads."""
    blank_lead = auth_client.post("/api/leads", json={"name": "No Source Lead"}).json()
    assert blank_lead.get("source") is None

    resp = auth_client.get("/api/leads?source=Not Specified")
    assert resp.status_code == 200
    ids = {l["id"] for l in resp.json()}
    assert blank_lead["id"] in ids


def test_get_leads_filters_by_assigned_team_member(auth_client):
    lead = auth_client.get("/api/leads").json()[0]
    rajesh = next(m for m in auth_client.get("/api/team").json() if m["name"] == "Rajesh Kumar")
    auth_client.put(f"/api/leads/{lead['id']}/assign", json={"team_member_id": rajesh["id"]})

    resp = auth_client.get(f"/api/leads?assigned_team_member_id={rajesh['id']}")
    assert resp.status_code == 200
    ids = {l["id"] for l in resp.json()}
    assert lead["id"] in ids

    unassigned_check = auth_client.get("/api/leads?assigned_team_member_id=9999")
    assert unassigned_check.json() == []


def test_get_contacts_filters_by_assigned_team_member(auth_client):
    contact = auth_client.get("/api/contacts").json()[0]
    suresh = next(m for m in auth_client.get("/api/team").json() if m["name"] == "Suresh Iyer")
    auth_client.put(f"/api/contacts/{contact['id']}/assign", json={"team_member_id": suresh["id"]})

    resp = auth_client.get(f"/api/contacts?assigned_team_member_id={suresh['id']}")
    assert resp.status_code == 200
    ids = {c["id"] for c in resp.json()}
    assert contact["id"] in ids

    other = auth_client.get("/api/contacts")
    assert len(other.json()) >= len(resp.json())


def test_get_contacts_without_filter_returns_all(auth_client):
    unfiltered = auth_client.get("/api/contacts").json()
    all_again = auth_client.get("/api/contacts").json()
    assert len(unfiltered) == len(all_again)


def test_lead_source_drilldown_matches_lead_source_roi_counts(auth_client):
    """The Reports page drill-down (GET /api/leads?source=X) must return exactly as many rows
    as the aggregate report says exist for that source - otherwise the drill-down would lie
    about what it's showing."""
    auth_client.post("/api/leads", json={"name": "A", "source": "Google Ads"})
    auth_client.post("/api/leads", json={"name": "B", "source": "Google Ads"})

    roi = auth_client.get("/api/analytics/lead-sources").json()
    google_row = next(r for r in roi if r["source"] == "Google Ads")

    drilldown = auth_client.get("/api/leads?source=Google Ads").json()
    assert len(drilldown) == google_row["total_leads"]
