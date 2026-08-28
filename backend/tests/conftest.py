import os
import tempfile
import pytest
from fastapi.testclient import TestClient

import database_sqlite

# Every external-service credential the app reads from the environment. Tests must never
# see real values from backend/.env - popping these guarantees the graceful-degradation
# ("not configured") path is always what gets tested, and that a real network call (e.g. an
# actual Mailchimp sync) never accidentally fires during a test run.
_CREDENTIAL_ENV_VARS = [
    "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER",
    "MAILCHIMP_API_KEY", "MAILCHIMP_AUDIENCE_ID",
    "WHATSAPP_TOKEN", "WHATSAPP_PHONE_ID",
    "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM",
    "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
    "LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_REDIRECT_URI",
    "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI",
    "WHATSAPP_BUSINESS_ACCOUNT_ID", "WHATSAPP_VERIFY_TOKEN", "WHATSAPP_APP_SECRET",
    "WHATSAPP_FLOW_PRIVATE_KEY_PATH", "WHATSAPP_FLOW_PRIVATE_KEY", "WHATSAPP_FLOW_PRIVATE_KEY_PASSWORD",
]


@pytest.fixture()
def client():
    """A TestClient backed by a fresh, isolated temp SQLite database - seeded with the same
    demo data (testuser/12345, 5 leads, 4 deals, etc.) as a real first-run database, and
    thrown away after the test. Never touches the real dev database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database_sqlite.DB_PATH = path

    import main  # import here (not top-level) so database_sqlite.DB_PATH is set first
    for key in _CREDENTIAL_ENV_VARS:
        os.environ.pop(key, None)

    with TestClient(main.app) as c:
        yield c

    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture()
def auth_token(client):
    """A valid token for the seeded testuser/12345 account."""
    resp = client.post("/api/auth/login", json={"username": "testuser", "password": "12345"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture()
def auth_client(client, auth_token):
    """The same TestClient, pre-configured to attach ?token=... to every request."""
    class _AuthedClient:
        def __init__(self, c, token):
            self._c = c
            self._token = token

        def _url(self, path):
            sep = '&' if '?' in path else '?'
            return f"{path}{sep}token={self._token}"

        def get(self, path, **kw):
            return self._c.get(self._url(path), **kw)

        def post(self, path, **kw):
            return self._c.post(self._url(path), **kw)

        def put(self, path, **kw):
            return self._c.put(self._url(path), **kw)

        def delete(self, path, **kw):
            return self._c.delete(self._url(path), **kw)

    return _AuthedClient(client, auth_token)
