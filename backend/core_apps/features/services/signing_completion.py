"""Apply a confirmed signature using the existing agreement and inventory rules."""

from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from core_apps.notifications.models import Notification
from ..models import Lease, RentalInventoryDayLock, SigningSession
from .rental_phase2 import RentalConflict


@transaction.atomic
def complete_signature(provider_session_id):
    from ..rental_phase2_views_parts.owner_payment_profile import _event, _notify

    session = get_object_or_404(SigningSession, provider_session_id=provider_session_id)
    if session.lease.renter_company_id:
        from ..services.company.tenancy_contracts import complete_signature

        complete_signature(session)
        return {"status": "accepted"}
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
