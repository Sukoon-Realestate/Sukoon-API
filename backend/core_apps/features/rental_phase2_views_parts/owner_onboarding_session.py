"""Rental phase2 views: owner onboarding session."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import OwnerOnboardingSession, OwnerPaymentProfile
from ..providers import (
    mock_completion_metadata,
    get_rental_provider,
    require_rental_provider,
)
from ..renderers import FeatureJsonRenderer
from ..rental_serializers import OwnerOnboardingBodySerializer
from ..services.rental_phase2 import RentalConflict, get_or_create_owner_profile
from .owner_payment_profile import _replay_response, _remember_session


class OwnerOnboardingSessionView(FeatureAPIView):
    name = "Owner Onboarding Session"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "owner_onboarding_session",
            "owner_onboarding_session",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request):
        require_rental_provider(request.user)
        serializer = OwnerOnboardingBodySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        profile = get_or_create_owner_profile(request.user)
        operation = "rental.owner_onboarding.create"
        replay = _replay_response(
            request.user, operation, data["request_key"], request.data
        )
        if replay:
            return replay
        if "rental-policy-v1" not in data["accepted_policy_versions"]:
            raise ValidationError(
                {"accepted_policy_versions": "rental-policy-v1 must be accepted."}
            )
        with transaction.atomic():
            profile = OwnerPaymentProfile.objects.select_for_update().get(pk=profile.pk)
            replay = _replay_response(
                request.user, operation, data["request_key"], request.data
            )
            if replay:
                return replay
            if data["expected_revision"] != profile.revision:
                raise RentalConflict(
                    "Owner profile revision conflict.", code="stale_revision"
                )
            if profile.status == OwnerPaymentProfile.Status.READY:
                raise RentalConflict("Beneficiary onboarding is already complete.")
            from core_apps.users.services.sensitive_actions import consume

            consume(
                request,
                action="beneficiary.onboarding",
                resource_id=profile.id,
                revision=profile.revision,
            )
            provider_session = get_rental_provider().create_onboarding_session(
                profile.id, data["request_key"]
            )
            expires_at = timezone.now() + timedelta(
                minutes=settings.RENTAL_ONBOARDING_TTL_MINUTES
            )
            session = OwnerOnboardingSession.objects.create(
                owner_profile=profile,
                request_key=data["request_key"],
                profile_revision=profile.revision,
                provider_session_id=provider_session.provider_session_id,
                hosted_url=provider_session.hosted_url,
                expires_at=expires_at,
            )
            # A new consent submission must not erase previously accepted versions.
            profile.accepted_policy_versions = list(
                dict.fromkeys(
                    [
                        *profile.accepted_policy_versions,
                        *data["accepted_policy_versions"],
                    ]
                )
            )
            profile.status = OwnerPaymentProfile.Status.PENDING
            profile.provider = get_rental_provider().name
            profile.revision += 1
            profile.save(
                update_fields=[
                    "accepted_policy_versions",
                    "status",
                    "provider",
                    "revision",
                    "updated_at",
                ]
            )
            output = {
                "session_id": str(session.id),
                "subject_id": str(profile.id),
                "request_key": str(data["request_key"]),
                "revision": session.profile_revision,
                "profile_revision": profile.revision,
                **mock_completion_metadata(
                    "onboarding-sessions", session.id, profile.revision
                ),
                "hosted_url": session.hosted_url,
                "expires_at": expires_at.isoformat(),
            }
            output = _remember_session(
                user=request.user,
                operation=operation,
                request_key=data["request_key"],
                payload=request.data,
                request_subject_id=profile.id,
                result_subject_id=session.id,
                result_revision=session.profile_revision,
                response_data=output,
            )
        return Response(output, status=status.HTTP_201_CREATED)


# Stable callable import for integrations; URLs use the explicit class.
owner_onboarding_session = OwnerOnboardingSessionView.as_view()

__all__ = ["OwnerOnboardingSessionView", "owner_onboarding_session"]
