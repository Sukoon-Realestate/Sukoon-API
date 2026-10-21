"""Encryption at rest for transient inputs and case evidence; supports key rotation."""

import base64
import hashlib
import json
from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings


def cipher():
    keys = [settings.SECRET_KEY, *getattr(settings, "SECRET_KEY_FALLBACKS", [])]
    return MultiFernet(
        [
            Fernet(
                base64.urlsafe_b64encode(
                    hashlib.sha256(("sokoun-chat-evidence-v1:" + key).encode()).digest()
                )
            )
            for key in keys
        ]
    )


def seal(value):
    return (
        cipher()
        .encrypt(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode())
        .decode()
    )


def unseal(value):
    return json.loads(cipher().decrypt(value.encode())) if value else {}
