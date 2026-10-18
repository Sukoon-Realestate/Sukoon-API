"""Rental phase5 views: change signing session."""

from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import ChangeSigningSession, RentalChange
from ..providers import mock_completion_metadata, get_rental_provider
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .maintenance_action import change_payload, _change


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def submit_change_for_signature(request, change_id, kind):
    item = _change(request, change_id, kind)
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    if request.user != item.lease.owner:
        raise PermissionDenied("Only the owner can submit the change.")
    operation = f"rental_change.submit.{item.id}"
    with transaction.atomic():
        item = _change(request, change_id, kind, lock=True)
        if request.user != item.lease.owner:
            raise PermissionDenied("Only the owner can submit the change.")
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        if item.status != RentalChange.Status.ACCEPTED:
            raise RentalConflict("Both participants must accept the exact change.")
        if kind == RentalChange.Kind.RENEWAL:
            from ..services.planning_transitions import require_no_departure

            require_no_departure(item.lease)
        if int(request.data.get("expected_revision", 0)) != item.revision:
            raise RentalConflict("Change revision conflict.", code="stale_revision")
        from ..services.change_terms import validate_changed_terms

        validate_changed_terms(item.terms)
        generated = get_rental_provider().generate_agreement(
            item.id, item.revision, item.terms
        )
        item.document_id = generated.document_id
        item.document_hash = generated.digest
        item.status = RentalChange.Status.PENDING_SIGNATURES
        item.signed_by = []
        item.revision += 1
        item.save()
        from ..services.planning_notifications import record_event

        record_event(item, request.user, operation)
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=change_payload(item, request.user),
        )
    return Response(output)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def change_signing_session(request, change_id, kind):
    item = _change(request, change_id, kind)
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"rental_change.signing_session.{item.id}.{request.user.id}"
    with transaction.atomic():
        item = _change(request, change_id, kind, lock=True)
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        if item.status != RentalChange.Status.PENDING_SIGNATURES:
            raise RentalConflict("Change is not awaiting signatures.")
        if str(request.user.id) in item.signed_by:
            raise RentalConflict("You already signed this change document.")
        from ..services.change_terms import validate_changed_terms

        validate_changed_terms(item.terms)
        if (
            int(request.data.get("expected_revision", 0)) != item.revision
            or str(request.data.get("document_id")) != str(item.document_id)
            or request.data.get("document_hash") != item.document_hash
        ):
            raise RentalConflict(
                "The change document is stale.", code="document_changed"
            )
        hosted = get_rental_provider().create_signing_session(
            item.id, request.user.id, request_key
        )
        session = ChangeSigningSession.objects.create(
            change=item,
            signer=request.user,
            request_key=request_key,
            change_revision=item.revision,
            document_id=item.document_id,
            document_hash=item.document_hash,
            provider_session_id=hosted.provider_session_id,
            hosted_url=hosted.hosted_url,
            expires_at=timezone.now() + timedelta(minutes=30),
        )
        resource = {
            "session_id": str(session.id),
            "subject_id": str(item.id),
            "request_key": str(request_key),
            "revision": item.revision,
            "document_id": str(item.document_id),
            "document_hash": item.document_hash,
            "hosted_url": session.hosted_url,
            **mock_completion_metadata(
                "change-signing-sessions", session.id, item.revision
            ),
            "expires_at": session.expires_at.isoformat(),
        }
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=item.id,
            result_subject_id=session.id,
            result_revision=item.revision,
            resource=resource,
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


def complete_change_signature(provider_session_id):
    with transaction.atomic():
        session = get_object_or_404(
            ChangeSigningSession, provider_session_id=provider_session_id
        )
        item = RentalChange.objects.select_for_update().get(pk=session.change_id)
        session = ChangeSigningSession.objects.select_for_update().get(pk=session.pk)
        if session.status == "completed":
            return item
        if (
            item.status != RentalChange.Status.PENDING_SIGNATURES
            or session.expires_at <= timezone.now()
            or session.change_revision != item.revision
            or session.document_id != item.document_id
            or session.document_hash != item.document_hash
        ):
            raise RentalConflict(
                "The signed change document is stale.", code="document_changed"
            )
        session.status = "completed"
        session.completed_at = timezone.now()
        session.save()
        signed = set(item.signed_by)
        signed.add(str(session.signer.id))
        item.signed_by = sorted(signed)
        if {str(item.lease.owner.id), str(item.lease.tenant.id)}.issubset(signed):
            item.status = RentalChange.Status.SIGNED
            item.revision += 1
        item.save()
        from ..services.planning_notifications import record_event

        record_event(item, session.signer, f"change.signed.{session.id}")
        return item
