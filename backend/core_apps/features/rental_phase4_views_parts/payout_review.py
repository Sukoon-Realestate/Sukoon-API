"""Review original instructions and explicitly renew an unsent approval."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from core_apps.users.models import User
from core_apps.users.services import sensitive_actions, totp
from ..models import OwnerPayable, OwnerPaymentProfile, PaymobPayout, PayoutAuditEvent
from ..pagination import FeaturePagination
from ..rental_serializers import OwnerPaymentProfileSerializer
from ..renderers import FeatureJsonRenderer
from ..services import (
    paymob_payout_client as client,
    paymob_payout_targets as targets,
    paymob_payouts,
)
from ..services.rental_phase2 import (
    RentalConflict,
    fingerprint,
    replay_operation,
    remember_mutation,
)
from ..services.rental_lifecycle.common import staff_role
from ..services.rental_lifecycle.provider_instructions import (
    validate_payout_instruction,
)
from .operations_execute_payout import _require_payout_role
from .handover_respond import payout_payload


def _reader(user):
    current = User.objects.get(pk=user.pk)
    if not staff_role(
        current,
        {
            StaffProfile.RoleName.PAYOUT_OPERATOR,
            StaffProfile.RoleName.PSP_RECONCILIATION,
        },
    ):
        raise PermissionDenied("A current payout review role is required.")
    return current


UNSENT_REVIEW = {
    "authorization_changed",
    "beneficiary_changed",
    "payout_held",
    "refund_pending",
}


def _details(item):
    from ..services.chargebacks.projection import payable_funding_sources

    profile = OwnerPaymentProfile.objects.filter(owner=item.payout.owner).first()
    return {
        "amount_minor": item.amount_minor,
        "currency": item.currency,
        "recipient_digest": item.recipient_digest,
        "instruction_reference": str(item.reference),
        "beneficiary_revision": profile.revision if profile else None,
        "beneficiary_account_digest": (
            fingerprint(profile.provider_account_id) if profile else None
        ),
        "funding_digest": fingerprint(
            [
                {
                    "id": str(payable.id),
                    "amount_minor": payable.net_minor,
                    "sources": sorted(
                        str(source.id) for source in payable_funding_sources(payable)
                    ),
                }
                for payable in item.payout.payables.order_by("pk")
            ]
        ),
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def payout_queue(request):
    _reader(request.user)
    paginator = FeaturePagination()
    query = (
        PaymobPayout.objects.filter(current=True)
        .select_related("payout__lease")
        .order_by("-created_at", "-pk")
    )
    page = paginator.paginate_queryset(query, request)
    return paginator.get_paginated_response(
        [
            {"resource": payout_payload(item.payout), "instruction_status": item.status}
            for item in page
        ]
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def payable_queue(request):
    current = _reader(request.user)
    paginator = FeaturePagination()
    query = (
        OwnerPayable.objects.filter(
            payout_status__in=["ready", "held", "pending_eligibility"]
        )
        .select_related("lease", "invoice")
        .order_by("-created_at", "-pk")
    )
    page = paginator.paginate_queryset(query, request)
    results = []
    for item in page:
        profile = OwnerPaymentProfile.objects.filter(
            owner_id=item.invoice.beneficiary_id or item.lease.owner_id
        ).first()
        ready = False
        if profile and profile.provider == client.PROVIDER:
            try:
                targets.for_profile(profile)
                ready = True
            except (client.PayoutUnavailable, RentalConflict):
                pass
        can_execute = (
            ready
            and item.payout_status == "ready"
            and staff_role(current, {StaffProfile.RoleName.PAYOUT_OPERATOR})
            and not current.sensitive_actions_frozen
            and not totp.pending_recovery(current)
        )
        reasons = list(item.blocking_reasons)
        if current.sensitive_actions_frozen or totp.pending_recovery(current):
            reasons.append(
                "الإجراءات الحساسة مقيدة. راجع أمان الحساب قبل اعتماد تحويل جديد."
            )
        results.append(
            {
                "id": str(item.id),
                "lease_id": str(item.lease.id),
                "invoice_id": str(item.invoice.id),
                "revision": item.revision,
                "amount": {
                    "amount_minor": item.net_minor,
                    "currency": "EGP",
                    "exponent": 2,
                },
                "status": item.payout_status,
                "blocking_reasons": reasons,
                "can_prepare": staff_role(
                    current, {StaffProfile.RoleName.PAYOUT_OPERATOR}
                ),
                "masked_beneficiary": (
                    OwnerPaymentProfileSerializer().get_masked_beneficiary(profile)
                    if profile
                    else ""
                ),
                "can_execute": can_execute,
                "provider_ready": ready,
            }
        )
    return paginator.get_paginated_response(results)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def payout_review(request, payout_id):
    current = _reader(request.user)
    item = get_object_or_404(
        PaymobPayout.objects.select_related("payout__lease"),
        payout__id=payout_id,
        current=True,
    )
    allowed = []
    restricted = current.sensitive_actions_frozen or totp.pending_recovery(current)
    if item.status in {"submitting", "unknown", "processing", "confirmed"}:
        allowed.append("reconcile")
    can_reauthorize = (
        staff_role(current, {StaffProfile.RoleName.PAYOUT_OPERATOR})
        and item.status == "held"
        and item.failure_code in UNSENT_REVIEW
        and item.submitted_at is None
    )
    can_retry = (
        staff_role(current, {StaffProfile.RoleName.PAYOUT_OPERATOR})
        and item.status == "failed"
        and bool(item.provider_transaction_id)
    )
    reauthorize_reason = ""
    if can_reauthorize or can_retry:
        if restricted:
            reauthorize_reason = "راجع أمان الحساب قبل اعتماد تحويل جديد."
        else:
            profile = OwnerPaymentProfile.objects.filter(
                owner=item.payout.owner
            ).first()
            try:
                if (
                    not profile
                    or fingerprint(targets.for_profile(profile))
                    != item.recipient_digest
                    or item.account_digest != client.account_digest()
                ):
                    raise client.PayoutUnavailable()
                if (
                    item.payout.amount_minor != item.amount_minor
                    or item.payout.currency != item.currency
                ):
                    raise RentalConflict(
                        "The original payout amount changed.", code="payout_changed"
                    )
                validate_payout_instruction(
                    item.payout,
                    profile_revision=profile.revision if can_reauthorize else None,
                    lock=False,
                )
            except (client.PayoutUnavailable, RentalConflict):
                reauthorize_reason = (
                    "راجع تجهيز القناة والمستفيد الأصلي والرصيد المحجوز قبل الاعتماد."
                )
            else:
                allowed.append("retry" if can_retry else "reauthorize")
    response = Response(
        {
            "resource": payout_payload(item.payout),
            "instruction_status": item.status,
            "provider_reference": item.provider_transaction_id,
            "allowed_actions": allowed,
            "can_reauthorize": can_reauthorize,
            "can_retry": can_retry,
            "reauthorize_reason": reauthorize_reason,
            "attempts": [
                {
                    "id": str(value.id),
                    "status": value.status,
                    "current": value.current,
                    "provider_reference": value.provider_transaction_id,
                    "created_at": value.created_at.isoformat(),
                    "retry_of": str(value.retry_of.id) if value.retry_of_id else None,
                }
                for value in item.payout.paymob_instructions.select_related(
                    "retry_of"
                ).order_by("created_at")
            ],
            "authorization_details": _details(item),
            "submitted_at": (
                item.submitted_at.isoformat() if item.submitted_at else None
            ),
            "confirmed_at": (
                item.confirmed_at.isoformat() if item.confirmed_at else None
            ),
        }
    )
    response["Cache-Control"] = "private, no-store"
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def payout_preview(request):
    _require_payout_role(request.user)
    ids = request.query_params.getlist("payable_id")
    import uuid

    try:
        identities = {uuid.UUID(value) for value in ids}
    except (ValueError, TypeError):
        raise ValidationError({"payable_id": "Use original payable UUIDs."}) from None
    if not identities or len(identities) > 100:
        raise ValidationError({"payable_id": "Select between 1 and 100 payables."})
    payables = list(
        OwnerPayable.objects.filter(id__in=identities).select_related(
            "lease", "invoice"
        )
    )
    if (
        len(payables) != len(identities)
        or len({value.lease_id for value in payables}) != 1
        or len(
            {value.invoice.beneficiary_id or value.lease.owner_id for value in payables}
        )
        != 1
    ):
        raise ValidationError(
            {"payable_id": "Select payables for one original lease and beneficiary."}
        )
    lease = payables[0].lease
    profile = get_object_or_404(
        OwnerPaymentProfile,
        owner_id=payables[0].invoice.beneficiary_id or lease.owner_id,
    )
    recipient = (
        targets.for_profile(profile) if profile.provider == client.PROVIDER else None
    )
    response = Response(
        {
            "resource_id": str(lease.id),
            "resource_revision": lease.revision,
            "masked_beneficiary": OwnerPaymentProfileSerializer().get_masked_beneficiary(
                profile
            ),
            "authorization_details": {
                "amount_minor": sum(value.net_minor for value in payables),
                "currency": "EGP",
                "beneficiary_revision": profile.revision,
                "beneficiary_account_digest": fingerprint(profile.provider_account_id),
                **({"recipient_digest": fingerprint(recipient)} if recipient else {}),
            },
        }
    )
    response["Cache-Control"] = "private, no-store"
    return response


def _approve_again(request, payout_id, *, retry=False):
    _require_payout_role(request.user)
    key = request.data.get("request_key")
    import uuid

    try:
        uuid.UUID(str(key))
    except (ValueError, TypeError):
        raise ValidationError(
            {"request_key": "A UUID request key is required."}
        ) from None
    operation = f"payout.{'retry' if retry else 'reauthorize'}.{payout_id}"
    with transaction.atomic():
        actor = _require_payout_role(request.user, lock=True)
        replay = replay_operation(actor, operation, key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        candidate = get_object_or_404(PaymobPayout, payout__id=payout_id, current=True)
        item, payout, _ = paymob_payouts._locked(candidate.pk)
        if request.data.get("expected_revision") != payout.revision:
            raise RentalConflict(
                "Refresh the original payout review.", code="stale_revision"
            )
        if (
            retry and (item.status != "failed" or not item.provider_transaction_id)
        ) or (
            not retry
            and (
                item.status != "held"
                or item.failure_code not in UNSENT_REVIEW
                or item.submitted_at is not None
            )
        ):
            raise RentalConflict(
                "This instruction cannot be submitted again.",
                code="reconciliation_required",
            )
        profile = OwnerPaymentProfile.objects.select_for_update().get(
            owner=payout.owner
        )
        if (
            fingerprint(targets.for_profile(profile)) != item.recipient_digest
            or item.account_digest != client.account_digest()
        ):
            raise RentalConflict(
                "The original beneficiary changed.", code="beneficiary_changed"
            )
        if payout.amount_minor != item.amount_minor or payout.currency != item.currency:
            raise RentalConflict(
                "The original payout amount changed.", code="payout_changed"
            )
        validate_payout_instruction(
            payout, profile_revision=profile.revision if not retry else None
        )
        sensitive_actions.consume(
            request,
            action="payout.execute",
            resource_id=payout.id,
            revision=payout.revision,
            payload={
                "command": request.data,
                "approval_kind": "retry" if retry else "reauthorize",
                **_details(item),
            },
        )
        if retry:
            previous = item
            previous.current = False
            previous.save(update_fields=["current", "updated_at"])
            item = paymob_payouts.stage(
                payout, targets.unseal(previous), actor=actor, retry_of=previous
            )
        else:
            item.authorization_context = paymob_payouts.authorization_context(actor)
            item.status, item.failure_code = "queued", ""
            item.save(
                update_fields=[
                    "authorization_context",
                    "status",
                    "failure_code",
                    "updated_at",
                ]
            )
        payout.status = "created"
        previous_profile_revision = payout.beneficiary_profile_revision
        payout.beneficiary_profile_revision = profile.revision
        payout.failure_code = payout.hold_reason = ""
        payout.revision += 1
        payout.save()
        PayoutAuditEvent.objects.create(
            payout=payout,
            actor=actor,
            action="retry_approved" if retry else "reauthorized",
            metadata={
                "instruction_id": str(item.id),
                "previous_beneficiary_revision": previous_profile_revision,
                "beneficiary_revision": profile.revision,
                "funding_digest": _details(item)["funding_digest"],
            },
        )
        from ..services.payout_notifications import record

        record(payout, "retry_approved" if retry else "reauthorized")
        result = remember_mutation(
            user=actor,
            operation=operation,
            request_key=key,
            payload=request.data,
            request_subject_id=payout.id,
            result_subject_id=payout.id,
            result_revision=payout.revision,
            resource=payout_payload(payout),
        )
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def reauthorize_payout(request, payout_id):
    return _approve_again(request, payout_id)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def retry_failed_payout(request, payout_id):
    return _approve_again(request, payout_id, retry=True)
