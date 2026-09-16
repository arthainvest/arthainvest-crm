"""Security tests for Meetings access control (Gate M-1/M-2).

Meetings never had any ownership-based filtering at all (unlike the original 7-entity release,
which at least had the columns sitting unused - Meetings' write endpoints didn't even check
existence consistently). Every test here runs as a non-admin employee to prove the restriction
actually holds, following the exact hierarchy shape used by test_data_visibility_security.py:
Nimita/Yogesh admins, Samiksha manages Chirag and Amol, Chirag/Amol strictly isolated.
"""
from unittest.mock import patch, MagicMock


class _TokenedClient:
    """Same shape as conftest.py's auth_client, for a token that isn't the seeded admin's."""
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
    yogesh_user_id, yogesh_token = _register_and_login(client, auth_token, "yogesh_meet", role="admin")
    samiksha_user_id, samiksha_token = _register_and_login(client, auth_token, "samiksha_meet")
    chirag_user_id, chirag_token = _register_and_login(client, auth_token, "chirag_meet")
    amol_user_id, amol_token = _register_and_login(client, auth_token, "amol_meet")

    samiksha_tm = auth_client.post("/api/team", json={"name": "Samiksha Meet", "role": "employee"}).json()
    chirag_tm = auth_client.post("/api/team", json={"name": "Chirag Meet", "role": "employee"}).json()
    amol_tm = auth_client.post("/api/team", json={"name": "Amol Meet", "role": "employee"}).json()

    assert auth_client.put(f"/api/team/{samiksha_tm['id']}", json={"user_id": samiksha_user_id}).status_code == 200
    assert auth_client.put(f"/api/team/{chirag_tm['id']}", json={"user_id": chirag_user_id, "reports_to": samiksha_tm['id']}).status_code == 200
    assert auth_client.put(f"/api/team/{amol_tm['id']}", json={"user_id": amol_user_id, "reports_to": samiksha_tm['id']}).status_code == 200

    return {
        "nimita": auth_client,
        "yogesh": _TokenedClient(client, yogesh_token),
        "samiksha": _TokenedClient(client, samiksha_token), "samiksha_tm_id": samiksha_tm['id'],
        "chirag": _TokenedClient(client, chirag_token), "chirag_tm_id": chirag_tm['id'],
        "amol": _TokenedClient(client, amol_token), "amol_tm_id": amol_tm['id'],
    }


def _mk_meeting(client, title="Meeting", **extra):
    payload = {"title": title, "meeting_date": "2027-01-15"}
    payload.update(extra)
    resp = client.post("/api/meetings", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# List visibility + hierarchy
# ---------------------------------------------------------------------------

def test_admins_see_everyones_meetings(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_meeting = _mk_meeting(h["chirag"], "Chirag's Meeting")

    for admin in (h["nimita"], h["yogesh"]):
        listing = admin.get("/api/meetings?date=2027-01-15").json()
        assert any(m["id"] == chirag_meeting["id"] for m in listing)


def test_samiksha_sees_own_and_reports_meetings(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_meeting = _mk_meeting(h["chirag"], "Chirag's Meeting")
    amol_meeting = _mk_meeting(h["amol"], "Amol's Meeting")
    samiksha_meeting = _mk_meeting(h["samiksha"], "Samiksha's Own Meeting")

    listing = h["samiksha"].get("/api/meetings?date=2027-01-15").json()
    ids = {m["id"] for m in listing}
    assert chirag_meeting["id"] in ids
    assert amol_meeting["id"] in ids
    assert samiksha_meeting["id"] in ids


def test_chirag_and_amol_mutually_isolated(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_meeting = _mk_meeting(h["chirag"], "Chirag's Meeting")
    amol_meeting = _mk_meeting(h["amol"], "Amol's Meeting")
    samiksha_meeting = _mk_meeting(h["samiksha"], "Samiksha's Own Meeting")

    chirag_listing = {m["id"] for m in h["chirag"].get("/api/meetings?date=2027-01-15").json()}
    assert chirag_meeting["id"] in chirag_listing
    assert amol_meeting["id"] not in chirag_listing
    assert samiksha_meeting["id"] not in chirag_listing

    amol_listing = {m["id"] for m in h["amol"].get("/api/meetings?date=2027-01-15").json()}
    assert amol_meeting["id"] in amol_listing
    assert chirag_meeting["id"] not in amol_listing
    assert samiksha_meeting["id"] not in amol_listing


def test_assigned_team_member_id_drilldown_is_scoped(client, auth_client, auth_token):
    """The assigned_team_member_id param narrows WITHIN the caller's scope - Amol asking for
    Chirag's assigned_team_member_id drill-down must get zero rows, not Chirag's meetings."""
    h = hierarchy(client, auth_client, auth_token)
    chirag_meeting = _mk_meeting(h["chirag"], "Chirag's Meeting", assigned_team_member_id=h["chirag_tm_id"])

    amol_view = h["amol"].get(f"/api/meetings?assigned_team_member_id={h['chirag_tm_id']}").json()
    assert amol_view == []

    samiksha_view = h["samiksha"].get(f"/api/meetings?assigned_team_member_id={h['chirag_tm_id']}").json()
    assert any(m["id"] == chirag_meeting["id"] for m in samiksha_view)


# ---------------------------------------------------------------------------
# Update / delete - check-before-write
# ---------------------------------------------------------------------------

def test_update_meeting_unauthorized_403_and_unchanged(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_meeting = _mk_meeting(h["chirag"], "Original Title")

    resp = h["amol"].put(f"/api/meetings/{chirag_meeting['id']}", json={"title": "Hijacked"})
    assert resp.status_code == 403

    still_there = h["chirag"].get("/api/meetings?date=2027-01-15").json()
    match = next(m for m in still_there if m["id"] == chirag_meeting["id"])
    assert match["title"] == "Original Title"


def test_delete_meeting_unauthorized_403_and_intact(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_meeting = _mk_meeting(h["chirag"], "Chirag's Meeting")

    resp = h["amol"].delete(f"/api/meetings/{chirag_meeting['id']}")
    assert resp.status_code == 403

    still_there = h["chirag"].get("/api/meetings?date=2027-01-15").json()
    assert any(m["id"] == chirag_meeting["id"] for m in still_there)


def test_update_delete_authorized_succeed(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_meeting = _mk_meeting(h["chirag"], "Chirag's Meeting")

    assert h["chirag"].put(f"/api/meetings/{chirag_meeting['id']}", json={"title": "Updated"}).status_code == 200
    assert h["samiksha"].delete(f"/api/meetings/{chirag_meeting['id']}").status_code == 200


# ---------------------------------------------------------------------------
# Link endpoints - meeting visibility + (when linking) target visibility
# ---------------------------------------------------------------------------

def test_link_company_authorization(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_meeting = _mk_meeting(h["chirag"], "Chirag's Meeting")
    amol_company = h["amol"].post("/api/companies", json={"name": "Amol's Company"}).json()

    # invisible meeting -> 403
    resp = h["amol"].put(f"/api/meetings/{chirag_meeting['id']}/company", json={"company_id": amol_company["id"]})
    assert resp.status_code == 403

    # authorized meeting + invisible target -> 403
    resp = h["chirag"].put(f"/api/meetings/{chirag_meeting['id']}/company", json={"company_id": amol_company["id"]})
    assert resp.status_code == 403

    # authorized meeting + authorized target -> success
    own_company = h["chirag"].post("/api/companies", json={"name": "Chirag's Company"}).json()
    resp = h["chirag"].put(f"/api/meetings/{chirag_meeting['id']}/company", json={"company_id": own_company["id"]})
    assert resp.status_code == 200


def test_link_deal_authorization(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_meeting = _mk_meeting(h["chirag"], "Chirag's Meeting")
    amol_lead = h["amol"].post("/api/leads", json={"name": "Amol Lead", "phone": "9990000001"}).json()
    amol_deal = h["amol"].post("/api/deals", json={"lead_id": amol_lead["id"], "deal_value": 100000}).json()

    resp = h["chirag"].put(f"/api/meetings/{chirag_meeting['id']}/deal", json={"deal_id": amol_deal["id"]})
    assert resp.status_code == 403

    own_lead = h["chirag"].post("/api/leads", json={"name": "Chirag Lead", "phone": "9990000002"}).json()
    own_deal = h["chirag"].post("/api/deals", json={"lead_id": own_lead["id"], "deal_value": 50000}).json()
    resp = h["chirag"].put(f"/api/meetings/{chirag_meeting['id']}/deal", json={"deal_id": own_deal["id"]})
    assert resp.status_code == 200


def test_link_call_authorization(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_meeting = _mk_meeting(h["chirag"], "Chirag's Meeting")
    amol_call = h["amol"].post("/api/calls", json={"name": "Amol Call"}).json()

    resp = h["chirag"].put(f"/api/meetings/{chirag_meeting['id']}/call", json={"call_id": amol_call["id"]})
    assert resp.status_code == 403

    own_call = h["chirag"].post("/api/calls", json={"name": "Chirag Call"}).json()
    resp = h["chirag"].put(f"/api/meetings/{chirag_meeting['id']}/call", json={"call_id": own_call["id"]})
    assert resp.status_code == 200


def test_link_task_authorization(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_meeting = _mk_meeting(h["chirag"], "Chirag's Meeting")
    amol_task = h["amol"].post("/api/tasks", json={"title": "Amol Task", "due_date": "2027-01-20"}).json()

    resp = h["chirag"].put(f"/api/meetings/{chirag_meeting['id']}/task", json={"task_id": amol_task["id"]})
    assert resp.status_code == 403

    own_task = h["chirag"].post("/api/tasks", json={"title": "Chirag Task", "due_date": "2027-01-20"}).json()
    resp = h["chirag"].put(f"/api/meetings/{chirag_meeting['id']}/task", json={"task_id": own_task["id"]})
    assert resp.status_code == 200


def test_link_quotation_authorization(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_meeting = _mk_meeting(h["chirag"], "Chirag's Meeting")
    amol_quotation = h["amol"].post("/api/quotations", json={"title": "Amol Quote"}).json()

    resp = h["chirag"].put(f"/api/meetings/{chirag_meeting['id']}/quotation", json={"quotation_id": amol_quotation["id"]})
    assert resp.status_code == 403

    own_quotation = h["chirag"].post("/api/quotations", json={"title": "Chirag Quote"}).json()
    resp = h["chirag"].put(f"/api/meetings/{chirag_meeting['id']}/quotation", json={"quotation_id": own_quotation["id"]})
    assert resp.status_code == 200


def test_unlink_does_not_require_target_visibility(client, auth_client, auth_token):
    """Unlinking (target id = None) never needs a target-visibility check - there is no target."""
    h = hierarchy(client, auth_client, auth_token)
    chirag_meeting = _mk_meeting(h["chirag"], "Chirag's Meeting")
    own_call = h["chirag"].post("/api/calls", json={"name": "Chirag Call"}).json()
    assert h["chirag"].put(f"/api/meetings/{chirag_meeting['id']}/call", json={"call_id": own_call["id"]}).status_code == 200
    resp = h["chirag"].put(f"/api/meetings/{chirag_meeting['id']}/call", json={"call_id": None})
    assert resp.status_code == 200
    assert resp.json()["call_id"] is None


# ---------------------------------------------------------------------------
# Reverse lookups
# ---------------------------------------------------------------------------

def test_reverse_lookups_only_return_authorized_meetings(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    company = h["nimita"].post("/api/companies", json={"name": "Shared Co"}).json()
    lead = h["nimita"].post("/api/leads", json={"name": "Shared Lead", "phone": "9990000010"}).json()
    deal = h["nimita"].post("/api/deals", json={"lead_id": lead["id"], "deal_value": 10000}).json()
    call = h["nimita"].post("/api/calls", json={"name": "Shared Call"}).json()
    task = h["nimita"].post("/api/tasks", json={"title": "Shared Task", "due_date": "2027-01-20"}).json()
    quotation = h["nimita"].post("/api/quotations", json={"title": "Shared Quote"}).json()

    chirag_meeting = _mk_meeting(h["chirag"], "Chirag's Meeting")
    amol_meeting = _mk_meeting(h["amol"], "Amol's Meeting")
    # Linked via the admin, not each owner - Company/Deal/Call/Task/Quotation created by Nimita
    # are not visible to non-admin Chirag/Amol (an admin's own records aren't automatically
    # visible to everyone else, only vice versa), so only an admin performing the link (which
    # no-ops the target-visibility check since scope is None) can attach the SAME shared entity
    # to both meetings - this test is about reverse-lookup scoping, not link authorization
    # (already covered by the dedicated per-entity link tests above).
    for meeting in (chirag_meeting, amol_meeting):
        assert h["nimita"].put(f"/api/meetings/{meeting['id']}/company", json={"company_id": company["id"]}).status_code == 200
        assert h["nimita"].put(f"/api/meetings/{meeting['id']}/deal", json={"deal_id": deal["id"]}).status_code == 200
        assert h["nimita"].put(f"/api/meetings/{meeting['id']}/call", json={"call_id": call["id"]}).status_code == 200
        assert h["nimita"].put(f"/api/meetings/{meeting['id']}/task", json={"task_id": task["id"]}).status_code == 200
        assert h["nimita"].put(f"/api/meetings/{meeting['id']}/quotation", json={"quotation_id": quotation["id"]}).status_code == 200

    for path in (f"/api/companies/{company['id']}/meetings", f"/api/deals/{deal['id']}/meetings",
                 f"/api/calls/{call['id']}/meetings", f"/api/tasks/{task['id']}/meetings",
                 f"/api/quotations/{quotation['id']}/meetings"):
        chirag_view = {m["id"] for m in h["chirag"].get(path).json()}
        assert chirag_meeting["id"] in chirag_view
        assert amol_meeting["id"] not in chirag_view

        samiksha_view = {m["id"] for m in h["samiksha"].get(path).json()}
        assert chirag_meeting["id"] in samiksha_view
        assert amol_meeting["id"] in samiksha_view


# ---------------------------------------------------------------------------
# Calendar sync
# ---------------------------------------------------------------------------

def test_calendar_sync_unauthorized_403_no_api_call(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_meeting = _mk_meeting(h["chirag"], "Chirag's Meeting")

    with patch("requests.post") as mock_post, patch("requests.patch") as mock_patch:
        resp = h["amol"].post(f"/api/meetings/{chirag_meeting['id']}/sync-to-google-calendar")
        assert resp.status_code == 403
        mock_post.assert_not_called()
        mock_patch.assert_not_called()


# ---------------------------------------------------------------------------
# Cross-entity redaction
# ---------------------------------------------------------------------------

def test_cross_entity_redaction_and_assignee_name_visible(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_lead = h["amol"].post("/api/leads", json={"name": "Amol's Lead", "phone": "9990000020"}).json()
    amol_contact = h["amol"].post("/api/contacts", json={"name": "Amol's Contact", "phone": "9990000021"}).json()
    amol_company = h["amol"].post("/api/companies", json={"name": "Amol's Company"}).json()
    amol_call = h["amol"].post("/api/calls", json={"name": "Amol's Call"}).json()
    amol_task = h["amol"].post("/api/tasks", json={"title": "Amol's Task", "due_date": "2027-01-20"}).json()
    amol_quotation = h["amol"].post("/api/quotations", json={"title": "Amol's Quote"}).json()

    chirag_meeting = _mk_meeting(
        h["chirag"], "Chirag's Meeting", assigned_team_member_id=h["chirag_tm_id"],
        lead_id=amol_lead["id"], contact_id=amol_contact["id"],
    )
    # Nimita (admin) links the rest, so setup itself isn't blocked by the same authorization
    # being tested here.
    assert h["nimita"].put(f"/api/meetings/{chirag_meeting['id']}/company", json={"company_id": amol_company["id"]}).status_code == 200
    assert h["nimita"].put(f"/api/meetings/{chirag_meeting['id']}/call", json={"call_id": amol_call["id"]}).status_code == 200
    assert h["nimita"].put(f"/api/meetings/{chirag_meeting['id']}/task", json={"task_id": amol_task["id"]}).status_code == 200
    assert h["nimita"].put(f"/api/meetings/{chirag_meeting['id']}/quotation", json={"quotation_id": amol_quotation["id"]}).status_code == 200

    chirag_view = next(m for m in h["chirag"].get("/api/meetings?date=2027-01-15").json() if m["id"] == chirag_meeting["id"])
    assert chirag_view["lead_name"] is None
    assert chirag_view["contact_name"] is None
    assert chirag_view["company_name"] is None
    assert chirag_view["call_name"] is None
    assert chirag_view["task_name"] is None
    assert chirag_view["quotation_title"] is None
    # Ownership metadata is never redacted, even though Chirag can't see Amol's records.
    assert chirag_view["assigned_team_member_name"] == "Chirag Meet"

    nimita_view = next(m for m in h["nimita"].get("/api/meetings?date=2027-01-15").json() if m["id"] == chirag_meeting["id"])
    assert nimita_view["lead_name"] == "Amol's Lead"
    assert nimita_view["contact_name"] == "Amol's Contact"
    assert nimita_view["company_name"] == "Amol's Company"
    assert nimita_view["call_name"] == "Amol's Call"
    assert nimita_view["task_name"] == "Amol's Task"
    assert nimita_view["quotation_title"] == "Amol's Quote"


def test_deal_label_two_tier_redaction(client, auth_client, auth_token):
    """A Meeting's deal_label is hidden entirely if the Deal isn't visible; if the Deal IS
    visible, the deal's own originating Lead name is independently redacted if that Lead isn't."""
    h = hierarchy(client, auth_client, auth_token)
    amol_lead = h["amol"].post("/api/leads", json={"name": "Amol's Originating Lead", "phone": "9990000030"}).json()
    amol_deal = h["amol"].post("/api/deals", json={"lead_id": amol_lead["id"], "deal_value": 75000}).json()

    chirag_meeting = _mk_meeting(h["chirag"], "Chirag's Meeting")
    assert h["nimita"].put(f"/api/meetings/{chirag_meeting['id']}/deal", json={"deal_id": amol_deal["id"]}).status_code == 200

    chirag_view = next(m for m in h["chirag"].get("/api/meetings?date=2027-01-15").json() if m["id"] == chirag_meeting["id"])
    assert chirag_view["deal_label"] is None

    nimita_view = next(m for m in h["nimita"].get("/api/meetings?date=2027-01-15").json() if m["id"] == chirag_meeting["id"])
    assert nimita_view["deal_label"] is not None
    assert "Amol's Originating Lead" in nimita_view["deal_label"]
