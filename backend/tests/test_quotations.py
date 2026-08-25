from unittest.mock import patch, MagicMock


def _first_lead(auth_client):
    return auth_client.get("/api/leads").json()[0]


def _first_contact(auth_client):
    return auth_client.get("/api/contacts").json()[0]


def test_quotations_empty_by_default(auth_client):
    resp = auth_client.get("/api/quotations")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_quotation_computes_grand_total_and_number(auth_client):
    lead = _first_lead(auth_client)

    resp = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"],
        "title": "Home Loan Quotation",
        "valid_until": "2026-09-30",
        "items": [
            {"description": "Processing Fee", "amount": 5000},
            {"description": "Loan Principal", "amount": 2500000},
        ],
    })
    assert resp.status_code == 200
    quotation = resp.json()
    assert quotation["quotation_number"] == f"QT-{quotation['id']:04d}"
    assert quotation["status"] == "Draft"
    assert quotation["grand_total"] == 2505000
    assert quotation["lead_name"] == lead["name"]
    assert len(quotation["items"]) == 2

    listed = auth_client.get("/api/quotations").json()
    assert len(listed) == 1
    assert listed[0]["id"] == quotation["id"]


def test_get_single_quotation_and_404(auth_client):
    lead = _first_lead(auth_client)
    created = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "Test Quote", "items": [{"description": "A", "amount": 100}]
    }).json()

    resp = auth_client.get(f"/api/quotations/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test Quote"

    missing = auth_client.get("/api/quotations/9999")
    assert missing.status_code == 404


def test_update_quotation_status_and_replace_items(auth_client):
    lead = _first_lead(auth_client)
    created = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "Test Quote", "items": [{"description": "A", "amount": 100}]
    }).json()

    resp = auth_client.put(f"/api/quotations/{created['id']}", json={
        "status": "Accepted",
        "items": [{"description": "Revised Item", "amount": 999}],
    })
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["status"] == "Accepted"
    assert len(updated["items"]) == 1
    assert updated["items"][0]["description"] == "Revised Item"
    assert updated["grand_total"] == 999


def test_update_nonexistent_quotation_404s(auth_client):
    resp = auth_client.put("/api/quotations/9999", json={"status": "Sent"})
    assert resp.status_code == 404


def test_delete_quotation(auth_client):
    lead = _first_lead(auth_client)
    created = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "Test Quote", "items": []
    }).json()

    resp = auth_client.delete(f"/api/quotations/{created['id']}")
    assert resp.status_code == 200
    assert auth_client.get("/api/quotations").json() == []


def test_send_quotation_emails_recipient_and_marks_sent(auth_client, monkeypatch):
    contact = _first_contact(auth_client)
    created = auth_client.post("/api/quotations", json={
        "contact_id": contact["id"],
        "title": "Term Insurance Quotation",
        "items": [{"description": "Annual Premium", "amount": 12000}],
    }).json()
    assert created["status"] == "Draft"

    monkeypatch.setenv("SMTP_HOST", "smtp.fake.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@fake.com")
    monkeypatch.setenv("SMTP_PASSWORD", "fakepass")

    mock_server = MagicMock()
    with patch("smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.return_value.__enter__.return_value = mock_server
        resp = auth_client.post(f"/api/quotations/{created['id']}/send")

    assert resp.status_code == 200
    assert resp.json()["configured"] is True
    assert "sent" in resp.json()["message"].lower()

    updated = auth_client.get(f"/api/quotations/{created['id']}").json()
    assert updated["status"] == "Sent"

    log = auth_client.get("/api/communication-log").json()
    assert len(log) == 1
    assert log[0]["channel"] == "Email"
    assert log[0]["recipient"] == contact["email"]

    activities = auth_client.get("/api/activities?channel=Email").json()
    assert len(activities) == 1


def test_send_quotation_without_email_on_file(auth_client):
    lead_resp = auth_client.post("/api/leads", json={"name": "No Email Lead", "phone": "9998887771"})
    lead = lead_resp.json()
    created = auth_client.post("/api/quotations", json={
        "lead_id": lead["id"], "title": "Test Quote", "items": [{"description": "A", "amount": 100}]
    }).json()

    resp = auth_client.post(f"/api/quotations/{created['id']}/send")
    assert resp.status_code == 200
    assert "no email address" in resp.json()["message"].lower()

    # Status must stay Draft - nothing was actually sent.
    unchanged = auth_client.get(f"/api/quotations/{created['id']}").json()
    assert unchanged["status"] == "Draft"


def test_send_quotation_not_found(auth_client):
    resp = auth_client.post("/api/quotations/9999/send")
    assert resp.status_code == 404
