"""Security tests for the employee data-visibility feature (access_control.py).

Mirrors the real reported bug and the confirmed business rule: admins (Nimita/Yogesh) see and
can modify everything; Samiksha (a manager) sees her own records plus her direct reports'
(Chirag and Amol); Chirag and Amol each see only their own records, strictly isolated from
each other and from Samiksha's own personal records.

Unlike every other test file in this suite (which runs entirely as the seeded admin `testuser`
and therefore never exercises non-admin scoping at all), every test here deliberately runs as a
non-admin employee to prove the restriction actually holds - "the existing 705 tests still
pass" only proves the admin bypass works, not that anyone is actually restricted.

Covers, per the resume instructions:
  - admin sees everything; Samiksha sees herself+Chirag+Amol; Chirag/Amol are mutually isolated
    and isolated from Samiksha's own records
  - out-of-scope records are unreachable via direct GET, reverse-lookup routes, update, delete,
    assign, and link-to-bypass-visibility
  - a rejected write leaves the underlying record unchanged
  - a visible record linked to an invisible entity does not expose that entity's name (the
    denormalized cross-entity display-field leak fix)
  - GET /api/contacts/renewals follows the same visibility model as the rest of Contacts
"""
import pytest


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


@pytest.fixture()
def hierarchy(client, auth_client, auth_token):
    """A second admin (Yogesh-equivalent) plus a 3-person reporting hierarchy: Samiksha
    (manager) with Chirag and Amol as her direct reports - mirroring the real reported bug's
    exact org shape. `auth_client`/`auth_token` are the seeded testuser (Nimita-equivalent)."""
    yogesh_user_id, yogesh_token = _register_and_login(client, auth_token, "yogesh_sec", role="admin")
    samiksha_user_id, samiksha_token = _register_and_login(client, auth_token, "samiksha_sec")
    chirag_user_id, chirag_token = _register_and_login(client, auth_token, "chirag_sec")
    amol_user_id, amol_token = _register_and_login(client, auth_token, "amol_sec")

    samiksha_tm = auth_client.post("/api/team", json={"name": "Samiksha Sec", "role": "employee"}).json()
    chirag_tm = auth_client.post("/api/team", json={"name": "Chirag Sec", "role": "employee"}).json()
    amol_tm = auth_client.post("/api/team", json={"name": "Amol Sec", "role": "employee"}).json()

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


def _assign(client, path, team_member_id):
    resp = client.put(path, json={"team_member_id": team_member_id})
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Contacts - the exact entity from the original bug report
# ---------------------------------------------------------------------------

def test_admins_see_everyones_contacts(hierarchy):
    chirag_contact = hierarchy["chirag"].post("/api/contacts", json={"name": "Chirag's Client", "phone": "9990000001"}).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{chirag_contact['id']}/assign", hierarchy["chirag_tm_id"])

    for admin in (hierarchy["nimita"], hierarchy["yogesh"]):
        listing = admin.get("/api/contacts").json()
        assert any(c["id"] == chirag_contact["id"] for c in listing)
        assert admin.get(f"/api/contacts/{chirag_contact['id']}").status_code == 200


def test_manager_sees_both_direct_reports_contacts_peer_isolation_holds(hierarchy):
    chirag_contact = hierarchy["chirag"].post("/api/contacts", json={"name": "Chirag's Client", "phone": "9990000002"}).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{chirag_contact['id']}/assign", hierarchy["chirag_tm_id"])
    amol_contact = hierarchy["amol"].post("/api/contacts", json={"name": "Amol's Client", "phone": "9990000003"}).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{amol_contact['id']}/assign", hierarchy["amol_tm_id"])

    # Samiksha (manager) sees both her reports' contacts.
    samiksha_ids = {c["id"] for c in hierarchy["samiksha"].get("/api/contacts").json()}
    assert chirag_contact["id"] in samiksha_ids
    assert amol_contact["id"] in samiksha_ids

    # Chirag sees only his own - not Amol's. This is the exact bug reported, reproduced and
    # confirmed fixed.
    chirag_ids = {c["id"] for c in hierarchy["chirag"].get("/api/contacts").json()}
    assert chirag_contact["id"] in chirag_ids
    assert amol_contact["id"] not in chirag_ids

    # And symmetrically the other direction.
    amol_ids = {c["id"] for c in hierarchy["amol"].get("/api/contacts").json()}
    assert amol_contact["id"] in amol_ids
    assert chirag_contact["id"] not in amol_ids

    # Direct GET on the peer's contact 403s, it isn't just absent from the list.
    assert hierarchy["amol"].get(f"/api/contacts/{chirag_contact['id']}").status_code == 403
    assert hierarchy["chirag"].get(f"/api/contacts/{amol_contact['id']}").status_code == 403


def test_reports_cannot_see_managers_own_unassigned_contact(hierarchy):
    """Samiksha's own personal record (created by her, not assigned to a report) is admin/
    self-only - her reports do not inherit visibility upward."""
    samiksha_contact = hierarchy["samiksha"].post("/api/contacts", json={"name": "Samiksha's Own Client", "phone": "9990000004"}).json()

    assert hierarchy["chirag"].get(f"/api/contacts/{samiksha_contact['id']}").status_code == 403
    assert hierarchy["amol"].get(f"/api/contacts/{samiksha_contact['id']}").status_code == 403
    assert hierarchy["samiksha"].get(f"/api/contacts/{samiksha_contact['id']}").status_code == 200
    assert hierarchy["nimita"].get(f"/api/contacts/{samiksha_contact['id']}").status_code == 200


def test_out_of_scope_contact_cannot_be_updated_deleted_or_assigned_and_stays_unchanged(hierarchy):
    chirag_contact = hierarchy["chirag"].post("/api/contacts", json={"name": "Chirag's Client", "phone": "9990000005"}).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{chirag_contact['id']}/assign", hierarchy["chirag_tm_id"])

    update_resp = hierarchy["amol"].put(f"/api/contacts/{chirag_contact['id']}", json={"name": "Hijacked Name"})
    assert update_resp.status_code == 403

    assign_resp = hierarchy["amol"].put(f"/api/contacts/{chirag_contact['id']}/assign", json={"team_member_id": hierarchy["amol_tm_id"]})
    assert assign_resp.status_code == 403

    delete_resp = hierarchy["amol"].delete(f"/api/contacts/{chirag_contact['id']}")
    assert delete_resp.status_code == 403

    # Confirm none of the rejected attempts actually mutated anything - fetched as the owner.
    still_there = hierarchy["chirag"].get(f"/api/contacts/{chirag_contact['id']}").json()
    assert still_there["name"] == "Chirag's Client"
    assert still_there["assigned_team_member_id"] == hierarchy["chirag_tm_id"]


def test_out_of_scope_contact_unreachable_via_reverse_lookup(hierarchy):
    """A peer cannot pull an out-of-scope contact's data back out through a reverse-lookup
    route (e.g. the company's contact list) either - only via a bulk endpoint that filters by
    the contact's own scope, same as the direct list."""
    company = hierarchy["nimita"].post("/api/companies", json={"name": "Shared Employer Sec"}).json()
    chirag_contact = hierarchy["chirag"].post("/api/contacts", json={"name": "Chirag's Client", "phone": "9990000006", "company_id": company["id"]}).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{chirag_contact['id']}/assign", hierarchy["chirag_tm_id"])

    amol_view = hierarchy["amol"].get(f"/api/companies/{company['id']}/contacts").json()
    assert all(c["id"] != chirag_contact["id"] for c in amol_view)

    chirag_view = hierarchy["chirag"].get(f"/api/companies/{company['id']}/contacts").json()
    assert any(c["id"] == chirag_contact["id"] for c in chirag_view)


def test_renewals_endpoint_follows_the_same_contact_visibility_model(hierarchy):
    """GET /api/contacts/renewals was the confirmed, previously-unfiltered gap - fixed to use
    the identical Contact visibility rule as every other Contacts endpoint."""
    chirag_contact = hierarchy["chirag"].post(
        "/api/contacts",
        json={"name": "Chirag's Renewal Client", "phone": "9990000007", "renewal_date": "2026-01-01"},
    ).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{chirag_contact['id']}/assign", hierarchy["chirag_tm_id"])

    amol_renewals = hierarchy["amol"].get("/api/contacts/renewals").json()
    assert all(r["id"] != chirag_contact["id"] for r in amol_renewals)

    chirag_renewals = hierarchy["chirag"].get("/api/contacts/renewals").json()
    assert any(r["id"] == chirag_contact["id"] for r in chirag_renewals)

    samiksha_renewals = hierarchy["samiksha"].get("/api/contacts/renewals").json()
    assert any(r["id"] == chirag_contact["id"] for r in samiksha_renewals)

    admin_renewals = hierarchy["nimita"].get("/api/contacts/renewals").json()
    assert any(r["id"] == chirag_contact["id"] for r in admin_renewals)


# ---------------------------------------------------------------------------
# Cross-entity display-field redaction - the second confirmed leak
# ---------------------------------------------------------------------------

def test_deal_does_not_leak_out_of_scope_contacts_name(hierarchy):
    """The exact scenario from the security checkpoint report: Chirag can see a Deal, but the
    Deal's linked Contact belongs to Amol - Chirag must not learn that Contact's name through
    the Deal's own (otherwise-legitimate) response."""
    amol_contact = hierarchy["amol"].post("/api/contacts", json={"name": "Amol's Private Client", "phone": "9990000008"}).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{amol_contact['id']}/assign", hierarchy["amol_tm_id"])

    chirag_lead = hierarchy["chirag"].post("/api/leads", json={"name": "Chirag Lead Sec", "phone": "9990000009"}).json()
    chirag_deal = hierarchy["chirag"].post("/api/deals", json={"lead_id": chirag_lead["id"], "deal_value": 100000, "loan_product": "Home"}).json()
    _assign(hierarchy["nimita"], f"/api/deals/{chirag_deal['id']}/assign", hierarchy["chirag_tm_id"])

    # Link the deal to Amol's contact (an admin action, modeling e.g. a referral scenario).
    linked = hierarchy["nimita"].put(f"/api/deals/{chirag_deal['id']}/contact", json={"contact_id": amol_contact["id"]}).json()
    assert linked["contact_id"] == amol_contact["id"]

    # Chirag can see the deal (he owns it) ...
    chirag_view = hierarchy["chirag"].get(f"/api/deals/{chirag_deal['id']}")
    assert chirag_view.status_code == 200
    # ... but must NOT see the linked contact's name, since that contact is Amol's, not his.
    assert chirag_view.json()["contact_name"] is None

    # Confirmed still present for someone who *can* see that contact.
    amol_view = hierarchy["amol"].get(f"/api/contacts/{amol_contact['id']}")
    assert amol_view.json()["name"] == "Amol's Private Client"

    # And an admin, who has no restriction, still sees the real name on the deal.
    admin_view = hierarchy["nimita"].get(f"/api/deals/{chirag_deal['id']}")
    assert admin_view.json()["contact_name"] == "Amol's Private Client"

    # The same deal appearing in Chirag's list view must be redacted identically.
    list_view = hierarchy["chirag"].get("/api/deals").json()
    row = next(d for d in list_view if d["id"] == chirag_deal["id"])
    assert row["contact_name"] is None


def test_task_does_not_leak_out_of_scope_leads_name(hierarchy):
    """Same redaction rule, a different entity pair (Task -> Lead) - confirms the fix isn't
    special-cased to Deal->Contact alone."""
    amol_lead = hierarchy["amol"].post("/api/leads", json={"name": "Amol's Private Lead", "phone": "9990000010"}).json()
    _assign(hierarchy["nimita"], f"/api/leads/{amol_lead['id']}/assign", hierarchy["amol_tm_id"])

    chirag_task = hierarchy["chirag"].post(
        "/api/tasks",
        json={"title": "Chirag Task Sec", "due_date": "2026-12-31", "assigned_team_member_id": hierarchy["chirag_tm_id"]},
    ).json()

    with_lead = hierarchy["nimita"].put(f"/api/tasks/{chirag_task['id']}", json={"lead_id": amol_lead["id"]})
    assert with_lead.status_code == 200
    assert with_lead.json()["lead_id"] == amol_lead["id"]

    chirag_view = hierarchy["chirag"].get(f"/api/tasks/{chirag_task['id']}")
    assert chirag_view.status_code == 200
    assert chirag_view.json()["lead_name"] is None

    admin_view = hierarchy["nimita"].get(f"/api/tasks/{chirag_task['id']}")
    assert admin_view.json()["lead_name"] == "Amol's Private Lead"


def test_quotation_creator_only_visibility_ignores_linked_deals_assignee(hierarchy):
    """Quotations have no assignee of their own - confirmed rule is created_by only, even when
    linked to a Deal assigned to someone else."""
    chirag_lead = hierarchy["chirag"].post("/api/leads", json={"name": "Chirag Lead Sec 2", "phone": "9990000011"}).json()
    chirag_deal = hierarchy["chirag"].post("/api/deals", json={"lead_id": chirag_lead["id"], "deal_value": 200000, "loan_product": "Business"}).json()
    _assign(hierarchy["nimita"], f"/api/deals/{chirag_deal['id']}/assign", hierarchy["chirag_tm_id"])

    amol_quotation = hierarchy["amol"].post(
        "/api/quotations",
        json={"title": "Amol's Quotation", "items": [{"description": "Fee", "amount": 1000}]},
    ).json()
    linked = hierarchy["nimita"].put(f"/api/quotations/{amol_quotation['id']}/deal", json={"deal_id": chirag_deal["id"]})
    assert linked.status_code == 200

    # Amol created it - he can see it regardless of the deal's assignment.
    assert hierarchy["amol"].get(f"/api/quotations/{amol_quotation['id']}").status_code == 200
    # Chirag owns the linked deal but did NOT create the quotation - still invisible to him.
    assert hierarchy["chirag"].get(f"/api/quotations/{amol_quotation['id']}").status_code == 403
    # Samiksha manages Amol, so she can see it too.
    assert hierarchy["samiksha"].get(f"/api/quotations/{amol_quotation['id']}").status_code == 200


def test_company_visible_via_linked_contact_even_without_creating_it(hierarchy):
    """Confirmed Company rule: visible if the caller created it, OR can see a Contact/Deal
    that references it - Companies have no assignee column of their own."""
    company = hierarchy["nimita"].post("/api/companies", json={"name": "Chirags Employer Sec"}).json()
    chirag_contact = hierarchy["chirag"].post(
        "/api/contacts", json={"name": "Chirag's Company Contact", "phone": "9990000012", "company_id": company["id"]}
    ).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{chirag_contact['id']}/assign", hierarchy["chirag_tm_id"])

    chirag_companies = {c["id"] for c in hierarchy["chirag"].get("/api/companies").json()}
    assert company["id"] in chirag_companies

    amol_companies = {c["id"] for c in hierarchy["amol"].get("/api/companies").json()}
    assert company["id"] not in amol_companies


# ---------------------------------------------------------------------------
# Hardening pass 2: Task link/reverse authorization
# ---------------------------------------------------------------------------

def test_task_link_endpoints_reject_out_of_scope_task(hierarchy):
    """Chirag cannot manipulate a Task he cannot see - the mutation itself is unauthorized,
    not just its response."""
    amol_task = hierarchy["amol"].post(
        "/api/tasks", json={"title": "Amol Task Sec", "due_date": "2026-12-31", "assigned_team_member_id": hierarchy["amol_tm_id"]},
    ).json()

    amol_contact = hierarchy["amol"].post("/api/contacts", json={"name": "Amol Contact For Task", "phone": "9990000013"}).json()

    resp = hierarchy["chirag"].put(f"/api/tasks/{amol_task['id']}/contact", json={"contact_id": amol_contact["id"]})
    assert resp.status_code == 403

    # Confirm the task's link was NOT mutated by the rejected attempt.
    still = hierarchy["amol"].get(f"/api/tasks/{amol_task['id']}").json()
    assert still["contact_id"] is None


def test_task_link_endpoints_reject_out_of_scope_linked_target(hierarchy):
    """Chirag owns a Task, but cannot link it to a Contact he cannot see - linking must not
    become a way to associate your own accessible record with someone else's data."""
    chirag_task = hierarchy["chirag"].post(
        "/api/tasks", json={"title": "Chirag Task For Link", "due_date": "2026-12-31", "assigned_team_member_id": hierarchy["chirag_tm_id"]},
    ).json()
    amol_contact = hierarchy["amol"].post("/api/contacts", json={"name": "Amol Contact Not Linkable", "phone": "9990000014"}).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{amol_contact['id']}/assign", hierarchy["amol_tm_id"])

    resp = hierarchy["chirag"].put(f"/api/tasks/{chirag_task['id']}/contact", json={"contact_id": amol_contact["id"]})
    assert resp.status_code == 403

    still = hierarchy["chirag"].get(f"/api/tasks/{chirag_task['id']}").json()
    assert still["contact_id"] is None


def test_task_reverse_lookup_never_discovers_an_inaccessible_task(hierarchy):
    """An out-of-scope Task must not surface through a reverse-lookup route even when the
    path's own parent id (here, a Contact) is visible to the caller."""
    shared_contact = hierarchy["nimita"].post("/api/contacts", json={"name": "Shared Contact For Tasks", "phone": "9990000015"}).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{shared_contact['id']}/assign", hierarchy["chirag_tm_id"])

    amol_task = hierarchy["amol"].post(
        "/api/tasks", json={"title": "Amol Task Via Contact", "due_date": "2026-12-31", "assigned_team_member_id": hierarchy["amol_tm_id"]},
    ).json()
    linked = hierarchy["nimita"].put(f"/api/tasks/{amol_task['id']}/contact", json={"contact_id": shared_contact["id"]})
    assert linked.status_code == 200

    # Chirag can see the shared contact (it's his), but must not see Amol's task through it.
    chirag_view = hierarchy["chirag"].get(f"/api/contacts/{shared_contact['id']}/tasks").json()
    assert all(t["id"] != amol_task["id"] for t in chirag_view)

    amol_view = hierarchy["amol"].get(f"/api/contacts/{shared_contact['id']}/tasks").json()
    assert any(t["id"] == amol_task["id"] for t in amol_view)


# ---------------------------------------------------------------------------
# Hardening pass 2: Contact documents
# ---------------------------------------------------------------------------

def test_contact_documents_full_matrix(hierarchy):
    amol_contact = hierarchy["amol"].post("/api/contacts", json={"name": "Amol Doc Client", "phone": "9990000016"}).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{amol_contact['id']}/assign", hierarchy["amol_tm_id"])

    upload = hierarchy["amol"].post(
        f"/api/contacts/{amol_contact['id']}/documents",
        files={"file": ("pan.pdf", b"fake-pan-bytes", "application/pdf")},
    )
    assert upload.status_code == 200
    doc_id = upload.json()["id"]

    # Chirag (peer, no access to Amol's contact) cannot list, download by known id, or delete.
    assert hierarchy["chirag"].get(f"/api/contacts/{amol_contact['id']}/documents").status_code == 403
    assert hierarchy["chirag"].get(f"/api/contacts/{amol_contact['id']}/documents/{doc_id}/content").status_code == 403
    assert hierarchy["chirag"].delete(f"/api/contacts/{amol_contact['id']}/documents/{doc_id}").status_code == 403
    # Nor can Chirag upload a new document to a Contact he cannot see.
    bad_upload = hierarchy["chirag"].post(
        f"/api/contacts/{amol_contact['id']}/documents",
        files={"file": ("evil.pdf", b"x", "application/pdf")},
    )
    assert bad_upload.status_code == 403

    # Amol (owner), Samiksha (manager), and admins can all reach it.
    assert hierarchy["amol"].get(f"/api/contacts/{amol_contact['id']}/documents/{doc_id}/content").status_code == 200
    assert hierarchy["samiksha"].get(f"/api/contacts/{amol_contact['id']}/documents/{doc_id}/content").status_code == 200
    assert hierarchy["nimita"].get(f"/api/contacts/{amol_contact['id']}/documents/{doc_id}/content").status_code == 200

    # The rejected delete really didn't delete anything.
    still_listed = hierarchy["amol"].get(f"/api/contacts/{amol_contact['id']}/documents").json()
    assert any(d["id"] == doc_id for d in still_listed)


# ---------------------------------------------------------------------------
# Hardening pass 2: Contact/Lead notes, audio, AI-suggest
# ---------------------------------------------------------------------------

def test_contact_notes_and_ai_suggest_follow_parent_visibility(hierarchy):
    amol_contact = hierarchy["amol"].post("/api/contacts", json={"name": "Amol Notes Client", "phone": "9990000017"}).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{amol_contact['id']}/assign", hierarchy["amol_tm_id"])

    note = hierarchy["amol"].post(f"/api/contacts/{amol_contact['id']}/notes", json={"transcript": "Called, interested."})
    assert note.status_code == 200
    note_id = note.json()["id"]

    assert hierarchy["chirag"].get(f"/api/contacts/{amol_contact['id']}/notes").status_code == 403
    assert hierarchy["chirag"].post(f"/api/contacts/{amol_contact['id']}/notes", json={"transcript": "Injected"}).status_code == 403
    assert hierarchy["chirag"].put(f"/api/contacts/{amol_contact['id']}/notes/{note_id}", json={"transcript": "Hijacked"}).status_code == 403
    assert hierarchy["chirag"].delete(f"/api/contacts/{amol_contact['id']}/notes/{note_id}").status_code == 403
    assert hierarchy["chirag"].post(
        f"/api/contacts/{amol_contact['id']}/notes/{note_id}/audio",
        files={"audio": ("note.wav", b"fake-audio", "audio/wav")},
    ).status_code == 403
    assert hierarchy["chirag"].post(f"/api/contacts/{amol_contact['id']}/ai-suggest").status_code == 403

    # Owner and admin still work; the rejected mutations left the note unchanged.
    assert hierarchy["amol"].get(f"/api/contacts/{amol_contact['id']}/notes").status_code == 200
    assert hierarchy["nimita"].post(f"/api/contacts/{amol_contact['id']}/ai-suggest").status_code == 200
    unchanged = hierarchy["amol"].get(f"/api/contacts/{amol_contact['id']}/notes").json()
    assert unchanged[0]["transcript"] == "Called, interested."


def test_lead_notes_and_ai_suggest_follow_parent_visibility(hierarchy):
    amol_lead = hierarchy["amol"].post("/api/leads", json={"name": "Amol Notes Lead", "phone": "9990000018"}).json()
    _assign(hierarchy["nimita"], f"/api/leads/{amol_lead['id']}/assign", hierarchy["amol_tm_id"])

    note = hierarchy["amol"].post(f"/api/leads/{amol_lead['id']}/notes", json={"transcript": "First contact made."})
    assert note.status_code == 200
    note_id = note.json()["id"]

    assert hierarchy["chirag"].get(f"/api/leads/{amol_lead['id']}/notes").status_code == 403
    assert hierarchy["chirag"].post(f"/api/leads/{amol_lead['id']}/notes", json={"transcript": "Injected"}).status_code == 403
    assert hierarchy["chirag"].put(f"/api/leads/{amol_lead['id']}/notes/{note_id}", json={"transcript": "Hijacked"}).status_code == 403
    assert hierarchy["chirag"].delete(f"/api/leads/{amol_lead['id']}/notes/{note_id}").status_code == 403
    assert hierarchy["chirag"].post(
        f"/api/leads/{amol_lead['id']}/notes/{note_id}/audio",
        files={"audio": ("note.wav", b"fake-audio", "audio/wav")},
    ).status_code == 403
    assert hierarchy["chirag"].post(f"/api/leads/{amol_lead['id']}/ai-suggest").status_code == 403

    assert hierarchy["amol"].get(f"/api/leads/{amol_lead['id']}/notes").status_code == 200
    unchanged = hierarchy["amol"].get(f"/api/leads/{amol_lead['id']}/notes").json()
    assert unchanged[0]["transcript"] == "First contact made."


# ---------------------------------------------------------------------------
# N-29: note-audio recordings moved off the unauthenticated /uploads static mount onto a
# DB-blob-plus-authenticated-GET pattern - the GET route must re-check parent visibility on
# every request, not just at upload time.
# ---------------------------------------------------------------------------

def test_contact_note_audio_url_no_longer_points_at_uploads_mount(hierarchy):
    amol_contact = hierarchy["amol"].post("/api/contacts", json={"name": "Amol Audio Client", "phone": "9990000019"}).json()
    note = hierarchy["amol"].post(f"/api/contacts/{amol_contact['id']}/notes", json={"transcript": "x"}).json()

    uploaded = hierarchy["amol"].post(
        f"/api/contacts/{amol_contact['id']}/notes/{note['id']}/audio",
        files={"audio": ("note.wav", b"fake-audio-bytes", "audio/wav")},
    )
    assert uploaded.status_code == 200
    audio_url = uploaded.json()["audio_url"]
    assert audio_url == f"/api/contacts/{amol_contact['id']}/notes/{note['id']}/audio"
    assert not audio_url.startswith("/uploads/")


def test_contact_note_audio_get_requires_parent_visibility(hierarchy):
    amol_contact = hierarchy["amol"].post("/api/contacts", json={"name": "Amol Audio Client 2", "phone": "9990000020"}).json()
    note = hierarchy["amol"].post(f"/api/contacts/{amol_contact['id']}/notes", json={"transcript": "x"}).json()
    hierarchy["amol"].post(
        f"/api/contacts/{amol_contact['id']}/notes/{note['id']}/audio",
        files={"audio": ("note.wav", b"real-recording-bytes", "audio/wav")},
    )

    # Peer with no access to this contact - IDOR check.
    resp = hierarchy["chirag"].get(f"/api/contacts/{amol_contact['id']}/notes/{note['id']}/audio")
    assert resp.status_code == 403

    # Owner and admin can fetch the actual bytes back.
    own = hierarchy["amol"].get(f"/api/contacts/{amol_contact['id']}/notes/{note['id']}/audio")
    assert own.status_code == 200
    assert own.content == b"real-recording-bytes"
    assert own.headers["content-type"] == "audio/wav"

    admin = hierarchy["nimita"].get(f"/api/contacts/{amol_contact['id']}/notes/{note['id']}/audio")
    assert admin.status_code == 200
    assert admin.content == b"real-recording-bytes"


def test_contact_note_audio_get_404_when_no_recording(hierarchy):
    amol_contact = hierarchy["amol"].post("/api/contacts", json={"name": "Amol No Audio", "phone": "9990000021"}).json()
    note = hierarchy["amol"].post(f"/api/contacts/{amol_contact['id']}/notes", json={"transcript": "no recording"}).json()

    resp = hierarchy["amol"].get(f"/api/contacts/{amol_contact['id']}/notes/{note['id']}/audio")
    assert resp.status_code == 404


def test_lead_note_audio_url_no_longer_points_at_uploads_mount(hierarchy):
    amol_lead = hierarchy["amol"].post("/api/leads", json={"name": "Amol Audio Lead", "phone": "9990000022"}).json()
    note = hierarchy["amol"].post(f"/api/leads/{amol_lead['id']}/notes", json={"transcript": "x"}).json()

    uploaded = hierarchy["amol"].post(
        f"/api/leads/{amol_lead['id']}/notes/{note['id']}/audio",
        files={"audio": ("note.wav", b"fake-audio-bytes", "audio/wav")},
    )
    assert uploaded.status_code == 200
    audio_url = uploaded.json()["audio_url"]
    assert audio_url == f"/api/leads/{amol_lead['id']}/notes/{note['id']}/audio"
    assert not audio_url.startswith("/uploads/")


def test_lead_note_audio_get_requires_parent_visibility(hierarchy):
    amol_lead = hierarchy["amol"].post("/api/leads", json={"name": "Amol Audio Lead 2", "phone": "9990000023"}).json()
    note = hierarchy["amol"].post(f"/api/leads/{amol_lead['id']}/notes", json={"transcript": "x"}).json()
    hierarchy["amol"].post(
        f"/api/leads/{amol_lead['id']}/notes/{note['id']}/audio",
        files={"audio": ("note.wav", b"real-lead-recording", "audio/wav")},
    )

    resp = hierarchy["chirag"].get(f"/api/leads/{amol_lead['id']}/notes/{note['id']}/audio")
    assert resp.status_code == 403

    own = hierarchy["amol"].get(f"/api/leads/{amol_lead['id']}/notes/{note['id']}/audio")
    assert own.status_code == 200
    assert own.content == b"real-lead-recording"

    manager = hierarchy["samiksha"].get(f"/api/leads/{amol_lead['id']}/notes/{note['id']}/audio")
    assert manager.status_code == 200
    assert manager.content == b"real-lead-recording"


def test_lead_note_audio_get_404_when_no_recording(hierarchy):
    amol_lead = hierarchy["amol"].post("/api/leads", json={"name": "Amol No Audio Lead", "phone": "9990000024"}).json()
    note = hierarchy["amol"].post(f"/api/leads/{amol_lead['id']}/notes", json={"transcript": "no recording"}).json()

    resp = hierarchy["amol"].get(f"/api/leads/{amol_lead['id']}/notes/{note['id']}/audio")
    assert resp.status_code == 404


def test_note_audio_mismatched_parent_and_note_id_404s(hierarchy):
    """IDOR check: pairing a real note_id with the wrong parent contact_id in the URL must
    404, not accidentally serve the recording via the mismatched parent's visibility."""
    amol_contact = hierarchy["amol"].post("/api/contacts", json={"name": "Amol Mismatch A", "phone": "9990000025"}).json()
    nimita_contact = hierarchy["nimita"].post("/api/contacts", json={"name": "Nimita Mismatch B", "phone": "9990000026"}).json()
    note = hierarchy["amol"].post(f"/api/contacts/{amol_contact['id']}/notes", json={"transcript": "x"}).json()
    hierarchy["amol"].post(
        f"/api/contacts/{amol_contact['id']}/notes/{note['id']}/audio",
        files={"audio": ("note.wav", b"bytes", "audio/wav")},
    )

    # Admin can see nimita_contact, but note['id'] doesn't belong to it.
    resp = hierarchy["nimita"].get(f"/api/contacts/{nimita_contact['id']}/notes/{note['id']}/audio")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Hardening pass 2: Company team-members
# ---------------------------------------------------------------------------

def test_company_team_members_follows_company_visibility(hierarchy):
    amol_company = hierarchy["amol"].post("/api/companies", json={"name": "Amol Only Employer"}).json()
    amol_contact = hierarchy["amol"].post(
        "/api/contacts", json={"name": "Amol Company Contact", "phone": "9990000019", "company_id": amol_company["id"]}
    ).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{amol_contact['id']}/assign", hierarchy["amol_tm_id"])

    assert hierarchy["chirag"].get(f"/api/companies/{amol_company['id']}/team_members").status_code == 403
    assert hierarchy["amol"].get(f"/api/companies/{amol_company['id']}/team_members").status_code == 200
    assert hierarchy["nimita"].get(f"/api/companies/{amol_company['id']}/team_members").status_code == 200


def test_team_member_companies_follows_company_visibility(hierarchy):
    """Mirror image of the Company team_members fix, found during the final audit: Chirag
    should not learn which companies Amol has worked with via GET /api/team/{amol}/companies
    for a company Chirag otherwise cannot see."""
    amol_company = hierarchy["nimita"].post("/api/companies", json={"name": "Amol Deal Employer"}).json()
    amol_lead = hierarchy["amol"].post("/api/leads", json={"name": "Amol Lead For Deal", "phone": "9990000020"}).json()
    amol_deal = hierarchy["amol"].post(
        "/api/deals", json={"lead_id": amol_lead["id"], "deal_value": 50000, "loan_product": "Home", "company_id": amol_company["id"]}
    ).json()
    _assign(hierarchy["nimita"], f"/api/deals/{amol_deal['id']}/assign", hierarchy["amol_tm_id"])

    chirag_view = {c["id"] for c in hierarchy["chirag"].get(f"/api/team/{hierarchy['amol_tm_id']}/companies").json()}
    assert amol_company["id"] not in chirag_view

    amol_view = {c["id"] for c in hierarchy["amol"].get(f"/api/team/{hierarchy['amol_tm_id']}/companies").json()}
    assert amol_company["id"] in amol_view

    admin_view = {c["id"] for c in hierarchy["nimita"].get(f"/api/team/{hierarchy['amol_tm_id']}/companies").json()}
    assert amol_company["id"] in admin_view


# ---------------------------------------------------------------------------
# Final blocker fix: bulk-import phone-existence oracle
# ---------------------------------------------------------------------------

def test_bulk_import_admin_duplicate_detection_unrestricted(hierarchy):
    """Admins keep the original unrestricted dedup behavior."""
    hierarchy["amol"].post("/api/contacts", json={"name": "Amol Bulk Target", "phone": "9990000021"})

    resp = hierarchy["nimita"].post("/api/contacts/bulk-import", json={"contacts": [{"name": "Reimport", "phone": "9990000021"}]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["skipped_duplicate"] == 1
    assert body["created"] == 0


def test_bulk_import_cannot_detect_out_of_scope_contact_via_phone(hierarchy):
    """Chirag importing a phone number that belongs ONLY to Amol's contact must not learn Amol
    has that contact - the import creates a new row rather than silently rejecting it, since
    rejection would itself be the leak."""
    amol_contact = hierarchy["amol"].post("/api/contacts", json={"name": "Amol Only Bulk Contact", "phone": "9990000022"}).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{amol_contact['id']}/assign", hierarchy["amol_tm_id"])

    resp = hierarchy["chirag"].post("/api/contacts/bulk-import", json={"contacts": [{"name": "Chirag Import Attempt", "phone": "9990000022"}]})
    assert resp.status_code == 200
    body = resp.json()
    # No duplicate signal - Chirag gets no information that this number already exists for Amol.
    assert body["skipped_duplicate"] == 0
    assert body["created"] == 1

    # Symmetric check the other direction.
    chirag_contact = hierarchy["chirag"].post("/api/contacts", json={"name": "Chirag Only Bulk Contact", "phone": "9990000023"}).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{chirag_contact['id']}/assign", hierarchy["chirag_tm_id"])

    resp2 = hierarchy["amol"].post("/api/contacts/bulk-import", json={"contacts": [{"name": "Amol Import Attempt", "phone": "9990000023"}]})
    assert resp2.json()["skipped_duplicate"] == 0
    assert resp2.json()["created"] == 1


def test_bulk_import_accessible_duplicate_behavior_unchanged(hierarchy):
    """Chirag importing a phone belonging to his OWN visible contact still gets the normal
    duplicate-skip behavior."""
    hierarchy["chirag"].post("/api/contacts", json={"name": "Chirag Existing Bulk Contact", "phone": "9990000024"})

    resp = hierarchy["chirag"].post("/api/contacts/bulk-import", json={"contacts": [{"name": "Chirag Reimport", "phone": "9990000024"}]})
    body = resp.json()
    assert body["skipped_duplicate"] == 1
    assert body["created"] == 0


def test_bulk_import_manager_detects_reports_contacts(hierarchy):
    """Samiksha importing a number belonging to Chirag (her direct report) gets the normal
    duplicate behavior, since Chirag's records are within her visibility scope."""
    hierarchy["chirag"].post("/api/contacts", json={"name": "Chirag Manager-Visible Contact", "phone": "9990000025"})

    resp = hierarchy["samiksha"].post("/api/contacts/bulk-import", json={"contacts": [{"name": "Samiksha Reimport", "phone": "9990000025"}]})
    body = resp.json()
    assert body["skipped_duplicate"] == 1
    assert body["created"] == 0


def test_bulk_import_same_phone_accessible_and_inaccessible_leaks_nothing_extra(hierarchy):
    """Same phone number exists on both an accessible (Chirag's own) and inaccessible (Amol's)
    contact - the response must reflect only the accessible one, never expose anything about
    the inaccessible record, and must not double count."""
    hierarchy["chirag"].post("/api/contacts", json={"name": "Chirag Shared Number Contact", "phone": "9990000026"})
    amol_contact = hierarchy["amol"].post("/api/contacts", json={"name": "Amol Shared Number Contact", "phone": "9990000026"}).json()
    _assign(hierarchy["nimita"], f"/api/contacts/{amol_contact['id']}/assign", hierarchy["amol_tm_id"])

    resp = hierarchy["chirag"].post("/api/contacts/bulk-import", json={"contacts": [{"name": "Chirag Reimport Shared", "phone": "9990000026"}]})
    body = resp.json()
    assert body["skipped_duplicate"] == 1
    assert body["created"] == 0
    # The response contains no reference to Amol's contact at all.
    assert "created_contacts" in body and all(c.get("phone") != "9990000026" for c in body["created_contacts"])
