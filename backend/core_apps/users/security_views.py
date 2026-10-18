from django.db import transaction
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from .services import sensitive_actions
from .services.sessions import revoke_all
from .models import AuthSession, User, SecurityEvent
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
        if action not in {"revoke_all", "report_compromise"}:
            raise serializers.ValidationError(
                {"action": "Use revoke_all or report_compromise."}
            )
        with transaction.atomic():
            current = User.objects.select_for_update().get(pk=request.user.pk)
            if request.auth:
                from .services.sessions import validate_session

                validate_session(current, request.auth)
            ticket = None
            if action == "report_compromise" and not current.sensitive_actions_frozen:
                from core_apps.support.services import create_ticket

                ticket = create_ticket(
                    current,
                    workspace=(
                        "owner"
                        if request.data.get("workspace") == "owner"
                        else "tenant"
                    ),
                    category="verification",
                    subject="Account access security review",
                    description="The account holder reported possible unauthorized access. Sensitive actions were frozen and all sessions revoked. Review identity and original operation receipts before authorizing recovery. No reversal or replacement payment is authorized.",
                )
            current = revoke_all(
                current,
                actor=current,
                action=(
                    "account.compromise_reported"
                    if action == "report_compromise"
                    else "session.revoke_all"
                ),
                freeze=action == "report_compromise",
            )
            if ticket:
                SecurityEvent.objects.create(
                    user=current,
                    actor=current,
                    action="account.security_case",
                    security_epoch=current.security_epoch,
                    subject_id=ticket.id,
                    decision="awaiting_review",
                )
        return Response(
            {
                "status": "revoked",
                "support_ticket_id": str(ticket.id) if ticket else None,
            }
        )
    return Response(
        {
            "sensitive_actions_frozen": request.user.sensitive_actions_frozen,
            "results": [
                {
                    "id": str(item.id),
                    "created_at": item.created_at.isoformat(),
                    "expires_at": item.expires_at.isoformat(),
                    "current": str(item.id) == (request.auth or {}).get("session_id"),
                }
                for item in AuthSession.objects.filter(
                    user=request.user,
                    revoked_at__isnull=True,
                    expires_at__gt=timezone.now(),
                )
            ],
        }
    )
