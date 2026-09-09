"""ArthaInvest Connect (Phase 2B-i): optional Lead <-> message linking.

Covers: valid/invalid lead_id on message creation (REST + WebSocket), that lead_id can never
bypass normal conversation-membership authorization, and that every existing Phase 2A-iii
feature (reply, edit, delete, attachments, search, mentions) keeps working unchanged when
lead_id is simply absent - the new field must be completely optional."""


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


def _create_lead(auth_client, name):
    return auth_client.post("/api/leads", json={"name": name, "phone": "9990001234"}).json()


def test_valid_lead_link_is_stored(client, auth_client):
    other_token, other_id = _register_and_login(client, "nimita_leadlink", "Nimita")
    conv_id = _create_dm(auth_client, other_id)
    lead = _create_lead(auth_client, "Rohit Sharma")

    resp = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "Any update on this lead?", "lead_id": lead["id"]},
    )
    assert resp.status_code == 200
    assert resp.json()["lead_id"] == lead["id"]


def test_invalid_lead_id_is_rejected(client, auth_client):
    other_token, other_id = _register_and_login(client, "yogesh_leadlink", "Yogesh")
    conv_id = _create_dm(auth_client, other_id)

    resp = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "linking a lead that doesn't exist", "lead_id": 999999999},
    )
    assert resp.status_code == 400


def test_message_without_lead_id_still_succeeds(client, auth_client):
    other_token, other_id = _register_and_login(client, "samiksha_leadlink", "Samiksha")
    conv_id = _create_dm(auth_client, other_id)

    resp = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "just a normal message"})
    assert resp.status_code == 200
    assert resp.json()["lead_id"] is None


def test_lead_id_does_not_bypass_conversation_membership(client, auth_client):
    """The core guardrail: a non-member still can't post into a conversation, valid lead_id or
    not - lead_id is never a substitute for conversation membership authorization."""
    other_token, other_id = _register_and_login(client, "amol_leadlink", "Amol")
    bystander_token, _ = _register_and_login(client, "bystander_leadlink", "Bystander")
    conv_id = _create_dm(auth_client, other_id)
    lead = _create_lead(auth_client, "Priya Nair")

    resp = client.post(
        f"/api/chat/conversations/{conv_id}/messages?token={bystander_token}",
        json={"body": "trying to sneak in via a lead link", "lead_id": lead["id"]},
    )
    assert resp.status_code == 403


def test_websocket_send_message_with_invalid_lead_id_returns_error(client, auth_client, auth_token):
    other_token, other_id = _register_and_login(client, "chirag_leadlink", "Chirag")
    conv_id = _create_dm(auth_client, other_id)

    with client.websocket_connect(f"/ws?token={auth_token}") as ws:
        ws.send_json({
            "event": "send_message",
            "data": {"conversation_id": conv_id, "body": "bad lead link", "lead_id": 999999999},
        })
        event = ws.receive_json()
        assert event["event"] == "error"


def test_websocket_send_message_with_valid_lead_id_broadcasts_lead_id(client, auth_client, auth_token):
    other_token, other_id = _register_and_login(client, "nimita_leadlink2", "Nimita")
    conv_id = _create_dm(auth_client, other_id)
    lead = _create_lead(auth_client, "Deepak Verma")

    with client.websocket_connect(f"/ws?token={auth_token}") as ws:
        ws.send_json({
            "event": "send_message",
            "data": {"conversation_id": conv_id, "body": "discussing this lead", "lead_id": lead["id"]},
        })
        event = ws.receive_json()
        assert event["event"] == "new_message"
        assert event["data"]["lead_id"] == lead["id"]


def test_existing_2a_iii_features_work_normally_without_lead_id(client, auth_client):
    """Regression check: reply, edit, delete, attachments, search, and mentions must all keep
    working exactly as before when lead_id is simply never supplied."""
    other_token, other_id = _register_and_login(client, "yogesh_leadlink2", "Yogesh")
    conv_id = _create_dm(auth_client, other_id)

    original = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": f"unique_regression_marker_2b hello @yogesh_leadlink2"},
    ).json()
    assert original["lead_id"] is None
    assert original["mentioned_user_ids"] == [other_id]

    reply = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "replying, no lead attached", "reply_to_message_id": original["id"]},
    ).json()
    assert reply["reply_to_message_id"] == original["id"]
    assert reply["lead_id"] is None

    edited = auth_client.put(f"/api/chat/messages/{reply['id']}", json={"body": "edited, still no lead"}).json()
    assert edited["body"] == "edited, still no lead"
    assert edited["lead_id"] is None

    files = {"file": ("no_lead.txt", b"attachment content", "text/plain")}
    attachment_msg = auth_client.post(f"/api/chat/conversations/{conv_id}/attachments", files=files, data={"body": ""}).json()
    assert attachment_msg["lead_id"] is None
    assert len(attachment_msg["attachments"]) == 1

    deleted = auth_client.delete(f"/api/chat/messages/{attachment_msg['id']}").json()
    assert deleted["deleted_at"] is not None

    search_resp = auth_client.get("/api/chat/search?q=unique_regression_marker_2b")
    assert search_resp.status_code == 200
    assert any(m["id"] == original["id"] for m in search_resp.json())
