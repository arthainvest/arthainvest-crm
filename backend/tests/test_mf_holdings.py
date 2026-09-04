def _make_contact(auth_client, name="MF Test Client"):
    resp = auth_client.post("/api/contacts", json={"name": name, "phone": "9876500000"})
    return resp.json()["id"]


def test_mf_holdings_require_auth(client):
    resp = client.get("/api/mf-holdings")
    assert resp.status_code == 401


def test_create_and_list_mf_holding(auth_client):
    contact_id = _make_contact(auth_client)

    resp = auth_client.post("/api/mf-holdings", json={
        "contact_id": contact_id, "fund_name": "Parag Parikh Flexi Cap",
        "fund_category": "Equity", "investment_type": "SIP", "amount": 5000,
        "next_due_date": "2026-10-01", "goal": "Retirement"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["fund_name"] == "Parag Parikh Flexi Cap"
    assert data["contact_name"] == "MF Test Client"
    assert data["status"] == "Active"

    resp = auth_client.get("/api/mf-holdings")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_mf_holdings_filter_by_contact_and_status(auth_client):
    c1 = _make_contact(auth_client, "Client One")
    c2 = _make_contact(auth_client, "Client Two")

    auth_client.post("/api/mf-holdings", json={"contact_id": c1, "fund_name": "Fund A", "status": "Active"})
    auth_client.post("/api/mf-holdings", json={"contact_id": c1, "fund_name": "Fund B", "status": "Stopped"})
    auth_client.post("/api/mf-holdings", json={"contact_id": c2, "fund_name": "Fund C", "status": "Active"})

    resp = auth_client.get(f"/api/mf-holdings?contact_id={c1}")
    assert len(resp.json()) == 2

    resp = auth_client.get("/api/mf-holdings?status=Active")
    funds = {r["fund_name"] for r in resp.json()}
    assert funds == {"Fund A", "Fund C"}


def test_mf_holdings_due_soon(auth_client):
    contact_id = _make_contact(auth_client)

    auth_client.post("/api/mf-holdings", json={
        "contact_id": contact_id, "fund_name": "Overdue Fund",
        "status": "Active", "next_due_date": "2020-01-01"
    })
    auth_client.post("/api/mf-holdings", json={
        "contact_id": contact_id, "fund_name": "Far Future Fund",
        "status": "Active", "next_due_date": "2099-01-01"
    })
    auth_client.post("/api/mf-holdings", json={
        "contact_id": contact_id, "fund_name": "Stopped Fund",
        "status": "Stopped", "next_due_date": "2020-01-01"
    })

    resp = auth_client.get("/api/mf-holdings/due-soon")
    assert resp.status_code == 200
    names = {r["fund_name"] for r in resp.json()}
    assert names == {"Overdue Fund"}


def test_update_mf_holding(auth_client):
    contact_id = _make_contact(auth_client)
    created = auth_client.post("/api/mf-holdings", json={
        "contact_id": contact_id, "fund_name": "Original Fund", "amount": 1000
    }).json()

    resp = auth_client.put(f"/api/mf-holdings/{created['id']}", json={"amount": 2000, "status": "Paused"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["amount"] == 2000
    assert data["status"] == "Paused"
    assert data["fund_name"] == "Original Fund"  # untouched field preserved


def test_update_unknown_mf_holding_404s(auth_client):
    resp = auth_client.put("/api/mf-holdings/999999", json={"amount": 1})
    assert resp.status_code == 404


def test_update_mf_holding_with_no_fields_400s(auth_client):
    contact_id = _make_contact(auth_client)
    created = auth_client.post("/api/mf-holdings", json={
        "contact_id": contact_id, "fund_name": "Fund"
    }).json()

    resp = auth_client.put(f"/api/mf-holdings/{created['id']}", json={})
    assert resp.status_code == 400


def test_delete_mf_holding(auth_client):
    contact_id = _make_contact(auth_client)
    created = auth_client.post("/api/mf-holdings", json={
        "contact_id": contact_id, "fund_name": "To Delete"
    }).json()

    resp = auth_client.delete(f"/api/mf-holdings/{created['id']}")
    assert resp.status_code == 200

    resp = auth_client.get("/api/mf-holdings")
    assert resp.json() == []


def test_delete_unknown_mf_holding_404s(auth_client):
    resp = auth_client.delete("/api/mf-holdings/999999")
    assert resp.status_code == 404
