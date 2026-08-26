def test_get_calls_filters_by_team_member(auth_client):
    calls = auth_client.get("/api/calls").json()
    rajesh = next(m for m in auth_client.get("/api/team").json() if m["name"] == "Rajesh Kumar")

    auth_client.put(f"/api/calls/{calls[0]['id']}/assign", json={"team_member_id": rajesh["id"]})

    resp = auth_client.get(f"/api/calls?team_member_id={rajesh['id']}")
    assert resp.status_code == 200
    ids = {c["id"] for c in resp.json()}
    assert calls[0]["id"] in ids
    assert all(c["team_member_id"] == rajesh["id"] for c in resp.json())

    unassigned_check = auth_client.get("/api/calls?team_member_id=9999")
    assert unassigned_check.json() == []


def test_get_calls_team_member_filter_includes_login_linked_legacy_calls(auth_client):
    """Team analytics (/api/analytics/team) counts a call for a member via team_member_id OR
    (created_by matches their linked login AND team_member_id is still null) - the seeded calls
    predate explicit assignment. The drill-down filter must use the exact same OR so a card's
    displayed "N Calls" figure never contradicts what the drill-down underneath it shows."""
    artha = next(m for m in auth_client.get("/api/team").json() if m["name"] == "Artha")
    productivity = next(r for r in auth_client.get("/api/analytics/team").json() if r["name"] == "Artha")

    resp = auth_client.get(f"/api/calls?team_member_id={artha['id']}")
    assert resp.status_code == 200
    assert len(resp.json()) == productivity["calls"]


def test_get_deals_filters_by_assigned_team_member_and_stage(auth_client):
    """Team/Reports pages' per-member drill-down uses stage=closed + assigned_team_member_id to
    explain the "Closed"/"Revenue" figures shown on the same card - the count and value-sum
    must match /api/analytics/team exactly (same OR-fallback: explicit assignment, or
    login-linked owner_id for legacy unassigned deals)."""
    rajesh = next(m for m in auth_client.get("/api/team").json() if m["name"] == "Rajesh Kumar")
    deal = auth_client.get("/api/deals").json()[0]
    auth_client.put(f"/api/deals/{deal['id']}/assign", json={"team_member_id": rajesh["id"]})
    auth_client.put(f"/api/deals/{deal['id']}/move", json={"stage": "closed"})

    resp = auth_client.get(f"/api/deals?stage=closed&assigned_team_member_id={rajesh['id']}")
    assert resp.status_code == 200
    ids = {d["id"] for d in resp.json()}
    assert deal["id"] in ids
    assert all(d["stage"] == "closed" for d in resp.json())

    productivity = next(r for r in auth_client.get("/api/analytics/team").json() if r["name"] == "Rajesh Kumar")
    drilldown = auth_client.get(f"/api/deals?stage=closed&assigned_team_member_id={rajesh['id']}").json()
    assert len(drilldown) == productivity["deals_closed"]
    assert sum(d["deal_value"] for d in drilldown) == productivity["revenue"]


def test_get_deals_team_member_filter_includes_login_linked_legacy_deals(auth_client):
    artha = next(m for m in auth_client.get("/api/team").json() if m["name"] == "Artha")
    deal = auth_client.get("/api/deals").json()[1]
    auth_client.put(f"/api/deals/{deal['id']}/move", json={"stage": "closed"})

    productivity = next(r for r in auth_client.get("/api/analytics/team").json() if r["name"] == "Artha")
    drilldown = auth_client.get(f"/api/deals?stage=closed&assigned_team_member_id={artha['id']}").json()
    assert len(drilldown) == productivity["deals_closed"]


def test_get_calls_without_filter_returns_all(auth_client):
    unfiltered = auth_client.get("/api/calls").json()
    all_again = auth_client.get("/api/calls").json()
    assert len(unfiltered) == len(all_again)


def test_team_member_drilldown_matches_assignment(auth_client):
    """The Team page's per-member drill-down (GET /api/leads, /api/contacts, /api/calls, each
    filtered by team member) must find exactly the records actually assigned to that person -
    proving the Team page's real records match what's really in the CRM, not a fabricated list."""
    suresh = next(m for m in auth_client.get("/api/team").json() if m["name"] == "Suresh Iyer")

    lead = auth_client.get("/api/leads").json()[0]
    contact = auth_client.get("/api/contacts").json()[0]
    auth_client.put(f"/api/leads/{lead['id']}/assign", json={"team_member_id": suresh["id"]})
    auth_client.put(f"/api/contacts/{contact['id']}/assign", json={"team_member_id": suresh["id"]})

    leads_resp = auth_client.get(f"/api/leads?assigned_team_member_id={suresh['id']}").json()
    contacts_resp = auth_client.get(f"/api/contacts?assigned_team_member_id={suresh['id']}").json()

    assert lead["id"] in {l["id"] for l in leads_resp}
    assert contact["id"] in {c["id"] for c in contacts_resp}
