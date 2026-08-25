from unittest.mock import patch, MagicMock


def _first_lead(auth_client):
    return auth_client.get("/api/leads").json()[0]


def _team_member(auth_client, name):
    return next(m for m in auth_client.get("/api/team").json() if m["name"] == name)


def test_dialer_assign_and_work_queue(auth_client):
    lead = _first_lead(auth_client)
    rajesh = _team_member(auth_client, "Rajesh Kumar")

    resp = auth_client.post("/api/dialer/assign", json={
        "team_member_id": rajesh["id"], "lead_ids": [lead["id"]]
    })
    assert resp.status_code == 200
    assert resp.json() == {"assigned": 1, "skipped": 0}

    queue = auth_client.get(f"/api/dialer/queue?team_member_id={rajesh['id']}").json()
    assert len(queue) == 1
    assert queue[0]["name"] == lead["name"]
    assert queue[0]["phone"] == lead["phone"]
    assert queue[0]["status"] == "Pending"
    assert queue[0]["lead_id"] == lead["id"]

    item_id = queue[0]["id"]
    updated = auth_client.put(f"/api/dialer/queue/{item_id}", json={"status": "Called"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "Called"
    assert updated.json()["completed_at"] is not None

    # Marking it Called removes it from the default (Pending) queue view.
    queue_after = auth_client.get(f"/api/dialer/queue?team_member_id={rajesh['id']}").json()
    assert queue_after == []


def test_dialer_assign_skips_records_already_pending_for_that_member(auth_client):
    lead = _first_lead(auth_client)
    rajesh = _team_member(auth_client, "Rajesh Kumar")

    first = auth_client.post("/api/dialer/assign", json={
        "team_member_id": rajesh["id"], "lead_ids": [lead["id"]]
    }).json()
    assert first == {"assigned": 1, "skipped": 0}

    second = auth_client.post("/api/dialer/assign", json={
        "team_member_id": rajesh["id"], "lead_ids": [lead["id"]]
    }).json()
    assert second == {"assigned": 0, "skipped": 1}

    # Only one entry exists, not two.
    queue = auth_client.get(f"/api/dialer/queue?team_member_id={rajesh['id']}").json()
    assert len(queue) == 1


def test_dialer_assign_rejects_unknown_team_member(auth_client):
    lead = _first_lead(auth_client)
    resp = auth_client.post("/api/dialer/assign", json={
        "team_member_id": 9999, "lead_ids": [lead["id"]]
    })
    assert resp.status_code == 404


def test_dialer_assign_requires_at_least_one_record(auth_client):
    rajesh = _team_member(auth_client, "Rajesh Kumar")
    resp = auth_client.post("/api/dialer/assign", json={"team_member_id": rajesh["id"]})
    assert resp.status_code == 400


def test_dialer_delete_removes_from_queue(auth_client):
    lead = _first_lead(auth_client)
    rajesh = _team_member(auth_client, "Rajesh Kumar")
    auth_client.post("/api/dialer/assign", json={"team_member_id": rajesh["id"], "lead_ids": [lead["id"]]})
    item_id = auth_client.get(f"/api/dialer/queue?team_member_id={rajesh['id']}").json()[0]["id"]

    del_resp = auth_client.delete(f"/api/dialer/queue/{item_id}")
    assert del_resp.status_code == 200

    queue = auth_client.get(f"/api/dialer/queue?team_member_id={rajesh['id']}").json()
    assert queue == []


def test_activities_feed_includes_seeded_calls(auth_client):
    """The demo database seeds 4 calls - the unified feed must surface them as Call-channel
    activities without needing anything logged to communication_log."""
    resp = auth_client.get("/api/activities")
    assert resp.status_code == 200
    items = resp.json()
    call_items = [i for i in items if i["channel"] == "Call"]
    assert len(call_items) == 4
    assert all(i["contact"] for i in call_items)

    # Channel filter narrows correctly - no Email activity exists yet.
    email_items = auth_client.get("/api/activities?channel=Email").json()
    assert email_items == []


def test_activities_feed_merges_communication_log_with_calls(auth_client, monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.fake.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@fake.com")
    monkeypatch.setenv("SMTP_PASSWORD", "fakepass")

    mock_server = MagicMock()
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.return_value = mock_server
        auth_client.post("/api/email/send", json={
            "to": "client@example.com", "subject": "Renewal reminder", "body": "Please renew soon."
        })

    items = auth_client.get("/api/activities").json()
    email_items = [i for i in items if i["channel"] == "Email"]
    assert len(email_items) == 1
    assert email_items[0]["contact"] == "client@example.com"
    assert email_items[0]["outcome"] == "Sent"

    # Most recent first - the just-sent email should be the very first item.
    assert items[0]["channel"] == "Email"


def test_companies_crud(auth_client):
    empty = auth_client.get("/api/companies")
    assert empty.status_code == 200
    assert empty.json() == []

    create_resp = auth_client.post("/api/companies", json={
        "name": "Acme Textiles", "industry": "Manufacturing", "city": "Surat", "phone": "9998887770"
    })
    assert create_resp.status_code == 200
    company = create_resp.json()
    assert company["name"] == "Acme Textiles"
    assert company["industry"] == "Manufacturing"

    listed = auth_client.get("/api/companies").json()
    assert len(listed) == 1

    update_resp = auth_client.put(f"/api/companies/{company['id']}", json={"city": "Ahmedabad"})
    assert update_resp.status_code == 200
    assert update_resp.json()["city"] == "Ahmedabad"
    assert update_resp.json()["name"] == "Acme Textiles"  # untouched fields survive a partial update

    delete_resp = auth_client.delete(f"/api/companies/{company['id']}")
    assert delete_resp.status_code == 200
    assert auth_client.get("/api/companies").json() == []


def test_update_nonexistent_company_404s(auth_client):
    resp = auth_client.put("/api/companies/9999", json={"name": "Ghost Co"})
    assert resp.status_code == 404
