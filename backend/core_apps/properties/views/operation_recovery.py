"""Return original authoritative acknowledgment or fence an uncommitted command."""

from django.shortcuts import get_object_or_404
from django.db import transaction
from core_apps.users.models import User
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import UUIDField
from core_apps.common.idempotency import request_key, resolve_or_close
from core_apps.common.renderers import GenericJsonRenderer
from ..models import Property


class PropertyOperationRecovery(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request):
        if request.data.get('kind') == 'image.upload':
            from ..services.image_uploads import reconcile
            identity = UUIDField().run_validation(request.data.get('property_id'))
            reconcile(user=request.user, claims=request.auth, property_id=identity, key=request_key(request))
        return self._resolve(request)

    @transaction.atomic
    def _resolve(self, request):
        User.objects.select_for_update().get(pk=request.user.pk)
        kind, identity = request.data.get("kind"), request.data.get("property_id")
        if kind not in {"create", "update", "image.upload"}:
            raise ValidationError("Unsupported property command.")
        if kind != "create":
            identity = UUIDField().run_validation(identity)
            subject = get_object_or_404(
                Property.objects.select_for_update(), id=identity, owner=request.user
            )
            # Receipt scope must match the canonical UUID used by execution,
            # including callers that supplied a different valid UUID spelling.
            identity = str(subject.id)
        operation = (
            "property.create" if kind == "create" else f"property.{kind}:{identity}"
        )
        key = request_key(request)
        record = resolve_or_close(
            user=request.user, operation=operation, key=key, auth_claims=request.auth
        )
        if record.result_subject_id and kind == "create":
            get_object_or_404(Property, id=record.result_subject_id, owner=request.user)
        outcome = (
            "acknowledged"
            if record.recovery_status == "confirmed"
            else record.recovery_status
        )
        return Response(
            {
                "request_key": key,
                "outcome": outcome,
                "resource": record.response_data if outcome == "acknowledged" else None,
            },
            headers={"Cache-Control": "no-store"},
        )
