"""Private owner input, separate from verified provider recipients and payouts."""

from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from core_apps.users.models import User
from core_apps.users.services import sensitive_actions, totp
from ..models import OwnerPaymentProfile, OwnerBeneficiarySubmission, RentalAuditEvent
from ..planning_models import PlanningEvent
from ..providers import require_verified_rental_account
from . import paymob_payout_targets as targets
from .beneficiary_confirmation import verification_ready
from .rental_phase2 import (
    RentalConflict,
    fingerprint,
    get_or_create_owner_profile,
    replay_operation,
    remember_mutation,
)


def latest(profile):
    return profile.beneficiary_submissions.order_by("-revision").first()


def projection(item):
    if not item:
        return None
    return {
        "id": str(item.id),
        "profile_id": str(item.profile.id),
        "revision": item.revision,
        "status": item.status,
        "channel": item.channel,
        "beneficiary_name": item.beneficiary_name,
        "bank_name": item.bank_name,
        "masked_account": "•••• " + item.account_last4,
        "created_at": item.created_at.isoformat(),
    }


def can_submit(profile, user):
    return bool(
        user
        and user.is_active
        and user.is_verified
        and profile.owner_id == user.pk
        and not user.sensitive_actions_frozen
        and not totp.pending_recovery(user)
        and verification_ready(user)
    )


def matches_prepared(profile, configured, recipient):
    item = latest(profile)
    if not item:
        return True  # Preserve existing, independently provisioned beneficiaries.
    return item.status == "pending_verification" and matches_submission(
        item, configured, recipient
    )


def matches_submission(item, configured, recipient):
    if (
        configured.get("submission_id") != str(item.id)
        or configured.get("submission_digest") != item.recipient_digest
    ):
        return False
    original = targets.unseal(item)
    return all(
        (configured.get(key) if key == "full_name" else recipient.get(key)) == value
        for key, value in original.items()
        if key != "bank_name"
    )


@transaction.atomic
def submit(request, data):
    actor = User.objects.select_for_update().get(pk=request.user.pk)
    from core_apps.users.services.sessions import validate_session

    validate_session(actor, request.auth or {})
    request.user = actor
    require_verified_rental_account(actor)
    profile = get_or_create_owner_profile(actor)
    profile = OwnerPaymentProfile.objects.select_for_update().get(pk=profile.pk)
    operation = "owner_beneficiary.submit"
    replay = replay_operation(actor, operation, data["request_key"], request.data)
    if replay:
        return replay
    if not can_submit(profile, actor):
        raise PermissionDenied(
            "Complete account verification and review account security before changing beneficiary details."
        )
    current = latest(profile)
    revision = current.revision if current else 0
    if (
        profile.revision != data["expected_revision"]
        or revision != data["details_revision"]
    ):
        raise RentalConflict(
            "Beneficiary details changed. Refresh and review the current version.",
            code="stale_revision",
        )
    if "rental-policy-v1" not in data["accepted_policy_versions"]:
        raise ValidationError(
            {"accepted_policy_versions": "Review the current rental policy."}
        )
    sensitive_actions.consume(
        request,
        action="beneficiary.onboarding",
        resource_id=profile.id,
        revision=profile.revision,
        payload=request.data,
    )
    recipient = {"issuer": data["channel"], "full_name": data["beneficiary_name"]}
    if data["channel"] == "bank_card":
        recipient.update(
            bank_card_number=data["account_number"], bank_name=data["bank_name"]
        )
    else:
        recipient["msisdn"] = data["account_number"]
    # Only unverified proposals are superseded. Existing confirmed payout targets,
    # recipient snapshots and unknown provider attempts are never rewritten here.
    OwnerBeneficiarySubmission.objects.filter(
        profile=profile, status="pending_verification"
    ).update(status="superseded")
    item = OwnerBeneficiarySubmission.objects.create(
        profile=profile,
        revision=revision + 1,
        channel=data["channel"],
        recipient_ciphertext=targets.seal(recipient),
        recipient_digest=fingerprint(recipient),
        beneficiary_name=data["beneficiary_name"],
        bank_name=data.get("bank_name", ""),
        account_last4=data["account_number"][-4:],
        accepted_policy_versions=data["accepted_policy_versions"],
    )
    RentalAuditEvent.objects.create(
        actor=actor,
        subject_kind="ownerpaymentprofile",
        subject_id=profile.id,
        subject_revision=profile.revision,
        action="beneficiary_details_submitted",
        metadata={"submission_id": str(item.id), "details_revision": item.revision},
    )
    PlanningEvent.objects.get_or_create(
        recipient=actor,
        event_key=f"beneficiary-details:{item.id}",
        defaults={
            "destination": {
                "action_type": "open_owner_payment_profile",
                "event_kind": "beneficiary_updated",
                "target_id": str(profile.id),
                "workspace": "owner",
                "revision": profile.revision,
                "submission_id": str(item.id),
                "details_revision": item.revision,
            }
        },
    )
    return (
        remember_mutation(
            user=actor,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=profile.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=projection(item),
            response_status=201,
        ),
        201,
    )
