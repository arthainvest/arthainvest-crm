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


def test_non_admin_cannot_manage_team(client):
    """Creating/editing/removing team roster entries affects everyone, not just the person
    doing it - only an admin account may do it."""
    client.post("/api/auth/register", json={
        "username": "fieldemployee", "email": "field@example.com", "password": "pw12345",
        "full_name": "Field Employee", "role": "employee"
    })
    login_resp = client.post("/api/auth/login", json={"username": "fieldemployee", "password": "pw12345"})
    employee_token = login_resp.json()["access_token"]

    resp = client.post(f"/api/team?token={employee_token}", json={"name": "New Hire", "role": "employee"})
    assert resp.status_code == 403

    resp = client.put(f"/api/team/1?token={employee_token}", json={"role": "team_lead"})
    assert resp.status_code == 403

    resp = client.delete(f"/api/team/1?token={employee_token}")
    assert resp.status_code == 403


def test_team_analytics_counts_assigned_activity_for_every_member(auth_client):
    """Every team member is measurable now via the explicit assignment columns
    (calls.team_member_id, deals/leads.assigned_team_member_id) added alongside the
    Calls/Pipeline/Leads employee-assignment features - not just members with a linked login.
    A member with nothing assigned to them yet gets a real 0, not a fabricated placeholder."""
    resp = auth_client.get("/api/analytics/team")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 7

    artha = next(r for r in rows if r["name"] == "Artha")
    assert artha["calls"] == 4  # linked to testuser, who has 4 seeded (unassigned) calls

    rajesh = next(r for r in rows if r["name"] == "Rajesh Kumar")
    assert rajesh["calls"] == 0  # no login, and nothing explicitly assigned to him yet
    assert rajesh["deals_closed"] == 0
    assert rajesh["revenue"] == 0

    # Assigning a call to Rajesh directly must show up here immediately.
    calls = auth_client.get("/api/calls").json()
    auth_client.put(f"/api/calls/{calls[0]['id']}/assign", json={"team_member_id": rajesh["id"]})
    resp = auth_client.get("/api/analytics/team")
    rajesh_after = next(r for r in resp.json() if r["name"] == "Rajesh Kumar")
    assert rajesh_after["calls"] == 1


def test_team_analytics_counts_tasks_completed_and_meetings_conducted(auth_client):
    from datetime import date
    today = date.today().isoformat()

    rajesh_id = next(m["id"] for m in auth_client.get("/api/team").json() if m["name"] == "Rajesh Kumar")

    baseline = next(r for r in auth_client.get("/api/analytics/team").json() if r["name"] == "Rajesh Kumar")
    assert baseline["tasks_completed"] == 0
    assert baseline["meetings_conducted"] == 0

    # An incomplete task and a still-Scheduled meeting must NOT count yet.
    task = auth_client.post("/api/tasks", json={
        "title": "Chase KYC docs", "due_date": today, "assigned_team_member_id": rajesh_id
    }).json()
    meeting = auth_client.post("/api/meetings", json={
        "title": "Policy review", "meeting_date": today, "assigned_team_member_id": rajesh_id
    }).json()

    mid_resp = next(r for r in auth_client.get("/api/analytics/team").json() if r["name"] == "Rajesh Kumar")
    assert mid_resp["tasks_completed"] == 0
    assert mid_resp["meetings_conducted"] == 0

    # Completing the task and marking the meeting Conducted must both show up immediately.
    auth_client.put(f"/api/tasks/{task['id']}", json={"completed": True})
    auth_client.put(f"/api/meetings/{meeting['id']}", json={"status": "Conducted"})

    final = next(r for r in auth_client.get("/api/analytics/team").json() if r["name"] == "Rajesh Kumar")
    assert final["tasks_completed"] == 1
    assert final["meetings_conducted"] == 1
