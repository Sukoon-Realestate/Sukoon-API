"""Rental phase4 views: handover respond."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import DepositAgreement, RentalPayout
from ..renderers import FeatureJsonRenderer
from .handover_payload import _money, _lease
from .lease_handovers import deposit_payload


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_deposit(request, lease_id):
    lease = _lease(request, lease_id)
    # Issuance belongs to the signing transaction. A read must not create a
    # separate charge, especially after the combined invoice was already paid.
    deposit = get_object_or_404(DepositAgreement, lease=lease)
    return Response(deposit_payload(deposit))


class HandoverRespondView(FeatureAPIView):
    name = "Handover Respond"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "handover_respond",
            "handover_respond",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, handover_id):
        from ..rental_serializers_parts.command_serializers import (
            HandoverRespondCommand,
            validated,
        )

        data = request.data if hasattr(request.data, "get") else {}
        action = data.get("action") or data.get("decision")
        if (
            not isinstance(action, str)
            or action not in {"accept", "dispute"}
            or not data.get("request_key")
        ):
            raise ValidationError(
                "accept/dispute, expected_revision, and request_key are required."
            )
        command = validated(HandoverRespondCommand, request.data)
        from ..services.handover_commands import respond_handover

        payload, status = respond_handover(
            request.user,
            request.auth,
            command,
            request.data,
            handover_id,
            action,
        )
        return Response(payload, status=status)


# Stable callable import for integrations; URLs use the explicit class.
handover_respond = HandoverRespondView.as_view()


def payout_payload(item):
    from ..rental_serializers import OwnerPaymentProfileSerializer

    instruction = item.paymob_instructions.filter(current=True).first()
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "revision": item.revision,
        "status": item.status,
        "amount": _money(item.amount_minor),
        "masked_beneficiary": OwnerPaymentProfileSerializer().get_masked_beneficiary(
            item
        ),
        "reason": item.hold_reason or item.failure_code,
        "submitted_at": (
            instruction.submitted_at.isoformat()
            if instruction and instruction.submitted_at
            else None if instruction else item.created_at.isoformat()
        ),
        "succeeded_at": (
            instruction.confirmed_at.isoformat()
            if instruction and instruction.confirmed_at
            else (
                item.updated_at.isoformat()
                if item.status == RentalPayout.Status.PAID
                else None
            )
        ),
        "history": [
            {"action": value.action, "occurred_at": value.created_at.isoformat()}
            for value in item.audit_events.filter(
                action__in=[
                    "approved",
                    "submitted",
                    "reauthorized",
                    "retry_approved",
                    "paid",
                    "held",
                ]
            ).order_by("pk")
        ],
        "payable_ids": [str(x.id) for x in item.payables.all()],
    }


# Supported imports used by public facades and domain callers.
from ..services.payable_eligibility import (
    evaluate_owner_payables as evaluate_owner_payables,
)

__all__ = ["evaluate_owner_payables"]
