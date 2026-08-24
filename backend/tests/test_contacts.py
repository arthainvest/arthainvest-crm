def test_list_contacts_returns_seeded_data(auth_client):
    resp = auth_client.get("/api/contacts")
    assert resp.status_code == 200
    assert len(resp.json()) == 5


def test_create_update_delete_contact(auth_client):
    resp = auth_client.post("/api/contacts", json={
        "name": "New Contact", "company": "Acme", "phone": "8888888888", "city": "Pune"
    })
    assert resp.status_code == 200
    contact_id = resp.json()["id"]

    resp = auth_client.put(f"/api/contacts/{contact_id}", json={"score": 90})
    assert resp.status_code == 200
    assert resp.json()["score"] == 90

    resp = auth_client.delete(f"/api/contacts/{contact_id}")
    assert resp.status_code == 200

    resp = auth_client.get("/api/contacts")
    assert len(resp.json()) == 5


def test_upcoming_renewals(auth_client):
    from datetime import date, timedelta
    today = date.today()

    overdue_id = auth_client.post("/api/contacts", json={
        "name": "Overdue Client", "phone": "1111111111",
        "renewal_date": (today - timedelta(days=5)).isoformat()
    }).json()["id"]
    due_soon_id = auth_client.post("/api/contacts", json={
        "name": "Due Soon Client", "phone": "2222222222",
        "renewal_date": (today + timedelta(days=3)).isoformat()
    }).json()["id"]
    upcoming_id = auth_client.post("/api/contacts", json={
        "name": "Upcoming Client", "phone": "3333333333",
        "renewal_date": (today + timedelta(days=20)).isoformat()
    }).json()["id"]
    # Renews in 90 days - should NOT show up, only the next 30 days matter here.
    auth_client.post("/api/contacts", json={
        "name": "Far Off Client", "phone": "4444444444",
        "renewal_date": (today + timedelta(days=90)).isoformat()
    })

    resp = auth_client.get("/api/contacts/renewals")
    assert resp.status_code == 200
    rows = resp.json()
    by_id = {r["id"]: r for r in rows}

    assert set(by_id.keys()) == {overdue_id, due_soon_id, upcoming_id}
    assert by_id[overdue_id]["urgency"] == "overdue"
    assert by_id[due_soon_id]["urgency"] == "due_soon"
    assert by_id[upcoming_id]["urgency"] == "upcoming"
    # Sorted soonest first.
    assert [r["id"] for r in rows] == [overdue_id, due_soon_id, upcoming_id]


def test_contact_notes_crud(auth_client):
    resp = auth_client.get("/api/contacts/1/notes")
    assert resp.status_code == 200
    assert len(resp.json()) == 1  # seeded note

    resp = auth_client.post("/api/contacts/1/notes", json={"transcript": "Follow-up call."})
    assert resp.status_code == 200
    note_id = resp.json()["id"]

    resp = auth_client.get("/api/contacts/1/notes")
    assert len(resp.json()) == 2

    resp = auth_client.delete(f"/api/contacts/1/notes/{note_id}")
    assert resp.status_code == 200
    resp = auth_client.get("/api/contacts/1/notes")
    assert len(resp.json()) == 1
