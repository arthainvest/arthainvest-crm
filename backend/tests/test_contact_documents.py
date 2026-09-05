def _make_contact(auth_client, name="Document Test Client"):
    resp = auth_client.post("/api/contacts", json={"name": name, "phone": "9876511111"})
    return resp.json()["id"]


def test_contact_documents_require_auth(client):
    resp = client.get("/api/contacts/1/documents")
    assert resp.status_code == 401


def test_upload_list_and_delete_document(auth_client):
    contact_id = _make_contact(auth_client)

    resp = auth_client.post(
        f"/api/contacts/{contact_id}/documents?document_type=PAN",
        files={"file": ("pan_card.pdf", b"%PDF-1.4 fake pan card bytes", "application/pdf")}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["contact_id"] == contact_id
    assert data["document_type"] == "PAN"
    assert data["file_name"] == "pan_card.pdf"
    # No S3 configured in tests, so this falls back to database-blob storage (see
    # upload_contact_document in main.py) - file_url points at the /content endpoint below
    # rather than a static file path.
    assert data["file_url"] == f"/api/contacts/{contact_id}/documents/{data['id']}/content"
    assert data["uploaded_by_name"] == "testuser"

    resp = auth_client.get(f"/api/contacts/{contact_id}/documents")
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 1
    assert docs[0]["document_type"] == "PAN"

    resp = auth_client.get(data["file_url"])
    assert resp.status_code == 200
    assert resp.content == b"%PDF-1.4 fake pan card bytes"
    assert resp.headers["content-type"] == "application/pdf"

    resp = auth_client.delete(f"/api/contacts/{contact_id}/documents/{data['id']}")
    assert resp.status_code == 200

    resp = auth_client.get(f"/api/contacts/{contact_id}/documents")
    assert resp.json() == []

    resp = auth_client.get(data["file_url"])
    assert resp.status_code == 404


def test_upload_multiple_document_types_for_same_contact(auth_client):
    contact_id = _make_contact(auth_client)

    for doc_type, filename in [("Aadhar", "aadhar.pdf"), ("CIBIL Report", "cibil.pdf"), ("Photo", "photo.jpg")]:
        resp = auth_client.post(
            f"/api/contacts/{contact_id}/documents?document_type={doc_type}",
            files={"file": (filename, b"fake bytes", "application/octet-stream")}
        )
        assert resp.status_code == 200

    resp = auth_client.get(f"/api/contacts/{contact_id}/documents")
    assert len(resp.json()) == 3


def test_upload_document_unknown_contact_404s(auth_client):
    resp = auth_client.post(
        "/api/contacts/999999/documents?document_type=PAN",
        files={"file": ("pan.pdf", b"fake bytes", "application/pdf")}
    )
    assert resp.status_code == 404


def test_delete_unknown_document_404s(auth_client):
    contact_id = _make_contact(auth_client)
    resp = auth_client.delete(f"/api/contacts/{contact_id}/documents/999999")
    assert resp.status_code == 404


def test_document_defaults_to_other_type(auth_client):
    contact_id = _make_contact(auth_client)
    resp = auth_client.post(
        f"/api/contacts/{contact_id}/documents",
        files={"file": ("misc.pdf", b"fake bytes", "application/pdf")}
    )
    assert resp.status_code == 200
    assert resp.json()["document_type"] == "Other"
