"""Phase 1.5: /api/health now actually round-trips the database instead of being a static
'ok' stub - this is what an external uptime monitor pings, so a database outage must show up
as a real failure, not a false-positive 200."""
from unittest.mock import patch


def test_health_check_reports_database_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["database"]["status"] == "ok"
    assert isinstance(data["database"]["latency_ms"], (int, float))
    assert data["database"]["error"] is None


def test_health_check_is_public_no_token_required(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_health_check_returns_503_when_database_is_down(client):
    with patch("main.get_db", side_effect=Exception("connection refused")):
        resp = client.get("/api/health")
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["database"]["status"] == "error"
    assert "connection refused" in data["database"]["error"]
