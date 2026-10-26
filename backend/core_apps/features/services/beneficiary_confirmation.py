"""Owner consent for an independently provisioned staging beneficiary.

No bank verification, role grant, provider onboarding URL, or payout is invented.
The secure record must target the exact profile and its next revision.
"""

import hashlib
import hmac
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound
from core_apps.users.services import totp
from core_apps.users.models import TotpFactor
from ..models import OwnerPaymentProfile
from ..planning_models import PlanningEvent
from . import paymob_payout_client as client, paymob_payout_targets as targets
from .rental_phase2 import RentalConflict, fingerprint


def candidate(profile):
    from .beneficiary_details import latest, matches_prepared

    pending = latest(profile)
    # Older unprepared profiles copied the signing adapter name. It is not a
    # payout provider; only an independently verified recipient can replace it.
    providers = {"", client.PROVIDER}
    if not profile.payout_ready and profile.status in {"not_started", "pending"}:
        providers.add("signwell")
    if (
        profile.status not in {"not_started", "pending", "ready"}
        or profile.provider not in providers
    ):
        raise client.PayoutUnavailable()
    if profile.status == "ready" and (
        not pending or pending.status != "pending_verification"
    ):
        raise client.PayoutUnavailable()
    configured = getattr(settings, "PAYMOB_PAYOUTS_BENEFICIARIES", {})
    matches = [
        (identity, value)
        for identity, value in configured.items()
        if isinstance(value, dict)
        and value.get("profile_id") == str(profile.id)
        and type(value.get("profile_revision")) is int
        and value["profile_revision"] == profile.revision + 1
        and isinstance(value.get("verification_reference"), str)
        and value["verification_reference"].strip()
    ]
    if len(matches) != 1:
        raise client.PayoutUnavailable()
    identity, record = matches[0]
    if not isinstance(identity, str) or not identity.strip() or len(identity) > 120:
        raise client.PayoutUnavailable()
    recipient = targets.recipient_from_configuration(record)
    if not matches_prepared(profile, record, recipient):
        raise client.PayoutUnavailable()
    account = recipient.get("msisdn") or recipient.get("bank_card_number")
    public = {
        "digest": hmac.new(
            settings.SECRET_KEY.encode(),
            fingerprint(
                {
                    "profile_id": str(profile.id),
                    "revision": profile.revision,
                    "account": client.account_digest(),
                    "identity": identity,
                    "record": record,
                }
            ).encode(),
            hashlib.sha256,
        ).hexdigest(),
        "channel": recipient["issuer"],
        "masked_account": "•••• " + account[-4:],
        "beneficiary_name": recipient.get("full_name", ""),
    }
    return identity, recipient, public


def preview(profile, user):
    if not user or user.pk != profile.owner_id:
        return None
    try:
        return candidate(profile)[2]
    except (client.PayoutUnavailable, RentalConflict):
        return None


def can_confirm(profile, user):
    return bool(
        user
        and user.is_active
        and user.is_verified
        and user.pk == profile.owner_id
        and not user.sensitive_actions_frozen
        and not totp.pending_recovery(user)
        and verification_ready(user)
        and preview(profile, user)
    )


def verification_ready(user):
    if not totp.is_staff_account(user):
        return user.is_email_verified
    return (
        TotpFactor.objects.filter(user=user, confirmed_at__isnull=False)
        .exclude(secret_ciphertext="")
        .filter(Q(locked_until__isnull=True) | Q(locked_until__lte=timezone.now()))
        .exists()
    )


def record(profile):
    PlanningEvent.objects.get_or_create(
        recipient=profile.owner,
        event_key=f"beneficiary:{profile.id}:{profile.revision}",
        defaults={
            "destination": {
                "action_type": "open_owner_payment_profile",
                "event_kind": "beneficiary_updated",
                "target_id": str(profile.id),
                "workspace": "owner",
                "revision": profile.revision,
            }
        },
    )


def notification_copy(event):
    data = event.destination
    if (
        data.get("event_kind") != "beneficiary_updated"
        or data.get("workspace") != "owner"
        or not event.recipient.is_active
        or not OwnerPaymentProfile.objects.filter(
            id=data.get("target_id"), owner=event.recipient
        ).exists()
    ):
        raise NotFound()
    return {
        "title": "تحديث حساب المستفيد / Beneficiary update",
        "body": "راجع الحالة الحالية لحساب المستفيد. / Review the current beneficiary status.",
    }
