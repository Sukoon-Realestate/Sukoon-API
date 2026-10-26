from django.db import transaction
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from .services import sensitive_actions
from .services.sessions import revoke_all
from .models import AuthSession, User
from django.utils import timezone


class ChallengeBody(serializers.Serializer):
    action = serializers.ChoiceField(choices=sorted(sensitive_actions.ACTIONS))
    resource_id = serializers.UUIDField()
    resource_revision = serializers.IntegerField(min_value=0)
    payload = serializers.DictField()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def challenges(request):
    body = ChallengeBody(data=request.data)
    body.is_valid(raise_exception=True)
    return Response(sensitive_actions.begin(request, body.validated_data), status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def verify(request, identity):
    assertion = request.data.get("assertion")
    if not isinstance(assertion, str) or not 1 <= len(assertion) <= 16384:
        raise serializers.ValidationError(
            {"assertion": "A provider assertion is required."}
        )
    return Response(sensitive_actions.verify(request, identity, assertion))


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def sessions(request):
    if request.method == "POST":
        action = request.data.get("action")
        if action in {"revoke_session", "revoke_others"}:
            from .services.session_management import revoke_selected
            from core_apps.common.idempotency import response_headers

            data, code, replayed = revoke_selected(request)
            return Response(data, status=code, headers=response_headers(replayed))
        if action != "revoke_all":
            raise serializers.ValidationError(
                {"action": "Use revoke_all, revoke_session or revoke_others."}
            )
        with transaction.atomic():
            current = User.objects.select_for_update().get(pk=request.user.pk)
            if request.auth:
                from .services.sessions import validate_session

                validate_session(current, request.auth)
            revoke_all(
                current,
                actor=current,
                action="session.revoke_all",
            )
        return Response({"status": "revoked"})
    return Response(
        {
            "sensitive_actions_frozen": request.user.sensitive_actions_frozen,
            "results": [
                {
                    "id": str(item.id),
                    "created_at": item.created_at.isoformat(),
                    "expires_at": item.expires_at.isoformat(),
                    "current": str(item.id) == (request.auth or {}).get("session_id"),
                    "client_platform": item.client_platform or "",
                    "device_model": item.device_model or "",
                    "os_version": item.os_version or "",
                    "app_version": item.app_version or "",
                    "last_seen_at": (
                        item.last_seen_at.isoformat() if item.last_seen_at else ""
                    ),
                }
                for item in AuthSession.objects.filter(
                    user=request.user,
                    revoked_at__isnull=True,
                    expires_at__gt=timezone.now(),
                )
            ],
        },
        headers={"Cache-Control": "private, no-store"},
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def session_metadata(request):
    from .services.session_management import update_metadata

    return Response(
        update_metadata(request), headers={"Cache-Control": "private, no-store"}
    )
