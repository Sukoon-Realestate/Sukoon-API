"""Authenticated provider simulation for explicitly enabled non-production APIs."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    ChangeSigningSession,
    Lease,
    OwnerOnboardingSession,
    OwnerPaymentProfile,
    PaymentAttempt,
    RentalChange,
    SigningSession,
)
from .providers import (
    checkout_available,
    fake_provider_available,
    require_rental_provider,
)
from .renderers import FeatureJsonRenderer
from .rental_phase2_views import apply_fake_rental_event
from .rental_phase3_views import apply_fake_payment_event
from .rental_phase5_views import change_payload
from .rental_serializers import LeasePhase2Serializer, OwnerPaymentProfileSerializer
from .services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .services.rental_phase3 import payment_attempt_payload


class MockCompletionBody(serializers.Serializer):
    request_key = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=1)


class MockPaymentBody(MockCompletionBody):
    event = serializers.ChoiceField(choices=["captured", "settled", "failed"])


def _body(request, serializer_class=MockCompletionBody):
    if not fake_provider_available():
        raise NotFound()
    require_rental_provider(request.user)
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def _replay(request, data, operation):
    replay = replay_operation(
        request.user, operation, data["request_key"], request.data
    )
    return Response(replay[0], status=replay[1]) if replay else None


def _revision(data, subject):
    if data["expected_revision"] != subject.revision:
        raise RentalConflict(
            "Mock completion revision conflict.", code="stale_revision"
        )


def _remember(request, data, operation, subject, resource):
    resource["provider_mode"] = "mock"
    return Response(
        remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=subject.id,
            result_subject_id=subject.id,
            result_revision=subject.revision,
            resource=resource,
        )
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def onboarding_complete(request, session_id):
    data = _body(request)
    session = get_object_or_404(
        OwnerOnboardingSession, id=session_id, owner_profile__owner=request.user
    )
    operation = f"mock.onboarding.complete.{session_id}"
    with transaction.atomic():
        profile = OwnerPaymentProfile.objects.select_for_update().get(
            pk=session.owner_profile_id
        )
        replay = _replay(request, data, operation)
        if replay is not None:
            return replay
        _revision(data, profile)
        apply_fake_rental_event(
            {
                "type": "onboarding.completed",
                "provider_session_id": session.provider_session_id,
            }
        )
        profile.refresh_from_db()
        return _remember(
            request,
            data,
            operation,
            profile,
            dict(
                OwnerPaymentProfileSerializer(
                    profile, context={"request": request}
                ).data
            ),
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def signing_complete(request, session_id, change=False):
    data = _body(request)
    session_model = ChangeSigningSession if change else SigningSession
    session = get_object_or_404(session_model, id=session_id, signer=request.user)
    operation = f"mock.signing.complete.{session_id}"
    with transaction.atomic():
        if change:
            subject = RentalChange.objects.select_for_update().get(pk=session.change_id)
        else:
            subject = Lease.objects.select_for_update().get(pk=session.lease_id)
        replay = _replay(request, data, operation)
        if replay is not None:
            return replay
        _revision(data, subject)
        apply_fake_rental_event(
            {
                "type": (
                    "change-signature.completed" if change else "signature.completed"
                ),
                "provider_session_id": session.provider_session_id,
            }
        )
        subject.refresh_from_db()
        resource = (
            change_payload(subject, request.user)
            if change
            else dict(LeasePhase2Serializer(subject, context={"request": request}).data)
        )
        return _remember(request, data, operation, subject, resource)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def payment_event(request, attempt_id):
    data = _body(request, MockPaymentBody)
    if not checkout_available():
        raise NotFound()
    operation = f"mock.payment.event.{attempt_id}"
    with transaction.atomic():
        candidate = get_object_or_404(
            PaymentAttempt.objects.select_related("invoice"),
            id=attempt_id,
            payer=request.user,
        )
        Lease.objects.select_for_update().get(pk=candidate.invoice.lease_id)
        attempt = get_object_or_404(
            PaymentAttempt.objects.select_for_update(),
            id=attempt_id,
            payer=request.user,
        )
        replay = _replay(request, data, operation)
        if replay is not None:
            return replay
        _revision(data, attempt)
        # Amount, currency and event identity come from persisted server state.
        # A tester cannot alter the invoice by supplying their own payment amount.
        apply_fake_payment_event(
            {
                "event_id": f"mock:{attempt.id}:{data['request_key']}",
                "type": f"payment.{data['event']}",
                "sequence": attempt.revision,
                "payment_attempt_id": str(attempt.id),
                "amount_minor": attempt.amount_minor,
                "currency": attempt.currency,
            }
        )
        attempt.refresh_from_db()
        return _remember(
            request,
            data,
            operation,
            attempt,
            payment_attempt_payload(attempt, request.user),
        )
