from django.db import transaction
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.idempotency import execute_idempotent, request_key, response_headers
from . import identity_expiry


class ExpiryInput(serializers.Serializer):
    document_version = serializers.CharField(max_length=64)
    expected_revision = serializers.IntegerField(min_value=0)
    expires_on = serializers.DateField(allow_null=True)
    reminder_days = serializers.ListField(child=serializers.ChoiceField(choices=identity_expiry.REMINDER_DAYS), max_length=3)

    def validate(self, data):
        if len(set(data["reminder_days"])) != len(data["reminder_days"]):
            raise serializers.ValidationError("Choose each reminder once.")
        if data["reminder_days"] and not data["expires_on"]:
            raise serializers.ValidationError("Enter an expiry date before enabling reminders.")
        return data


class IdentityExpiryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def get(self, request):
        profile = identity_expiry.locked_profile(request.user)
        return Response(identity_expiry.projection(profile), headers={"Cache-Control": "private, no-store"})

    @transaction.atomic
    def post(self, request):
        profile = identity_expiry.locked_profile(request.user)
        key = request_key(request)
        if not key:
            raise serializers.ValidationError({"Idempotency-Key": "Required for recoverable saves."})
        serializer = ExpiryInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        # Recheck the physical card even for receipt replay after replacement.
        if identity_expiry.card_version(profile) != data["document_version"]:
            from core_apps.common.idempotency import IdempotencyConflict
            raise IdempotencyConflict("Identity card changed. Refresh before saving.")
        result, code, replayed = execute_idempotent(
            user=request.user, operation="identity.expiry", key=key, payload=data,
            action=lambda: (identity_expiry.update(profile, data), 200, str(profile.id)),
        )
        return Response(result, status=code, headers={**response_headers(replayed), "Cache-Control": "private, no-store"})
