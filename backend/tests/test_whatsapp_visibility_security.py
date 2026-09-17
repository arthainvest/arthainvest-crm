"""Security tests for WhatsApp Inbox access control (Gate N-1/N-2).

WhatsApp conversations are created by an inbound customer message, not by an employee, so this
table has no created_by and only a single ownership column: assigned_user_id (-> users.id).
Every route was previously authenticated-only (get_current_user) with a `mine_only` opt-in
filter that defaulted to False and had no manager-hierarchy expansion - any employee could see,
reply to, reassign, close, or opt-out any other employee's customer conversation by default.

Locked business rules (N-1 discovery, N-2 implementation):
  - Admins (Nimita/Yogesh): unrestricted, including unassigned conversations.
  - A manager (Samiksha) sees own + direct reports' (Chirag, Amol) assigned conversations, PLUS
    unassigned conversations (so someone can claim them).
  - An individual employee (Chirag, Amol) sees only conversations assigned to themselves - never
    unassigned conversations, never a peer's or their manager's.
  - Assignment target authorization is independent of visibility: admin -> anyone; manager ->
    herself + her reports; employee -> self only.
  - Reply/status/opt-out require the SAME visibility check as read access, checked before any
    mutation and before any real Meta API call.
"""
from unittest.mock import patch


class _TokenedClient:
    def __init__(self, client, token):
        self._c = client
        self._t = token

    def _url(self, path):
        sep = '&' if '?' in path else '?'
        return f"{path}{sep}token={self._t}"

    def get(self, path, **kw):
        return self._c.get(self._url(path), **kw)

    def post(self, path, **kw):
        return self._c.post(self._url(path), **kw)

    def put(self, path, **kw):
        return self._c.put(self._url(path), **kw)

    def delete(self, path, **kw):
        return self._c.delete(self._url(path), **kw)


def _register_and_login(client, admin_token, username, role="employee"):
    resp = client.post(
        f"/api/auth/register?token={admin_token}",
        json={
            "username": username, "email": f"{username}@example.com",
            "password": "pass12345", "full_name": username, "role": role,
        },
    )
    assert resp.status_code == 200, resp.text
    user_id = resp.json()["id"]
    login = client.post("/api/auth/login", json={"username": username, "password": "pass12345"})
    assert login.status_code == 200, login.text
    return user_id, login.json()["access_token"]


def hierarchy(client, auth_client, auth_token):
    yogesh_user_id, yogesh_token = _register_and_login(client, auth_token, "yogesh_wa", role="admin")
    samiksha_user_id, samiksha_token = _register_and_login(client, auth_token, "samiksha_wa")
    chirag_user_id, chirag_token = _register_and_login(client, auth_token, "chirag_wa")
    amol_user_id, amol_token = _register_and_login(client, auth_token, "amol_wa")

    samiksha_tm = auth_client.post("/api/team", json={"name": "Samiksha WA", "role": "employee"}).json()
    chirag_tm = auth_client.post("/api/team", json={"name": "Chirag WA", "role": "employee"}).json()
    amol_tm = auth_client.post("/api/team", json={"name": "Amol WA", "role": "employee"}).json()

    assert auth_client.put(f"/api/team/{samiksha_tm['id']}", json={"user_id": samiksha_user_id}).status_code == 200
    assert auth_client.put(f"/api/team/{chirag_tm['id']}", json={"user_id": chirag_user_id, "reports_to": samiksha_tm['id']}).status_code == 200
    assert auth_client.put(f"/api/team/{amol_tm['id']}", json={"user_id": amol_user_id, "reports_to": samiksha_tm['id']}).status_code == 200

    return {
        "nimita": auth_client,
        "yogesh": _TokenedClient(client, yogesh_token), "yogesh_id": yogesh_user_id,
        "samiksha": _TokenedClient(client, samiksha_token), "samiksha_id": samiksha_user_id,
        "chirag": _TokenedClient(client, chirag_token), "chirag_id": chirag_user_id,
        "amol": _TokenedClient(client, amol_token), "amol_id": amol_user_id,
    }


_next_phone = [919980000000]


def _inbound(client, body="Hi"):
    """Simulates an inbound customer WhatsApp message via the (intentionally unauthenticated)
    webhook, creating an unassigned conversation - mirrors the exact real-world creation path,
    with a fresh phone number each call so conversations never collide."""
    _next_phone[0] += 1
    phone = str(_next_phone[0])
    client.post("/api/webhooks/whatsapp", json={
        "entry": [{"changes": [{"value": {"messages": [{
            "from": phone, "id": f"wamid.SEC{_next_phone[0]}", "type": "text", "text": {"body": body}
        }]}}]}]
    })
    return phone


def _convo_id_for_phone(nimita, phone):
    convos = nimita.get("/api/whatsapp/conversations").json()
    return next(c["id"] for c in convos if c["wa_number"] == phone)


def _make_assigned_convo(h, assignee_user_id, body="Hi"):
    """Creates an unassigned conversation then has the admin assign it - admin bypasses both
    the visibility and assignment-target checks, so this is a safe, neutral way to set up test
    fixtures without depending on the very rules under test."""
    phone = _inbound(h["_client"], body)
    convo_id = _convo_id_for_phone(h["nimita"], phone)
    assert h["nimita"].put(f"/api/whatsapp/conversations/{convo_id}/assign", json={"user_id": assignee_user_id}).status_code == 200
    return convo_id


# ---------------------------------------------------------------------------
# List visibility
# ---------------------------------------------------------------------------

def test_admin_sees_everything_including_unassigned(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    chirag_convo = _make_assigned_convo(h, h["chirag_id"])
    unassigned_phone = _inbound(client)

    for admin in (h["nimita"], h["yogesh"]):
        ids = {c["id"] for c in admin.get("/api/whatsapp/conversations").json()}
        assert chirag_convo in ids
        assert _convo_id_for_phone(h["nimita"], unassigned_phone) in ids


def test_manager_sees_own_reports_and_unassigned(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    chirag_convo = _make_assigned_convo(h, h["chirag_id"])
    amol_convo = _make_assigned_convo(h, h["amol_id"])
    samiksha_convo = _make_assigned_convo(h, h["samiksha_id"])
    unassigned_phone = _inbound(client)

    ids = {c["id"] for c in h["samiksha"].get("/api/whatsapp/conversations").json()}
    assert chirag_convo in ids
    assert amol_convo in ids
    assert samiksha_convo in ids
    assert _convo_id_for_phone(h["nimita"], unassigned_phone) in ids


def test_report_sees_only_own_never_unassigned(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    chirag_convo = _make_assigned_convo(h, h["chirag_id"])
    amol_convo = _make_assigned_convo(h, h["amol_id"])
    samiksha_convo = _make_assigned_convo(h, h["samiksha_id"])
    unassigned_phone = _inbound(client)
    unassigned_id = _convo_id_for_phone(h["nimita"], unassigned_phone)

    chirag_ids = {c["id"] for c in h["chirag"].get("/api/whatsapp/conversations").json()}
    assert chirag_convo in chirag_ids
    assert amol_convo not in chirag_ids
    assert samiksha_convo not in chirag_ids
    assert unassigned_id not in chirag_ids

    amol_ids = {c["id"] for c in h["amol"].get("/api/whatsapp/conversations").json()}
    assert amol_convo in amol_ids
    assert chirag_convo not in amol_ids
    assert samiksha_convo not in amol_ids
    assert unassigned_id not in amol_ids


def test_status_filter_still_respects_visibility(client, auth_client, auth_token):
    """A search/filter parameter must narrow WITHIN scope, never bypass it."""
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    amol_convo = _make_assigned_convo(h, h["amol_id"])

    resp = h["chirag"].get("/api/whatsapp/conversations?status=open").json()
    assert not any(c["id"] == amol_convo for c in resp)


def test_mine_only_cannot_expand_or_bypass_hierarchy(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    amol_convo = _make_assigned_convo(h, h["amol_id"])
    chirag_convo = _make_assigned_convo(h, h["chirag_id"])

    # mine_only=true must not leak Amol's conversation to Chirag.
    chirag_mine = h["chirag"].get("/api/whatsapp/conversations?mine_only=true").json()
    assert not any(c["id"] == amol_convo for c in chirag_mine)
    assert any(c["id"] == chirag_convo for c in chirag_mine)

    # Omitting mine_only entirely (the historical bug) must NOT leak Amol's conversation either -
    # this is the core regression test for the original vulnerability.
    chirag_default = h["chirag"].get("/api/whatsapp/conversations").json()
    assert not any(c["id"] == amol_convo for c in chirag_default)


# ---------------------------------------------------------------------------
# Direct-ID access
# ---------------------------------------------------------------------------

def test_direct_id_messages_denied_for_hidden_conversation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    amol_convo = _make_assigned_convo(h, h["amol_id"], body="Amol secret message")

    resp = h["chirag"].get(f"/api/whatsapp/conversations/{amol_convo}/messages")
    assert resp.status_code == 403

    # Amol himself can see it.
    own = h["amol"].get(f"/api/whatsapp/conversations/{amol_convo}/messages")
    assert own.status_code == 200
    assert any("Amol secret message" in (m.get("body") or "") for m in own.json())


# ---------------------------------------------------------------------------
# Write authorization: reply / status / opt-out
# ---------------------------------------------------------------------------

def test_reply_denied_for_unauthorized_conversation_no_meta_call(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    amol_convo = _make_assigned_convo(h, h["amol_id"])

    with patch("requests.post") as mock_post:
        resp = h["chirag"].post(f"/api/whatsapp/conversations/{amol_convo}/reply", json={"message": "hijacked"})
        assert resp.status_code == 403
        mock_post.assert_not_called()


def test_reply_authorized_for_own_conversation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    chirag_convo = _make_assigned_convo(h, h["chirag_id"])

    resp = h["chirag"].post(f"/api/whatsapp/conversations/{chirag_convo}/reply", json={"message": "hello"})
    assert resp.status_code == 200
    # configured=False is expected (WHATSAPP_TOKEN/PHONE_ID stripped in tests) - the point is
    # this reached that far (200, not 403), proving the authorization check passed.
    assert resp.json()["configured"] is False


def test_reply_authorized_for_manager_on_reports_conversation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    chirag_convo = _make_assigned_convo(h, h["chirag_id"])

    resp = h["samiksha"].post(f"/api/whatsapp/conversations/{chirag_convo}/reply", json={"message": "manager reply"})
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_status_change_denied_for_unauthorized_conversation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    amol_convo = _make_assigned_convo(h, h["amol_id"])

    resp = h["chirag"].put(f"/api/whatsapp/conversations/{amol_convo}/status", json={"status": "closed"})
    assert resp.status_code == 403

    # Confirm unchanged.
    still_open = next(c for c in h["amol"].get("/api/whatsapp/conversations").json() if c["id"] == amol_convo)
    assert still_open["status"] == "open"


def test_opt_out_denied_for_unauthorized_conversation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    amol_convo = _make_assigned_convo(h, h["amol_id"])

    resp = h["chirag"].post(f"/api/whatsapp/conversations/{amol_convo}/opt-out")
    assert resp.status_code == 403

    still_active = next(c for c in h["amol"].get("/api/whatsapp/conversations").json() if c["id"] == amol_convo)
    assert still_active["opted_out_at"] is None


# ---------------------------------------------------------------------------
# Assignment authorization
# ---------------------------------------------------------------------------

def test_employee_can_only_assign_to_self(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    chirag_convo = _make_assigned_convo(h, h["chirag_id"])

    # Chirag reassigning his own conversation to himself: allowed.
    resp = h["chirag"].put(f"/api/whatsapp/conversations/{chirag_convo}/assign", json={"user_id": h["chirag_id"]})
    assert resp.status_code == 200

    # Chirag trying to hand it to Amol: denied - not a permitted assignment target.
    resp = h["chirag"].put(f"/api/whatsapp/conversations/{chirag_convo}/assign", json={"user_id": h["amol_id"]})
    assert resp.status_code == 403

    unchanged = next(c for c in h["nimita"].get("/api/whatsapp/conversations").json() if c["id"] == chirag_convo)
    assert unchanged["assigned_user_id"] == h["chirag_id"]


def test_employee_cannot_reassign_conversation_they_cannot_see(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    amol_convo = _make_assigned_convo(h, h["amol_id"])

    resp = h["chirag"].put(f"/api/whatsapp/conversations/{amol_convo}/assign", json={"user_id": h["chirag_id"]})
    assert resp.status_code == 403

    unchanged = next(c for c in h["amol"].get("/api/whatsapp/conversations").json() if c["id"] == amol_convo)
    assert unchanged["assigned_user_id"] == h["amol_id"]


def test_manager_can_assign_unassigned_to_self_or_reports(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    phone = _inbound(client)
    convo_id = _convo_id_for_phone(h["nimita"], phone)

    resp = h["samiksha"].put(f"/api/whatsapp/conversations/{convo_id}/assign", json={"user_id": h["chirag_id"]})
    assert resp.status_code == 200
    updated = next(c for c in h["nimita"].get("/api/whatsapp/conversations").json() if c["id"] == convo_id)
    assert updated["assigned_user_id"] == h["chirag_id"]


def test_manager_cannot_assign_to_someone_outside_her_team(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    phone = _inbound(client)
    convo_id = _convo_id_for_phone(h["nimita"], phone)

    resp = h["samiksha"].put(f"/api/whatsapp/conversations/{convo_id}/assign", json={"user_id": h["yogesh_id"]})
    assert resp.status_code == 403


def test_admin_can_assign_to_anyone(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    chirag_convo = _make_assigned_convo(h, h["chirag_id"])

    resp = h["nimita"].put(f"/api/whatsapp/conversations/{chirag_convo}/assign", json={"user_id": h["amol_id"]})
    assert resp.status_code == 200


def test_assign_rejects_nonexistent_target_user(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    phone = _inbound(client)
    convo_id = _convo_id_for_phone(h["nimita"], phone)

    resp = h["nimita"].put(f"/api/whatsapp/conversations/{convo_id}/assign", json={"user_id": 999999})
    assert resp.status_code == 404


def test_unassign_does_not_require_target_permission_check(client, auth_client, auth_token):
    """Unassigning (user_id=null) has no target to authorize - only the conversation's own
    visibility to the caller matters."""
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    chirag_convo = _make_assigned_convo(h, h["chirag_id"])

    resp = h["chirag"].put(f"/api/whatsapp/conversations/{chirag_convo}/assign", json={"user_id": None})
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Cross-entity redaction
# ---------------------------------------------------------------------------

def test_cross_entity_contact_name_redacted(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    amol_contact = h["amol"].post("/api/contacts", json={"name": "Amol's WA Contact", "phone": "9997771234"}).json()

    client.post("/api/webhooks/whatsapp", json={
        "entry": [{"changes": [{"value": {"messages": [{
            "from": "9997771234", "id": "wamid.REDACT001", "type": "text", "text": {"body": "Hi"}
        }]}}]}]
    })
    convo_id = _convo_id_for_phone(h["nimita"], "9997771234")
    assert h["nimita"].put(f"/api/whatsapp/conversations/{convo_id}/assign", json={"user_id": h["chirag_id"]}).status_code == 200

    chirag_view = next(c for c in h["chirag"].get("/api/whatsapp/conversations").json() if c["id"] == convo_id)
    assert chirag_view["contact_id"] == amol_contact["id"]
    assert chirag_view["contact_name"] is None

    nimita_view = next(c for c in h["nimita"].get("/api/whatsapp/conversations").json() if c["id"] == convo_id)
    assert nimita_view["contact_name"] == "Amol's WA Contact"


# ---------------------------------------------------------------------------
# Legitimate workflows still work (regression)
# ---------------------------------------------------------------------------

def test_legitimate_admin_and_manager_workflow_end_to_end(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    phone = _inbound(client, "New customer inquiry")
    convo_id = _convo_id_for_phone(h["nimita"], phone)

    # Manager claims it for a report.
    assert h["samiksha"].put(f"/api/whatsapp/conversations/{convo_id}/assign", json={"user_id": h["chirag_id"]}).status_code == 200
    # Report replies.
    assert h["chirag"].post(f"/api/whatsapp/conversations/{convo_id}/reply", json={"message": "Thanks for reaching out"}).status_code == 200
    # Report closes it.
    assert h["chirag"].put(f"/api/whatsapp/conversations/{convo_id}/status", json={"status": "closed"}).status_code == 200
    # Admin can see the whole thing throughout.
    assert any(c["id"] == convo_id for c in h["nimita"].get("/api/whatsapp/conversations").json())


def test_webhook_boundary_unaffected_by_visibility_changes(client):
    """Regression: the webhook receiver must remain reachable with no JWT at all."""
    resp = client.post("/api/webhooks/whatsapp", json={
        "entry": [{"changes": [{"value": {"messages": [{
            "from": "919980099999", "id": "wamid.WEBHOOKREG001", "type": "text", "text": {"body": "Hi"}
        }]}}]}]
    })
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# N-2.1: /api/whatsapp/send and /api/flows/{id}/send - compose-path authorization
#
# Both endpoints take a raw phone number (not a conversation_id) and internally resolve or
# create a conversation via _find_or_link_conversation. If that resolves to a PRE-EXISTING
# conversation owned by someone outside the caller's visibility scope, the send must be
# rejected before any mutation or Meta API call - otherwise these "compose new message"
# endpoints are an alternate path around the same authorization the Inbox reply endpoint
# enforces. A brand-new or currently-unassigned conversation must remain sendable by anyone,
# since that's the legitimate "start outreach" / "unclaimed conversation" case.
# ---------------------------------------------------------------------------

def _next_new_phone():
    _next_phone[0] += 1
    return str(_next_phone[0])


def test_send_admin_can_send_to_conversation_assigned_to_anyone(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    phone = _inbound(client)
    convo_id = _convo_id_for_phone(h["nimita"], phone)
    assert h["nimita"].put(f"/api/whatsapp/conversations/{convo_id}/assign", json={"user_id": h["chirag_id"]}).status_code == 200

    resp = h["nimita"].post("/api/whatsapp/send", json={"to": phone, "message": "from admin"})
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_send_manager_can_send_to_own_conversation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    phone = _inbound(client)
    convo_id = _convo_id_for_phone(h["nimita"], phone)
    assert h["nimita"].put(f"/api/whatsapp/conversations/{convo_id}/assign", json={"user_id": h["samiksha_id"]}).status_code == 200

    resp = h["samiksha"].post("/api/whatsapp/send", json={"to": phone, "message": "manager to own"})
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_send_manager_can_send_to_reports_conversations(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    chirag_phone = _inbound(client)
    chirag_convo = _convo_id_for_phone(h["nimita"], chirag_phone)
    assert h["nimita"].put(f"/api/whatsapp/conversations/{chirag_convo}/assign", json={"user_id": h["chirag_id"]}).status_code == 200

    amol_phone = _inbound(client)
    amol_convo = _convo_id_for_phone(h["nimita"], amol_phone)
    assert h["nimita"].put(f"/api/whatsapp/conversations/{amol_convo}/assign", json={"user_id": h["amol_id"]}).status_code == 200

    assert h["samiksha"].post("/api/whatsapp/send", json={"to": chirag_phone, "message": "to chirag's"}).status_code == 200
    assert h["samiksha"].post("/api/whatsapp/send", json={"to": amol_phone, "message": "to amol's"}).status_code == 200


def test_send_employee_can_send_to_own_conversation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    phone = _inbound(client)
    convo_id = _convo_id_for_phone(h["nimita"], phone)
    assert h["nimita"].put(f"/api/whatsapp/conversations/{convo_id}/assign", json={"user_id": h["chirag_id"]}).status_code == 200

    resp = h["chirag"].post("/api/whatsapp/send", json={"to": phone, "message": "own conversation"})
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_send_chirag_cannot_send_to_samikshas_conversation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    phone = _inbound(client)
    convo_id = _convo_id_for_phone(h["nimita"], phone)
    assert h["nimita"].put(f"/api/whatsapp/conversations/{convo_id}/assign", json={"user_id": h["samiksha_id"]}).status_code == 200

    with patch("requests.post") as mock_post:
        resp = h["chirag"].post("/api/whatsapp/send", json={"to": phone, "message": "hijack attempt"})
        assert resp.status_code == 403
        mock_post.assert_not_called()


def test_send_chirag_cannot_send_to_amols_conversation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    phone = _inbound(client)
    convo_id = _convo_id_for_phone(h["nimita"], phone)
    assert h["nimita"].put(f"/api/whatsapp/conversations/{convo_id}/assign", json={"user_id": h["amol_id"]}).status_code == 200

    with patch("requests.post") as mock_post:
        resp = h["chirag"].post("/api/whatsapp/send", json={"to": phone, "message": "hijack attempt"})
        assert resp.status_code == 403
        mock_post.assert_not_called()


def test_send_amol_cannot_send_to_chirags_conversation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    phone = _inbound(client)
    convo_id = _convo_id_for_phone(h["nimita"], phone)
    assert h["nimita"].put(f"/api/whatsapp/conversations/{convo_id}/assign", json={"user_id": h["chirag_id"]}).status_code == 200

    with patch("requests.post") as mock_post:
        resp = h["amol"].post("/api/whatsapp/send", json={"to": phone, "message": "hijack attempt"})
        assert resp.status_code == 403
        mock_post.assert_not_called()


def test_send_to_existing_unassigned_conversation_is_allowed(client, auth_client, auth_token):
    """An existing-but-unassigned conversation is sendable by anyone - this is the "legitimate
    new outreach on an unclaimed thread" case, distinct from the Inbox list/view surface's rule
    that hides unassigned conversations from individual employees."""
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    phone = _inbound(client)  # unassigned - never assigned to anyone

    resp = h["chirag"].post("/api/whatsapp/send", json={"to": phone, "message": "picking this up"})
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_send_to_brand_new_number_still_works_for_any_employee(client, auth_client, auth_token):
    """No conversation exists yet at all - starting fresh outreach must remain unrestricted."""
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    phone = _next_new_phone()

    resp = h["chirag"].post("/api/whatsapp/send", json={"to": phone, "message": "cold outreach"})
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_flow_send_follows_same_authorization(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    flow = auth_client.post("/api/flows", json={"meta_flow_id": "N21TEST", "name": "N-2.1 Flow"}).json()

    phone = _inbound(client)
    convo_id = _convo_id_for_phone(h["nimita"], phone)
    assert h["nimita"].put(f"/api/whatsapp/conversations/{convo_id}/assign", json={"user_id": h["amol_id"]}).status_code == 200

    # Unauthorized: Chirag cannot inject a Flow message into Amol's conversation.
    with patch("requests.post") as mock_post:
        denied = h["chirag"].post(f"/api/flows/{flow['id']}/send", json={"to": phone, "body_text": "Apply now"})
        assert denied.status_code == 403
        mock_post.assert_not_called()

    # Authorized: Amol can send the same Flow to his own conversation.
    allowed = h["amol"].post(f"/api/flows/{flow['id']}/send", json={"to": phone, "body_text": "Apply now"})
    assert allowed.status_code == 200
    assert allowed.json()["configured"] is False

    # A brand-new number (no conversation yet) is unrestricted for anyone.
    new_phone = _next_new_phone()
    fresh = h["chirag"].post(f"/api/flows/{flow['id']}/send", json={"to": new_phone, "body_text": "Apply now"})
    assert fresh.status_code == 200
    assert fresh.json()["configured"] is False


def test_send_and_flow_send_alternate_paths_both_blocked_consistently(client, auth_client, auth_token):
    """Neither compose-path endpoint may be used as a bypass for the other's authorization -
    both must independently enforce the same rule against the same pre-existing conversation."""
    h = hierarchy(client, auth_client, auth_token)
    h["_client"] = client
    flow = auth_client.post("/api/flows", json={"meta_flow_id": "N21TEST2", "name": "N-2.1 Flow Bypass Check"}).json()

    phone = _inbound(client)
    convo_id = _convo_id_for_phone(h["nimita"], phone)
    assert h["nimita"].put(f"/api/whatsapp/conversations/{convo_id}/assign", json={"user_id": h["samiksha_id"]}).status_code == 200

    with patch("requests.post") as mock_post:
        via_send = h["chirag"].post("/api/whatsapp/send", json={"to": phone, "message": "bypass via send"})
        assert via_send.status_code == 403
        via_flow = h["chirag"].post(f"/api/flows/{flow['id']}/send", json={"to": phone, "body_text": "bypass via flow"})
        assert via_flow.status_code == 403
        mock_post.assert_not_called()

    # The rightful owner's manager can still use either path legitimately.
    assert h["samiksha"].post("/api/whatsapp/send", json={"to": phone, "message": "legit"}).status_code == 200
