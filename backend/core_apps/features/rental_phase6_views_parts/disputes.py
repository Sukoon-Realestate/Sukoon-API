"""Rental phase6 views: disputes."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


import uuid
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from ..models import RentalDispute, RentalEvidence, PrivateAccessRevocation
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from ..services.rental_phase6 import evaluate_financial_closure
from .final_settlement_propose import _lease
from .refund_execute import SUBJECT_MODELS, dispute_payload, _dispute


class DisputesView(FeatureAPIView):
    name = "Disputes"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "disputes", "disputes", boundary="standard", capability=None, typed=False
        ),
        "post": ActionPolicy(
            "disputes", "disputes", boundary="standard", capability=None, typed=False
        ),
    }

    @transaction.atomic
    def get(self, request):
        if request.query_params.get("projection") == "compact_v1":
            from ..financial_http import compact_financial_response

            return compact_financial_response(request, "disputes")
        workspace = request.query_params.get("workspace")
        queryset = (
            RentalDispute.objects.filter(lease__owner=request.user)
            if workspace == "owner"
            else RentalDispute.objects.filter(lease__tenant=request.user)
        )
        if request.query_params.get("lease_id"):
            queryset = queryset.filter(lease__id=request.query_params["lease_id"])
        queryset = queryset.exclude(
            lease_id__in=PrivateAccessRevocation.objects.filter(
                user=request.user
            ).values("lease_id")
        )
        results = [
            dispute_payload(x, request.user)
            for x in queryset.prefetch_related("evidence")
        ]
        return Response(
            {"count": len(results), "next": None, "previous": None, "results": results}
        )

    @transaction.atomic
    def post(self, request):
        from ..rental_serializers_parts.command_serializers import (
            DisputeCreateCommand,
            validated,
        )
        from rest_framework.exceptions import NotFound
        from core_apps.common.command_fields import is_uuid

        body = request.data if hasattr(request.data, "get") else {}
        lease_id = body.get("lease_id")
        if not is_uuid(lease_id):
            from ..providers import require_verified_rental_account

            require_verified_rental_account(request.user)
            raise NotFound()
        lease = _lease(request, lease_id, lock=True)
        command = validated(DisputeCreateCommand, request.data)
        from core_apps.common.command_authority import recheck_session

        recheck_session(request)
        request_key = command["request_key"]
        operation = f"dispute.create.{lease.id}"
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        kind = command["subject_kind"]
        model = SUBJECT_MODELS.get(kind)
        if not model:
            raise ValidationError({"subject_kind": "Unsupported dispute subject."})
        subject = get_object_or_404(model, id=command["subject_id"])
        if getattr(subject, "lease_id", None) != lease.pk:
            raise ValidationError(
                {"subject_id": "Subject does not belong to this lease."}
            )
        evidence_ids = command["evidence_ids"]
        evidence = list(
            RentalEvidence.objects.filter(
                id__in=evidence_ids,
                lease=lease,
                malware_status=RentalEvidence.MalwareStatus.SAFE,
                deleted_at__isnull=True,
            )
        )
        if len(evidence) != len(set(evidence_ids)):
            raise ValidationError({"evidence_ids": "Invalid evidence."})
        item = RentalDispute.objects.create(
            lease=lease,
            opened_by=request.user,
            subject_kind=kind,
            subject_id=subject.id,
            reason=command["reason"],
        )
        item.evidence.set(evidence)
        return Response(
            remember_mutation(
                user=request.user,
                operation=operation,
                request_key=request_key,
                payload=request.data,
                request_subject_id=lease.id,
                result_subject_id=item.id,
                result_revision=item.revision,
                resource=dispute_payload(item, request.user),
                response_status=201,
            ),
            status=status.HTTP_201_CREATED,
        )


# Stable callable import for integrations; URLs use the explicit class.
disputes = DisputesView.as_view()


class DisputeDetailView(FeatureAPIView):
    name = "Dispute Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "disputes",
            "dispute_detail",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, dispute_id):
        return Response(dispute_payload(_dispute(request, dispute_id), request.user))


# Stable callable import for integrations; URLs use the explicit class.
dispute_detail = DisputeDetailView.as_view()


class DisputeRespondView(FeatureAPIView):
    name = "Dispute Respond"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "disputes",
            "dispute_respond",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, dispute_id):
        from ..rental_serializers_parts.command_serializers import (
            DisputeRespondCommand,
            validated,
        )

        item = _dispute(request, dispute_id, allow_operations=True)
        data = request.data if hasattr(request.data, "get") else {}
        action = data.get("action") or data.get("decision") or "reply"
        if not isinstance(action, str) or action not in {"reply", "resolve", "reject"}:
            raise ValidationError({"action": "Unsupported dispute action."})
        command = validated(DisputeRespondCommand, request.data)
        request_key = command["request_key"]
        operation = f"dispute.respond.{item.id}.{request.user.id}.{action}"
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        with transaction.atomic():
            if action in {"resolve", "reject"}:
                from core_apps.admin_api.permissions import require_staff_actor

                require_staff_actor(
                    request.user, {StaffProfile.RoleName.DISPUTE_RESOLVER}, lock=True
                )
            item = _dispute(request, dispute_id, allow_operations=True, lock=True)
            replay = replay_operation(
                request.user, operation, request_key, request.data
            )
            if replay:
                return Response(replay[0], status=replay[1])
            from core_apps.common.command_authority import recheck_session

            recheck_session(request)
            if item.revision != command["expected_revision"]:
                raise RentalConflict(
                    "Dispute revision conflict.", code="stale_revision"
                )
            if item.status != RentalDispute.Status.OPEN:
                raise RentalConflict(
                    "A resolved or rejected dispute cannot be changed.",
                    code="terminal_dispute",
                )
            if action == "reply":
                if request.user not in (item.lease.owner, item.lease.tenant):
                    raise PermissionDenied("Only parties may reply.")
                item.responses = [
                    *item.responses,
                    {
                        "id": str(uuid.uuid4()),
                        "author_id": str(request.user.id),
                        "note": command["note"],
                        "at": timezone.now().isoformat(),
                    },
                ]
            elif action in {"resolve", "reject"}:
                if request.user.pk in {item.lease.owner_id, item.lease.tenant_id}:
                    raise PermissionDenied(
                        "Dispute resolution requires an independent operator."
                    )
                profile = getattr(request.user, "staff_profile", None)
                if not request.user.is_superuser and (
                    not profile
                    or profile.role_name != StaffProfile.RoleName.DISPUTE_RESOLVER
                ):
                    raise PermissionDenied(
                        "Resolution requires the dispute resolver role."
                    )
                item.status = (
                    RentalDispute.Status.RESOLVED
                    if action == "resolve"
                    else RentalDispute.Status.REJECTED
                )
                item.resolution = command["note"]
                item.resolved_by = request.user
            else:
                raise ValidationError({"action": "Unsupported dispute action."})
            item.revision += 1
            item.save()
            evaluate_financial_closure(item.lease)
            output = remember_mutation(
                user=request.user,
                operation=operation,
                request_key=request_key,
                payload=request.data,
                request_subject_id=item.id,
                result_subject_id=item.id,
                result_revision=item.revision,
                resource=dispute_payload(item, request.user),
            )
        return Response(output)


# Stable callable import for integrations; URLs use the explicit class.
dispute_respond = DisputeRespondView.as_view()


def document_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "revision": item.revision,
        "type": item.document_type,
        "title": item.title,
        "status": item.status,
        "sha256": item.sha256,
        "created_at": item.created_at.isoformat(),
        "failure_code": item.failure_code,
        "media_type": item.media_type,
        "starts_on": str(item.starts_on) if item.starts_on else None,
        "ends_on_exclusive": (
            str(item.ends_on_exclusive) if item.ends_on_exclusive else None
        ),
    }


__all__ = [
    "DisputeDetailView",
    "DisputeRespondView",
    "DisputesView",
    "dispute_detail",
    "dispute_respond",
    "disputes",
    "document_payload",
]
