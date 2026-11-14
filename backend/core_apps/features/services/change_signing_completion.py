"""Apply an original confirmed change signature using current locked terms."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ..models import ChangeSigningSession, Lease, RentalChange
from .rental_phase2 import RentalConflict


def complete_change_signature(provider_session_id):
    with transaction.atomic():
        session = get_object_or_404(
            ChangeSigningSession, provider_session_id=provider_session_id
        )
        if session.change.lease.renter_company_id:
            from ..services.company.tenancy_continuation_signing import complete

            return complete(session)
        lease = Lease.objects.select_for_update().get(pk=session.change.lease_id)
        item = RentalChange.objects.select_for_update().get(pk=session.change_id)
        item.lease = lease
        session = ChangeSigningSession.objects.select_for_update().get(pk=session.pk)
        if session.status == "completed":
            return item
        from ..services.change_terms import require_current_change_base

        require_current_change_base(item)
        if (
            item.status != RentalChange.Status.PENDING_SIGNATURES
            or session.expires_at <= timezone.now()
            or session.change_revision != item.revision
            or (session.document_id != item.document_id)
            or (session.document_hash != item.document_hash)
        ):
            raise RentalConflict(
                "The signed change document is stale.", code="document_changed"
            )
        session.status = "completed"
        session.completed_at = timezone.now()
        session.save()
        signed = set(item.signed_by)
        signed.add(str(session.signer.id))
        item.signed_by = sorted(signed)
        if {str(item.lease.owner.id), str(item.lease.tenant.id)}.issubset(signed):
            item.status = RentalChange.Status.SIGNED
            item.revision += 1
        item.save()
        from ..services.document_intents import change

        change(item)
        from ..services.planning_notifications import record_event

        record_event(item, session.signer, f"change.signed.{session.id}")
        return item


__all__ = ["complete_change_signature"]
