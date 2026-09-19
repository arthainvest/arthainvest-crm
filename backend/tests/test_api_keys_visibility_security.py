"""Security tests for API Keys access control.

api_keys.created_by existed since the table was first created, but no route ever read it
back for scoping - every authenticated employee could list every API key in the system
(including ones created by other employees or admins) and revoke ANY key by guessing a
small sequential integer id, with zero ownership check at all. Revoking is the real risk:
it's a destructive action that silently kills a live website-lead-intake or Zapier webhook
integration the whole business may depend on.

Locked model (creator-only visibility with manager escalation, same rule as Campaigns/
Quotations/Automations - api_keys has no assignee column, so there is nothing to scope on
beyond created_by): admins unrestricted; a manager sees/manages own + direct reports' keys;
an individual employee sees/manages only keys they created.
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
    yogesh_user_id, yogesh_token = _register_and_login(client, auth_token, "yogesh_apikey", role="admin")
    samiksha_user_id, samiksha_token = _register_and_login(client, auth_token, "samiksha_apikey")
    chirag_user_id, chirag_token = _register_and_login(client, auth_token, "chirag_apikey")
    amol_user_id, amol_token = _register_and_login(client, auth_token, "amol_apikey")

    samiksha_tm = auth_client.post("/api/team", json={"name": "Samiksha ApiKey", "role": "employee"}).json()
    chirag_tm = auth_client.post("/api/team", json={"name": "Chirag ApiKey", "role": "employee"}).json()
    amol_tm = auth_client.post("/api/team", json={"name": "Amol ApiKey", "role": "employee"}).json()

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


def _key(client, name="Test Key"):
    resp = client.post("/api/api-keys", json={"name": name})
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Visibility
# ---------------------------------------------------------------------------

def test_admin_sees_all_keys(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_key = _key(h["chirag"], "Chirag's Key")
    amol_key = _key(h["amol"], "Amol's Key")
    samiksha_key = _key(h["samiksha"], "Samiksha's Key")

    for admin in (h["nimita"], h["yogesh"]):
        ids = {k["id"] for k in admin.get("/api/api-keys").json()}
        assert chirag_key["id"] in ids
        assert amol_key["id"] in ids
        assert samiksha_key["id"] in ids


def test_manager_sees_own_and_reports_keys(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_key = _key(h["chirag"], "Chirag's Key")
    amol_key = _key(h["amol"], "Amol's Key")

    ids = {k["id"] for k in h["samiksha"].get("/api/api-keys").json()}
    assert chirag_key["id"] in ids
    assert amol_key["id"] in ids


def test_report_sees_only_own_key(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_key = _key(h["chirag"], "Chirag's Key")
    amol_key = _key(h["amol"], "Amol's Key")

    chirag_ids = {k["id"] for k in h["chirag"].get("/api/api-keys").json()}
    assert chirag_key["id"] in chirag_ids
    assert amol_key["id"] not in chirag_ids

    amol_ids = {k["id"] for k in h["amol"].get("/api/api-keys").json()}
    assert amol_key["id"] in amol_ids
    assert chirag_key["id"] not in amol_ids


def test_list_never_leaks_raw_key_or_hash_for_anyone(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    _key(h["chirag"], "Chirag's Key")

    for viewer in (h["nimita"], h["chirag"], h["samiksha"]):
        for row in viewer.get("/api/api-keys").json():
            assert "api_key" not in row
            assert "key_hash" not in row


# ---------------------------------------------------------------------------
# The revoke IDOR - the real risk, since revocation is destructive and immediate
# ---------------------------------------------------------------------------

def test_unauthorized_revoke_denied_with_no_mutation(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_key = _key(h["amol"], "Amol's Key")

    resp = h["chirag"].delete(f"/api/api-keys/{amol_key['id']}")
    assert resp.status_code == 403

    still_active = next(k for k in h["amol"].get("/api/api-keys").json() if k["id"] == amol_key["id"])
    assert still_active["revoked_at"] is None


def test_authorized_revoke_succeeds(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_key = _key(h["chirag"], "Chirag's Key")

    resp = h["chirag"].delete(f"/api/api-keys/{chirag_key['id']}")
    assert resp.status_code == 200

    revoked = next(k for k in h["chirag"].get("/api/api-keys").json() if k["id"] == chirag_key["id"])
    assert revoked["revoked_at"] is not None


def test_manager_can_revoke_reports_key(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    amol_key = _key(h["amol"], "Amol's Key")

    resp = h["samiksha"].delete(f"/api/api-keys/{amol_key['id']}")
    assert resp.status_code == 200

    revoked = next(k for k in h["nimita"].get("/api/api-keys").json() if k["id"] == amol_key["id"])
    assert revoked["revoked_at"] is not None


def test_report_cannot_revoke_managers_own_key(client, auth_client, auth_token):
    """The reverse direction - a report must not be able to reach upward either."""
    h = hierarchy(client, auth_client, auth_token)
    samiksha_key = _key(h["samiksha"], "Samiksha's Key")

    resp = h["chirag"].delete(f"/api/api-keys/{samiksha_key['id']}")
    assert resp.status_code == 403


def test_peer_cannot_revoke_peers_key(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_key = _key(h["chirag"], "Chirag's Key")

    resp = h["amol"].delete(f"/api/api-keys/{chirag_key['id']}")
    assert resp.status_code == 403


def test_revoke_nonexistent_key_404s_for_everyone(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    resp = h["chirag"].delete("/api/api-keys/999999999")
    assert resp.status_code == 404


def test_admin_can_revoke_any_key(client, auth_client, auth_token):
    h = hierarchy(client, auth_client, auth_token)
    chirag_key = _key(h["chirag"], "Chirag's Key")

    resp = h["nimita"].delete(f"/api/api-keys/{chirag_key['id']}")
    assert resp.status_code == 200
