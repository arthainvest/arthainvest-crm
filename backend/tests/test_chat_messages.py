"""ArthaInvest Connect (Phase 2A-i): REST tests for message history and the REST send fallback."""


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


def _create_dm(auth_client, other_id):
    resp = auth_client.post("/api/chat/conversations", json={"type": "dm", "member_user_ids": [other_id]})
    return resp.json()["id"]


def test_send_message_rest_and_read_it_back(client, auth_client):
    other_token, other_id = _register_and_login(client, "nimita5", "Nimita")
    conv_id = _create_dm(auth_client, other_id)

    resp = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "Hello via REST"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["body"] == "Hello via REST"
    assert body["sender_name"] == "Test User"
    assert body["conversation_id"] == conv_id

    history = auth_client.get(f"/api/chat/conversations/{conv_id}/messages")
    assert history.status_code == 200
    assert [m["body"] for m in history.json()] == ["Hello via REST"]


def test_send_message_rejects_non_member(client, auth_client):
    other_token, other_id = _register_and_login(client, "yogesh5", "Yogesh")
    bystander_token, _ = _register_and_login(client, "bystander3", "Bystander")
    conv_id = _create_dm(auth_client, other_id)

    resp = client.post(
        f"/api/chat/conversations/{conv_id}/messages?token={bystander_token}",
        json={"body": "I shouldn't be able to post this"},
    )
    assert resp.status_code == 403


def test_send_message_rejects_empty_body(client, auth_client):
    other_token, other_id = _register_and_login(client, "samiksha5", "Samiksha")
    conv_id = _create_dm(auth_client, other_id)

    resp = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": ""})
    assert resp.status_code == 422  # MessageCreate.body has min_length=1


def test_message_history_pagination_after_id(client, auth_client):
    other_token, other_id = _register_and_login(client, "amol5", "Amol")
    conv_id = _create_dm(auth_client, other_id)

    ids = []
    for text in ["first", "second", "third"]:
        r = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": text})
        ids.append(r.json()["id"])

    after_first = auth_client.get(f"/api/chat/conversations/{conv_id}/messages?after_id={ids[0]}")
    assert [m["body"] for m in after_first.json()] == ["second", "third"]

    before_third = auth_client.get(f"/api/chat/conversations/{conv_id}/messages?before_id={ids[2]}")
    assert [m["body"] for m in before_third.json()] == ["first", "second"]


def test_message_history_requires_membership(client, auth_client):
    other_token, other_id = _register_and_login(client, "chirag5", "Chirag")
    bystander_token, _ = _register_and_login(client, "bystander4", "Bystander")
    conv_id = _create_dm(auth_client, other_id)

    resp = client.get(f"/api/chat/conversations/{conv_id}/messages?token={bystander_token}")
    assert resp.status_code == 403


def test_conversation_list_reflects_last_message_preview(client, auth_client):
    other_token, other_id = _register_and_login(client, "nimita6", "Nimita")
    conv_id = _create_dm(auth_client, other_id)

    auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "Latest one"})

    resp = auth_client.get("/api/chat/conversations")
    conv = next(c for c in resp.json() if c["id"] == conv_id)
    assert conv["last_message_body"] == "Latest one"
    assert conv["last_message_sender_id"] == 1


def test_rest_send_and_websocket_send_produce_identical_message_shape(client, auth_client, auth_token):
    """The REST send path and the WebSocket send path share one _create_message() function -
    this pins that a message sent either way looks the same to a reader."""
    other_token, other_id = _register_and_login(client, "yogesh6", "Yogesh")
    conv_id = _create_dm(auth_client, other_id)

    rest_msg = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "via rest"}).json()

    with client.websocket_connect(f"/ws?token={auth_token}") as ws:
        ws.send_json({"event": "send_message", "data": {"conversation_id": conv_id, "body": "via websocket"}})
        ws_msg = ws.receive_json()["data"]

    assert set(rest_msg.keys()) == set(ws_msg.keys())
    assert rest_msg["message_type"] == ws_msg["message_type"] == "text"
