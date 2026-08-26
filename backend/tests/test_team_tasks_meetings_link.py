from datetime import date


def test_get_tasks_filters_by_assigned_team_member_across_all_dates(auth_client):
    """Team/Reports pages' per-member drill-down needs every task ever assigned to a member,
    not just today's - matching what /api/analytics/team's tasks_completed figure counts."""
    rajesh = next(m for m in auth_client.get("/api/team").json() if m["name"] == "Rajesh Kumar")
    past_task = auth_client.post("/api/tasks", json={
        "title": "Old task", "due_date": "2020-01-01", "assigned_team_member_id": rajesh["id"]
    }).json()
    today_task = auth_client.post("/api/tasks", json={
        "title": "Today task", "due_date": date.today().isoformat(), "assigned_team_member_id": rajesh["id"]
    }).json()

    resp = auth_client.get(f"/api/tasks?assigned_team_member_id={rajesh['id']}")
    assert resp.status_code == 200
    ids = {t["id"] for t in resp.json()}
    assert past_task["id"] in ids
    assert today_task["id"] in ids


def test_get_tasks_assigned_team_member_filter_matches_analytics_completed_count(auth_client):
    rajesh = next(m for m in auth_client.get("/api/team").json() if m["name"] == "Rajesh Kumar")
    task = auth_client.post("/api/tasks", json={
        "title": "Chase KYC", "due_date": "2026-09-01", "assigned_team_member_id": rajesh["id"]
    }).json()
    auth_client.put(f"/api/tasks/{task['id']}", json={"completed": True})

    productivity = next(r for r in auth_client.get("/api/analytics/team").json() if r["name"] == "Rajesh Kumar")
    drilldown = auth_client.get(f"/api/tasks?assigned_team_member_id={rajesh['id']}").json()
    completed_in_drilldown = len([t for t in drilldown if t["completed"]])
    assert completed_in_drilldown == productivity["tasks_completed"]


def test_get_meetings_filters_by_assigned_team_member_across_all_dates(auth_client):
    rajesh = next(m for m in auth_client.get("/api/team").json() if m["name"] == "Rajesh Kumar")
    past_meeting = auth_client.post("/api/meetings", json={
        "title": "Old meeting", "meeting_date": "2020-01-01", "assigned_team_member_id": rajesh["id"]
    }).json()

    resp = auth_client.get(f"/api/meetings?assigned_team_member_id={rajesh['id']}")
    assert resp.status_code == 200
    ids = {m["id"] for m in resp.json()}
    assert past_meeting["id"] in ids


def test_get_meetings_assigned_team_member_filter_matches_analytics_conducted_count(auth_client):
    rajesh = next(m for m in auth_client.get("/api/team").json() if m["name"] == "Rajesh Kumar")
    meeting = auth_client.post("/api/meetings", json={
        "title": "Policy review", "meeting_date": "2026-09-02", "assigned_team_member_id": rajesh["id"]
    }).json()
    auth_client.put(f"/api/meetings/{meeting['id']}", json={"status": "Conducted"})

    productivity = next(r for r in auth_client.get("/api/analytics/team").json() if r["name"] == "Rajesh Kumar")
    drilldown = auth_client.get(f"/api/meetings?assigned_team_member_id={rajesh['id']}").json()
    conducted_in_drilldown = len([m for m in drilldown if m["status"] == "Conducted"])
    assert conducted_in_drilldown == productivity["meetings_conducted"]


def test_get_tasks_without_team_member_filter_stays_day_scoped(auth_client):
    """Confirms the new filter is additive - Today page's existing day-scoped behavior
    (no assigned_team_member_id param) must be unaffected."""
    auth_client.post("/api/tasks", json={"title": "Far future", "due_date": "2099-01-01"})
    resp = auth_client.get(f"/api/tasks?date={date.today().isoformat()}")
    assert resp.status_code == 200
    assert all(t["due_date"] == date.today().isoformat() for t in resp.json())
