from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def staff_identities(request):
    return response(staff_setup.identities(request))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def document_staff_identity(request, identity):
    body = StaffIdentityBody(data=request.data)
    body.is_valid(raise_exception=True)
    return response(
        staff_setup.document_identity(request, identity, body.validated_data)
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def initial_enrollment(request):
    return response(staff_setup.enroll(request))


def response(value, status=200):
    return Response(
        value, status=status, headers={"Cache-Control": "private, no-store"}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def security(request):
    return response(totp_recovery.status(request))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def recoveries(request):
    body = RecoveryBody(data=request.data)
    body.is_valid(raise_exception=True)
    return response(
        totp_recovery.create_request(request, body.validated_data["reason"]), 201
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def respond(request, identity):
    body = RecoveryResponseBody(data=request.data)
    body.is_valid(raise_exception=True)
    return response(totp_recovery.respond(request, identity, body.validated_data))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def queue(request):
    return response({"results": totp_recovery.review_queue(request)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def decide(request, identity):
    body = DecisionBody(data=request.data)
    body.is_valid(raise_exception=True)
    return response(totp_recovery.decide(request, identity, body.validated_data))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def enroll(request, identity):
    return response(totp_recovery.enroll(request, identity))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def confirm(request, identity):
    body = serializers.CharField(min_length=6, max_length=6).run_validation(
        request.data.get("code")
    )
    return response(totp_recovery.confirm(request, identity, body))
