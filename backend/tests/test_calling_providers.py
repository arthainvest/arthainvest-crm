"""Unit tests for calling_providers.py in isolation, run without going through the API."""
from unittest.mock import patch, MagicMock
from calling_providers import (
    LocalTelProvider, TwilioProvider, ExotelProvider, get_cloud_calling_provider,
)


def test_local_tel_provider_always_configured():
    provider = LocalTelProvider()
    assert provider.is_configured() is True
    result = provider.place_call("+919999999999", "+911234567890", call_id=1)
    assert result.ok is True
    assert result.call_sid is None


def test_get_cloud_calling_provider_returns_none_when_unconfigured(monkeypatch):
    for var in ["EXOTEL_SID", "EXOTEL_API_KEY", "EXOTEL_API_TOKEN", "EXOTEL_CALLER_ID",
                "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER"]:
        monkeypatch.delenv(var, raising=False)
    assert get_cloud_calling_provider() is None


def test_get_cloud_calling_provider_prefers_exotel_over_twilio(monkeypatch):
    monkeypatch.setenv("EXOTEL_SID", "sid")
    monkeypatch.setenv("EXOTEL_API_KEY", "key")
    monkeypatch.setenv("EXOTEL_API_TOKEN", "token")
    monkeypatch.setenv("EXOTEL_CALLER_ID", "caller")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "twilio-sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "twilio-token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+10000000000")

    provider = get_cloud_calling_provider()
    assert provider.name == "exotel"


def test_get_cloud_calling_provider_falls_back_to_twilio(monkeypatch):
    for var in ["EXOTEL_SID", "EXOTEL_API_KEY", "EXOTEL_API_TOKEN", "EXOTEL_CALLER_ID"]:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "twilio-sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "twilio-token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+10000000000")

    provider = get_cloud_calling_provider()
    assert provider.name == "twilio"


def test_twilio_provider_requires_all_three_vars(monkeypatch):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("TWILIO_FROM_NUMBER", raising=False)
    assert TwilioProvider().is_configured() is False


def test_exotel_provider_requires_all_four_vars(monkeypatch):
    monkeypatch.setenv("EXOTEL_SID", "sid")
    monkeypatch.setenv("EXOTEL_API_KEY", "key")
    monkeypatch.delenv("EXOTEL_API_TOKEN", raising=False)
    monkeypatch.delenv("EXOTEL_CALLER_ID", raising=False)
    assert ExotelProvider().is_configured() is False


def test_twilio_provider_place_call_success(monkeypatch):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+10000000000")

    with patch("twilio.rest.Client") as mock_client_cls:
        mock_client_cls.return_value.calls.create.return_value = MagicMock(sid="CA123")
        result = TwilioProvider().place_call("+919999999999", "+911234567890", call_id=42)

    assert result.ok is True
    assert result.call_sid == "CA123"


def test_exotel_provider_place_call_success(monkeypatch):
    monkeypatch.setenv("EXOTEL_SID", "sid")
    monkeypatch.setenv("EXOTEL_API_KEY", "key")
    monkeypatch.setenv("EXOTEL_API_TOKEN", "token")
    monkeypatch.setenv("EXOTEL_CALLER_ID", "caller")

    fake_response = MagicMock(status_code=200)
    fake_response.json.return_value = {"Call": {"Sid": "CSid1"}}
    with patch("requests.post", return_value=fake_response) as mock_post:
        result = ExotelProvider().place_call("+919999999999", "+911234567890", call_id=42)

    assert result.ok is True
    assert result.call_sid == "CSid1"
    assert mock_post.call_args.kwargs["data"]["CustomField"] == "42"


def test_exotel_provider_place_call_error_is_reported_not_raised(monkeypatch):
    monkeypatch.setenv("EXOTEL_SID", "sid")
    monkeypatch.setenv("EXOTEL_API_KEY", "key")
    monkeypatch.setenv("EXOTEL_API_TOKEN", "token")
    monkeypatch.setenv("EXOTEL_CALLER_ID", "caller")

    fake_response = MagicMock(status_code=401)
    fake_response.json.return_value = {"RestException": {"Message": "Authentication failed"}}
    fake_response.text = '{"RestException": {"Message": "Authentication failed"}}'
    with patch("requests.post", return_value=fake_response):
        result = ExotelProvider().place_call("+919999999999", "+911234567890", call_id=42)

    assert result.ok is False
    assert result.error == "Authentication failed"
