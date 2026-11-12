from .http import IdentityAPIView as APIView
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from .services import totp_recovery
from .services import staff_setup


class RecoveryBody(serializers.Serializer):
    reason = serializers.CharField(max_length=1000)


class RecoveryResponseBody(RecoveryBody):
    expected_revision = serializers.IntegerField(min_value=1)


class DecisionBody(serializers.Serializer):
    expected_revision = serializers.IntegerField(min_value=1)
    decision = serializers.ChoiceField(
        choices=["approve", "reject", "request_information", "renew_enrollment"]
    )
    reason = serializers.CharField(max_length=1000)
    verification_method = serializers.ChoiceField(
        choices=["in_person", "known_channel_video"], required=False
    )
    verification_reference = serializers.CharField(max_length=200, required=False)
    identity_matched = serializers.BooleanField(required=False)


class StaffIdentityBody(serializers.Serializer):
    person_reference = serializers.CharField(max_length=128)
    evidence_reference = serializers.CharField(max_length=200)
    known_channel_reference = serializers.CharField(max_length=200)
    verification_method = serializers.ChoiceField(
        choices=["in_person", "known_channel_video"]
    )
    identity_matched = serializers.BooleanField()


class StaffIdentityListAPIView(APIView):
    name = "Staff Identities"  # Preserve OPTIONS metadata.
    http_method_names = ['get', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request):
        return response(staff_setup.identities(request))


class StaffIdentityDocumentAPIView(APIView):
    name = "Document Staff Identity"  # Preserve OPTIONS metadata.
    http_method_names = ['post', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request, identity):
        body = StaffIdentityBody(data=request.data)
        body.is_valid(raise_exception=True)
        return response(
            staff_setup.document_identity(request, identity, body.validated_data)
        )


class StaffInitialEnrollmentAPIView(APIView):
    name = "Initial Enrollment"  # Preserve OPTIONS metadata.
    http_method_names = ['post', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request):
        return response(staff_setup.enroll(request))


def response(value, status=200):
    return Response(
        value, status=status, headers={"Cache-Control": "private, no-store"}
    )


class TotpSecurityAPIView(APIView):
    name = "Security"  # Preserve OPTIONS metadata.
    http_method_names = ['get', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request):
        return response(totp_recovery.status(request))


class TotpRecoveryCreateAPIView(APIView):
    name = "Recoveries"  # Preserve OPTIONS metadata.
    http_method_names = ['post', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request):
        body = RecoveryBody(data=request.data)
        body.is_valid(raise_exception=True)
        return response(
            totp_recovery.create_request(request, body.validated_data["reason"]), 201
        )


class TotpRecoveryRespondAPIView(APIView):
    name = "Respond"  # Preserve OPTIONS metadata.
    http_method_names = ['post', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request, identity):
        body = RecoveryResponseBody(data=request.data)
        body.is_valid(raise_exception=True)
        return response(totp_recovery.respond(request, identity, body.validated_data))


class TotpRecoveryQueueAPIView(APIView):
    name = "Queue"  # Preserve OPTIONS metadata.
    http_method_names = ['get', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def get(self, request):
        result = totp_recovery.review_queue(request)
        return response(result if isinstance(result, dict) else {"results": result})


class TotpRecoveryDecisionAPIView(APIView):
    name = "Decide"  # Preserve OPTIONS metadata.
    http_method_names = ['post', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request, identity):
        body = DecisionBody(data=request.data)
        body.is_valid(raise_exception=True)
        return response(totp_recovery.decide(request, identity, body.validated_data))


class TotpRecoveryEnrollAPIView(APIView):
    name = "Enroll"  # Preserve OPTIONS metadata.
    http_method_names = ['post', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request, identity):
        return response(totp_recovery.enroll(request, identity))


class TotpEnrollmentConfirmAPIView(APIView):
    name = "Confirm"  # Preserve OPTIONS metadata.
    http_method_names = ['post', 'options']
    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def post(self, request, identity):
        body = serializers.CharField(min_length=6, max_length=6).run_validation(
            request.data.get("code")
        )
        return response(totp_recovery.confirm(request, identity, body))
