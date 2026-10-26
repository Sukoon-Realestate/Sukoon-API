"""Rental phase2 views: apply fake rental event."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from ..models import (
    OwnerOnboardingSession,
    OwnerPaymentProfile,
    SigningSession,
)
from ..providers import fake_provider_available, verify_fake_webhook
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict


def apply_fake_rental_event(payload):
    event_type = payload.get("type")
    provider_session_id = payload.get("provider_session_id")
    with transaction.atomic():
        if event_type == "onboarding.completed":
            session = get_object_or_404(
                OwnerOnboardingSession, provider_session_id=provider_session_id
            )
            OwnerPaymentProfile.objects.select_for_update().get(
                pk=session.owner_profile_id
            )
            session = (
                OwnerOnboardingSession.objects.select_for_update(of=("self",))
                .select_related("owner_profile")
                .get(pk=session.pk)
            )
            if session.status != "completed":
                if session.expires_at <= timezone.now():
                    raise RentalConflict(
                        "The onboarding session has expired.", code="session_expired"
                    )
                if session.owner_profile.revision != session.profile_revision + 1:
                    raise RentalConflict(
                        "The onboarding session is stale.", code="stale_revision"
                    )
                session.status = "completed"
                session.completed_at = timezone.now()
                session.save(update_fields=["status", "completed_at", "updated_at"])
                profile = OwnerPaymentProfile.objects.select_for_update().get(
                    pk=session.owner_profile_id
                )
                profile.status = OwnerPaymentProfile.Status.READY
                profile.payout_ready = True
                profile.masked_beneficiary = {"account_last4": "4242"}
                profile.provider = "fake"
                profile.provider_account_id = f"fake-beneficiary:{profile.id}"
                profile.requirements = []
                profile.revision += 1
                profile.save()
        elif event_type == "signature.completed":
            from ..services.signing_completion import complete_signature
            from ..models import RentalSigningDocument

            session = get_object_or_404(SigningSession, provider_session_id=provider_session_id)
            if RentalSigningDocument.objects.filter(id=session.document_id).exists():
                raise PermissionDenied("A real provider document requires authenticated reconciliation.")
            complete_signature(provider_session_id)
        elif event_type == "change-signature.completed":
            from ..rental_phase5_views import complete_change_signature

            from ..models import ChangeSigningSession, RentalSigningDocument
            session = get_object_or_404(ChangeSigningSession, provider_session_id=provider_session_id)
            if RentalSigningDocument.objects.filter(id=session.document_id).exists():
                raise PermissionDenied("A real provider document requires authenticated reconciliation.")
            complete_change_signature(provider_session_id)
        else:
            raise ValidationError({"type": "Unsupported fake-provider event."})
    return {"status": "accepted"}


@api_view(["POST"])
@permission_classes([AllowAny])
@renderer_classes([FeatureJsonRenderer])
def fake_rental_provider_webhook(request):
    if not fake_provider_available():
        raise NotFound()
    if not verify_fake_webhook(request.data, request.headers.get("X-Rental-Signature")):
        raise PermissionDenied("Invalid provider signature.")

    return Response(apply_fake_rental_event(request.data))
