from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core_apps.users.models import User
from core_apps.common.idempotency import execute_idempotent, request_key, response_headers, IdempotencyConflict
from .models import NotificationDeliveryPolicy
from .services.delivery_policy import CATEGORIES, MODES, projection


class PolicyInput(serializers.Serializer):
    expected_revision = serializers.IntegerField(min_value=0)
    timezone = serializers.CharField(max_length=64)
    modes = serializers.DictField(child=serializers.ChoiceField(choices=MODES))
    quiet_start = serializers.IntegerField(min_value=0, max_value=1439, allow_null=True)
    quiet_end = serializers.IntegerField(min_value=0, max_value=1439, allow_null=True)

    def validate(self, data):
        try:
            ZoneInfo(data["timezone"])
        except (ZoneInfoNotFoundError, ValueError):
            raise serializers.ValidationError({"timezone": "Choose a valid IANA timezone."})
        if set(data["modes"]) != set(CATEGORIES):
            raise serializers.ValidationError({"modes": "Supply exactly the active optional categories."})
        if ((data["quiet_start"] is None) != (data["quiet_end"] is None)
                or data["quiet_start"] is not None and data["quiet_start"] == data["quiet_end"]):
            raise serializers.ValidationError("Choose distinct quiet-hour start and end, or disable both.")
        return data


class NotificationDeliveryPolicyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def current_user(self, request):
        user = User.objects.select_for_update().get(pk=request.user.pk)
        if not user.is_active or user.closed_at or user.security_epoch != request.user.security_epoch:
            raise PermissionDenied("Account authority changed.")
        return user

    @transaction.atomic
    def get(self, request):
        user = self.current_user(request)
        return Response(projection(NotificationDeliveryPolicy.objects.filter(user=user).first()), headers={"Cache-Control": "private, no-store"})

    @transaction.atomic
    def post(self, request):
        user = self.current_user(request)
        serializer = PolicyInput(data=request.data); serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        key = request_key(request)
        if not key:
            raise serializers.ValidationError("Idempotency-Key is required.")
        def action():
            policy = NotificationDeliveryPolicy.objects.filter(user=user).first()
            if (policy.revision if policy else 0) != data["expected_revision"]:
                raise IdempotencyConflict("Delivery preferences changed. Refresh before saving.")
            if policy is None:
                policy = NotificationDeliveryPolicy(user=user)
            else:
                policy.revision += 1
            policy.timezone_name, policy.modes = data["timezone"], data["modes"]
            policy.quiet_start, policy.quiet_end = data["quiet_start"], data["quiet_end"]
            policy.save()
            return projection(policy), 200, str(policy.id)
        result, code, replayed = execute_idempotent(user=user, operation="notification.delivery-policy", key=key, payload=data, action=action)
        return Response(result, status=code, headers={**response_headers(replayed), "Cache-Control": "private, no-store"})
