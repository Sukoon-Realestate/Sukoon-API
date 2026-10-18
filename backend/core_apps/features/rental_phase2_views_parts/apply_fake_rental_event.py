"""Rental phase2 views: apply fake rental event."""

from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from core_apps.notifications.models import Notification
from ..models import (
    Lease,
    OwnerOnboardingSession,
    OwnerPaymentProfile,
    RentalInventoryDayLock,
    SigningSession,
)
from ..providers import fake_provider_available, verify_fake_webhook
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict
from .owner_payment_profile import _event, _notify


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
            session = get_object_or_404(
                SigningSession, provider_session_id=provider_session_id
            )
            from core_apps.properties.models import Property

            Property.objects.select_for_update().get(pk=session.lease.property_id)
            Lease.objects.select_for_update().get(pk=session.lease_id)
            session = (
                SigningSession.objects.select_for_update(of=("self",))
                .select_related("lease__owner", "lease__tenant")
                .get(pk=session.pk)
            )
            if session.status != "completed":
                lease = Lease.objects.select_for_update().get(pk=session.lease_id)
                if (
                    lease.status != Lease.Status.PENDING_SIGNATURES
                    or session.expires_at <= timezone.now()
                    or session.document_id != lease.document_id
                    or session.document_hash != lease.document_hash
                    or session.lease_revision != lease.revision
                ):
                    raise RentalConflict(
                        "The signed document is stale.", code="document_changed"
                    )
                session.status = "completed"
                session.completed_at = timezone.now()
                session.save(update_fields=["status", "completed_at", "updated_at"])
                signer_ids = set(
                    SigningSession.objects.filter(
                        lease=lease,
                        status="completed",
                        document_id=lease.document_id,
                        document_hash=lease.document_hash,
                    ).values_list("signer_id", flat=True)
                )
                if {lease.owner_id, lease.tenant_id}.issubset(signer_ids):
                    now = timezone.now()
                    holds = lease.inventory_day_locks.filter(
                        kind=RentalInventoryDayLock.Kind.HOLD, expires_at__gt=now
                    )
                    from ..services.rental_lifecycle.inventory import hold_coverage

                    if not hold_coverage(lease):
                        raise RentalConflict(
                            "The inventory hold has expired.", code="hold_expired"
                        )
                    lease.hold_expires_at = now + timedelta(hours=48)
                    holds.update(expires_at=lease.hold_expires_at)
                    from ..models import ReservationHold

                    ReservationHold.objects.filter(lease=lease).update(
                        expires_at=lease.hold_expires_at
                    )
                    lease.status = Lease.Status.SIGNED
                    lease.revision += 1
                    lease.save(
                        update_fields=[
                            "status",
                            "hold_expires_at",
                            "revision",
                            "updated_at",
                        ]
                    )
                    from ..services.rental_phase3 import generate_billing_schedule

                    generate_billing_schedule(lease)
                    _event(
                        lease,
                        None,
                        "signed",
                        "Agreement signed; initial payment is due",
                    )
                    for participant, workspace in (
                        (lease.owner, "owner"),
                        (lease.tenant, "tenant"),
                    ):
                        transaction.on_commit(
                            lambda participant=participant, workspace=workspace: _notify(
                                participant,
                                Notification.NotificationType.RENTAL_AGREEMENT,
                                "Rental agreement signed; initial payment is due",
                                "open_rental_center",
                                lease.id,
                                lease_id=lease.id,
                                workspace=workspace,
                            )
                        )
        elif event_type == "change-signature.completed":
            from ..rental_phase5_views import complete_change_signature

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
    from core_apps.common.recovery import require_scope

    require_scope("provider_callbacks")
    return Response(apply_fake_rental_event(request.data))
