"""Rental phase6 views: disputes."""

import uuid
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from ..models import RentalDispute, RentalEvidence
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from ..services.rental_phase6 import evaluate_financial_closure
from .final_settlement_propose import _lease
from .refund_execute import SUBJECT_MODELS, dispute_payload, _dispute


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def disputes(request):
    if request.method == "GET":
        workspace = request.query_params.get("workspace")
        queryset = (
            RentalDispute.objects.filter(lease__owner=request.user)
            if workspace == "owner"
            else RentalDispute.objects.filter(lease__tenant=request.user)
        )
        if request.query_params.get("lease_id"):
            queryset = queryset.filter(lease__id=request.query_params["lease_id"])
        results = [
            dispute_payload(x, request.user)
            for x in queryset.prefetch_related("evidence")
        ]
        return Response(
            {"count": len(results), "next": None, "previous": None, "results": results}
        )
    lease = _lease(request, request.data.get("lease_id"))
    kind = request.data.get("subject_kind")
    model = SUBJECT_MODELS.get(kind)
    if not model:
        raise ValidationError({"subject_kind": "Unsupported dispute subject."})
    subject = get_object_or_404(model, id=request.data.get("subject_id"))
    if getattr(subject, "lease_id", None) != lease.pk:
        raise ValidationError({"subject_id": "Subject does not belong to this lease."})
    evidence_ids = request.data.get("evidence_ids", [])
    evidence = list(
        RentalEvidence.objects.filter(
            id__in=evidence_ids,
            lease=lease,
            malware_status=RentalEvidence.MalwareStatus.SAFE,
        )
    )
    if len(evidence) != len(set(evidence_ids)):
        raise ValidationError({"evidence_ids": "Invalid evidence."})
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"dispute.create.{lease.id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    item = RentalDispute.objects.create(
        lease=lease,
        opened_by=request.user,
        subject_kind=kind,
        subject_id=subject.id,
        reason=request.data.get("reason", ""),
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def dispute_detail(request, dispute_id):
    return Response(dispute_payload(_dispute(request, dispute_id), request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def dispute_respond(request, dispute_id):
    item = _dispute(request, dispute_id, allow_operations=True)
    action = request.data.get("action") or request.data.get("decision") or "reply"
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"dispute.respond.{item.id}.{request.user.id}.{action}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        item = _dispute(request, dispute_id, allow_operations=True, lock=True)
        if item.revision != int(request.data.get("expected_revision", 0)):
            raise RentalConflict("Dispute revision conflict.", code="stale_revision")
        if action == "reply":
            if request.user not in (item.lease.owner, item.lease.tenant):
                raise PermissionDenied("Only parties may reply.")
            item.responses = [
                *item.responses,
                {
                    "id": str(uuid.uuid4()),
                    "author_id": str(request.user.id),
                    "note": request.data.get("note", ""),
                    "at": timezone.now().isoformat(),
                },
            ]
        elif action in {"resolve", "reject"}:
            profile = getattr(request.user, "staff_profile", None)
            if not request.user.is_superuser and (
                not profile
                or profile.role_name != StaffProfile.RoleName.DISPUTE_RESOLVER
            ):
                raise PermissionDenied("Resolution requires the dispute resolver role.")
            item.status = (
                RentalDispute.Status.RESOLVED
                if action == "resolve"
                else RentalDispute.Status.REJECTED
            )
            item.resolution = request.data.get("note", "")
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


def document_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "revision": item.revision,
        "type": item.document_type,
        "title": item.title,
        "status": item.status,
        "sha256": item.sha256,
        "starts_on": str(item.starts_on) if item.starts_on else None,
        "ends_on_exclusive": (
            str(item.ends_on_exclusive) if item.ends_on_exclusive else None
        ),
    }
