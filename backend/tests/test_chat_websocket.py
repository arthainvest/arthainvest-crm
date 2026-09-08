"""ArthaInvest Connect (Phase 2A-i): WebSocket contract tests, via FastAPI's
client.websocket_connect - same TestClient(main.app) instance used by every REST test in this
suite, so no special test infrastructure is needed for real-time delivery either."""
import asyncio
import json
from datetime import datetime

import chat_routes


class _FakeWebSocket:
    """Mimics Starlette's WebSocket.send_json enough to reproduce a real production bug: it
    actually round-trips the payload through json.dumps()/json.loads(), since that's the
    operation that chokes on a raw datetime object - a stub that just stores the object
    without serializing it would not catch this."""
    def __init__(self):
        self.sent = []

    async def send_json(self, data):
        self.sent.append(json.loads(json.dumps(data)))


def test_broadcast_to_users_serializes_datetime_fields_without_raising():
    """Regression test for a real bug found during production verification: PyMySQL's
    DictCursor returns DATETIME columns as native datetime.datetime objects (unlike SQLite,
    which returns plain strings) - this test suite runs entirely against SQLite, so it would
    never otherwise exercise that value shape. A bare ws.send_json() on a dict containing one
    of these raises TypeError inside broadcast_to_users's try/except, which used to silently
    swallow it and falsely mark a perfectly healthy socket as dead - a message would save
    correctly but never broadcast live, exactly what was observed against the real deployed
    MySQL backend before this fix (jsonable_encoder in broadcast_to_users)."""
    fake_ws = _FakeWebSocket()
    chat_routes._connections[999999] = {fake_ws}
    try:
        event = {
            "event": "new_message",
            "data": {
                "id": 1, "conversation_id": 1, "sender_id": 1, "sender_name": "Test User",
                "body": "hello", "message_type": "text",
                "created_at": datetime(2026, 9, 8, 7, 26, 35),  # PyMySQL's actual return type
            },
        }
        asyncio.run(chat_routes.broadcast_to_users([999999], event))

        assert len(fake_ws.sent) == 1
        assert fake_ws.sent[0]["data"]["created_at"] == "2026-09-08T07:26:35"
        assert fake_ws in chat_routes._connections.get(999999, set()), (
            "socket was falsely marked dead and unregistered - the exact symptom of the bug this guards against"
        )
    finally:
        chat_routes._connections.pop(999999, None)


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


def _create_dm(client, token, other_user_id):
    resp = client.post(
        f"/api/chat/conversations?token={token}",
        json={"type": "dm", "member_user_ids": [other_user_id]},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def test_websocket_rejects_missing_or_invalid_token(client):
    import pytest
    from starlette.websockets import WebSocketDisconnect

    # Server closes with code 4401 before ever accepting the connection - the test client
    # surfaces that as the `with` block itself raising, not a receive() call inside it.
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws"):
            pass
    assert exc_info.value.code == 4401

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws?token=not-a-real-token"):
            pass
    assert exc_info.value.code == 4401


def test_websocket_ping_pong(client, auth_token):
    with client.websocket_connect(f"/ws?token={auth_token}") as ws:
        ws.send_json({"event": "ping"})
        assert ws.receive_json() == {"event": "pong", "data": {}}


def test_websocket_send_message_delivered_live_to_other_member(client, auth_token):
    other_token, other_id = _register_and_login(client, "yogesh", "Yogesh")
    conv_id = _create_dm(client, auth_token, other_id)

    with client.websocket_connect(f"/ws?token={auth_token}") as ws1, \
         client.websocket_connect(f"/ws?token={other_token}") as ws2:
        # ws1 connected first, so it receives ws2's connect as a presence event before any
        # chat traffic - drain it so the next receive is deterministically the chat message.
        presence = ws1.receive_json()
        assert presence["event"] == "presence"
        assert presence["data"]["status"] == "online"

        ws1.send_json({"event": "send_message", "data": {"conversation_id": conv_id, "body": "Hello there"}})

        delivered = ws2.receive_json()
        assert delivered["event"] == "new_message"
        assert delivered["data"]["body"] == "Hello there"
        assert delivered["data"]["sender_name"] == "Test User"

        # The sender also receives their own message broadcast (matches how every member,
        # sender included, sees the row - the frontend is expected to reconcile this against
        # its own optimistic UI update, the same pattern used elsewhere in this app).
        echoed_to_sender = ws1.receive_json()
        assert echoed_to_sender["data"]["body"] == "Hello there"


def test_websocket_send_message_rejects_non_member(client, auth_token):
    with client.websocket_connect(f"/ws?token={auth_token}") as ws:
        ws.send_json({"event": "send_message", "data": {"conversation_id": 999999, "body": "nope"}})
        err = ws.receive_json()
        assert err["event"] == "error"


def test_websocket_unknown_event_type_returns_error(client, auth_token):
    with client.websocket_connect(f"/ws?token={auth_token}") as ws:
        ws.send_json({"event": "not_a_real_event"})
        err = ws.receive_json()
        assert err["event"] == "error"


def test_reconnect_catch_up_recovers_messages_sent_while_disconnected(client, auth_token):
    """The core reliability guarantee: a client that was disconnected (e.g. during a Render
    restart) must be able to recover every message sent in the gap via the after_id REST
    catch-up query - no WebSocket session should be the only place a message exists."""
    other_token, other_id = _register_and_login(client, "samiksha", "Samiksha")
    conv_id = _create_dm(client, auth_token, other_id)

    # ws1 "goes offline" (context exits / closes) - then a message is sent via REST (as if
    # the other party sent it while ws1 was disconnected).
    with client.websocket_connect(f"/ws?token={auth_token}") as ws1:
        pass  # connect then immediately disconnect

    sent = client.post(
        f"/api/chat/conversations/{conv_id}/messages?token={other_token}",
        json={"body": "Sent while you were away"},
    )
    assert sent.status_code == 200
    last_seen_id = 0  # ws1 had seen nothing yet

    catch_up = client.get(
        f"/api/chat/conversations/{conv_id}/messages?after_id={last_seen_id}&token={auth_token}"
    )
    assert catch_up.status_code == 200
    bodies = [m["body"] for m in catch_up.json()]
    assert "Sent while you were away" in bodies


def test_presence_broadcast_excludes_the_connecting_user_themselves(client, auth_token):
    """A user should never receive a "you are now online" echo of their own connect - only
    other members of a shared conversation should see that presence event."""
    other_token, other_id = _register_and_login(client, "amol", "Amol")
    _create_dm(client, auth_token, other_id)

    with client.websocket_connect(f"/ws?token={auth_token}") as ws:
        ws.send_json({"event": "ping"})
        first = ws.receive_json()
        # If self-presence leaked, this would be a presence event instead of the pong we
        # just asked for - proves connecting doesn't queue a self-echo ahead of it.
        assert first == {"event": "pong", "data": {}}
