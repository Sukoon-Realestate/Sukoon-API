"""Scoped public assertions over existing approved review records."""

from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ...models import RentalVerificationClaim
from .common import audit, require_staff


def current_claims(queryset):
    return queryset.filter(
        revoked_at__isnull=True, checked_at__lte=timezone.now()
    ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))


def claim_current(claim):
    if (
        claim.revoked_at
        or claim.checked_at > timezone.now()
        or (claim.expires_at and claim.expires_at <= timezone.now())
    ):
        return False
    if claim.subject_kind == "identity":
        return bool(
            claim.kyc_submission
            and claim.kyc_submission.status == "approved"
            and claim.subject_user.is_active
        )
    return bool(
        claim.property
        and claim.property.owner_id == claim.subject_user_id
        and claim.property.status == "verified"
        and claim.property.is_verified
        and (
            claim.subject_kind != "property_authority"
            or claim.property.is_ownership_verified
        )
    )


def claim_payload(claim):
    return {
        "id": str(claim.id),
        "subject_kind": claim.subject_kind,
        "claim_code": claim.claim_code,
        "public_wording": claim.public_wording,
        "checked_at": claim.checked_at.isoformat(),
        "expires_at": claim.expires_at.isoformat() if claim.expires_at else None,
    }


def record_claim(actor, subject, data, *, prop=None, kyc=None):
    kind = data["subject_kind"]
    require_staff(
        actor, {"kyc_reviewer"} if kind == "identity" else {"property_reviewer"}
    )
    if kind == "identity":
        if not kyc or kyc.status != "approved" or kyc.profile.user_id != subject.pk:
            raise ValidationError(
                {"kyc_submission_id": "An approved review for this person is required."}
            )
    elif (
        not prop
        or prop.owner_id != subject.pk
        or prop.status != "verified"
        or not prop.is_verified
        or (kind == "property_authority" and not prop.is_ownership_verified)
    ):
        raise ValidationError(
            {"property_id": "An approved current property review is required."}
        )
    if data.get("expires_at") and data["expires_at"] <= timezone.now():
        raise ValidationError({"expires_at": "Must be in the future."})
    claim = RentalVerificationClaim.objects.create(
        subject_kind=kind,
        subject_user=subject,
        property=prop,
        kyc_submission=kyc,
        claim_code=data["claim_code"],
        public_wording=data["public_wording"],
        reviewer=actor,
        evidence_reference=data["evidence_reference"],
        checked_at=timezone.now(),
        expires_at=data.get("expires_at"),
    )
    audit(claim, actor, "verification.claim_recorded")
    return claim
