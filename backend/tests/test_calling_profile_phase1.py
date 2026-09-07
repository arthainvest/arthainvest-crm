"""Phase 1: Employee Calling Profile, the click-to-call lifecycle (initiated -> completed/
abandoned), and manual recording upload. testuser is login-linked to the seeded 'Artha'
team_members row, so toggling that row's calling_enabled/active directly affects what
testuser's own dial_call calls are allowed to do.
"""
import io
from unittest.mock import patch, MagicMock


def _artha_id(auth_client):
    return next(m for m in auth_client.get("/api/team").json() if m["name"] == "Artha")["id"]


def _configure_twilio_dial(monkeypatch, auth_client):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+10000000000")


# ---- Linking a roster entry to a login account ----

def test_link_team_member_to_user_id(auth_client):
    resp = auth_client.post("/api/team", json={"name": "Linkable Person", "role": "employee"})
    member_id = resp.json()["id"]
    assert resp.json()["user_id"] is None

    link_resp = auth_client.put(f"/api/team/{member_id}", json={"user_id": 42})
    assert link_resp.status_code == 200
    assert link_resp.json()["user_id"] == 42

    direct = next(m for m in auth_client.get("/api/team").json() if m["id"] == member_id)
    assert direct["user_id"] == 42


# ---- Calling Profile CRUD ----

def test_team_member_has_calling_profile_defaults(auth_client):
    artha = next(m for m in auth_client.get("/api/team").json() if m["name"] == "Artha")
    assert artha["calling_enabled"] is True
    assert artha["recording_enabled"] is False
    assert artha["active"] is True
    assert artha["phone_verification_status"] == "unverified"
    assert artha["phone_verified_at"] is None


def test_update_calling_profile_flags(auth_client):
    member_id = _artha_id(auth_client)
    resp = auth_client.put(f"/api/team/{member_id}", json={
        "calling_enabled": False, "recording_enabled": True, "active": False
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["calling_enabled"] is False
    assert data["recording_enabled"] is True
    assert data["active"] is False


def test_changing_phone_resets_verification_status(auth_client):
    member_id = _artha_id(auth_client)
    auth_client.put(f"/api/team/{member_id}/verify-phone")
    verified = next(m for m in auth_client.get("/api/team").json() if m["id"] == member_id)
    assert verified["phone_verification_status"] == "verified"
    assert verified["phone_verified_at"] is not None

    auth_client.put(f"/api/team/{member_id}", json={"phone": "+919876500099"})
    after = next(m for m in auth_client.get("/api/team").json() if m["id"] == member_id)
    assert after["phone_verification_status"] == "unverified"
    assert after["phone_verified_at"] is None


def test_verify_phone_requires_a_phone_number(auth_client):
    member_id = _artha_id(auth_client)
    auth_client.put(f"/api/team/{member_id}", json={"active": True})  # no-op update, phone untouched
    resp = auth_client.post("/api/team", json={"name": "No Phone Guy", "role": "employee"})
    new_id = resp.json()["id"]
    verify_resp = auth_client.put(f"/api/team/{new_id}/verify-phone")
    assert verify_resp.status_code == 400


# ---- dial_call respects the calling profile ----

def test_dial_blocked_when_calling_disabled(auth_client):
    member_id = _artha_id(auth_client)
    auth_client.put(f"/api/team/{member_id}", json={"calling_enabled": False})

    resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is False
    assert "disabled" in data["message"].lower()
    assert data["call_id"] is None  # blocked entirely - never even creates an initiated row


def test_dial_blocked_when_member_inactive(auth_client):
    member_id = _artha_id(auth_client)
    auth_client.put(f"/api/team/{member_id}", json={"active": False})

    resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    assert resp.status_code == 200
    assert resp.json()["configured"] is False
    assert resp.json()["call_id"] is None


def test_dial_uses_team_members_phone_over_user_settings_phone(auth_client, monkeypatch):
    """Phase 1 migration: team_members.phone is canonical, user_settings.phone is legacy
    fallback only - when both are set, the roster's number wins."""
    member_id = _artha_id(auth_client)
    auth_client.put(f"/api/team/{member_id}", json={"phone": "+919000000001"})
    auth_client.put("/api/settings", json={"phone": "+918000000002"})
    _configure_twilio_dial(monkeypatch, auth_client)

    with patch("twilio.rest.Client") as mock_client_cls:
        mock_create = mock_client_cls.return_value.calls.create
        mock_create.return_value = MagicMock(sid="CA_PHASE1")
        auth_client.post("/api/calls/dial", json={"to": "+911234567890"})

    assert mock_create.call_args.kwargs["to"] == "+919000000001"


def test_dial_falls_back_to_user_settings_phone_when_roster_phone_unset(auth_client, monkeypatch):
    member_id = _artha_id(auth_client)
    auth_client.put(f"/api/team/{member_id}", json={"phone": ""})
    auth_client.put("/api/settings", json={"phone": "+918000000002"})
    _configure_twilio_dial(monkeypatch, auth_client)

    with patch("twilio.rest.Client") as mock_client_cls:
        mock_create = mock_client_cls.return_value.calls.create
        mock_create.return_value = MagicMock(sid="CA_FALLBACK")
        auth_client.post("/api/calls/dial", json={"to": "+911234567890"})

    assert mock_create.call_args.kwargs["to"] == "+918000000002"


# ---- complete_call: same-row lifecycle, not a second call record ----

def test_complete_call_updates_the_same_row(auth_client):
    dial_resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    call_id = dial_resp.json()["call_id"]

    complete_resp = auth_client.put(f"/api/calls/{call_id}/complete", json={
        "status": "completed", "duration_seconds": 125, "outcome": "Interested",
        "notes": "Wants a home loan quote.", "follow_up_date": "2026-09-15"
    })
    assert complete_resp.status_code == 200
    data = complete_resp.json()
    assert data["id"] == call_id
    assert data["status"] == "completed"
    assert data["duration_seconds"] == 125
    assert data["outcome"] == "Interested"
    assert data["notes"] == "Wants a home loan quote."
    assert data["follow_up_date"] == "2026-09-15"

    all_calls = auth_client.get("/api/calls").json()
    assert len([c for c in all_calls if c["id"] == call_id]) == 1  # never duplicated


def test_complete_call_non_completed_status_maps_outcome(auth_client):
    dial_resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    call_id = dial_resp.json()["call_id"]

    resp = auth_client.put(f"/api/calls/{call_id}/complete", json={"status": "no_answer"})
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "No Answer"
    assert resp.json()["status"] == "no_answer"


def test_complete_call_rejects_invalid_status(auth_client):
    dial_resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    call_id = dial_resp.json()["call_id"]

    resp = auth_client.put(f"/api/calls/{call_id}/complete", json={"status": "bogus"})
    assert resp.status_code == 400


def test_complete_call_404s_for_unknown_call(auth_client):
    resp = auth_client.put("/api/calls/999999/complete", json={"status": "completed"})
    assert resp.status_code == 404


# ---- Abandoned-call sweep ----

def test_stale_initiated_call_is_swept_to_abandoned(auth_client):
    dial_resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    call_id = dial_resp.json()["call_id"]

    import database_sqlite
    with database_sqlite.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE calls SET created_at = datetime('now', '-1 hour') WHERE id = ?", (call_id,))
        conn.commit()

    calls = auth_client.get("/api/calls").json()  # sweep runs on every list fetch
    swept = next(c for c in calls if c["id"] == call_id)
    assert swept["status"] == "abandoned"
    assert swept["outcome"] == "Unknown"


def test_recently_initiated_call_is_not_swept(auth_client):
    dial_resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    call_id = dial_resp.json()["call_id"]

    calls = auth_client.get("/api/calls").json()
    fresh = next(c for c in calls if c["id"] == call_id)
    assert fresh["status"] == "initiated"


# ---- Recording upload/download ----

def test_upload_and_download_recording(auth_client):
    dial_resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    call_id = dial_resp.json()["call_id"]

    fake_audio = b"RIFF....WAVEfake audio bytes"
    resp = auth_client.post(
        f"/api/calls/{call_id}/recording",
        files={"file": ("call.wav", io.BytesIO(fake_audio), "audio/wav")}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["recording_source"] == "manual"
    assert data["recording_file_name"] == "call.wav"
    assert data["recording_file_size"] == len(fake_audio)
    assert data["recording_uploaded_at"] is not None

    download = auth_client.get(f"/api/calls/{call_id}/recording")
    assert download.status_code == 200
    assert download.content == fake_audio
    assert download.headers["content-type"] == "audio/wav"


def test_upload_rejects_wrong_content_type(auth_client):
    dial_resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    call_id = dial_resp.json()["call_id"]

    resp = auth_client.post(
        f"/api/calls/{call_id}/recording",
        files={"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")}
    )
    assert resp.status_code == 400


def test_upload_rejects_oversized_file(auth_client):
    dial_resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    call_id = dial_resp.json()["call_id"]

    oversized = b"0" * (20 * 1024 * 1024 + 1)
    resp = auth_client.post(
        f"/api/calls/{call_id}/recording",
        files={"file": ("big.wav", io.BytesIO(oversized), "audio/wav")}
    )
    assert resp.status_code == 400


def test_download_404s_when_no_recording_uploaded(auth_client):
    dial_resp = auth_client.post("/api/calls/dial", json={"to": "+911234567890"})
    call_id = dial_resp.json()["call_id"]

    resp = auth_client.get(f"/api/calls/{call_id}/recording")
    assert resp.status_code == 404


def test_recording_requires_auth(client):
    resp = client.get("/api/calls/1/recording")
    assert resp.status_code == 401
