def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_login_success(client):
    resp = client.post("/api/auth/login", json={"username": "testuser", "password": "12345"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testuser"
    assert data["access_token"]
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    resp = client.post("/api/auth/login", json={"username": "testuser", "password": "wrong"})
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    resp = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
    assert resp.status_code == 401


def test_protected_endpoint_without_token_is_rejected(client):
    resp = client.get("/api/leads")
    assert resp.status_code == 401


def test_protected_endpoint_with_invalid_token_is_rejected(client):
    resp = client.get("/api/leads?token=not-a-real-token")
    assert resp.status_code == 401


def test_register_requires_admin_token(client):
    """Registration used to be wide open - anyone who found the URL could create their own
    account with role='admin'. Now it's gated the same as team-roster management."""
    resp = client.post("/api/auth/register", json={
        "username": "walkin", "email": "walkin@example.com", "password": "walkin123",
        "full_name": "Walk In", "role": "employee"
    })
    assert resp.status_code == 401


def test_register_rejects_non_admin_token(auth_client, client):
    # Bootstrap a non-admin account the only way now possible - via an admin.
    auth_client.post("/api/auth/register", json={
        "username": "plainer", "email": "plainer@example.com", "password": "plainer123",
        "full_name": "Plainer", "role": "employee"
    })
    plain_token = client.post("/api/auth/login", json={
        "username": "plainer", "password": "plainer123"
    }).json()["access_token"]

    resp = client.post(f"/api/auth/register?token={plain_token}", json={
        "username": "shouldnotexist", "email": "shouldnotexist@example.com",
        "password": "whatever12", "full_name": "Should Not Exist", "role": "employee"
    })
    assert resp.status_code == 403


def test_admin_can_register_new_user(auth_client, client):
    resp = auth_client.post("/api/auth/register", json={
        "username": "newhire", "email": "newhire@example.com", "password": "newhire123",
        "full_name": "New Hire", "role": "employee"
    })
    assert resp.status_code == 200
    assert resp.json()["username"] == "newhire"

    assert client.post("/api/auth/login", json={"username": "newhire", "password": "newhire123"}).status_code == 200


def test_change_password_success(auth_client, client):
    resp = auth_client.put("/api/auth/change-password", json={
        "old_password": "12345", "new_password": "newpass1"
    })
    assert resp.status_code == 200

    # Old password no longer works, new one does.
    assert client.post("/api/auth/login", json={"username": "testuser", "password": "12345"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "testuser", "password": "newpass1"}).status_code == 200


def test_change_password_wrong_old_password_rejected(auth_client):
    resp = auth_client.put("/api/auth/change-password", json={
        "old_password": "wrong", "new_password": "newpass1"
    })
    assert resp.status_code == 401


def test_change_password_requires_auth(client):
    resp = client.put("/api/auth/change-password", json={
        "old_password": "12345", "new_password": "newpass1"
    })
    assert resp.status_code == 401


def test_admin_reset_password_success(auth_client, client):
    auth_client.post("/api/auth/register", json={
        "username": "junior", "email": "junior@example.com", "password": "orig1234",
        "full_name": "Junior", "role": "employee"
    })

    resp = auth_client.put("/api/auth/admin-reset-password", json={
        "username": "junior", "new_password": "reset5678"
    })
    assert resp.status_code == 200

    assert client.post("/api/auth/login", json={"username": "junior", "password": "orig1234"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "junior", "password": "reset5678"}).status_code == 200


def test_admin_reset_password_unknown_user(auth_client):
    resp = auth_client.put("/api/auth/admin-reset-password", json={
        "username": "nobody", "new_password": "reset5678"
    })
    assert resp.status_code == 404


def test_admin_reset_password_requires_admin(client, auth_client):
    auth_client.post("/api/auth/register", json={
        "username": "plainuser", "email": "plain@example.com", "password": "plainpass1",
        "full_name": "Plain User", "role": "employee"
    })
    plain_token = client.post("/api/auth/login", json={
        "username": "plainuser", "password": "plainpass1"
    }).json()["access_token"]

    resp = client.put(f"/api/auth/admin-reset-password?token={plain_token}", json={
        "username": "testuser", "new_password": "hijacked1"
    })
    assert resp.status_code == 403
