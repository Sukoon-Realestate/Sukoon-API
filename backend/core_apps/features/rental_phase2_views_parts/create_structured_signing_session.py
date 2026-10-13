"""Rental phase2 views: create structured signing session."""

from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import Lease, RentalInventoryDayLock, SigningSession
from ..providers import mock_completion_metadata, get_rental_provider
from ..renderers import FeatureJsonRenderer
from ..rental_serializers import (
    LeasePhase2Serializer,
    RentalDecisionSerializer,
    RentalSigningBodySerializer,
)
from ..services.rental_phase2 import (
    RentalConflict,
    assert_owner_ready,
    remember_mutation,
)
from .owner_payment_profile import (
    _replay_response,
    _remember_session,
    _participant_lease,
    _event,
)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_submit_for_signature(request, lease_id):
    lease = _participant_lease(request, lease_id)
    if request.user != lease.owner:
        raise PermissionDenied("Only the owner can submit the agreement.")
    serializer = RentalDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    operation = f"rental_agreement.submit_signature.{lease_id}"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        lease = _participant_lease(request, lease_id, lock=True)
        assert_owner_ready(request.user, lease.property)
        replay = _replay_response(
            request.user, operation, data["request_key"], request.data
        )
        if replay:
            return replay
        if lease.status != Lease.Status.DRAFT:
            raise RentalConflict(
                "Only a reviewed draft can be submitted for signature.",
                code="invalid_state",
            )
        if data["decision"] != "submit_for_signature":
            raise ValidationError({"decision": "Must be submit_for_signature."})
        if data["expected_revision"] != lease.revision:
            raise RentalConflict("Lease revision conflict.", code="stale_revision")
        required = {str(lease.owner.id), str(lease.tenant.id)}
        if not required.issubset(set(lease.reviewed_by)):
            raise RentalConflict("Both participants must review the current agreement.")
        if not lease.hold_expires_at or lease.hold_expires_at <= timezone.now():
            raise RentalConflict("The inventory hold expired.", code="hold_expired")
        required_days = (lease.end_date - lease.start_date).days
        held_days = RentalInventoryDayLock.objects.filter(
            lease=lease,
            kind=RentalInventoryDayLock.Kind.HOLD,
            expires_at__gt=timezone.now(),
        ).count()
        if held_days != required_days:
            raise RentalConflict("The inventory hold expired.", code="hold_expired")
        document = get_rental_provider().generate_agreement(
            lease.id, lease.revision, lease.terms
        )
        lease.document_id = document.document_id
        lease.document_hash = document.digest
        lease.status = Lease.Status.PENDING_SIGNATURES
        lease.revision += 1
        lease.save(
            update_fields=[
                "document_id",
                "document_hash",
                "status",
                "revision",
                "updated_at",
            ]
        )
        _event(lease, request.user, "signature_requested", "Submitted for signature")
        resource = LeasePhase2Serializer(lease, context={"request": request}).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=lease.id,
            result_revision=lease.revision,
            resource=resource,
        )
    return Response(output)


def create_structured_signing_session(request, lease_id):
    lease = _participant_lease(request, lease_id)
    serializer = RentalSigningBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    operation = f"rental_agreement.signing_session.{lease_id}"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        lease = _participant_lease(request, lease_id, lock=True)
        replay = _replay_response(
            request.user, operation, data["request_key"], request.data
        )
        if replay:
            return replay
        if lease.status != Lease.Status.PENDING_SIGNATURES:
            raise RentalConflict("The agreement is not awaiting signatures.")
        if data["expected_revision"] != lease.revision:
            raise RentalConflict("Lease revision conflict.", code="stale_revision")
        if (
            data["document_id"] != lease.document_id
            or data["document_hash"] != lease.document_hash
        ):
            raise RentalConflict(
                "The agreement document changed.", code="document_changed"
            )
        if lease.signing_sessions.filter(
            signer=request.user,
            status="completed",
            document_id=lease.document_id,
            document_hash=lease.document_hash,
        ).exists():
            raise RentalConflict("You already signed this agreement document.")
        provider = get_rental_provider().create_signing_session(
            lease.id, request.user.id, data["request_key"]
        )
        expires_at = timezone.now() + timedelta(
            minutes=settings.RENTAL_SIGNING_TTL_MINUTES
        )
        session = SigningSession.objects.create(
            lease=lease,
            signer=request.user,
            hosted_url=provider.hosted_url,
            expires_at=expires_at,
            request_key=data["request_key"],
            lease_revision=lease.revision,
            document_id=lease.document_id,
            document_hash=lease.document_hash,
            provider_session_id=provider.provider_session_id,
        )
        output = {
            "session_id": str(session.id),
            "subject_id": str(lease.id),
            "request_key": str(data["request_key"]),
            "revision": lease.revision,
            "document_id": str(lease.document_id),
            "document_hash": lease.document_hash,
            **mock_completion_metadata("signing-sessions", session.id, lease.revision),
            "hosted_url": session.hosted_url,
            "expires_at": expires_at.isoformat(),
        }
        output = _remember_session(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=session.id,
            result_revision=lease.revision,
            response_data=output,
        )
    return Response(output, status=status.HTTP_201_CREATED)
