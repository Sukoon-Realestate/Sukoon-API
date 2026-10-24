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
            result = execute_refund(refund)
            refunded += int(result.status == "succeeded")
        except RentalConflict as exc:
            # One held refund must not starve unrelated refunds or closure work.
            RefundRequest.objects.filter(pk=refund.pk, status="approved").update(
                failure_code=str(exc.get_codes()), updated_at=timezone.now()
            )
    # Paymob submissions happen only after the canonical refund reservation
    # transaction commits. Turning off new sales does not stop reconciliation.
    from ..models import PaymobPayment, PaymobRefund
    from ..services.paymob_payments import reconcile as reconcile_paymob
    from ..services.paymob_refunds import process as process_paymob_refund
    from rest_framework.exceptions import APIException

    for payment in PaymobPayment.objects.exclude(status="captured").select_related(
        "attempt__invoice"
    )[:100]:
        try:
            reconcile_paymob(payment)
        except APIException:
            pass  # The original attempt/case remains durable for the next run.
    for item in PaymobRefund.objects.exclude(refund__status="succeeded").select_related(
        "payment__attempt", "refund__lease"
    )[:100]:
        try:
            result = process_paymob_refund(item)
            refunded += int(result.status == "succeeded")
        except APIException:
            pass  # Never resubmit an instruction whose outcome is unknown.
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

        with transaction.atomic():
            from ..services.rental_lifecycle.locks import lock_financial_lease

            lease = lock_financial_lease(lease)
            previous = lease.financial_closure_status
            evaluate_financial_closure(lease)
            if lease.renter_company_id:
                from ..services.company.tenancy_access import notify

                tenancy = lease.company_tenancy
                if previous != lease.financial_closure_status:
                    notify(tenancy)
        evaluated += 1
        for participant in (lease.owner, lease.tenant):
            if participant is not None and not participant.is_active:
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
