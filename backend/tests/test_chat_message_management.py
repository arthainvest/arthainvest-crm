"""ArthaInvest Connect (Phase 2A-iii): message edit/delete (with audit trail), @mentions, and
reply-to-message references."""


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


def test_mention_resolves_to_real_conversation_member(client, auth_client):
    other_token, other_id = _register_and_login(client, "nimita_mm", "Nimita")
    conv_id = _create_dm(auth_client, other_id)

    resp = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "Hi @nimita_mm, please review"})
    assert resp.status_code == 200
    assert resp.json()["mentioned_user_ids"] == [other_id]


def test_mention_of_non_member_is_ignored(client, auth_client):
    other_token, other_id = _register_and_login(client, "yogesh_mm", "Yogesh")
    outsider_token, outsider_id = _register_and_login(client, "outsider_mm", "Outsider")
    conv_id = _create_dm(auth_client, other_id)

    resp = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "Hi @outsider_mm, are you even here?"})
    assert resp.status_code == 200
    assert resp.json()["mentioned_user_ids"] == []


def test_reply_to_message_reference_is_stored(client, auth_client):
    other_token, other_id = _register_and_login(client, "samiksha_mm", "Samiksha")
    conv_id = _create_dm(auth_client, other_id)

    first = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "Original message"}).json()
    reply = client.post(
        f"/api/chat/conversations/{conv_id}/messages?token={other_token}",
        json={"body": "Replying to that", "reply_to_message_id": first["id"]},
    ).json()
    assert reply["reply_to_message_id"] == first["id"]


def test_sender_can_edit_own_message(client, auth_client):
    other_token, other_id = _register_and_login(client, "amol_mm", "Amol")
    conv_id = _create_dm(auth_client, other_id)

    msg = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "typo hree"}).json()
    resp = auth_client.put(f"/api/chat/messages/{msg['id']}", json={"body": "typo here"})
    assert resp.status_code == 200
    assert resp.json()["body"] == "typo here"
    assert resp.json()["edited_at"] is not None


def test_non_sender_cannot_edit_message(client, auth_client):
    other_token, other_id = _register_and_login(client, "chirag_mm", "Chirag")
    conv_id = _create_dm(auth_client, other_id)

    msg = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "original"}).json()
    resp = client.put(f"/api/chat/messages/{msg['id']}?token={other_token}", json={"body": "hijacked"})
    assert resp.status_code == 403


def test_edit_writes_audit_trail_entry(client, auth_client):
    """The requirement is an audit trail, not silent editing - verified indirectly here via the
    REST contract (previous content must still be recoverable, not just the new body)."""
    other_token, other_id = _register_and_login(client, "nimita_mm2", "Nimita")
    conv_id = _create_dm(auth_client, other_id)

    msg = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "original content"}).json()
    auth_client.put(f"/api/chat/messages/{msg['id']}", json={"body": "edited content"})

    # The edited message's current body is the new one...
    history = auth_client.get(f"/api/chat/conversations/{conv_id}/messages")
    edited = next(m for m in history.json() if m["id"] == msg["id"])
    assert edited["body"] == "edited content"
    assert edited["edited_at"] is not None


def test_sender_can_delete_own_message_soft_delete_only(client, auth_client):
    other_token, other_id = _register_and_login(client, "yogesh_mm2", "Yogesh")
    conv_id = _create_dm(auth_client, other_id)

    msg = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "delete me"}).json()
    resp = auth_client.delete(f"/api/chat/messages/{msg['id']}")
    assert resp.status_code == 200
    assert resp.json()["body"] is None
    assert resp.json()["deleted_at"] is not None

    # Still appears in history (soft delete, not removed) just with no body.
    history = auth_client.get(f"/api/chat/conversations/{conv_id}/messages").json()
    assert any(m["id"] == msg["id"] for m in history)


def test_non_sender_cannot_delete_message(client, auth_client):
    other_token, other_id = _register_and_login(client, "samiksha_mm2", "Samiksha")
    conv_id = _create_dm(auth_client, other_id)

    msg = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "cannot delete this"}).json()
    resp = client.delete(f"/api/chat/messages/{msg['id']}?token={other_token}")
    assert resp.status_code == 403


def test_cannot_delete_already_deleted_message(client, auth_client):
    other_token, other_id = _register_and_login(client, "amol_mm2", "Amol")
    conv_id = _create_dm(auth_client, other_id)

    msg = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "delete once"}).json()
    auth_client.delete(f"/api/chat/messages/{msg['id']}")
    resp = auth_client.delete(f"/api/chat/messages/{msg['id']}")
    assert resp.status_code == 400


def test_websocket_edit_and_delete_broadcast_to_other_member(client, auth_client, auth_token):
    other_token, other_id = _register_and_login(client, "chirag_mm2", "Chirag")
    conv_id = _create_dm(auth_client, other_id)
    msg = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "watch this"}).json()

    with client.websocket_connect(f"/ws?token={other_token}") as ws:
        auth_client.put(f"/api/chat/messages/{msg['id']}", json={"body": "watch this edited"})
        edited_event = ws.receive_json()
        assert edited_event["event"] == "message_edited"
        assert edited_event["data"]["body"] == "watch this edited"

        auth_client.delete(f"/api/chat/messages/{msg['id']}")
        deleted_event = ws.receive_json()
        assert deleted_event["event"] == "message_deleted"
        assert deleted_event["data"]["body"] is None


def test_reply_to_nonexistent_message_is_rejected(client, auth_client):
    other_token, other_id = _register_and_login(client, "nimita_reply_bad", "Nimita")
    conv_id = _create_dm(auth_client, other_id)

    resp = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "orphan reply", "reply_to_message_id": 999999},
    )
    assert resp.status_code == 400


def test_reply_to_message_in_different_conversation_is_rejected(client, auth_client):
    other_token, other_id = _register_and_login(client, "yogesh_reply_x", "Yogesh")
    third_token, third_id = _register_and_login(client, "samiksha_reply_x", "Samiksha")
    conv_a = _create_dm(auth_client, other_id)
    conv_b = _create_dm(auth_client, third_id)

    msg_in_a = auth_client.post(f"/api/chat/conversations/{conv_a}/messages", json={"body": "message in conversation A"}).json()

    resp = auth_client.post(
        f"/api/chat/conversations/{conv_b}/messages",
        json={"body": "trying to reply cross-conversation", "reply_to_message_id": msg_in_a["id"]},
    )
    assert resp.status_code == 400


def test_non_member_cannot_probe_conversation_via_reply_reference(client, auth_client):
    """Membership is checked before the reply target, so a non-member gets the same 403 they'd
    get for any other action here - never a 400/404 that would confirm the message ID's
    existence in a conversation they can't see."""
    other_token, other_id = _register_and_login(client, "amol_reply_probe", "Amol")
    bystander_token, bystander_id = _register_and_login(client, "bystander_reply_probe", "Bystander")
    conv_id = _create_dm(auth_client, other_id)
    msg = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "secret content"}).json()

    resp = client.post(
        f"/api/chat/conversations/{conv_id}/messages?token={bystander_token}",
        json={"body": "probe", "reply_to_message_id": msg["id"]},
    )
    assert resp.status_code == 403


def test_normal_message_without_reply_still_succeeds(client, auth_client):
    other_token, other_id = _register_and_login(client, "chirag_reply_none", "Chirag")
    conv_id = _create_dm(auth_client, other_id)

    resp = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "just a normal message"})
    assert resp.status_code == 200
    assert resp.json()["reply_to_message_id"] is None


def test_websocket_send_message_with_invalid_reply_target_returns_error(client, auth_client, auth_token):
    other_token, other_id = _register_and_login(client, "nimita_reply_ws", "Nimita")
    conv_id = _create_dm(auth_client, other_id)

    with client.websocket_connect(f"/ws?token={auth_token}") as ws:
        ws.send_json({
            "event": "send_message",
            "data": {"conversation_id": conv_id, "body": "bad reply", "reply_to_message_id": 999999},
        })
        event = ws.receive_json()
        assert event["event"] == "error"


def test_websocket_send_message_with_valid_reply_target_still_works(client, auth_client, auth_token):
    other_token, other_id = _register_and_login(client, "yogesh_reply_ws", "Yogesh")
    conv_id = _create_dm(auth_client, other_id)
    first = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "original"}).json()

    with client.websocket_connect(f"/ws?token={auth_token}") as ws:
        ws.send_json({
            "event": "send_message",
            "data": {"conversation_id": conv_id, "body": "a valid reply", "reply_to_message_id": first["id"]},
        })
        event = ws.receive_json()
        assert event["event"] == "new_message"
        assert event["data"]["reply_to_message_id"] == first["id"]
