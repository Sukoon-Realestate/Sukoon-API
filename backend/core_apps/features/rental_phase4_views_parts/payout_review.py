"""Review original instructions and explicitly renew an unsent approval."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from core_apps.users.services import totp
from ..models import OwnerPayable, OwnerPaymentProfile, PaymobPayout
from ..pagination import FeaturePagination
from ..rental_serializers import OwnerPaymentProfileSerializer
from ..renderers import FeatureJsonRenderer
from ..services import paymob_payout_client as client, paymob_payout_targets as targets
from ..services.rental_phase2 import RentalConflict, fingerprint
from ..services.rental_lifecycle.common import staff_role
from ..services.rental_lifecycle.provider_instructions import (
    validate_payout_instruction,
)
from .operations_execute_payout import _require_payout_role
from .handover_respond import payout_payload


from ..services.payout_authority import _reader as _reader


UNSENT_REVIEW = {
    "authorization_changed",
    "beneficiary_changed",
    "payout_held",
    "refund_pending",
}


from core_apps.features.services.money_projection import _details as _details


class PayoutQueueView(FeatureAPIView):
    name = "Payout Queue"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "payout_review",
            "payout_queue",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
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
                {
                    "resource": payout_payload(item.payout),
                    "instruction_status": item.status,
                }
                for item in page
            ]
        )


# Stable callable import for integrations; URLs use the explicit class.
payout_queue = PayoutQueueView.as_view()


class PayableQueueView(FeatureAPIView):
    name = "Payable Queue"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "payout_review",
            "payable_queue",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
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


# Stable callable import for integrations; URLs use the explicit class.
payable_queue = PayableQueueView.as_view()


class PayoutReviewView(FeatureAPIView):
    name = "Payout Review"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "payout_review",
            "payout_review",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, payout_id):
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
                    reauthorize_reason = "راجع تجهيز القناة والمستفيد الأصلي والرصيد المحجوز قبل الاعتماد."
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
                        "retry_of": (
                            str(value.retry_of.id) if value.retry_of_id else None
                        ),
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


# Stable callable import for integrations; URLs use the explicit class.
payout_review = PayoutReviewView.as_view()


class PayoutPreviewView(FeatureAPIView):
    name = "Payout Preview"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "payout_review",
            "payout_preview",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        _require_payout_role(request.user)
        ids = request.query_params.getlist("payable_id")
        import uuid

        try:
            identities = {uuid.UUID(value) for value in ids}
        except (ValueError, TypeError):
            raise ValidationError(
                {"payable_id": "Use original payable UUIDs."}
            ) from None
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
                {
                    value.invoice.beneficiary_id or value.lease.owner_id
                    for value in payables
                }
            )
            != 1
        ):
            raise ValidationError(
                {
                    "payable_id": "Select payables for one original lease and beneficiary."
                }
            )
        lease = payables[0].lease
        profile = get_object_or_404(
            OwnerPaymentProfile,
            owner_id=payables[0].invoice.beneficiary_id or lease.owner_id,
        )
        recipient = (
            targets.for_profile(profile)
            if profile.provider == client.PROVIDER
            else None
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
                    "beneficiary_account_digest": fingerprint(
                        profile.provider_account_id
                    ),
                    **(
                        {"recipient_digest": fingerprint(recipient)}
                        if recipient
                        else {}
                    ),
                },
            }
        )
        response["Cache-Control"] = "private, no-store"
        return response


# Stable callable import for integrations; URLs use the explicit class.
payout_preview = PayoutPreviewView.as_view()


def _approve_again(request, payout_id, *, retry=False):
    from ..services.payout_commands import approve_again

    result = approve_again(
        request.user,
        request.auth,
        request.data,
        request.headers.get("X-Sokoun-Authorization", ""),
        payout_id,
        retry=retry,
    )
    return Response(result.data, status=result.status)


class ReauthorizePayoutView(FeatureAPIView):
    name = "Reauthorize Payout"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "payout_review",
            "reauthorize_payout",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, payout_id):
        return _approve_again(request, payout_id)


# Stable callable import for integrations; URLs use the explicit class.
reauthorize_payout = ReauthorizePayoutView.as_view()


class RetryFailedPayoutView(FeatureAPIView):
    name = "Retry Failed Payout"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "payout_review",
            "retry_failed_payout",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, payout_id):
        return _approve_again(request, payout_id, retry=True)


# Stable callable import for integrations; URLs use the explicit class.
retry_failed_payout = RetryFailedPayoutView.as_view()

__all__ = [
    "PayableQueueView",
    "PayoutPreviewView",
    "PayoutQueueView",
    "PayoutReviewView",
    "ReauthorizePayoutView",
    "RetryFailedPayoutView",
    "_details",
    "_reader",
    "payable_queue",
    "payout_preview",
    "payout_queue",
    "payout_review",
    "reauthorize_payout",
    "retry_failed_payout",
]
