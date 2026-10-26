"""SignWell Test transport. No live, email delivery, redirects or implicit retries."""

import base64
import hashlib
import hmac
import uuid
from urllib.parse import urlsplit
import requests
from django.conf import settings

BASE = "https://www.signwell.com/api/v1/documents"
MAX_BYTES = 15 * 1024 * 1024


class SigningTransportError(Exception):
    def __init__(self, code, *, uncertain=False):
        self.code, self.uncertain = code, uncertain
        super().__init__(code)


def ready():
    return bool(
        getattr(settings, "SIGNWELL_TEST_ENABLED", False)
        and getattr(settings, "SIGNWELL_API_KEY", "")
        and getattr(settings, "SIGNWELL_WEBHOOK_ID", "")
        and getattr(settings, "RENTAL_RUNTIME_ENVIRONMENT", "production")
        in {"test", "development", "staging"}
    )


def verify_event(payload):
    # SignWell authenticates event type/time, not the object body. Authenticated
    # GET still verifies every document fact before any business transition.
    try:
        event = payload["event"]
        kind, timestamp, signature = event["type"], event["time"], event["hash"]
        if (
            not isinstance(kind, str)
            or len(kind) > 80
            or not isinstance(timestamp, int)
            or isinstance(timestamp, bool)
            or not isinstance(signature, str)
            or len(signature) != 64
        ):
            return False
        key = getattr(settings, "SIGNWELL_WEBHOOK_ID", "")
        expected = hmac.new(
            key.encode(), f"{kind}@{timestamp}".encode(), hashlib.sha256
        ).hexdigest()
        return bool(key) and hmac.compare_digest(signature, expected)
    except (KeyError, TypeError):
        return False


def _request(method, path="", *, payload=None, pdf=False):
    if not ready():
        raise SigningTransportError("signing_provider_unavailable")
    try:
        with requests.request(
            method,
            BASE + path,
            headers={
                "X-Api-Key": settings.SIGNWELL_API_KEY,
                "X-TestMode-Enabled": "true",
                "Accept": "application/pdf" if pdf else "application/json",
            },
            json=payload,
            timeout=(5, 30),
            allow_redirects=False,
            stream=True,
        ) as response:
            if response.status_code not in {200, 201}:
                if pdf and response.status_code == 400:
                    raise SigningTransportError("signed_pdf_processing")
                raise SigningTransportError(
                    (
                        f"signing_provider_http_{response.status_code}"
                        if 400 <= response.status_code < 500
                        else "signing_provider_unknown"
                    ),
                    uncertain=method == "POST"
                    and response.status_code not in {400, 401, 403, 422, 429},
                )
            chunks, size = [], 0
            for chunk in response.iter_content(64 * 1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise SigningTransportError(
                        "signing_response_too_large", uncertain=method == "POST"
                    )
                chunks.append(chunk)
            content = b"".join(chunks)
            if pdf:
                if not content.startswith(b"%PDF-"):
                    raise SigningTransportError("signed_pdf_invalid")
                return content
            import json

            result = json.loads(content)
            if not isinstance(result, dict):
                raise ValueError()
            return result
    except (requests.RequestException, ValueError, UnicodeError):
        raise SigningTransportError(
            "signing_provider_unknown", uncertain=method == "POST"
        ) from None


def create(document):
    return _request(
        "POST",
        payload={
            "test_mode": True,
            "name": f"Sokoun {document.id}",
            "files": [
                {
                    "name": "agreement.html",
                    "file_base64": base64.b64encode(
                        bytes(document.source_content)
                    ).decode("ascii"),
                }
            ],
            "recipients": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "email": row["email"],
                    "send_email": False,
                }
                for row in document.recipients
            ],
            "embedded_signing": True,
            "embedded_signing_notifications": False,
            "reminders": False,
            "with_signature_page": True,
            "allow_reassign": False,
            "language": "ar",
            "metadata": {
                "sokoun_document_id": str(document.id),
                "sokoun_source_hash": document.source_hash,
            },
        },
    )


def retrieve(identity):
    return _request("GET", "/" + str(uuid.UUID(str(identity))))


def completed_pdf(identity):
    return _request(
        "GET",
        "/"
        + str(uuid.UUID(str(identity)))
        + "/completed_pdf?url_only=false&audit_page=true&file_format=pdf",
        pdf=True,
    )


def verified(document, result):
    """A callback is only a hint; authenticated provider reads carry authority."""
    try:
        identity = uuid.UUID(str(result["id"]))
        metadata = result["metadata"]
        rows = result["recipients"]
        expected = {row["id"]: row["email"].casefold() for row in document.recipients}
        actual = {str(row["id"]): row["email"].casefold() for row in rows}
        valid = (
            result.get("test_mode") is True
            and metadata.get("sokoun_document_id") == str(document.id)
            and metadata.get("sokoun_source_hash") == document.source_hash
            and actual == expected
            and len(rows) == len(expected)
            and (
                not document.provider_document_id
                or identity == document.provider_document_id
            )
        )
        if not valid:
            raise ValueError()
        for row in rows:
            url = row.get("embedded_signing_url")
            if url:
                parsed = urlsplit(url)
                if (
                    parsed.scheme != "https"
                    or parsed.hostname != "www.signwell.com"
                    or parsed.port not in {None, 443}
                    or parsed.username
                    or parsed.password
                ):
                    raise ValueError()
        return identity
    except (KeyError, TypeError, ValueError, AttributeError):
        raise SigningTransportError("signing_document_mismatch") from None
