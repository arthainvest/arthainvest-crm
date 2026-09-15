"""Google OAuth genuinely can't be exercised end to end without a real Google Cloud project
and a real user consenting in a browser - unlike WhatsApp's webhook (which we could
independently re-implement the client side of) there's no way to "be Google" for a real HTTP
round trip. So this mirrors the established pattern in test_graceful_degradation.py /
test_kylas_parity.py: monkeypatch the env vars, patch requests.post/get/put at the point of
use, and assert on what the endpoint actually did with a fake-but-realistic response shape -
plus real, unmocked assertions on what landed in the database (token storage, lead creation),
since that part genuinely is this codebase's own logic and needs no external service to test.
"""
from unittest.mock import patch, MagicMock

import pytest


def test_connect_returns_not_configured_without_credentials(auth_client):
    resp = auth_client.get("/api/integrations/google/connect")
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_connect_builds_auth_url_when_configured(auth_client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "fake-client-id")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/integrations/google/callback")

    resp = auth_client.get("/api/integrations/google/connect")
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    assert "accounts.google.com" in data["auth_url"]
    assert "access_type=offline" in data["auth_url"]
    assert "prompt=consent" in data["auth_url"]


def test_status_shows_not_connected_before_oauth(auth_client):
    resp = auth_client.get("/api/integrations/google/status")
    assert resp.status_code == 200
    assert resp.json()["connected"] is False


def test_callback_stores_tokens_and_status_reflects_connection(auth_client, client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "fake-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "fake-client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/integrations/google/callback")

    # auth_client's token identifies the CRM user the callback should attach the Google
    # tokens to - grab it the same way the connect endpoint would put it in `state`.
    crm_token = auth_client._token

    fake_token_response = MagicMock()
    fake_token_response.json.return_value = {
        "access_token": "fake-google-access-token",
        "refresh_token": "fake-google-refresh-token",
        "expires_in": 3600,
    }
    fake_token_response.raise_for_status = MagicMock()

    fake_userinfo_response = MagicMock()
    fake_userinfo_response.json.return_value = {"email": "advisor@example.com"}
    fake_userinfo_response.raise_for_status = MagicMock()

    with patch("requests.post", return_value=fake_token_response), \
         patch("requests.get", return_value=fake_userinfo_response):
        resp = client.get(
            "/api/integrations/google/callback",
            params={"code": "fake-auth-code", "state": crm_token},
            follow_redirects=False
        )

    assert resp.status_code in (302, 307)
    assert "google=connected" in resp.headers["location"]

    status = auth_client.get("/api/integrations/google/status").json()
    assert status["connected"] is True
    assert status["google_email"] == "advisor@example.com"


def test_callback_without_refresh_token_fails_cleanly(auth_client, client, monkeypatch):
    """A response missing refresh_token (e.g. Google decided the grant was already fresh)
    must not silently store a token that'll stop working in an hour."""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "fake-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "fake-client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/integrations/google/callback")

    fake_token_response = MagicMock()
    fake_token_response.json.return_value = {"access_token": "fake-access-token", "expires_in": 3600}
    fake_token_response.raise_for_status = MagicMock()

    with patch("requests.post", return_value=fake_token_response):
        resp = client.get(
            "/api/integrations/google/callback",
            params={"code": "fake-auth-code", "state": auth_client._token},
            follow_redirects=False
        )

    assert "google=error" in resp.headers["location"]
    status = auth_client.get("/api/integrations/google/status").json()
    assert status["connected"] is False


def test_callback_with_denied_error_redirects_cleanly(client):
    resp = client.get(
        "/api/integrations/google/callback",
        params={"error": "access_denied", "state": "irrelevant"},
        follow_redirects=False
    )
    assert "google=error" in resp.headers["location"]


def test_disconnect_removes_stored_tokens(auth_client, client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "fake-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "fake-client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/integrations/google/callback")

    fake_token_response = MagicMock()
    fake_token_response.json.return_value = {"access_token": "a", "refresh_token": "r", "expires_in": 3600}
    fake_token_response.raise_for_status = MagicMock()
    fake_userinfo_response = MagicMock()
    fake_userinfo_response.json.return_value = {"email": "advisor@example.com"}
    fake_userinfo_response.raise_for_status = MagicMock()

    with patch("requests.post", return_value=fake_token_response), \
         patch("requests.get", return_value=fake_userinfo_response):
        client.get("/api/integrations/google/callback", params={"code": "c", "state": auth_client._token}, follow_redirects=False)

    assert auth_client.get("/api/integrations/google/status").json()["connected"] is True

    resp = auth_client.post("/api/integrations/google/disconnect")
    assert resp.status_code == 200
    assert auth_client.get("/api/integrations/google/status").json()["connected"] is False


def test_export_returns_not_configured_when_not_connected(auth_client):
    resp = auth_client.post("/api/integrations/google-sheets/export", json={
        "spreadsheet_id": "fake-sheet-id", "entity": "contacts"
    })
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_export_rejects_invalid_entity(auth_client):
    resp = auth_client.post("/api/integrations/google-sheets/export", json={
        "spreadsheet_id": "fake-sheet-id", "entity": "deals"
    })
    assert resp.status_code == 400


def _connect_fake_google_account(auth_client, client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "fake-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "fake-client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/integrations/google/callback")
    fake_token_response = MagicMock()
    fake_token_response.json.return_value = {"access_token": "a", "refresh_token": "r", "expires_in": 3600}
    fake_token_response.raise_for_status = MagicMock()
    fake_userinfo_response = MagicMock()
    fake_userinfo_response.json.return_value = {"email": "advisor@example.com"}
    fake_userinfo_response.raise_for_status = MagicMock()
    with patch("requests.post", return_value=fake_token_response), \
         patch("requests.get", return_value=fake_userinfo_response):
        client.get("/api/integrations/google/callback", params={"code": "c", "state": auth_client._token}, follow_redirects=False)


def test_export_contacts_writes_expected_headers_and_rows(auth_client, client, monkeypatch):
    _connect_fake_google_account(auth_client, client, monkeypatch)
    contact = auth_client.post("/api/contacts", json={
        "name": "Sheet Export Contact", "email": "export@example.com", "phone": "9998887777", "status": "Active"
    }).json()

    fake_put_response = MagicMock()
    fake_put_response.status_code = 200
    captured = {}

    def fake_put(url, headers=None, params=None, json=None, timeout=None):
        captured['url'] = url
        captured['body'] = json
        return fake_put_response

    with patch("requests.put", side_effect=fake_put):
        resp = auth_client.post("/api/integrations/google-sheets/export", json={
            "spreadsheet_id": "fake-sheet-id", "sheet_name": "Sheet1", "entity": "contacts"
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    assert data["rows_written"] >= 1
    assert "fake-sheet-id" in captured['url']
    assert captured['body']['values'][0] == ['Name', 'Company', 'Email', 'Phone', 'City/Area', 'Score', 'Amount', 'Bank', 'Status', 'Renewal Date', 'Employee']
    exported_names = [row[0] for row in captured['body']['values'][1:]]
    assert "Sheet Export Contact" in exported_names


def test_export_leads_writes_expected_headers(auth_client, client, monkeypatch):
    _connect_fake_google_account(auth_client, client, monkeypatch)

    fake_put_response = MagicMock()
    fake_put_response.status_code = 200
    captured = {}

    def fake_put(url, headers=None, params=None, json=None, timeout=None):
        captured['body'] = json
        return fake_put_response

    with patch("requests.put", side_effect=fake_put):
        resp = auth_client.post("/api/integrations/google-sheets/export", json={
            "spreadsheet_id": "fake-sheet-id", "entity": "leads"
        })

    assert resp.status_code == 200
    assert captured['body']['values'][0] == ['Name', 'Company', 'Email', 'Phone', 'Status', 'Score', 'Employee']


def test_import_returns_not_configured_when_not_connected(auth_client):
    resp = auth_client.post("/api/integrations/google-sheets/import", json={"spreadsheet_id": "fake-sheet-id"})
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_import_creates_leads_from_sheet_rows(auth_client, client, monkeypatch):
    _connect_fake_google_account(auth_client, client, monkeypatch)

    fake_get_response = MagicMock()
    fake_get_response.status_code = 200
    fake_get_response.json.return_value = {
        "values": [
            ["Name", "Company", "Email", "Phone", "Product", "Source"],
            ["Sheet Lead One", "Acme Corp", "one@example.com", "9991112222", "Home Loan", ""],
            ["Sheet Lead Two", "", "two@example.com", "9993334444", "", "Referral"],
            ["", "Skip Me Co", "noname@example.com", "9995556666", "", ""],
        ]
    }

    with patch("requests.get", return_value=fake_get_response):
        resp = auth_client.post("/api/integrations/google-sheets/import", json={"spreadsheet_id": "fake-sheet-id"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    assert data["created"] == 2
    assert data["failed"] == 1

    leads = auth_client.get("/api/leads").json()
    names = [l["name"] for l in leads]
    assert "Sheet Lead One" in names
    assert "Sheet Lead Two" in names
    lead_two = next(l for l in leads if l["name"] == "Sheet Lead Two")
    assert lead_two["source"] == "Referral"
    lead_one = next(l for l in leads if l["name"] == "Sheet Lead One")
    assert lead_one["source"] == "Google Sheets"  # defaulted when the sheet left Source blank


def test_import_empty_sheet_reports_no_rows(auth_client, client, monkeypatch):
    _connect_fake_google_account(auth_client, client, monkeypatch)
    fake_get_response = MagicMock()
    fake_get_response.status_code = 200
    fake_get_response.json.return_value = {"values": [["Name", "Company"]]}

    with patch("requests.get", return_value=fake_get_response):
        resp = auth_client.post("/api/integrations/google-sheets/import", json={"spreadsheet_id": "fake-sheet-id"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] == 0


# ---------------------------------------------------------------------------
# Security fix: export must respect the caller's Contact/Lead visibility scope,
# not dump the whole table just because the destination is external.
# ---------------------------------------------------------------------------

def _register_and_login(client, admin_token, username, role="employee"):
    resp = client.post(
        f"/api/auth/register?token={admin_token}",
        json={"username": username, "email": f"{username}@example.com",
              "password": "pass12345", "full_name": username, "role": role},
    )
    assert resp.status_code == 200, resp.text
    user_id = resp.json()["id"]
    login = client.post("/api/auth/login", json={"username": username, "password": "pass12345"})
    assert login.status_code == 200
    return user_id, login.json()["access_token"]


class _TokenedClient:
    def __init__(self, client, token):
        self._c = client
        self._token = token

    def _url(self, path):
        sep = '&' if '?' in path else '?'
        return f"{path}{sep}token={self._token}"

    def get(self, path, **kw):
        return self._c.get(self._url(path), **kw)

    def post(self, path, **kw):
        return self._c.post(self._url(path), **kw)

    def put(self, path, **kw):
        return self._c.put(self._url(path), **kw)


def _connect_fake_google_account_as(export_client, client, monkeypatch):
    """Same as _connect_fake_google_account, but for an arbitrary employee's client rather
    than always the seeded admin, so a non-admin can have their own Google connection."""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "fake-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "fake-client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/integrations/google/callback")
    fake_token_response = MagicMock()
    fake_token_response.json.return_value = {"access_token": "a", "refresh_token": "r", "expires_in": 3600}
    fake_token_response.raise_for_status = MagicMock()
    fake_userinfo_response = MagicMock()
    fake_userinfo_response.json.return_value = {"email": f"{export_client._token[:8]}@example.com"}
    fake_userinfo_response.raise_for_status = MagicMock()
    with patch("requests.post", return_value=fake_token_response), \
         patch("requests.get", return_value=fake_userinfo_response):
        client.get("/api/integrations/google/callback", params={"code": "c", "state": export_client._token}, follow_redirects=False)


def _export(export_client, entity, client, monkeypatch):
    """Runs the export with requests.put mocked, returns (response_json, captured_rows)."""
    _connect_fake_google_account_as(export_client, client, monkeypatch)
    fake_put_response = MagicMock()
    fake_put_response.status_code = 200
    captured = {}

    def fake_put(url, headers=None, params=None, json=None, timeout=None):
        captured['body'] = json
        return fake_put_response

    with patch("requests.put", side_effect=fake_put):
        resp = export_client.post("/api/integrations/google-sheets/export", json={
            "spreadsheet_id": "fake-sheet-id", "sheet_name": "Sheet1", "entity": entity
        })
    return resp.json(), captured.get('body', {}).get('values', [])


@pytest.fixture()
def export_hierarchy(client, auth_client, auth_token):
    """A manager (Samiksha-equivalent) with two direct reports (Chirag/Amol-equivalent),
    mirroring the reporting structure the core access-control feature was built and tested
    against, but self-contained in this file rather than importing the other test module's
    fixture."""
    samiksha_uid, samiksha_token = _register_and_login(client, auth_token, "samiksha_sheets")
    chirag_uid, chirag_token = _register_and_login(client, auth_token, "chirag_sheets")
    amol_uid, amol_token = _register_and_login(client, auth_token, "amol_sheets")

    samiksha_tm = auth_client.post("/api/team", json={"name": "Samiksha Sheets", "role": "employee"}).json()
    chirag_tm = auth_client.post("/api/team", json={"name": "Chirag Sheets", "role": "employee"}).json()
    amol_tm = auth_client.post("/api/team", json={"name": "Amol Sheets", "role": "employee"}).json()
    auth_client.put(f"/api/team/{samiksha_tm['id']}", json={"user_id": samiksha_uid})
    auth_client.put(f"/api/team/{chirag_tm['id']}", json={"user_id": chirag_uid, "reports_to": samiksha_tm['id']})
    auth_client.put(f"/api/team/{amol_tm['id']}", json={"user_id": amol_uid, "reports_to": samiksha_tm['id']})

    return {
        "admin": auth_client,
        "samiksha": _TokenedClient(client, samiksha_token), "samiksha_tm_id": samiksha_tm['id'],
        "chirag": _TokenedClient(client, chirag_token), "chirag_tm_id": chirag_tm['id'],
        "amol": _TokenedClient(client, amol_token), "amol_tm_id": amol_tm['id'],
    }


def test_export_admin_contacts_unrestricted(export_hierarchy, client, monkeypatch):
    """A. Admin Contact export - all permitted (i.e. all) Contacts exported."""
    h = export_hierarchy
    chirag_contact = h["chirag"].post("/api/contacts", json={"name": "Chirag Export Contact", "phone": "9990000030"}).json()
    h["admin"].put(f"/api/contacts/{chirag_contact['id']}/assign", json={"team_member_id": h["chirag_tm_id"]})
    amol_contact = h["amol"].post("/api/contacts", json={"name": "Amol Export Contact", "phone": "9990000031"}).json()
    h["admin"].put(f"/api/contacts/{amol_contact['id']}/assign", json={"team_member_id": h["amol_tm_id"]})

    body, rows = _export(h["admin"], "contacts", client, monkeypatch)
    assert body["configured"] is True
    names = [r[0] for r in rows[1:]]
    assert "Chirag Export Contact" in names
    assert "Amol Export Contact" in names


def test_export_non_admin_contacts_scoped_to_own_visibility(export_hierarchy, client, monkeypatch):
    """B, E. Non-admin Contact export contains only visible Contacts - Chirag cannot export
    Amol's Contacts, and vice versa."""
    h = export_hierarchy
    chirag_contact = h["chirag"].post("/api/contacts", json={"name": "Chirag Only Export", "phone": "9990000032"}).json()
    h["admin"].put(f"/api/contacts/{chirag_contact['id']}/assign", json={"team_member_id": h["chirag_tm_id"]})
    amol_contact = h["amol"].post("/api/contacts", json={"name": "Amol Only Export", "phone": "9990000033"}).json()
    h["admin"].put(f"/api/contacts/{amol_contact['id']}/assign", json={"team_member_id": h["amol_tm_id"]})

    body, rows = _export(h["chirag"], "contacts", client, monkeypatch)
    names = [r[0] for r in rows[1:]]
    assert "Chirag Only Export" in names
    assert "Amol Only Export" not in names
    # No trace of Amol's data anywhere in the response, including row count/metadata.
    assert body["rows_written"] == len(rows) - 1

    body2, rows2 = _export(h["amol"], "contacts", client, monkeypatch)
    names2 = [r[0] for r in rows2[1:]]
    assert "Amol Only Export" in names2
    assert "Chirag Only Export" not in names2


def test_export_manager_sees_reports_contacts(export_hierarchy, client, monkeypatch):
    """F. Samiksha (manager) exports her own permitted Contacts, including her direct
    reports' - Chirag's and Amol's."""
    h = export_hierarchy
    chirag_contact = h["chirag"].post("/api/contacts", json={"name": "Chirag Manager-Visible", "phone": "9990000034"}).json()
    h["admin"].put(f"/api/contacts/{chirag_contact['id']}/assign", json={"team_member_id": h["chirag_tm_id"]})

    body, rows = _export(h["samiksha"], "contacts", client, monkeypatch)
    names = [r[0] for r in rows[1:]]
    assert "Chirag Manager-Visible" in names


def test_export_admin_leads_unrestricted(export_hierarchy, client, monkeypatch):
    """C. Admin Lead export - all permitted Leads exported."""
    h = export_hierarchy
    chirag_lead = h["chirag"].post("/api/leads", json={"name": "Chirag Export Lead", "phone": "9990000035"}).json()
    h["admin"].put(f"/api/leads/{chirag_lead['id']}/assign", json={"team_member_id": h["chirag_tm_id"]})

    body, rows = _export(h["admin"], "leads", client, monkeypatch)
    names = [r[0] for r in rows[1:]]
    assert "Chirag Export Lead" in names


def test_export_non_admin_leads_scoped_to_own_visibility(export_hierarchy, client, monkeypatch):
    """D, E. Non-admin Lead export contains only visible Leads - peer isolation holds for
    Leads too, not just Contacts."""
    h = export_hierarchy
    chirag_lead = h["chirag"].post("/api/leads", json={"name": "Chirag Only Lead Export", "phone": "9990000036"}).json()
    h["admin"].put(f"/api/leads/{chirag_lead['id']}/assign", json={"team_member_id": h["chirag_tm_id"]})
    amol_lead = h["amol"].post("/api/leads", json={"name": "Amol Only Lead Export", "phone": "9990000037"}).json()
    h["admin"].put(f"/api/leads/{amol_lead['id']}/assign", json={"team_member_id": h["amol_tm_id"]})

    body, rows = _export(h["chirag"], "leads", client, monkeypatch)
    names = [r[0] for r in rows[1:]]
    assert "Chirag Only Lead Export" in names
    assert "Amol Only Lead Export" not in names


def test_export_no_hidden_record_leakage_in_response_metadata(export_hierarchy, client, monkeypatch):
    """G, H. The export response itself (row count, message text) must not disclose that
    inaccessible records exist - it should read exactly as if the invisible records simply
    aren't in the database at all, from Chirag's point of view."""
    h = export_hierarchy
    amol_contact = h["amol"].post("/api/contacts", json={"name": "Amol Hidden From Metadata", "phone": "9990000038"}).json()
    h["admin"].put(f"/api/contacts/{amol_contact['id']}/assign", json={"team_member_id": h["amol_tm_id"]})

    body, rows = _export(h["chirag"], "contacts", client, monkeypatch)
    assert "Amol" not in body["message"]
    assert str(amol_contact["id"]) not in body["message"]
    assert body["rows_written"] == len(rows) - 1  # header row excluded, count matches only what Chirag can see
