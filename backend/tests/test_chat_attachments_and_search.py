"""ArthaInvest Connect (Phase 2A-iii): file/image attachments and message search."""


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


def test_upload_text_attachment_and_download_it_back(client, auth_client):
    other_token, other_id = _register_and_login(client, "nimita_att", "Nimita")
    conv_id = _create_dm(auth_client, other_id)

    files = {"file": ("checklist.txt", b"loan document checklist contents", "text/plain")}
    resp = auth_client.post(f"/api/chat/conversations/{conv_id}/attachments", files=files, data={"body": "See attached"})
    assert resp.status_code == 200
    msg = resp.json()
    assert msg["message_type"] == "file"
    assert msg["body"] == "See attached"
    assert len(msg["attachments"]) == 1
    attachment = msg["attachments"][0]
    assert attachment["file_name"] == "checklist.txt"
    assert attachment["content_type"] == "text/plain"

    download = client.get(f"/api/chat/attachments/{attachment['id']}/content?token={other_token}")
    assert download.status_code == 200
    assert download.content == b"loan document checklist contents"


def test_image_attachment_gets_image_message_type(client, auth_client):
    other_token, other_id = _register_and_login(client, "yogesh_att", "Yogesh")
    conv_id = _create_dm(auth_client, other_id)

    files = {"file": ("photo.png", b"\x89PNG fake image bytes", "image/png")}
    resp = auth_client.post(f"/api/chat/conversations/{conv_id}/attachments", files=files, data={"body": ""})
    assert resp.status_code == 200
    assert resp.json()["message_type"] == "image"


def test_attachment_upload_rejects_disallowed_content_type(client, auth_client):
    other_token, other_id = _register_and_login(client, "samiksha_att", "Samiksha")
    conv_id = _create_dm(auth_client, other_id)

    files = {"file": ("script.exe", b"MZ fake executable", "application/x-msdownload")}
    resp = auth_client.post(f"/api/chat/conversations/{conv_id}/attachments", files=files, data={"body": ""})
    assert resp.status_code == 400


def test_attachment_upload_requires_membership(client, auth_client):
    other_token, other_id = _register_and_login(client, "amol_att", "Amol")
    bystander_token, _ = _register_and_login(client, "bystander_att", "Bystander")
    conv_id = _create_dm(auth_client, other_id)

    files = {"file": ("test.txt", b"data", "text/plain")}
    resp = client.post(f"/api/chat/conversations/{conv_id}/attachments?token={bystander_token}", files=files, data={"body": ""})
    assert resp.status_code == 403


def test_attachment_download_requires_membership(client, auth_client):
    other_token, other_id = _register_and_login(client, "chirag_att", "Chirag")
    bystander_token, _ = _register_and_login(client, "bystander_att2", "Bystander")
    conv_id = _create_dm(auth_client, other_id)

    files = {"file": ("secret.txt", b"private content", "text/plain")}
    msg = auth_client.post(f"/api/chat/conversations/{conv_id}/attachments", files=files, data={"body": ""}).json()
    attachment_id = msg["attachments"][0]["id"]

    resp = client.get(f"/api/chat/attachments/{attachment_id}/content?token={bystander_token}")
    assert resp.status_code == 403


def test_attachment_becomes_inaccessible_after_message_deleted(client, auth_client):
    other_token, other_id = _register_and_login(client, "nimita_del_att", "Nimita")
    conv_id = _create_dm(auth_client, other_id)

    files = {"file": ("report.txt", b"quarterly report content", "text/plain")}
    msg = auth_client.post(f"/api/chat/conversations/{conv_id}/attachments", files=files, data={"body": ""}).json()
    attachment_id = msg["attachments"][0]["id"]

    before = client.get(f"/api/chat/attachments/{attachment_id}/content?token={other_token}")
    assert before.status_code == 200

    auth_client.delete(f"/api/chat/messages/{msg['id']}")

    after = client.get(f"/api/chat/attachments/{attachment_id}/content?token={other_token}")
    assert after.status_code == 404


def test_deleted_attachment_still_rejects_non_member(client, auth_client):
    """Existing membership authorization on the content endpoint must survive the deleted-check
    being added - a non-member gets the same 403 as ever, deleted or not."""
    other_token, other_id = _register_and_login(client, "yogesh_del_att2", "Yogesh")
    bystander_token, _ = _register_and_login(client, "bystander_del_att", "Bystander")
    conv_id = _create_dm(auth_client, other_id)

    files = {"file": ("private.txt", b"private content", "text/plain")}
    msg = auth_client.post(f"/api/chat/conversations/{conv_id}/attachments", files=files, data={"body": ""}).json()
    attachment_id = msg["attachments"][0]["id"]
    auth_client.delete(f"/api/chat/messages/{msg['id']}")

    resp = client.get(f"/api/chat/attachments/{attachment_id}/content?token={bystander_token}")
    assert resp.status_code == 403


def test_deleting_message_does_not_destroy_attachment_record(client, auth_client):
    """Deletion must be a content-access block only - the attachment metadata (and, by
    extension, the underlying blob) is never physically removed, preserving the audit trail."""
    other_token, other_id = _register_and_login(client, "samiksha_del_att", "Samiksha")
    conv_id = _create_dm(auth_client, other_id)

    files = {"file": ("evidence.txt", b"evidence content", "text/plain")}
    msg = auth_client.post(f"/api/chat/conversations/{conv_id}/attachments", files=files, data={"body": ""}).json()
    auth_client.delete(f"/api/chat/messages/{msg['id']}")

    history = auth_client.get(f"/api/chat/conversations/{conv_id}/messages").json()
    deleted = next(m for m in history if m["id"] == msg["id"])
    assert deleted["deleted_at"] is not None
    assert len(deleted["attachments"]) == 1
    assert deleted["attachments"][0]["file_name"] == "evidence.txt"


def test_attachment_upload_broadcasts_new_message_over_websocket(client, auth_client, auth_token):
    other_token, other_id = _register_and_login(client, "nimita_att2", "Nimita")
    conv_id = _create_dm(auth_client, other_id)

    with client.websocket_connect(f"/ws?token={other_token}") as ws:
        files = {"file": ("shared.txt", b"shared content", "text/plain")}
        auth_client.post(f"/api/chat/conversations/{conv_id}/attachments", files=files, data={"body": "check this file"})
        event = ws.receive_json()
        assert event["event"] == "new_message"
        assert event["data"]["message_type"] == "file"
        assert len(event["data"]["attachments"]) == 1


def test_search_finds_message_by_body_text(client, auth_client):
    other_token, other_id = _register_and_login(client, "yogesh_search", "Yogesh")
    conv_id = _create_dm(auth_client, other_id)

    auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "the quarterly loan disbursement report is ready"})
    auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "unrelated message about lunch"})

    resp = auth_client.get("/api/chat/search?q=disbursement")
    assert resp.status_code == 200
    bodies = [m["body"] for m in resp.json()]
    assert any("disbursement" in b for b in bodies)
    assert not any("lunch" in b for b in bodies)


def test_search_excludes_conversations_caller_is_not_in(client, auth_client):
    other_token, other_id = _register_and_login(client, "samiksha_search", "Samiksha")
    bystander_token, bystander_id = _register_and_login(client, "bystander_search", "Bystander")
    conv_id = _create_dm(auth_client, other_id)

    auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "confidential unique_search_term_xyz content"})

    resp = client.get(f"/api/chat/search?q=unique_search_term_xyz&token={bystander_token}")
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_excludes_deleted_messages(client, auth_client):
    other_token, other_id = _register_and_login(client, "amol_search", "Amol")
    conv_id = _create_dm(auth_client, other_id)

    msg = auth_client.post(f"/api/chat/conversations/{conv_id}/messages", json={"body": "findable_before_delete_marker"}).json()
    auth_client.delete(f"/api/chat/messages/{msg['id']}")

    resp = auth_client.get("/api/chat/search?q=findable_before_delete_marker")
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_scoped_to_one_conversation_requires_membership(client, auth_client):
    other_token, other_id = _register_and_login(client, "chirag_search", "Chirag")
    bystander_token, _ = _register_and_login(client, "bystander_search2", "Bystander")
    conv_id = _create_dm(auth_client, other_id)

    resp = client.get(f"/api/chat/search?q=anything&conversation_id={conv_id}&token={bystander_token}")
    assert resp.status_code == 403
