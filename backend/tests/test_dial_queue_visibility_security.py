"""Security tests for Dial Queue access control (Gate N-19).

dial_queue had two ownership columns from the start (team_member_id -> team_members.id,
assigned_by -> users.id, the exact same dual-space pair used everywhere else) but no route
ever read them back for scoping: GET /api/dialer/queue defaulted to every team member's
entire queue when team_member_id was omitted, PUT only checked existence, DELETE checked
nothing at all, and POST /api/dialer/assign let any employee assign into any other team
member's queue and queue up a lead/contact they couldn't otherwise see (the dialer-assign
IDOR, the same class of bug as the Campaigns-recipient IDOR fixed in N-11).

Locked model (same as every other creator-or-assignee entity): a queue entry is visible if
assigned_by is in the caller's own scope.user_ids OR team_member_id is in scope.team_member_ids.
Admins (Nimita/Yogesh): unrestricted. A manager (Samiksha) sees/assigns into own + Chirag's +
Amol's queues. Chirag/Amol: own only.
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
    yogesh_user_id, yogesh_token = _register_and_login(client, auth_token, "yogesh_dq", role="admin")
    samiksha_user_id, samiksha_token = _register_and_login(client, auth_token, "samiksha_dq")
    chirag_user_id, chirag_token = _register_and_login(client, auth_token, "chirag_dq")
    amol_user_id, amol_token = _register_and_login(client, auth_token, "amol_dq")
    solo_user_id, solo_token = _register_and_login(client, auth_token, "solo_dq")

    samiksha_tm = auth_client.post("/api/team", json={"name": "Samiksha DQ", "role": "employee"}).json()
    chirag_tm = auth_client.post("/api/team", json={"name": "Chirag DQ", "role": "employee"}).json()
    amol_tm = auth_client.post("/api/team", json={"name": "Amol DQ", "role": "employee"}).json()
    solo_tm = auth_client.post("/api/team", json={"name": "Solo DQ", "role": "employee"}).json()

    assert auth_client.put(f"/api/team/{samiksha_tm['id']}", json={"user_id": samiksha_user_id}).status_code == 200
    assert auth_client.put(f"/api/team/{chirag_tm['id']}", json={"user_id": chirag_user_id, "reports_to": samiksha_tm['id']}).status_code == 200
    assert auth_client.put(f"/api/team/{amol_tm['id']}", json={"user_id": amol_user_id, "reports_to": samiksha_tm['id']}).status_code == 200
    assert auth_client.put(f"/api/team/{solo_tm['id']}", json={"user_id": solo_user_id}).status_code == 200

    return {
        "nimita": auth_client,
        "yogesh": _TokenedClient(client, yogesh_token),
        "samiksha": _TokenedClient(client, samiksha_token), "samiksha_tm": samiksha_tm['id'],
        "chirag": _TokenedClient(client, chirag_token), "chirag_tm": chirag_tm['id'],
        "amol": _TokenedClient(client, amol_token), "amol_tm": amol_tm['id'],
        "solo": _TokenedClient(client, solo_token), "solo_tm": solo_tm['id'],
    }


def _lead(client, name, phone):
    resp = client.post("/api/leads", json={"name": name, "phone": phone})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _contact(client, name, phone):
    resp = client.post("/api/contacts", json={"name": name, "phone": phone})
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Assignment authorization: who may assign INTO whose queue
# ---------------------------------------------------------------------------

def test_employee_can_assign_into_own_queue(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    lead = _lead(h["chirag"], "Chirag's Own Lead", "9970000001")

    resp = h["chirag"].post("/api/dialer/assign", json={"team_member_id": h["chirag_tm"], "lead_ids": [lead["id"]]})
    assert resp.status_code == 200
    assert resp.json() == {"assigned": 1, "skipped": 0}


def test_manager_can_assign_into_reports_queue(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    lead = _lead(h["amol"], "Amol's Own Lead", "9970000002")

    resp = h["samiksha"].post("/api/dialer/assign", json={"team_member_id": h["amol_tm"], "lead_ids": [lead["id"]]})
    assert resp.status_code == 200
    assert resp.json() == {"assigned": 1, "skipped": 0}


def test_employee_cannot_assign_into_unrelated_queue(client, auth_client, auth_token):
    """The dialer-assign IDOR: Chirag must not be able to push work into Amol's queue -
    they're peers, not manager/report."""
    h = hierarchy(client, auth_client, auth_token)
    lead = _lead(h["chirag"], "Chirag's Lead", "9970000003")

    resp = h["chirag"].post("/api/dialer/assign", json={"team_member_id": h["amol_tm"], "lead_ids": [lead["id"]]})
    assert resp.status_code == 403

    queue = h["amol"].get(f"/api/dialer/queue?team_member_id={h['amol_tm']}").json()
    assert queue == []


def test_manager_cannot_assign_into_unrelated_team_members_queue(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    lead = _lead(h["samiksha"], "Samiksha's Lead", "9970000004")

    resp = h["samiksha"].post("/api/dialer/assign", json={"team_member_id": h["solo_tm"], "lead_ids": [lead["id"]]})
    assert resp.status_code == 403


def test_admin_can_assign_into_anyones_queue(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    lead = _lead(h["solo"], "Solo's Own Lead", "9970000005")

    resp = h["nimita"].post("/api/dialer/assign", json={"team_member_id": h["solo_tm"], "lead_ids": [lead["id"]]})
    assert resp.status_code == 200
    assert resp.json() == {"assigned": 1, "skipped": 0}


# ---------------------------------------------------------------------------
# The dialer-assign IDOR: target lead/contact must itself be visible
# ---------------------------------------------------------------------------

def test_hidden_lead_cannot_be_queued(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_lead = _lead(h["amol"], "Amol's Hidden Lead", "9970000006")

    # Chirag assigning into his OWN queue (authorized target queue) but with Amol's lead
    # (an invisible target) - the queue-target check alone must not be sufficient.
    resp = h["chirag"].post("/api/dialer/assign", json={"team_member_id": h["chirag_tm"], "lead_ids": [amol_lead["id"]]})
    assert resp.status_code == 200
    assert resp.json() == {"assigned": 0, "skipped": 1}

    queue = h["chirag"].get(f"/api/dialer/queue?team_member_id={h['chirag_tm']}").json()
    assert queue == []


def test_hidden_contact_cannot_be_queued(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_contact = _contact(h["amol"], "Amol's Hidden Contact", "9970000007")

    resp = h["chirag"].post("/api/dialer/assign", json={"team_member_id": h["chirag_tm"], "contact_ids": [amol_contact["id"]]})
    assert resp.status_code == 200
    assert resp.json() == {"assigned": 0, "skipped": 1}


def test_nonexistent_lead_id_treated_same_as_hidden(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    resp = h["chirag"].post("/api/dialer/assign", json={"team_member_id": h["chirag_tm"], "lead_ids": [999999999]})
    assert resp.status_code == 200
    assert resp.json() == {"assigned": 0, "skipped": 1}


def test_mixed_visible_and_invisible_targets_handled_safely(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    own_lead = _lead(h["chirag"], "Chirag's Visible Lead", "9970000008")
    hidden_lead = _lead(h["amol"], "Amol's Invisible Lead", "9970000009")

    resp = h["chirag"].post(
        "/api/dialer/assign",
        json={"team_member_id": h["chirag_tm"], "lead_ids": [own_lead["id"], hidden_lead["id"]]},
    )
    assert resp.status_code == 200
    assert resp.json() == {"assigned": 1, "skipped": 1}

    queue = h["chirag"].get(f"/api/dialer/queue?team_member_id={h['chirag_tm']}").json()
    assert len(queue) == 1
    assert queue[0]["lead_id"] == own_lead["id"]


# ---------------------------------------------------------------------------
# List visibility
# ---------------------------------------------------------------------------

def test_admin_sees_entire_queue_across_team_members(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_lead = _lead(h["chirag"], "Chirag Q Lead", "9970000010")
    amol_lead = _lead(h["amol"], "Amol Q Lead", "9970000011")
    h["nimita"].post("/api/dialer/assign", json={"team_member_id": h["chirag_tm"], "lead_ids": [chirag_lead["id"]]})
    h["nimita"].post("/api/dialer/assign", json={"team_member_id": h["amol_tm"], "lead_ids": [amol_lead["id"]]})

    for admin in (h["nimita"], h["yogesh"]):
        full_queue = admin.get("/api/dialer/queue?status=Pending").json()
        team_member_ids = {q["team_member_id"] for q in full_queue}
        assert h["chirag_tm"] in team_member_ids
        assert h["amol_tm"] in team_member_ids


def test_manager_sees_own_and_reports_queue_without_filter(client, auth_client, auth_token):
    """Omitting team_member_id entirely must not leak the unrelated solo employee's queue -
    this is the core regression test for the original 'entire unfiltered queue' vulnerability."""
    h = hierarchy(client, auth_client, auth_token)
    chirag_lead = _lead(h["chirag"], "Chirag Q Lead2", "9970000012")
    solo_lead = _lead(h["solo"], "Solo Q Lead", "9970000013")
    h["nimita"].post("/api/dialer/assign", json={"team_member_id": h["chirag_tm"], "lead_ids": [chirag_lead["id"]]})
    h["nimita"].post("/api/dialer/assign", json={"team_member_id": h["solo_tm"], "lead_ids": [solo_lead["id"]]})

    queue = h["samiksha"].get("/api/dialer/queue?status=Pending").json()
    team_member_ids = {q["team_member_id"] for q in queue}
    assert h["chirag_tm"] in team_member_ids
    assert h["solo_tm"] not in team_member_ids


def test_report_sees_only_own_queue_without_filter(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_lead = _lead(h["chirag"], "Chirag Q Lead3", "9970000014")
    amol_lead = _lead(h["amol"], "Amol Q Lead2", "9970000015")
    h["nimita"].post("/api/dialer/assign", json={"team_member_id": h["chirag_tm"], "lead_ids": [chirag_lead["id"]]})
    h["nimita"].post("/api/dialer/assign", json={"team_member_id": h["amol_tm"], "lead_ids": [amol_lead["id"]]})

    chirag_queue = h["chirag"].get("/api/dialer/queue?status=Pending").json()
    assert {q["team_member_id"] for q in chirag_queue} == {h["chirag_tm"]}


def test_supplying_out_of_scope_team_member_id_returns_empty_not_leaked(client, auth_client, auth_token):
    """The team_member_id query param is a narrowing filter WITHIN scope, never a bypass -
    Chirag explicitly asking for Amol's queue by id must get nothing, not a 403 that would
    at least confirm the id is valid, and not Amol's actual data."""
    h = hierarchy(client, auth_client, auth_token)
    amol_lead = _lead(h["amol"], "Amol Q Lead3", "9970000016")
    h["nimita"].post("/api/dialer/assign", json={"team_member_id": h["amol_tm"], "lead_ids": [amol_lead["id"]]})

    resp = h["chirag"].get(f"/api/dialer/queue?team_member_id={h['amol_tm']}")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Direct-ID write authorization: status update / delete
# ---------------------------------------------------------------------------

def test_unauthorized_status_update_denied_with_no_mutation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_lead = _lead(h["amol"], "Amol Q Lead4", "9970000017")
    h["nimita"].post("/api/dialer/assign", json={"team_member_id": h["amol_tm"], "lead_ids": [amol_lead["id"]]})
    item_id = h["amol"].get(f"/api/dialer/queue?team_member_id={h['amol_tm']}").json()[0]["id"]

    resp = h["chirag"].put(f"/api/dialer/queue/{item_id}", json={"status": "Called"})
    assert resp.status_code == 403

    still_pending = h["amol"].get(f"/api/dialer/queue?team_member_id={h['amol_tm']}").json()
    assert any(q["id"] == item_id and q["status"] == "Pending" for q in still_pending)


def test_authorized_status_update_succeeds(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_lead = _lead(h["chirag"], "Chirag Q Lead5", "9970000018")
    h["chirag"].post("/api/dialer/assign", json={"team_member_id": h["chirag_tm"], "lead_ids": [chirag_lead["id"]]})
    item_id = h["chirag"].get(f"/api/dialer/queue?team_member_id={h['chirag_tm']}").json()[0]["id"]

    resp = h["chirag"].put(f"/api/dialer/queue/{item_id}", json={"status": "Called"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "Called"


def test_manager_can_update_reports_queue_item(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_lead = _lead(h["amol"], "Amol Q Lead6", "9970000019")
    h["nimita"].post("/api/dialer/assign", json={"team_member_id": h["amol_tm"], "lead_ids": [amol_lead["id"]]})
    item_id = h["amol"].get(f"/api/dialer/queue?team_member_id={h['amol_tm']}").json()[0]["id"]

    resp = h["samiksha"].put(f"/api/dialer/queue/{item_id}", json={"status": "Skipped"})
    assert resp.status_code == 200


def test_update_nonexistent_queue_item_404s(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    resp = h["chirag"].put("/api/dialer/queue/999999999", json={"status": "Called"})
    assert resp.status_code == 404


def test_unauthorized_delete_denied_with_no_mutation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_lead = _lead(h["amol"], "Amol Q Lead7", "9970000020")
    h["nimita"].post("/api/dialer/assign", json={"team_member_id": h["amol_tm"], "lead_ids": [amol_lead["id"]]})
    item_id = h["amol"].get(f"/api/dialer/queue?team_member_id={h['amol_tm']}").json()[0]["id"]

    resp = h["chirag"].delete(f"/api/dialer/queue/{item_id}")
    assert resp.status_code == 403

    still_there = h["amol"].get(f"/api/dialer/queue?team_member_id={h['amol_tm']}").json()
    assert any(q["id"] == item_id for q in still_there)


def test_authorized_delete_succeeds(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_lead = _lead(h["chirag"], "Chirag Q Lead8", "9970000021")
    h["chirag"].post("/api/dialer/assign", json={"team_member_id": h["chirag_tm"], "lead_ids": [chirag_lead["id"]]})
    item_id = h["chirag"].get(f"/api/dialer/queue?team_member_id={h['chirag_tm']}").json()[0]["id"]

    resp = h["chirag"].delete(f"/api/dialer/queue/{item_id}")
    assert resp.status_code == 200

    queue = h["chirag"].get(f"/api/dialer/queue?team_member_id={h['chirag_tm']}").json()
    assert queue == []


def test_delete_nonexistent_queue_item_404s(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    resp = h["chirag"].delete("/api/dialer/queue/999999999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Cross-entity redaction: name/phone must not leak a hidden lead/contact
# ---------------------------------------------------------------------------

def test_queue_list_redacts_hidden_entity_details(client, auth_client, auth_token):
    """Defense-in-depth for a queue entry whose underlying lead is (or becomes) invisible to
    the viewer, e.g. attached by an admin bypassing the per-target check - the viewer must see
    the queue item exists (it's in their own scope via team_member_id) but never the hidden
    lead's actual name/phone."""
    h = hierarchy(client, auth_client, auth_token)
    solo_lead = _lead(h["solo"], "Solo's Fully Hidden Lead", "9970000022")

    # Admin bypasses both checks, simulating a pre-existing/legacy attachment.
    admin_assign = h["nimita"].post("/api/dialer/assign", json={"team_member_id": h["chirag_tm"], "lead_ids": [solo_lead["id"]]})
    assert admin_assign.status_code == 200
    assert admin_assign.json() == {"assigned": 1, "skipped": 0}

    chirag_view = h["chirag"].get(f"/api/dialer/queue?team_member_id={h['chirag_tm']}").json()
    assert len(chirag_view) == 1
    assert chirag_view[0]["lead_id"] == solo_lead["id"]
    assert chirag_view[0]["name"] is None
    assert chirag_view[0]["phone"] is None

    nimita_view = h["nimita"].get(f"/api/dialer/queue?team_member_id={h['chirag_tm']}").json()
    assert nimita_view[0]["name"] == "Solo's Fully Hidden Lead"
