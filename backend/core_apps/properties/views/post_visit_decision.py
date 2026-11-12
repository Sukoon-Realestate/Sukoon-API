from ..services.post_visit_reads import decision_context
from rest_framework.views import APIView
import logging
from functools import wraps
from django.db import IntegrityError
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.features.models import IdempotencyRecord
from ..serializers.visit import TenantVisitRequestDetailSerializer
from ..services.post_visit_decision import (
    OPERATION,
    DecisionConflict,
    PostVisitDecisionBody,
    invalid,
    submit_decision,
)

logger = logging.getLogger(__name__)


def private_visit_errors(view):
    """Keep private serializer/database locals out of generic crash reports."""

    @wraps(view)
    def guarded(self, request, id):
        try:
            return view(self, request, id)
        except (APIException, Http404, DjangoPermissionDenied):
            raise
        except Exception as error:
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


class PostVisitDecisionAPIView(APIView):
    http_method_names = ["get", "post", "options"]
    name = "Post Visit Decision"
    permission_classes = [IsAuthenticated]
    renderer_classes = [PostVisitJsonRenderer]

    @private_visit_errors
    def get(self, request, id):
        return Response(
            decision_context(
                request.user,
                id,
                request.query_params.get("request_key"),
                context={"request": request},
            )
        )

    @private_visit_errors
    def post(self, request, id):
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
