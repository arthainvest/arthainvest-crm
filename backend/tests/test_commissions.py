import pytest


@pytest.fixture()
def nimita_client(client, auth_client):
    """A TestClient pre-configured with a token for a freshly-registered 'nimita' admin
    account - the one account the commission ledger is restricted to."""
    auth_client.post("/api/auth/register", json={
        "username": "nimita", "email": "nimita@example.com", "password": "nimita1234",
        "full_name": "Nimita", "role": "admin"
    })
    token = client.post("/api/auth/login", json={
        "username": "nimita", "password": "nimita1234"
    }).json()["access_token"]

    class _NimitaClient:
        def __init__(self, c, tok):
            self._c, self._tok = c, tok

        def _url(self, path):
            sep = '&' if '?' in path else '?'
            return f"{path}{sep}token={self._tok}"

        def get(self, path, **kw):
            return self._c.get(self._url(path), **kw)

        def post(self, path, **kw):
            return self._c.post(self._url(path), **kw)

        def delete(self, path, **kw):
            return self._c.delete(self._url(path), **kw)

    return _NimitaClient(client, token)


def test_commissions_require_nimita_not_just_admin(auth_client):
    """testuser is admin but not nimita - the whole ledger is off-limits."""
    resp = auth_client.get("/api/commissions")
    assert resp.status_code == 403

    resp = auth_client.post("/api/commissions", json={
        "product_type": "mutual_fund", "description": "SIP trail", "amount": 500,
        "received_date": "2026-09-01"
    })
    assert resp.status_code == 403


def test_commissions_require_auth(client):
    resp = client.get("/api/commissions")
    assert resp.status_code == 401


def test_nimita_can_create_and_list_commission_records(nimita_client):
    resp = nimita_client.post("/api/commissions", json={
        "product_type": "insurance", "description": "Health policy renewal commission",
        "amount": 3500, "received_date": "2026-09-02", "notes": "Niva Bupa"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_type"] == "insurance"
    assert data["amount"] == 3500

    resp = nimita_client.get("/api/commissions")
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) == 1
    assert records[0]["description"] == "Health policy renewal commission"


def test_commission_list_filters_by_product_type(nimita_client):
    nimita_client.post("/api/commissions", json={
        "product_type": "loan", "description": "LAP payout", "amount": 15000, "received_date": "2026-09-01"
    })
    nimita_client.post("/api/commissions", json={
        "product_type": "mutual_fund", "description": "SIP trail", "amount": 400, "received_date": "2026-09-01"
    })

    resp = nimita_client.get("/api/commissions?product_type=loan")
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) == 1
    assert records[0]["product_type"] == "loan"


def test_create_commission_rejects_invalid_product_type(nimita_client):
    resp = nimita_client.post("/api/commissions", json={
        "product_type": "crypto", "description": "Not a real product", "amount": 100, "received_date": "2026-09-01"
    })
    assert resp.status_code == 400


def test_commission_summary_groups_by_product_type(nimita_client):
    nimita_client.post("/api/commissions", json={
        "product_type": "loan", "description": "LAP payout", "amount": 15000, "received_date": "2026-09-01"
    })
    nimita_client.post("/api/commissions", json={
        "product_type": "loan", "description": "Business loan payout", "amount": 8000, "received_date": "2026-09-02"
    })
    nimita_client.post("/api/commissions", json={
        "product_type": "mutual_fund", "description": "SIP trail", "amount": 400, "received_date": "2026-09-01"
    })

    resp = nimita_client.get("/api/commissions/summary")
    assert resp.status_code == 200
    rows = {r["product_type"]: r for r in resp.json()}
    assert rows["loan"]["total_amount"] == 23000
    assert rows["loan"]["record_count"] == 2
    assert rows["mutual_fund"]["total_amount"] == 400


def test_commission_summary_respects_date_range(nimita_client):
    nimita_client.post("/api/commissions", json={
        "product_type": "insurance", "description": "August commission", "amount": 1000, "received_date": "2026-08-15"
    })
    nimita_client.post("/api/commissions", json={
        "product_type": "insurance", "description": "September commission", "amount": 2000, "received_date": "2026-09-15"
    })

    resp = nimita_client.get("/api/commissions/summary?start_date=2026-09-01&end_date=2026-09-30")
    assert resp.status_code == 200
    rows = {r["product_type"]: r for r in resp.json()}
    assert rows["insurance"]["total_amount"] == 2000


def test_nimita_can_delete_commission_record(nimita_client):
    created = nimita_client.post("/api/commissions", json={
        "product_type": "loan", "description": "To be deleted", "amount": 500, "received_date": "2026-09-01"
    }).json()

    resp = nimita_client.delete(f"/api/commissions/{created['id']}")
    assert resp.status_code == 200

    resp = nimita_client.get("/api/commissions")
    assert resp.json() == []


def test_delete_unknown_commission_record_404s(nimita_client):
    resp = nimita_client.delete("/api/commissions/999999")
    assert resp.status_code == 404
