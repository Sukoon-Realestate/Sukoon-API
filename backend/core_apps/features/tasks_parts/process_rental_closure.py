"""Tasks: process rental closure."""

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from ..models import Lease, RefundRequest, RentalDocument, PrivateAccessRevocation
from ..services.rental_phase2 import RentalConflict


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def process_rental_closure(self):
    import hashlib
    import json
    from ..services.rental_phase6 import evaluate_financial_closure, execute_refund
    from ..planning_transition_views import reconcile_transitions

    from ..services.legal_lifecycle import end_due_leases

    ended = end_due_leases()
    refunded = generated = evaluated = revoked = 0
    for refund in RefundRequest.objects.filter(status=RefundRequest.Status.APPROVED)[
        :100
    ]:
        try:
            execute_refund(refund)
            refunded += 1
        except RentalConflict as exc:
            # One held refund must not starve unrelated refunds or closure work.
            RefundRequest.objects.filter(pk=refund.pk, status="approved").update(
                failure_code=str(exc.get_codes()), updated_at=timezone.now()
            )
    for candidate in RentalDocument.objects.filter(
        status=RentalDocument.Status.QUEUED
    ).select_related("lease")[:100]:
        with transaction.atomic():
            document = RentalDocument.objects.select_for_update().get(pk=candidate.pk)
            if document.status != RentalDocument.Status.QUEUED:
                continue
            from ..services.private_rental_documents import generate

            generated += int(generate(document))
    for lease in Lease.objects.all().iterator():
        evaluate_financial_closure(lease)
        evaluated += 1
        for participant in (lease.owner, lease.tenant):
            if not participant.is_active:
                _, created = PrivateAccessRevocation.objects.get_or_create(
                    lease=lease, user=participant, defaults={"reason": "account_closed"}
                )
                revoked += int(created)
    transitions = reconcile_transitions()
    from ..services.planning import purge_expired_discovery

    purge_expired_discovery()
    return {
        "refunds": refunded,
        "transitions": transitions,
        "legally_ended": ended,
        "documents": generated,
        "leases": evaluated,
        "access_revocations": revoked,
    }
