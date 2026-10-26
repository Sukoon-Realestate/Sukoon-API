"""Provisioned Test recipients, bound to an already reviewed owner profile.

This does not mark a profile ready or invent a provider onboarding decision.
Full recipient details come from secure deployment configuration and are sealed
in the instruction, never placed in public projections or operational cases.
"""

import base64
import hashlib
import json
import re
from cryptography.fernet import Fernet, MultiFernet, InvalidToken
from django.conf import settings
from . import paymob_payout_client as client
from .rental_phase2 import RentalConflict, fingerprint


def cipher():
    return MultiFernet(
        [
            Fernet(
                base64.urlsafe_b64encode(
                    hashlib.sha256(
                        ("sokoun-payout-recipient-v1:" + key).encode()
                    ).digest()
                )
            )
            for key in [
                settings.SECRET_KEY,
                *getattr(settings, "SECRET_KEY_FALLBACKS", []),
            ]
        ]
    )


def seal(recipient):
    return cipher().encrypt(json.dumps(recipient, sort_keys=True).encode()).decode()


def unseal(item):
    try:
        value = json.loads(cipher().decrypt(item.recipient_ciphertext.encode()))
        if not isinstance(value, dict) or fingerprint(value) != item.recipient_digest:
            raise ValueError()
        return value
    except (InvalidToken, ValueError, TypeError):
        raise client.PayoutUnavailable() from None


def for_profile(profile):
    configured = getattr(settings, "PAYMOB_PAYOUTS_BENEFICIARIES", {}).get(
        profile.provider_account_id
    )
    if (
        profile.provider != client.PROVIDER
        or not profile.payout_ready
        or profile.status != "ready"
        or not isinstance(configured, dict)
        or configured.get("profile_id") != str(profile.id)
        or configured.get("profile_revision") != profile.revision
        or not configured.get("verification_reference")
    ):
        raise RentalConflict(
            "The staging beneficiary needs verified provisioning.",
            code="beneficiary_unavailable",
        )
    recipient = recipient_from_configuration(configured)
    from .beneficiary_details import matches_submission

    confirmed = (
        profile.beneficiary_submissions.filter(status="confirmed")
        .order_by("-revision")
        .first()
    )
    if confirmed and not matches_submission(confirmed, configured, recipient):
        raise RentalConflict(
            "The configured recipient differs from the owner's confirmed details.",
            code="beneficiary_changed",
        )
    account = recipient.get("msisdn") or recipient.get("bank_card_number")
    masked = profile.masked_beneficiary
    if (
        not isinstance(masked, dict)
        or str(masked.get("account_last4") or masked.get("last4") or "") != account[-4:]
    ):
        raise RentalConflict(
            "Review the staging recipient against the beneficiary profile.",
            code="beneficiary_changed",
        )
    return recipient


def recipient_from_configuration(configured):
    """Validate an already provisioned target without granting profile readiness."""
    issuer = configured.get("issuer")
    fields = {"issuer"}
    if issuer in client.WALLETS:
        fields.add("msisdn")
        if not re.fullmatch(r"01[0125][0-9]{8}", str(configured.get("msisdn", ""))):
            raise client.PayoutUnavailable()
        account = configured["msisdn"]
        if issuer in {"orange", "bank_wallet"}:
            fields.add("full_name")
    elif issuer in client.BANKS:
        fields.update(
            {"bank_card_number", "bank_code", "full_name", "bank_transaction_type"}
        )
        account = str(configured.get("bank_card_number", ""))
        if (
            not re.fullmatch(r"[A-Z0-9]{6,34}", account)
            or configured.get("bank_transaction_type") != "cash_transfer"
        ):
            raise client.PayoutUnavailable()
    else:
        raise client.PayoutUnavailable()
    recipient = {key: configured.get(key) for key in fields}
    if any(
        not isinstance(value, str) or not value.strip() or len(value) > 200
        for value in recipient.values()
    ):
        raise client.PayoutUnavailable()
    if not client.ready(issuer, submission=True):
        raise client.PayoutUnavailable()
    return recipient
