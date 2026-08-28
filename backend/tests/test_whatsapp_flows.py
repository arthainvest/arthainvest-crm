"""Tests the Flow data-exchange endpoint's encryption round-trip against a self-generated
test RSA keypair, acting as an independent implementation of Meta's client-side spec (not
just re-using the server's own helper functions) - the whole point is to prove the server's
crypto is actually compatible with what Meta would really send/expect, not just internally
consistent with itself.

Spec (verified against Meta's docs before implementing, see main.py's WHATSAPP FLOWS HELPERS
comment): AES key via RSA-OAEP-SHA256/MGF1-SHA256; flow data via AES-GCM with the 128-bit tag
appended to the ciphertext; response encrypted with the same AES key but every bit of the
request IV flipped (XOR 0xFF), tag appended, base64, returned as raw text/plain.
"""
import base64
import json
import os
import tempfile

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@pytest.fixture()
def flow_keypair():
    """A throwaway 2048-bit RSA keypair, written to a temp PEM file and pointed at via
    WHATSAPP_FLOW_PRIVATE_KEY_PATH - this is never a real Meta-registered key, purely for
    proving the encrypt/decrypt round-trip is correct."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    fd, path = tempfile.mkstemp(suffix=".pem")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(pem)

    old_path = os.environ.get("WHATSAPP_FLOW_PRIVATE_KEY_PATH")
    os.environ["WHATSAPP_FLOW_PRIVATE_KEY_PATH"] = path
    yield private_key
    if old_path is None:
        os.environ.pop("WHATSAPP_FLOW_PRIVATE_KEY_PATH", None)
    else:
        os.environ["WHATSAPP_FLOW_PRIVATE_KEY_PATH"] = old_path
    try:
        os.remove(path)
    except OSError:
        pass


def _encrypt_request(public_key, payload_dict, aes_key=None, iv=None):
    """Acts as Meta would: generates (or reuses) a 128-bit AES key and 16-byte IV, RSA-OAEP
    encrypts the AES key with the Flow's public key, AES-GCM encrypts the JSON payload with
    the tag appended, and returns the three base64 fields the real request body carries."""
    aes_key = aes_key or os.urandom(16)
    iv = iv or os.urandom(16)

    encrypted_aes_key = public_key.encrypt(
        aes_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    plaintext = json.dumps(payload_dict).encode()
    encrypted_flow_data = AESGCM(aes_key).encrypt(iv, plaintext, None)

    return {
        "encrypted_flow_data": base64.b64encode(encrypted_flow_data).decode(),
        "encrypted_aes_key": base64.b64encode(encrypted_aes_key).decode(),
        "initial_vector": base64.b64encode(iv).decode(),
    }, aes_key, iv


def _decrypt_response(response_text, aes_key, request_iv):
    """Acts as Meta's client would: flips the request IV, AES-GCM decrypts the raw base64
    text/plain body, returns the parsed JSON."""
    flipped_iv = bytes(b ^ 0xFF for b in request_iv)
    ciphertext = base64.b64decode(response_text)
    plaintext = AESGCM(aes_key).decrypt(flipped_iv, ciphertext, None)
    return json.loads(plaintext)


def test_ping_health_check_round_trip(client, flow_keypair):
    public_key = flow_keypair.public_key()
    body, aes_key, iv = _encrypt_request(public_key, {"version": "3.0", "action": "ping"})

    resp = client.post("/api/webhooks/whatsapp-flow", json=body)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")

    decrypted = _decrypt_response(resp.text, aes_key, iv)
    assert decrypted == {"data": {"status": "active"}}


def test_init_action_returns_requested_screen(client, flow_keypair):
    public_key = flow_keypair.public_key()
    body, aes_key, iv = _encrypt_request(public_key, {
        "version": "3.0", "action": "INIT", "screen": "WELCOME", "data": {}, "flow_token": "unused-init"
    })

    resp = client.post("/api/webhooks/whatsapp-flow", json=body)
    assert resp.status_code == 200
    decrypted = _decrypt_response(resp.text, aes_key, iv)
    assert decrypted["screen"] == "WELCOME"


def test_decryption_failure_returns_421(client, flow_keypair):
    """A body that isn't valid for this key at all - proves the failure path answers with
    the Meta-mandated 421, not a generic 400/500."""
    resp = client.post("/api/webhooks/whatsapp-flow", json={
        "encrypted_flow_data": base64.b64encode(b"not real ciphertext").decode(),
        "encrypted_aes_key": base64.b64encode(b"not a real encrypted key").decode(),
        "initial_vector": base64.b64encode(b"0123456789abcdef").decode(),
    })
    assert resp.status_code == 421


def test_decryption_fails_without_any_key_configured(client):
    """No flow_keypair fixture here - WHATSAPP_FLOW_PRIVATE_KEY_PATH is unset, matching a
    fresh install before the user has generated/uploaded a keypair at all."""
    resp = client.post("/api/webhooks/whatsapp-flow", json={
        "encrypted_flow_data": "AAAA", "encrypted_aes_key": "AAAA", "initial_vector": "AAAA",
    })
    assert resp.status_code == 421


def test_data_exchange_non_terminal_screen_echoes_data_unchanged(auth_client, client, flow_keypair):
    """We don't know this Flow's real screen graph (it's authored in Meta's Flow Builder,
    not here) - a data_exchange for a screen that isn't the configured terminal_screen should
    be a safe no-op echo, not an error and not a guess at business logic."""
    flow = auth_client.post("/api/flows", json={"meta_flow_id": "999999", "name": "Test Flow"}).json()
    assert flow["terminal_screen"] == "SUCCESS"  # the default

    public_key = flow_keypair.public_key()
    body, aes_key, iv = _encrypt_request(public_key, {
        "version": "3.0", "action": "data_exchange", "screen": "STEP_ONE",
        "data": {"full_name": "Test User"}, "flow_token": "no-session-for-this-token"
    })

    resp = client.post("/api/webhooks/whatsapp-flow", json=body)
    assert resp.status_code == 200
    decrypted = _decrypt_response(resp.text, aes_key, iv)
    assert decrypted["screen"] == "STEP_ONE"
    assert decrypted["data"] == {"full_name": "Test User"}


def test_data_exchange_terminal_screen_maps_onto_contact_custom_fields(auth_client, client, flow_keypair):
    """The real end-to-end case: sending a Flow creates a session tied to a conversation/
    contact, and a data_exchange on the configured terminal screen should both signal
    completion (Meta's SUCCESS convention) and write the submitted fields onto that
    contact's custom fields - the brief's "map onto the existing lead/contact/custom-field
    model" requirement, verified with a real assertion against GET .../custom-fields, not
    just that the HTTP call succeeded."""
    contact = auth_client.post("/api/contacts", json={"name": "Flow Test Contact", "phone": "+91-9991112233"}).json()
    flow = auth_client.post("/api/flows", json={
        "meta_flow_id": "888888", "name": "Loan Application Flow", "terminal_screen": "DONE"
    }).json()
    assert flow["terminal_screen"] == "DONE"

    # Establish the conversation via an inbound webhook message (same as any real customer
    # reply), so it's linked to the contact by phone before the Flow session references it.
    client.post("/api/webhooks/whatsapp", json={
        "entry": [{"changes": [{"value": {"messages": [{
            "from": "919991112233", "id": "wamid.FLOWLINK001", "type": "text", "text": {"body": "Hi"}
        }]}}]}]
    })

    # Manually seed a flow session the way POST /flows/{id}/send would (bypassing the actual
    # WhatsApp send, since WHATSAPP_TOKEN isn't configured in tests) - this test is about the
    # data-exchange mapping, not the send call itself (covered separately below).
    import database_sqlite
    with database_sqlite.get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM whatsapp_conversation WHERE wa_number = '919991112233'")
        conversation_id = cur.fetchone()["id"]
        cur.execute(
            "INSERT INTO whatsapp_flow_session (flow_token, flow_id, conversation_id, current_screen) VALUES (?, ?, ?, ?)",
            ("test-flow-token-terminal", flow["id"], conversation_id, "STEP_ONE")
        )
        conn.commit()

    public_key = flow_keypair.public_key()
    body, aes_key, iv = _encrypt_request(public_key, {
        "version": "3.0", "action": "data_exchange", "screen": "DONE",
        "data": {"loan_amount": "500000", "loan_purpose": "Home Renovation"},
        "flow_token": "test-flow-token-terminal"
    })

    resp = client.post("/api/webhooks/whatsapp-flow", json=body)
    assert resp.status_code == 200
    decrypted = _decrypt_response(resp.text, aes_key, iv)
    assert decrypted["screen"] == "SUCCESS"

    custom_fields = auth_client.get(f"/api/custom-fields/for/contact/{contact['id']}").json()
    by_name = {f["name"]: f["value"] for f in custom_fields}
    assert by_name.get("loan_amount") == "500000"
    assert by_name.get("loan_purpose") == "Home Renovation"

    sessions = auth_client.get(f"/api/flows/{flow['id']}/sessions").json()
    session = next(s for s in sessions if s["flow_token"] == "test-flow-token-terminal")
    assert session["status"] == "completed"
    assert session["completed_at"] is not None


def test_flow_crud(auth_client):
    created = auth_client.post("/api/flows", json={"meta_flow_id": "111", "name": "KYC Flow"}).json()
    assert created["status"] == "draft"

    updated = auth_client.put(f"/api/flows/{created['id']}", json={"status": "published", "terminal_screen": "COMPLETE"}).json()
    assert updated["status"] == "published"
    assert updated["terminal_screen"] == "COMPLETE"

    listed = auth_client.get("/api/flows").json()
    assert any(f["id"] == created["id"] for f in listed)

    resp = auth_client.delete(f"/api/flows/{created['id']}")
    assert resp.status_code == 200
    listed_after = auth_client.get("/api/flows").json()
    assert not any(f["id"] == created["id"] for f in listed_after)


def test_flow_update_unknown_404s(auth_client):
    resp = auth_client.put("/api/flows/9999", json={"status": "published"})
    assert resp.status_code == 404


def test_flow_delete_unknown_404s(auth_client):
    resp = auth_client.delete("/api/flows/9999")
    assert resp.status_code == 404


def test_send_flow_returns_not_configured_without_whatsapp_credentials(auth_client):
    """conftest strips WHATSAPP_TOKEN/WHATSAPP_PHONE_ID for every test - same graceful
    degradation pattern as every other external-service endpoint."""
    flow = auth_client.post("/api/flows", json={"meta_flow_id": "222", "name": "Test Flow"}).json()
    resp = auth_client.post(f"/api/flows/{flow['id']}/send", json={
        "to": "919876500001", "body_text": "Please complete this form", "screen": "WELCOME"
    })
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_send_flow_unknown_flow_404s(auth_client):
    resp = auth_client.post("/api/flows/9999/send", json={"to": "919876500001", "body_text": "Hi", "screen": "WELCOME"})
    assert resp.status_code == 404
