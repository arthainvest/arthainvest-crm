"""Security tests for Campaigns access control (Gate N-11).

campaigns.created_by existed since the table was first created, but no route ever read it back
for scoping - every authenticated employee could list/get/update/delete/send any other
employee's campaign, and could attach an arbitrary (including invisible) Lead/Contact id to any
campaign's recipient list (the campaign-recipient IDOR). This is the first fix for both.

Locked N-11 rules (same ownership model as every other creator-only entity, e.g. Quotations):
  - Admins (Nimita/Yogesh): unrestricted, see/modify/send every campaign.
  - A manager (Samiksha) sees own + direct reports' (Chirag, Amol) campaigns.
  - An individual employee (Chirag, Amol) sees only campaigns they created.
  - Recipient attachment additionally requires the target Lead/Contact be visible to the caller -
    campaign visibility alone is not sufficient authorization to attach an arbitrary person.
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
    yogesh_user_id, yogesh_token = _register_and_login(client, auth_token, "yogesh_camp", role="admin")
    samiksha_user_id, samiksha_token = _register_and_login(client, auth_token, "samiksha_camp")
    chirag_user_id, chirag_token = _register_and_login(client, auth_token, "chirag_camp")
    amol_user_id, amol_token = _register_and_login(client, auth_token, "amol_camp")
    # An employee with no manager relationship to Samiksha's team at all - used only to build a
    # recipient the campaign owner genuinely cannot see, for the redaction test.
    solo_user_id, solo_token = _register_and_login(client, auth_token, "solo_camp")

    samiksha_tm = auth_client.post("/api/team", json={"name": "Samiksha Camp", "role": "employee"}).json()
    chirag_tm = auth_client.post("/api/team", json={"name": "Chirag Camp", "role": "employee"}).json()
    amol_tm = auth_client.post("/api/team", json={"name": "Amol Camp", "role": "employee"}).json()
    solo_tm = auth_client.post("/api/team", json={"name": "Solo Camp", "role": "employee"}).json()

    assert auth_client.put(f"/api/team/{samiksha_tm['id']}", json={"user_id": samiksha_user_id}).status_code == 200
    assert auth_client.put(f"/api/team/{chirag_tm['id']}", json={"user_id": chirag_user_id, "reports_to": samiksha_tm['id']}).status_code == 200
    assert auth_client.put(f"/api/team/{amol_tm['id']}", json={"user_id": amol_user_id, "reports_to": samiksha_tm['id']}).status_code == 200
    assert auth_client.put(f"/api/team/{solo_tm['id']}", json={"user_id": solo_user_id}).status_code == 200

    return {
        "nimita": auth_client,
        "yogesh": _TokenedClient(client, yogesh_token),
        "samiksha": _TokenedClient(client, samiksha_token),
        "chirag": _TokenedClient(client, chirag_token),
        "amol": _TokenedClient(client, amol_token),
        "solo": _TokenedClient(client, solo_token),
    }


def _campaign(client, name="Test Campaign", **overrides):
    payload = {"name": name, "type": "Email", "message": "Hello there"}
    payload.update(overrides)
    resp = client.post("/api/campaigns", json=payload)
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
# Campaign visibility
# ---------------------------------------------------------------------------

def test_admin_sees_all_campaigns(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_campaign = _campaign(h["chirag"], "Chirag's Campaign")
    amol_campaign = _campaign(h["amol"], "Amol's Campaign")
    samiksha_campaign = _campaign(h["samiksha"], "Samiksha's Campaign")

    for admin in (h["nimita"], h["yogesh"]):
        ids = {c["id"] for c in admin.get("/api/campaigns").json()}
        assert chirag_campaign["id"] in ids
        assert amol_campaign["id"] in ids
        assert samiksha_campaign["id"] in ids


def test_manager_sees_own_and_reports_campaigns(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_campaign = _campaign(h["chirag"], "Chirag's Campaign")
    amol_campaign = _campaign(h["amol"], "Amol's Campaign")
    samiksha_campaign = _campaign(h["samiksha"], "Samiksha's Campaign")

    ids = {c["id"] for c in h["samiksha"].get("/api/campaigns").json()}
    assert chirag_campaign["id"] in ids
    assert amol_campaign["id"] in ids
    assert samiksha_campaign["id"] in ids


def test_report_sees_only_own_campaign(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_campaign = _campaign(h["chirag"], "Chirag's Campaign")
    amol_campaign = _campaign(h["amol"], "Amol's Campaign")
    samiksha_campaign = _campaign(h["samiksha"], "Samiksha's Campaign")

    chirag_ids = {c["id"] for c in h["chirag"].get("/api/campaigns").json()}
    assert chirag_campaign["id"] in chirag_ids
    assert amol_campaign["id"] not in chirag_ids
    assert samiksha_campaign["id"] not in chirag_ids

    amol_ids = {c["id"] for c in h["amol"].get("/api/campaigns").json()}
    assert amol_campaign["id"] in amol_ids
    assert chirag_campaign["id"] not in amol_ids
    assert samiksha_campaign["id"] not in amol_ids


def test_manager_cannot_access_unrelated_campaign(client, auth_client, auth_token):
    """Samiksha's own scope must not include a totally unrelated employee's (solo's) campaign."""
    h = hierarchy(client, auth_client, auth_token)
    solo_campaign = _campaign(h["solo"], "Solo's Campaign")

    ids = {c["id"] for c in h["samiksha"].get("/api/campaigns").json()}
    assert solo_campaign["id"] not in ids


# ---------------------------------------------------------------------------
# Write authorization: update / delete / send
# ---------------------------------------------------------------------------

def test_unauthorized_update_denied_with_no_mutation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_campaign = _campaign(h["amol"], "Amol's Campaign")

    resp = h["chirag"].put(f"/api/campaigns/{amol_campaign['id']}", json={"status": "Completed"})
    assert resp.status_code == 403

    unchanged = next(c for c in h["nimita"].get("/api/campaigns").json() if c["id"] == amol_campaign["id"])
    assert unchanged["status"] == amol_campaign["status"]


def test_authorized_update_succeeds(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_campaign = _campaign(h["chirag"], "Chirag's Campaign")

    resp = h["chirag"].put(f"/api/campaigns/{chirag_campaign['id']}", json={"status": "Completed"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "Completed"


def test_manager_can_update_reports_campaign(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_campaign = _campaign(h["amol"], "Amol's Campaign")

    resp = h["samiksha"].put(f"/api/campaigns/{amol_campaign['id']}", json={"status": "Completed"})
    assert resp.status_code == 200


def test_unauthorized_delete_denied_with_no_mutation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_campaign = _campaign(h["amol"], "Amol's Campaign")

    resp = h["chirag"].delete(f"/api/campaigns/{amol_campaign['id']}")
    assert resp.status_code == 403

    ids = {c["id"] for c in h["nimita"].get("/api/campaigns").json()}
    assert amol_campaign["id"] in ids


def test_authorized_delete_succeeds(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_campaign = _campaign(h["chirag"], "Chirag's Campaign")

    resp = h["chirag"].delete(f"/api/campaigns/{chirag_campaign['id']}")
    assert resp.status_code == 200

    ids = {c["id"] for c in h["nimita"].get("/api/campaigns").json()}
    assert chirag_campaign["id"] not in ids


def test_delete_nonexistent_campaign_404s(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    resp = h["chirag"].delete("/api/campaigns/999999999")
    assert resp.status_code == 404


def test_unauthorized_send_denied_before_any_outbound_operation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_campaign = _campaign(h["amol"], "Amol's Campaign", type="Email", message="Body")
    amol_lead = _lead(h["amol"], "Amol Lead", "9990000001")
    h["amol"].post(f"/api/campaigns/{amol_campaign['id']}/recipients", json={"lead_ids": [amol_lead["id"]]})

    with patch("smtplib.SMTP") as mock_smtp_cls:
        resp = h["chirag"].post(f"/api/campaigns/{amol_campaign['id']}/send")
        assert resp.status_code == 403
        mock_smtp_cls.assert_not_called()

    # Recipient status must remain untouched - nothing was attempted.
    recipients = h["amol"].get(f"/api/campaigns/{amol_campaign['id']}/recipients").json()
    assert recipients[0]["status"] == "Pending"


def test_authorized_send_reaches_configured_check(client, auth_client, auth_token):
    """No SMTP credentials configured in tests - reaching a 200 (not 403) proves authorization
    passed, matching the established pattern from WhatsApp's own send tests."""
    h = hierarchy(client, auth_client, auth_token)
    chirag_campaign = _campaign(h["chirag"], "Chirag's Campaign", type="Email", message="Body")

    resp = h["chirag"].post(f"/api/campaigns/{chirag_campaign['id']}/send")
    assert resp.status_code == 200


def test_send_nonexistent_campaign_404s(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    resp = h["chirag"].post("/api/campaigns/999999999/send")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Recipients: authorization + the campaign-recipient IDOR
# ---------------------------------------------------------------------------

def test_unauthorized_add_recipients_denied(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_campaign = _campaign(h["amol"], "Amol's Campaign")
    chirag_lead = _lead(h["chirag"], "Chirag Lead", "9990000002")

    resp = h["chirag"].post(f"/api/campaigns/{amol_campaign['id']}/recipients", json={"lead_ids": [chirag_lead["id"]]})
    assert resp.status_code == 403

    recipients = h["amol"].get(f"/api/campaigns/{amol_campaign['id']}/recipients").json()
    assert recipients == []


def test_unauthorized_get_recipients_denied(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_campaign = _campaign(h["amol"], "Amol's Campaign")

    resp = h["chirag"].get(f"/api/campaigns/{amol_campaign['id']}/recipients")
    assert resp.status_code == 403


def test_authorized_add_recipients_succeeds(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_campaign = _campaign(h["chirag"], "Chirag's Campaign")
    chirag_lead = _lead(h["chirag"], "Chirag's Own Lead", "9990000003")

    resp = h["chirag"].post(f"/api/campaigns/{chirag_campaign['id']}/recipients", json={"lead_ids": [chirag_lead["id"]]})
    assert resp.status_code == 200
    assert resp.json() == {"added": 1, "skipped": 0}


def test_manager_can_attach_reports_lead_to_reports_campaign(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_campaign = _campaign(h["amol"], "Amol's Campaign")
    amol_lead = _lead(h["amol"], "Amol's Own Lead", "9990000004")

    resp = h["samiksha"].post(f"/api/campaigns/{amol_campaign['id']}/recipients", json={"lead_ids": [amol_lead["id"]]})
    assert resp.status_code == 200
    assert resp.json() == {"added": 1, "skipped": 0}


def test_hidden_lead_cannot_be_attached(client, auth_client, auth_token):
    """The core IDOR fix: campaign visibility alone is not enough - the target Lead must also
    be visible to the caller. Chirag owns the campaign but tries to attach Amol's lead."""
    h = hierarchy(client, auth_client, auth_token)
    chirag_campaign = _campaign(h["chirag"], "Chirag's Campaign")
    amol_lead = _lead(h["amol"], "Amol's Hidden Lead", "9990000005")

    resp = h["chirag"].post(f"/api/campaigns/{chirag_campaign['id']}/recipients", json={"lead_ids": [amol_lead["id"]]})
    assert resp.status_code == 200
    assert resp.json() == {"added": 0, "skipped": 1}

    recipients = h["chirag"].get(f"/api/campaigns/{chirag_campaign['id']}/recipients").json()
    assert recipients == []


def test_hidden_contact_cannot_be_attached(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_campaign = _campaign(h["chirag"], "Chirag's Campaign")
    amol_contact = _contact(h["amol"], "Amol's Hidden Contact", "9990000006")

    resp = h["chirag"].post(f"/api/campaigns/{chirag_campaign['id']}/recipients", json={"contact_ids": [amol_contact["id"]]})
    assert resp.status_code == 200
    assert resp.json() == {"added": 0, "skipped": 1}

    recipients = h["chirag"].get(f"/api/campaigns/{chirag_campaign['id']}/recipients").json()
    assert recipients == []


def test_nonexistent_lead_id_treated_same_as_hidden(client, auth_client, auth_token):
    """A nonexistent id must be rejected identically to a real-but-invisible one, so this
    endpoint never confirms whether an id exists."""
    h = hierarchy(client, auth_client, auth_token)
    chirag_campaign = _campaign(h["chirag"], "Chirag's Campaign")

    resp = h["chirag"].post(f"/api/campaigns/{chirag_campaign['id']}/recipients", json={"lead_ids": [999999999]})
    assert resp.status_code == 200
    assert resp.json() == {"added": 0, "skipped": 1}


def test_mixed_visible_and_invisible_targets_handled_safely(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_campaign = _campaign(h["chirag"], "Chirag's Campaign")
    chirag_lead = _lead(h["chirag"], "Chirag's Visible Lead", "9990000007")
    amol_lead = _lead(h["amol"], "Amol's Invisible Lead", "9990000008")

    resp = h["chirag"].post(
        f"/api/campaigns/{chirag_campaign['id']}/recipients",
        json={"lead_ids": [chirag_lead["id"], amol_lead["id"]]}
    )
    assert resp.status_code == 200
    assert resp.json() == {"added": 1, "skipped": 1}

    recipients = h["chirag"].get(f"/api/campaigns/{chirag_campaign['id']}/recipients").json()
    assert len(recipients) == 1
    assert recipients[0]["lead_id"] == chirag_lead["id"]


def test_recipient_list_redacts_hidden_entity_details(client, auth_client, auth_token):
    """Defense-in-depth for data attached before/outside the normal flow (e.g. by an admin) -
    a recipient list must never display the name/phone/email of a Lead the viewer cannot see,
    even though the campaign itself is visible to them."""
    h = hierarchy(client, auth_client, auth_token)
    samiksha_campaign = _campaign(h["samiksha"], "Samiksha's Campaign")
    solo_lead = _lead(h["solo"], "Solo's Fully Hidden Lead", "9990000009")

    # Admin bypasses both the campaign-visibility and lead-visibility checks, simulating a
    # pre-existing/legacy attachment that the IDOR fix itself would now prevent going forward.
    admin_add = h["nimita"].post(f"/api/campaigns/{samiksha_campaign['id']}/recipients", json={"lead_ids": [solo_lead["id"]]})
    assert admin_add.status_code == 200
    assert admin_add.json() == {"added": 1, "skipped": 0}

    samiksha_view = h["samiksha"].get(f"/api/campaigns/{samiksha_campaign['id']}/recipients").json()
    assert len(samiksha_view) == 1
    assert samiksha_view[0]["lead_id"] == solo_lead["id"]
    assert samiksha_view[0]["lead_name"] is None
    assert samiksha_view[0]["name"] is None
    assert samiksha_view[0]["phone"] is None

    # Admin still sees the real details.
    nimita_view = h["nimita"].get(f"/api/campaigns/{samiksha_campaign['id']}/recipients").json()
    assert nimita_view[0]["lead_name"] == "Solo's Fully Hidden Lead"


def test_recipient_removal_cannot_cross_ownership_boundary(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_campaign = _campaign(h["amol"], "Amol's Campaign")
    amol_lead = _lead(h["amol"], "Amol's Lead", "9990000010")
    h["amol"].post(f"/api/campaigns/{amol_campaign['id']}/recipients", json={"lead_ids": [amol_lead["id"]]})
    recipient_id = h["amol"].get(f"/api/campaigns/{amol_campaign['id']}/recipients").json()[0]["id"]

    resp = h["chirag"].delete(f"/api/campaigns/{amol_campaign['id']}/recipients/{recipient_id}")
    assert resp.status_code == 403

    still_present = h["amol"].get(f"/api/campaigns/{amol_campaign['id']}/recipients").json()
    assert any(r["id"] == recipient_id for r in still_present)


def test_authorized_recipient_removal_succeeds(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_campaign = _campaign(h["chirag"], "Chirag's Campaign")
    chirag_lead = _lead(h["chirag"], "Chirag's Lead", "9990000011")
    h["chirag"].post(f"/api/campaigns/{chirag_campaign['id']}/recipients", json={"lead_ids": [chirag_lead["id"]]})
    recipient_id = h["chirag"].get(f"/api/campaigns/{chirag_campaign['id']}/recipients").json()[0]["id"]

    resp = h["chirag"].delete(f"/api/campaigns/{chirag_campaign['id']}/recipients/{recipient_id}")
    assert resp.status_code == 200
    assert h["chirag"].get(f"/api/campaigns/{chirag_campaign['id']}/recipients").json() == []
