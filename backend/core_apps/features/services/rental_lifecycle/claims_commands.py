"""Named claims commands; adapters supply typed data and current actor."""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from core_apps.users.models import User
from core_apps.properties.models import Property
from core_apps.admin_api.models import KYCSubmission
from core_apps.features.models import RentalVerificationClaim
from core_apps.features.services.rental_lifecycle.claims import (
    record_claim,
    claim_payload,
)
from core_apps.features.services.rental_lifecycle.common import (
    audit,
    require_staff,
    require_revision,
)


def verification_claims_post_authorize(*, actor, data):
    require_staff(
        actor,
        (
            {"kyc_reviewer"}
            if data["subject_kind"] == "identity"
            else {"property_reviewer"}
        ),
    )
    return actor


def verification_claims_post_execute(actor, *, data):
    subject = get_object_or_404(User, id=data["subject_user_id"])
    prop = (
        get_object_or_404(Property.objects.select_for_update(), id=data["property_id"])
        if data.get("property_id")
        else None
    )
    kyc = (
        get_object_or_404(KYCSubmission, id=data["kyc_submission_id"])
        if data.get("kyc_submission_id")
        else None
    )
    item = record_claim(actor, subject, data, prop=prop, kyc=kyc)
    return (item, {**claim_payload(item), "revision": item.revision}, 201)


def revoke_claim_post_authorize(*, actor, claim_id):
    item = get_object_or_404(
        RentalVerificationClaim.objects.select_for_update(), id=claim_id
    )
    require_staff(
        actor,
        (
            {"kyc_reviewer"}
            if item.subject_kind in {"identity", "student_enrollment"}
            else {"property_reviewer"}
        ),
    )
    return item


def revoke_claim_post_execute(item, *, actor, data):
    require_revision(item, data["expected_revision"])
    item.revoked_at = timezone.now()
    item.revision += 1
    item.save()
    audit(item, actor, "verification.revoked", data.get("reason", ""))
    return (
        item,
        {"id": str(item.id), "revision": item.revision, "status": "revoked"},
        200,
    )
