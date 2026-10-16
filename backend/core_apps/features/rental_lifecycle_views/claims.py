from django.shortcuts import get_object_or_404
from django.utils import timezone
from core_apps.users.models import User
from core_apps.properties.models import Property
from core_apps.admin_api.models import KYCSubmission
from ..models import RentalVerificationClaim
from ..rental_lifecycle_serializers import ClaimBody, ReasonBody
from ..services.rental_lifecycle.claims import record_claim, claim_payload
from ..services.rental_lifecycle.common import audit, require_staff, require_revision
from .common import endpoint, validated, mutate


@endpoint(["POST"])
def verification_claims(request):
    data = validated(ClaimBody, request.data)

    def authorize():
        require_staff(
            request.user,
            (
                {"kyc_reviewer"}
                if data["subject_kind"] == "identity"
                else {"property_reviewer"}
            ),
        )
        return request.user

    def execute(actor):
        subject = get_object_or_404(User, id=data["subject_user_id"])
        prop = (
            get_object_or_404(
                Property.objects.select_for_update(), id=data["property_id"]
            )
            if data.get("property_id")
            else None
        )
        kyc = (
            get_object_or_404(KYCSubmission, id=data["kyc_submission_id"])
            if data.get("kyc_submission_id")
            else None
        )
        item = record_claim(actor, subject, data, prop=prop, kyc=kyc)
        return item, {**claim_payload(item), "revision": item.revision}, 201

    return mutate(request, "verification_claim.create", authorize, execute)


@endpoint(["POST"])
def revoke_claim(request, claim_id):
    data = validated(ReasonBody, request.data)

    def authorize():
        item = get_object_or_404(
            RentalVerificationClaim.objects.select_for_update(), id=claim_id
        )
        require_staff(
            request.user,
            (
                {"kyc_reviewer"}
                if item.subject_kind in {"identity", "student_enrollment"}
                else {"property_reviewer"}
            ),
        )
        return item

    def execute(item):
        require_revision(item, data["expected_revision"])
        item.revoked_at = timezone.now()
        item.revision += 1
        item.save()
        audit(item, request.user, "verification.revoked", data.get("reason", ""))
        return (
            item,
            {"id": str(item.id), "revision": item.revision, "status": "revoked"},
            200,
        )

    return mutate(request, f"verification_claim.revoke.{claim_id}", authorize, execute)
