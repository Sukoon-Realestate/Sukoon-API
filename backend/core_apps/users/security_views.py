"""HTTP adapters for challenges and revocable account sessions."""
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .http import IdentityAPIView as APIView

from core_apps.common.idempotency import response_headers
from core_apps.common.renderers import GenericJsonRenderer
from .services import sensitive_actions, session_management
from .selectors import active_sessions


class ChallengeBody(serializers.Serializer):
    action = serializers.ChoiceField(choices=sorted(sensitive_actions.ACTIONS))
    resource_id = serializers.UUIDField()
    resource_revision = serializers.IntegerField(min_value=0)
    payload = serializers.DictField()


class AssertionField(serializers.Field):
    """Preserve the provider assertion's exact bytes and established error."""

    def run_validation(self, value=serializers.empty):
        if not isinstance(value, str) or not 1 <= len(value) <= 16384:
            raise serializers.ValidationError("A provider assertion is required.")
        return value


class AssertionBody(serializers.Serializer):
    assertion = AssertionField(required=False)

    def validate(self, data):
        if "assertion" not in data:
            raise serializers.ValidationError({"assertion": "A provider assertion is required."})
        return data


class SecurityChallengeAPIView(APIView):
    name = "Challenges"  # Preserve OPTIONS metadata.
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request):
        body = ChallengeBody(data=request.data)
        body.is_valid(raise_exception=True)
        return Response(sensitive_actions.begin(request, body.validated_data), status=201)


class SecurityChallengeVerifyAPIView(APIView):
    name = "Verify"  # Preserve OPTIONS metadata.
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request, identity):
        body = AssertionBody(data=request.data)
        body.is_valid(raise_exception=True)
        return Response(sensitive_actions.verify(request, identity, body.validated_data["assertion"]))


class AuthSessionListAPIView(APIView):
    name = "Sessions"  # Preserve OPTIONS metadata.
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request):
        return Response(
            active_sessions(request.user, request.auth, request.query_params),
            headers={"Cache-Control": "private, no-store"},
        )

    def post(self, request):
        data, code, replayed = session_management.revoke_sessions(request)
        return Response(data, status=code, headers=response_headers(replayed))


class AuthSessionMetadataAPIView(APIView):
    name = "Session Metadata"  # Preserve OPTIONS metadata.
    http_method_names = ["patch", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def patch(self, request):
        return Response(
            session_management.update_metadata(request),
            headers={"Cache-Control": "private, no-store"},
        )
