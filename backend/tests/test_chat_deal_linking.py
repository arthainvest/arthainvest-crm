"""ArthaInvest Connect (Phase 2B-iii): optional Deal <-> message linking.

Mirrors test_chat_lead_linking.py / test_chat_contact_linking.py's coverage exactly, for the
third independent link column: valid/invalid deal_id on message creation (REST + WebSocket),
that deal_id can never bypass normal conversation-membership authorization, that every existing
Phase 2A-iii/2B-i/2B-ii feature keeps working unchanged when deal_id is simply absent, and that
lead_id, contact_id and deal_id are genuinely independent columns - setting one never implies
anything about the other two."""


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


def _create_contact(auth_client, name):
    return auth_client.post("/api/contacts", json={"name": name, "phone": "9990001234"}).json()


def _create_deal(auth_client, lead_id):
    return auth_client.post(
        "/api/deals", json={"lead_id": lead_id, "deal_value": 500000, "loan_product": "Home"}
    ).json()


def test_valid_deal_link_is_stored(client, auth_client):
    other_token, other_id = _register_and_login(client, "nimita_deallink", "Nimita")
    conv_id = _create_dm(auth_client, other_id)
    lead = _create_lead(auth_client, "Rohit Sharma")
    deal = _create_deal(auth_client, lead["id"])

    resp = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "Any update on this loan?", "deal_id": deal["id"]},
    )
    assert resp.status_code == 200
    assert resp.json()["deal_id"] == deal["id"]
    assert resp.json()["lead_id"] is None
    assert resp.json()["contact_id"] is None


def test_invalid_deal_id_is_rejected(client, auth_client):
    other_token, other_id = _register_and_login(client, "yogesh_deallink", "Yogesh")
    conv_id = _create_dm(auth_client, other_id)

    resp = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "linking a deal that doesn't exist", "deal_id": 999999999},
    )
    assert resp.status_code == 400


def test_message_without_deal_id_still_succeeds(client, auth_client):
    other_token, other_id = _register_and_login(client, "samiksha_deallink", "Samiksha")
    conv_id = _create_dm(auth_client, other_id)

    resp = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "just a normal message"})
    assert resp.status_code == 200
    assert resp.json()["deal_id"] is None


def test_deal_id_does_not_bypass_conversation_membership(client, auth_client):
    """The core guardrail: a non-member still can't post into a conversation, valid deal_id or
    not - deal_id is never a substitute for conversation membership authorization."""
    other_token, other_id = _register_and_login(client, "amol_deallink", "Amol")
    bystander_token, _ = _register_and_login(client, "bystander_deallink", "Bystander")
    conv_id = _create_dm(auth_client, other_id)
    lead = _create_lead(auth_client, "Priya Nair")
    deal = _create_deal(auth_client, lead["id"])

    resp = client.post(
        f"/api/chat/conversations/{conv_id}/messages?token={bystander_token}",
        json={"body": "trying to sneak in via a deal link", "deal_id": deal["id"]},
    )
    assert resp.status_code == 403


def test_websocket_send_message_with_invalid_deal_id_returns_error(client, auth_client, auth_token):
    other_token, other_id = _register_and_login(client, "chirag_deallink", "Chirag")
    conv_id = _create_dm(auth_client, other_id)

    with client.websocket_connect(f"/ws?token={auth_token}") as ws:
        ws.send_json({
            "event": "send_message",
            "data": {"conversation_id": conv_id, "body": "bad deal link", "deal_id": 999999999},
        })
        event = ws.receive_json()
        assert event["event"] == "error"


def test_websocket_send_message_with_valid_deal_id_broadcasts_deal_id(client, auth_client, auth_token):
    other_token, other_id = _register_and_login(client, "nimita_deallink2", "Nimita")
    conv_id = _create_dm(auth_client, other_id)
    lead = _create_lead(auth_client, "Deepak Verma")
    deal = _create_deal(auth_client, lead["id"])

    with client.websocket_connect(f"/ws?token={auth_token}") as ws:
        ws.send_json({
            "event": "send_message",
            "data": {"conversation_id": conv_id, "body": "discussing this loan", "deal_id": deal["id"]},
        })
        event = ws.receive_json()
        assert event["event"] == "new_message"
        assert event["data"]["deal_id"] == deal["id"]


def test_lead_contact_and_deal_ids_are_mutually_independent(client, auth_client):
    """A message can carry any one of the three link columns, or none - this test pins down
    that setting one never sets or clears the other two, guarding against the three columns
    ever becoming accidentally coupled in a future refactor."""
    other_token, other_id = _register_and_login(client, "yogesh_deallink2", "Yogesh")
    conv_id = _create_dm(auth_client, other_id)
    lead = _create_lead(auth_client, "Anita Deshmukh")
    contact = _create_contact(auth_client, "Sanjay Rao")
    deal = _create_deal(auth_client, lead["id"])

    lead_msg = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "about the lead", "lead_id": lead["id"]},
    ).json()
    assert lead_msg["lead_id"] == lead["id"]
    assert lead_msg["contact_id"] is None
    assert lead_msg["deal_id"] is None

    contact_msg = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "about the contact", "contact_id": contact["id"]},
    ).json()
    assert contact_msg["contact_id"] == contact["id"]
    assert contact_msg["lead_id"] is None
    assert contact_msg["deal_id"] is None

    deal_msg = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "about the deal", "deal_id": deal["id"]},
    ).json()
    assert deal_msg["deal_id"] == deal["id"]
    assert deal_msg["lead_id"] is None
    assert deal_msg["contact_id"] is None


def test_existing_2a_iii_features_work_normally_without_deal_id(client, auth_client):
    """Regression check: reply, edit, delete, attachments, search, and mentions must all keep
    working exactly as before when deal_id is simply never supplied."""
    other_token, other_id = _register_and_login(client, "yogesh_deallink3", "Yogesh")
    conv_id = _create_dm(auth_client, other_id)

    original = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": f"unique_regression_marker_2b_iii hello @yogesh_deallink3"},
    ).json()
    assert original["deal_id"] is None
    assert original["mentioned_user_ids"] == [other_id]

    reply = auth_client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"body": "replying, no deal attached", "reply_to_message_id": original["id"]},
    ).json()
    assert reply["reply_to_message_id"] == original["id"]
    assert reply["deal_id"] is None

    edited = auth_client.put(f"/api/chat/messages/{reply['id']}", json={"body": "edited, still no deal"}).json()
    assert edited["body"] == "edited, still no deal"
    assert edited["deal_id"] is None

    files = {"file": ("no_deal.txt", b"attachment content", "text/plain")}
    attachment_msg = auth_client.post(f"/api/chat/conversations/{conv_id}/attachments", files=files, data={"body": ""}).json()
    assert attachment_msg["deal_id"] is None
    assert len(attachment_msg["attachments"]) == 1

    deleted = auth_client.delete(f"/api/chat/messages/{attachment_msg['id']}").json()
    assert deleted["deleted_at"] is not None

    search_resp = auth_client.get("/api/chat/search?q=unique_regression_marker_2b_iii")
    assert search_resp.status_code == 200
    assert any(m["id"] == original["id"] for m in search_resp.json())
