"""Rental phase5 views: change signing session."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from core_apps.common.command_fields import parse_revision, require_request_key
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import ChangeSigningSession, RentalChange
from ..providers import mock_completion_metadata, get_rental_provider
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from ..services.rental_notes import record_response_note, validated_note
from .maintenance_action import change_payload, _change


class SubmitChangeForSignatureView(FeatureAPIView):
    name = "Submit Change For Signature"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "change_signing_session",
            "submit_change_for_signature",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, change_id, kind):
        item = _change(request, change_id, kind)
        request_key = require_request_key(request.data)
        if request.user != item.lease.owner:
            raise PermissionDenied("Only the owner can submit the change.")
        operation = f"rental_change.submit.{item.id}"
        note = validated_note(request.data)
        with transaction.atomic():
            item = _change(request, change_id, kind, lock=True)
            if request.user != item.lease.owner:
                raise PermissionDenied("Only the owner can submit the change.")
            replay = replay_operation(
                request.user, operation, request_key, request.data
            )
            if replay:
                return Response(replay[0], status=replay[1])
            if item.status != RentalChange.Status.ACCEPTED:
                raise RentalConflict("Both participants must accept the exact change.")
            if kind == RentalChange.Kind.RENEWAL:
                from ..services.planning_transitions import require_no_departure

                require_no_departure(item.lease)
            if (
                parse_revision(request.data, "expected_revision", default=0)
                != item.revision
            ):
                raise RentalConflict("Change revision conflict.", code="stale_revision")
            from ..services.change_terms import (
                require_current_change_base,
                validate_changed_terms,
            )

            require_current_change_base(item)
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
            from ..services.change_versions import snapshot
            from ..services.rental_lifecycle.consents import record_consent

            record_consent(
                item,
                request.user,
                "submit_for_signature",
                {
                    **snapshot(item),
                    "note": note,
                    "document_id": str(item.document_id),
                    "document_hash": item.document_hash,
                },
            )
            record_response_note(
                item, request.user, "change", "submit_for_signature", note
            )
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


# Stable callable import for integrations; URLs use the explicit class.
submit_change_for_signature = SubmitChangeForSignatureView.as_view()


class ChangeSigningSessionView(FeatureAPIView):
    name = "Change Signing Session"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "change_signing_session",
            "change_signing_session",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, change_id, kind):
        item = _change(request, change_id, kind)
        request_key = require_request_key(request.data)
        operation = f"rental_change.signing_session.{item.id}.{request.user.id}"
        with transaction.atomic():
            item = _change(request, change_id, kind, lock=True)
            replay = replay_operation(
                request.user, operation, request_key, request.data
            )
            if replay:
                return Response(replay[0], status=replay[1])
            if item.status != RentalChange.Status.PENDING_SIGNATURES:
                raise RentalConflict("Change is not awaiting signatures.")
            if str(request.user.id) in item.signed_by:
                raise RentalConflict("You already signed this change document.")
            from ..services.change_terms import (
                require_current_change_base,
                validate_changed_terms,
            )

            require_current_change_base(item)
            validate_changed_terms(item.terms)
            if (
                parse_revision(request.data, "expected_revision", default=0)
                != item.revision
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


# Stable callable import for integrations; URLs use the explicit class.
change_signing_session = ChangeSigningSessionView.as_view()


from core_apps.features.services.change_signing_completion import (
    complete_change_signature as complete_change_signature,
)

__all__ = [
    "ChangeSigningSessionView",
    "SubmitChangeForSignatureView",
    "change_signing_session",
    "complete_change_signature",
    "submit_change_for_signature",
]
