"""Security tests for Automations access control (Gate N-24).

automations.created_by existed since the table was first created, but no route ever read it
back for scoping - every authenticated employee could list/get/update/delete/pause any other
employee's automation, view its enrollment list (including linked Lead/Contact name+phone),
enroll an arbitrary (including invisible) Lead/Contact into it, or stop any enrollment. The
enroll endpoints are the real risk: enrollment is what a background scheduler later turns into
a genuine outbound Email/WhatsApp/SMS send, so an invisible target being enrollable is the same
IDOR class already closed for Campaigns (N-11) and Dial Queue (N-19).

Locked model (creator-only, same as Campaigns/Quotations - automations have no assignee
column): admins unrestricted; a manager sees/manages own + direct reports' automations;
an individual employee sees/manages only automations they created.
"""


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
    yogesh_user_id, yogesh_token = _register_and_login(client, auth_token, "yogesh_auto", role="admin")
    samiksha_user_id, samiksha_token = _register_and_login(client, auth_token, "samiksha_auto")
    chirag_user_id, chirag_token = _register_and_login(client, auth_token, "chirag_auto")
    amol_user_id, amol_token = _register_and_login(client, auth_token, "amol_auto")

    samiksha_tm = auth_client.post("/api/team", json={"name": "Samiksha Auto", "role": "employee"}).json()
    chirag_tm = auth_client.post("/api/team", json={"name": "Chirag Auto", "role": "employee"}).json()
    amol_tm = auth_client.post("/api/team", json={"name": "Amol Auto", "role": "employee"}).json()

    assert auth_client.put(f"/api/team/{samiksha_tm['id']}", json={"user_id": samiksha_user_id}).status_code == 200
    assert auth_client.put(f"/api/team/{chirag_tm['id']}", json={"user_id": chirag_user_id, "reports_to": samiksha_tm['id']}).status_code == 200
    assert auth_client.put(f"/api/team/{amol_tm['id']}", json={"user_id": amol_user_id, "reports_to": samiksha_tm['id']}).status_code == 200

    return {
        "nimita": auth_client,
        "yogesh": _TokenedClient(client, yogesh_token),
        "samiksha": _TokenedClient(client, samiksha_token),
        "chirag": _TokenedClient(client, chirag_token),
        "amol": _TokenedClient(client, amol_token),
    }


def _automation(client, name="Test Automation", steps=None):
    payload = {
        "name": name, "trigger_type": "manual",
        "steps": steps if steps is not None else [{"wait_minutes": 0, "message_type": "text", "body": "Hello"}],
    }
    resp = client.post("/api/automations", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _lead(client, name, phone):
    resp = client.post("/api/leads", json={"name": name, "phone": phone})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _contact(client, name, phone):
    resp = client.post("/api/contacts", json={"name": name, "phone": phone})
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Visibility
# ---------------------------------------------------------------------------

def test_admin_sees_all_automations(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_auto = _automation(h["chirag"], "Chirag's Automation")
    amol_auto = _automation(h["amol"], "Amol's Automation")
    samiksha_auto = _automation(h["samiksha"], "Samiksha's Automation")

    for admin in (h["nimita"], h["yogesh"]):
        ids = {a["id"] for a in admin.get("/api/automations").json()}
        assert chirag_auto["id"] in ids
        assert amol_auto["id"] in ids
        assert samiksha_auto["id"] in ids


def test_manager_sees_own_and_reports_automations(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_auto = _automation(h["chirag"], "Chirag's Automation")
    amol_auto = _automation(h["amol"], "Amol's Automation")

    ids = {a["id"] for a in h["samiksha"].get("/api/automations").json()}
    assert chirag_auto["id"] in ids
    assert amol_auto["id"] in ids


def test_report_sees_only_own_automation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_auto = _automation(h["chirag"], "Chirag's Automation")
    amol_auto = _automation(h["amol"], "Amol's Automation")

    chirag_ids = {a["id"] for a in h["chirag"].get("/api/automations").json()}
    assert chirag_auto["id"] in chirag_ids
    assert amol_auto["id"] not in chirag_ids

    amol_ids = {a["id"] for a in h["amol"].get("/api/automations").json()}
    assert amol_auto["id"] in amol_ids
    assert chirag_auto["id"] not in amol_ids


# ---------------------------------------------------------------------------
# Write authorization: update / delete
# ---------------------------------------------------------------------------

def test_unauthorized_update_denied_with_no_mutation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_auto = _automation(h["amol"], "Amol's Automation")

    resp = h["chirag"].put(f"/api/automations/{amol_auto['id']}", json={"status": "paused"})
    assert resp.status_code == 403

    unchanged = next(a for a in h["nimita"].get("/api/automations").json() if a["id"] == amol_auto["id"])
    assert unchanged["status"] == "active"


def test_authorized_update_succeeds(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_auto = _automation(h["chirag"], "Chirag's Automation")

    resp = h["chirag"].put(f"/api/automations/{chirag_auto['id']}", json={"status": "paused"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "paused"


def test_manager_can_update_reports_automation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_auto = _automation(h["amol"], "Amol's Automation")

    resp = h["samiksha"].put(f"/api/automations/{amol_auto['id']}", json={"status": "paused"})
    assert resp.status_code == 200


def test_unauthorized_delete_denied_with_no_mutation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_auto = _automation(h["amol"], "Amol's Automation")

    resp = h["chirag"].delete(f"/api/automations/{amol_auto['id']}")
    assert resp.status_code == 403

    ids = {a["id"] for a in h["nimita"].get("/api/automations").json()}
    assert amol_auto["id"] in ids


def test_authorized_delete_succeeds(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_auto = _automation(h["chirag"], "Chirag's Automation")

    resp = h["chirag"].delete(f"/api/automations/{chirag_auto['id']}")
    assert resp.status_code == 200

    ids = {a["id"] for a in h["nimita"].get("/api/automations").json()}
    assert chirag_auto["id"] not in ids


def test_update_nonexistent_automation_404s(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    resp = h["chirag"].put("/api/automations/999999999", json={"status": "paused"})
    assert resp.status_code == 404


def test_delete_nonexistent_automation_404s(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    resp = h["chirag"].delete("/api/automations/999999999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Enrollments: list authorization + redaction
# ---------------------------------------------------------------------------

def test_unauthorized_get_enrollments_denied(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_auto = _automation(h["amol"], "Amol's Automation")

    resp = h["chirag"].get(f"/api/automations/{amol_auto['id']}/enrollments")
    assert resp.status_code == 403


def test_authorized_get_enrollments_succeeds(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_auto = _automation(h["chirag"], "Chirag's Automation")
    chirag_lead = _lead(h["chirag"], "Chirag's Own Lead", "9950000001")
    h["chirag"].post(f"/api/automations/{chirag_auto['id']}/enroll", json={"entity_type": "lead", "entity_id": chirag_lead["id"]})

    resp = h["chirag"].get(f"/api/automations/{chirag_auto['id']}/enrollments")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["entity_name"] == "Chirag's Own Lead"


def test_enrollments_get_404s_for_nonexistent_automation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    resp = h["chirag"].get("/api/automations/999999999/enrollments")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# The enroll IDOR: target Lead/Contact must itself be visible - the real risk, since
# enrollment is what eventually triggers a real outbound message via the scheduler
# ---------------------------------------------------------------------------

def test_unauthorized_enroll_denied(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_auto = _automation(h["amol"], "Amol's Automation")
    chirag_lead = _lead(h["chirag"], "Chirag's Lead", "9950000002")

    resp = h["chirag"].post(f"/api/automations/{amol_auto['id']}/enroll", json={"entity_type": "lead", "entity_id": chirag_lead["id"]})
    assert resp.status_code == 403

    enrollments = h["amol"].get(f"/api/automations/{amol_auto['id']}/enrollments").json()
    assert enrollments == []


def test_hidden_lead_cannot_be_enrolled(client, auth_client, auth_token):
    """The core IDOR fix: automation visibility alone is not enough - Chirag owns the
    automation but tries to enroll Amol's lead."""
    h = hierarchy(client, auth_client, auth_token)
    chirag_auto = _automation(h["chirag"], "Chirag's Automation")
    amol_lead = _lead(h["amol"], "Amol's Hidden Lead", "9950000003")

    resp = h["chirag"].post(f"/api/automations/{chirag_auto['id']}/enroll", json={"entity_type": "lead", "entity_id": amol_lead["id"]})
    assert resp.status_code == 403

    enrollments = h["chirag"].get(f"/api/automations/{chirag_auto['id']}/enrollments").json()
    assert enrollments == []


def test_hidden_contact_cannot_be_enrolled(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_auto = _automation(h["chirag"], "Chirag's Automation")
    amol_contact = _contact(h["amol"], "Amol's Hidden Contact", "9950000004")

    resp = h["chirag"].post(f"/api/automations/{chirag_auto['id']}/enroll", json={"entity_type": "contact", "entity_id": amol_contact["id"]})
    assert resp.status_code == 403


def test_nonexistent_lead_enroll_denied_same_as_hidden(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_auto = _automation(h["chirag"], "Chirag's Automation")

    resp = h["chirag"].post(f"/api/automations/{chirag_auto['id']}/enroll", json={"entity_type": "lead", "entity_id": 999999999})
    assert resp.status_code == 403


def test_manager_can_enroll_reports_lead_into_reports_automation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_auto = _automation(h["amol"], "Amol's Automation")
    amol_lead = _lead(h["amol"], "Amol's Own Lead", "9950000005")

    resp = h["samiksha"].post(f"/api/automations/{amol_auto['id']}/enroll", json={"entity_type": "lead", "entity_id": amol_lead["id"]})
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# enroll-group: unauthorized automation denied; invisible members silently excluded
# ---------------------------------------------------------------------------

def test_unauthorized_enroll_group_denied(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_auto = _automation(h["amol"], "Amol's Automation")
    group = h["chirag"].post("/api/groups", json={"name": "Chirag's Group"}).json()

    resp = h["chirag"].post(f"/api/automations/{amol_auto['id']}/enroll-group/{group['id']}")
    assert resp.status_code == 403


def test_enroll_group_excludes_invisible_members(client, auth_client, auth_token):
    """A group is a shared, unowned taxonomy - Chirag's own automation + group, but one of
    the group's members is Amol's lead. That member must be silently skipped, never
    enrolled, while Chirag's own visible member is enrolled normally."""
    h = hierarchy(client, auth_client, auth_token)
    chirag_auto = _automation(h["chirag"], "Chirag's Automation")
    chirag_lead = _lead(h["chirag"], "Chirag's Group Lead", "9950000006")
    amol_lead = _lead(h["amol"], "Amol's Group Lead", "9950000007")
    group = h["chirag"].post("/api/groups", json={"name": "Mixed Visibility Group"}).json()
    h["chirag"].post("/api/groups/assign", json={"entity_type": "lead", "entity_id": chirag_lead["id"], "group_id": group["id"]})
    h["chirag"].post("/api/groups/assign", json={"entity_type": "lead", "entity_id": amol_lead["id"], "group_id": group["id"]})

    resp = h["chirag"].post(f"/api/automations/{chirag_auto['id']}/enroll-group/{group['id']}")
    assert resp.status_code == 200
    assert "1" in resp.json()["message"]

    enrollments = h["chirag"].get(f"/api/automations/{chirag_auto['id']}/enrollments").json()
    assert len(enrollments) == 1
    assert enrollments[0]["entity_id"] == chirag_lead["id"]


# ---------------------------------------------------------------------------
# stop_enrollment: ownership resolved via the parent automation
# ---------------------------------------------------------------------------

def test_unauthorized_stop_enrollment_denied_with_no_mutation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_auto = _automation(h["amol"], "Amol's Automation")
    amol_lead = _lead(h["amol"], "Amol's Lead", "9950000008")
    h["amol"].post(f"/api/automations/{amol_auto['id']}/enroll", json={"entity_type": "lead", "entity_id": amol_lead["id"]})
    enrollment_id = h["amol"].get(f"/api/automations/{amol_auto['id']}/enrollments").json()[0]["id"]

    resp = h["chirag"].post(f"/api/automations/enrollments/{enrollment_id}/stop")
    assert resp.status_code == 403

    still_active = h["amol"].get(f"/api/automations/{amol_auto['id']}/enrollments").json()[0]
    assert still_active["status"] == "active"


def test_authorized_stop_enrollment_succeeds(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_auto = _automation(h["chirag"], "Chirag's Automation")
    chirag_lead = _lead(h["chirag"], "Chirag's Lead", "9950000009")
    h["chirag"].post(f"/api/automations/{chirag_auto['id']}/enroll", json={"entity_type": "lead", "entity_id": chirag_lead["id"]})
    enrollment_id = h["chirag"].get(f"/api/automations/{chirag_auto['id']}/enrollments").json()[0]["id"]

    resp = h["chirag"].post(f"/api/automations/enrollments/{enrollment_id}/stop")
    assert resp.status_code == 200

    stopped = h["chirag"].get(f"/api/automations/{chirag_auto['id']}/enrollments").json()[0]
    assert stopped["status"] == "stopped"


def test_manager_can_stop_reports_enrollment(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_auto = _automation(h["amol"], "Amol's Automation")
    amol_lead = _lead(h["amol"], "Amol's Lead2", "9950000010")
    h["amol"].post(f"/api/automations/{amol_auto['id']}/enroll", json={"entity_type": "lead", "entity_id": amol_lead["id"]})
    enrollment_id = h["amol"].get(f"/api/automations/{amol_auto['id']}/enrollments").json()[0]["id"]

    resp = h["samiksha"].post(f"/api/automations/enrollments/{enrollment_id}/stop")
    assert resp.status_code == 200


def test_stop_nonexistent_enrollment_404s(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    resp = h["chirag"].post("/api/automations/enrollments/999999999/stop")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Cross-entity redaction
# ---------------------------------------------------------------------------

def test_enrollment_list_redacts_hidden_entity_details(client, auth_client, auth_token):
    """Defense-in-depth for an enrollment whose underlying lead is invisible to the viewer,
    e.g. attached by an admin bypassing the per-target check. Uses yogesh (a second admin,
    outside Samiksha's own manager/reports hierarchy) as the lead's creator - Amol's lead
    would NOT work here, since Amol reports to Samiksha and is already inside her scope."""
    h = hierarchy(client, auth_client, auth_token)
    samiksha_auto = _automation(h["samiksha"], "Samiksha's Automation")
    yogesh_lead = _lead(h["yogesh"], "Yogesh's Fully Hidden Lead", "9950000011")

    # Admin bypasses the per-target visibility check, simulating a legacy/edge-case attachment.
    admin_enroll = h["nimita"].post(f"/api/automations/{samiksha_auto['id']}/enroll", json={"entity_type": "lead", "entity_id": yogesh_lead["id"]})
    assert admin_enroll.status_code == 200

    samiksha_view = h["samiksha"].get(f"/api/automations/{samiksha_auto['id']}/enrollments").json()
    assert len(samiksha_view) == 1
    assert samiksha_view[0]["entity_id"] == yogesh_lead["id"]
    assert samiksha_view[0]["entity_name"] is None

    nimita_view = h["nimita"].get(f"/api/automations/{samiksha_auto['id']}/enrollments").json()
    assert nimita_view[0]["entity_name"] == "Yogesh's Fully Hidden Lead"
