"""ArthaInvest Connect (Phase 2A-i): REST + WebSocket endpoints for internal real-time chat.

Kept out of main.py (already ~8700 lines) as its own APIRouter - the first module of its kind
in this codebase, following the same instinct that already split out calling_providers.py/
storage.py/db_compat.py. Deliberately does NOT import anything from main.py - this module
re-derives the tiny get_db/get_current_user primitives itself, the same way calling_providers.py
and storage.py are self-contained modules main.py imports rather than the other way around.

Design notes (see the approved Phase 2 plan for the full rationale):
- Every existing endpoint in this app authenticates via `token` as a URL query parameter, not
  an Authorization header - so `wss://.../ws?token=<jwt>` works with zero new auth plumbing.
- Render's free tier runs a single process (WEB_CONCURRENCY=1), so a plain in-memory
  connection registry is sufficient - no Redis/pub-sub needed at this scale.
- A message is always committed to the `messages` table BEFORE being broadcast over the
  WebSocket, so a dropped connection never loses data - only live-delivery. The REST endpoints
  below (`after_id` pagination, `updated_after` on the conversation list) are the actual source
  of truth a reconnecting client resyncs against; the WebSocket event is a live-delivery
  optimization layered on top of a row that already exists.
"""
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from auth import decode_token
from schemas import ChatUserResponse, ConversationCreate, ConversationResponse, MessageCreate, MessageResponse

if os.getenv("DATABASE_URL"):
    from database_mysql import get_db
else:
    from database_sqlite import get_db

router = APIRouter(prefix="/api/chat", tags=["chat"])
ws_router = APIRouter()


def get_current_user(token: str = None):
    """Same contract as main.py's get_current_user - duplicated rather than imported so this
    module has no import-time dependency on main.py (see module docstring)."""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_data = decode_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_data


# ============= In-memory WebSocket connection registry =============
# user_id -> set of live sockets (a set, not one socket, since one person may have the CRM
# open in more than one browser tab at once).
_connections: dict[int, set] = {}


def _register(user_id: int, ws: WebSocket):
    _connections.setdefault(user_id, set()).add(ws)


def _unregister(user_id: int, ws: WebSocket):
    sockets = _connections.get(user_id)
    if sockets:
        sockets.discard(ws)
        if not sockets:
            _connections.pop(user_id, None)


def _is_online(user_id: int) -> bool:
    return bool(_connections.get(user_id))


async def broadcast_to_users(user_ids, event: dict):
    """Send `event` to every currently-connected socket for each user in user_ids. Silently
    skips anyone offline - they never get it queued in memory, only via REST catch-up on their
    next load/reconnect."""
    dead = []
    for user_id in user_ids:
        for ws in list(_connections.get(user_id, ())):
            try:
                await ws.send_json(event)
            except Exception:
                dead.append((user_id, ws))
    for user_id, ws in dead:
        _unregister(user_id, ws)


# ============= Shared query helpers =============

def _require_member(cursor, conversation_id: int, user_id: int):
    cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Conversation not found")
    cursor.execute(
        "SELECT 1 FROM conversation_members WHERE conversation_id = ? AND user_id = ? AND left_at IS NULL",
        (conversation_id, user_id),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=403, detail="You are not a member of this conversation")


def _conversation_to_dict(cursor, conv_row) -> dict:
    conv = dict(conv_row)
    cursor.execute(
        """
        SELECT conversation_members.user_id, conversation_members.role_in_conversation,
               users.username, users.full_name
        FROM conversation_members
        JOIN users ON users.id = conversation_members.user_id
        WHERE conversation_members.conversation_id = ? AND conversation_members.left_at IS NULL
        """,
        (conv["id"],),
    )
    conv["members"] = [
        {**dict(row), "online": _is_online(row["user_id"])} for row in cursor.fetchall()
    ]
    return conv


def _co_member_ids(cursor, user_id: int):
    """Every OTHER user who currently shares at least one conversation with user_id - the
    audience for that user's presence (online/offline) broadcasts. Excludes user_id itself -
    without that, a user would receive a "you are now online" echo of their own connect/
    disconnect, which is noise, not information."""
    cursor.execute(
        """
        SELECT DISTINCT cm2.user_id FROM conversation_members cm1
        JOIN conversation_members cm2 ON cm2.conversation_id = cm1.conversation_id
        WHERE cm1.user_id = ? AND cm1.left_at IS NULL AND cm2.left_at IS NULL AND cm2.user_id != ?
        """,
        (user_id, user_id),
    )
    return [row["user_id"] for row in cursor.fetchall()]


async def _create_message(conn, cursor, conversation_id: int, sender_id: int, body: str, message_type: str = "text") -> dict:
    """Writes the message, updates the conversation's last_message_at, then broadcasts it to
    every current member - the one path both the WebSocket handler and the REST send endpoint
    go through, so the two can never diverge."""
    cursor.execute(
        "INSERT INTO messages (conversation_id, sender_id, body, message_type, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
        (conversation_id, sender_id, body, message_type),
    )
    message_id = cursor.lastrowid
    cursor.execute(
        "UPDATE conversations SET last_message_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (conversation_id,),
    )
    conn.commit()

    cursor.execute(
        "SELECT messages.*, users.full_name as sender_name FROM messages JOIN users ON users.id = messages.sender_id WHERE messages.id = ?",
        (message_id,),
    )
    message = dict(cursor.fetchone())

    cursor.execute(
        "SELECT user_id FROM conversation_members WHERE conversation_id = ? AND left_at IS NULL",
        (conversation_id,),
    )
    member_ids = [row["user_id"] for row in cursor.fetchall()]

    await broadcast_to_users(member_ids, {"event": "new_message", "data": message})
    return message


# ============= REST endpoints =============

@router.get("/users", response_model=list[ChatUserResponse])
async def list_chat_users(token: str = Query(None)):
    """Real login accounts eligible as chat participants - never fake/demo data. Available to
    any authenticated user (unlike the admin-only /api/auth/users) since anyone should be able
    to start a DM with any teammate."""
    get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, full_name FROM users WHERE is_active = 1 ORDER BY full_name")
        return [dict(row) for row in cursor.fetchall()]


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(updated_after: Optional[str] = Query(None), token: str = Query(None)):
    """The caller's conversations, most recently active first. `updated_after` (a
    'YYYY-MM-DD HH:MM:SS' timestamp) is the reconnect catch-up query - it returns only
    conversations with new activity since the client's last sync, per the WebSocket contract's
    reconnect design."""
    user = get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT conversations.*,
                   (SELECT body FROM messages WHERE messages.conversation_id = conversations.id
                    ORDER BY messages.id DESC LIMIT 1) as last_message_body,
                   (SELECT sender_id FROM messages WHERE messages.conversation_id = conversations.id
                    ORDER BY messages.id DESC LIMIT 1) as last_message_sender_id
            FROM conversations
            JOIN conversation_members ON conversation_members.conversation_id = conversations.id
            WHERE conversation_members.user_id = ? AND conversation_members.left_at IS NULL
        """
        params = [user["user_id"]]
        if updated_after:
            query += " AND COALESCE(conversations.last_message_at, conversations.created_at) > ?"
            params.append(updated_after)
        query += " ORDER BY COALESCE(conversations.last_message_at, conversations.created_at) DESC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [_conversation_to_dict(cursor, row) for row in rows]


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(payload: ConversationCreate, token: str = Query(None)):
    user = get_current_user(token)
    if payload.type not in ("dm", "group"):
        raise HTTPException(status_code=400, detail="type must be 'dm' or 'group'")

    member_ids = sorted(set(payload.member_user_ids) | {user["user_id"]})
    if payload.type == "dm" and len(member_ids) != 2:
        raise HTTPException(status_code=400, detail="A DM must have exactly 2 participants")
    if payload.type == "group" and len(member_ids) < 2:
        raise HTTPException(status_code=400, detail="A group needs at least 2 participants")

    with get_db() as conn:
        cursor = conn.cursor()

        placeholders = ",".join(["?"] * len(member_ids))
        cursor.execute(f"SELECT id FROM users WHERE id IN ({placeholders})", tuple(member_ids))
        found_ids = {row["id"] for row in cursor.fetchall()}
        missing = set(member_ids) - found_ids
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown user id(s): {sorted(missing)}")

        if payload.type == "dm":
            # Reuse an existing DM between exactly these two people rather than creating a
            # duplicate - a DM is treated as a fixed pair, same as most chat products.
            other_id = next(uid for uid in member_ids if uid != user["user_id"])
            cursor.execute(
                """
                SELECT conversations.id FROM conversations
                WHERE conversations.type = 'dm'
                AND conversations.id IN (
                    SELECT conversation_id FROM conversation_members WHERE user_id = ? AND left_at IS NULL
                )
                AND conversations.id IN (
                    SELECT conversation_id FROM conversation_members WHERE user_id = ? AND left_at IS NULL
                )
                """,
                (user["user_id"], other_id),
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute("SELECT * FROM conversations WHERE id = ?", (existing["id"],))
                return _conversation_to_dict(cursor, cursor.fetchone())

        cursor.execute(
            "INSERT INTO conversations (type, name, created_by, created_at, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (payload.type, payload.name, user["user_id"]),
        )
        conversation_id = cursor.lastrowid

        for member_id in member_ids:
            role = "owner" if member_id == user["user_id"] else "member"
            cursor.execute(
                "INSERT INTO conversation_members (conversation_id, user_id, role_in_conversation, joined_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (conversation_id, member_id, role),
            )
        conn.commit()

        cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        return _conversation_to_dict(cursor, cursor.fetchone())


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: int, token: str = Query(None)):
    user = get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        _require_member(cursor, conversation_id, user["user_id"])
        cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        return _conversation_to_dict(cursor, cursor.fetchone())


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: int,
    after_id: Optional[int] = Query(None),
    before_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    token: str = Query(None),
):
    """Cursor-based paginated history. `after_id` is the reconnect catch-up query - it returns
    messages chronologically (oldest of the batch first). Without `after_id`/`before_id`, it
    returns the most recent `limit` messages in chronological order (the normal
    open-a-conversation case)."""
    user = get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        _require_member(cursor, conversation_id, user["user_id"])

        query = """
            SELECT messages.*, users.full_name as sender_name
            FROM messages JOIN users ON users.id = messages.sender_id
            WHERE messages.conversation_id = ?
        """
        params = [conversation_id]
        if after_id is not None:
            query += " AND messages.id > ?"
            params.append(after_id)
        if before_id is not None:
            query += " AND messages.id < ?"
            params.append(before_id)

        if after_id is not None:
            query += " ORDER BY messages.id ASC LIMIT ?"
        else:
            query += " ORDER BY messages.id DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, tuple(params))
        rows = [dict(row) for row in cursor.fetchall()]

    if after_id is None:
        rows.reverse()
    return rows


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message_rest(conversation_id: int, payload: MessageCreate, token: str = Query(None)):
    """REST fallback for sending a message when the WebSocket isn't connected. Goes through the
    same _create_message() the WebSocket handler uses, so a REST-sent message is logged and
    broadcast identically to a WS-sent one."""
    user = get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        _require_member(cursor, conversation_id, user["user_id"])
        return await _create_message(conn, cursor, conversation_id, user["user_id"], payload.body.strip())


# ============= WebSocket =============

@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    user_data = decode_token(token) if token else None
    if not user_data:
        await websocket.close(code=4401)
        return

    user_id = user_data["user_id"]
    await websocket.accept()
    _register(user_id, websocket)

    with get_db() as conn:
        cursor = conn.cursor()
        co_members = _co_member_ids(cursor, user_id)
    await broadcast_to_users(co_members, {"event": "presence", "data": {"user_id": user_id, "status": "online"}})

    try:
        while True:
            payload = await websocket.receive_json()
            event = payload.get("event")
            data = payload.get("data") or {}

            if event == "send_message":
                conversation_id = data.get("conversation_id")
                body = (data.get("body") or "").strip()
                if not conversation_id or not body:
                    await websocket.send_json({"event": "error", "data": {"message": "conversation_id and body are required"}})
                    continue
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT 1 FROM conversation_members WHERE conversation_id = ? AND user_id = ? AND left_at IS NULL",
                        (conversation_id, user_id),
                    )
                    if not cursor.fetchone():
                        await websocket.send_json({"event": "error", "data": {"message": "Not a member of this conversation"}})
                        continue
                    await _create_message(conn, cursor, conversation_id, user_id, body)

            elif event == "ping":
                await websocket.send_json({"event": "pong", "data": {}})

            else:
                await websocket.send_json({"event": "error", "data": {"message": f"Unknown event type: {event}"}})

    except WebSocketDisconnect:
        pass
    finally:
        _unregister(user_id, websocket)
        with get_db() as conn:
            cursor = conn.cursor()
            co_members = _co_member_ids(cursor, user_id)
        await broadcast_to_users(co_members, {"event": "presence", "data": {"user_id": user_id, "status": "offline"}})
