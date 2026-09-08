"""Calling provider abstraction (Phase 1.5).

    CRM Call Engine
          |
          +-- LocalTelProvider   <- CURRENT, Rs.0 (plain tel: link, no server-side dialing)
          |
          +-- ExotelProvider     <- FUTURE (built, not connected - no credentials set)
          |
          +-- TwilioProvider     <- FUTURE (built, not connected - no credentials set)

dial_call (see main.py) resolves a provider via get_cloud_calling_provider() and only falls
back to a plain tel: link when none is configured - swapping in a real telephony provider
later means setting its env vars, not rewriting the calling flow, the calling-profile checks,
or the call-record lifecycle (initiated -> completed/abandoned) that already exist.

ExotelProvider and TwilioProvider are functionally unchanged from what dial_call/
_dial_via_exotel did inline before this module existed - this is an extraction, not a rewrite,
specifically so the already-live-verified Phase 1 behavior doesn't shift under this abstraction.
"""
from abc import ABC, abstractmethod
import os


class CallProviderResult:
    def __init__(self, ok, call_sid=None, error=None):
        self.ok = ok
        self.call_sid = call_sid
        self.error = error


class CallProvider(ABC):
    name: str

    @abstractmethod
    def is_configured(self) -> bool:
        ...

    @abstractmethod
    def place_call(self, agent_number: str, customer_number: str, call_id: int) -> CallProviderResult:
        """Ring agent_number first, then bridge to customer_number once answered. call_id is
        this app's own calls.id row (already created as status='initiated' by the caller),
        threaded through so an async status webhook can correlate back to the right record -
        see ExotelProvider's CustomField and main.py's exotel_status_webhook."""
        ...


class LocalTelProvider(CallProvider):
    """The current setup: no server-side dialing at all - the frontend opens a plain tel:
    link on the employee's own device. Always "configured" (no credentials needed), and
    place_call is a no-op since there's nothing for the server to do here. Not returned by
    get_cloud_calling_provider() (that only resolves a REAL bridging provider) - dial_call
    falls back to this behavior itself whenever get_cloud_calling_provider() returns None."""
    name = "local_tel"

    def is_configured(self) -> bool:
        return True

    def place_call(self, agent_number, customer_number, call_id):
        return CallProviderResult(ok=True)


class TwilioProvider(CallProvider):
    name = "twilio"

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER")

    def is_configured(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.from_number)

    def place_call(self, agent_number, customer_number, call_id):
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioRestException

        try:
            client = Client(self.account_sid, self.auth_token)
            call = client.calls.create(
                to=agent_number,
                from_=self.from_number,
                twiml=f'<Response><Dial callerId="{self.from_number}">{customer_number}</Dial></Response>'
            )
            return CallProviderResult(ok=True, call_sid=call.sid)
        except TwilioRestException as e:
            return CallProviderResult(ok=False, error=e.msg)
        except Exception as e:
            return CallProviderResult(ok=False, error=str(e))


class ExotelProvider(CallProvider):
    """Indian multi-agent dialer with call recording built into the platform - preferred over
    Twilio whenever both happen to be configured (see get_cloud_calling_provider), since it
    needs no separate DLT/SMS overhead for an Indian number."""
    name = "exotel"

    def __init__(self):
        self.sid = os.getenv("EXOTEL_SID")
        self.api_key = os.getenv("EXOTEL_API_KEY")
        self.api_token = os.getenv("EXOTEL_API_TOKEN")
        self.caller_id = os.getenv("EXOTEL_CALLER_ID")
        self.subdomain = os.getenv("EXOTEL_SUBDOMAIN", "api.exotel.com")
        self.callback_base = os.getenv("EXOTEL_STATUS_CALLBACK_BASE_URL")

    def is_configured(self) -> bool:
        return bool(self.sid and self.api_key and self.api_token and self.caller_id)

    def place_call(self, agent_number, customer_number, call_id):
        import requests

        payload = {
            "From": agent_number,
            "To": customer_number,
            "CallerId": self.caller_id,
            "CallType": "trans",
            "Record": "true",
            "CustomField": str(call_id),
        }
        if self.callback_base:
            payload["StatusCallback"] = f"{self.callback_base.rstrip('/')}/api/webhooks/exotel/status"

        try:
            resp = requests.post(
                f"https://{self.subdomain}/v1/Accounts/{self.sid}/Calls/connect.json",
                data=payload,
                auth=(self.api_key, self.api_token),
                timeout=15,
            )
            body = resp.json()
            if resp.status_code >= 400:
                error_msg = (body.get("RestException") or {}).get("Message") or resp.text[:200]
                return CallProviderResult(ok=False, error=error_msg)
            call_sid = (body.get("Call") or {}).get("Sid")
            return CallProviderResult(ok=True, call_sid=call_sid)
        except Exception as e:
            return CallProviderResult(ok=False, error=str(e))


def get_cloud_calling_provider():
    """Returns the configured cloud telephony provider (Exotel preferred over Twilio), or
    None when neither is set - meaning dial_call should fall back to LocalTelProvider's
    behavior (a plain tel: link, the current Rs.0 setup)."""
    exotel = ExotelProvider()
    if exotel.is_configured():
        return exotel
    twilio = TwilioProvider()
    if twilio.is_configured():
        return twilio
    return None
