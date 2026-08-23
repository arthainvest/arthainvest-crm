def test_list_team_returns_seeded_roster(auth_client):
    resp = auth_client.get("/api/team")
    assert resp.status_code == 200
    team = resp.json()
    assert len(team) == 7

    roles = [m["role"] for m in team]
    assert roles.count("admin") == 2
    assert roles.count("team_lead") == 1
    assert roles.count("location_head") == 1
    assert roles.count("employee") == 3
    # sorted by role hierarchy: admins first
    assert team[0]["role"] == "admin"


def test_create_update_delete_team_member(auth_client):
    resp = auth_client.post("/api/team", json={"name": "New Hire", "role": "employee"})
    assert resp.status_code == 200
    member_id = resp.json()["id"]

    resp = auth_client.put(f"/api/team/{member_id}", json={"role": "team_lead"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "team_lead"

    resp = auth_client.delete(f"/api/team/{member_id}")
    assert resp.status_code == 200

    resp = auth_client.get("/api/team")
    assert len(resp.json()) == 7


def test_delete_nonexistent_team_member_404s(auth_client):
    resp = auth_client.delete("/api/team/9999")
    assert resp.status_code == 404


def test_team_analytics_honest_about_unlinked_members(auth_client):
    """Team members with no linked login account must report None/'no data', never a
    fabricated 0 - a fake number would misleadingly look like poor performance."""
    resp = auth_client.get("/api/analytics/team")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 7

    artha = next(r for r in rows if r["name"] == "Artha")
    assert artha["calls"] == 4  # linked to testuser, who has 4 seeded calls

    rajesh = next(r for r in rows if r["name"] == "Rajesh Kumar")
    assert rajesh["calls"] is None
    assert rajesh["deals_closed"] is None
    assert rajesh["revenue"] is None
