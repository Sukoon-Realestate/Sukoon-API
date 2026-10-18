import logging
import uuid
from functools import wraps

from django.db import IntegrityError, transaction
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from core_apps.common.renderers import GenericJsonRenderer
from core_apps.features.models import IdempotencyRecord
from ..models import PropertyVisit, PropertyVisitDecision
from ..serializers.visit import (
    TenantVisitRequestDetailSerializer,
    OwnerVisitRequestDetailSerializer,
)
from ..services.post_visit_decision import (
    OPERATION,
    DecisionConflict,
    PostVisitDecisionBody,
    invalid,
    reason_visible,
    submit_decision,
    visit_context,
)


logger = logging.getLogger(__name__)


def private_visit_errors(view):
    """Keep private serializer/database locals out of generic crash reports."""

    @wraps(view)
    def guarded(request, id):
        try:
            return view(request, id)
        except (APIException, Http404, DjangoPermissionDenied):
            raise
        except Exception as error:
            # Exception strings/tracebacks can contain the row or request body.
            # Log only identifiers, outcome and class; recovery remains read-only.
            logger.error(
                "post_visit_request_failed visit_id=%s actor_id=%s error_type=%s",
                id,
                request.user.pk,
                type(error).__name__,
            )
            return Response(
                {
                    "message": "The visit decision could not be confirmed. Please refresh to recover it.",
                    "code": "decision_request_failed",
                },
                status=500,
            )

    return guarded


class PostVisitJsonRenderer(GenericJsonRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get("response")
        if response is not None:
            response["Cache-Control"] = "private, no-store"
        return super().render(data, accepted_media_type, renderer_context)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([PostVisitJsonRenderer])
@private_visit_errors
def post_visit_decision(request, id):
    if request.method == "POST":
        body = PostVisitDecisionBody(data=request.data)
        if not body.is_valid():
            if "decision" in body.errors:
                invalid("Choose proceed or decline.", "invalid_decision")
            if "attended" in body.errors:
                invalid("Attendance acknowledgment is required.", "attendance_required")
            body.is_valid(raise_exception=True)
        try:
            visit, created = submit_decision(request.user, id, body.validated_data)
        except IntegrityError:
            # Cross-visit reuse races share the actor/operation unique key. The
            # losing transaction rolled back its decision and event entirely.
            if IdempotencyRecord.objects.filter(
                user=request.user,
                operation=OPERATION,
                request_key=str(body.validated_data["request_key"]),
            ).exists():
                raise DecisionConflict(
                    "This request key was used for different data.",
                    "idempotency_conflict",
                )
            raise
        output = TenantVisitRequestDetailSerializer(
            visit, context={"request": request}
        ).data
        output["operation"] = {
            "request_key": str(body.validated_data["request_key"]),
            "status": "recorded",
        }
        return Response({"message": "Your decision is saved.", **output}, status=200)

    with transaction.atomic():
        # Lock serializes lookup with a simultaneous commit. GET never writes or
        # reruns the mutation, and absent is scoped to this actor AND visit.
        visit = get_object_or_404(
            PropertyVisit.objects.select_for_update(of=("self",)).select_related(
                "property", "property__owner", "tenant"
            ),
            id=id,
        )
        from ..services.viewing_access import can_read

        participant = can_read(visit, request.user)
        if not participant and not reason_visible(request.user, visit):
            from rest_framework.exceptions import NotFound

            raise NotFound()
        if participant:
            serializer = (
                TenantVisitRequestDetailSerializer
                if request.user.pk != visit.property.owner_id
                else OwnerVisitRequestDetailSerializer
            )
            output = serializer(visit, context={"request": request}).data
        else:
            # Authorized support gets only the relevant decision context; do not
            # grant owner actions or unrelated tenant phone/account data.
            output = {"id": str(visit.id), **visit_context(visit, request.user)}
            output["rental_continuation"]["next_action"] = None
            for field in ("invitation_id", "agreement_id", "invoice_id"):
                output["rental_continuation"][field] = None
        key = request.query_params.get("request_key")
        if key is not None:
            try:
                key = str(uuid.UUID(key))
            except (ValueError, TypeError, AttributeError):
                invalid("request_key must be a UUID.", "invalid_request_key")
            recorded = (
                IdempotencyRecord.objects.filter(
                    user=request.user,
                    operation=OPERATION,
                    request_key=key,
                    request_subject_id=visit.id,
                ).exists()
                or PropertyVisitDecision.objects.filter(
                    visit=visit, tenant=request.user, request_key=key
                ).exists()
            )
            output["operation"] = {
                "request_key": key,
                "status": "recorded" if recorded else "absent",
            }
        return Response(output)
