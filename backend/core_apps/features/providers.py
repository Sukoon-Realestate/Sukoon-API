import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


@dataclass(frozen=True)
class HostedProviderSession:
    provider_session_id: str
    hosted_url: str


@dataclass(frozen=True)
class GeneratedRentalDocument:
    document_id: uuid.UUID
    digest: str


class FakeRentalProvider:
    name = "fake"

    def __init__(self):
        if getattr(settings, "RENTAL_RUNTIME_ENVIRONMENT", "production") not in {
            "development",
            "test",
        }:
            raise ImproperlyConfigured(
                "The fake rental provider is forbidden outside development and tests."
            )

    def create_onboarding_session(self, profile_id, request_key):
        session_id = uuid.uuid5(uuid.NAMESPACE_URL, f"onboarding:{request_key}")
        return HostedProviderSession(
            provider_session_id=str(session_id),
            hosted_url=(
                "https://fake-rental-provider.test/onboarding/"
                f"{profile_id}/{session_id}"
            ),
        )

    def generate_agreement(self, lease_id, revision, terms):
        canonical = json.dumps(
            {"lease_id": str(lease_id), "revision": revision, "terms": terms},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return GeneratedRentalDocument(
            document_id=uuid.uuid5(
                uuid.NAMESPACE_URL, f"agreement:{lease_id}:{revision}"
            ),
            digest=hashlib.sha256(canonical).hexdigest(),
        )

    def create_signing_session(self, lease_id, signer_id, request_key):
        session_id = uuid.uuid5(
            uuid.NAMESPACE_URL, f"signing:{lease_id}:{signer_id}:{request_key}"
        )
        return HostedProviderSession(
            provider_session_id=str(session_id),
            hosted_url=f"https://fake-rental-provider.test/signing/{session_id}",
        )

    def create_checkout_session(self, attempt_id, request_key):
        session_id = uuid.uuid5(
            uuid.NAMESPACE_URL, f"checkout:{attempt_id}:{request_key}"
        )
        return HostedProviderSession(
            provider_session_id=str(session_id),
            hosted_url=f"https://fake-rental-provider.test/checkout/{session_id}",
        )

    def store_private_evidence(self, lease_id, evidence_id, content):
        return f"rental-evidence/{lease_id}/{evidence_id}/{hashlib.sha256(content).hexdigest()}"

    def scan_evidence(self, content):
        return b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" not in content

    def create_private_download(self, evidence_id, expires_at):
        token = hmac.new(
            settings.RENTAL_PROVIDER_WEBHOOK_SECRET.encode(),
            f"evidence:{evidence_id}:{expires_at.isoformat()}".encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"https://fake-rental-provider.test/private/evidence/{evidence_id}?token={token}"

    def execute_payout(self, payout_id, request_key):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"payout:{payout_id}:{request_key}"))

    def execute_refund(self, refund_id, request_key):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"refund:{refund_id}:{request_key}"))


def fake_provider_available():
    return bool(
        getattr(settings, "RENTAL_PROVIDER_BACKEND", "disabled") == "fake"
        and getattr(settings, "RENTAL_FAKE_PROVIDER_ALLOWED", False)
        and getattr(settings, "RENTAL_RUNTIME_ENVIRONMENT", "production")
        in {"development", "test"}
    )


def get_rental_provider():
    backend = getattr(settings, "RENTAL_PROVIDER_BACKEND", "disabled")
    if backend == "fake":
        return FakeRentalProvider()
    raise ImproperlyConfigured("No production rental provider is configured.")


def sign_fake_webhook(payload):
    secret = settings.RENTAL_PROVIDER_WEBHOOK_SECRET.encode()
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(secret, body, hashlib.sha256).hexdigest()


def verify_fake_webhook(payload, signature):
    expected = sign_fake_webhook(payload)
    return hmac.compare_digest(expected, signature or "")
