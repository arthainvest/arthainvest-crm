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
