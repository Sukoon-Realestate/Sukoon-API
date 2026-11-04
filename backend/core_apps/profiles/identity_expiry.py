"""Private national-card expiry metadata and version-scoped reminder authority."""

from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied

from core_apps.common.idempotency import fingerprint, IdempotencyConflict
from core_apps.users.models import User
from .identity_media import reference
from .models import IdentityDocumentExpiry, Profile

EVENT_KIND = "identity_document_expiry"
REMINDER_DAYS = (30, 7, 1)


def card_version(profile):
    if not all((profile.national_id, profile.id_face, profile.id_back)):
        return None
    if not profile.kyc_submissions.exists():
        return None
    return fingerprint({"number": profile.national_id,
                        "front": reference(profile.id_face), "back": reference(profile.id_back)})


def locked_profile(user):
    current = User.objects.select_for_update().get(pk=user.pk)
    if not current.is_active or current.closed_at or current.security_epoch != user.security_epoch:
        raise PermissionDenied("Account authority changed. Sign in again.")
    return Profile.objects.select_for_update().get(user=current)


def projection(profile):
    version = card_version(profile)
    row = IdentityDocumentExpiry.objects.filter(profile=profile, document_version=version).first() if version else None
    return {"document_version": version, "revision": row.revision if row else 0,
            "expires_on": row.expires_on.isoformat() if row and row.expires_on else None,
            "source": "user_entered" if row and row.expires_on else "unknown",
            "reminder_days": row.reminder_days if row else [], "allowed_reminder_days": list(REMINDER_DAYS)}


def update(profile, data):
    version = card_version(profile)
    if not version or version != data["document_version"]:
        raise IdempotencyConflict("Identity card changed. Review the current card before saving.")
    row = IdentityDocumentExpiry.objects.filter(profile=profile, document_version=version).first()
    if data["expected_revision"] != (row.revision if row else 0):
        raise IdempotencyConflict("Expiry information changed. Refresh before saving.")
    if row is None:
        row = IdentityDocumentExpiry(profile=profile, document_version=version)
    else:
        row.revision += 1
    row.expires_on = data["expires_on"]
    row.reminder_days = sorted(data["reminder_days"], reverse=True)
    row.save()
    return projection(profile)


def record_reminders(*, today=None):
    """Exact civil-day thresholds; retries use the durable, deduplicated outbox."""
    from core_apps.features.planning_models import PlanningEvent

    today = today or timezone.now().astimezone(ZoneInfo("Africa/Cairo")).date()
    count = 0
    rows = IdentityDocumentExpiry.objects.filter(
        expires_on__in=[today + timedelta(days=day) for day in REMINDER_DAYS]
    ).values_list("pk", "profile__user_id")
    for pk, user_pk in rows.iterator():
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user_pk)
            if not user.is_active or user.closed_at:
                continue
            profile = Profile.objects.select_for_update().get(user=user)
            row = IdentityDocumentExpiry.objects.get(pk=pk)
            days = (row.expires_on - today).days if row.expires_on else None
            if days not in REMINDER_DAYS or days not in row.reminder_days or card_version(profile) != row.document_version:
                continue
            _, created = PlanningEvent.objects.get_or_create(
                recipient=user, event_key=f"identity-expiry:{row.id}:{row.expires_on}:{days}",
                defaults={"destination": {"event_kind": EVENT_KIND, "action_type": "open_identity_expiry",
                    "expiry_id": str(row.id), "document_version": row.document_version,
                    "expires_on": row.expires_on.isoformat(), "reminder_days": days}},
            )
            count += int(created)
    return count


def event_copy(event):
    """Called both before inbox creation and on every push retry."""
    destination = event.destination
    user = User.objects.get(pk=event.recipient_id)
    if not user.is_active or user.closed_at:
        raise NotFound()
    row = IdentityDocumentExpiry.objects.select_related("profile").filter(
        id=destination.get("expiry_id"), profile__user=user,
        document_version=destination.get("document_version"),
    ).first()
    if (row is None or not row.expires_on or row.expires_on.isoformat() != destination.get("expires_on")
            or destination.get("reminder_days") not in row.reminder_days
            or card_version(row.profile) != row.document_version):
        raise NotFound()
    if timezone.now().astimezone(ZoneInfo("Africa/Cairo")).date() > row.expires_on:
        raise NotFound()
    return {"title": "Identity document reminder", "body": "Open your private identity settings to review the expiry date you entered.",
            "category": "identity_expiry", "notification_type": "general"}
