"""ArthaInvest Connect (Phase 2A-ii): fixed team channels, typing indicators, read receipts,
and unread counts."""

EXPECTED_CHANNEL_SLUGS = {"loans", "insurance", "mutual-funds", "mumbai", "akola"}


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


def test_five_fixed_channels_exist_on_first_startup(client, auth_client):
    """Channels must be ready from the very first request against a fresh database - this test
    itself proves it, since the `client` fixture always starts from a brand-new temp database."""
    resp = auth_client.get("/api/chat/conversations")
    assert resp.status_code == 200
    channels = [c for c in resp.json() if c["type"] == "channel"]
    assert {c["slug"] for c in channels} == EXPECTED_CHANNEL_SLUGS
    for c in channels:
        assert c["unread_count"] == 0


def test_newly_registered_user_is_auto_joined_to_all_channels(client, auth_client):
    other_token, other_id = _register_and_login(client, "amol_ch", "Amol")
    resp = client.get(f"/api/chat/conversations?token={other_token}")
    channels = [c for c in resp.json() if c["type"] == "channel"]
    assert {c["slug"] for c in channels} == EXPECTED_CHANNEL_SLUGS


def test_websocket_typing_indicator_broadcasts_to_other_members_only(client, auth_client, auth_token):
    other_token, other_id = _register_and_login(client, "chirag_ch", "Chirag")
    my_user_id = next(u["id"] for u in auth_client.get("/api/chat/users").json() if u["username"] == "testuser")

    resp = auth_client.get("/api/chat/conversations")
    conv_id = next(c["id"] for c in resp.json() if c["slug"] == "loans")

    with client.websocket_connect(f"/ws?token={auth_token}") as ws1, \
         client.websocket_connect(f"/ws?token={other_token}") as ws2:
        presence = ws1.receive_json()
        assert presence["event"] == "presence"

        ws1.send_json({"event": "typing_start", "data": {"conversation_id": conv_id}})
        typing_event = ws2.receive_json()
        assert typing_event == {
            "event": "typing",
            "data": {"conversation_id": conv_id, "user_id": my_user_id, "is_typing": True},
        }

        ws1.send_json({"event": "typing_stop", "data": {"conversation_id": conv_id}})
        typing_stop_event = ws2.receive_json()
        assert typing_stop_event["data"]["is_typing"] is False


def test_unread_count_increments_and_clears_on_mark_read(client, auth_client, auth_token):
    other_token, other_id = _register_and_login(client, "samiksha_ch", "Samiksha")

    resp = auth_client.get("/api/chat/conversations")
    conv_id = next(c["id"] for c in resp.json() if c["slug"] == "insurance")

    sent = client.post(
        f"/api/chat/conversations/{conv_id}/messages?token={other_token}",
        json={"body": "New insurance lead assigned"},
    ).json()

    resp = auth_client.get("/api/chat/conversations")
    conv = next(c for c in resp.json() if c["id"] == conv_id)
    assert conv["unread_count"] == 1

    mark = auth_client.post(f"/api/chat/conversations/{conv_id}/read", json={"up_to_message_id": sent["id"]})
    assert mark.status_code == 200

    resp = auth_client.get("/api/chat/conversations")
    conv = next(c for c in resp.json() if c["id"] == conv_id)
    assert conv["unread_count"] == 0


def test_mark_read_requires_membership(client, auth_client):
    other_token, other_id = _register_and_login(client, "yogesh_ch", "Yogesh")
    bystander_token, _ = _register_and_login(client, "bystander_ch", "Bystander")

    conv = auth_client.post("/api/chat/conversations", json={"type": "dm", "member_user_ids": [other_id]}).json()

    resp = client.post(
        f"/api/chat/conversations/{conv['id']}/read?token={bystander_token}",
        json={"up_to_message_id": 1},
    )
    assert resp.status_code == 403


def test_websocket_mark_read_broadcasts_read_receipt(client, auth_client, auth_token):
    other_token, _ = _register_and_login(client, "nimita_ch", "Nimita")

    resp = auth_client.get("/api/chat/conversations")
    conv_id = next(c["id"] for c in resp.json() if c["slug"] == "mumbai")

    sent = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "Mumbai team, please check the new lead"},
    ).json()

    with client.websocket_connect(f"/ws?token={auth_token}") as ws1, \
         client.websocket_connect(f"/ws?token={other_token}") as ws2:
        presence = ws1.receive_json()
        assert presence["event"] == "presence"

        ws2.send_json({"event": "mark_read", "data": {"conversation_id": conv_id, "up_to_message_id": sent["id"]}})
        receipt = ws1.receive_json()
        assert receipt["event"] == "read_receipt"
        assert receipt["data"]["up_to_message_id"] == sent["id"]
