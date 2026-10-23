from datetime import timedelta
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from core_apps.common.idempotency import execute_idempotent, request_key
from core_apps.notifications.models import DeviceToken
from ..models import AuthSession, SecurityEvent, User
from .sessions import validate_session


class DeviceMetadata(serializers.Serializer):
    client_platform = serializers.ChoiceField(
        choices=["android", "ios", "web", "macos", "windows", "linux"]
    )
    device_model = serializers.CharField(max_length=100, allow_blank=True)
    os_version = serializers.CharField(max_length=40, allow_blank=True)
    app_version = serializers.CharField(max_length=40, allow_blank=True)

    def validate(self, data):
        if any(any(ord(c) < 32 for c in v) for v in data.values()):
            raise serializers.ValidationError(
                "Device labels cannot contain control characters."
            )
        return data


def touch_session(user, claims):
    sid = (claims or {}).get("session_id")
    if sid:
        now = timezone.now()
        AuthSession.objects.filter(user=user, id=sid, revoked_at__isnull=True).filter(
            Q(last_seen_at__isnull=True)
            | Q(last_seen_at__lt=now - timedelta(minutes=5))
        ).update(last_seen_at=now)


@transaction.atomic
def update_metadata(request):
    current = User.objects.select_for_update().get(pk=request.user.pk)
    validate_session(current, request.auth or {})
    sid = (request.auth or {}).get("session_id")
    if not sid:
        raise ValidationError(
            {
                "code": "reauthentication_required",
                "message": "Sign in again to identify this session.",
            }
        )
    body = DeviceMetadata(data=request.data)
    body.is_valid(raise_exception=True)
    AuthSession.objects.filter(user=current, id=sid, revoked_at__isnull=True).update(
        **body.validated_data
    )
    return {"status": "updated"}


def close_sockets(identities):
    layer = get_channel_layer()
    if layer is not None:
        for identity in identities:
            try:
                async_to_sync(layer.group_send)(
                    f"chat_session_{identity}", {"type": "session.revoked"}
                )
            except Exception:
                # The committed session fence also rejects every subsequent frame.
                import logging

                logging.getLogger(__name__).warning(
                    "Session socket close delivery unavailable"
                )


@transaction.atomic
def revoke_selected(request):
    user = User.objects.select_for_update().get(pk=request.user.pk)
    validate_session(user, request.auth or {})
    sid = (request.auth or {}).get("session_id")
    if not sid:
        raise ValidationError(
            {
                "code": "reauthentication_required",
                "message": "Sign in again before managing individual sessions.",
            }
        )
    action = request.data.get("action")
    key = request_key(request)
    if not key:
        raise ValidationError(
            {"Idempotency-Key": "A stable operation key is required."}
        )
    target = None
    if action == "revoke_session":
        target = serializers.UUIDField().run_validation(request.data.get("session_id"))
    elif action != "revoke_others":
        raise ValidationError({"action": "Unsupported session action."})

    def apply():
        rows = AuthSession.objects.filter(user=user)
        if target:
            rows = rows.filter(id=target)
            if not rows.exists():
                raise NotFound()
        else:
            rows = rows.exclude(id=sid)
        identities = [
            str(i)
            for i in rows.filter(revoked_at__isnull=True).values_list("id", flat=True)
        ]
        rows.filter(revoked_at__isnull=True).update(revoked_at=timezone.now())
        DeviceToken.objects.filter(user=user, auth_session__id__in=identities).update(
            is_active=False
        )
        # Legacy tokens cannot be safely attributed to a device being revoked.
        DeviceToken.objects.filter(user=user, auth_session__isnull=True).update(
            is_active=False
        )
        SecurityEvent.objects.create(
            user=user,
            actor=user,
            action=f"session.{action}",
            security_epoch=user.security_epoch,
            subject_id=target,
            decision="revoked",
        )
        transaction.on_commit(lambda: close_sockets(identities))
        return (
            {
                "status": "revoked",
                "revoked_session_ids": identities,
                "current_session_revoked": str(sid) in identities,
                "request_key": key,
            },
            200,
            target,
        )

    return execute_idempotent(
        user=user,
        operation="security.session.revoke",
        key=key,
        payload={"action": action, "session_id": str(target or "")},
        action=apply,
        auth_claims=request.auth,
    )
