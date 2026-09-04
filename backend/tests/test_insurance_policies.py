def _make_contact(auth_client, name="Insurance Test Client"):
    resp = auth_client.post("/api/contacts", json={"name": name, "phone": "9876500001"})
    return resp.json()["id"]


def test_insurance_policies_require_auth(client):
    resp = client.get("/api/insurance-policies")
    assert resp.status_code == 401


def test_create_and_list_insurance_policy(auth_client):
    contact_id = _make_contact(auth_client)

    resp = auth_client.post("/api/insurance-policies", json={
        "contact_id": contact_id, "policy_type": "Health", "insurer": "Niva Bupa",
        "sum_assured": 500000, "premium_amount": 12000, "renewal_date": "2026-12-01"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["insurer"] == "Niva Bupa"
    assert data["contact_name"] == "Insurance Test Client"
    assert data["status"] == "Active"

    resp = auth_client.get("/api/insurance-policies")
    assert len(resp.json()) == 1


def test_client_can_hold_multiple_policy_types(auth_client):
    """The whole point of a dedicated table - one client, several policies."""
    contact_id = _make_contact(auth_client)

    auth_client.post("/api/insurance-policies", json={"contact_id": contact_id, "policy_type": "Health", "insurer": "Niva Bupa"})
    auth_client.post("/api/insurance-policies", json={"contact_id": contact_id, "policy_type": "Life", "insurer": "TATA AIG"})
    auth_client.post("/api/insurance-policies", json={"contact_id": contact_id, "policy_type": "Motor", "insurer": "TATA AIG"})

    resp = auth_client.get(f"/api/insurance-policies?contact_id={contact_id}")
    types = {r["policy_type"] for r in resp.json()}
    assert types == {"Health", "Life", "Motor"}


def test_insurance_policies_filter_by_status(auth_client):
    contact_id = _make_contact(auth_client)

    auth_client.post("/api/insurance-policies", json={"contact_id": contact_id, "policy_type": "Health", "status": "Active"})
    auth_client.post("/api/insurance-policies", json={"contact_id": contact_id, "policy_type": "Life", "status": "Lapsed"})

    resp = auth_client.get("/api/insurance-policies?status=Lapsed")
    policies = resp.json()
    assert len(policies) == 1
    assert policies[0]["policy_type"] == "Life"


def test_insurance_policies_due_soon(auth_client):
    contact_id = _make_contact(auth_client)

    auth_client.post("/api/insurance-policies", json={
        "contact_id": contact_id, "policy_type": "Health", "status": "Active", "renewal_date": "2020-01-01"
    })
    auth_client.post("/api/insurance-policies", json={
        "contact_id": contact_id, "policy_type": "Life", "status": "Active", "renewal_date": "2099-01-01"
    })
    auth_client.post("/api/insurance-policies", json={
        "contact_id": contact_id, "policy_type": "Motor", "status": "Lapsed", "renewal_date": "2020-01-01"
    })

    resp = auth_client.get("/api/insurance-policies/due-soon")
    assert resp.status_code == 200
    types = {r["policy_type"] for r in resp.json()}
    assert types == {"Health"}


def test_update_insurance_policy(auth_client):
    contact_id = _make_contact(auth_client)
    created = auth_client.post("/api/insurance-policies", json={
        "contact_id": contact_id, "policy_type": "Health", "premium_amount": 10000
    }).json()

    resp = auth_client.put(f"/api/insurance-policies/{created['id']}", json={"status": "Renewed", "premium_amount": 11000})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Renewed"
    assert data["premium_amount"] == 11000
    assert data["policy_type"] == "Health"  # untouched field preserved


def test_update_unknown_insurance_policy_404s(auth_client):
    resp = auth_client.put("/api/insurance-policies/999999", json={"status": "Lapsed"})
    assert resp.status_code == 404


def test_delete_insurance_policy(auth_client):
    contact_id = _make_contact(auth_client)
    created = auth_client.post("/api/insurance-policies", json={
        "contact_id": contact_id, "policy_type": "Health"
    }).json()

    resp = auth_client.delete(f"/api/insurance-policies/{created['id']}")
    assert resp.status_code == 200

    resp = auth_client.get("/api/insurance-policies")
    assert resp.json() == []


def test_delete_unknown_insurance_policy_404s(auth_client):
    resp = auth_client.delete("/api/insurance-policies/999999")
    assert resp.status_code == 404
