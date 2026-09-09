"""ArthaInvest Connect (Phase 2B-ii): optional Contact <-> message linking.

Mirrors test_chat_lead_linking.py's coverage exactly, for the independent contact_id column:
valid/invalid contact_id on message creation (REST + WebSocket), that contact_id can never
bypass normal conversation-membership authorization, that every existing Phase 2A-iii/2B-i
feature keeps working unchanged when contact_id is simply absent, and that lead_id and
contact_id are genuinely independent columns - one being set never implies anything about
the other."""


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


def _create_contact(auth_client, name):
    return auth_client.post("/api/contacts", json={"name": name, "phone": "9990001234"}).json()


def _create_lead(auth_client, name):
    return auth_client.post("/api/leads", json={"name": name, "phone": "9990001234"}).json()


def test_valid_contact_link_is_stored(client, auth_client):
    other_token, other_id = _register_and_login(client, "nimita_contactlink", "Nimita")
    conv_id = _create_dm(auth_client, other_id)
    contact = _create_contact(auth_client, "Rohit Sharma")

    resp = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "Any update on this client?", "contact_id": contact["id"]},
    )
    assert resp.status_code == 200
    assert resp.json()["contact_id"] == contact["id"]
    assert resp.json()["lead_id"] is None


def test_invalid_contact_id_is_rejected(client, auth_client):
    other_token, other_id = _register_and_login(client, "yogesh_contactlink", "Yogesh")
    conv_id = _create_dm(auth_client, other_id)

    resp = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "linking a contact that doesn't exist", "contact_id": 999999999},
    )
    assert resp.status_code == 400


def test_message_without_contact_id_still_succeeds(client, auth_client):
    other_token, other_id = _register_and_login(client, "samiksha_contactlink", "Samiksha")
    conv_id = _create_dm(auth_client, other_id)

    resp = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "just a normal message"})
    assert resp.status_code == 200
    assert resp.json()["contact_id"] is None


def test_contact_id_does_not_bypass_conversation_membership(client, auth_client):
    """The core guardrail: a non-member still can't post into a conversation, valid contact_id
    or not - contact_id is never a substitute for conversation membership authorization."""
    other_token, other_id = _register_and_login(client, "amol_contactlink", "Amol")
    bystander_token, _ = _register_and_login(client, "bystander_contactlink", "Bystander")
    conv_id = _create_dm(auth_client, other_id)
    contact = _create_contact(auth_client, "Priya Nair")

    resp = client.post(
        f"/api/chat/conversations/{conv_id}/messages?token={bystander_token}",
        json={"body": "trying to sneak in via a contact link", "contact_id": contact["id"]},
    )
    assert resp.status_code == 403


def test_websocket_send_message_with_invalid_contact_id_returns_error(client, auth_client, auth_token):
    other_token, other_id = _register_and_login(client, "chirag_contactlink", "Chirag")
    conv_id = _create_dm(auth_client, other_id)

    with client.websocket_connect(f"/ws?token={auth_token}") as ws:
        ws.send_json({
            "event": "send_message",
            "data": {"conversation_id": conv_id, "body": "bad contact link", "contact_id": 999999999},
        })
        event = ws.receive_json()
        assert event["event"] == "error"


def test_websocket_send_message_with_valid_contact_id_broadcasts_contact_id(client, auth_client, auth_token):
    other_token, other_id = _register_and_login(client, "nimita_contactlink2", "Nimita")
    conv_id = _create_dm(auth_client, other_id)
    contact = _create_contact(auth_client, "Deepak Verma")

    with client.websocket_connect(f"/ws?token={auth_token}") as ws:
        ws.send_json({
            "event": "send_message",
            "data": {"conversation_id": conv_id, "body": "discussing this client", "contact_id": contact["id"]},
        })
        event = ws.receive_json()
        assert event["event"] == "new_message"
        assert event["data"]["contact_id"] == contact["id"]


def test_lead_id_and_contact_id_are_independent_columns(client, auth_client):
    """A message can carry a lead_id without a contact_id (already covered by
    test_chat_lead_linking.py) or a contact_id without a lead_id (covered above) - this test
    just pins down that setting one never sets or clears the other, guarding against the two
    columns ever becoming accidentally coupled in a future refactor."""
    other_token, other_id = _register_and_login(client, "yogesh_contactlink2", "Yogesh")
    conv_id = _create_dm(auth_client, other_id)
    lead = _create_lead(auth_client, "Anita Deshmukh")
    contact = _create_contact(auth_client, "Sanjay Rao")

    lead_msg = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "about the lead", "lead_id": lead["id"]},
    ).json()
    assert lead_msg["lead_id"] == lead["id"]
    assert lead_msg["contact_id"] is None

    contact_msg = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "about the contact", "contact_id": contact["id"]},
    ).json()
    assert contact_msg["contact_id"] == contact["id"]
    assert contact_msg["lead_id"] is None


def test_existing_2a_iii_features_work_normally_without_contact_id(client, auth_client):
    """Regression check: reply, edit, delete, attachments, search, and mentions must all keep
    working exactly as before when contact_id is simply never supplied."""
    other_token, other_id = _register_and_login(client, "yogesh_contactlink3", "Yogesh")
    conv_id = _create_dm(auth_client, other_id)

    original = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": f"unique_regression_marker_2b_ii hello @yogesh_contactlink3"},
    ).json()
    assert original["contact_id"] is None
    assert original["mentioned_user_ids"] == [other_id]

    reply = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "replying, no contact attached", "reply_to_message_id": original["id"]},
    ).json()
    assert reply["reply_to_message_id"] == original["id"]
    assert reply["contact_id"] is None

    edited = auth_client.put(f"/api/chat/messages/{reply['id']}", json={"body": "edited, still no contact"}).json()
    assert edited["body"] == "edited, still no contact"
    assert edited["contact_id"] is None

    files = {"file": ("no_contact.txt", b"attachment content", "text/plain")}
    attachment_msg = auth_client.post(f"/api/chat/conversations/{conv_id}/attachments", files=files, data={"body": ""}).json()
    assert attachment_msg["contact_id"] is None
    assert len(attachment_msg["attachments"]) == 1

    deleted = auth_client.delete(f"/api/chat/messages/{attachment_msg['id']}").json()
    assert deleted["deleted_at"] is not None

    search_resp = auth_client.get("/api/chat/search?q=unique_regression_marker_2b_ii")
    assert search_resp.status_code == 200
    assert any(m["id"] == original["id"] for m in search_resp.json())
