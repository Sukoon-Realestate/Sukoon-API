"""Replay service delivery without replaying collection."""

import logging
from django.db import transaction
from django.utils import timezone
from ..models import PaymentFulfillment

logger = logging.getLogger(__name__)


@transaction.atomic
def deliver(identity):
    # Match capture lock order, including when a worker retries later.
    from django.contrib.auth import get_user_model
    from ..models import Company, RentInvoice

    candidate = PaymentFulfillment.objects.select_related("invoice", "attempt").get(
        pk=identity
    )
    get_user_model().objects.select_for_update().get(pk=candidate.attempt.payer_id)
    if candidate.invoice.organization_id:
        Company.objects.select_for_update().get(pk=candidate.invoice.organization_id)
    RentInvoice.objects.select_for_update().get(pk=candidate.invoice_id)
    job = (
        PaymentFulfillment.objects.select_for_update(of=("self",))
        .select_related("invoice", "attempt")
        .get(pk=identity)
    )
    if job.status == "fulfilled":
        return job
    if job.attempt.payment_status != "captured" or job.invoice.status != "paid":
        return job
    job.attempts += 1
    try:
        # Savepoint rolls back only delivery if eligibility changed after payment.
        with transaction.atomic():
            from .billing_settlement import fulfill_purchase

            fulfill_purchase(job.invoice, job.attempt)
        job.status, job.failure_code, job.completed_at = "fulfilled", "", timezone.now()
    except Exception as exc:
        job.status = "pending"
        code = getattr(exc, "default_code", "fulfillment_pending")
        job.failure_code = str(code)[:80]
        logger.warning(
            "Payment fulfillment pending invoice=%s type=%s",
            job.invoice.id,
            type(exc).__name__,
        )
    job.save()
    return job
