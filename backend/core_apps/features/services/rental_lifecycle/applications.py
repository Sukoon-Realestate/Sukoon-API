"""Private application versions and deliberately scoped, revocable sharing."""

from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from ...models import (
    ApplicationProfile,
    ApplicationProfileVersion,
    ApplicationAccessGrant,
)
from ..rental_phase2 import RentalConflict, fingerprint
from .common import audit, lifecycle_policy, require_revision


FIELDS = ("desired_start", "months", "occupants", "introduction")
CATEGORIES = {
    "rental_preferences": ("desired_start", "months", "occupants"),
    "introduction": ("introduction",),
}


def profile_payload(profile, user):
    values = {key: getattr(profile, key, None) for key in FIELDS}
    if values["desired_start"]:
        values["desired_start"] = values["desired_start"].isoformat()
    values["introduction"] = values["introduction"] or ""
    version = profile.versions.order_by("-revision").first() if profile else None
    return {
        "id": str(profile.id if profile else user.id),
        "revision": profile.revision if profile else 0,
        **values,
        "latest_version_id": str(version.id) if version else None,
        "allowed_actions": ["save_application", "freeze_application"],
        "blocking_reasons": [],
    }


def save_profile(user, data):
    profile = (
        ApplicationProfile.objects.select_for_update().filter(applicant=user).first()
    )
    revision = profile.revision if profile else 0
    if data["expected_revision"] != revision:
        raise RentalConflict(
            "Review the current application profile.", code="stale_revision"
        )
    if data.get("desired_start") and data["desired_start"] < timezone.localdate():
        raise ValidationError({"desired_start": "Cannot be in the past."})
    if profile is None:
        profile = ApplicationProfile(applicant=user)
    else:
        profile.revision += 1
    for field in FIELDS:
        if field in data:
            setattr(profile, field, data[field])
    profile.save()
    audit(profile, user, "application.saved")
    return profile


def freeze_profile(profile, user, data):
    require_revision(profile, data["expected_revision"])
    snapshot = {key: profile_payload(profile, user)[key] for key in FIELDS}
    if not all(snapshot[key] for key in ("desired_start", "months", "occupants")):
        raise ValidationError(
            {"profile": "Start date, duration and occupant count are required."}
        )
    version, _ = ApplicationProfileVersion.objects.get_or_create(
        profile=profile,
        revision=profile.revision,
        defaults={"snapshot": snapshot, "digest": fingerprint(snapshot)},
    )
    audit(version, user, "application.frozen")
    return version


def version_payload(version):
    return {
        "id": str(version.id),
        "revision": version.revision,
        "digest": version.digest,
        "snapshot": version.snapshot,
        "allowed_actions": ["share_application"],
        "blocking_reasons": [],
    }


def share_review(version, prop, categories, expires_at):
    if (
        not categories
        or len(categories) != len(set(categories))
        or set(categories) - set(CATEGORIES)
    ):
        raise ValidationError(
            {"categories": "Select supported application categories."}
        )
    if prop.owner_id == version.profile.applicant_id:
        raise ValidationError({"property_id": "Choose another owner's property."})
    review = {
        "version_id": str(version.id),
        "version_digest": version.digest,
        "recipient_id": str(prop.owner.id),
        "recipient_name": prop.owner.get_full_name,
        "property_id": str(prop.id),
        "purpose": "rental_application",
        "categories": sorted(categories),
        "expires_at": expires_at.isoformat(),
    }
    return {
        **review,
        "revision": version.revision,
        "consent_digest": fingerprint(review),
        "snapshot": {
            key: version.snapshot[key]
            for category in categories
            for key in CATEGORIES[category]
        },
    }


def create_share(version, user, prop, data):
    _, rules = lifecycle_policy("application_sharing")
    if (
        not timezone.now()
        < data["expires_at"]
        <= timezone.now() + timedelta(days=rules["share_days"])
    ):
        raise ValidationError(
            {"expires_at": "The share expiry exceeds the configured access window."}
        )
    review = share_review(version, prop, data["categories"], data["expires_at"])
    if review["consent_digest"] != data["consent_digest"]:
        raise RentalConflict(
            "Review the recipient and exact shared fields again.",
            code="document_changed",
        )
    grant = ApplicationAccessGrant.objects.create(
        version=version,
        applicant=user,
        recipient=prop.owner,
        property=prop,
        categories=review["categories"],
        consent_digest=review["consent_digest"],
        expires_at=data["expires_at"],
    )
    audit(
        grant,
        user,
        "application.shared",
        metadata={"version_id": str(version.id), "categories": grant.categories},
    )
    return grant


def share_payload(grant, user):
    current = (
        grant.revoked_at is None
        and grant.expires_at > timezone.now()
        and grant.property.owner_id == grant.recipient_id
    )
    if user.pk != grant.applicant_id and (user.pk != grant.recipient_id or not current):
        raise NotFound()
    return {
        "id": str(grant.id),
        "revision": grant.revision,
        "version_id": str(grant.version.id),
        "recipient_id": str(grant.recipient.id),
        "recipient_name": grant.recipient.get_full_name,
        "property_id": str(grant.property.id),
        "purpose": grant.purpose,
        "categories": grant.categories,
        "expires_at": grant.expires_at.isoformat(),
        "status": (
            "active" if current else ("revoked" if grant.revoked_at else "expired")
        ),
        "snapshot": (
            {
                key: grant.version.snapshot[key]
                for category in grant.categories
                for key in CATEGORIES[category]
            }
            if current
            else {}
        ),
        "allowed_actions": (
            ["revoke_application_share"]
            if current and user.pk == grant.applicant_id
            else []
        ),
        "blocking_reasons": [],
    }


def valid_interest_share(grant_id, user, prop):
    grant = ApplicationAccessGrant.objects.filter(
        id=grant_id,
        applicant=user,
        property=prop,
        recipient=prop.owner,
        revoked_at__isnull=True,
        expires_at__gt=timezone.now(),
    ).first()
    if not grant:
        raise NotFound()
    return grant
