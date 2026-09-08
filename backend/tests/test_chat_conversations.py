"""ArthaInvest Connect (Phase 2A-i): REST tests for /api/chat/users and /api/chat/conversations."""


def _register_and_login(client, username, full_name):
    admin_token = client.post(
        "/api/auth/login", json={"username": "testuser", "password": "12345"}
    ).json()["access_token"]
    client.post(
        f"/api/auth/register?token={admin_token}",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "pass123",
            "full_name": full_name,
            "role": "employee",
        },
    )
    login = client.post("/api/auth/login", json={"username": username, "password": "pass123"})
    return login.json()["access_token"], login.json()["user_id"]


def test_list_chat_users_requires_auth(client):
    resp = client.get("/api/chat/users")
    assert resp.status_code == 401


def test_list_chat_users_returns_real_users_only(client, auth_client):
    resp = auth_client.get("/api/chat/users")
    assert resp.status_code == 200
    users = resp.json()
    assert any(u["username"] == "testuser" for u in users)
    for u in users:
        assert set(u.keys()) == {"id", "username", "full_name"}


def test_create_dm_requires_exactly_two_participants(client, auth_client, auth_token):
    other_token, other_id = _register_and_login(client, "chirag", "Chirag")
    third_token, third_id = _register_and_login(client, "nimita2", "Nimita Two")

    resp = auth_client.post("/api/chat/conversations", json={"type": "dm", "member_user_ids": [other_id, third_id]})
    assert resp.status_code == 400


def test_create_dm_and_reuses_existing_dm_between_same_pair(client, auth_client):
    other_token, other_id = _register_and_login(client, "yogesh2", "Yogesh Two")

    first = auth_client.post("/api/chat/conversations", json={"type": "dm", "member_user_ids": [other_id]})
    assert first.status_code == 200
    conv = first.json()
    assert conv["type"] == "dm"
    member_ids = {m["user_id"] for m in conv["members"]}
    assert member_ids == {1, other_id}

    second = auth_client.post("/api/chat/conversations", json={"type": "dm", "member_user_ids": [other_id]})
    assert second.status_code == 200
    assert second.json()["id"] == conv["id"], "creating a DM with the same pair again should reuse it, not duplicate it"


def test_create_group_needs_at_least_two_participants_total(client, auth_client):
    resp = auth_client.post("/api/chat/conversations", json={"type": "group", "member_user_ids": [], "name": "Solo"})
    # member_user_ids=[] plus the caller themselves = 1 total member, below the minimum of 2.
    assert resp.status_code == 400


def test_create_conversation_rejects_unknown_user_id(client, auth_client):
    resp = auth_client.post("/api/chat/conversations", json={"type": "dm", "member_user_ids": [999999]})
    assert resp.status_code == 400


def test_create_conversation_rejects_invalid_type(client, auth_client):
    other_token, other_id = _register_and_login(client, "amol2", "Amol Two")
    resp = auth_client.post("/api/chat/conversations", json={"type": "channel", "member_user_ids": [other_id]})
    assert resp.status_code == 400


def test_group_conversation_with_multiple_real_employees(client, auth_client):
    """Mirrors the actual use case: the 5 real employees in one group, no fake data."""
    _, nimita_id = _register_and_login(client, "nimita3", "Nimita")
    _, yogesh_id = _register_and_login(client, "yogesh3", "Yogesh")
    _, samiksha_id = _register_and_login(client, "samiksha3", "Samiksha")

    resp = auth_client.post(
        "/api/chat/conversations",
        json={"type": "group", "member_user_ids": [nimita_id, yogesh_id, samiksha_id], "name": "Loans Team"},
    )
    assert resp.status_code == 200
    conv = resp.json()
    assert conv["name"] == "Loans Team"
    assert len(conv["members"]) == 4  # caller + 3 named employees
    owner = next(m for m in conv["members"] if m["role_in_conversation"] == "owner")
    assert owner["user_id"] == 1  # testuser, the creator


def test_list_conversations_only_shows_callers_own(client, auth_client):
    other_token, other_id = _register_and_login(client, "samiksha4", "Samiksha")
    bystander_token, bystander_id = _register_and_login(client, "bystander", "Bystander")

    dm = auth_client.post("/api/chat/conversations", json={"type": "dm", "member_user_ids": [other_id]}).json()

    resp = client.get(f"/api/chat/conversations?token={bystander_token}")
    assert resp.status_code == 200
    # Every user auto-joins the fixed team channels (Phase 2A-ii), so a bystander legitimately
    # sees those - the assertion here is specifically that they do NOT see the DM they're not in.
    assert dm["id"] not in [c["id"] for c in resp.json()]
    assert all(c["type"] == "channel" for c in resp.json())


def test_get_conversation_403_for_non_member(client, auth_client):
    other_token, other_id = _register_and_login(client, "amol3", "Amol")
    bystander_token, _ = _register_and_login(client, "bystander2", "Bystander")

    conv = auth_client.post("/api/chat/conversations", json={"type": "dm", "member_user_ids": [other_id]}).json()

    resp = client.get(f"/api/chat/conversations/{conv['id']}?token={bystander_token}")
    assert resp.status_code == 403


def test_get_conversation_404_for_nonexistent(client, auth_client):
    resp = auth_client.get("/api/chat/conversations/999999")
    assert resp.status_code == 404
