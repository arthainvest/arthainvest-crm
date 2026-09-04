def test_get_my_team_member_returns_linked_roster_entry(auth_client):
    """testuser is seeded as login-linked to the 'Artha' roster entry (team_members.user_id)."""
    resp = auth_client.get("/api/team/me")
    assert resp.status_code == 200
    member = resp.json()
    assert member is not None
    assert member["name"] == "Artha"
    assert member["role"] == "admin"


def test_get_my_team_member_null_when_unlinked(client, auth_client):
    """A brand-new login has no roster entry pointing at it yet - must return null, not 404."""
    auth_client.post("/api/auth/register", json={
        "username": "unlinked_user", "email": "unlinked@example.com", "password": "pw12345",
        "full_name": "Unlinked User", "role": "employee"
    })
    login_resp = client.post("/api/auth/login", json={"username": "unlinked_user", "password": "pw12345"})
    token = login_resp.json()["access_token"]

    resp = client.get(f"/api/team/me?token={token}")
    assert resp.status_code == 200
    assert resp.json() is None


def test_saving_profile_settings_syncs_linked_roster_entry(auth_client):
    resp = auth_client.put("/api/settings", json={
        "full_name": "Artha Updated", "email": "artha.new@arthainvest.com", "phone": "+919999911111"
    })
    assert resp.status_code == 200

    member = auth_client.get("/api/team/me").json()
    assert member["name"] == "Artha Updated"
    assert member["email"] == "artha.new@arthainvest.com"
    assert member["phone"] == "+919999911111"

    # And the change is visible from the team roster list too, not just /team/me.
    roster = auth_client.get("/api/team").json()
    updated = next(m for m in roster if m["id"] == member["id"])
    assert updated["name"] == "Artha Updated"


def test_saving_settings_without_profile_fields_does_not_touch_roster(auth_client):
    before = auth_client.get("/api/team/me").json()

    resp = auth_client.put("/api/settings", json={"theme": "dark"})
    assert resp.status_code == 200

    after = auth_client.get("/api/team/me").json()
    assert after["name"] == before["name"]
    assert after["email"] == before["email"]
    assert after["phone"] == before["phone"]


def test_saving_profile_settings_for_unlinked_login_does_not_error(client, auth_client):
    """No roster entry to sync into - the UPDATE just matches zero rows, no crash."""
    auth_client.post("/api/auth/register", json={
        "username": "solo_user", "email": "solo@example.com", "password": "pw12345",
        "full_name": "Solo User", "role": "employee"
    })
    login_resp = client.post("/api/auth/login", json={"username": "solo_user", "password": "pw12345"})
    token = login_resp.json()["access_token"]

    resp = client.put(f"/api/settings?token={token}", json={"full_name": "Solo Renamed"})
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Solo Renamed"

    assert client.get(f"/api/team/me?token={token}").json() is None
