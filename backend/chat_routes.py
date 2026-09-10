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
import re
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, Response, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from auth import decode_token
from schemas import (
    ChatUserResponse, ConversationCreate, ConversationResponse, MarkReadRequest,
    MessageAttachmentResponse, MessageCreate, MessageEditRequest, MessageResponse,
)

IS_MYSQL = bool(os.getenv("DATABASE_URL"))
if IS_MYSQL:
    from database_mysql import get_db
else:
    from database_sqlite import get_db

# Attachments (Phase 2A-iii): validated allow-list rather than accepting anything, and a size
# ceiling generous enough for a scanned document or a phone photo without inviting someone to
# park large files in the database (Render's free tier has no persistent disk, so every
# attachment lives here as a LONGBLOB - see message_attachments in database_mysql.py).
ALLOWED_ATTACHMENT_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
}
MAX_ATTACHMENT_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB

_MENTION_RE = re.compile(r"@(\w+)")

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
    next load/reconnect.

    jsonable_encoder is required here, not optional: `event["data"]` can be a raw DB row dict
    (e.g. a message with a `created_at` field) and PyMySQL's DictCursor returns DATETIME columns
    as native `datetime.datetime` objects (unlike SQLite, which returns plain strings) - a bare
    `ws.send_json()` calls `json.dumps()` directly and raises TypeError on those, which would
    silently be swallowed by the except below and falsely mark a perfectly healthy socket as
    dead. jsonable_encoder applies the same datetime->ISO-string conversion FastAPI's REST
    response_model already does automatically, so the WS and REST payloads stay consistent."""
    encoded = jsonable_encoder(event)
    dead = []
    for user_id in user_ids:
        for ws in list(_connections.get(user_id, ())):
            try:
                await ws.send_json(encoded)
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


def _conversation_to_dict(cursor, conv_row, viewer_id: int) -> dict:
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

    # Unread count (Phase 2A-ii): everything after the viewer's own last_read_message_id -
    # NULL (never read anything here) is treated as 0 so every message counts as unread.
    cursor.execute(
        "SELECT last_read_message_id FROM conversation_members WHERE conversation_id = ? AND user_id = ?",
        (conv["id"], viewer_id),
    )
    read_row = cursor.fetchone()
    last_read_id = (read_row["last_read_message_id"] if read_row else None) or 0
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM messages WHERE conversation_id = ? AND id > ?",
        (conv["id"], last_read_id),
    )
    conv["unread_count"] = cursor.fetchone()["cnt"]

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


def _extract_mentions(cursor, conversation_id: int, body: str):
    """Parses @username tokens out of a message body and resolves them against real,
    currently-active members of THIS conversation - never trusted from the client, and never
    resolves to someone who isn't actually in the conversation (mentioning an outsider is not
    possible, there's no one for the notification to reach anyway)."""
    if not body:
        return []
    usernames = {m.lower() for m in _MENTION_RE.findall(body)}
    if not usernames:
        return []
    placeholders = ",".join(["?"] * len(usernames))
    cursor.execute(
        f"""
        SELECT users.id FROM users
        JOIN conversation_members ON conversation_members.user_id = users.id
        WHERE conversation_members.conversation_id = ? AND conversation_members.left_at IS NULL
        AND LOWER(users.username) IN ({placeholders})
        """,
        (conversation_id, *usernames),
    )
    return [row["id"] for row in cursor.fetchall()]


def _row_to_message_dict(cursor, message_id: int) -> dict:
    """Assembles the full MessageResponse shape for one message - mentions and attachments are
    separate queries (this codebase's convention throughout, matching _conversation_to_dict's
    members lookup) rather than a join, since a message has at most a handful of either."""
    cursor.execute(
        "SELECT messages.*, users.full_name as sender_name FROM messages JOIN users ON users.id = messages.sender_id WHERE messages.id = ?",
        (message_id,),
    )
    message = dict(cursor.fetchone())
    cursor.execute("SELECT mentioned_user_id FROM message_mentions WHERE message_id = ?", (message_id,))
    message["mentioned_user_ids"] = [row["mentioned_user_id"] for row in cursor.fetchall()]
    cursor.execute(
        "SELECT id, message_id, file_name, content_type, file_size, uploaded_by, created_at FROM message_attachments WHERE message_id = ?",
        (message_id,),
    )
    message["attachments"] = [dict(row) for row in cursor.fetchall()]
    return message


def _enrich_messages(cursor, rows: list) -> list:
    """Batch-attaches mentioned_user_ids/attachments to a list of raw message rows (from
    `messages.*`) in 2 extra queries total, regardless of list size - used by get_messages and
    search, where per-row lookups (as in _row_to_message_dict) would be N+1."""
    messages = [dict(r) for r in rows]
    message_ids = [m["id"] for m in messages]
    if not message_ids:
        return messages

    placeholders = ",".join(["?"] * len(message_ids))
    mentions_by_msg = {}
    cursor.execute(f"SELECT message_id, mentioned_user_id FROM message_mentions WHERE message_id IN ({placeholders})", tuple(message_ids))
    for row in cursor.fetchall():
        mentions_by_msg.setdefault(row["message_id"], []).append(row["mentioned_user_id"])

    attachments_by_msg = {}
    cursor.execute(
        f"SELECT id, message_id, file_name, content_type, file_size, uploaded_by, created_at FROM message_attachments WHERE message_id IN ({placeholders})",
        tuple(message_ids),
    )
    for row in cursor.fetchall():
        attachments_by_msg.setdefault(row["message_id"], []).append(dict(row))

    for m in messages:
        m["mentioned_user_ids"] = mentions_by_msg.get(m["id"], [])
        m["attachments"] = attachments_by_msg.get(m["id"], [])
    return messages


def _require_sender(cursor, message_id: int, user_id: int) -> dict:
    """Only the original sender may edit or delete a message - never another employee, even an
    admin (an admin's oversight comes from the message_edits audit trail, not delete-override
    power - see the Phase 2A-iii design notes)."""
    cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Message not found")
    msg = dict(row)
    if msg["deleted_at"]:
        raise HTTPException(status_code=400, detail="This message has already been deleted")
    if msg["sender_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit or delete your own messages")
    return msg


def _valid_reply_target(cursor, conversation_id: int, reply_to_message_id: Optional[int]) -> bool:
    """A reply reference is valid only if it points to a real message in the SAME conversation
    as the new message - never trusted from the client. Deliberately returns a plain bool
    rather than distinguishing "doesn't exist" from "exists in a different conversation": both
    must fail identically, so this can never be used to probe whether a message ID exists in a
    conversation the caller isn't a member of."""
    if reply_to_message_id is None:
        return True
    cursor.execute(
        "SELECT 1 FROM messages WHERE id = ? AND conversation_id = ?",
        (reply_to_message_id, conversation_id),
    )
    return cursor.fetchone() is not None


def _valid_lead_target(cursor, lead_id: Optional[int]) -> bool:
    """A lead link is valid only if it references a real lead. Unlike reply targets, leads
    aren't conversation-scoped, so this only checks existence - authorization comes entirely
    from the normal conversation-membership check that already runs before this in every call
    site (see the Phase 2B-i design notes: this must never become a way to bypass that).
    Permission model here inherits GET /api/leads/{id}'s existing semantics (any authenticated
    employee can view any lead) - no new lead-level permission system is introduced; that's
    explicitly deferred to Phase 2D."""
    if lead_id is None:
        return True
    cursor.execute("SELECT 1 FROM leads WHERE id = ?", (lead_id,))
    return cursor.fetchone() is not None


def _valid_contact_target(cursor, contact_id: Optional[int]) -> bool:
    """A contact link is valid only if it references a real contact. Same existence-only shape
    as _valid_lead_target (Phase 2B-i) - kept as a separate function against a separate table
    rather than a generic "linked CRM record" check, since messages.lead_id and
    messages.contact_id are deliberately kept as independent nullable columns (see the Phase
    2B-ii design notes: one column per entity, no polymorphic abstraction until more than one
    instance of this pattern justifies it). Permission model inherits GET /api/contacts's
    existing semantics (any authenticated employee can view any contact) - no new
    contact-level permission system is introduced; that's the same Phase 2D deferral as leads."""
    if contact_id is None:
        return True
    cursor.execute("SELECT 1 FROM contacts WHERE id = ?", (contact_id,))
    return cursor.fetchone() is not None


def _valid_deal_target(cursor, deal_id: Optional[int]) -> bool:
    """A deal link is valid only if it references a real deal. Same existence-only shape as
    _valid_lead_target/_valid_contact_target - third independent column, not a generic
    "linked CRM record" check, per the same Phase 2B-ii/2B-iii design notes: one column per
    entity, no polymorphic abstraction until the pattern demonstrably needs it (still doesn't,
    three instances in). Permission model inherits GET /api/deals's existing semantics (any
    authenticated employee can view any deal) - no new deal-level permission system is
    introduced; that's the same Phase 2D deferral as leads and contacts."""
    if deal_id is None:
        return True
    cursor.execute("SELECT 1 FROM deals WHERE id = ?", (deal_id,))
    return cursor.fetchone() is not None


def _valid_task_target(cursor, task_id: Optional[int]) -> bool:
    """A task link is valid only if it references a real task. Same existence-only shape as
    _valid_lead_target/_valid_contact_target/_valid_deal_target - fourth independent column, not
    a generic "linked CRM record" check, per the same Phase 2B design notes: one column per
    entity, no polymorphic abstraction until the pattern demonstrably needs it (still doesn't,
    four instances in). Permission model inherits GET /api/tasks's existing semantics (any
    authenticated employee can view any task) - no new task-level permission system is
    introduced; that's the same Phase 2D deferral as leads, contacts, and deals."""
    if task_id is None:
        return True
    cursor.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,))
    return cursor.fetchone() is not None


async def _create_message(
    conn, cursor, conversation_id: int, sender_id: int, body: str,
    message_type: str = "text", reply_to_message_id: Optional[int] = None,
    lead_id: Optional[int] = None, contact_id: Optional[int] = None,
    deal_id: Optional[int] = None, task_id: Optional[int] = None,
) -> dict:
    """Writes the message, resolves @mentions, updates the conversation's last_message_at, then
    broadcasts it to every current member - the one path the WebSocket handler, the REST send
    endpoint, and the attachment-upload endpoint all go through, so none of them can diverge."""
    cursor.execute(
        "INSERT INTO messages (conversation_id, sender_id, body, message_type, reply_to_message_id, lead_id, contact_id, deal_id, task_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
        (conversation_id, sender_id, body, message_type, reply_to_message_id, lead_id, contact_id, deal_id, task_id),
    )
    message_id = cursor.lastrowid
    cursor.execute(
        "UPDATE conversations SET last_message_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (conversation_id,),
    )

    for mentioned_user_id in _extract_mentions(cursor, conversation_id, body):
        cursor.execute(
            "INSERT INTO message_mentions (message_id, mentioned_user_id, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (message_id, mentioned_user_id),
        )

    conn.commit()

    message = _row_to_message_dict(cursor, message_id)

    cursor.execute(
        "SELECT user_id FROM conversation_members WHERE conversation_id = ? AND left_at IS NULL",
        (conversation_id,),
    )
    member_ids = [row["user_id"] for row in cursor.fetchall()]

    await broadcast_to_users(member_ids, {"event": "new_message", "data": message})
    return message


async def _mark_read(conn, cursor, conversation_id: int, user_id: int, up_to_message_id: int):
    """Updates the caller's read position and notifies every other current member - the one
    path both the WebSocket mark_read event and the REST fallback endpoint go through."""
    cursor.execute(
        "UPDATE conversation_members SET last_read_message_id = ? WHERE conversation_id = ? AND user_id = ?",
        (up_to_message_id, conversation_id, user_id),
    )
    conn.commit()
    cursor.execute(
        "SELECT user_id FROM conversation_members WHERE conversation_id = ? AND left_at IS NULL AND user_id != ?",
        (conversation_id, user_id),
    )
    other_ids = [row["user_id"] for row in cursor.fetchall()]
    await broadcast_to_users(
        other_ids,
        {"event": "read_receipt", "data": {"conversation_id": conversation_id, "user_id": user_id, "up_to_message_id": up_to_message_id}},
    )


def add_user_to_all_channels(cursor, conn, user_id: int):
    """Called from main.py's POST /api/auth/register right after a new user account is created,
    so a newly onboarded employee is immediately a member of every existing fixed channel -
    without this, they'd only get channel membership on the next server restart (when
    database_mysql.py/database_sqlite.py's _ensure_chat_channels() next runs)."""
    cursor.execute("SELECT id FROM conversations WHERE type = 'channel'")
    channel_ids = [row["id"] for row in cursor.fetchall()]
    for channel_id in channel_ids:
        cursor.execute(
            "SELECT 1 FROM conversation_members WHERE conversation_id = ? AND user_id = ?",
            (channel_id, user_id),
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO conversation_members (conversation_id, user_id, role_in_conversation, joined_at) "
                "VALUES (?, ?, 'member', CURRENT_TIMESTAMP)",
                (channel_id, user_id),
            )
    conn.commit()


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
        return [_conversation_to_dict(cursor, row, user["user_id"]) for row in rows]


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
                return _conversation_to_dict(cursor, cursor.fetchone(), user["user_id"])

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
        return _conversation_to_dict(cursor, cursor.fetchone(), user["user_id"])


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: int, token: str = Query(None)):
    user = get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        _require_member(cursor, conversation_id, user["user_id"])
        cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        return _conversation_to_dict(cursor, cursor.fetchone(), user["user_id"])


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
        rows = _enrich_messages(cursor, cursor.fetchall())

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
        if not _valid_reply_target(cursor, conversation_id, payload.reply_to_message_id):
            raise HTTPException(status_code=400, detail="Invalid reply_to_message_id")
        if not _valid_lead_target(cursor, payload.lead_id):
            raise HTTPException(status_code=400, detail="Invalid lead_id")
        if not _valid_contact_target(cursor, payload.contact_id):
            raise HTTPException(status_code=400, detail="Invalid contact_id")
        if not _valid_deal_target(cursor, payload.deal_id):
            raise HTTPException(status_code=400, detail="Invalid deal_id")
        if not _valid_task_target(cursor, payload.task_id):
            raise HTTPException(status_code=400, detail="Invalid task_id")
        return await _create_message(
            conn, cursor, conversation_id, user["user_id"], payload.body.strip(),
            reply_to_message_id=payload.reply_to_message_id, lead_id=payload.lead_id,
            contact_id=payload.contact_id, deal_id=payload.deal_id, task_id=payload.task_id,
        )


@router.put("/messages/{message_id}", response_model=MessageResponse)
async def edit_message(message_id: int, payload: MessageEditRequest, token: str = Query(None)):
    """Only the sender may edit their own message. The pre-edit body is written to
    message_edits BEFORE messages.body is touched, so nothing is ever silently lost."""
    user = get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        msg = _require_sender(cursor, message_id, user["user_id"])
        cursor.execute(
            "INSERT INTO message_edits (message_id, edited_by, previous_body, edit_type, edited_at) VALUES (?, ?, ?, 'edit', CURRENT_TIMESTAMP)",
            (message_id, user["user_id"], msg["body"]),
        )
        cursor.execute(
            "UPDATE messages SET body = ?, edited_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payload.body.strip(), message_id),
        )
        conn.commit()

        updated = _row_to_message_dict(cursor, message_id)
        cursor.execute(
            "SELECT user_id FROM conversation_members WHERE conversation_id = ? AND left_at IS NULL",
            (msg["conversation_id"],),
        )
        member_ids = [row["user_id"] for row in cursor.fetchall()]

    await broadcast_to_users(member_ids, {"event": "message_edited", "data": updated})
    return updated


@router.delete("/messages/{message_id}", response_model=MessageResponse)
async def delete_message(message_id: int, token: str = Query(None)):
    """Soft delete only - the row (and its pre-delete content) survives in message_edits, so
    this is a real audit trail, not silent deletion, while still making the message show as
    removed for every other reader (body cleared, deleted_at set)."""
    user = get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        msg = _require_sender(cursor, message_id, user["user_id"])
        cursor.execute(
            "INSERT INTO message_edits (message_id, edited_by, previous_body, edit_type, edited_at) VALUES (?, ?, ?, 'delete', CURRENT_TIMESTAMP)",
            (message_id, user["user_id"], msg["body"]),
        )
        cursor.execute(
            "UPDATE messages SET body = NULL, deleted_at = CURRENT_TIMESTAMP WHERE id = ?",
            (message_id,),
        )
        conn.commit()

        updated = _row_to_message_dict(cursor, message_id)
        cursor.execute(
            "SELECT user_id FROM conversation_members WHERE conversation_id = ? AND left_at IS NULL",
            (msg["conversation_id"],),
        )
        member_ids = [row["user_id"] for row in cursor.fetchall()]

    await broadcast_to_users(member_ids, {"event": "message_deleted", "data": updated})
    return updated


@router.post("/conversations/{conversation_id}/attachments", response_model=MessageResponse)
async def upload_attachment(
    conversation_id: int,
    file: UploadFile = File(...),
    body: str = Form(""),
    token: str = Query(None),
):
    """Uploads a file/image as a new message - reuses the same DB-blob-plus-authenticated-
    stream pattern as contact_documents/calls.recording_file_data (see message_attachments in
    database_mysql.py), since Render's free tier has no persistent disk."""
    user = get_current_user(token)
    data = await file.read()
    if len(data) > MAX_ATTACHMENT_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"File too large - max {MAX_ATTACHMENT_SIZE_BYTES // (1024 * 1024)} MB")
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_ATTACHMENT_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"File type '{content_type}' is not allowed")

    with get_db() as conn:
        cursor = conn.cursor()
        _require_member(cursor, conversation_id, user["user_id"])

        message_type = "image" if content_type.startswith("image/") else "file"
        cursor.execute(
            "INSERT INTO messages (conversation_id, sender_id, body, message_type, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (conversation_id, user["user_id"], body.strip() or None, message_type),
        )
        message_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO message_attachments (message_id, file_name, content_type, file_size, file_data, uploaded_by, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (message_id, file.filename, content_type, len(data), data, user["user_id"]),
        )
        cursor.execute(
            "UPDATE conversations SET last_message_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,),
        )
        conn.commit()

        message = _row_to_message_dict(cursor, message_id)
        cursor.execute(
            "SELECT user_id FROM conversation_members WHERE conversation_id = ? AND left_at IS NULL",
            (conversation_id,),
        )
        member_ids = [row["user_id"] for row in cursor.fetchall()]

    await broadcast_to_users(member_ids, {"event": "new_message", "data": message})
    return message


@router.get("/attachments/{attachment_id}/content")
async def get_attachment_content(attachment_id: int, token: str = Query(None)):
    """Streams an attachment's bytes back - gated on membership in the conversation the
    attachment's message belongs to, never a public/unauthenticated URL. Once the parent
    message is deleted, content retrieval is blocked here too (same 404 as a missing
    attachment, so a deleted one is never distinguishable from one that never existed) - the
    underlying row and file bytes are left untouched, so the audit trail is unaffected."""
    user = get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT message_attachments.*, messages.conversation_id, messages.deleted_at FROM message_attachments "
            "JOIN messages ON messages.id = message_attachments.message_id WHERE message_attachments.id = ?",
            (attachment_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Attachment not found")
        attachment = dict(row)
        _require_member(cursor, attachment["conversation_id"], user["user_id"])
        if attachment["deleted_at"]:
            raise HTTPException(status_code=404, detail="Attachment not found")

    return Response(
        content=bytes(attachment["file_data"]),
        media_type=attachment["content_type"] or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{attachment["file_name"]}"'},
    )


@router.get("/search", response_model=list[MessageResponse])
async def search_messages(
    q: str = Query(..., min_length=1),
    conversation_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    token: str = Query(None),
):
    """Full-text search on MySQL (FULLTEXT/MATCH...AGAINST), a plain LIKE fallback on SQLite -
    always scoped to conversations the caller is actually a member of, even for an admin, and
    always excludes soft-deleted messages. `conversation_id` narrows to one conversation the
    caller must already belong to."""
    user = get_current_user(token)
    if conversation_id is not None:
        with get_db() as conn:
            cursor = conn.cursor()
            _require_member(cursor, conversation_id, user["user_id"])

    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT messages.*, users.full_name as sender_name
            FROM messages JOIN users ON users.id = messages.sender_id
            WHERE messages.conversation_id IN (
                SELECT conversation_id FROM conversation_members WHERE user_id = ? AND left_at IS NULL
            )
            AND messages.deleted_at IS NULL
        """
        params = [user["user_id"]]

        if IS_MYSQL:
            query += " AND MATCH(messages.body) AGAINST (? IN NATURAL LANGUAGE MODE)"
            params.append(q)
        else:
            query += " AND messages.body LIKE ?"
            params.append(f"%{q}%")

        if conversation_id is not None:
            query += " AND messages.conversation_id = ?"
            params.append(conversation_id)

        query += " ORDER BY messages.id DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, tuple(params))
        return _enrich_messages(cursor, cursor.fetchall())


@router.post("/conversations/{conversation_id}/read")
async def mark_conversation_read(conversation_id: int, payload: MarkReadRequest, token: str = Query(None)):
    """REST fallback for marking a conversation read when the WebSocket isn't connected - mirrors
    the WS mark_read event via the same _mark_read() function."""
    user = get_current_user(token)
    with get_db() as conn:
        cursor = conn.cursor()
        _require_member(cursor, conversation_id, user["user_id"])
        await _mark_read(conn, cursor, conversation_id, user["user_id"], payload.up_to_message_id)
    return {"ok": True}


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
                reply_to_message_id = data.get("reply_to_message_id")
                lead_id = data.get("lead_id")
                contact_id = data.get("contact_id")
                deal_id = data.get("deal_id")
                task_id = data.get("task_id")
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
                    if not _valid_reply_target(cursor, conversation_id, reply_to_message_id):
                        await websocket.send_json({"event": "error", "data": {"message": "Invalid reply_to_message_id"}})
                        continue
                    if not _valid_lead_target(cursor, lead_id):
                        await websocket.send_json({"event": "error", "data": {"message": "Invalid lead_id"}})
                        continue
                    if not _valid_contact_target(cursor, contact_id):
                        await websocket.send_json({"event": "error", "data": {"message": "Invalid contact_id"}})
                        continue
                    if not _valid_deal_target(cursor, deal_id):
                        await websocket.send_json({"event": "error", "data": {"message": "Invalid deal_id"}})
                        continue
                    if not _valid_task_target(cursor, task_id):
                        await websocket.send_json({"event": "error", "data": {"message": "Invalid task_id"}})
                        continue
                    await _create_message(conn, cursor, conversation_id, user_id, body, reply_to_message_id=reply_to_message_id, lead_id=lead_id, contact_id=contact_id, deal_id=deal_id, task_id=task_id)

            elif event in ("typing_start", "typing_stop"):
                conversation_id = data.get("conversation_id")
                if not conversation_id:
                    continue
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT 1 FROM conversation_members WHERE conversation_id = ? AND user_id = ? AND left_at IS NULL",
                        (conversation_id, user_id),
                    )
                    if not cursor.fetchone():
                        continue
                    cursor.execute(
                        "SELECT user_id FROM conversation_members WHERE conversation_id = ? AND left_at IS NULL AND user_id != ?",
                        (conversation_id, user_id),
                    )
                    other_ids = [row["user_id"] for row in cursor.fetchall()]
                await broadcast_to_users(
                    other_ids,
                    {"event": "typing", "data": {"conversation_id": conversation_id, "user_id": user_id, "is_typing": event == "typing_start"}},
                )

            elif event == "mark_read":
                conversation_id = data.get("conversation_id")
                up_to_message_id = data.get("up_to_message_id")
                if not conversation_id or up_to_message_id is None:
                    continue
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT 1 FROM conversation_members WHERE conversation_id = ? AND user_id = ? AND left_at IS NULL",
                        (conversation_id, user_id),
                    )
                    if not cursor.fetchone():
                        continue
                    await _mark_read(conn, cursor, conversation_id, user_id, up_to_message_id)

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
